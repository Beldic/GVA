"""Formularios del panel (Flask-WTF / WTForms)."""
from flask_wtf import FlaskForm
from wtforms import (
    DateField,
    IntegerField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import URL, DataRequired, Length, Optional


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
    submit = SubmitField("Guardar")


class SalaForm(FlaskForm):
    nombre = StringField("Nombre de la sala", validators=[DataRequired(), Length(max=120)])
    plantilla_3d = SelectField("Plantilla", validators=[Optional()])
    orden = IntegerField("Orden en el recorrido", validators=[Optional()], default=0)
    submit = SubmitField("Guardar")
