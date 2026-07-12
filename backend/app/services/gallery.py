"""Serialización de una sala a un dict plano para el frontend 3D.

El render de Babylon.js (static/js/gallery) consume esta estructura: la página
la incrusta como JSON y los módulos la leen para construir la escena. El `codigo`
de cada zona (far/near/left/right) mapea directamente a las paredes de room.js.
"""
import os

from flask import current_app, url_for

from backend.app.services import cloudinary_service
from backend.app.utils import slugify


def _imagen_url(obra) -> str:
    """URL de la imagen para texturizar el cuadro: versión transformada de
    Cloudinary si la obra tiene imagen propia, o el placeholder ya guardado."""
    if obra.cloudinary_public_id:
        return cloudinary_service.url_obra(obra.cloudinary_public_id)
    return obra.cloudinary_url


def _serializar_obra(obra) -> dict:
    return {
        "id": obra.id,
        "orden": obra.orden,
        "tipo": obra.tipo,
        "titulo": obra.titulo,
        "autor": obra.autor.nombre,
        "anio": obra.anio,
        "tecnica": obra.tecnica,
        "ancho_cm": obra.ancho_cm,
        "alto_cm": obra.alto_cm,
        "descripcion": obra.descripcion,
        "imagen_url": _imagen_url(obra),
        # Variante ligera para la rejilla del modo 2D en móvil.
        "imagen_movil": (
            cloudinary_service.url_obra(obra.cloudinary_public_id, ancho=600)
            if obra.cloudinary_public_id
            else obra.cloudinary_url
        ),
    }


def _miniatura_card(obra):
    return cloudinary_service.url_miniatura(
        obra.cloudinary_public_id, ancho=800, alto=520
    )


def _primera_obra_url(expo):
    """Primera obra con imagen propia en Cloudinary, en orden de recorrido."""
    for sala in expo.salas:
        for zona in sala.zonas:
            for obra in zona.obras:
                if obra.cloudinary_public_id:
                    return _miniatura_card(obra)
    return None


def _portada_card(expo, propietario):
    """Portada de la card del portal, por prioridad: obra elegida por el
    organizador -> logo del organizador (como placeholder centrado) ->
    primera obra con imagen -> nada (la plantilla pone el emblema).
    Devuelve (url, es_logo)."""
    elegida = expo.portada_obra
    if elegida is not None and elegida.cloudinary_public_id:
        return _miniatura_card(elegida), False
    logo = logo_organizador(propietario)
    if logo:
        return logo, True
    return _primera_obra_url(expo), False


def _contar_obras(expo) -> int:
    return sum(len(zona.obras) for sala in expo.salas for zona in sala.zonas)


def logo_organizador(propietario):
    """Logo del organizador: el subido a su perfil (Cloudinary) manda; si no
    hay, la convención static/img/organizadores/<slug-del-nombre>.png."""
    if propietario is None:
        return None
    if propietario.logo_url:
        return propietario.logo_url
    if not propietario.nombre:
        return None
    relativa = f"img/organizadores/{slugify(propietario.nombre)}.png"
    if os.path.exists(os.path.join(current_app.static_folder, *relativa.split("/"))):
        return url_for("static", filename=relativa)
    return None


def autores_de_expo(expo) -> list:
    """Autores con obra colgada en la exposición, en orden de aparición en el
    recorrido y sin repetidos."""
    vistos = set()
    autores = []
    for sala in expo.salas:
        for zona in sala.zonas:
            for obra in zona.obras:
                if obra.autor_id not in vistos:
                    vistos.add(obra.autor_id)
                    autores.append(obra.autor)
    return autores


def foto_autor(autor):
    """Retrato del autor: el subido a Cloudinary (recortado a cuadrado) o la
    URL manual; None si no hay ninguno."""
    if autor.foto_public_id:
        return cloudinary_service.url_miniatura(autor.foto_public_id, 240, 240)
    return autor.foto_url or None


def resumen_exposicion(expo) -> dict:
    """Datos que muestra la card de una galería publicada en el portal."""
    propietario = expo.propietario
    portada, portada_es_logo = _portada_card(expo, propietario)
    return {
        "titulo": expo.titulo,
        "slug": expo.slug,
        "descripcion": expo.descripcion,
        # Solo el nombre visible; nunca el email en público.
        "organizador": propietario.nombre if propietario else None,
        "organizador_logo": logo_organizador(propietario),
        "fecha_inicio": expo.fecha_inicio,
        "fecha_fin": expo.fecha_fin,
        "n_salas": len(expo.salas),
        "n_obras": _contar_obras(expo),
        "portada": portada,
        "portada_es_logo": portada_es_logo,
        "visitable": bool(expo.salas),
        "apertura": expo.apertura,
        "privada": expo.requiere_codigo,
    }


def og_de_expo(expo) -> dict:
    """Metadatos Open Graph para compartir una exposición: título, resumen
    recortado, imagen de portada ABSOLUTA y URL canónica. Sutileza de
    privacidad: las expos con código no exponen su portada en la
    previsualización (se usa la imagen genérica de la plataforma)."""
    from backend.app.models.exposicion import VISIBILIDAD_CODIGO

    descripcion = (expo.descripcion or "").strip()
    if len(descripcion) > 160:
        descripcion = descripcion[:157].rstrip() + "…"
    if not descripcion:
        descripcion = "Recorre esta exposición en 3D en la Galería Virtual."

    imagen = None
    if expo.visibilidad != VISIBILIDAD_CODIGO:
        imagen, _ = _portada_card(expo, expo.propietario)
        if imagen and imagen.startswith("/"):
            imagen = url_for(
                "static",
                filename=imagen.split("/static/", 1)[-1],
                _external=True,
            )
    if not imagen:
        imagen = url_for(
            "static",
            filename="favicons/web-app-manifest-512x512.png",
            _external=True,
        )
    return {
        "titulo": expo.titulo,
        "descripcion": descripcion,
        "imagen": imagen,
        "url": url_for("main.gallery", slug=expo.slug, _external=True),
    }


def serializar_sala(sala) -> dict:
    """Estructura completa de una sala lista para el 3D. Las relaciones ya
    vienen ordenadas por `orden` (definido en los modelos)."""
    expo = sala.exposicion
    # Solo el nombre visible; nunca el email en público.
    organizador = expo.propietario.nombre if expo.propietario else None
    return {
        "exposicion": {
            "titulo": expo.titulo,
            "slug": expo.slug,
            "organizador": organizador,
            "musica_url": expo.musica_url,
        },
        "sala": {
            "nombre": sala.nombre,
            "plantilla_3d": sala.plantilla_3d,
            "parametros": sala.dimensiones,
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
