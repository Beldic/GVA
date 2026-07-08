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
    const planta = buildRoom(scene, salaData.plantilla_3d);

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

    // Focos cálidos estilo museo: una fila por celda a lo largo de su eje más
    // largo, con una pequeña carcasa visible en el techo.
    const fixtureMat = new BABYLON.StandardMaterial("fixtureMat", scene);
    fixtureMat.diffuseColor = new BABYLON.Color3(0.06, 0.08, 0.14);
    fixtureMat.emissiveColor = new BABYLON.Color3(0.5, 0.45, 0.3); // foco encendido

    let li = 0;
    for (const c of planta.cells) {
        const alongZ = c.d >= c.w;
        const largo = alongZ ? c.d : c.w;
        const nLuces = Math.max(1, Math.round(largo / 4));
        for (let i = 0; i < nLuces; i++) {
            const t = -largo / 2 + (i + 0.5) * (largo / nLuces);
            const x = c.x + (alongZ ? 0 : t);
            const z = c.z + (alongZ ? t : 0);

            const luz = new BABYLON.PointLight(
                `luz-${li}`, new BABYLON.Vector3(x, planta.height - 0.25, z), scene
            );
            luz.intensity = 0.55;
            luz.diffuse = new BABYLON.Color3(1.0, 0.96, 0.86);
            luz.specular = new BABYLON.Color3(0.3, 0.28, 0.22);
            luz.range = Math.max(c.w, c.d);

            const carcasa = BABYLON.MeshBuilder.CreateBox(
                `fixture-${li}`,
                alongZ
                    ? { width: 0.5, height: 0.08, depth: 0.18 }
                    : { width: 0.18, height: 0.08, depth: 0.5 },
                scene
            );
            carcasa.position = new BABYLON.Vector3(x, planta.height - 0.05, z);
            carcasa.material = fixtureMat;
            li++;
        }
    }

    // ---- Obras: cada una en su pared (zona.codigo) y hueco (obra.orden) ----
    for (const zona of salaData.zonas) {
        for (const obra of zona.obras) {
            const placement = slotPlacement(
                zona.codigo,
                planta,
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
    createFirstPersonCamera(scene, canvas, planta, options.onExit);

    return scene;
}
