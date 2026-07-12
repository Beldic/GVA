// Motor de plantas de galería (data-driven).
//
// Una "planta" es un plano compuesto por celdas rectangulares (estancias y
// pasillos) alineadas a los ejes X/Z, más una lista de tramos de pared donde
// cuelgan las obras. Cada tramo lleva un `codigo` que casa con el `codigo` de
// las zonas del backend (plantillas.py). Todas las formas previstas (rect, L,
// T, O, E, F) son uniones de rectángulos alineados a ejes: por eso las paredes
// son siempre horizontales (z constante) o verticales (x constante), sin
// geometría diagonal.
//
// Un tramo: { codigo, x1, z1, x2, z2, nx, nz, door? }
//   (x1,z1)-(x2,z2) recorre la pared;  (nx,nz) = normal hacia el interior.
//   door (opcional) = { width, height } abre un hueco centrado en el tramo.

// ---- Fábrica de una planta rectangular simple (una sola celda) ----
function rectPlanta(width, depth, height, door = null) {
    const hx = width / 2;
    const hz = depth / 2;
    return {
        height,
        cells: [{ x: 0, z: 0, w: width, d: depth }],
        walls: [
            { codigo: "far", x1: -hx, z1: hz, x2: hx, z2: hz, nx: 0, nz: -1 },
            {
                codigo: "near", x1: -hx, z1: -hz, x2: hx, z2: -hz, nx: 0, nz: 1,
                door: door && door.wall === "near" ? { width: door.width, height: door.height } : null,
            },
            { codigo: "left", x1: -hx, z1: -hz, x2: -hx, z2: hz, nx: 1, nz: 0 },
            { codigo: "right", x1: hx, z1: -hz, x2: hx, z2: hz, nx: -1, nz: 0 },
        ],
        // Puerta de entrada/salida (hueco por el que se cruza el umbral).
        door: door
            ? { x: 0, z: -hz, width: door.width, height: door.height, out: { x: 0, z: -1 } }
            : null,
        start: { x: 0, z: -hz + 1.2, lookAt: { x: 0, z: 0 } },
    };
}

// ---- Planta en T: pasillo (stem) que abre a una estancia amplia (hall) ----
// Entras por el fondo del pasillo (dibujos a los lados), avanzas y desemboca
// por un arco en una estancia ancha con cuadros bien espaciados. La pared del
// tabique de la puerta queda limpia (sin obra), solo con su arco de acceso.
// Elástica: `pasillo` = largo del pasillo, `estancia` = ancho de la estancia.
function plantaT(pasillo = 12, estancia = 20) {
    const height = 4.2;
    const hE = estancia / 2;
    const z0 = -3 - pasillo; // testero de entrada
    return {
        height,
        cells: [
            { x: 0, z: -3 - pasillo / 2, w: 5, d: pasillo }, // pasillo
            { x: 0, z: 1, w: estancia, d: 8 }, // estancia
        ],
        walls: [
            // Pasillo — el tabique de la entrada es estructural (sin codigo → sin obra)
            { x1: -2.5, z1: z0, x2: 2.5, z2: z0, nx: 0, nz: 1, door: { width: 1.4, height: 2.6 } },
            { codigo: "pasillo_izq", x1: -2.5, z1: z0, x2: -2.5, z2: -3, nx: 1, nz: 0 },
            { codigo: "pasillo_der", x1: 2.5, z1: z0, x2: 2.5, z2: -3, nx: -1, nz: 0 },
            // Estancia
            { codigo: "fondo", x1: -hE, z1: 5, x2: hE, z2: 5, nx: 0, nz: -1 },
            { codigo: "hall_izq", x1: -hE, z1: -3, x2: -hE, z2: 5, nx: 1, nz: 0 },
            { codigo: "hall_der", x1: hE, z1: -3, x2: hE, z2: 5, nx: -1, nz: 0 },
            // Pared de unión estancia↔pasillo, con arco central (ancho del pasillo)
            {
                codigo: "hall_frente", x1: -hE, z1: -3, x2: hE, z2: -3, nx: 0, nz: 1,
                door: { width: 5, height: 3.0 },
            },
        ],
        door: { x: 0, z: z0, width: 1.4, height: 2.6, out: { x: 0, z: -1 } },
        start: { x: 0, z: z0 + 1.2, lookAt: { x: 0, z: 0 } },
    };
}

