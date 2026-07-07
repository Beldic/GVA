from datetime import datetime, timezone

from backend.app.extensions import db


class Visita(db.Model):
    """Registro de una visita a la galería de una exposición.

    Se inserta una fila por exposición y sesión de navegador (ver
    `main.gallery`), de modo que recargar la página no infla el contador.
    Base de las estadísticas del panel de plataforma."""

    __tablename__ = "visita"

    id = db.Column(db.Integer, primary_key=True)
    exposicion_id = db.Column(
        db.Integer, db.ForeignKey("exposicion.id"), nullable=False, index=True
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    exposicion = db.relationship("Exposicion", back_populates="visitas")

    def __repr__(self) -> str:
        return f"<Visita expo={self.exposicion_id} {self.created_at:%Y-%m-%d}>"
