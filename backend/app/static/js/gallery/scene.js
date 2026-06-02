import { buildRoom, slotPlacement } from "./room.js";
import { buildPainting } from "./painting.js";
import { createFirstPersonCamera } from "./camera.js";

export function createScene(engine, canvas, datos, options = {}) {
    const scene = new BABYLON.Scene(engine);
    scene.clearColor = new BABYLON.Color4(0.02, 0.04, 0.08, 1);
    scene.ambientColor = new BABYLON.Color3(0.15, 0.18, 0.25);

    // Colisiones + gravedad disponibles (la cámara usa acotado, no colisión)
    scene.collisionsEnabled = true;
    scene.gravity = new BABYLON.Vector3(0, -0.6, 0);

    const salaData = datos.sala;

    // ---- Geometría (según la plantilla de la sala) ----
    const room = buildRoom(scene, salaData.plantilla_3d);

    // ---- Iluminación: base ambiental + fila de focos cálidos en el techo ----
    const hemi = new BABYLON.HemisphericLight(
        "hemi",
        new BABYLON.Vector3(0, 1, 0),
        scene
    );
    hemi.intensity = 0.7;
    hemi.diffuse = new BABYLON.Color3(0.95, 0.96, 1.0);
    hemi.groundColor = new BABYLON.Color3(0.2, 0.24, 0.34);
    hemi.specular = new BABYLON.Color3(0, 0, 0);

    // Focos cálidos repartidos a lo largo del eje Z (estilo museo). Cada uno con
    // una pequeña carcasa visible en el techo.
    const fixtureMat = new BABYLON.StandardMaterial("fixtureMat", scene);
    fixtureMat.diffuseColor = new BABYLON.Color3(0.06, 0.08, 0.14);
    fixtureMat.emissiveColor = new BABYLON.Color3(0.5, 0.45, 0.3); // foco encendido

    const nLuces = Math.max(1, Math.round(room.depth / 4));
    for (let i = 0; i < nLuces; i++) {
        const z = -room.depth / 2 + (i + 0.5) * (room.depth / nLuces);
        const pos = new BABYLON.Vector3(0, room.height - 0.25, z);

        const luz = new BABYLON.PointLight(`luz-${i}`, pos, scene);
        luz.intensity = 0.55;
        luz.diffuse = new BABYLON.Color3(1.0, 0.96, 0.86);
        luz.specular = new BABYLON.Color3(0.3, 0.28, 0.22);
        luz.range = room.depth; // alcance suficiente para las paredes laterales

        const carcasa = BABYLON.MeshBuilder.CreateBox(
            `fixture-${i}`,
            { width: 0.5, height: 0.08, depth: 0.18 },
            scene
        );
        carcasa.position = new BABYLON.Vector3(0, room.height - 0.05, z);
        carcasa.material = fixtureMat;
    }

    // ---- Obras: cada una en su pared (zona.codigo) y hueco (obra.orden) ----
    for (const zona of salaData.zonas) {
        for (const obra of zona.obras) {
            const placement = slotPlacement(
                zona.codigo,
                room,
                zona.capacidad,
                obra.orden
            );
            if (!placement) {
                console.warn(
                    `[scene] zona '${zona.codigo}' sin pared en la plantilla; obra omitida`
                );
                continue;
            }
            buildPainting(scene, obra, placement);
        }
    }

    // ---- Cámara primera persona (con salida por la puerta) ----
    createFirstPersonCamera(scene, canvas, room, options.onExit);

    return scene;
}