// ---- Planta en cruz (+): vestíbulo central con cuatro alas ----
// Entras por el ala sur; cuadros en los fondos de las otras tres alas y
// dibujos en los ocho costados. Alas de 5 m de ancho y `ala` m de fondo sobre
// un vestíbulo de 5×5: el perímetro son 12 tramos alineados a ejes.
function plantaCruz(ala = 6) {
    const height = 3.6;
    const a = 2.5; // medio ancho de ala
    const b = a + ala; // extremo de cada ala
    return {
        height,
        cells: [
            { x: 0, z: 0, w: 5, d: 5 },                        // vestíbulo central
            { x: 0, z: -(a + ala / 2), w: 5, d: ala },         // ala sur (entrada)
            { x: 0, z: a + ala / 2, w: 5, d: ala },            // ala norte
            { x: -(a + ala / 2), z: 0, w: ala, d: 5 },         // ala oeste
            { x: a + ala / 2, z: 0, w: ala, d: 5 },            // ala este
        ],
        walls: [
            // Ala sur — el testero de entrada es estructural (sin codigo)
            { x1: -a, z1: -b, x2: a, z2: -b, nx: 0, nz: 1, door: { width: 1.4, height: 2.6 } },
            { codigo: "entrada_izq", x1: -a, z1: -b, x2: -a, z2: -a, nx: 1, nz: 0 },
            { codigo: "entrada_der", x1: a, z1: -b, x2: a, z2: -a, nx: -1, nz: 0 },
            // Ala oeste
            { codigo: "oeste_sur", x1: -b, z1: -a, x2: -a, z2: -a, nx: 0, nz: 1 },
            { codigo: "oeste_fondo", x1: -b, z1: -a, x2: -b, z2: a, nx: 1, nz: 0 },
            { codigo: "oeste_norte", x1: -b, z1: a, x2: -a, z2: a, nx: 0, nz: -1 },
            // Ala este
            { codigo: "este_sur", x1: a, z1: -a, x2: b, z2: -a, nx: 0, nz: 1 },
            { codigo: "este_fondo", x1: b, z1: -a, x2: b, z2: a, nx: -1, nz: 0 },
            { codigo: "este_norte", x1: a, z1: a, x2: b, z2: a, nx: 0, nz: -1 },
            // Ala norte
            { codigo: "norte_izq", x1: -a, z1: a, x2: -a, z2: b, nx: 1, nz: 0 },
            { codigo: "fondo", x1: -a, z1: b, x2: a, z2: b, nx: 0, nz: -1 },
            { codigo: "norte_der", x1: a, z1: a, x2: a, z2: b, nx: -1, nz: 0 },
        ],
        door: { x: 0, z: -b, width: 1.4, height: 2.6, out: { x: 0, z: -1 } },
        start: { x: 0, z: -b + 1.2, lookAt: { x: 0, z: 0 } },
    };
}

// Cada forma es una función de sus parámetros elásticos (sala.parametros,
// calculados por el backend al crear la sala). Sin parámetros -> medidas por
// defecto, que son las de las salas creadas antes de las plantas elásticas.
const PUERTA = { wall: "near", width: 1.4, height: 2.3 };

export const PLANTAS_GEO = {
    // La clásica también con su puerta: todas las plantas tienen entrada.
    "sala-clasica": (p) => rectPlanta(p.ancho || 8, p.fondo || 6, 3.2, PUERTA),
    "sala-rectangular": (p) => rectPlanta(p.ancho || 11, p.fondo || 16, 3.4, PUERTA),
    "planta-cruz": (p) => plantaCruz(p.ala || 6),
    "planta-t": (p) => plantaT(p.pasillo || 12, p.estancia || 20),
};

export const DEFAULT_PLANTA = "sala-clasica";

export function plantaDe(plantilla, params) {
    const builder = PLANTAS_GEO[plantilla] || PLANTAS_GEO[DEFAULT_PLANTA];
    return builder(params || {});
}

