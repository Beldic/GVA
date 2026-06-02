from pathlib import Path

from flask import Flask, send_from_directory

# .../backend/app/__init__.py → raíz del proyecto = parents[2]
PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_ASSETS = PROJECT_ROOT / "frontend" / "assets"


def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates",
    )

    @app.get("/frontend-assets/<path:subpath>")
    def frontend_assets(subpath: str):
        return send_from_directory(FRONTEND_ASSETS, subpath)

    from backend.app.routes.main import bp as main_bp
    app.register_blueprint(main_bp)

    return app
