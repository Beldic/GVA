from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user

import re

from backend.app.extensions import csrf, db
from backend.app.models import Exposicion, Obra, Sala, Visita, VistaObra, Zona
from backend.app.models.exposicion import (
    ESTADO_PUBLICADA,
    VISIBILIDAD_ENLACE,
    VISIBILIDAD_PUBLICA,
)
from backend.app.models.visita import (
    DISPOSITIVO_ESCRITORIO,
    DISPOSITIVO_MOVIL,
    MODO_2D,
    MODO_3D,
)
from backend.app.models.vista_obra import VISTA_2D, VISTA_3D
from backend.app.services.gallery import (
    autores_de_expo,
    foto_autor,
    logo_organizador,
    og_de_expo,
    resumen_exposicion,
    serializar_sala,
)

bp = Blueprint("main", __name__)

_UA_MOVIL = re.compile(r"Mobi|Android|iPhone|iPad|iPod", re.IGNORECASE)


def _registrar_visita(expo) -> None:
    """Cuenta una visita por exposición y sesión de navegador: recargar la
    página no vuelve a sumar. Guarda dispositivo y modo del primer acceso
    (dimensiones anónimas; nunca identidad del visitante)."""
    vistas = session.get("expos_vistas", [])
    if expo.id in vistas:
        return
    ua = request.headers.get("User-Agent", "")
    db.session.add(
        Visita(
            exposicion_id=expo.id,
            dispositivo=(
                DISPOSITIVO_MOVIL if _UA_MOVIL.search(ua) else DISPOSITIVO_ESCRITORIO
            ),
            modo=MODO_2D if request.args.get("modo") == "2d" else MODO_3D,
        )
    )
    db.session.commit()
    session["expos_vistas"] = vistas + [expo.id]


def _puede_gestionar(expo) -> bool:
    """El dueño de la exposición y el superadmin entran siempre (previsualizan
    aunque esté cerrada o pida código), sin sumar visitas."""
    return current_user.is_authenticated and (
        current_user.es_superadmin or expo.usuario_id == current_user.id
    )


def _expo_visible(slug):
    """La exposición que puede verse en esta petición: publicada para todo el
    mundo; en cualquier estado (borrador incluido) para su dueño o el
    superadmin — la previsualización desde el panel."""
    expo = Exposicion.query.filter_by(slug=slug).first_or_404()
    if expo.estado != ESTADO_PUBLICADA and not _puede_gestionar(expo):
        abort(404)
    return expo


def _visitante_autorizado(expo) -> bool:
    """El visitante ya introdujo el código correcto en esta sesión de navegador."""
    return expo.id in session.get("expos_autorizadas", [])


def _autorizar_visitante(expo) -> None:
    autorizadas = session.get("expos_autorizadas", [])
    if expo.id not in autorizadas:
        session["expos_autorizadas"] = autorizadas + [expo.id]


@bp.get("/")
def index():
    """Portal: rejilla de galerías publicadas, cada card con su estado de
    apertura (abierta/próximamente/cerrada) y candado si pide código. Solo
    las de enlace secreto quedan fuera del listado."""
    publicadas = (
        Exposicion.query.filter(
            Exposicion.estado == ESTADO_PUBLICADA,
            Exposicion.visibilidad != VISIBILIDAD_ENLACE,
        )
        .order_by(Exposicion.created_at.desc())
        .all()
    )
    galerias = [resumen_exposicion(expo) for expo in publicadas]
    return render_template("index.html", galerias=galerias)


@bp.get("/g/<slug>")
def gallery(slug):
    """Muestra en 3D la primera sala (por orden) de la exposición publicada
    con ese slug. Para el visitante anónimo hay dos puertas: la exposición
    debe estar abierta (fechas/cierre manual) y, si pide código, haberlo
    introducido. El dueño y el superadmin entran siempre. Si no tiene salas,
    `datos` es None y la plantilla avisa."""
    expo = _expo_visible(slug)
    og = og_de_expo(expo)
    if not _puede_gestionar(expo):
        if not expo.abierta:
            return render_template("gallery_cerrada.html", expo=expo, og=og)
        if expo.requiere_codigo and not _visitante_autorizado(expo):
            return render_template("gallery_codigo.html", expo=expo, og=og)
        _registrar_visita(expo)
    datos = serializar_sala(expo.salas[0]) if expo.salas else None
    es_preview = expo.estado != ESTADO_PUBLICADA
    # Para el gestor, la salida del visor vuelve a su panel, no al portal.
    es_gestor = _puede_gestionar(expo)
    # Modo 2D (?modo=2d): la misma sala como galería vertical, pensada para
    # móvil. Pasa por las mismas puertas de acceso que el 3D.
    if request.args.get("modo") == "2d":
        return render_template(
            "gallery_2d.html", datos=datos, og=og, expo=expo,
            es_preview=es_preview, es_gestor=es_gestor,
        )
    return render_template(
        "gallery.html", datos=datos, og=og, expo=expo,
        es_preview=es_preview, es_gestor=es_gestor,
    )


