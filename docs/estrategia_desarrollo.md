# Estrategia de desarrollo — Galería Virtual de Arte (GVA / AFESOL)

> Documento de referencia para **retomar el proyecto tras una interrupción no
> programada** (corte de sesión, cambio de equipo, pausa larga). Resume qué se
> está construyendo, cómo, en qué punto estamos y cómo continuar.
>
> Última actualización: 2026-07-12 — **v1.0 en producción**
> (galeriavirtual.org). Catálogo completo de funcionalidades y su técnica en
> [funcionalidades.md](funcionalidades.md).

---

## 1. Visión del proyecto

**Plataforma de Exposiciones Virtuales**: galería Web en **3D** multi-organizador,
en producción en **galeriavirtual.org** con AFESOL como organizador piloto.

Tres tipos de sesión:
- **Visitante** (anónimo, sin rastreo): portal `/` con *cards* → ficha de la
  exposición (`/g/<slug>/ficha`) → puerta → sala 3D en primera persona
  (Babylon.js), o **modo 2D** en móvil (`?modo=2d`). Exposiciones públicas,
  de enlace secreto o privadas con código; hilo musical; compartir en RRSS.
- **Organizador** (`/admin`): gestiona SOLO sus exposiciones/salas/obras/autores
  + su perfil público + dashboard de estadísticas. Alta solo por invitación.
- **Superadmin** (`/plataforma`): CRUD de organizadores, reasignación de
  exposiciones y estadísticas globales.

Estética: azul/blanco. Portal navy + acento cian; panel admin claro. Marca
**"Galería Virtual"** con logo hexagonal y favicon GV.

---

## 2. Stack tecnológico

| Capa | Tecnología |
|---|---|
| Backend | Python + **Flask** (app factory + blueprints) |
| ORM / migraciones | Flask-SQLAlchemy + Flask-Migrate (Alembic) |
| Autenticación | Flask-Login + CSRF global (Flask-WTF) |
| BD (local) | **SQLite** (`galeria_dev.db`) |
| BD (producción) | **PostgreSQL** en Railway |
| Imágenes y audio | **Cloudinary** (CDN; guardamos `public_id` + `secure_url`) |
| Frontend | HTML5, CSS3 vanilla + Bootstrap, JS vanilla |
| 3D | **Babylon.js** (CDN) — motor de plantas propio data-driven |
| Servidor prod | gunicorn (+ ProxyFix para https tras el proxy) |
| Hosting | **Railway** (deploy automático desde GitHub) |
| Repo | github.com:Beldic/GVA.git |

---

## 3. Estructura del proyecto

```
Galeria/
├─ app.py                     # entrypoint; en Postgres aplica migraciones al arrancar
├─ requirements.txt / Procfile / .env.example
├─ galeria_dev.db             # SQLite local (gitignored)
├─ docs/                      # este documento + funcionalidades.md + resumen.md
├─ backend/
│  ├─ app/
│  │  ├─ __init__.py          # create_app(): extensiones, ProxyFix, blueprints
│  │  ├─ config.py  extensions.py  authz.py  bootstrap.py  cli.py  utils.py
│  │  ├─ plantillas.py        # plantillas de sala + PLANTAS ELÁSTICAS (ajustar_planta)
│  │  ├─ models/              # usuario, autor, exposicion, sala, zona, obra,
│  │  │                       # visita, vista_obra
│  │  ├─ routes/              # main (público), admin (organizador), plataforma
│  │  ├─ services/            # gallery (serialización/OG), stats, cloudinary_service
│  │  ├─ static/
│  │  │  ├─ css/              # main, portal, gallery, gallery2d, ficha, door, admin…
│  │  │  ├─ js/gallery/       # main, room, painting, camera, scene (visor 3D)
│  │  │  ├─ img/              # logo + logos de organizadores (convención)
│  │  │  └─ favicons/
│  │  └─ templates/           # portal, ficha, visor, 2D, admin/, plataforma/,
│  │                          # parciales (_og_expo, _iconos_rrss)
│  └─ migrations/             # Alembic (11 revisiones, todas aditivas)
└─ frontend/assets/           # legado, servido vía /frontend-assets
```

---

