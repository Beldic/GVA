"""Utilidades varias."""
import re
import unicodedata


def slugify(texto: str) -> str:
    """Convierte un texto en un slug apto para URL (minúsculas, sin acentos)."""
    if not texto:
        return ""
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    texto = re.sub(r"[^a-zA-Z0-9]+", "-", texto).strip("-").lower()
    return texto
