"""Panel de administración: autenticación + CRUD de autores y exposiciones.

Salas (3b) y obras (3c) se añadirán en sub-partes posteriores.
"""
from urllib.parse import urlparse

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user

from backend.app.authz import exigir_acceso_exposicion, exigir_propietario
from backend.app.extensions import db
from backend.app.forms import AutorForm, ExposicionForm, ObraForm, SalaForm
from backend.app.models import Autor, Exposicion, Obra, Sala, Usuario, Zona
from backend.app.models.exposicion import (
    APERTURA_CERRADA,
    ESTADO_BORRADOR,
    ESTADO_PUBLICADA,
    VISIBILIDAD_CODIGO,
)
from backend.app.models.obra import PLACEHOLDER_IMAGEN, TIPO_CUADRO, TIPO_DIBUJO
from backend.app.models.zona import TIPO_MIXTO
from backend.app.plantillas import (
    nombre_plantilla,
    opciones_plantilla,
    sembrar_zonas,
)
from backend.app.services import cloudinary_service, stats
from backend.app.utils import slugify

bp = Blueprint("admin", __name__, url_prefix="/admin")


# --------------------------------------------------------------------------
# Autenticación
# --------------------------------------------------------------------------
def _es_url_segura(destino: str) -> bool:
    """Evita open-redirects: solo permite rutas locales (relativas)."""
    if not destino:
        return False
    parsed = urlparse(destino)
    return parsed.scheme == "" and parsed.netloc == "" and destino.startswith("/")


def _inicio_por_rol():
    """Panel de inicio según el rol: superadmin -> plataforma, resto -> admin."""
    if current_user.es_superadmin:
        return url_for("plataforma.dashboard")
    return url_for("admin.dashboard")


@bp.get("/login")
def login():
    if current_user.is_authenticated:
        return redirect(_inicio_por_rol())
    return render_template("admin/login.html")


@bp.post("/login")
def login_post():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    usuario = Usuario.query.filter_by(email=email).first()
    if usuario is not None and usuario.check_password(password):
        # login_user rechaza cuentas con is_active=False (activo=False).
        if not login_user(usuario):
            flash("Tu cuenta está desactivada. Contacta con la plataforma.", "error")
            return redirect(url_for("admin.login"))
        siguiente = request.args.get("next")
        if _es_url_segura(siguiente):
            return redirect(siguiente)
        return redirect(_inicio_por_rol())

    flash("Email o contraseña incorrectos.", "error")
    return redirect(url_for("admin.login"))


@bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("admin.login"))


@bp.get("/")
@login_required
def dashboard():
    return render_template(
        "admin/dashboard.html", stats=stats.panel_organizador(current_user.id)
    )


# --------------------------------------------------------------------------
# Autores
# --------------------------------------------------------------------------
@bp.get("/autores")
@login_required
def autores_list():
    autores = (
        Autor.query.filter_by(usuario_id=current_user.id)
        .order_by(Autor.nombre)
        .all()
    )
    return render_template("admin/autores_list.html", autores=autores)


@bp.route("/autores/nuevo", methods=["GET", "POST"])
@login_required
def autor_nuevo():
    form = AutorForm()
    if form.validate_on_submit():
        autor = Autor(
            usuario_id=current_user.id,
            nombre=form.nombre.data.strip(),
            bio=form.bio.data or None,
            foto_url=form.foto_url.data or None,
            contacto=form.contacto.data or None,
        )
        db.session.add(autor)
        db.session.commit()
        flash("Autor creado.", "info")
        return redirect(url_for("admin.autores_list"))
    return render_template("admin/autor_form.html", form=form, titulo="Nuevo autor")


@bp.route("/autores/<int:autor_id>/editar", methods=["GET", "POST"])
@login_required
def autor_editar(autor_id):
    autor = db.get_or_404(Autor, autor_id)
    exigir_propietario(autor.usuario_id)
    form = AutorForm(obj=autor)
    if form.validate_on_submit():
        autor.nombre = form.nombre.data.strip()
        autor.bio = form.bio.data or None
        autor.foto_url = form.foto_url.data or None
        autor.contacto = form.contacto.data or None
        db.session.commit()
        flash("Autor actualizado.", "info")
        return redirect(url_for("admin.autores_list"))
    return render_template(
        "admin/autor_form.html", form=form, titulo=f"Editar: {autor.nombre}"
    )


