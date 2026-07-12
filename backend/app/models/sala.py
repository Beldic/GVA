import json
from datetime import datetime, timezone

from backend.app.extensions import db


class Sala(db.Model):
    """Un espacio 3D dentro de una exposición. `plantilla_3d` identifica la
    forma de la planta; `parametros` (JSON) guarda sus dimensiones elásticas
    calculadas al crearla — NULL en salas antiguas, que usan las medidas por
    defecto de la forma. `orden` define el recorrido entre salas."""

    __tablename__ = "sala"

    id = db.Column(db.Integer, primary_key=True)
    exposicion_id = db.Column(
        db.Integer, db.ForeignKey("exposicion.id"), nullable=False, index=True
    )
    nombre = db.Column(db.String(120), nullable=False)
    plantilla_3d = db.Column(db.String(80), nullable=False)
    parametros = db.Column(db.Text)
    orden = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    exposicion = db.relationship("Exposicion", back_populates="salas")
    zonas = db.relationship(
        "Zona",
        back_populates="sala",
        cascade="all, delete-orphan",
        order_by="Zona.orden",
    )

    @property
    def dimensiones(self):
        """Parámetros de la planta como dict, o None (medidas por defecto)."""
        if not self.parametros:
            return None
        try:
            return json.loads(self.parametros)
        except ValueError:
            return None

    def __repr__(self) -> str:
        return f"<Sala {self.nombre}>"
