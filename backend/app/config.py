"""Configuración de la aplicación por entorno.

Local (desarrollo): si no hay DATABASE_URL definida, se usa SQLite en un
archivo dentro del proyecto. Producción (Railway): Railway inyecta DATABASE_URL
apuntando a Postgres, que tiene prioridad automáticamente.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Carga variables SOLO desde el .env del propio proyecto (no rastrear hacia
# arriba: evita que un .env suelto en una carpeta superior se cuele). En Railway
# este archivo no existe y las variables vienen del entorno.
load_dotenv(PROJECT_ROOT / ".env")


def _normalize_db_url(url: str) -> str:
    """Railway/Heroku exponen a veces 'postgres://'; SQLAlchemy exige 'postgresql://'."""
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-inseguro-cambiar-en-produccion")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    _db_url = os.environ.get("DATABASE_URL")
    if _db_url:
        SQLALCHEMY_DATABASE_URI = _normalize_db_url(_db_url)
    else:
        # SQLite local por defecto (archivo en la raíz del proyecto)
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{(PROJECT_ROOT / 'galeria_dev.db').as_posix()}"
