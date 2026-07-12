"""Integración con Cloudinary: subida, borrado y URLs transformadas.

El api_secret vive solo en el servidor (subida server-side). La BD guarda el
`public_id` y el `secure_url`; las distintas resoluciones se obtienen aplicando
transformaciones sobre la URL (Cloudinary las genera on-the-fly).

Todas las llamadas a la API pueden fallar (red, rechazo de la API, archivo
inválido). La subida convierte cualquier fallo en `CloudinaryError` para que la
ruta lo muestre con un flash; el borrado es best-effort y solo registra el error
(una imagen huérfana no debe tumbar la operación).
"""
import time

import cloudinary
import cloudinary.api
import cloudinary.uploader
import cloudinary.utils
from flask import current_app

CARPETA = "afesol/obras"
CARPETA_MUSICA = "afesol/musica"


class CloudinaryError(Exception):
    """Fallo al operar contra Cloudinary (subida)."""


def configurar(app) -> None:
    cloudinary.config(
        cloud_name=app.config.get("CLOUDINARY_CLOUD_NAME"),
        api_key=app.config.get("CLOUDINARY_API_KEY"),
        api_secret=app.config.get("CLOUDINARY_API_SECRET"),
        secure=True,
    )


def esta_configurado() -> bool:
    cfg = cloudinary.config()
    return bool(cfg.cloud_name and cfg.api_key and cfg.api_secret)


def subir_imagen(archivo):
    """Sube un archivo (file-like / FileStorage) a Cloudinary.
    Devuelve (public_id, secure_url, ancho_px, alto_px).
    Lanza CloudinaryError si falla."""
    try:
        resultado = cloudinary.uploader.upload(
            archivo, folder=CARPETA, resource_type="image"
        )
    except Exception as exc:  # la API de Cloudinary lanza varios tipos
        current_app.logger.exception("Fallo al subir imagen a Cloudinary")
        raise CloudinaryError(str(exc)) from exc
    return (
        resultado["public_id"],
        resultado["secure_url"],
        resultado.get("width"),
        resultado.get("height"),
    )


def dimensiones_imagen(public_id):
    """(ancho_px, alto_px) de una imagen ya subida, o None si no se puede
    consultar. Best-effort: se usa para ajustar proporciones, nunca debe
    tumbar la operación."""
    if not public_id:
        return None
    try:
        info = cloudinary.api.resource(public_id)
        if info.get("width") and info.get("height"):
            return info["width"], info["height"]
    except Exception:
        current_app.logger.exception(
            "No se pudieron consultar las dimensiones de %s", public_id
        )
    return None


def eliminar_imagen(public_id) -> None:
    """Borra una imagen. Best-effort: registra el error pero no lo propaga
    (una imagen huérfana no debe interrumpir la operación del usuario)."""
    if not public_id:
        return
    try:
        cloudinary.uploader.destroy(public_id, invalidate=True)
    except Exception:
        current_app.logger.exception(
            "No se pudo borrar la imagen de Cloudinary: %s", public_id
        )


def subir_audio(archivo):
    """Sube una pista de audio (el hilo musical de una exposición).
    Cloudinary gestiona el audio bajo resource_type «video».
    Devuelve (public_id, secure_url). Lanza CloudinaryError si falla."""
    try:
        resultado = cloudinary.uploader.upload(
            archivo, folder=CARPETA_MUSICA, resource_type="video"
        )
    except Exception as exc:
        current_app.logger.exception("Fallo al subir audio a Cloudinary")
        raise CloudinaryError(str(exc)) from exc
    return resultado["public_id"], resultado["secure_url"]


def eliminar_audio(public_id) -> None:
    """Borra una pista de audio. Best-effort, como eliminar_imagen."""
    if not public_id:
        return
    try:
        cloudinary.uploader.destroy(
            public_id, resource_type="video", invalidate=True
        )
    except Exception:
        current_app.logger.exception(
            "No se pudo borrar el audio de Cloudinary: %s", public_id
        )


def firmar_subida() -> dict:
    """Datos para una subida firmada directa desde el navegador a Cloudinary.

    El navegador sube el archivo directo al endpoint de Cloudinary con estos
    parámetros; el `api_secret` no sale del servidor (solo se usa para firmar).
    La misma firma sirve para varias subidas dentro de su ventana temporal."""
    cfg = cloudinary.config()
    timestamp = int(time.time())
    firma = cloudinary.utils.api_sign_request(
        {"folder": CARPETA, "timestamp": timestamp}, cfg.api_secret
    )
    return {
        "cloud_name": cfg.cloud_name,
        "api_key": cfg.api_key,
        "timestamp": timestamp,
        "signature": firma,
        "folder": CARPETA,
    }


def url_miniatura(public_id, ancho=80, alto=80) -> str:
    """URL de miniatura recortada (para el panel)."""
    url, _ = cloudinary.utils.cloudinary_url(
        public_id, width=ancho, height=alto, crop="fill", secure=True
    )
    return url


def url_obra(public_id, ancho=1200) -> str:
    """URL para mostrar la obra en el 3D: redimensionada sin recortar, con
    calidad y formato automáticos (Cloudinary sirve WebP/AVIF si el navegador
    lo admite). `crop="limit"` no agranda imágenes más pequeñas que `ancho`."""
    url, _ = cloudinary.utils.cloudinary_url(
        public_id,
        width=ancho,
        crop="limit",
        quality="auto",
        fetch_format="auto",
        secure=True,
    )
    return url
