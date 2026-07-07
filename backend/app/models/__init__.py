"""Modelos del dominio de la Plataforma de Exposiciones Virtuales.

Jerarquía: exposicion -> sala -> zona -> obra (>- autor). Más `usuario` para el
panel de administración. Importar este paquete registra todos los modelos en el
metadata de SQLAlchemy (necesario para que Flask-Migrate los detecte).
"""
from backend.app.extensions import db
from backend.app.models.autor import Autor
from backend.app.models.exposicion import Exposicion
from backend.app.models.obra import Obra
from backend.app.models.sala import Sala
from backend.app.models.usuario import Usuario
from backend.app.models.visita import Visita
from backend.app.models.zona import Zona

__all__ = ["db", "Usuario", "Autor", "Exposicion", "Sala", "Zona", "Obra", "Visita"]
