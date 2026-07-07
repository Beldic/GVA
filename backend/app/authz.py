"""Autorización del panel: roles y propiedad de datos.

En la plataforma multi-organizador cada `organizador` solo puede ver y tocar sus
propios datos. El `superadmin` es transversal: pasa cualquier comprobación de
propiedad (gestiona la plataforma entera).
"""
from functools import wraps

from flask import abort
from flask_login import current_user


def rol_requerido(*roles):
    """Exige que el usuario autenticado tenga uno de los roles dados.

    El superadmin siempre pasa. Úsese junto a `@login_required` (que ya
    garantiza la autenticación y redirige al login si falta)."""

    def decorador(vista):
        @wraps(vista)
        def envoltorio(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if not current_user.es_superadmin and current_user.rol not in roles:
                abort(403)
            return vista(*args, **kwargs)

        return envoltorio

    return decorador


def exigir_propietario(usuario_id) -> None:
    """Aborta con 403 si el usuario actual no es dueño del recurso.

    Acepta el `usuario_id` del recurso. El superadmin nunca es bloqueado."""
    if current_user.es_superadmin:
        return
    if usuario_id != current_user.id:
        abort(403)


def exigir_acceso_exposicion(expo) -> None:
    """Comprueba la propiedad de una exposición (y, por la cadena
    obra→zona→sala→exposicion, de todo lo que cuelga de ella)."""
    exigir_propietario(expo.usuario_id)
