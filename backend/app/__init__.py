from pathlib import Path

from flask import Flask, send_from_directory

from backend.app.config import Config
from backend.app.extensions import csrf, db, login_manager, migrate

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
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "admin.login"
    login_manager.login_message = "Inicia sesión para acceder al panel."
    login_manager.login_message_category = "info"

    # Importar los modelos para que Flask-Migrate los detecte
    from backend.app import models  # noqa: F401
    from backend.app.models import Usuario

    @login_manager.user_loader
    def load_user(user_id: str):
        return db.session.get(Usuario, int(user_id))

    @app.get("/frontend-assets/<path:subpath>")
    def frontend_assets(subpath: str):
        return send_from_directory(FRONTEND_ASSETS, subpath)

    # Blueprints
    from backend.app.routes.admin import bp as admin_bp
    from backend.app.routes.main import bp as main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)

    # Comandos CLI
    from backend.app.cli import register_commands

    register_commands(app)

    return app
