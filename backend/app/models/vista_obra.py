from datetime import datetime, timezone

from backend.app.extensions import db

VISTA_3D = "3d"  # contemplación: mirar el cuadro de cerca unos segundos
VISTA_2D = "2d"  # apertura de la ficha de la obra en el modo 2D


class VistaObra(db.Model):
    """Interés registrado sobre una obra concreta, con dimensiones anónimas:
    en el 3D, una contemplación (el visitante se detiene a mirarla); en el 2D,
    la apertura de su ficha. Una fila por obra y sesión de navegador (dedupe
    en `main.obra_vista`); nunca identidad del visitante."""

    __tablename__ = "vista_obra"

    id = db.Column(db.Integer, primary_key=True)
    obra_id = db.Column(
        db.Integer, db.ForeignKey("obra.id"), nullable=False, index=True
    )
    modo = db.Column(db.String(10), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    obra = db.relationship("Obra", back_populates="vistas")

    def __repr__(self) -> str:
        return f"<VistaObra obra={self.obra_id} {self.modo}>"
