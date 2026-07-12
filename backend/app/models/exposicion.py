from datetime import date, datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from backend.app.extensions import db

ESTADO_BORRADOR = "borrador"
ESTADO_PUBLICADA = "publicada"

VISIBILIDAD_PUBLICA = "publica"
VISIBILIDAD_ENLACE = "enlace"
VISIBILIDAD_CODIGO = "codigo"

APERTURA_PROXIMAMENTE = "proximamente"
APERTURA_ABIERTA = "abierta"
APERTURA_CERRADA = "cerrada"


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
    # Quién puede ver una exposición publicada: en el portal y en abierto
    # (publica), solo con la URL (enlace) o pidiendo un código (codigo).
    visibilidad = db.Column(
        db.String(20), nullable=False, default=VISIBILIDAD_PUBLICA, index=True
    )
    codigo_acceso_hash = db.Column(db.String(255))
    # Cierre manual del organizador; se combina con las fechas en `apertura`.
    cerrada_manual = db.Column(db.Boolean, nullable=False, default=False)
    # Obra elegida como portada de la card del portal. Entero sin FK: una FK
    # obra->exposicion crearía un ciclo con la cadena obra>zona>sala>exposicion;
    # `portada_obra` valida que la obra exista y siga en esta exposición.
    portada_obra_id = db.Column(db.Integer)
    # Hilo musical de la exposición (audio en Cloudinary, opcional).
    musica_public_id = db.Column(db.String(255))
    musica_url = db.Column(db.String(500))
    # Vídeo de presentación (enlace YouTube/Vimeo/mp4; se embebe en la ficha).
    # video_vertical: True si es 9:16 (móvil); se detecta al guardar (oEmbed).
    video_url = db.Column(db.String(500))
    video_vertical = db.Column(db.Boolean)
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

    @property
    def portada_obra(self):
        """La obra elegida como portada, o None si no hay elección o la obra
        ya no cuelga en esta exposición (retirada o movida)."""
        if self.portada_obra_id is None:
            return None
        from backend.app.models.obra import Obra

        obra = db.session.get(Obra, self.portada_obra_id)
        if obra is None or obra.zona.sala.exposicion_id != self.id:
            return None
        return obra

    @property
    def apertura(self) -> str:
        """Estado de apertura de cara al visitante: cierre manual del
        organizador o, en su defecto, lo que digan las fechas."""
        if self.cerrada_manual:
            return APERTURA_CERRADA
        hoy = date.today()
        if self.fecha_fin and hoy > self.fecha_fin:
            return APERTURA_CERRADA
        if self.fecha_inicio and hoy < self.fecha_inicio:
            return APERTURA_PROXIMAMENTE
        return APERTURA_ABIERTA

    @property
    def abierta(self) -> bool:
        return self.apertura == APERTURA_ABIERTA

    @property
    def es_publica(self) -> bool:
        return self.visibilidad == VISIBILIDAD_PUBLICA

    @property
    def requiere_codigo(self) -> bool:
        return self.visibilidad == VISIBILIDAD_CODIGO

    def set_codigo_acceso(self, codigo: str) -> None:
        self.codigo_acceso_hash = generate_password_hash(codigo)

    def check_codigo_acceso(self, codigo: str) -> bool:
        if not self.codigo_acceso_hash:
            return False
        return check_password_hash(self.codigo_acceso_hash, codigo)

    def __repr__(self) -> str:
        return f"<Exposicion {self.titulo} ({self.estado})>"
