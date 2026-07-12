"""Plantillas de sala: cada forma (rect, cruz, T) define su geometría 3D y
sus zonas. Al crear una sala, las zonas se siembran automáticamente.

Dos modos de siembra:
- Estática (PLANTILLAS): medidas y capacidades por defecto de la forma.
- Elástica (ELASTICAS + ajustar_planta): la forma se estira entre límites
  generosos hasta acoger la colección declarada (nº de obras por tipo),
  asignando UNA pared a UN tipo. Los parámetros elegidos se guardan en
  `sala.parametros` y room.js construye la geometría con ellos.

El `codigo` de cada zona coincide con el nombre de la pared en el frontend 3D
(room.js) para que el mapeo sea directo.
"""
from itertools import product

from backend.app.models.obra import (
    TIPO_FOTOGRAFIA,
    TIPO_INFOGRAFIA,
    TIPOS_OBRA,
)
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
    "planta-cruz": {
        "nombre": "Planta en cruz (vestíbulo + 4 alas)",
        "descripcion": "Entras por el ala sur a un vestíbulo central del que "
        "salen tres alas más. Cuadros en los fondos norte, este y oeste; "
        "dibujos en los costados de las cuatro alas. "
        "Capacidad: 9 cuadros + 32 dibujos.",
        "zonas": [
            {"codigo": "fondo", "nombre": "Ala norte · fondo (frente a la entrada)", "tipo_admitido": TIPO_CUADRO, "capacidad": 3, "orden": 0},
            {"codigo": "oeste_fondo", "nombre": "Ala oeste · fondo", "tipo_admitido": TIPO_CUADRO, "capacidad": 3, "orden": 1},
            {"codigo": "este_fondo", "nombre": "Ala este · fondo", "tipo_admitido": TIPO_CUADRO, "capacidad": 3, "orden": 2},
            {"codigo": "entrada_izq", "nombre": "Ala de entrada · costado izquierdo", "tipo_admitido": TIPO_DIBUJO, "capacidad": 4, "orden": 3},
            {"codigo": "entrada_der", "nombre": "Ala de entrada · costado derecho", "tipo_admitido": TIPO_DIBUJO, "capacidad": 4, "orden": 4},
            {"codigo": "oeste_sur", "nombre": "Ala oeste · costado sur", "tipo_admitido": TIPO_DIBUJO, "capacidad": 4, "orden": 5},
            {"codigo": "oeste_norte", "nombre": "Ala oeste · costado norte", "tipo_admitido": TIPO_DIBUJO, "capacidad": 4, "orden": 6},
            {"codigo": "este_sur", "nombre": "Ala este · costado sur", "tipo_admitido": TIPO_DIBUJO, "capacidad": 4, "orden": 7},
            {"codigo": "este_norte", "nombre": "Ala este · costado norte", "tipo_admitido": TIPO_DIBUJO, "capacidad": 4, "orden": 8},
            {"codigo": "norte_izq", "nombre": "Ala norte · costado izquierdo", "tipo_admitido": TIPO_DIBUJO, "capacidad": 4, "orden": 9},
            {"codigo": "norte_der", "nombre": "Ala norte · costado derecho", "tipo_admitido": TIPO_DIBUJO, "capacidad": 4, "orden": 10},
        ],
    },
    "planta-t": {
        "nombre": "Planta en T (pasillo + estancia)",
        "descripcion": "Entras por un pasillo con dibujos a los lados que desemboca, "
        "por un arco, en una estancia amplia con cuadros bien espaciados al fondo y "
        "al frente. Iluminación por lucernarios. Capacidad: 10 cuadros + 40 dibujos.",
        "zonas": [
            {"codigo": "fondo", "nombre": "Estancia · pared del fondo", "tipo_admitido": TIPO_CUADRO, "capacidad": 6, "orden": 0},
            {"codigo": "hall_frente", "nombre": "Estancia · frente (junto al arco)", "tipo_admitido": TIPO_CUADRO, "capacidad": 4, "orden": 1},
            {"codigo": "hall_izq", "nombre": "Estancia · pared izquierda", "tipo_admitido": TIPO_DIBUJO, "capacidad": 8, "orden": 2},
            {"codigo": "hall_der", "nombre": "Estancia · pared derecha", "tipo_admitido": TIPO_DIBUJO, "capacidad": 8, "orden": 3},
            {"codigo": "pasillo_izq", "nombre": "Pasillo · pared izquierda", "tipo_admitido": TIPO_DIBUJO, "capacidad": 12, "orden": 4},
            {"codigo": "pasillo_der", "nombre": "Pasillo · pared derecha", "tipo_admitido": TIPO_DIBUJO, "capacidad": 12, "orden": 5},
        ],
    },
}


