import { ROOM } from "./room.js?v=2";

export function createFirstPersonCamera(scene, canvas, planta = ROOM, onExit) {
    const eyeHeight = 1.7;
    const s = planta.start || { x: 0, z: 0, lookAt: { x: 0, z: 1 } };
    const startPos = new BABYLON.Vector3(s.x, eyeHeight, s.z);
    const camera = new BABYLON.UniversalCamera("fpCamera", startPos, scene);

    const look = s.lookAt || { x: s.x, z: s.z + 1 };
    camera.setTarget(new BABYLON.Vector3(look.x, eyeHeight, look.z));

    // Movimiento con COLISIONES reales contra los colisores de pared (permite
    // recorrer pasillos y cruzar huecos entre estancias). La altura del ojo se
    // fija cada frame para que mirar al suelo no hunda la cámara.
    camera.applyGravity = false;
    camera.checkCollisions = true;
    camera.ellipsoid = new BABYLON.Vector3(0.4, eyeHeight / 2, 0.4);
    camera.ellipsoidOffset = new BABYLON.Vector3(0, eyeHeight / 2, 0);

    // Puerta de salida: al cruzar su umbral hacia fuera, se dispara onExit.
    const door = planta.door || null;
    let saliendo = false;

    scene.onBeforeRenderObservable.add(() => {
        const p = camera.position;
        p.y = eyeHeight; // altura del ojo constante

        if (door && !saliendo) {
            const out = door.out; // normal hacia fuera de la puerta
            const along = { x: -out.z, z: out.x }; // eje a lo largo de la pared
            const dx = p.x - door.x;
            const dz = p.z - door.z;
            const fuera = dx * out.x + dz * out.z; // >0 = ya cruzó el umbral
            const lateral = Math.abs(dx * along.x + dz * along.z); // dist. al centro
            if (fuera > 0 && lateral <= door.width / 2) {
                saliendo = true;
                if (typeof onExit === "function") onExit();
            }
        }
    });

    camera.speed = 0.18;
    camera.angularSensibility = 1800;
    camera.inertia = 0.6;
    // Plano cercano/lejano acotados: la relación maxZ/minZ determina la precisión
    // del buffer de profundidad. Con 0.05→10000 (relación 200.000) las superficies
    // casi coplanares peleaban por la profundidad (Z-fighting: cuadros blancos que
    // saltaban en las GPU Apple/M1). Con 0.3→80 la relación baja a ~267 y desaparece.
    // El ojo va a 1.7 m y la colisión frena a 0.4 m de la pared, así que 0.3 sobra;
    // la sala mayor mide ~20 m, así que 80 va holgado.
    camera.minZ = 0.3;
    camera.maxZ = 80;
    camera.fov = 1.05;

    camera.keysUp = [87, 38]; // W, ↑
    camera.keysDown = [83, 40]; // S, ↓
    camera.keysLeft = [65, 37]; // A, ←
    camera.keysRight = [68, 39]; // D, →

    camera.attachControl(canvas, true);

    camera.upperBetaLimit = Math.PI - 0.1;
    camera.lowerBetaLimit = 0.1;

    return camera;
}
