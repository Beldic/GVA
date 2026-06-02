import { ROOM } from "./room.js";

export function createFirstPersonCamera(scene, canvas, room = ROOM, onExit) {
    const eyeHeight = 1.7;
    const startPos = new BABYLON.Vector3(0, eyeHeight, -room.depth / 2 + 1.2);
    const camera = new BABYLON.UniversalCamera("fpCamera", startPos, scene);

    camera.setTarget(new BABYLON.Vector3(0, eyeHeight, 0));

    // Movimiento. En lugar de gravedad + colisiones (que se pueden atravesar al
    // mirar al suelo y avanzar), fijamos la altura del ojo y acotamos la posición
    // dentro de la sala: límite determinista, imposible salirse o hundirse.
    camera.applyGravity = false;
    camera.checkCollisions = false;

    const margin = 0.6; // separación a las paredes para no pegarse a los cuadros
    const limX = room.width / 2 - margin;
    const limZ = room.depth / 2 - margin;
    // Puerta en la pared near (z = -depth/2): por su hueco se puede cruzar y salir.
    const door = room.door && room.door.wall === "near" ? room.door : null;
    const doorHalf = door ? door.width / 2 : 0;
    let saliendo = false;
    const clamp = (v, lim) => Math.max(-lim, Math.min(lim, v));

    scene.onBeforeRenderObservable.add(() => {
        const p = camera.position;
        p.y = eyeHeight; // altura del ojo constante (a la altura de los cuadros)
        p.x = clamp(p.x, limX);

        const enPuerta = door && Math.abs(p.x) <= doorHalf;
        if (enPuerta) {
            // Dentro del hueco de la puerta: dejamos avanzar hacia -Z y, al
            // cruzar el umbral, salimos a la entrada.
            if (p.z < -room.depth / 2 && !saliendo) {
                saliendo = true;
                if (typeof onExit === "function") onExit();
            }
            if (p.z > limZ) p.z = limZ; // tope del fondo (far)
        } else {
            p.z = clamp(p.z, limZ);
        }
    });

    camera.speed = 0.18;
    camera.angularSensibility = 1800; // mayor = más lento
    camera.inertia = 0.6;
    camera.minZ = 0.05;
    camera.fov = 1.05;

    // WASD además de las flechas
    camera.keysUp = [87, 38];    // W, ↑
    camera.keysDown = [83, 40];  // S, ↓
    camera.keysLeft = [65, 37];  // A, ←
    camera.keysRight = [68, 39]; // D, →

    // Control activado siempre; el pointer lock se gestiona en main.js
    camera.attachControl(canvas, true);

    // Evitar mirar completamente al cielo o al suelo
    camera.upperBetaLimit = Math.PI - 0.1;
    camera.lowerBetaLimit = 0.1;

    return camera;
}
