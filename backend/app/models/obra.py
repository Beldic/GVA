from datetime import datetime, timezone

from backend.app.extensions import db

TIPO_DIBUJO = "dibujo"
TIPO_CUADRO = "cuadro"
TIPO_FOTOGRAFIA = "fotografia"
TIPO_INFOGRAFIA = "infografia"

# Catálogo de tipos: etiqueta visible y medidas por defecto (cm) cuando la
# obra no trae las suyas (carga múltiple, placeholder del 3D).
TIPOS_OBRA = {
    TIPO_CUADRO: {"nombre": "Cuadro", "ancho_cm": 100.0, "alto_cm": 80.0},
    TIPO_FOTOGRAFIA: {"nombre": "Fotografía", "ancho_cm": 60.0, "alto_cm": 40.0},
    TIPO_INFOGRAFIA: {"nombre": "Infografía", "ancho_cm": 70.0, "alto_cm": 100.0},
    TIPO_DIBUJO: {"nombre": "Dibujo", "ancho_cm": 29.7, "alto_cm": 42.0},
}

# Imagen por defecto mientras no se sube la definitiva a Cloudinary (Fase 4).
PLACEHOLDER_IMAGEN = "/frontend-assets/images/afesol4.png"


class Obra(db.Model):
    """Una pieza (dibujo o cuadro) colgada en una zona. La posición en la sala
    se calcula en el 3D a partir de `orden` dentro de la zona y de las medidas
    físicas (ancho_cm/alto_cm). La imagen se aloja en Cloudinary."""

    __tablename__ = "obra"
    __table_args__ = (
        db.UniqueConstraint("zona_id", "orden", name="uq_obra_zona_orden"),
    )

    id = db.Column(db.Integer, primary_key=True)
    autor_id = db.Column(
        db.Integer, db.ForeignKey("autor.id"), nullable=False, index=True
    )
    zona_id = db.Column(
        db.Integer, db.ForeignKey("zona.id"), nullable=False, index=True
    )

    titulo = db.Column(db.String(200), nullable=False)
    anio = db.Column(db.Integer)
    tecnica = db.Column(db.String(160))
    tipo = db.Column(db.String(20), nullable=False, default=TIPO_CUADRO)
    ancho_cm = db.Column(db.Float)
    alto_cm = db.Column(db.Float)
    descripcion = db.Column(db.Text)

    # Datos que devuelve Cloudinary al subir la imagen
    cloudinary_public_id = db.Column(db.String(255))
    cloudinary_url = db.Column(db.String(500))

    # Posición dentro de la zona (UNIQUE(zona_id, orden) evita solapes)
    orden = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    autor = db.relationship("Autor", back_populates="obras")
    zona = db.relationship("Zona", back_populates="obras")
    vistas = db.relationship(
        "VistaObra",
        back_populates="obra",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Obra {self.titulo}>"
