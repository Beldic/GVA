// Geometría de sala por plantilla. El `codigo` de cada zona del backend
// (far/near/left/right) se traduce a una posición en la pared con slotPlacement.
// Una plantilla puede declarar una `door` (puerta) en una de sus paredes.
export const PLANTILLAS_GEO = {
    "sala-clasica": { width: 8 /* X */, depth: 6 /* Z */, height: 3.2 /* Y */ },
    "sala-rectangular": {
        width: 11, // X
        depth: 16, // Z
        height: 3.4, // Y
        door: { wall: "near", width: 1.4, height: 2.3 },
    },
};

export const DEFAULT_PLANTILLA = "sala-clasica";

export function geometriaDe(plantilla) {
    return PLANTILLAS_GEO[plantilla] || PLANTILLAS_GEO[DEFAULT_PLANTILLA];
}

// Dimensiones por defecto (la cámara las usa para el punto de partida).
export const ROOM = geometriaDe(DEFAULT_PLANTILLA);

export function buildRoom(scene, plantilla) {
    const room = geometriaDe(plantilla);
    const { width, depth, height } = room;
    const half = { x: width / 2, z: depth / 2 };
    const door = room.door || null;

    // ---- Materiales ----
    const wallMat = new BABYLON.StandardMaterial("wallMat", scene);
    wallMat.diffuseColor = new BABYLON.Color3(0.94, 0.95, 0.97); // blanco roto
    wallMat.specularColor = new BABYLON.Color3(0.02, 0.02, 0.03);
    wallMat.ambientColor = new BABYLON.Color3(0.6, 0.62, 0.7);

    const ceilingMat = new BABYLON.StandardMaterial("ceilingMat", scene);
    ceilingMat.diffuseColor = new BABYLON.Color3(0.97, 0.97, 0.98);
    ceilingMat.specularColor = new BABYLON.Color3(0, 0, 0);

    const floorMat = new BABYLON.StandardMaterial("floorMat", scene);
    floorMat.diffuseColor = new BABYLON.Color3(0.12, 0.16, 0.24); // azul-grafito
    floorMat.specularColor = new BABYLON.Color3(0.25, 0.3, 0.45);
    floorMat.specularPower = 96;

    const baseboardMat = new BABYLON.StandardMaterial("baseboardMat", scene);
    baseboardMat.diffuseColor = new BABYLON.Color3(0.08, 0.13, 0.22);
    baseboardMat.specularColor = new BABYLON.Color3(0.1, 0.12, 0.18);

    const darkMat = new BABYLON.StandardMaterial("darkMat", scene);
    darkMat.diffuseColor = new BABYLON.Color3(0.06, 0.09, 0.16); // marco/umbral
    darkMat.specularColor = new BABYLON.Color3(0.15, 0.18, 0.26);
    darkMat.specularPower = 64;

    // ---- Suelo ----
    const floor = BABYLON.MeshBuilder.CreateGround(
        "floor",
        { width, height: depth, subdivisions: 2 },
        scene
    );
    floor.material = floorMat;
    floor.checkCollisions = true;
    floor.receiveShadows = true;

    // ---- Techo ----
    const ceiling = BABYLON.MeshBuilder.CreateGround(
        "ceiling",
        { width, height: depth },
        scene
    );
    ceiling.position.y = height;
    ceiling.rotation.x = Math.PI; // mirar hacia abajo
    ceiling.material = ceilingMat;

    // ---- Paredes (planos orientados hacia el interior) ----
    const makeWall = (name, w, h, position, rotationY) => {
        const wall = BABYLON.MeshBuilder.CreatePlane(
            name,
            { width: w, height: h, sideOrientation: BABYLON.Mesh.FRONTSIDE },
            scene
        );
        wall.position = position;
        wall.rotation.y = rotationY;
        wall.material = wallMat;
        wall.checkCollisions = true;
        return wall;
    };

    // Far wall (z = +half.z), mira hacia -Z
    makeWall("wallFar", width, height, new BABYLON.Vector3(0, height / 2, half.z), Math.PI);
    // Left wall (x = -half.x), mira hacia +X
    makeWall("wallLeft", depth, height, new BABYLON.Vector3(-half.x, height / 2, 0), -Math.PI / 2);
    // Right wall (x = +half.x), mira hacia -X
    makeWall("wallRight", depth, height, new BABYLON.Vector3(half.x, height / 2, 0), Math.PI / 2);

    // Near wall (z = -half.z), mira hacia +Z. Con puerta: dos paneles + dintel.
    if (door && door.wall === "near") {
        const dHalf = door.width / 2;
        const sideW = half.x - dHalf; // ancho de cada panel lateral
        makeWall("wallNearL", sideW, height, new BABYLON.Vector3(-(half.x + dHalf) / 2, height / 2, -half.z), 0);
        makeWall("wallNearR", sideW, height, new BABYLON.Vector3((half.x + dHalf) / 2, height / 2, -half.z), 0);
        makeWall(
            "wallNearTop",
            door.width,
            height - door.height,
            new BABYLON.Vector3(0, (door.height + height) / 2, -half.z),
            0
        );
        buildDoorway(scene, door, half, darkMat);
    } else {
        makeWall("wallNear", width, height, new BABYLON.Vector3(0, height / 2, -half.z), 0);
    }

    // ---- Cajas invisibles para colisión en las paredes ----
    const wallThickness = 0.2;
    const collider = (name, size, position) => {
        const box = BABYLON.MeshBuilder.CreateBox(name, size, scene);
        box.position = position;
        box.checkCollisions = true;
        box.isVisible = false;
        return box;
    };
    collider("colFar", { width: width + wallThickness * 2, height, depth: wallThickness }, new BABYLON.Vector3(0, height / 2, half.z + wallThickness / 2));
    collider("colNear", { width: width + wallThickness * 2, height, depth: wallThickness }, new BABYLON.Vector3(0, height / 2, -half.z - wallThickness / 2));
    collider("colLeft", { width: wallThickness, height, depth: depth + wallThickness * 2 }, new BABYLON.Vector3(-half.x - wallThickness / 2, height / 2, 0));
    collider("colRight", { width: wallThickness, height, depth: depth + wallThickness * 2 }, new BABYLON.Vector3(half.x + wallThickness / 2, height / 2, 0));

    // ---- Rodapiés azul oscuro como detalle elegante ----
    const baseboardHeight = 0.1;
    const baseboardDepth = 0.04;
    const baseboard = (name, w, position, rotationY = 0) => {
        const bb = BABYLON.MeshBuilder.CreateBox(
            name,
            { width: w, height: baseboardHeight, depth: baseboardDepth },
            scene
        );
        bb.position = position;
        bb.rotation.y = rotationY;
        bb.material = baseboardMat;
        return bb;
    };
    baseboard("bbFar", width, new BABYLON.Vector3(0, baseboardHeight / 2, half.z - baseboardDepth / 2));
    baseboard("bbNear", width, new BABYLON.Vector3(0, baseboardHeight / 2, -half.z + baseboardDepth / 2));
    baseboard("bbLeft", depth, new BABYLON.Vector3(-half.x + baseboardDepth / 2, baseboardHeight / 2, 0), Math.PI / 2);
    baseboard("bbRight", depth, new BABYLON.Vector3(half.x - baseboardDepth / 2, baseboardHeight / 2, 0), Math.PI / 2);

    // ---- Decoración: alfombra/runner central azul oscuro ----
    const rugMat = new BABYLON.StandardMaterial("rugMat", scene);
    rugMat.diffuseColor = new BABYLON.Color3(0.09, 0.14, 0.28);
    rugMat.specularColor = new BABYLON.Color3(0.04, 0.05, 0.09);
    const rug = BABYLON.MeshBuilder.CreateBox(
        "rug",
        { width: 1.6, height: 0.02, depth: depth - 2 },
        scene
    );
    rug.position = new BABYLON.Vector3(0, 0.011, 0);
    rug.material = rugMat;

    return room;
}