@bp.get("/g/<slug>/ficha")
def gallery_ficha(slug):
    """Ficha de la exposición: el catálogo previo a la puerta — leitmotiv
    íntegro, organizador (logo + web) y autores con retrato y bio. Mismas
    puertas de acceso que el visor; no cuenta visita (eso lo hace entrar)."""
    expo = _expo_visible(slug)
    og = og_de_expo(expo)
    if not _puede_gestionar(expo):
        if not expo.abierta:
            return render_template("gallery_cerrada.html", expo=expo, og=og)
        if expo.requiere_codigo and not _visitante_autorizado(expo):
            return render_template("gallery_codigo.html", expo=expo, og=og)
    autores = [
        {"autor": a, "foto": foto_autor(a)} for a in autores_de_expo(expo)
    ]
    return render_template(
        "gallery_ficha.html",
        expo=expo,
        og=og,
        autores=autores,
        logo=logo_organizador(expo.propietario),
    )


@bp.get("/robots.txt")
def robots():
    """SEO: los paneles no se indexan; el resto sí, con el sitemap a mano."""
    cuerpo = (
        "User-agent: *\n"
        "Disallow: /admin\n"
        "Disallow: /plataforma\n"
        f"Sitemap: {url_for('main.sitemap', _external=True)}\n"
    )
    return cuerpo, 200, {"Content-Type": "text/plain; charset=utf-8"}


@bp.get("/sitemap.xml")
def sitemap():
    """Sitemap con el portal y las exposiciones publicadas visibles (las de
    enlace secreto o con código no se anuncian a los buscadores)."""
    publicas = Exposicion.query.filter(
        Exposicion.estado == ESTADO_PUBLICADA,
        Exposicion.visibilidad == VISIBILIDAD_PUBLICA,
    ).all()
    urls = [f"<url><loc>{url_for('main.index', _external=True)}</loc></url>"]
    for expo in publicas:
        loc = url_for("main.gallery", slug=expo.slug, _external=True)
        urls.append(f"<url><loc>{loc}</loc></url>")
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>\n"
    )
    return xml, 200, {"Content-Type": "application/xml; charset=utf-8"}


@bp.post("/g/<slug>/obra-vista")
@csrf.exempt  # beacon anónimo del visor; sin sesión de formulario que proteger
def obra_vista(slug):
    """Registra interés anónimo por una obra: contemplación en el 3D o
    apertura de su ficha en el 2D. Mismas puertas que el visor; una fila por
    obra y sesión de navegador; los gestores no cuentan."""
    expo = _expo_visible(slug)
    if _puede_gestionar(expo):
        return "", 204  # previsualización del dueño/superadmin: no sesga
    if not expo.abierta:
        return "", 403
    if expo.requiere_codigo and not _visitante_autorizado(expo):
        return "", 403

    data = request.get_json(silent=True) or {}
    modo = data.get("modo")
    if modo not in (VISTA_3D, VISTA_2D):
        return "", 400
    try:
        obra_id = int(data.get("obra_id"))
    except (TypeError, ValueError):
        return "", 400

    vistas = session.get("obras_vistas", [])
    if obra_id in vistas:
        return "", 204

    # La obra debe colgar en ESTA exposición (nada de inflar ajenas).
    pertenece = (
        db.session.query(Obra.id)
        .join(Zona, Obra.zona_id == Zona.id)
        .join(Sala, Zona.sala_id == Sala.id)
        .filter(Obra.id == obra_id, Sala.exposicion_id == expo.id)
        .first()
    )
    if pertenece is None:
        return "", 404

    db.session.add(VistaObra(obra_id=obra_id, modo=modo))
    db.session.commit()
    # Dedupe por sesión, con tope para no engordar la cookie sin límite.
    session["obras_vistas"] = (vistas + [obra_id])[-300:]
    return "", 204


@bp.post("/g/<slug>/codigo")
def gallery_codigo(slug):
    """Valida el código de acceso de una exposición privada y recuerda la
    autorización en la sesión del navegador (el visitante sigue anónimo)."""
    expo = Exposicion.query.filter_by(
        slug=slug, estado=ESTADO_PUBLICADA
    ).first_or_404()
    codigo = (request.form.get("codigo") or "").strip()
    if expo.requiere_codigo and expo.check_codigo_acceso(codigo):
        _autorizar_visitante(expo)
    else:
        flash("Código incorrecto. Vuelve a intentarlo.", "error")
    return redirect(url_for("main.gallery", slug=slug))