@bp.post("/autores/<int:autor_id>/borrar")
@login_required
def autor_borrar(autor_id):
    autor = db.get_or_404(Autor, autor_id)
    exigir_propietario(autor.usuario_id)
    if autor.obras:
        flash("No se puede borrar: el autor tiene obras asignadas.", "error")
    else:
        db.session.delete(autor)
        db.session.commit()
        flash("Autor borrado.", "info")
    return redirect(url_for("admin.autores_list"))


# --------------------------------------------------------------------------
# Exposiciones
# --------------------------------------------------------------------------
def _slug_unico(base: str, exclude_id=None) -> str:
    """Garantiza un slug único añadiendo un sufijo numérico si hace falta."""
    base = base or "exposicion"
    slug = base
    i = 2
    while True:
        q = Exposicion.query.filter_by(slug=slug)
        if exclude_id is not None:
            q = q.filter(Exposicion.id != exclude_id)
        if q.first() is None:
            return slug
        slug = f"{base}-{i}"
        i += 1


def _aplicar_visibilidad(expo, form) -> bool:
    """Vuelca visibilidad y código de acceso del formulario a la exposición.
    Devuelve False (con error en el campo) si la modalidad con código queda
    sin ningún código fijado."""
    codigo = (form.codigo_acceso.data or "").strip()
    if form.visibilidad.data == VISIBILIDAD_CODIGO and not codigo:
        if not expo.codigo_acceso_hash:
            form.codigo_acceso.errors.append(
                "Fija un código de acceso para la modalidad privada."
            )
            return False
    expo.visibilidad = form.visibilidad.data
    if codigo:
        expo.set_codigo_acceso(codigo)
    return True


def _aplicar_musica(expo, form) -> None:
    """Vuelca el hilo musical del formulario a la exposición: quitar la pista
    actual o subir una nueva (reemplazando la anterior). Los fallos de subida
    se comunican con flash y no interrumpen el guardado del resto."""
    if form.quitar_musica.data:
        cloudinary_service.eliminar_audio(expo.musica_public_id)
        expo.musica_public_id = None
        expo.musica_url = None
        return
    archivo = form.musica.data
    if not archivo:
        return
    if not cloudinary_service.esta_configurado():
        flash("Cloudinary no está configurado: la música no se subió.", "error")
        return
    anterior = expo.musica_public_id
    try:
        public_id, url = cloudinary_service.subir_audio(archivo)
    except cloudinary_service.CloudinaryError:
        flash("No se pudo subir la música: se conserva la anterior.", "error")
        return
    expo.musica_public_id = public_id
    expo.musica_url = url
    cloudinary_service.eliminar_audio(anterior)  # limpia la pista antigua


@bp.get("/exposiciones")
@login_required
def exposiciones_list():
    exposiciones = (
        Exposicion.query.filter_by(usuario_id=current_user.id)
        .order_by(Exposicion.created_at.desc())
        .all()
    )
    return render_template(
        "admin/exposiciones_list.html",
        exposiciones=exposiciones,
        ESTADO_PUBLICADA=ESTADO_PUBLICADA,
    )


@bp.route("/exposiciones/nueva", methods=["GET", "POST"])
@login_required
def exposicion_nueva():
    form = ExposicionForm()
    if form.validate_on_submit():
        base = slugify(form.slug.data or form.titulo.data)
        expo = Exposicion(
            usuario_id=current_user.id,
            titulo=form.titulo.data.strip(),
            slug=_slug_unico(base),
            descripcion=form.descripcion.data or None,
            fecha_inicio=form.fecha_inicio.data,
            fecha_fin=form.fecha_fin.data,
            estado=ESTADO_BORRADOR,
        )
        if _aplicar_visibilidad(expo, form):
            _aplicar_musica(expo, form)
            db.session.add(expo)
            db.session.commit()
            flash("Exposición creada.", "info")
            return redirect(url_for("admin.exposiciones_list"))
    return render_template(
        "admin/exposicion_form.html", form=form, titulo="Nueva exposición"
    )


