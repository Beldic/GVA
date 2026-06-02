import { createScene } from "./scene.js";

const canvas = document.getElementById("renderCanvas");
const overlay = document.getElementById("overlay");
const startBtn = document.getElementById("start-btn");

// Datos de la sala incrustados por el servidor (gallery.html).
function leerDatos() {
    const el = document.getElementById("gallery-data");
    if (!el) return null;
    try {
        return JSON.parse(el.textContent);
    } catch (err) {
        console.error("[gallery] datos incrustados inválidos", err);
        return null;
    }
}

const datos = leerDatos();

if (typeof BABYLON === "undefined") {
    console.error("Babylon.js no se ha cargado.");
} else if (!datos || !datos.sala) {
    console.error("[gallery] sin datos de sala: no se inicia el render.");
} else {
    const engine = new BABYLON.Engine(canvas, true, {
        preserveDrawingBuffer: true,
        stencil: true,
        adaptToDeviceRatio: true,
    });

    // Salir por la puerta = volver a donde apunta el enlace «Salir» del HUD.
    const salirLink = document.querySelector(".hud-link");
    const onExit = () => {
        window.location.href = salirLink ? salirLink.href : "/";
    };

    const scene = createScene(engine, canvas, datos, { onExit });

    engine.runRenderLoop(() => scene.render());

    window.addEventListener("resize", () => engine.resize());

    const enterPointerLock = () => {
        overlay.classList.add("is-hidden");
        // Pequeño retardo para que el clic del botón no entre en conflicto
        window.setTimeout(() => {
            if (canvas.requestPointerLock) {
                canvas.requestPointerLock();
            }
        }, 50);
    };

    startBtn.addEventListener("click", enterPointerLock);
    canvas.addEventListener("click", () => {
        if (overlay.classList.contains("is-hidden") && !document.pointerLockElement) {
            canvas.requestPointerLock();
        }
    });

    // Al soltar el ratón (Esc), volvemos a mostrar el overlay para reentrar
    document.addEventListener("pointerlockchange", () => {
        if (!document.pointerLockElement) {
            overlay.classList.remove("is-hidden");
        }
    });
}