def opciones_plantilla():
    """Lista de (codigo, nombre) para poblar el SelectField del formulario."""
    return [(codigo, p["nombre"]) for codigo, p in PLANTILLAS.items()]


def capacidades(codigo: str) -> dict:
    """Huecos que ofrece una plantilla, por tipo de obra."""
    p = PLANTILLAS.get(codigo, {"zonas": []})
    cuadros = sum(z["capacidad"] for z in p["zonas"] if z["tipo_admitido"] == TIPO_CUADRO)
    dibujos = sum(z["capacidad"] for z in p["zonas"] if z["tipo_admitido"] == TIPO_DIBUJO)
    return {"cuadros": cuadros, "dibujos": dibujos, "total": cuadros + dibujos}


def catalogo_plantillas() -> list:
    """Datos completos para el selector de planta del asistente de nueva
    exposición: (codigo, nombre, descripcion, capacidades)."""
    return [
        {
            "codigo": codigo,
            "nombre": p["nombre"],
            "descripcion": p["descripcion"],
            "capacidad": capacidades(codigo),
        }
        for codigo, p in PLANTILLAS.items()
    ]


def nombre_plantilla(codigo: str) -> str:
    return PLANTILLAS.get(codigo, {}).get("nombre", codigo)


# ==========================================================================
# Plantas elásticas: ajuste de dimensiones y reparto de tipos por pared
# ==========================================================================

# Metros lineales de pared que respira cada pieza (hueco), por tipo.
METROS_HUECO = {
    TIPO_CUADRO: 1.8,
    TIPO_FOTOGRAFIA: 1.2,
    TIPO_INFOGRAFIA: 1.1,
    TIPO_DIBUJO: 0.8,
}

# Orden de reparto: de la pieza más ancha a la más estrecha.
ORDEN_REPARTO = [TIPO_CUADRO, TIPO_FOTOGRAFIA, TIPO_INFOGRAFIA, TIPO_DIBUJO]