@bp.route("/exposiciones/<int:exposicion_id>/editar", methods=["GET", "POST"])
@login_required
def exposicion_editar(exposicion_id):
    expo = db.get_or_404(Exposicion, exposicion_id)
    exigir_acceso_exposicion(expo)
    form = ExposicionForm(obj=expo)
    if form.validate_on_submit() and _aplicar_visibilidad(expo, form):
        expo.titulo = form.titulo.data.strip()
        base = slugify(form.slug.data or form.titulo.data)
        expo.slug = _slug_unico(base, exclude_id=expo.id)
        expo.descripcion = form.descripcion.data or None
        expo.fecha_inicio = form.fecha_inicio.data
        expo.fecha_fin = form.fecha_fin.data
        _aplicar_musica(expo, form)
        db.session.commit()
        flash("Exposición actualizada.", "info")
        return redirect(url_for("admin.exposiciones_list"))
    return render_template(
        "admin/exposicion_form.html",
        form=form,
        titulo=f"Editar: {expo.titulo}",
        tiene_musica=bool(expo.musica_url),
    )


@bp.post("/exposiciones/<int:exposicion_id>/publicar")
@login_required
def exposicion_publicar(exposicion_id):
    expo = db.get_or_404(Exposicion, exposicion_id)
    exigir_acceso_exposicion(expo)
    # Cada organizador publica sus exposiciones de forma independiente.
    expo.estado = ESTADO_PUBLICADA
    db.session.commit()
    flash(f"«{expo.titulo}» está publicada.", "info")
    return redirect(url_for("admin.exposiciones_list"))


@bp.post("/exposiciones/<int:exposicion_id>/despublicar")
@login_required
def exposicion_despublicar(exposicion_id):
    expo = db.get_or_404(Exposicion, exposicion_id)
    exigir_acceso_exposicion(expo)
    expo.estado = ESTADO_BORRADOR
    db.session.commit()
    flash(f"«{expo.titulo}» pasó a borrador.", "info")
    return redirect(url_for("admin.exposiciones_list"))


@bp.post("/exposiciones/<int:exposicion_id>/cerrar")
@login_required
def exposicion_cerrar(exposicion_id):
    expo = db.get_or_404(Exposicion, exposicion_id)
    exigir_acceso_exposicion(expo)
    expo.cerrada_manual = True
    db.session.commit()
    flash(f"«{expo.titulo}» está cerrada: su card se ve pero nadie puede entrar.", "info")
    return redirect(url_for("admin.exposiciones_list"))


@bp.post("/exposiciones/<int:exposicion_id>/reabrir")
@login_required
def exposicion_reabrir(exposicion_id):
    expo = db.get_or_404(Exposicion, exposicion_id)
    exigir_acceso_exposicion(expo)
    expo.cerrada_manual = False
    db.session.commit()
    if expo.apertura == APERTURA_CERRADA:
        flash(
            f"«{expo.titulo}» ya no está cerrada a mano, pero su fecha de fin "
            "ya pasó: amplía las fechas para reabrirla.",
            "error",
        )
    else:
        flash(f"«{expo.titulo}» reabierta.", "info")
    return redirect(url_for("admin.exposiciones_list"))


@bp.post("/exposiciones/<int:exposicion_id>/borrar")
@login_required
def exposicion_borrar(exposicion_id):
    expo = db.get_or_404(Exposicion, exposicion_id)
    exigir_acceso_exposicion(expo)
    musica_public_id = expo.musica_public_id
    db.session.delete(expo)
    db.session.commit()
    cloudinary_service.eliminar_audio(musica_public_id)  # pista huérfana
    flash("Exposición borrada.", "info")
    return redirect(url_for("admin.exposiciones_list"))


@bp.get("/exposiciones/<int:exposicion_id>")
@login_required
def exposicion_detail(exposicion_id):
    expo = db.get_or_404(Exposicion, exposicion_id)
    exigir_acceso_exposicion(expo)
    return render_template(
        "admin/exposicion_detail.html",
        expo=expo,
        ESTADO_PUBLICADA=ESTADO_PUBLICADA,
        nombre_plantilla=nombre_plantilla,
    )


