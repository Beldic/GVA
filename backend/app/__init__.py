from pathlib import Path

from flask import Flask, send_from_directory

from backend.app.config import Config
from backend.app.extensions import db, migrate

# .../backend/app/__init__.py → raíz del proyecto = parents[2]
PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_ASSETS = PROJECT_ROOT / "frontend" / "assets"


def create_app(config_class=Config) -> Flask:
    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates",
    )
    app.config.from_object(config_class)

    # Extensiones
    db.init_app(app)
    migrate.init_app(app, db, directory=str(PROJECT_ROOT / "backend" / "migrations"))

    # Importar los modelos para que Flask-Migrate los detecte
    from backend.app import models  # noqa: F401

    @app.get("/frontend-assets/<path:subpath>")
    def frontend_assets(subpath: str):
        return send_from_directory(FRONTEND_ASSETS, subpath)

    from backend.app.routes.main import bp as main_bp

    app.register_blueprint(main_bp)

    return app
