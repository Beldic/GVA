"""Comandos de línea de comandos personalizados (flask <comando>)."""
import os

import click

from backend.app.extensions import db
from backend.app.models import Usuario
from backend.app.models.usuario import ROL_ADMIN


def register_commands(app) -> None:
    @app.cli.command("crear-admin")
    @click.option("--email", default=None, help="Email del administrador.")
    @click.option("--password", default=None, help="Contraseña (se pedirá si falta).")
    def crear_admin(email, password):
        """Crea o actualiza el usuario administrador del panel.

        Toma los valores de las opciones, o de ADMIN_EMAIL/ADMIN_PASSWORD del
        entorno, o los pide por teclado.
        """
        email = email or os.environ.get("ADMIN_EMAIL") or click.prompt("Email")
        password = (
            password
            or os.environ.get("ADMIN_PASSWORD")
            or click.prompt("Contraseña", hide_input=True, confirmation_prompt=True)
        )

        usuario = Usuario.query.filter_by(email=email).first()
        if usuario is None:
            usuario = Usuario(email=email, rol=ROL_ADMIN)
            usuario.set_password(password)
            db.session.add(usuario)
            accion = "creado"
        else:
            usuario.set_password(password)
            usuario.rol = ROL_ADMIN
            accion = "actualizado"

        db.session.commit()
        click.echo(f"Administrador {accion}: {email}")