# Cada forma: parámetros (nombre, mín, máx, paso en metros) y paredes cuyo
# largo colgable depende de los parámetros. `rol` guía el reparto: los
# cuadros prefieren paredes principales; el papel, las laterales. Los largos
# descuentan los huecos de puerta/arco (room.js usa los mismos números).
ELASTICAS = {
    "sala-clasica": {
        "params": [("ancho", 8, 12, 1.0), ("fondo", 6, 14, 1.0)],
        "dims_texto": lambda p: f"{p['ancho']:g} × {p['fondo']:g} m",
        "paredes": [
            {"codigo": "far", "nombre": "Pared del fondo", "rol": "principal", "orden": 0, "largo": lambda p: p["ancho"]},
            {"codigo": "near", "nombre": "Pared de entrada", "rol": "principal", "orden": 1, "largo": lambda p: p["ancho"] - 1.4},
            {"codigo": "left", "nombre": "Pared izquierda", "rol": "lateral", "orden": 2, "largo": lambda p: p["fondo"]},
            {"codigo": "right", "nombre": "Pared derecha", "rol": "lateral", "orden": 3, "largo": lambda p: p["fondo"]},
        ],
    },
    "sala-rectangular": {
        "params": [("ancho", 10, 16, 1.0), ("fondo", 12, 28, 1.0)],
        "dims_texto": lambda p: f"{p['ancho']:g} × {p['fondo']:g} m",
        "paredes": [
            {"codigo": "far", "nombre": "Pared del fondo", "rol": "principal", "orden": 0, "largo": lambda p: p["ancho"]},
            {"codigo": "near", "nombre": "Pared de entrada (junto a la puerta)", "rol": "principal", "orden": 1, "largo": lambda p: p["ancho"] - 1.4},
            {"codigo": "left", "nombre": "Pared izquierda", "rol": "lateral", "orden": 2, "largo": lambda p: p["fondo"]},
            {"codigo": "right", "nombre": "Pared derecha", "rol": "lateral", "orden": 3, "largo": lambda p: p["fondo"]},
        ],
    },
    "planta-cruz": {
        "params": [("ala", 4, 12, 1.0)],
        "dims_texto": lambda p: f"alas de {p['ala']:g} m",
        "paredes": [
            {"codigo": "fondo", "nombre": "Ala norte · fondo (frente a la entrada)", "rol": "principal", "orden": 0, "largo": lambda p: 5.0},
            {"codigo": "oeste_fondo", "nombre": "Ala oeste · fondo", "rol": "principal", "orden": 1, "largo": lambda p: 5.0},
            {"codigo": "este_fondo", "nombre": "Ala este · fondo", "rol": "principal", "orden": 2, "largo": lambda p: 5.0},
            {"codigo": "entrada_izq", "nombre": "Ala de entrada · costado izquierdo", "rol": "lateral", "orden": 3, "largo": lambda p: p["ala"]},
            {"codigo": "entrada_der", "nombre": "Ala de entrada · costado derecho", "rol": "lateral", "orden": 4, "largo": lambda p: p["ala"]},
            {"codigo": "oeste_sur", "nombre": "Ala oeste · costado sur", "rol": "lateral", "orden": 5, "largo": lambda p: p["ala"]},
            {"codigo": "oeste_norte", "nombre": "Ala oeste · costado norte", "rol": "lateral", "orden": 6, "largo": lambda p: p["ala"]},
            {"codigo": "este_sur", "nombre": "Ala este · costado sur", "rol": "lateral", "orden": 7, "largo": lambda p: p["ala"]},
            {"codigo": "este_norte", "nombre": "Ala este · costado norte", "rol": "lateral", "orden": 8, "largo": lambda p: p["ala"]},
            {"codigo": "norte_izq", "nombre": "Ala norte · costado izquierdo", "rol": "lateral", "orden": 9, "largo": lambda p: p["ala"]},
            {"codigo": "norte_der", "nombre": "Ala norte · costado derecho", "rol": "lateral", "orden": 10, "largo": lambda p: p["ala"]},
        ],
    },
    "planta-t": {
        "params": [("pasillo", 8, 20, 1.0), ("estancia", 14, 26, 1.0)],
        "dims_texto": lambda p: f"pasillo de {p['pasillo']:g} m · estancia de {p['estancia']:g} m",
        "paredes": [
            {"codigo": "fondo", "nombre": "Estancia · pared del fondo", "rol": "principal", "orden": 0, "largo": lambda p: p["estancia"]},
            {"codigo": "hall_frente", "nombre": "Estancia · frente (junto al arco)", "rol": "principal", "orden": 1, "largo": lambda p: p["estancia"] - 5.0},
            {"codigo": "hall_izq", "nombre": "Estancia · pared izquierda", "rol": "lateral", "orden": 2, "largo": lambda p: 8.0},
            {"codigo": "hall_der", "nombre": "Estancia · pared derecha", "rol": "lateral", "orden": 3, "largo": lambda p: 8.0},
            {"codigo": "pasillo_izq", "nombre": "Pasillo · pared izquierda", "rol": "lateral", "orden": 4, "largo": lambda p: p["pasillo"]},
            {"codigo": "pasillo_der", "nombre": "Pasillo · pared derecha", "rol": "lateral", "orden": 5, "largo": lambda p: p["pasillo"]},
        ],
    },
}


