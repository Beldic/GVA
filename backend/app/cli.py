"""Comandos de línea de comandos personalizados (flask <comando>)."""
import os
import sys

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

        Toma los valores de las opciones o de ADMIN_EMAIL/ADMIN_PASSWORD del
        entorno. En modo interactivo (terminal) los pide por teclado; en un
        deploy no interactivo sin esas variables, se omite sin bloquear.
        """
        email = email or os.environ.get("ADMIN_EMAIL")
        password = password or os.environ.get("ADMIN_PASSWORD")

        if not email or not password:
            if sys.stdin.isatty():
                email = email or click.prompt("Email")
                password = password or click.prompt(
                    "Contraseña", hide_input=True, confirmation_prompt=True
                )
            else:
                click.echo(
                    "crear-admin: faltan ADMIN_EMAIL/ADMIN_PASSWORD; omitido."
                )
                return

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

    @app.cli.command("seed-afesol-cero")
    @click.option("--reset", is_flag=True, help="Borra la exposición si ya existe y la recrea.")
    def seed_afesol_cero(reset):
        """Crea la exposición de ejemplo 'afesol_cero' (40 dibujos + 15 cuadros, placeholders)."""
        from backend.app.models import Autor, Exposicion, Obra, Sala
        from backend.app.models.exposicion import ESTADO_BORRADOR
        from backend.app.models.obra import (
            PLACEHOLDER_IMAGEN,
            TIPO_CUADRO,
            TIPO_DIBUJO,
        )
        from backend.app.plantillas import sembrar_zonas
        from backend.app.utils import slugify

        slug = slugify("afesol_cero")
        existente = Exposicion.query.filter_by(slug=slug).first()
        if existente is not None:
            if not reset:
                click.echo("Ya existe 'afesol_cero'. Usa --reset para recrearla.")
                return
            db.session.delete(existente)
            db.session.commit()
            click.echo("Exposición anterior borrada (--reset).")

        # Autor placeholder (reutilizado por todas las obras de ejemplo)
        autor = Autor.query.filter_by(nombre="Autor de ejemplo").first()
        if autor is None:
            autor = Autor(
                nombre="Autor de ejemplo",
                bio="Autor ficticio para los datos de ejemplo.",
            )
            db.session.add(autor)

        expo = Exposicion(
            titulo="afesol_cero",
            slug=slug,
            descripcion="Exposición de ejemplo con imágenes y textos provisionales (placeholders).",
            estado=ESTADO_BORRADOR,
        )
        db.session.add(expo)

        # 3 salas "sala-clasica": 7 cuadros + 16 dibujos por sala (21/48 de capacidad)
        salas = []
        for i in range(3):
            sala = Sala(
                exposicion=expo,
                nombre=f"Sala {i + 1}",
                plantilla_3d="sala-clasica",
                orden=i,
            )
            sembrar_zonas(sala)
            salas.append(sala)
        db.session.add_all(salas)
        db.session.flush()

        # Reunir zonas por tipo, en orden de recorrido
        zonas_cuadro, zonas_dibujo = [], []
        for sala in salas:
            for z in sorted(sala.zonas, key=lambda z: z.orden):
                if z.tipo_admitido == TIPO_CUADRO:
                    zonas_cuadro.append(z)
                elif z.tipo_admitido == TIPO_DIBUJO:
                    zonas_dibujo.append(z)

        def slots(zonas):
            for z in zonas:
                for orden in range(z.capacidad):
                    yield z, orden

        def llenar(zonas, cantidad, tipo, prefijo, ancho, alto, tecnica):
            creadas = 0
            for n, (z, orden) in zip(range(1, cantidad + 1), slots(zonas)):
                db.session.add(
                    Obra(
                        zona=z,
                        autor=autor,
                        titulo=f"{prefijo} {n:02d}",
                        tipo=tipo,
                        anio=2026,
                        tecnica=tecnica,
                        ancho_cm=ancho,
                        alto_cm=alto,
                        descripcion=f"{prefijo} {n:02d} — texto de ejemplo provisional.",
                        orden=orden,
                        cloudinary_url=PLACEHOLDER_IMAGEN,
                    )
                )
                creadas += 1
            return creadas

        n_cuadros = llenar(zonas_cuadro, 15, TIPO_CUADRO, "Cuadro", 150, 120, "Óleo sobre lienzo (ejemplo)")
        n_dibujos = llenar(zonas_dibujo, 40, TIPO_DIBUJO, "Dibujo", 29.7, 42, "Lápiz sobre papel (ejemplo)")

        db.session.commit()
        click.echo(
            f"Exposición 'afesol_cero' creada: {len(salas)} salas, "
            f"{n_cuadros} cuadros, {n_dibujos} dibujos."
        )

    @app.cli.command("seed-rectangular")
    @click.option("--reset", is_flag=True, help="Borra la exposición si ya existe y la recrea.")
    @click.option("--publicar", is_flag=True, help="Publica la exposición al crearla.")
    def seed_rectangular(reset, publicar):
        """Crea 'afesol_rect': una sola sala rectangular (15 cuadros + 40 dibujos)."""
        from backend.app.seeds import sembrar_rectangular

        res = sembrar_rectangular(reset=reset, publicar=publicar)
        if res is None:
            click.echo("Ya existe 'afesol_rect'. Usa --reset para recrearla.")
            return
        n_cuadros, n_dibujos = res
        estado = "publicada" if publicar else "borrador"
        click.echo(
            f"Exposición 'afesol_rect' creada ({estado}): 1 sala rectangular, "
            f"{n_cuadros} cuadros, {n_dibujos} dibujos."
        )
