from datetime import datetime, timezone

from backend.app.extensions import db


class Autor(db.Model):
    """Catálogo de autores privado de cada organizador."""

    __tablename__ = "autor"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(
        db.Integer, db.ForeignKey("usuario.id"), nullable=False, index=True
    )
    nombre = db.Column(db.String(160), nullable=False, index=True)
    bio = db.Column(db.Text)
    foto_url = db.Column(db.String(500))
    contacto = db.Column(db.String(255))
    created_at = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    propietario = db.relationship("Usuario", back_populates="autores")
    obras = db.relationship("Obra", back_populates="autor")

    def __repr__(self) -> str:
        return f"<Autor {self.nombre}>"
