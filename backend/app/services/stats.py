"""Estadísticas de visitas para el panel de plataforma.

Las cuentas se obtienen con agregados SQL (GROUP BY) en una sola consulta por
ventana temporal, en vez de recorrer las relaciones en Python."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import func

from backend.app.extensions import db
from backend.app.models import Exposicion, Usuario, Visita
from backend.app.models.exposicion import ESTADO_PUBLICADA
from backend.app.models.usuario import ROL_ORGANIZADOR


def _desde(dias: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=dias)


def _conteos(dias=None) -> dict:
    """{exposicion_id: nº visitas}, opcionalmente en los últimos `dias`."""
    q = db.session.query(Visita.exposicion_id, func.count(Visita.id))
    if dias is not None:
        q = q.filter(Visita.created_at >= _desde(dias))
    return dict(q.group_by(Visita.exposicion_id).all())


def resumen_plataforma() -> dict:
    """KPIs de cabecera del dashboard de plataforma."""
    return {
        "organizadores": Usuario.query.filter_by(rol=ROL_ORGANIZADOR).count(),
        "organizadores_activos": Usuario.query.filter_by(
            rol=ROL_ORGANIZADOR, activo=True
        ).count(),
        "exposiciones": Exposicion.query.count(),
        "publicadas": Exposicion.query.filter_by(estado=ESTADO_PUBLICADA).count(),
        "visitas_total": Visita.query.count(),
        "visitas_7d": Visita.query.filter(Visita.created_at >= _desde(7)).count(),
    }


def exposiciones_con_visitas() -> list:
    """Todas las exposiciones con su nº de visitas (total y últimos 7 días),
    ordenadas de más a menos visitadas."""
    totales = _conteos()
    recientes = _conteos(7)
    filas = [
        {
            "exposicion": expo,
            "total": totales.get(expo.id, 0),
            "recientes": recientes.get(expo.id, 0),
        }
        for expo in Exposicion.query.all()
    ]
    filas.sort(key=lambda f: f["total"], reverse=True)
    return filas
