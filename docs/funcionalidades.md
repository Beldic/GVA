# Funcionalidades — Plataforma de Exposiciones Virtuales (GVA)

> Catálogo de lo que hace la plataforma y cómo está resuelto técnicamente,
> a grosso modo. Para la hoja de ruta y cómo retomar el proyecto, ver
> [estrategia_desarrollo.md](estrategia_desarrollo.md).
>
> Última actualización: 2026-07-12.

---

## 1. El recorrido del visitante

**Portal → ficha → puerta → sala 3D** (o modo 2D en el móvil). El visitante es
**anónimo por diseño**: sin cuentas, sin cookies de rastreo, sin identificadores
persistentes (decisión deliberada de privacidad/RGPD).

### Portal (`/`)
Rejilla de *cards* de las exposiciones publicadas. Cada card muestra portada,
badge de estado (**Abierta / Próximamente / Cerrada**), candado si pide código,
logo y nombre del organizador, contadores y fechas. Las no abiertas se ven pero
no se pueden visitar. Footer de créditos.
- *Técnica:* `routes/main.py::index` + `services/gallery.py::resumen_exposicion`
  + `templates/index.html` + `static/css/portal.css`.
- *Portada de card*, por prioridad: obra elegida por el organizador →
  logo del organizador → primera obra con imagen → emblema.

### Ficha de exposición (`/g/<slug>/ficha`)
El catálogo previo a la puerta: rótulo "Organiza" + logo (clicable a la web del
organizador), título, fechas, **leitmotiv íntegro**, autores con obra colgada
(retrato circular + bio), botones *Entrar en 3D* / *Ver en 2D* y compartir.
- *Técnica:* `main.py::gallery_ficha` + `gallery_ficha.html` + `ficha.css`.
  Mismas puertas de acceso que el visor.

### Visor 3D (`/g/<slug>`)
Recorrido en primera persona (Babylon.js): puerta cinematográfica de entrada,
ventana de instrucciones (WASD/ratón/M/Esc + casilla de hilo musical), placas
por obra, HUD con salir/compartir/música, salida por la puerta.
- *Técnica:* `static/js/gallery/` — `main.js` (orquestación, puertas, HUD),
  `room.js` (motor de plantas data-driven: celdas + tramos de pared),
  `painting.js` (marco+lienzo+placa por obra), `camera.js` (primera persona
  con colisiones), `scene.js` (montaje + detección de contemplación).
  Los datos llegan como JSON embebido (`services/gallery.py::serializar_sala`).
- Marca de build en consola (`[gallery] visor build vN`) para detectar caché.

### Modo 2D (`/g/<slug>?modo=2d`)
La misma sala como galería vertical para móvil: secciones por zona en orden de
recorrido, rejilla de obras con imagen ligera, ficha `<dialog>` con navegación
anterior/siguiente, botón de música flotante y compartir.
- *Técnica:* `gallery_2d.html` + `gallery2d.css`. Misma ruta y puertas que el
  3D. El visor detecta móvil por puntero principal (`pointer: coarse`) y ofrece
  el enlace; la puerta 3D lleva escotilla "Ver en modo 2D".

### Hilo musical
Pista de audio por exposición (opcional) que suena en bucle durante la visita.
Arranca con el primer gesto (requisito de autoplay de los navegadores), casilla
en la ventana de instrucciones, botón ♪ en el HUD y tecla **M**.
- *Técnica:* `exposicion.musica_public_id/musica_url` (Cloudinary,
  `resource_type=video`), subida/reemplazo/quitar en el formulario de la expo.

---

## 2. Acceso y visibilidad

### Visibilidad por exposición
- **Pública**: aparece en el portal, entra cualquiera.
- **Enlace secreto**: no se lista; entra quien tenga la URL.
- **Privada con código**: pantalla que pide un código de paso; la autorización
  se recuerda en la sesión del navegador (visitante sigue anónimo).
- *Técnica:* `exposicion.visibilidad` + `codigo_acceso_hash` (Werkzeug, nunca
  en claro). Gate en `main.py::gallery` + `gallery_codigo.html`.

### Apertura
Calculada: **cierre manual** del organizador (botones Cerrar/Reabrir) o
**fechas** (antes de inicio → Próximamente; pasada la de fin → Cerrada). Las
cerradas se ven en el portal pero solo el dueño o el superadmin entran al 3D.
- *Técnica:* `exposicion.cerrada_manual` + propiedad `apertura`;
  `gallery_cerrada.html` para quien llegue por URL.

---

## 3. El organizador y su panel (`/admin`)

Multi-organizador con aislamiento estricto: cada organizador ve y toca SOLO lo
suyo (`authz.py`; la propiedad sube por la cadena obra→zona→sala→exposición).

### Asistente de nueva exposición
Título + **leitmotiv** + fechas + visibilidad + música + **colección** (nº de
obras por tipo) + **planta**, con recomendación en vivo. La exposición nace con
su *Sala principal* sembrada a medida.

### Plantas elásticas
4 formas (clásica, rectangular, **cruz**, T) que se **estiran entre límites**
según la colección declarada. El algoritmo busca el estiramiento mínimo,
dedica **una pared a un tipo** (cuadros en paredes principales) y guarda las
dimensiones en `sala.parametros` (JSON); `room.js` construye la geometría con
ellas. Si ni al máximo cabe: se crea igual y se avisa del excedente.
- *Técnica:* `plantillas.py` — `ELASTICAS` (specs paramétricas),
  `ajustar_planta()`, `METROS_HUECO` (cuadro 1,8 m · fotografía 1,2 ·
  infografía 1,1 · dibujo 0,8). Recomendación en vivo vía
  `POST /admin/plantas/ajustar` (misma fuente de verdad).