# --------------------------------------------------------------------------
# Salas (dentro de una exposición)
# --------------------------------------------------------------------------
@bp.route("/exposiciones/<int:exposicion_id>/salas/nueva", methods=["GET", "POST"])
@login_required
def sala_nueva(exposicion_id):
    expo = db.get_or_404(Exposicion, exposicion_id)
    exigir_acceso_exposicion(expo)
    form = SalaForm()
    form.plantilla_3d.choices = opciones_plantilla()
    if request.method == "GET":
        form.orden.data = len(expo.salas)
    if form.validate_on_submit():
        sala = Sala(
            exposicion=expo,
            nombre=form.nombre.data.strip(),
            plantilla_3d=form.plantilla_3d.data,
            orden=form.orden.data or 0,
        )
        sembrar_zonas(sala)
        db.session.add(sala)
        db.session.commit()
        flash(f"Sala «{sala.nombre}» creada con {len(sala.zonas)} zonas.", "info")
        return redirect(url_for("admin.exposicion_detail", exposicion_id=expo.id))
    return render_template(
        "admin/sala_form.html", form=form, expo=expo, titulo="Nueva sala", es_nueva=True
    )


@bp.route("/salas/<int:sala_id>/editar", methods=["GET", "POST"])
@login_required
def sala_editar(sala_id):
    sala = db.get_or_404(Sala, sala_id)
    exigir_acceso_exposicion(sala.exposicion)
    form = SalaForm(obj=sala)
    # La plantilla no se cambia tras crear la sala (las zonas ya están sembradas).
    form.plantilla_3d.choices = [(sala.plantilla_3d, nombre_plantilla(sala.plantilla_3d))]
    if form.validate_on_submit():
        sala.nombre = form.nombre.data.strip()
        sala.orden = form.orden.data or 0
        db.session.commit()
        flash("Sala actualizada.", "info")
        return redirect(url_for("admin.exposicion_detail", exposicion_id=sala.exposicion_id))
    return render_template(
        "admin/sala_form.html",
        form=form,
        expo=sala.exposicion,
        titulo=f"Editar: {sala.nombre}",
        es_nueva=False,
        plantilla_actual=nombre_plantilla(sala.plantilla_3d),
    )


@bp.get("/salas/<int:sala_id>")
@login_required
def sala_detail(sala_id):
    sala = db.get_or_404(Sala, sala_id)
    exigir_acceso_exposicion(sala.exposicion)
    return render_template(
        "admin/sala_detail.html", sala=sala, nombre_plantilla=nombre_plantilla
    )


@bp.post("/salas/<int:sala_id>/borrar")
@login_required
def sala_borrar(sala_id):
    sala = db.get_or_404(Sala, sala_id)
    exigir_acceso_exposicion(sala.exposicion)
    exposicion_id = sala.exposicion_id
    db.session.delete(sala)
    db.session.commit()
    flash("Sala borrada.", "info")
    return redirect(url_for("admin.exposicion_detail", exposicion_id=exposicion_id))


# --------------------------------------------------------------------------
# Obras (colgadas en una zona)
# --------------------------------------------------------------------------
def _siguiente_hueco(zona) -> int:
    """Primer orden libre en la zona dentro de su capacidad."""
    ocupados = {o.orden for o in zona.obras}
    for i in range(zona.capacidad):
        if i not in ocupados:
            return i
    return len(zona.obras)  # no debería alcanzarse (la capacidad se valida antes)


@bp.route("/zonas/<int:zona_id>/obras/nueva", methods=["GET", "POST"])
@login_required
def obra_nueva(zona_id):
    zona = db.get_or_404(Zona, zona_id)
    exigir_acceso_exposicion(zona.sala.exposicion)
    if len(zona.obras) >= zona.capacidad:
        flash("La zona está completa.", "error")
        return redirect(url_for("admin.sala_detail", sala_id=zona.sala_id))

    autores = (
        Autor.query.filter_by(usuario_id=current_user.id)
        .order_by(Autor.nombre)
        .all()
    )
    if not autores:
        flash("Crea al menos un autor antes de colgar obras.", "error")
        return redirect(url_for("admin.autor_nuevo"))

    form = ObraForm()
    form.autor_id.choices = [(a.id, a.nombre) for a in autores]
    zona_mixta = zona.tipo_admitido == TIPO_MIXTO

    if form.validate_on_submit():
        obra = Obra(
            zona=zona,
            autor_id=form.autor_id.data,
            titulo=form.titulo.data.strip(),
            tipo=form.tipo.data if zona_mixta else zona.tipo_admitido,
            anio=form.anio.data,
            tecnica=form.tecnica.data or None,
            ancho_cm=form.ancho_cm.data,
            alto_cm=form.alto_cm.data,
            descripcion=form.descripcion.data or None,
            orden=_siguiente_hueco(zona),
            cloudinary_url=PLACEHOLDER_IMAGEN,
        )
        archivo = form.imagen.data
        if archivo:
            if cloudinary_service.esta_configurado():
                try:
                    public_id, url = cloudinary_service.subir_imagen(archivo)
                    obra.cloudinary_public_id = public_id
                    obra.cloudinary_url = url
                except cloudinary_service.CloudinaryError:
                    flash("No se pudo subir la imagen: se mantiene el placeholder.", "error")
            else:
                flash("Cloudinary no está configurado: se mantiene el placeholder.", "error")
        db.session.add(obra)
        db.session.commit()
        flash(f"Obra «{obra.titulo}» colgada.", "info")
        return redirect(url_for("admin.sala_detail", sala_id=zona.sala_id))

    return render_template(
        "admin/obra_form.html",
        form=form,
        zona=zona,
        zona_mixta=zona_mixta,
        titulo="Colgar obra",
        es_nueva=True,
        imagen_actual=None,
    )


