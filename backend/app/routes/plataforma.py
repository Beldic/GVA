"""Panel de plataforma (superadmin): organizadores + estadísticas de visitas.

Todo el blueprint exige sesión de superadmin (ver `_requiere_superadmin`). Los
organizadores usan `/admin`; aquí no entran (403).
"""
import secrets

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user

from backend.app.extensions import db
from backend.app.forms import OrganizadorEditForm, OrganizadorForm
from backend.app.models import Exposicion, Usuario
from backend.app.models.usuario import ROL_ORGANIZADOR
from backend.app.services import stats

bp = Blueprint("plataforma", __name__, url_prefix="/plataforma")


@bp.before_request
def _requiere_superadmin():
    """Verja del panel: solo superadmin. Anónimo -> login; organizador -> 403."""
    if not current_user.is_authenticated:
        return current_app.login_manager.unauthorized()
    if not current_user.es_superadmin:
        abort(403)


def _contrasena_temporal() -> str:
    return secrets.token_urlsafe(9)


# --------------------------------------------------------------------------
# Dashboard
# --------------------------------------------------------------------------
@bp.get("/")
def dashboard():
    return render_template(
        "plataforma/dashboard.html",
        resumen=stats.resumen_plataforma(),
        top=stats.exposiciones_con_visitas()[:5],
    )


# --------------------------------------------------------------------------
# Organizadores
# --------------------------------------------------------------------------
@bp.get("/organizadores")
def organizadores_list():
    organizadores = (
        Usuario.query.filter_by(rol=ROL_ORGANIZADOR)
        .order_by(Usuario.created_at.desc())
        .all()
    )
    return render_template(
        "plataforma/organizadores_list.html", organizadores=organizadores
    )


@bp.route("/organizadores/nuevo", methods=["GET", "POST"])
def organizador_nuevo():
    form = OrganizadorForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        if Usuario.query.filter_by(email=email).first() is not None:
            flash("Ya existe una cuenta con ese email.", "error")
            return render_template(
                "plataforma/organizador_form.html", form=form, titulo="Nuevo organizador"
            )
        password = form.password.data or _contrasena_temporal()
        organizador = Usuario(
            email=email,
            nombre=form.nombre.data.strip() or None,
            rol=ROL_ORGANIZADOR,
            activo=True,
        )
        organizador.set_password(password)
        db.session.add(organizador)
        db.session.commit()
        if form.password.data:
            flash(f"Organizador «{email}» creado.", "info")
        else:
            flash(
                f"Organizador «{email}» creado. Contraseña temporal: {password} "
                "(cópiala ahora: no se volverá a mostrar).",
                "info",
            )
        return redirect(url_for("plataforma.organizadores_list"))
    return render_template(
        "plataforma/organizador_form.html", form=form, titulo="Nuevo organizador"
    )


@bp.route("/organizadores/<int:usuario_id>/editar", methods=["GET", "POST"])
def organizador_editar(usuario_id):
    organizador = _get_organizador(usuario_id)
    form = OrganizadorEditForm(obj=organizador)
    if form.validate_on_submit():
        organizador.nombre = form.nombre.data.strip() or None
        organizador.activo = form.activo.data
        db.session.commit()
        flash("Organizador actualizado.", "info")
        return redirect(url_for("plataforma.organizadores_list"))
    return render_template(
        "plataforma/organizador_form.html",
        form=form,
        titulo=f"Editar: {organizador.email}",
        organizador=organizador,
        es_edicion=True,
    )


@bp.post("/organizadores/<int:usuario_id>/reset-password")
def organizador_reset_password(usuario_id):
    organizador = _get_organizador(usuario_id)
    password = _contrasena_temporal()
    organizador.set_password(password)
    db.session.commit()
    flash(
        f"Nueva contraseña de «{organizador.email}»: {password} "
        "(cópiala ahora: no se volverá a mostrar).",
        "info",
    )
    return redirect(url_for("plataforma.organizadores_list"))


