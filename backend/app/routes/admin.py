"""Panel de administración: login, logout y dashboard protegido.

El CRUD de exposiciones/salas/autores/obras se añadirá en la Fase 3; aquí solo
queda montada la autenticación (la puerta y la cerradura).
"""
from urllib.parse import urlparse

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user

from backend.app.models import Usuario

bp = Blueprint("admin", __name__, url_prefix="/admin")


def _es_url_segura(destino: str) -> bool:
    """Evita open-redirects: solo permite rutas locales (relativas)."""
    if not destino:
        return False
    parsed = urlparse(destino)
    return parsed.scheme == "" and parsed.netloc == "" and destino.startswith("/")


@bp.get("/login")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))
    return render_template("admin/login.html")


@bp.post("/login")
def login_post():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    usuario = Usuario.query.filter_by(email=email).first()
    if usuario is not None and usuario.check_password(password):
        login_user(usuario)
        siguiente = request.args.get("next")
        if _es_url_segura(siguiente):
            return redirect(siguiente)
        return redirect(url_for("admin.dashboard"))

    flash("Email o contraseña incorrectos.", "error")
    return redirect(url_for("admin.login"))


@bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("admin.login"))


@bp.get("/")
@login_required
def dashboard():
    return render_template("admin/dashboard.html")
