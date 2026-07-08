# Estrategia de desarrollo — Galería Virtual de Arte (GVA / AFESOL)

> Documento de referencia para **retomar el proyecto tras una interrupción no
> programada** (corte de sesión, cambio de equipo, pausa larga). Resume qué se
> está construyendo, cómo, en qué punto estamos y cómo continuar.
>
> Última actualización: 2026-07-08 — **Cambio de rumbo: plataforma
> multi-organizador**. Fases A–C + portal público + rebranding completados.

---

## 1. Visión del proyecto

**Plataforma de Exposiciones Virtuales**: galería Web en **3D** multi-organizador.

> ⚠️ **Cambio de rumbo (jul-2026):** de piloto single-tenant de AFESOL (admin
> único, una exposición publicada) a **plataforma con varios organizadores**,
> cada uno dueño de sus propias exposiciones, autores y obras.

Tres tipos de sesión:
- **Visitante** (anónimo): portal `/` con *cards* de las galerías publicadas →
  `/g/<slug>` recorre en primera persona la sala en 3D (Babylon.js).
- **Organizador** (`/admin`): gestiona SOLO sus exposiciones/salas/obras/autores.
  Alta **solo por invitación** (los crea el superadmin).
- **Superadmin** (`/plataforma`): CRUD de organizadores + estadísticas de visitas.

Estética: azul/blanco. Portal navy + acento cian; panel admin claro. Marca
**"Plataforma de Exposiciones Virtuales"** (ya no "SIT").

---

## 2. Stack tecnológico

| Capa | Tecnología |
|---|---|
| Backend | Python + **Flask** |
| ORM / migraciones | Flask-SQLAlchemy + Flask-Migrate (Alembic) |
| BD (local) | **SQLite** (`galeria_dev.db`) |
| BD (producción) | **PostgreSQL** en Railway |
| Imágenes | **Cloudinary** (CDN; guardamos `public_id` + `secure_url`) |
| Frontend | HTML5, CSS3 vanilla + Bootstrap, JS vanilla |
| 3D | **Babylon.js** (CDN) |
| Servidor prod | gunicorn |
| Hosting | **Railway** (deploy desde GitHub) |
| Repo | github.com:Beldic/GVA.git |

---

## 3. Estructura del proyecto

```
Galeria/
├─ app.py                     # entrypoint: app = create_app()
├─ requirements.txt
├─ Procfile                   # web: gunicorn app:app --bind 0.0.0.0:$PORT
├─ .env.example               # plantilla (copiar a .env en local)
├─ galeria_dev.db             # SQLite local (gitignored)
├─ backend/
│  ├─ app/
│  │  ├─ __init__.py          # create_app(): init extensiones + blueprints
│  │  ├─ config.py            # config por entorno (SQLite/Postgres)
│  │  ├─ extensions.py        # db, migrate
│  │  ├─ models/              # un archivo por entidad
│  │  │  ├─ usuario.py  autor.py  exposicion.py
│  │  │  └─ sala.py  zona.py  obra.py
│  │  ├─ routes/              # blueprints (main.py = público)
│  │  ├─ services/            # lógica (Cloudinary, etc.) — pendiente
│  │  ├─ static/              # css/ y js/gallery (Babylon)
│  │  └─ templates/           # base.html, index.html, gallery.html
│  └─ migrations/             # Alembic
└─ frontend/assets/           # imágenes/modelos servidos vía /frontend-assets
```

---

## 4. Modelo de datos (confirmado)

Jerarquía: `usuario 1─<N exposicion 1─<N sala 1─<N zona 1─<N obra >─N─1 autor`. Más `visita`.

| Tabla | Campos clave | Relaciones |
|---|---|---|
| **usuario** | email, password_hash, **nombre**, **rol** (`superadmin`/`organizador`), **activo** | dueño de exposiciones y autores |
| **autor** | **usuario_id (dueño)**, nombre, bio, foto_url, contacto | 1 ─< N obra |
| **exposicion** | **usuario_id (dueño)**, titulo, slug (único global), descripcion, fechas, **estado** (borrador/publicada) | 1 ─< N sala |
| **sala** | nombre, plantilla_3d, orden | 1 ─< N zona |
| **zona** | nombre, codigo, capacidad, tipo_admitido | 1 ─< N obra |
| **obra** | titulo, anio, tecnica, **ancho_cm/alto_cm**, tipo, descripcion, `cloudinary_public_id`, `cloudinary_url`, **orden** | → autor, → zona |
| **visita** | exposicion_id, created_at | estadísticas (1 por expo y sesión) |