@bp.post("/organizadores/<int:usuario_id>/borrar")
def organizador_borrar(usuario_id):
    organizador = _get_organizador(usuario_id)
    email = organizador.email
    db.session.delete(organizador)  # cascada: exposiciones, autores, salas, obras...
    db.session.commit()
    flash(f"Organizador «{email}» y todo su contenido borrados.", "info")
    return redirect(url_for("plataforma.organizadores_list"))


# --------------------------------------------------------------------------
# Exposiciones (visión transversal + reasignación de dueño)
# --------------------------------------------------------------------------
@bp.get("/exposiciones")
def exposiciones_list():
    exposiciones = Exposicion.query.order_by(Exposicion.created_at.desc()).all()
    organizadores = (
        Usuario.query.filter_by(rol=ROL_ORGANIZADOR, activo=True)
        .order_by(Usuario.nombre)
        .all()
    )
    return render_template(
        "plataforma/exposiciones_list.html",
        exposiciones=exposiciones,
        organizadores=organizadores,
    )


def _mover_autores(expo, origen_id, destino) -> tuple[list, list]:
    """Al reasignar una exposición, mueve con ella los autores de sus obras.
    Un autor solo se mueve si TODAS sus obras cuelgan en esta exposición; si
    también tiene obras en otras del dueño anterior, se queda (compartido) y
    se avisa. Devuelve (movidos, compartidos) por nombre."""
    obras_expo = {
        o.id for sala in expo.salas for zona in sala.zonas for o in zona.obras
    }
    autores = {
        o.autor for sala in expo.salas for zona in sala.zonas for o in zona.obras
    }
    movidos, compartidos = [], []
    for autor in autores:
        if autor.usuario_id != origen_id:
            continue
        if all(obra.id in obras_expo for obra in autor.obras):
            autor.usuario_id = destino.id
            movidos.append(autor.nombre)
        else:
            compartidos.append(autor.nombre)
    return movidos, compartidos


@bp.post("/exposiciones/<int:exposicion_id>/reasignar")
def exposicion_reasignar(exposicion_id):
    expo = db.get_or_404(Exposicion, exposicion_id)
    destino_id = request.form.get("usuario_id", type=int)
    if destino_id is None:
        flash("Elige el organizador de destino.", "error")
        return redirect(url_for("plataforma.exposiciones_list"))
    destino = _get_organizador(destino_id)
    if destino.id == expo.usuario_id:
        flash(f"«{expo.titulo}» ya pertenece a ese organizador.", "info")
        return redirect(url_for("plataforma.exposiciones_list"))

    origen_id = expo.usuario_id
    expo.usuario_id = destino.id
    movidos, compartidos = _mover_autores(expo, origen_id, destino)
    db.session.commit()

    quien = destino.nombre or destino.email
    msg = f"«{expo.titulo}» reasignada a {quien}."
    if movidos:
        msg += f" Autores movidos: {', '.join(sorted(movidos))}."
    flash(msg, "info")
    if compartidos:
        flash(
            "Estos autores NO se movieron porque tienen obras en otras "
            f"exposiciones del dueño anterior: {', '.join(sorted(compartidos))}.",
            "error",
        )
    return redirect(url_for("plataforma.exposiciones_list"))


# --------------------------------------------------------------------------
# Estadísticas
# --------------------------------------------------------------------------
@bp.get("/estadisticas")
def estadisticas():
    filas = stats.exposiciones_con_visitas()
    maximo = max((f["total"] for f in filas), default=0)
    return render_template(
        "plataforma/estadisticas.html",
        resumen=stats.resumen_plataforma(),
        filas=filas,
        maximo=maximo,
    )


def _get_organizador(usuario_id) -> Usuario:
    """Carga un usuario y garantiza que es un organizador (no otro superadmin)."""
    usuario = db.get_or_404(Usuario, usuario_id)
    if usuario.rol != ROL_ORGANIZADOR:
        abort(404)
    return usuario
