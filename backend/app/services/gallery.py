"""Serialización de una sala a un dict plano para el frontend 3D.

El render de Babylon.js (static/js/gallery) consume esta estructura: la página
la incrusta como JSON y los módulos la leen para construir la escena. El `codigo`
de cada zona (far/near/left/right) mapea directamente a las paredes de room.js.
"""
from backend.app.services import cloudinary_service


def _imagen_url(obra) -> str:
    """URL de la imagen para texturizar el cuadro: versión transformada de
    Cloudinary si la obra tiene imagen propia, o el placeholder ya guardado."""
    if obra.cloudinary_public_id:
        return cloudinary_service.url_obra(obra.cloudinary_public_id)
    return obra.cloudinary_url


def _serializar_obra(obra) -> dict:
    return {
        "orden": obra.orden,
        "titulo": obra.titulo,
        "autor": obra.autor.nombre,
        "anio": obra.anio,
        "tecnica": obra.tecnica,
        "ancho_cm": obra.ancho_cm,
        "alto_cm": obra.alto_cm,
        "descripcion": obra.descripcion,
        "imagen_url": _imagen_url(obra),
    }


def serializar_sala(sala) -> dict:
    """Estructura completa de una sala lista para el 3D. Las relaciones ya
    vienen ordenadas por `orden` (definido en los modelos)."""
    return {
        "exposicion": {
            "titulo": sala.exposicion.titulo,
            "slug": sala.exposicion.slug,
        },
        "sala": {
            "nombre": sala.nombre,
            "plantilla_3d": sala.plantilla_3d,
            "zonas": [
                {
                    "codigo": zona.codigo,
                    "nombre": zona.nombre,
                    "capacidad": zona.capacidad,
                    "obras": [_serializar_obra(o) for o in zona.obras],
                }
                for zona in sala.zonas
            ],
        },
    }
