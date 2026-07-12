"""Formularios del panel (Flask-WTF / WTForms)."""
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import (
    BooleanField,
    DateField,
    FloatField,
    IntegerField,
    PasswordField,
    RadioField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import (
    URL,
    DataRequired,
    Length,
    NumberRange,
    Optional,
    Regexp,
)

# Validación de email ligera (evita la dependencia email_validator de WTForms).
_EMAIL_RE = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class AutorForm(FlaskForm):
    nombre = StringField("Nombre", validators=[DataRequired(), Length(max=160)])
    bio = TextAreaField("Biografía", validators=[Optional()])
    foto_url = StringField(
        "URL de foto", validators=[Optional(), URL(), Length(max=500)]
    )
    contacto = StringField("Contacto", validators=[Optional(), Length(max=255)])
    submit = SubmitField("Guardar")


class ExposicionForm(FlaskForm):
    titulo = StringField("Título", validators=[DataRequired(), Length(max=200)])
    slug = StringField(
        "Slug (URL)", validators=[Optional(), Length(max=220)]
    )
    descripcion = TextAreaField("Descripción", validators=[Optional()])
    fecha_inicio = DateField("Fecha de inicio", validators=[Optional()])
    fecha_fin = DateField("Fecha de fin", validators=[Optional()])
    visibilidad = SelectField(
        "Visibilidad",
        choices=[
            ("publica", "Pública — aparece en el portal"),
            ("enlace", "Enlace secreto — solo quien tenga la URL"),
            ("codigo", "Privada — pide un código de acceso"),
        ],
        default="publica",
    )
    codigo_acceso = StringField(
        "Código de acceso",
        validators=[Optional(), Length(min=4, max=64)],
        description="Mínimo 4 caracteres. Al editar, déjalo vacío para conservar el actual.",
    )
    musica = FileField(
        "Hilo musical",
        validators=[
            Optional(),
            FileAllowed(["mp3", "ogg", "m4a", "aac", "wav"],
                        "Solo audio (mp3, ogg, m4a, aac, wav)."),
        ],
        description="Suena en bucle durante el recorrido 3D; el visitante puede silenciarlo.",
    )
    quitar_musica = BooleanField("Quitar el hilo musical actual")
    submit = SubmitField("Guardar")


class ExposicionNuevaForm(ExposicionForm):
    """Asistente de nueva exposición: además de los datos de la exposición,
    pide la colección estimada (para recomendar planta) y la planta de la
    sala inicial, que se crea junto a la exposición."""

    n_cuadros = IntegerField(
        "Cuadros", validators=[Optional(), NumberRange(min=0)]
    )
    n_fotografias = IntegerField(
        "Fotografías", validators=[Optional(), NumberRange(min=0)]
    )
    n_infografias = IntegerField(
        "Infografías", validators=[Optional(), NumberRange(min=0)]
    )
    n_dibujos = IntegerField(
        "Dibujos", validators=[Optional(), NumberRange(min=0)]
    )
    plantilla = RadioField("Planta de la sala", validators=[DataRequired()])


class SalaForm(FlaskForm):
    nombre = StringField("Nombre de la sala", validators=[DataRequired(), Length(max=120)])
    plantilla_3d = SelectField("Plantilla", validators=[Optional()])
    orden = IntegerField("Orden en el recorrido", validators=[Optional()], default=0)
    submit = SubmitField("Guardar")


class ObraForm(FlaskForm):
    titulo = StringField("Título", validators=[DataRequired(), Length(max=200)])
    autor_id = SelectField("Autor", coerce=int, validators=[DataRequired()])
    tipo = SelectField(
        "Tipo",
        choices=[
            ("cuadro", "Cuadro"),
            ("fotografia", "Fotografía"),
            ("infografia", "Infografía"),
            ("dibujo", "Dibujo"),
        ],
        validators=[Optional()],
    )
    anio = IntegerField("Año", validators=[Optional()])
    tecnica = StringField("Técnica", validators=[Optional(), Length(max=160)])
    ancho_cm = FloatField("Ancho (cm)", validators=[Optional(), NumberRange(min=0)])
    alto_cm = FloatField("Alto (cm)", validators=[Optional(), NumberRange(min=0)])
    descripcion = TextAreaField("Descripción", validators=[Optional()])
    imagen = FileField(
        "Imagen",
        validators=[
            Optional(),
            FileAllowed(["jpg", "jpeg", "png", "webp"], "Solo imágenes (jpg, png, webp)."),
        ],
    )
    submit = SubmitField("Guardar")


class OrganizadorForm(FlaskForm):
    """Alta de un organizador desde el panel de plataforma."""

    email = StringField(
        "Email",
        validators=[
            DataRequired(),
            Length(max=255),
            Regexp(_EMAIL_RE, message="Introduce un email válido."),
        ],
    )
    nombre = StringField(
        "Nombre visible", validators=[Optional(), Length(max=160)]
    )
    password = PasswordField(
        "Contraseña (opcional)",
        validators=[Optional(), Length(min=8, max=128)],
        description="Si la dejas vacía se genera una automáticamente.",
    )
    submit = SubmitField("Crear organizador")


class OrganizadorEditForm(FlaskForm):
    """Edición de datos básicos de un organizador."""

    nombre = StringField(
        "Nombre visible", validators=[Optional(), Length(max=160)]
    )
    activo = BooleanField("Cuenta activa")
    submit = SubmitField("Guardar cambios")
