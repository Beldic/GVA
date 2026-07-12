from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from backend.app.extensions import db

# Roles de la plataforma multi-organizador.
#   superadmin  -> administra la plataforma (organizadores + vista global).
#   organizador -> gestiona SOLO sus propias exposiciones, autores y obras.
ROL_SUPERADMIN = "superadmin"
ROL_ORGANIZADOR = "organizador"


class Usuario(UserMixin, db.Model):
    """Cuenta con acceso al panel: superadmin (plataforma) u organizador.

    Los visitantes de la galería son anónimos y no tienen cuenta.

    UserMixin aporta los atributos que Flask-Login necesita
    (is_authenticated, is_active, get_id, ...)."""

    __tablename__ = "usuario"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    nombre = db.Column(db.String(160))  # nombre visible del organizador / entidad
    # Perfil público del organizador (ficha de sus exposiciones).
    web = db.Column(db.String(300))
    logo_public_id = db.Column(db.String(255))
    logo_url = db.Column(db.String(500))
    rol = db.Column(db.String(20), nullable=False, default=ROL_ORGANIZADOR)
    activo = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    exposiciones = db.relationship(
        "Exposicion",
        back_populates="propietario",
        cascade="all, delete-orphan",
        order_by="Exposicion.created_at.desc()",
    )
    autores = db.relationship(
        "Autor",
        back_populates="propietario",
        cascade="all, delete-orphan",
        order_by="Autor.nombre",
    )

    @property
    def es_superadmin(self) -> bool:
        return self.rol == ROL_SUPERADMIN

    @property
    def es_organizador(self) -> bool:
        return self.rol == ROL_ORGANIZADOR

    # Flask-Login usa is_active para permitir la sesión; una cuenta desactivada
    # queda bloqueada sin borrar sus datos.
    @property
    def is_active(self) -> bool:  # noqa: D401 - override de UserMixin
        return bool(self.activo)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f"<Usuario {self.email} ({self.rol})>"
