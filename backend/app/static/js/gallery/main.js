import { createScene } from "./scene.js";

const canvas = document.getElementById("renderCanvas");
const overlay = document.getElementById("overlay");
const startBtn = document.getElementById("start-btn");

if (typeof BABYLON === "undefined") {
    console.error("Babylon.js no se ha cargado.");
} else {
    const engine = new BABYLON.Engine(canvas, true, {
        preserveDrawingBuffer: true,
        stencil: true,
        adaptToDeviceRatio: true,
    });

    const scene = createScene(engine, canvas);

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
