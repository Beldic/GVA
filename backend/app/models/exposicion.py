from datetime import datetime, timezone

from backend.app.extensions import db

ESTADO_BORRADOR = "borrador"
ESTADO_PUBLICADA = "publicada"


class Exposicion(db.Model):
    """Una muestra completa, propiedad de un organizador. Cada organizador
    publica sus exposiciones de forma independiente; la galería pública sirve
    cada exposición publicada por su slug."""

    __tablename__ = "exposicion"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(
        db.Integer, db.ForeignKey("usuario.id"), nullable=False, index=True
    )
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

    propietario = db.relationship("Usuario", back_populates="exposiciones")
    visitas = db.relationship(
        "Visita",
        back_populates="exposicion",
        cascade="all, delete-orphan",
    )
    salas = db.relationship(
        "Sala",
        back_populates="exposicion",
        cascade="all, delete-orphan",
        order_by="Sala.orden",
    )

    def __repr__(self) -> str:
        return f"<Exposicion {self.titulo} ({self.estado})>"