@bp.route("/obras/<int:obra_id>/editar", methods=["GET", "POST"])
@login_required
def obra_editar(obra_id):
    obra = db.get_or_404(Obra, obra_id)
    zona = obra.zona
    exigir_acceso_exposicion(zona.sala.exposicion)
    autores = (
        Autor.query.filter_by(usuario_id=current_user.id)
        .order_by(Autor.nombre)
        .all()
    )
    form = ObraForm(obj=obra)
    form.autor_id.choices = [(a.id, a.nombre) for a in autores]
    zona_mixta = zona.tipo_admitido == TIPO_MIXTO

    if form.validate_on_submit():
        obra.titulo = form.titulo.data.strip()
        obra.autor_id = form.autor_id.data
        if zona_mixta:
            obra.tipo = form.tipo.data
        obra.anio = form.anio.data
        obra.tecnica = form.tecnica.data or None
        obra.ancho_cm = form.ancho_cm.data
        obra.alto_cm = form.alto_cm.data
        obra.descripcion = form.descripcion.data or None

        archivo = form.imagen.data
        if archivo:
            if cloudinary_service.esta_configurado():
                anterior = obra.cloudinary_public_id
                try:
                    public_id, url = cloudinary_service.subir_imagen(archivo)
                    obra.cloudinary_public_id = public_id
                    obra.cloudinary_url = url
                    cloudinary_service.eliminar_imagen(anterior)  # limpia la antigua
                except cloudinary_service.CloudinaryError:
                    flash("No se pudo subir la imagen: se conserva la anterior.", "error")
            else:
                flash("Cloudinary no está configurado: la imagen no se actualizó.", "error")

        db.session.commit()
        flash("Obra actualizada.", "info")
        return redirect(url_for("admin.sala_detail", sala_id=zona.sala_id))

    return render_template(
        "admin/obra_form.html",
        form=form,
        zona=zona,
        zona_mixta=zona_mixta,
        titulo=f"Editar: {obra.titulo}",
        es_nueva=False,
        imagen_actual=obra.cloudinary_url,
    )


@bp.post("/obras/<int:obra_id>/portada")
@login_required
def obra_portada(obra_id):
    """Marca la obra como portada de la card de su exposición en el portal
    (o la desmarca si ya lo era)."""
    obra = db.get_or_404(Obra, obra_id)
    expo = obra.zona.sala.exposicion
    exigir_acceso_exposicion(expo)
    if expo.portada_obra_id == obra.id:
        expo.portada_obra_id = None
        flash("Portada quitada: la card vuelve al logo o a la primera obra.", "info")
    else:
        expo.portada_obra_id = obra.id
        flash(f"«{obra.titulo}» es ahora la portada de la exposición.", "info")
    db.session.commit()
    return redirect(url_for("admin.sala_detail", sala_id=obra.zona.sala_id))


@bp.post("/obras/<int:obra_id>/borrar")
@login_required
def obra_borrar(obra_id):
    obra = db.get_or_404(Obra, obra_id)
    expo = obra.zona.sala.exposicion
    exigir_acceso_exposicion(expo)
    sala_id = obra.zona.sala_id
    public_id = obra.cloudinary_public_id
    if expo.portada_obra_id == obra.id:
        expo.portada_obra_id = None  # la portada no puede apuntar a una obra retirada
    db.session.delete(obra)
    db.session.commit()
    if public_id and cloudinary_service.esta_configurado():
        cloudinary_service.eliminar_imagen(public_id)  # borra la imagen huérfana
    flash("Obra retirada.", "info")
    return redirect(url_for("admin.sala_detail", sala_id=sala_id))