## 4. Modelo de datos (confirmado)

Jerarquía: `usuario 1─<N exposicion 1─<N sala 1─<N zona 1─<N obra >─N─1 autor`.
Más `visita` y `vista_obra` (métricas anónimas).

| Tabla | Campos clave | Notas |
|---|---|---|
| **usuario** | email, password_hash, nombre, **web, logo_public_id/url**, rol (`superadmin`/`organizador`), activo | perfil público del organizador |
| **autor** | usuario_id (dueño), nombre, bio, **foto_public_id**/foto_url, contacto | privado por organizador |
| **exposicion** | usuario_id, titulo, slug único, descripcion (leitmotiv), fechas, estado, **visibilidad** (publica/enlace/codigo) + codigo_acceso_hash, **cerrada_manual** (→ propiedad `apertura`), **portada_obra_id**, **musica_public_id/url** | cascada a salas y visitas |
| **sala** | nombre, plantilla_3d, **parametros** (JSON: dimensiones elásticas; NULL = medidas por defecto), orden | |
| **zona** | codigo (= pared 3D), nombre, capacidad, tipo_admitido | las siembra la plantilla (estática o elástica) |
| **obra** | titulo, **tipo** (cuadro/fotografia/infografia/dibujo), anio, tecnica, ancho_cm/alto_cm (proporción real de la imagen), descripcion, cloudinary_*, orden | UNIQUE(zona_id, orden) |
| **visita** | exposicion_id, **dispositivo, modo**, created_at | 1 por expo y sesión; anónima |
| **vista_obra** | obra_id, **modo** (3d=contemplación / 2d=ficha), created_at | interés por obra; anónima |

**Decisiones de diseño vigentes:**
- Propiedad y aislamiento por `usuario_id`, heredada por la cadena
  obra→zona→sala→exposición (`authz.exigir_acceso_exposicion`).
- Posición = `zona_id` + `orden`; sin coordenadas en BD. La **geometría 3D vive
  en el frontend** (`room.js`), parametrizada por `sala.parametros`.
- Visitante **anónimo siempre**: métricas con dimensiones agregadas, sin
  identificadores de persona (decisión RGPD deliberada).
- `portada_obra_id` es entero SIN FK (evita ciclo exposicion↔obra); se valida
  en lectura.

---

## 5. Hoja de ruta por fases

**Base single-tenant (1–6)** ✅ y **pivote multi-organizador (A–C + portal)** ✅
— ver historial de este documento.

**Sprint v1.0 (9–12 jul-2026), todo ✅ desplegado en producción:**

| Bloque | Contenido |
|---|---|
| Acceso | Visibilidad pública/enlace/código · apertura por fechas + cierre manual |
| Portal | Badges de estado, candado, portada elegible, logo de organizador, footer, favicon, logo de marca |
| Plataforma | Sección Exposiciones + reasignación de dueño (autores incluidos) |
| Visor | Hilo musical (♪/M), ventana de instrucciones, HUD accesible, puerta responsive, compartir |
| Móvil | **Modo 2D** completo + detección táctil robusta + escotilla en la puerta |
| Estadísticas | Dashboard del organizador (KPIs, series, frecuencias, desgloses) + **interés por obra** (contemplación 3D / ficha 2D) |
| Salas | **Plantas elásticas** (4 formas, algoritmo de ajuste) + 4 tipos de obra + asistente de nueva exposición + proporciones reales de imagen |
| Catálogo | **Ficha de exposición** + Mi perfil (web/logo) + retratos de autor |
| SEO | OG/Twitter cards, JSON-LD, sitemap, robots, iconos oficiales de RRSS |

**Pendiente / aparcado:** ver la sección final de
[funcionalidades.md](funcionalidades.md) (formas complejas multi-sala,
girar imágenes, placeholders opcionales, perfiles sociales…).

> Cada fase se diseña/consensúa antes de implementar y se cierra con un commit
> (coautoría J.C. Sobrepere + Claude).

---

## 6. Entornos y base de datos