// Compatibilidad: la cámara importa ROOM como planta por defecto.
export const ROOM = plantaDe(DEFAULT_PLANTA);

// ---- Utilidades de geometría (tramos alineados a ejes) ----
const segLen = (w) => Math.hypot(w.x2 - w.x1, w.z2 - w.z1);
const lerp = (a, b, t) => a + (b - a) * t;
// Un plano de Babylon (frente +Z local) mira hacia (nx,nz) con esta rotación.
const wallFacingY = (nx, nz) => Math.atan2(-nx, nz);
// Un cuadro (frente -Z local, ver painting.js) mira hacia (nx,nz) con esta.
const paintingFacingY = (nx, nz) => Math.atan2(-nx, -nz);

export function buildRoom(scene, plantilla, params) {
    const planta = plantaDe(plantilla, params);
    const { height } = planta;

    // ---- Materiales ----
    const wallMat = new BABYLON.StandardMaterial("wallMat", scene);
    wallMat.diffuseColor = new BABYLON.Color3(0.94, 0.95, 0.97);
    wallMat.specularColor = new BABYLON.Color3(0.02, 0.02, 0.03);
    wallMat.ambientColor = new BABYLON.Color3(0.6, 0.62, 0.7);
    // NO se desactiva el backface culling: las paredes usan geometría DOUBLESIDE
    // (ya trae sus dos caras), así que quitar el culling dibujaba las dos caras
    // coincidentes a la MISMA profundidad y peleaban por el z-buffer. En GPU Apple
    // (M1) eso salía como rectángulos blancos que parpadeaban al girar la cámara.
    // Con el culling activo (por defecto), cada cara se ve por su lado, sin pelea,
    // y las paredes siguen siendo visibles por ambos lados en los pasillos.
    wallMat.maxSimultaneousLights = 8;

    const ceilingMat = new BABYLON.StandardMaterial("ceilingMat", scene);
    ceilingMat.diffuseColor = new BABYLON.Color3(0.97, 0.97, 0.98);
    ceilingMat.specularColor = new BABYLON.Color3(0, 0, 0);
    ceilingMat.maxSimultaneousLights = 8;

    const floorMat = new BABYLON.StandardMaterial("floorMat", scene);
    floorMat.diffuseColor = new BABYLON.Color3(0.12, 0.16, 0.24);
    floorMat.specularColor = new BABYLON.Color3(0.25, 0.3, 0.45);
    floorMat.specularPower = 96;
    floorMat.maxSimultaneousLights = 8;

    const baseboardMat = new BABYLON.StandardMaterial("baseboardMat", scene);
    baseboardMat.diffuseColor = new BABYLON.Color3(0.08, 0.13, 0.22);
    baseboardMat.specularColor = new BABYLON.Color3(0.1, 0.12, 0.18);

    const darkMat = new BABYLON.StandardMaterial("darkMat", scene);
    darkMat.diffuseColor = new BABYLON.Color3(0.06, 0.09, 0.16);
    darkMat.specularColor = new BABYLON.Color3(0.15, 0.18, 0.26);
    darkMat.specularPower = 64;

    const rugMat = new BABYLON.StandardMaterial("rugMat", scene);
    rugMat.diffuseColor = new BABYLON.Color3(0.09, 0.14, 0.28);
    rugMat.specularColor = new BABYLON.Color3(0.04, 0.05, 0.09);

    // ---- Suelos, techos y alfombra por celda ----
    planta.cells.forEach((c, i) => {
        const floor = BABYLON.MeshBuilder.CreateGround(
            `floor-${i}`, { width: c.w, height: c.d, subdivisions: 2 }, scene
        );
        floor.position = new BABYLON.Vector3(c.x, 0, c.z);
        floor.material = floorMat;
        floor.receiveShadows = true;

        const ceiling = BABYLON.MeshBuilder.CreateGround(
            `ceiling-${i}`, { width: c.w, height: c.d }, scene
        );
        ceiling.position = new BABYLON.Vector3(c.x, height, c.z);
        ceiling.rotation.x = Math.PI;
        ceiling.material = ceilingMat;

        // Alfombra a lo largo del eje más largo de la celda.
        const along = Math.max(c.w, c.d) - 2;
        if (along > 0.5) {
            const rug = BABYLON.MeshBuilder.CreateBox(
                `rug-${i}`,
                c.d >= c.w
                    ? { width: 1.6, height: 0.02, depth: along }
                    : { width: along, height: 0.02, depth: 1.6 },
                scene
            );
            rug.position = new BABYLON.Vector3(c.x, 0.011, c.z);
            rug.material = rugMat;
        }
    });

    // ---- Paredes (planos + colisores + rodapié), tramo a tramo ----
    const wallThickness = 0.2;
    const baseboardH = 0.1;
    const baseboardD = 0.04;

    const makeWallPlane = (name, len, midX, midZ, facingY) => {
        const wall = BABYLON.MeshBuilder.CreatePlane(
            name, { width: len, height, sideOrientation: BABYLON.Mesh.DOUBLESIDE }, scene
        );
        wall.position = new BABYLON.Vector3(midX, height / 2, midZ);
        wall.rotation.y = facingY;
        wall.material = wallMat;
        return wall;
    };

    // Colisor: caja fina alineada al tramo (horizontal o vertical).
    const makeCollider = (name, x1, z1, x2, z2) => {
        const horizontal = Math.abs(z1 - z2) < 1e-6;
        const len = horizontal ? Math.abs(x2 - x1) : Math.abs(z2 - z1);
        const size = horizontal
            ? { width: len, height, depth: wallThickness }
            : { width: wallThickness, height, depth: len };
        const box = BABYLON.MeshBuilder.CreateBox(name, size, scene);
        box.position = new BABYLON.Vector3((x1 + x2) / 2, height / 2, (z1 + z2) / 2);
        box.checkCollisions = true;
        box.isVisible = false;
    };

    const makeBaseboard = (name, x1, z1, x2, z2) => {
        const horizontal = Math.abs(z1 - z2) < 1e-6;
        const len = horizontal ? Math.abs(x2 - x1) : Math.abs(z2 - z1);
        const bb = BABYLON.MeshBuilder.CreateBox(
            name,
            horizontal
                ? { width: len, height: baseboardH, depth: baseboardD }
                : { width: baseboardD, height: baseboardH, depth: len },
            scene
        );
        bb.position = new BABYLON.Vector3((x1 + x2) / 2, baseboardH / 2, (z1 + z2) / 2);
        bb.material = baseboardMat;
    };

    planta.walls.forEach((w, i) => {
        const len = segLen(w);
        const facingY = wallFacingY(w.nx, w.nz);
        if (w.door) {
            // Dos paneles laterales + dintel; hueco centrado.
            const dHalf = w.door.width / 2;
            const t1 = 0.5 - dHalf / len; // fin del panel izquierdo (param)
            const t2 = 0.5 + dHalf / len; // inicio del panel derecho
            const p = (t) => ({ x: lerp(w.x1, w.x2, t), z: lerp(w.z1, w.z2, t) });
            const a = p(0), b = p(t1), c = p(t2), d = p(1);
            const segL = segLen({ x1: a.x, z1: a.z, x2: b.x, z2: b.z });

            makeWallPlane(`wall-${i}L`, segL, (a.x + b.x) / 2, (a.z + b.z) / 2, facingY);
            makeWallPlane(`wall-${i}R`, segL, (c.x + d.x) / 2, (c.z + d.z) / 2, facingY);
            // Dintel sobre el hueco
            const lintel = BABYLON.MeshBuilder.CreatePlane(
                `wall-${i}Top`,
                { width: w.door.width, height: height - w.door.height, sideOrientation: BABYLON.Mesh.DOUBLESIDE },
                scene
            );
            lintel.position = new BABYLON.Vector3(w.x1 + (w.x2 - w.x1) / 2, (w.door.height + height) / 2, w.z1 + (w.z2 - w.z1) / 2);
            lintel.rotation.y = facingY;
            lintel.material = wallMat;

            makeCollider(`col-${i}L`, a.x, a.z, b.x, b.z);
            makeCollider(`col-${i}R`, c.x, c.z, d.x, d.z);
            makeBaseboard(`bb-${i}L`, a.x, a.z, b.x, b.z);
            makeBaseboard(`bb-${i}R`, c.x, c.z, d.x, d.z);
        } else {
            makeWallPlane(`wall-${i}`, len, (w.x1 + w.x2) / 2, (w.z1 + w.z2) / 2, facingY);
            makeCollider(`col-${i}`, w.x1, w.z1, w.x2, w.z2);
            makeBaseboard(`bb-${i}`, w.x1, w.z1, w.x2, w.z2);
        }
    });

    // ---- Marco y umbral de la puerta ----
    if (planta.door) buildDoorway(scene, planta.door, darkMat);

    return planta;
}