// Marco de puerta (jambas + dintel) y un fondo oscuro recedido que da sensación
// de salida, en la pared near (z = -half.z).
function buildDoorway(scene, door, half, darkMat) {
    const z = -half.z;
    const dHalf = door.width / 2;
    const jamb = 0.12;
    const jambDepth = 0.2;

    const mkBox = (name, size, position) => {
        const b = BABYLON.MeshBuilder.CreateBox(name, size, scene);
        b.position = position;
        b.material = darkMat;
        return b;
    };
    // Jambas
    mkBox("doorJambL", { width: jamb, height: door.height, depth: jambDepth }, new BABYLON.Vector3(-dHalf, door.height / 2, z));
    mkBox("doorJambR", { width: jamb, height: door.height, depth: jambDepth }, new BABYLON.Vector3(dHalf, door.height / 2, z));
    // Dintel
    mkBox("doorLintel", { width: door.width + jamb * 2, height: jamb, depth: jambDepth }, new BABYLON.Vector3(0, door.height, z));

    // Fondo oscuro recedido (umbral) tras el hueco
    const back = BABYLON.MeshBuilder.CreatePlane(
        "doorBack",
        { width: door.width, height: door.height, sideOrientation: BABYLON.Mesh.DOUBLESIDE },
        scene
    );
    back.position = new BABYLON.Vector3(0, door.height / 2, z - 0.12);
    const backMat = new BABYLON.StandardMaterial("doorBackMat", scene);
    backMat.diffuseColor = new BABYLON.Color3(0.02, 0.03, 0.06);
    backMat.emissiveColor = new BABYLON.Color3(0.06, 0.08, 0.14); // leve brillo de salida
    backMat.specularColor = new BABYLON.Color3(0, 0, 0);
    back.material = backMat;
}

