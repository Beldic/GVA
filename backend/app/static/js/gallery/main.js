import { createScene } from "./scene.js";

const canvas = document.getElementById("renderCanvas");
const doorLayer = document.getElementById("door-layer");
const enterBtn = document.getElementById("enter-btn");
const resume = document.getElementById("resume");
const resumeBtn = document.getElementById("resume-btn");
const salirLink = document.getElementById("salir-link");
const portalUrl = salirLink ? salirLink.href : "/";

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

    let entrado = false; // se han abierto las puertas y empezó la visita
    let saliendo = false; // animación de salida en curso

    const bloquearPuntero = () => {
        window.setTimeout(() => {
            if (canvas.requestPointerLock) canvas.requestPointerLock();
        }, 40);
    };

    // ---- Salida cinematográfica: la puerta se cierra y volvemos al portal ----
    const salirPorLaPuerta = () => {
        if (saliendo) return;
        saliendo = true;
        if (resume) resume.classList.add("is-hidden");
        if (document.pointerLockElement) document.exitPointerLock();
        if (!doorLayer) {
            window.location.href = portalUrl;
            return;
        }
        // Coloca las hojas abiertas al instante (no-anim) y luego las cierra.
        doorLayer.classList.add("is-exiting", "no-anim", "is-opening");
        doorLayer.classList.remove("is-gone");
        void doorLayer.offsetWidth; // fuerza reflow para fijar el estado abierto
        doorLayer.classList.remove("no-anim", "is-opening"); // las hojas se cierran
        window.setTimeout(() => {
            window.location.href = portalUrl;
        }, 1900);
    };

    const scene = createScene(engine, canvas, datos, { onExit: salirPorLaPuerta });
    engine.runRenderLoop(() => scene.render());
    window.addEventListener("resize", () => engine.resize());

    // ---- Entrada: abrir las puertas y revelar la sala ----
    let abriendo = false;
    const abrirPuertas = () => {
        if (abriendo || saliendo) return;
        abriendo = true;
        doorLayer.classList.add("is-opening");
        window.setTimeout(() => doorLayer.classList.add("is-gone"), 1400);
        window.setTimeout(() => {
            entrado = true;
            bloquearPuntero();
        }, 1600);
    };

    if (enterBtn) enterBtn.addEventListener("click", abrirPuertas);
    const frame = doorLayer && doorLayer.querySelector(".door-frame");
    if (frame) frame.addEventListener("click", abrirPuertas);
    window.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !entrado && !abriendo) abrirPuertas();
    });

    // ---- Reanudar tras liberar el cursor (Esc) ----
    if (resumeBtn) {
        resumeBtn.addEventListener("click", () => {
            resume.classList.add("is-hidden");
            bloquearPuntero();
        });
    }
    const resumeSalir = document.getElementById("resume-salir");
    if (resumeSalir) resumeSalir.addEventListener("click", salirPorLaPuerta);
    canvas.addEventListener("click", () => {
        if (entrado && !saliendo && !document.pointerLockElement) {
            canvas.requestPointerLock();
        }
    });
    document.addEventListener("pointerlockchange", () => {
        if (!document.pointerLockElement && entrado && !saliendo && resume) {
            resume.classList.remove("is-hidden");
        }
    });

    // ---- «Salir» del HUD: anima la salida en vez de navegar en seco ----
    if (salirLink) {
        salirLink.addEventListener("click", (e) => {
            e.preventDefault();
            salirPorLaPuerta();
        });
    }
}
