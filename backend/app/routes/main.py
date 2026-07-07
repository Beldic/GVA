from flask import Blueprint, render_template, session

from backend.app.extensions import db
from backend.app.models import Exposicion, Visita
from backend.app.models.exposicion import ESTADO_PUBLICADA
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


@bp.get("/")
def index():
    """Portal: rejilla de galerías abiertas (todas las exposiciones publicadas),
    cada una con enlace a su recorrido en 3D."""
    publicadas = (
        Exposicion.query.filter_by(estado=ESTADO_PUBLICADA)
        .order_by(Exposicion.created_at.desc())
        .all()
    )
    galerias = [resumen_exposicion(expo) for expo in publicadas]
    return render_template("index.html", galerias=galerias)


@bp.get("/g/<slug>")
def gallery(slug):
    """Muestra en 3D la primera sala (por orden) de la exposición publicada con
    ese slug. Solo se sirven exposiciones publicadas; si no tiene salas, `datos`
    es None y la plantilla avisa."""
    expo = Exposicion.query.filter_by(
        slug=slug, estado=ESTADO_PUBLICADA
    ).first_or_404()
    _registrar_visita(expo)
    datos = serializar_sala(expo.salas[0]) if expo.salas else None
    return render_template("gallery.html", datos=datos)
