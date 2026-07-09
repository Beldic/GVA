import { buildRoom, slotPlacement } from "./room.js?v=2";
import { buildPainting } from "./painting.js?v=2";
import { createFirstPersonCamera } from "./camera.js?v=2";

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

    // Iluminación: lucernarios (claraboyas cenitales que hacen de ventanas), un
    // panel luminoso alargado por celda con luz cálida repartida bajo él.
    const skyMat = new BABYLON.StandardMaterial("skyMat", scene);
    skyMat.emissiveColor = new BABYLON.Color3(0.92, 0.95, 1.0); // luz de día
    skyMat.diffuseColor = new BABYLON.Color3(0, 0, 0);
    skyMat.specularColor = new BABYLON.Color3(0, 0, 0);
    skyMat.disableLighting = true; // brilla uniforme, no depende de otras luces

    const skyFrameMat = new BABYLON.StandardMaterial("skyFrameMat", scene);
    skyFrameMat.diffuseColor = new BABYLON.Color3(0.05, 0.07, 0.12);
    skyFrameMat.specularColor = new BABYLON.Color3(0, 0, 0);

    let li = 0;
    planta.cells.forEach((c, ci) => {
        const alongZ = c.d >= c.w;
        const largo = alongZ ? c.d : c.w;
        const stripLen = Math.max(1, largo - 2.5);
        const stripW = 1.6;
        const dims = (extra) => (alongZ
            ? { width: stripW + extra, height: stripLen + extra }
            : { width: stripLen + extra, height: stripW + extra });

        // Marco oscuro recedido + panel luminoso, colgando bajo el techo mirando
        // abajo. Separación holgada entre techo / marco / panel para no depender del
        // filo de la precisión de profundidad (evita Z-fighting con el techo).
        const frame = BABYLON.MeshBuilder.CreateGround(`sky-frame-${ci}`, dims(0.35), scene);
        frame.position = new BABYLON.Vector3(c.x, planta.height - 0.04, c.z);
        frame.rotation.x = Math.PI;
        frame.material = skyFrameMat;

        const panel = BABYLON.MeshBuilder.CreateGround(`sky-${ci}`, dims(0), scene);
        panel.position = new BABYLON.Vector3(c.x, planta.height - 0.09, c.z);
        panel.rotation.x = Math.PI;
        panel.material = skyMat;

        // Focos cálidos bajo el lucernario, a lo largo del eje mayor.
        const nLuces = Math.max(2, Math.round(largo / 5));
        for (let i = 0; i < nLuces; i++) {
            const t = -largo / 2 + (i + 0.5) * (largo / nLuces);
            const x = c.x + (alongZ ? 0 : t);
            const z = c.z + (alongZ ? t : 0);
            const luz = new BABYLON.PointLight(
                `luz-${li}`, new BABYLON.Vector3(x, planta.height - 0.5, z), scene
            );
            luz.intensity = 0.42;
            luz.diffuse = new BABYLON.Color3(1.0, 0.96, 0.88);
            luz.specular = new BABYLON.Color3(0.2, 0.2, 0.18);
            luz.range = Math.max(c.w, c.d) * 1.15;
            li++;
        }
    });

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
