from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user

from backend.app.extensions import db
from backend.app.models import Exposicion, Visita
from backend.app.models.exposicion import ESTADO_PUBLICADA, VISIBILIDAD_ENLACE
from backend.app.services.gallery import resumen_exposicion, serializar_sala

bp = Blueprint("main", __name__)


def _registrar_visita(expo) -> None:
    """Cuenta una visita por exposición y sesión de navegador: recargar la
    página no vuelve a sumar."""
    vistas = session.get("expos_vistas", [])
    if expo.id in vistas:
        return
    db.session.add(Visita(exposicion_id=expo.id))
    db.session.commit()
    session["expos_vistas"] = vistas + [expo.id]


def _puede_gestionar(expo) -> bool:
    """El dueño de la exposición y el superadmin entran siempre (previsualizan
    aunque esté cerrada o pida código), sin sumar visitas."""
    return current_user.is_authenticated and (
        current_user.es_superadmin or expo.usuario_id == current_user.id
    )


def _visitante_autorizado(expo) -> bool:
    """El visitante ya introdujo el código correcto en esta sesión de navegador."""
    return expo.id in session.get("expos_autorizadas", [])


def _autorizar_visitante(expo) -> None:
    autorizadas = session.get("expos_autorizadas", [])
    if expo.id not in autorizadas:
        session["expos_autorizadas"] = autorizadas + [expo.id]


@bp.get("/")
def index():
    """Portal: rejilla de galerías publicadas, cada card con su estado de
    apertura (abierta/próximamente/cerrada) y candado si pide código. Solo
    las de enlace secreto quedan fuera del listado."""
    publicadas = (
        Exposicion.query.filter(
            Exposicion.estado == ESTADO_PUBLICADA,
            Exposicion.visibilidad != VISIBILIDAD_ENLACE,
        )
        .order_by(Exposicion.created_at.desc())
        .all()
    )
    galerias = [resumen_exposicion(expo) for expo in publicadas]
    return render_template("index.html", galerias=galerias)


@bp.get("/g/<slug>")
def gallery(slug):
    """Muestra en 3D la primera sala (por orden) de la exposición publicada
    con ese slug. Para el visitante anónimo hay dos puertas: la exposición
    debe estar abierta (fechas/cierre manual) y, si pide código, haberlo
    introducido. El dueño y el superadmin entran siempre. Si no tiene salas,
    `datos` es None y la plantilla avisa."""
    expo = Exposicion.query.filter_by(
        slug=slug, estado=ESTADO_PUBLICADA
    ).first_or_404()
    if not _puede_gestionar(expo):
        if not expo.abierta:
            return render_template("gallery_cerrada.html", expo=expo)
        if expo.requiere_codigo and not _visitante_autorizado(expo):
            return render_template("gallery_codigo.html", expo=expo)
        _registrar_visita(expo)
    datos = serializar_sala(expo.salas[0]) if expo.salas else None
    return render_template("gallery.html", datos=datos)


@bp.post("/g/<slug>/codigo")
def gallery_codigo(slug):
    """Valida el código de acceso de una exposición privada y recuerda la
    autorización en la sesión del navegador (el visitante sigue anónimo)."""
    expo = Exposicion.query.filter_by(
        slug=slug, estado=ESTADO_PUBLICADA
    ).first_or_404()
    codigo = (request.form.get("codigo") or "").strip()
    if expo.requiere_codigo and expo.check_codigo_acceso(codigo):
        _autorizar_visitante(expo)
    else:
        flash("Código incorrecto. Vuelve a intentarlo.", "error")
    return redirect(url_for("main.gallery", slug=slug))
