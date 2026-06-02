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

from backend.app.extensions import db
from backend.app.forms import AutorForm, ExposicionForm, ObraForm, SalaForm
from backend.app.models import Autor, Exposicion, Obra, Sala, Usuario, Zona
from backend.app.models.exposicion import ESTADO_BORRADOR, ESTADO_PUBLICADA
from backend.app.models.obra import PLACEHOLDER_IMAGEN
from backend.app.models.zona import TIPO_MIXTO
from backend.app.plantillas import (
    nombre_plantilla,
    opciones_plantilla,
    sembrar_zonas,
)
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


@bp.get("/login")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))
    return render_template("admin/login.html")


@bp.post("/login")
def login_post():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    usuario = Usuario.query.filter_by(email=email).first()
    if usuario is not None and usuario.check_password(password):
        login_user(usuario)
        siguiente = request.args.get("next")
        if _es_url_segura(siguiente):
            return redirect(siguiente)
        return redirect(url_for("admin.dashboard"))

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
    return render_template("admin/dashboard.html")


# --------------------------------------------------------------------------
# Autores
# --------------------------------------------------------------------------
@bp.get("/autores")
@login_required
def autores_list():
    autores = Autor.query.order_by(Autor.nombre).all()
    return render_template("admin/autores_list.html", autores=autores)


@bp.route("/autores/nuevo", methods=["GET", "POST"])
@login_required
def autor_nuevo():
    form = AutorForm()
    if form.validate_on_submit():
        autor = Autor(
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


@bp.get("/exposiciones")
@login_required
def exposiciones_list():
    exposiciones = Exposicion.query.order_by(Exposicion.created_at.desc()).all()
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
            titulo=form.titulo.data.strip(),
            slug=_slug_unico(base),
            descripcion=form.descripcion.data or None,
            fecha_inicio=form.fecha_inicio.data,
            fecha_fin=form.fecha_fin.data,
            estado=ESTADO_BORRADOR,
        )
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
    form = ExposicionForm(obj=expo)
    if form.validate_on_submit():
        expo.titulo = form.titulo.data.strip()
        base = slugify(form.slug.data or form.titulo.data)
        expo.slug = _slug_unico(base, exclude_id=expo.id)
        expo.descripcion = form.descripcion.data or None
        expo.fecha_inicio = form.fecha_inicio.data
        expo.fecha_fin = form.fecha_fin.data
        db.session.commit()
        flash("Exposición actualizada.", "info")
        return redirect(url_for("admin.exposiciones_list"))
    return render_template(
        "admin/exposicion_form.html", form=form, titulo=f"Editar: {expo.titulo}"
    )


@bp.post("/exposiciones/<int:exposicion_id>/publicar")
@login_required
def exposicion_publicar(exposicion_id):
    expo = db.get_or_404(Exposicion, exposicion_id)
    # Solo una publicada a la vez: despublica las demás.
    Exposicion.query.filter(
        Exposicion.id != expo.id, Exposicion.estado == ESTADO_PUBLICADA
    ).update({"estado": ESTADO_BORRADOR})
    expo.estado = ESTADO_PUBLICADA
    db.session.commit()
    flash(f"«{expo.titulo}» es ahora la exposición publicada.", "info")
    return redirect(url_for("admin.exposiciones_list"))


@bp.post("/exposiciones/<int:exposicion_id>/despublicar")
@login_required
def exposicion_despublicar(exposicion_id):
    expo = db.get_or_404(Exposicion, exposicion_id)
    expo.estado = ESTADO_BORRADOR
    db.session.commit()
    flash(f"«{expo.titulo}» pasó a borrador.", "info")
    return redirect(url_for("admin.exposiciones_list"))


@bp.post("/exposiciones/<int:exposicion_id>/borrar")
@login_required
def exposicion_borrar(exposicion_id):
    expo = db.get_or_404(Exposicion, exposicion_id)
    db.session.delete(expo)
    db.session.commit()
    flash("Exposición borrada.", "info")
    return redirect(url_for("admin.exposiciones_list"))


@bp.get("/exposiciones/<int:exposicion_id>")
@login_required
def exposicion_detail(exposicion_id):
    expo = db.get_or_404(Exposicion, exposicion_id)
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
    return render_template(
        "admin/sala_detail.html", sala=sala, nombre_plantilla=nombre_plantilla
    )


@bp.post("/salas/<int:sala_id>/borrar")
@login_required
def sala_borrar(sala_id):
    sala = db.get_or_404(Sala, sala_id)
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
    if len(zona.obras) >= zona.capacidad:
        flash("La zona está completa.", "error")
        return redirect(url_for("admin.sala_detail", sala_id=zona.sala_id))

    autores = Autor.query.order_by(Autor.nombre).all()
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
    )


@bp.route("/obras/<int:obra_id>/editar", methods=["GET", "POST"])
@login_required
def obra_editar(obra_id):
    obra = db.get_or_404(Obra, obra_id)
    zona = obra.zona
    autores = Autor.query.order_by(Autor.nombre).all()
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
    )


@bp.post("/obras/<int:obra_id>/borrar")
@login_required
def obra_borrar(obra_id):
    obra = db.get_or_404(Obra, obra_id)
    sala_id = obra.zona.sala_id
    db.session.delete(obra)
    db.session.commit()
    flash("Obra retirada.", "info")
    return redirect(url_for("admin.sala_detail", sala_id=sala_id))
