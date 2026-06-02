"""Panel de administración: autenticación + CRUD de autores y exposiciones.

Salas (3b) y obras (3c) se añadirán en sub-partes posteriores.
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

from backend.app.extensions import db
from backend.app.forms import AutorForm, ExposicionForm
from backend.app.models import Autor, Exposicion, Usuario
from backend.app.models.exposicion import ESTADO_BORRADOR, ESTADO_PUBLICADA
from backend.app.utils import slugify

bp = Blueprint("admin", __name__, url_prefix="/admin")


# --------------------------------------------------------------------------
# Autenticación
# --------------------------------------------------------------------------
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


# --------------------------------------------------------------------------
# Autores
# --------------------------------------------------------------------------
@bp.get("/autores")
@login_required
def autores_list():
    autores = Autor.query.order_by(Autor.nombre).all()
    return render_template("admin/autores_list.html", autores=autores)


@bp.route("/autores/nuevo", methods=["GET", "POST"])
@login_required
def autor_nuevo():
    form = AutorForm()
    if form.validate_on_submit():
        autor = Autor(
            nombre=form.nombre.data.strip(),
            bio=form.bio.data or None,
            foto_url=form.foto_url.data or None,
            contacto=form.contacto.data or None,
        )
        db.session.add(autor)
        db.session.commit()
        flash("Autor creado.", "info")
        return redirect(url_for("admin.autores_list"))
    return render_template("admin/autor_form.html", form=form, titulo="Nuevo autor")


@bp.route("/autores/<int:autor_id>/editar", methods=["GET", "POST"])
@login_required
def autor_editar(autor_id):
    autor = db.get_or_404(Autor, autor_id)
    form = AutorForm(obj=autor)
    if form.validate_on_submit():
        autor.nombre = form.nombre.data.strip()
        autor.bio = form.bio.data or None
        autor.foto_url = form.foto_url.data or None
        autor.contacto = form.contacto.data or None
        db.session.commit()
        flash("Autor actualizado.", "info")
        return redirect(url_for("admin.autores_list"))
    return render_template(
        "admin/autor_form.html", form=form, titulo=f"Editar: {autor.nombre}"
    )


@bp.post("/autores/<int:autor_id>/borrar")
@login_required
def autor_borrar(autor_id):
    autor = db.get_or_404(Autor, autor_id)
    if autor.obras:
        flash("No se puede borrar: el autor tiene obras asignadas.", "error")
    else:
        db.session.delete(autor)
        db.session.commit()
        flash("Autor borrado.", "info")
    return redirect(url_for("admin.autores_list"))


# --------------------------------------------------------------------------
# Exposiciones
# --------------------------------------------------------------------------
def _slug_unico(base: str, exclude_id=None) -> str:
    """Garantiza un slug único añadiendo un sufijo numérico si hace falta."""
    base = base or "exposicion"
    slug = base
    i = 2
    while True:
        q = Exposicion.query.filter_by(slug=slug)
        if exclude_id is not None:
            q = q.filter(Exposicion.id != exclude_id)
        if q.first() is None:
            return slug
        slug = f"{base}-{i}"
        i += 1


@bp.get("/exposiciones")
@login_required
def exposiciones_list():
    exposiciones = Exposicion.query.order_by(Exposicion.created_at.desc()).all()
    return render_template(
        "admin/exposiciones_list.html",
        exposiciones=exposiciones,
        ESTADO_PUBLICADA=ESTADO_PUBLICADA,
    )


@bp.route("/exposiciones/nueva", methods=["GET", "POST"])
@login_required
def exposicion_nueva():
    form = ExposicionForm()
    if form.validate_on_submit():
        base = slugify(form.slug.data or form.titulo.data)
        expo = Exposicion(
            titulo=form.titulo.data.strip(),
            slug=_slug_unico(base),
            descripcion=form.descripcion.data or None,
            fecha_inicio=form.fecha_inicio.data,
            fecha_fin=form.fecha_fin.data,
            estado=ESTADO_BORRADOR,
        )
        db.session.add(expo)
        db.session.commit()
        flash("Exposición creada.", "info")
        return redirect(url_for("admin.exposiciones_list"))
    return render_template(
        "admin/exposicion_form.html", form=form, titulo="Nueva exposición"
    )


@bp.route("/exposiciones/<int:exposicion_id>/editar", methods=["GET", "POST"])
@login_required
def exposicion_editar(exposicion_id):
    expo = db.get_or_404(Exposicion, exposicion_id)
    form = ExposicionForm(obj=expo)
    if form.validate_on_submit():
        expo.titulo = form.titulo.data.strip()
        base = slugify(form.slug.data or form.titulo.data)
        expo.slug = _slug_unico(base, exclude_id=expo.id)
        expo.descripcion = form.descripcion.data or None
        expo.fecha_inicio = form.fecha_inicio.data
        expo.fecha_fin = form.fecha_fin.data
        db.session.commit()
        flash("Exposición actualizada.", "info")
        return redirect(url_for("admin.exposiciones_list"))
    return render_template(
        "admin/exposicion_form.html", form=form, titulo=f"Editar: {expo.titulo}"
    )


@bp.post("/exposiciones/<int:exposicion_id>/publicar")
@login_required
def exposicion_publicar(exposicion_id):
    expo = db.get_or_404(Exposicion, exposicion_id)
    # Solo una publicada a la vez: despublica las demás.
    Exposicion.query.filter(
        Exposicion.id != expo.id, Exposicion.estado == ESTADO_PUBLICADA
    ).update({"estado": ESTADO_BORRADOR})
    expo.estado = ESTADO_PUBLICADA
    db.session.commit()
    flash(f"«{expo.titulo}» es ahora la exposición publicada.", "info")
    return redirect(url_for("admin.exposiciones_list"))


@bp.post("/exposiciones/<int:exposicion_id>/despublicar")
@login_required
def exposicion_despublicar(exposicion_id):
    expo = db.get_or_404(Exposicion, exposicion_id)
    expo.estado = ESTADO_BORRADOR
    db.session.commit()
    flash(f"«{expo.titulo}» pasó a borrador.", "info")
    return redirect(url_for("admin.exposiciones_list"))


@bp.post("/exposiciones/<int:exposicion_id>/borrar")
@login_required
def exposicion_borrar(exposicion_id):
    expo = db.get_or_404(Exposicion, exposicion_id)
    db.session.delete(expo)
    db.session.commit()
    flash("Exposición borrada.", "info")
    return redirect(url_for("admin.exposiciones_list"))