def _repartir(paredes, coleccion):
    """Asigna a cada pared UN tipo de obra y calcula su capacidad. Devuelve
    (zonas, deficit). Las paredes que sobran se dedican al tipo más numeroso
    de la colección (huecos de reserva para crecer)."""
    pendiente = {t: coleccion.get(t, 0) for t in ORDEN_REPARTO}
    libres = list(paredes)
    zonas = []

    for tipo in ORDEN_REPARTO:
        if pendiente[tipo] <= 0:
            continue
        pref = "principal" if tipo == TIPO_CUADRO else "lateral"
        candidatas = sorted(libres, key=lambda w: (w["rol"] != pref, w["orden"]))
        for pared in candidatas:
            if pendiente[tipo] <= 0:
                break
            cap = int(pared["largo_m"] // METROS_HUECO[tipo])
            if cap <= 0:
                continue
            libres.remove(pared)
            zonas.append({**pared, "tipo_admitido": tipo, "capacidad": cap})
            pendiente[tipo] -= cap

    deficit = {t: n for t, n in pendiente.items() if n > 0}

    con_obras = {t: n for t, n in coleccion.items() if n > 0}
    tipo_reserva = max(con_obras, key=con_obras.get) if con_obras else TIPO_DIBUJO
    for pared in libres:
        tipo = tipo_reserva
        cap = int(pared["largo_m"] // METROS_HUECO[tipo])
        if cap <= 0:
            tipo = TIPO_DIBUJO
            cap = max(int(pared["largo_m"] // METROS_HUECO[tipo]), 1)
        zonas.append({**pared, "tipo_admitido": tipo, "capacidad": cap})

    zonas.sort(key=lambda z: z["orden"])
    return zonas, deficit


def _combos(spec):
    """Combinaciones de parámetros de menor a mayor estiramiento total."""
    ejes = [
        [(nombre, v) for v in _rango(minimo, maximo, paso)]
        for nombre, minimo, maximo, paso in spec["params"]
    ]
    combos = [dict(c) for c in product(*ejes)]
    combos.sort(key=lambda c: sum(c.values()))
    return combos


def _rango(minimo, maximo, paso):
    valores = []
    v = minimo
    while v <= maximo + 1e-9:
        valores.append(round(v, 2))
        v += paso
    return valores


def ajustar_planta(plantilla: str, coleccion: dict) -> dict:
    """Estiramiento mínimo de la forma que acoge la colección (nº de obras
    por tipo). Si ni al máximo cabe, devuelve el máximo con su déficit.

    Devuelve {params, zonas, deficit, dims_texto, capacidad_por_tipo}.
    """
    spec = ELASTICAS[plantilla]
    mejor = None
    for combo in _combos(spec):
        paredes = [
            {**p, "largo_m": p["largo"](combo)} for p in spec["paredes"]
        ]
        zonas, deficit = _repartir(paredes, coleccion)
        if not deficit:
            mejor = (combo, zonas, deficit)
            break
        mejor = (combo, zonas, deficit)  # el último (máximo) queda si nada cabe
    combo, zonas, deficit = mejor
    capacidad = {}
    for z in zonas:
        capacidad[z["tipo_admitido"]] = capacidad.get(z["tipo_admitido"], 0) + z["capacidad"]
    return {
        "params": combo,
        "zonas": [
            {k: z[k] for k in ("codigo", "nombre", "tipo_admitido", "capacidad", "orden")}
            for z in zonas
        ],
        "deficit": deficit,
        "dims_texto": spec["dims_texto"](combo),
        "capacidad_por_tipo": capacidad,
    }


def texto_deficit(deficit: dict) -> str:
    partes = [
        f"{n} {TIPOS_OBRA[t]['nombre'].lower()}{'s' if n != 1 else ''}"
        for t, n in deficit.items()
    ]
    return ", ".join(partes)


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


def sembrar_zonas_elasticas(sala, zonas: list) -> None:
    """Siembra las zonas calculadas por `ajustar_planta` (una pared, un tipo)."""
    from backend.app.models import Zona

    for z in zonas:
        sala.zonas.append(
            Zona(
                codigo=z["codigo"],
                nombre=z["nombre"],
                capacidad=z["capacidad"],
                tipo_admitido=z["tipo_admitido"],
                orden=z["orden"],
            )
        )
