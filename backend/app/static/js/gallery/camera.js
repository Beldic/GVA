import { ROOM } from "./room.js";

export function createFirstPersonCamera(scene, canvas) {
    const eyeHeight = 1.7;
    const startPos = new BABYLON.Vector3(0, eyeHeight, -ROOM.depth / 2 + 1.2);
    const camera = new BABYLON.UniversalCamera("fpCamera", startPos, scene);

    camera.setTarget(new BABYLON.Vector3(0, eyeHeight, 0));

    // Movimiento y colisiones
    camera.applyGravity = true;
    camera.checkCollisions = true;
    camera.ellipsoid = new BABYLON.Vector3(0.4, eyeHeight / 2, 0.4);
    camera.ellipsoidOffset = new BABYLON.Vector3(0, eyeHeight / 2, 0);

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