// Posición de un hueco en una pared. Reparte `capacidad` huecos a lo largo de la
// pared y devuelve la base (sobre la superficie, y=0) y la rotación para que el
// cuadro mire al centro de la sala. Si la pared tiene puerta, reparte los huecos
// en los dos segmentos a ambos lados del hueco central. `slotWidth` permite
// recortar el cuadro para que no invada el hueco contiguo.
export function slotPlacement(codigo, room, capacidad, orden) {
    const half = { x: room.width / 2, z: room.depth / 2 };
    const n = Math.max(capacidad, 1);
    const isX = codigo === "far" || codigo === "near";
    const length = isX ? room.width : room.depth;
    const door = room.door && room.door.wall === codigo ? room.door : null;

    let axisPos;
    let slotWidth;
    if (door) {
        const seg = (length - door.width) / 2; // largo de cada segmento lateral
        const nLeft = Math.floor(n / 2);
        const nRight = n - nLeft;
        if (orden < nLeft) {
            const c = Math.max(nLeft, 1);
            axisPos = -length / 2 + (orden + 0.5) * (seg / c);
            slotWidth = seg / c;
        } else {
            const c = Math.max(nRight, 1);
            const i = orden - nLeft;
            axisPos = door.width / 2 + (i + 0.5) * (seg / c);
            slotWidth = seg / c;
        }
    } else {
        axisPos = -length / 2 + (orden + 0.5) * (length / n);
        slotWidth = length / n;
    }

    let position;
    let rotationY;
    switch (codigo) {
        case "far":
            position = new BABYLON.Vector3(axisPos, 0, half.z);
            rotationY = 0;
            break;
        case "near":
            position = new BABYLON.Vector3(axisPos, 0, -half.z);
            rotationY = Math.PI;
            break;
        case "left":
            position = new BABYLON.Vector3(-half.x, 0, axisPos);
            rotationY = -Math.PI / 2;
            break;
        case "right":
            position = new BABYLON.Vector3(half.x, 0, axisPos);
            rotationY = Math.PI / 2;
            break;
        default:
            return null; // código de zona desconocido para esta plantilla
    }
    return { position, rotationY, slotWidth };
}
