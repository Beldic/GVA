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


def _portada_url(expo):
    """Miniatura de portada para la card del portal: primera obra con imagen
    propia en Cloudinary, recortada a proporción de card. `None` si la
    exposición aún no tiene ninguna imagen real (la plantilla usa un fondo)."""
    for sala in expo.salas:
        for zona in sala.zonas:
            for obra in zona.obras:
                if obra.cloudinary_public_id:
                    return cloudinary_service.url_miniatura(
                        obra.cloudinary_public_id, ancho=800, alto=520
                    )
    return None


def _contar_obras(expo) -> int:
    return sum(len(zona.obras) for sala in expo.salas for zona in sala.zonas)


def resumen_exposicion(expo) -> dict:
    """Datos que muestra la card de una galería publicada en el portal."""
    propietario = expo.propietario
    return {
        "titulo": expo.titulo,
        "slug": expo.slug,
        "descripcion": expo.descripcion,
        "organizador": (propietario.nombre or propietario.email)
        if propietario
        else None,
        "fecha_inicio": expo.fecha_inicio,
        "fecha_fin": expo.fecha_fin,
        "n_salas": len(expo.salas),
        "n_obras": _contar_obras(expo),
        "portada": _portada_url(expo),
        "visitable": bool(expo.salas),
    }


def serializar_sala(sala) -> dict:
    """Estructura completa de una sala lista para el 3D. Las relaciones ya
    vienen ordenadas por `orden` (definido en los modelos)."""
    expo = sala.exposicion
    organizador = (
        (expo.propietario.nombre or expo.propietario.email)
        if expo.propietario
        else None
    )
    return {
        "exposicion": {
            "titulo": expo.titulo,
            "slug": expo.slug,
            "organizador": organizador,
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