### Tipos de obra
**Cuadro, fotografía, infografía y dibujo** (`obra.TIPOS_OBRA`), cada uno con
medidas por defecto. Al subir imágenes, las medidas de la obra **respetan la
proporción real** de la imagen (Cloudinary devuelve los píxeles); botón
"Ajustar medidas a la proporción de la imagen" para rescatar obras antiguas.

### Gestión de contenido
- CRUD de exposiciones, salas, obras y autores (autores privados por organizador).
- **Carga múltiple**: subida directa navegador → Cloudinary (firmada) y alta en
  lote ocupando huecos libres en orden de recorrido.
- **Portada de card**: acción "Hacer/Quitar portada" en cada obra.
- **Mi perfil**: nombre visible, web y logo subible (aparece en cards y ficha).
- **Autores**: bio + retrato subible (o URL manual).

### Dashboard de estadísticas
KPIs (total, 7/30 días, abiertas/publicadas), gráfica de visitas por día,
frecuencia por día de semana y franja horaria (en hora española), desglose
móvil/escritorio y 3D/2D, **obras con más interés** (top 10) y tabla por
exposición. La columna "Interés" también en el detalle de sala.
- *Técnica:* `services/stats.py::panel_organizador` — una consulta + agregados
  en Python (portabilidad SQLite/Postgres, TZ Europe/Madrid).

---

## 4. Métricas anónimas (sin identidad del visitante)

- **visita**: una por exposición y sesión de navegador, con dimensiones
  anónimas `dispositivo` (user-agent) y `modo` (3d/2d). Los gestores no cuentan.
- **vista_obra** (interés por obra): en el 3D, **contemplación** = mantener un
  cuadro en el centro de la vista a <5 m durante 2 s (ray-picking en
  `scene.js`); en el 2D, apertura de la ficha de la obra. Beacon
  `POST /g/<slug>/obra-vista` con dedupe por sesión y validación de pertenencia.

---

## 5. Plataforma (superadmin, `/plataforma`)

CRUD de organizadores (alta con contraseña temporal, edición, reset, borrado en
cascada), **reasignación de exposiciones** entre organizadores (los autores se
mueven con ella salvo compartidos, con aviso) y estadísticas globales.

---

## 6. SEO y compartir

- **Open Graph + Twitter Cards** por exposición (portada, título, leitmotiv);
  las expos con código **no** exponen su portada. **JSON-LD ExhibitionEvent**
  (fechas, organizador). Canonical y meta descripciones dinámicas.
- **robots.txt** (paneles fuera del índice) y **sitemap.xml** (solo públicas).
- **Compartir sin terceros**: endpoints intent oficiales (WhatsApp, X,
  Facebook, Telegram, LinkedIn) + copiar enlace — glifos oficiales en SVG
  monocromo (`templates/_iconos_rrss.html`). En móvil, compartir nativo
  (`navigator.share`). Instagram no ofrece API web de compartir (cubierto vía
  compartir nativo en su app).
- *Técnica:* `services/gallery.py::og_de_expo`, parcial `_og_expo.html`,
  `ProxyFix` para URLs absolutas `https` tras el proxy de Railway.

---

## 7. Marca

Logo oficial (sala hexagonal) en portal, cards y puerta (`static/img/logoF*`),
favicon GV completo (ico/svg/png + apple-touch + manifest PWA), footer de
créditos, paleta azul/cian documentada en `static/css/main.css` (`:root`).

---

## 8. Migraciones (orden cronológico)

| Revisión | Contenido |
|---|---|
| `618b523d69f8` | Modelo inicial (usuario, autor, exposicion, sala, zona, obra) |
| `a1b2c3d4e5f6` | Multi-organizador: roles + propiedad (con backfill) |
| `b2c3d4e5f6a7` | Tabla `visita` |
| `c3d4e5f6a7b8` | `visibilidad` + `codigo_acceso_hash` |
| `d4e5f6a7b8c9` | `cerrada_manual` |
| `e5f6a7b8c9d0` | `portada_obra_id` |
| `f6a7b8c9d0e1` | Hilo musical (`musica_public_id/url`) |
| `a7b8c9d0e1f2` | `visita.dispositivo/modo` |
| `b8c9d0e1f2a3` | Tabla `vista_obra` (interés por obra) |
| `c9d0e1f2a3b4` | `sala.parametros` (plantas elásticas) |
| `d0e1f2a3b4c5` | Perfil del organizador (web/logo) + retrato de autor |

Todas aditivas. En producción se aplican solas al arrancar
(`bootstrap.aplicar_migraciones`).

---

## Aparcado / ideas futuras

- Formas complejas conectando varias plantas (el motor de `room.js` las
  soporta; falta el constructor y el recorrido multi-sala en el visor).
- Botón "Girar 90°" para imágenes escaneadas tumbadas (transformación
  `angle` de Cloudinary).
- Sembrar placeholders opcionales al crear la exposición.
- Expulsión inmediata de sesiones autorizadas al cambiar el código de acceso.
- Enlaces a perfiles sociales del organizador (Instagram, etc.).
