from flask import Blueprint, render_template

from backend.app.models import Exposicion
from backend.app.models.exposicion import ESTADO_PUBLICADA
from backend.app.services.gallery import serializar_sala

bp = Blueprint("main", __name__)


@bp.get("/")
def index():
    return render_template("index.html")


@bp.get("/gallery")
def gallery():
    """Muestra en 3D la primera sala (por orden) de la exposición publicada.
    Si no hay exposición publicada o no tiene salas, `datos` es None y la
    plantilla muestra un aviso."""
    expo = Exposicion.query.filter_by(estado=ESTADO_PUBLICADA).first()
    datos = None
    if expo is not None and expo.salas:
        datos = serializar_sala(expo.salas[0])
    return render_template("gallery.html", datos=datos)