// Marco de puerta (jambas + dintel) y fondo oscuro recedido en el hueco de
// entrada/salida. Asume puerta en una pared horizontal (z constante).
function buildDoorway(scene, door, darkMat) {
    const z = door.z;
    const dHalf = door.width / 2;
    const jamb = 0.12;
    const jambDepth = 0.2;

    const mkBox = (name, size, position) => {
        const b = BABYLON.MeshBuilder.CreateBox(name, size, scene);
        b.position = position;
        b.material = darkMat;
    };
    mkBox("doorJambL", { width: jamb, height: door.height, depth: jambDepth }, new BABYLON.Vector3(door.x - dHalf, door.height / 2, z));
    mkBox("doorJambR", { width: jamb, height: door.height, depth: jambDepth }, new BABYLON.Vector3(door.x + dHalf, door.height / 2, z));
    mkBox("doorLintel", { width: door.width + jamb * 2, height: jamb, depth: jambDepth }, new BABYLON.Vector3(door.x, door.height, z));

    const back = BABYLON.MeshBuilder.CreatePlane(
        "doorBack", { width: door.width, height: door.height, sideOrientation: BABYLON.Mesh.DOUBLESIDE }, scene
    );
    // Recede el fondo un poco hacia fuera (a lo largo de la normal de salida).
    back.position = new BABYLON.Vector3(door.x, door.height / 2, z + 0.12 * door.out.z);
    const backMat = new BABYLON.StandardMaterial("doorBackMat", scene);
    backMat.diffuseColor = new BABYLON.Color3(0.02, 0.03, 0.06);
    backMat.emissiveColor = new BABYLON.Color3(0.06, 0.08, 0.14);
    backMat.specularColor = new BABYLON.Color3(0, 0, 0);
    back.material = backMat;
}

