"""Siembra de datos de ejemplo (placeholders), reutilizable por la CLI y el
arranque en producción. Las imágenes usan el placeholder; el contenido real se
gestiona luego desde el panel."""
from backend.app.extensions import db


def sembrar_rectangular(reset: bool = False, publicar: bool = False):
    """Crea la exposición 'afesol_rect': una sala rectangular con 15 cuadros +
    40 dibujos placeholder. Devuelve (n_cuadros, n_dibujos), o None si ya existía
    y no se pidió `reset`."""
    from backend.app.models import Autor, Exposicion, Obra, Sala
    from backend.app.models.exposicion import ESTADO_BORRADOR, ESTADO_PUBLICADA
    from backend.app.models.obra import (
        PLACEHOLDER_IMAGEN,
        TIPO_CUADRO,
        TIPO_DIBUJO,
    )
    from backend.app.plantillas import sembrar_zonas
    from backend.app.utils import slugify

    slug = slugify("afesol_rect")
    existente = Exposicion.query.filter_by(slug=slug).first()
    if existente is not None:
        if not reset:
            return None
        db.session.delete(existente)
        db.session.commit()

    autor = Autor.query.filter_by(nombre="Autor de ejemplo").first()
    if autor is None:
        autor = Autor(
            nombre="Autor de ejemplo",
            bio="Autor ficticio para los datos de ejemplo.",
        )
        db.session.add(autor)

    if publicar:
        # Solo una publicada a la vez: despublica las demás.
        Exposicion.query.filter(Exposicion.estado == ESTADO_PUBLICADA).update(
            {"estado": ESTADO_BORRADOR}
        )

    expo = Exposicion(
        titulo="afesol_rect",
        slug=slug,
        descripcion="Sala rectangular de prueba (placeholders).",
        estado=ESTADO_PUBLICADA if publicar else ESTADO_BORRADOR,
    )
    db.session.add(expo)

    sala = Sala(
        exposicion=expo,
        nombre="Sala única",
        plantilla_3d="sala-rectangular",
        orden=0,
    )
    sembrar_zonas(sala)
    db.session.add(sala)
    db.session.flush()

    zonas = sorted(sala.zonas, key=lambda z: z.orden)
    zonas_cuadro = [z for z in zonas if z.tipo_admitido == TIPO_CUADRO]
    zonas_dibujo = [z for z in zonas if z.tipo_admitido == TIPO_DIBUJO]

    def slots(zs):
        for z in zs:
            for orden in range(z.capacidad):
                yield z, orden

    def llenar(zs, cantidad, tipo, prefijo, ancho, alto, tecnica):
        creadas = 0
        for n, (z, orden) in zip(range(1, cantidad + 1), slots(zs)):
            db.session.add(
                Obra(
                    zona=z,
                    autor=autor,
                    titulo=f"{prefijo} {n:02d}",
                    tipo=tipo,
                    anio=2026,
                    tecnica=tecnica,
                    ancho_cm=ancho,
                    alto_cm=alto,
                    descripcion=f"{prefijo} {n:02d} — texto de ejemplo provisional.",
                    orden=orden,
                    cloudinary_url=PLACEHOLDER_IMAGEN,
                )
            )
            creadas += 1
        return creadas

    n_cuadros = llenar(zonas_cuadro, 15, TIPO_CUADRO, "Cuadro", 150, 120, "Óleo sobre lienzo (ejemplo)")
    n_dibujos = llenar(zonas_dibujo, 40, TIPO_DIBUJO, "Dibujo", 29.7, 42, "Lápiz sobre papel (ejemplo)")

    db.session.commit()
    return n_cuadros, n_dibujos
