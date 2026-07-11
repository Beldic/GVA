"""Estadísticas de visitas para los paneles de plataforma y organizador.

Las cuentas de plataforma se obtienen con agregados SQL (GROUP BY). Las del
organizador se calculan en Python sobre una única consulta de sus visitas:
volúmenes pequeños, portabilidad SQLite/Postgres (strftime vs extract) y
conversión de zona horaria fila a fila."""
from collections import Counter
from datetime import datetime, timedelta, timezone

from sqlalchemy import func

from backend.app.extensions import db
from backend.app.models import Exposicion, Usuario, Visita
from backend.app.models.exposicion import ESTADO_PUBLICADA
from backend.app.models.usuario import ROL_ORGANIZADOR

try:
    from zoneinfo import ZoneInfo

    TZ_LOCAL = ZoneInfo("Europe/Madrid")
except Exception:  # sin base de datos tz (Windows sin tzdata): se queda en UTC
    TZ_LOCAL = timezone.utc

DIAS_SEMANA = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
FRANJAS = [
    ("Mañana", 7, 14),      # 07:00–13:59
    ("Tarde", 14, 21),      # 14:00–20:59
    ("Noche", 21, 24),      # 21:00–23:59
    ("Madrugada", 0, 7),    # 00:00–06:59
]


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


# --------------------------------------------------------------------------
# Panel del organizador
# --------------------------------------------------------------------------
def _hora_local(dt: datetime) -> datetime:
    """created_at en hora española (los agregados de día/franja se hacen en
    la zona del público, no en UTC). SQLite devuelve datetimes naive: son UTC."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(TZ_LOCAL)


def panel_organizador(usuario_id: int) -> dict:
    """Todos los datos del dashboard del organizador en una pasada: KPIs,
    serie diaria (30 días), frecuencia por día de semana y franja horaria,
    desgloses móvil/escritorio y 3D/2D, y visitas por exposición."""
    expos = (
        Exposicion.query.filter_by(usuario_id=usuario_id)
        .order_by(Exposicion.created_at.desc())
        .all()
    )
    ids = [e.id for e in expos]
    visitas = (
        Visita.query.filter(Visita.exposicion_id.in_(ids)).all() if ids else []
    )

    hoy = datetime.now(timezone.utc).astimezone(TZ_LOCAL).date()
    hace_7 = hoy - timedelta(days=6)
    hace_30 = hoy - timedelta(days=29)

    por_dia = Counter()
    por_semana = Counter()
    por_franja = Counter()
    por_dispositivo = Counter()
    por_modo = Counter()
    por_expo_total = Counter()
    por_expo_7d = Counter()
    total_7d = total_30d = 0

    for v in visitas:
        local = _hora_local(v.created_at)
        dia = local.date()
        por_expo_total[v.exposicion_id] += 1
        por_dispositivo[v.dispositivo or "desconocido"] += 1
        por_modo[v.modo or "desconocido"] += 1
        por_semana[local.weekday()] += 1
        for nombre, desde, hasta in FRANJAS:
            if desde <= local.hour < hasta:
                por_franja[nombre] += 1
                break
        if dia >= hace_30:
            total_30d += 1
            por_dia[dia] += 1
        if dia >= hace_7:
            total_7d += 1
            por_expo_7d[v.exposicion_id] += 1

    serie = [
        {"fecha": d, "visitas": por_dia.get(d, 0)}
        for d in (hace_30 + timedelta(days=i) for i in range(30))
    ]
    return {
        "kpis": {
            "visitas_total": len(visitas),
            "visitas_7d": total_7d,
            "visitas_30d": total_30d,
            "publicadas": sum(1 for e in expos if e.estado == ESTADO_PUBLICADA),
            "abiertas": sum(
                1 for e in expos if e.estado == ESTADO_PUBLICADA and e.abierta
            ),
            "exposiciones": len(expos),
        },
        "serie_diaria": serie,
        "max_dia": max((p["visitas"] for p in serie), default=0),
        "semana": [
            {"dia": DIAS_SEMANA[i], "visitas": por_semana.get(i, 0)}
            for i in range(7)
        ],
        "franjas": [
            {"franja": nombre, "visitas": por_franja.get(nombre, 0)}
            for nombre, _, _ in FRANJAS
        ],
        "dispositivos": dict(por_dispositivo),
        "modos": dict(por_modo),
        "expos": [
            {
                "exposicion": e,
                "total": por_expo_total.get(e.id, 0),
                "recientes": por_expo_7d.get(e.id, 0),
            }
            for e in expos
        ],
    }