**Decisiones de diseño:**
- **Propiedad:** exposiciones y autores tienen `usuario_id`. Los organizadores solo ven/tocan lo suyo; el superadmin es transversal. La propiedad de sala/zona/obra se hereda por la cadena hasta `exposicion.usuario_id` (`authz.exigir_acceso_exposicion`).
- **Autores privados** por organizador; la obra llega a su exposición por la cadena `obra→zona→sala→exposicion` (sin duplicar `exposicion_id`).
- **Posición = `zona_id` + `orden`**, con `UNIQUE(zona_id, orden)`. El 3D reparte y dimensiona según `ancho_cm/alto_cm`. **No hay coordenadas en BD.**
- Las **zonas las predefine la plantilla de sala**; el organizador solo asigna obras.
- La **geometría 3D** vive en el **frontend**, no en BD.
- **Cada organizador publica de forma independiente** (varias exposiciones publicadas a la vez; el portal `/g/<slug>` sirve cada una por su slug). Ya NO hay "una sola publicada global".

**Aparcado para fases posteriores:** conexiones/puertas entre salas en BD y
estadísticas de **clicks por obra** (engagement; las visitas por exposición ya están).

---

## 5. Hoja de ruta por fases

**Base single-tenant (1–6):** andamiaje ORM, autenticación, dashboard CRUD
(autores/exposiciones/salas/obras), Cloudinary, 3D dinámico y despliegue en
Railway — todo ✅ hecho antes del cambio de rumbo.

**Cambio de rumbo → plataforma multi-organizador:**

| Fase | Contenido | Estado |
|---|---|---|
| **A** | Modelo multi-organizador: roles `superadmin`/`organizador`, `usuario_id` en exposicion/autor, migración con backfill (organizador legado) | ✅ Hecho |
| **B** | Autorización y aislamiento: `authz.py`, scoping de `/admin` por dueño, publicación independiente, login de cuentas activas | ✅ Hecho |
| **C** | Panel de plataforma `/plataforma` (superadmin): CRUD de organizadores + **estadísticas de visitas** (tabla `visita`); login enruta por rol | ✅ Hecho |
| **Portal** | Portada pública con *cards* de galerías abiertas + `/g/<slug>`; rebranding SIT → Plataforma; puerta como transición de entrada/salida | ✅ Hecho |
| **E** | Pulido: seeds con dueño, docs y memoria al día | ✅ Hecho |
| — | **Pendiente:** desplegar el pivote en Railway (aplicar migraciones `a1b2c3d4e5f6` y `b2c3d4e5f6a7`); autoservicio de imágenes; clicks por obra | ⬜ |

> Cada fase se diseña/consensúa antes de implementar y se cierra con un commit.

---

## 6. Entornos y base de datos

- **Local:** si `DATABASE_URL` está vacía → SQLite (`galeria_dev.db`). Cero instalación.
- **Producción (Railway):** Railway inyecta `DATABASE_URL` (Postgres). `config.py`
  la detecta y normaliza `postgres://` → `postgresql://`.
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

# Crear/actualizar el administrador del panel
& ".\venv\Scripts\python.exe" -m flask crear-admin --email "tu@email" --password "tu-pass"

# Crear datos de ejemplo: exposición 'afesol_cero' (40 dibujos + 15 cuadros, placeholders)
& ".\venv\Scripts\python.exe" -m flask seed-afesol-cero --reset

# Arrancar en local
& ".\venv\Scripts\python.exe" app.py     # http://127.0.0.1:5000
```

**Panel de administración:** `/admin/login` (login) → `/admin/` (dashboard).
Todo lo que cuelgue de `/admin` requiere sesión.

---

## 8. Gotchas conocidos (¡importante!)

- **`.env` del Escritorio:** existe `C:\Users\jordi\Desktop\.env` con una
  `DATABASE_URL` de **Render**. El CLI de `flask` auto-carga `.env` rastreando
  hacia carpetas superiores, así que **sin `FLASK_SKIP_DOTENV=1` los comandos
  `flask` se conectan a Render en vez de a SQLite local**. El `config.py` de la
  app ya carga solo el `.env` del proyecto, pero el CLI no.
  → *Solución definitiva pendiente: mover/borrar ese `.env` del Escritorio.*
- **psycopg2-binary:** usar `==2.9.10` (la 2.9.9 no tiene wheel para Python
  3.13 e intenta compilar). En local no se usa (SQLite); solo en Railway.

---

## 9. Despliegue en Railway

- El repo está conectado; Railway hace build con Nixpacks (detecta Python por
  `requirements.txt`) y arranca con el `Procfile`.
- Generar dominio público: **Settings → Networking → Generate Domain**.
- Postgres (Fase 6): **New → Database → PostgreSQL**; Railway inyecta
  `DATABASE_URL`. Hay que ejecutar `flask db upgrade` contra la BD de prod.

---

## 10. Cómo retomar tras una interrupción

1. Lee este documento y la sección **5 (hoja de ruta)** para ubicar la fase actual.
2. Verifica el entorno: `git status`, venv activo, `galeria_dev.db` presente.
3. Si faltan tablas: `flask db upgrade` (con las variables de la sección 7).
4. Revisa los commits recientes (`git log --oneline`) para ver hasta dónde se llegó.
5. Continúa por la **siguiente fase no marcada** en la hoja de ruta.

> Notas de diseño y decisiones también guardadas en la memoria del asistente
> (`db-data-model`, `flujo-migraciones-dev`, `project-gva`).
