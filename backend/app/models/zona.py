from backend.app.extensions import db

TIPO_DIBUJO = "dibujo"
TIPO_CUADRO = "cuadro"
TIPO_MIXTO = "mixto"


class Zona(db.Model):
    """Pared o área dentro de una sala donde cuelgan obras. Las zonas las
    predefine la plantilla de sala (se siembran al crearla). `codigo` es un
    identificador estable que el frontend 3D usa para situar la zona."""

    __tablename__ = "zona"

    id = db.Column(db.Integer, primary_key=True)
    sala_id = db.Column(
        db.Integer, db.ForeignKey("sala.id"), nullable=False, index=True
    )
    nombre = db.Column(db.String(80), nullable=False)
    codigo = db.Column(db.String(40), nullable=False)
    capacidad = db.Column(db.Integer, nullable=False, default=0)
    tipo_admitido = db.Column(db.String(20), nullable=False, default=TIPO_MIXTO)
    orden = db.Column(db.Integer, nullable=False, default=0)

    sala = db.relationship("Sala", back_populates="zonas")
    obras = db.relationship(
        "Obra",
        back_populates="zona",
        cascade="all, delete-orphan",
        order_by="Obra.orden",
    )

    def __repr__(self) -> str:
        return f"<Zona {self.nombre} ({self.codigo})>"
