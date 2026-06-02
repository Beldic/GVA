from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from backend.app.extensions import db

ROL_ADMIN = "admin"
ROL_COMISARIO = "comisario"


class Usuario(db.Model):
    """Administrador / comisario que gestiona el panel."""

    __tablename__ = "usuario"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), nullable=False, default=ROL_COMISARIO)
    created_at = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f"<Usuario {self.email}>"
