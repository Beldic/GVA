from datetime import datetime, timezone

from backend.app.extensions import db

ESTADO_BORRADOR = "borrador"
ESTADO_PUBLICADA = "publicada"


class Exposicion(db.Model):
    """Una muestra completa. Solo una puede estar 'publicada' a la vez;
    la galería pública muestra siempre esa."""

    __tablename__ = "exposicion"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), unique=True, nullable=False, index=True)
    descripcion = db.Column(db.Text)
    fecha_inicio = db.Column(db.Date)
    fecha_fin = db.Column(db.Date)
    estado = db.Column(
        db.String(20), nullable=False, default=ESTADO_BORRADOR, index=True
    )
    created_at = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    salas = db.relationship(
        "Sala",
        back_populates="exposicion",
        cascade="all, delete-orphan",
        order_by="Sala.orden",
    )

    def __repr__(self) -> str:
        return f"<Exposicion {self.titulo} ({self.estado})>"