// Posición de un hueco (obra) en el tramo de su zona. Reparte `capacidad`
// huecos a lo largo del tramo (saltando el hueco de puerta si lo hay) y
// devuelve la base sobre el suelo (y=0) y la rotación para mirar al interior.
export function slotPlacement(codigo, planta, capacidad, orden) {
    const w = planta.walls.find((x) => x.codigo === codigo);
    if (!w) return null;

    const len = segLen(w);
    const n = Math.max(capacidad, 1);
    const rotationY = paintingFacingY(w.nx, w.nz);

    let t; // parámetro 0..1 a lo largo del tramo
    let slotWidth;
    if (w.door) {
        const seg = (len - w.door.width) / 2; // largo de cada lateral
        const nLeft = Math.floor(n / 2);
        const nRight = n - nLeft;
        if (orden < nLeft) {
            const c = Math.max(nLeft, 1);
            const dist = (orden + 0.5) * (seg / c); // desde el extremo inicial
            t = dist / len;
            slotWidth = seg / c;
        } else {
            const c = Math.max(nRight, 1);
            const i = orden - nLeft;
            const dist = (len - seg) + (i + 0.5) * (seg / c);
            t = dist / len;
            slotWidth = seg / c;
        }
    } else {
        const dist = (orden + 0.5) * (len / n);
        t = dist / len;
        slotWidth = len / n;
    }

    const position = new BABYLON.Vector3(lerp(w.x1, w.x2, t), 0, lerp(w.z1, w.z2, t));
    return { position, rotationY, slotWidth };
}
