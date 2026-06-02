# Estrategia de desarrollo — Galería Virtual de Arte (GVA / AFESOL)

> Documento de referencia para **retomar el proyecto tras una interrupción no
> programada** (corte de sesión, cambio de equipo, pausa larga). Resume qué se
> está construyendo, cómo, en qué punto estamos y cómo continuar.
>
> Última actualización: 2026-06-02 — fin de la **Fase 2 (autenticación)**.

---

## 1. Visión del proyecto

Galería Web en **3D** para mostrar las exposiciones de arte de la asociación
**AFESOL**. El visitante recorre en primera persona unas salas virtuales
(Babylon.js) donde cuelgan las obras. Un **comisario/admin** gestiona todo desde
un panel: crea exposiciones, sube imágenes y las coloca en las salas.

Estética: azul y blanco, elegante y homogénea. Fuente *Cormorant Garamond*.

Primera exposición real: **40 dibujos A3 + 15 cuadros de ~1,5 m** (55 piezas)
repartidos en **varias salas conectadas**.

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

Jerarquía: `exposicion 1─<N sala 1─<N zona 1─<N obra >─N─1 autor`. Más `usuario`.

| Tabla | Campos clave | Relaciones |
|---|---|---|
| **usuario** | email, password_hash, rol | login del panel |
| **autor** | nombre, bio, foto_url, contacto | 1 ─< N obra |
| **exposicion** | titulo, slug, descripcion, fechas, **estado** (borrador/publicada) | 1 ─< N sala |
| **sala** | nombre, plantilla_3d, orden | 1 ─< N zona |
| **zona** | nombre, codigo, capacidad, tipo_admitido | 1 ─< N obra |
| **obra** | titulo, anio, tecnica, **ancho_cm/alto_cm**, tipo, descripcion, `cloudinary_public_id`, `cloudinary_url`, **orden** | → autor, → zona |

**Decisiones de diseño:**
- La obra llega a su exposición por la cadena `obra→zona→sala→exposicion` (sin duplicar `exposicion_id`).
- **Posición = `zona_id` + `orden`**, con `UNIQUE(zona_id, orden)`. El 3D reparte y dimensiona las obras automáticamente según `ancho_cm/alto_cm`. **No hay coordenadas en BD.**
- Las **zonas las predefine la plantilla de sala** (se siembran al crear la sala); el comisario solo asigna obras.
- La **geometría 3D** (salas, puertas, coordenadas de zonas) vive en el **frontend**, no en BD.
- Una obra pertenece a **una sola** exposición; para recolocar se crean exposiciones nuevas. **Un autor por obra**.
- Solo **una exposición publicada** a la vez (la galería pública muestra esa).

**Aparcado para fases posteriores:** conexiones/puertas entre salas en BD y
tabla de **estadísticas** de clicks por obra (engagement).

---

## 5. Hoja de ruta por fases

| # | Fase | Estado |
|---|---|---|
| 1 | **Andamiaje ORM** — extensiones, config, modelos, 1ª migración, BD SQLite | ✅ Hecho |
| 2 | **Autenticación** — Flask-Login, login/logout, `/admin` protegido, comando `crear-admin` | ✅ Hecho |
| 3 | **Dashboard CRUD** — exposiciones, salas (desde plantilla), autores, obras + asignar zona/orden | ⏳ Siguiente |
| 4 | **Cloudinary** — subida en el formulario de obra (`public_id`/`secure_url`) | ⬜ |
| 5 | **API + 3D dinámico** — endpoint de la expo publicada; `painting.js` deja de estar hardcodeado | ⬜ |
| 6 | **Postgres en Railway** — provisionar BD, variables, migraciones en prod, deploy | ⬜ |

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
