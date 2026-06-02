"""Instancias de extensiones Flask, inicializadas en create_app().

Se definen aquí (sin app) para evitar imports circulares: los modelos importan
`db` desde este módulo, y la app las enlaza con init_app().
"""
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