- **Local:** si `DATABASE_URL` está vacía → SQLite (`galeria_dev.db`). Cero instalación.
- **Producción (Railway):** Railway inyecta `DATABASE_URL` (Postgres). `config.py`
  la detecta y normaliza `postgres://` → `postgresql://`. Al arrancar, `app.py`
  aplica migraciones y asegura el superadmin (`bootstrap.py`).
- Variables en `.env` (local) / panel de Railway (prod). Plantilla en `.env.example`.

---

## 7. Comandos de desarrollo

Desde la raíz del proyecto, con el venv (`venv/`, Python 3.13):

```powershell
# Variables necesarias para el CLI de flask
$env:FLASK_APP = "app.py"
$env:FLASK_SKIP_DOTENV = "1"   # ver gotcha en sección 8

# Instalar dependencias
& ".\venv\Scripts\python.exe" -m pip install -r requirements.txt

# Migraciones
& ".\venv\Scripts\python.exe" -m flask db migrate -m "mensaje"
& ".\venv\Scripts\python.exe" -m flask db upgrade

# Crear/actualizar el superadmin del panel
& ".\venv\Scripts\python.exe" -m flask crear-admin --email "tu@email" --password "tu-pass"

# Datos de ejemplo (placeholders)
& ".\venv\Scripts\python.exe" -m flask seed-afesol-cero --reset
& ".\venv\Scripts\python.exe" -m flask seed-rectangular --reset --publicar

# Arrancar en local (accesible desde el móvil en la misma red con --host)
& ".\venv\Scripts\python.exe" -m flask run --host=0.0.0.0   # http://127.0.0.1:5000
```

**Paneles:** `/admin/login` → organizador · `/plataforma` → superadmin (el
login enruta por rol).

---

## 8. Gotchas conocidos (¡importante!)

- **`.env` del Escritorio:** existe `C:\Users\jordi\Desktop\.env` con una
  `DATABASE_URL` de **Render**. El CLI de `flask` auto-carga `.env` rastreando
  hacia carpetas superiores, así que **sin `FLASK_SKIP_DOTENV=1` los comandos
  `flask` se conectan a Render en vez de a SQLite local**.
- **psycopg2-binary:** usar `==2.9.10` (la 2.9.9 no tiene wheel para Python 3.13).
- **Caché del visor:** los módulos JS del 3D llevan versión en el import
  (`room.js?v=N`) y una marca de build en consola (`[gallery] visor build vN`).
  Al tocar el visor, **subir ambos** o el navegador servirá JS viejo.
- **GPU Apple/Metal (Mac M1):** el visor se prueba también en Mac; los bugs
  de Z-fighting/backface ya corregidos están documentados en los comentarios
  de `room.js`/`painting.js` — no reintroducir `preserveDrawingBuffer` ni
  `backFaceCulling=false`.
- **Plantillas y zonas:** cada `codigo` de zona en `plantillas.py` debe tener
  su tramo de pared homónimo en `room.js` (hay comprobación en los smoke
  tests del scratchpad).

---

## 9. Despliegue en Railway

- **En producción**: dominio propio **galeriavirtual.org**; deploy automático
  con cada push a `main` (build Nixpacks + `Procfile` con gunicorn).
- Las **migraciones se aplican solas** al arrancar el proceso web (solo en
  Postgres); el superadmin se asegura con `ADMIN_EMAIL`/`ADMIN_PASSWORD`.
- Variables en el panel de Railway: `DATABASE_URL` (inyectada), Cloudinary
  (`CLOUDINARY_*`), `SECRET_KEY`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`.
- SEO: sitemap enviado a Google Search Console (`/sitemap.xml`).

---

## 10. Cómo retomar tras una interrupción

1. Lee este documento y [funcionalidades.md](funcionalidades.md) para ubicarte.
2. Verifica el entorno: `git status`, venv activo, `galeria_dev.db` presente.
3. Si faltan tablas: `flask db upgrade` (con las variables de la sección 7).
4. Revisa los commits recientes (`git log --oneline`) para ver hasta dónde se llegó.
5. Continúa por lo **pendiente/aparcado** de funcionalidades.md o lo que pida
   el momento.

> Notas de diseño y decisiones también guardadas en la memoria del asistente
> (`db-data-model`, `flujo-migraciones-dev`, `project-gva`, `commits-coautoria-duo`).
