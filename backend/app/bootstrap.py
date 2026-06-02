"""Arranque en producción.

Aplica las migraciones y asegura el usuario administrador al importar la app web.
Algunos hostings (p. ej. Railway con un start command propio) no ejecutan los
comandos previos del Procfile, así que esto garantiza el esquema y el acceso sin
depender de esa configuración. Solo se invoca cuando la BD es Postgres.
"""
import os

from flask_migrate import upgrade

from backend.app.extensions import db


def aplicar_migraciones(app) -> None:
    with app.app_context():
        app.logger.info("[bootstrap] aplicando migraciones...")
        upgrade()
        app.logger.info("[bootstrap] migraciones al día.")


def asegurar_admin(app) -> None:
    """Crea o actualiza el admin a partir de ADMIN_EMAIL/ADMIN_PASSWORD si están
    definidas. Idempotente."""
    email = os.environ.get("ADMIN_EMAIL")
    password = os.environ.get("ADMIN_PASSWORD")
    if not email or not password:
        app.logger.info("[bootstrap] sin ADMIN_EMAIL/ADMIN_PASSWORD; admin omitido.")
        return

    from backend.app.models import Usuario
    from backend.app.models.usuario import ROL_ADMIN

    with app.app_context():
        usuario = Usuario.query.filter_by(email=email).first()
        if usuario is None:
            usuario = Usuario(email=email, rol=ROL_ADMIN)
            usuario.set_password(password)
            db.session.add(usuario)
        else:
            usuario.set_password(password)
            usuario.rol = ROL_ADMIN
        db.session.commit()
        app.logger.info("[bootstrap] administrador asegurado: %s", email)
