# Galería Virtual — Plataforma de Exposiciones Virtuales

Galería de arte **en 3D** para la web, multi-organizador, en producción en
**[galeriavirtual.org](https://galeriavirtual.org)** con
[AFESOL](https://afesol.org) como organizador piloto.

El visitante recorre las salas en primera persona (Babylon.js) — o en un
**modo 2D** pensado para el móvil — con hilo musical, ficha de exposición y
compartir en redes. El organizador declara su colección (número y tipo de
obras) y la plataforma **le construye una sala a medida**: las plantas
(rectangular, cruz, T…) se estiran hasta acogerla, dedicando cada pared a un
tipo de obra. Cada organizador gestiona lo suyo desde su panel, con
estadísticas de visitas e **interés por obra** — todo con visitantes anónimos,
sin rastreadores.

## Características

- 🚪 **Visor 3D** en primera persona con puerta cinematográfica, placas por
  obra e hilo musical · **modo 2D** para móvil con fichas de obra.
- 📐 **Plantas elásticas**: algoritmo que dimensiona la sala según la
  colección (cuadros, fotografías, infografías, dibujos).
- 🔒 **Visibilidad** por exposición: pública, enlace secreto o código de
  acceso · apertura por fechas o cierre manual.
- 📖 **Ficha de exposición**: leitmotiv, organizador con logo y web, autores
  con retrato y bio.
- 📊 **Estadísticas anónimas**: visitas por día/franja/dispositivo y
  contemplaciones por obra (gaze-detection en el 3D).
- 📡 **SEO y compartir**: Open Graph, JSON-LD, sitemap, iconos oficiales de
  RRSS vía endpoints intent (sin SDKs de terceros).

## Stack

Flask + SQLAlchemy/Alembic · PostgreSQL (Railway) / SQLite (local) ·
Cloudinary (imágenes y audio, CDN) · Babylon.js · HTML/CSS/JS vanilla.

## Documentación

- [docs/funcionalidades.md](docs/funcionalidades.md) — catálogo de
  funcionalidades y su técnica a grosso modo.
- [docs/estrategia_desarrollo.md](docs/estrategia_desarrollo.md) — estrategia,
  modelo de datos, comandos y cómo retomar el desarrollo.
- [docs/resumen.md](docs/resumen.md) — documento fundacional (histórico).

## Desarrollo local

```powershell
$env:FLASK_APP = "app.py"
$env:FLASK_SKIP_DOTENV = "1"
& ".\venv\Scripts\python.exe" -m pip install -r requirements.txt
& ".\venv\Scripts\python.exe" -m flask db upgrade
& ".\venv\Scripts\python.exe" -m flask crear-admin --email "tu@email" --password "tu-pass"
& ".\venv\Scripts\python.exe" -m flask run    # http://127.0.0.1:5000
```

---

*Galería Virtual v1.0 · J.C. Sobrepere*
