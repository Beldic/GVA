import { buildRoom, ROOM } from "./room.js";
import { buildPainting } from "./painting.js";
import { createFirstPersonCamera } from "./camera.js";

export function createScene(engine, canvas) {
    const scene = new BABYLON.Scene(engine);
    scene.clearColor = new BABYLON.Color4(0.02, 0.04, 0.08, 1);
    scene.ambientColor = new BABYLON.Color3(0.15, 0.18, 0.25);

    // Colisiones + gravedad para movimiento en primera persona
    scene.collisionsEnabled = true;
    scene.gravity = new BABYLON.Vector3(0, -0.6, 0);

    // ---- Luz ambiental suave (azulada) ----
    const hemi = new BABYLON.HemisphericLight(
        "hemi",
        new BABYLON.Vector3(0, 1, 0),
        scene
    );
    hemi.intensity = 0.4;
    hemi.diffuse = new BABYLON.Color3(0.82, 0.88, 1.0);
    hemi.groundColor = new BABYLON.Color3(0.08, 0.1, 0.18);
    hemi.specular = new BABYLON.Color3(0, 0, 0);

    // ---- Foco principal sobre el cuadro (cálido, contraste museo) ----
    const spot = new BABYLON.SpotLight(
        "paintingSpot",
        new BABYLON.Vector3(0, ROOM.height - 0.2, ROOM.depth / 2 - 1.6),
        new BABYLON.Vector3(0, -0.7, 0.6),
        Math.PI / 4,
        10,
        scene
    );
    spot.intensity = 2.2;
    spot.diffuse = new BABYLON.Color3(1.0, 0.96, 0.85);
    spot.specular = new BABYLON.Color3(0.6, 0.55, 0.45);

    // ---- Luz de relleno frontal suave ----
    const fill = new BABYLON.PointLight(
        "fill",
        new BABYLON.Vector3(0, ROOM.height - 0.5, 0),
        scene
    );
    fill.intensity = 0.4;
    fill.diffuse = new BABYLON.Color3(0.9, 0.92, 1.0);
    fill.specular = new BABYLON.Color3(0, 0, 0);

    // ---- Geometría ----
    buildRoom(scene);
    buildPainting(scene);

    // ---- Cámara primera persona ----
    createFirstPersonCamera(scene, canvas);

    return scene;
}
