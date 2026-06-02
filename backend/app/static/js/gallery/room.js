export const ROOM = {
    width: 8,    // X
    depth: 6,    // Z
    height: 3.2, // Y
};

export function buildRoom(scene) {
    const { width, depth, height } = ROOM;
    const half = { x: width / 2, z: depth / 2 };

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
    makeWall(
        "wallFar",
        width,
        height,
        new BABYLON.Vector3(0, height / 2, half.z),
        Math.PI
    );
    // Near wall (z = -half.z), mira hacia +Z
    makeWall(
        "wallNear",
        width,
        height,
        new BABYLON.Vector3(0, height / 2, -half.z),
        0
    );
    // Left wall (x = -half.x), mira hacia +X
    makeWall(
        "wallLeft",
        depth,
        height,
        new BABYLON.Vector3(-half.x, height / 2, 0),
        -Math.PI / 2
    );
    // Right wall (x = +half.x), mira hacia -X
    makeWall(
        "wallRight",
        depth,
        height,
        new BABYLON.Vector3(half.x, height / 2, 0),
        Math.PI / 2
    );

    // ---- Cajas invisibles para colisión en las paredes (los planos no colisionan bien por una sola cara) ----
    const wallThickness = 0.2;
    const collider = (name, size, position) => {
        const box = BABYLON.MeshBuilder.CreateBox(name, size, scene);
        box.position = position;
        box.checkCollisions = true;
        box.isVisible = false;
        return box;
    };
    collider(
        "colFar",
        { width: width + wallThickness * 2, height, depth: wallThickness },
        new BABYLON.Vector3(0, height / 2, half.z + wallThickness / 2)
    );
    collider(
        "colNear",
        { width: width + wallThickness * 2, height, depth: wallThickness },
        new BABYLON.Vector3(0, height / 2, -half.z - wallThickness / 2)
    );
    collider(
        "colLeft",
        { width: wallThickness, height, depth: depth + wallThickness * 2 },
        new BABYLON.Vector3(-half.x - wallThickness / 2, height / 2, 0)
    );
    collider(
        "colRight",
        { width: wallThickness, height, depth: depth + wallThickness * 2 },
        new BABYLON.Vector3(half.x + wallThickness / 2, height / 2, 0)
    );

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
}
