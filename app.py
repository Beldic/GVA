from backend.app import create_app

app = create_app()

# En producción (Postgres) garantizamos el esquema y el admin al arrancar el
# proceso web, por si el hosting no ejecuta los comandos previos del Procfile.
# En local (SQLite) no se toca nada: las migraciones se aplican con la CLI.
if app.config["SQLALCHEMY_DATABASE_URI"].startswith("postgresql"):
    from backend.app.bootstrap import (
        aplicar_migraciones,
        asegurar_admin,
        sembrar_demo_si_procede,
    )

    aplicar_migraciones(app)
    asegurar_admin(app)
    sembrar_demo_si_procede(app)

if __name__ == "__main__":
    app.run(debug=True)
