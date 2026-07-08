"""Plantillas de sala: definen la geometría 3D (por nombre) y las zonas que
trae cada una. Al crear una sala con una plantilla, sus zonas se siembran
automáticamente. El comisario no crea zonas a mano.

El `codigo` de cada zona coincide con el nombre de la pared en el frontend 3D
(room.js: far/near/left/right) para que el mapeo en la Fase 5 sea directo.
"""
from backend.app.models.zona import TIPO_CUADRO, TIPO_DIBUJO

PLANTILLAS = {
    "sala-clasica": {
        "nombre": "Sala clásica (4 paredes)",
        "descripcion": "Sala rectangular 8×6 m. Cuadros en las paredes anchas, "
        "dibujos en las laterales.",
        "zonas": [
            {"codigo": "far", "nombre": "Pared del fondo", "tipo_admitido": TIPO_CUADRO, "capacidad": 4, "orden": 0},
            {"codigo": "near", "nombre": "Pared de entrada", "tipo_admitido": TIPO_CUADRO, "capacidad": 3, "orden": 1},
            {"codigo": "left", "nombre": "Pared izquierda", "tipo_admitido": TIPO_DIBUJO, "capacidad": 8, "orden": 2},
            {"codigo": "right", "nombre": "Pared derecha", "tipo_admitido": TIPO_DIBUJO, "capacidad": 8, "orden": 3},
        ],
    },
    "sala-rectangular": {
        "nombre": "Sala rectangular grande (con puerta)",
        "descripcion": "Sala alargada 11×16 m con puerta de entrada. Cuadros al "
        "fondo y a ambos lados de la puerta; dibujos en las dos paredes laterales. "
        "Capacidad: 15 cuadros + 40 dibujos.",
        "zonas": [
            {"codigo": "far", "nombre": "Pared del fondo", "tipo_admitido": TIPO_CUADRO, "capacidad": 8, "orden": 0},
            {"codigo": "near", "nombre": "Pared de entrada (junto a la puerta)", "tipo_admitido": TIPO_CUADRO, "capacidad": 7, "orden": 1},
            {"codigo": "left", "nombre": "Pared izquierda", "tipo_admitido": TIPO_DIBUJO, "capacidad": 20, "orden": 2},
            {"codigo": "right", "nombre": "Pared derecha", "tipo_admitido": TIPO_DIBUJO, "capacidad": 20, "orden": 3},
        ],
    },
    "planta-t": {
        "nombre": "Planta en T (pasillo + estancia)",
        "descripcion": "Entras por un pasillo con dibujos a los lados que desemboca, "
        "por un arco, en una estancia amplia con cuadros bien espaciados al fondo y "
        "al frente. Iluminación por lucernarios. Capacidad: 10 cuadros + 36 dibujos.",
        "zonas": [
            {"codigo": "fondo", "nombre": "Estancia · pared del fondo", "tipo_admitido": TIPO_CUADRO, "capacidad": 6, "orden": 0},
            {"codigo": "hall_frente", "nombre": "Estancia · frente (junto al arco)", "tipo_admitido": TIPO_CUADRO, "capacidad": 4, "orden": 1},
            {"codigo": "hall_izq", "nombre": "Estancia · pared izquierda", "tipo_admitido": TIPO_DIBUJO, "capacidad": 8, "orden": 2},
            {"codigo": "hall_der", "nombre": "Estancia · pared derecha", "tipo_admitido": TIPO_DIBUJO, "capacidad": 8, "orden": 3},
            {"codigo": "pasillo_izq", "nombre": "Pasillo · pared izquierda", "tipo_admitido": TIPO_DIBUJO, "capacidad": 10, "orden": 4},
            {"codigo": "pasillo_der", "nombre": "Pasillo · pared derecha", "tipo_admitido": TIPO_DIBUJO, "capacidad": 10, "orden": 5},
        ],
    },
}


def opciones_plantilla():
    """Lista de (codigo, nombre) para poblar el SelectField del formulario."""
    return [(codigo, p["nombre"]) for codigo, p in PLANTILLAS.items()]


def nombre_plantilla(codigo: str) -> str:
    return PLANTILLAS.get(codigo, {}).get("nombre", codigo)


def sembrar_zonas(sala) -> None:
    """Añade a la sala las zonas definidas por su plantilla (vía la relación,
    se persisten al hacer commit de la sala)."""
    from backend.app.models import Zona

    plantilla = PLANTILLAS.get(sala.plantilla_3d)
    if not plantilla:
        return
    for z in plantilla["zonas"]:
        sala.zonas.append(
            Zona(
                codigo=z["codigo"],
                nombre=z["nombre"],
                capacidad=z["capacidad"],
                tipo_admitido=z["tipo_admitido"],
                orden=z["orden"],
            )
        )
