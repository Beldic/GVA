"""Integración con Cloudinary: subida, borrado y URLs transformadas.

El api_secret vive solo en el servidor (subida server-side). La BD guarda el
`public_id` y el `secure_url`; las distintas resoluciones se obtienen aplicando
transformaciones sobre la URL (Cloudinary las genera on-the-fly).

Todas las llamadas a la API pueden fallar (red, rechazo de la API, archivo
inválido). La subida convierte cualquier fallo en `CloudinaryError` para que la
ruta lo muestre con un flash; el borrado es best-effort y solo registra el error
(una imagen huérfana no debe tumbar la operación).
"""
import cloudinary
import cloudinary.uploader
import cloudinary.utils
from flask import current_app

CARPETA = "afesol/obras"


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
    Devuelve (public_id, secure_url). Lanza CloudinaryError si falla."""
    try:
        resultado = cloudinary.uploader.upload(
            archivo, folder=CARPETA, resource_type="image"
        )
    except Exception as exc:  # la API de Cloudinary lanza varios tipos
        current_app.logger.exception("Fallo al subir imagen a Cloudinary")
        raise CloudinaryError(str(exc)) from exc
    return resultado["public_id"], resultado["secure_url"]


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