# --------------------------------------------------------------------------
# Carga múltiple de obras (subida directa navegador → Cloudinary)
# --------------------------------------------------------------------------
def _huecos_libres(sala, tipo):
    """(zona, orden) libres que admiten `tipo`, en orden de recorrido."""
    huecos = []
    for zona in sala.zonas:  # ya vienen ordenadas por Zona.orden
        if zona.tipo_admitido not in (tipo, TIPO_MIXTO):
            continue
        ocupados = {o.orden for o in zona.obras}
        for i in range(zona.capacidad):
            if i not in ocupados:
                huecos.append((zona, i))
    return huecos


@bp.get("/salas/<int:sala_id>/obras/subir")
@login_required
def obras_subir_form(sala_id):
    sala = db.get_or_404(Sala, sala_id)
    exigir_acceso_exposicion(sala.exposicion)
    autores = (
        Autor.query.filter_by(usuario_id=current_user.id)
        .order_by(Autor.nombre)
        .all()
    )
    return render_template(
        "admin/obras_bulk.html",
        sala=sala,
        autores=autores,
        libres_dibujo=len(_huecos_libres(sala, TIPO_DIBUJO)),
        libres_cuadro=len(_huecos_libres(sala, TIPO_CUADRO)),
        cloudinary_ok=cloudinary_service.esta_configurado(),
    )


@bp.get("/cloudinary/firma")
@login_required
def cloudinary_firma():
    """Devuelve la firma para subir directamente a Cloudinary desde el navegador."""
    if not cloudinary_service.esta_configurado():
        return {"error": "Cloudinary no está configurado en el servidor."}, 400
    return cloudinary_service.firmar_subida()


@bp.post("/salas/<int:sala_id>/obras/subir")
@login_required
def obras_subir(sala_id):
    """Crea en lote las obras ya subidas a Cloudinary por el navegador.
    Recibe JSON con el autor, el tipo y la lista de imágenes (public_id/url)."""
    sala = db.get_or_404(Sala, sala_id)
    exigir_acceso_exposicion(sala.exposicion)

    data = request.get_json(silent=True) or {}
    tipo = data.get("tipo")
    if tipo not in (TIPO_DIBUJO, TIPO_CUADRO):
        return {"error": "Tipo inválido."}, 400
    imagenes = data.get("imagenes") or []
    if not imagenes:
        return {"error": "No se recibió ninguna imagen."}, 400

    # Autor: nuevo (por nombre) o uno propio existente.
    nombre_nuevo = (data.get("autor_nuevo") or "").strip()
    if nombre_nuevo:
        autor = Autor(usuario_id=current_user.id, nombre=nombre_nuevo[:160])
        db.session.add(autor)
        db.session.flush()
    else:
        try:
            autor = db.session.get(Autor, int(data.get("autor_id")))
        except (TypeError, ValueError):
            autor = None
        if autor is None or autor.usuario_id != current_user.id:
            return {"error": "Elige un autor válido o crea uno nuevo."}, 400

    huecos = _huecos_libres(sala, tipo)
    ancho, alto = (29.7, 42.0) if tipo == TIPO_DIBUJO else (100.0, 80.0)
    creadas = 0
    sin_hueco = []
    for img in imagenes:
        public_id = img.get("public_id")
        url = img.get("secure_url")
        nombre = (img.get("filename") or "Obra").rsplit(".", 1)[0].strip() or "Obra"
        if not public_id or not url:
            continue
        if creadas >= len(huecos):
            sin_hueco.append(nombre)
            continue
        zona, orden = huecos[creadas]
        db.session.add(
            Obra(
                zona=zona,
                autor=autor,
                titulo=nombre[:200],
                tipo=tipo,
                ancho_cm=ancho,
                alto_cm=alto,
                orden=orden,
                cloudinary_public_id=public_id,
                cloudinary_url=url,
            )
        )
        creadas += 1

    db.session.commit()
    return {"creadas": creadas, "sin_hueco": sin_hueco, "autor": autor.nombre}
