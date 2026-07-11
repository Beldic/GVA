import { createScene } from "./scene.js?v=2";

// Marca de build: sirve para comprobar en la consola del navegador que se está
// cargando la versión NUEVA del visor y no una cacheada. Súbela al desplegar.
console.log("[gallery] visor build v6");

const canvas = document.getElementById("renderCanvas");
const doorLayer = document.getElementById("door-layer");
const enterBtn = document.getElementById("enter-btn");
const instrucciones = document.getElementById("instrucciones");
const comenzarBtn = document.getElementById("comenzar-btn");
const resume = document.getElementById("resume");
const resumeBtn = document.getElementById("resume-btn");
const salirLink = document.getElementById("salir-link");
const flash = document.getElementById("door-flash");
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
const soloEscritorio = document.getElementById("solo-escritorio");

// El recorrido 3D usa teclado + ratón (pointer lock). Detectamos móvil/tablet
// por el puntero PRINCIPAL (pointer: coarse = táctil): muchos Android declaran
// además un puntero fino (S-Pen, ratón Bluetooth emparejado) y con
// any-pointer:fine se colaban al 3D. Un portátil táctil no entra aquí porque
// su puntero principal sigue siendo el ratón (fine).
function esSoloTactil() {
    try {
        return (
            window.matchMedia("(pointer: coarse)").matches ||
            !window.matchMedia("(any-pointer: fine)").matches
        );
    } catch (e) {
        return false;
    }
}

if (esSoloTactil()) {
    // El aviso ofrece el enlace real al modo 2D (?modo=2d).
    if (doorLayer) doorLayer.classList.add("is-gone");
    if (resume) resume.classList.add("is-hidden");
    if (soloEscritorio) soloEscritorio.classList.remove("is-hidden");
} else if (typeof BABYLON === "undefined") {
    console.error("Babylon.js no se ha cargado.");
} else if (!datos || !datos.sala) {
    console.error("[gallery] sin datos de sala: no se inicia el render.");
} else {
    // preserveDrawingBuffer se quita a propósito: en las GPU Apple (Metal) forzaba
    // un camino de compositor que dibujaba rectángulos blancos a medio renderizar
    // mientras se movía la cámara (limpio al parar). No lo necesitamos: no hay
    // capturas de pantalla que requieran conservar el búfer entre fotogramas.
    const engine = new BABYLON.Engine(canvas, true, {
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
        // Destello luminoso justo cuando las hojas se abren.
        window.setTimeout(() => { if (flash) flash.classList.add("flash-on"); }, 1050);
        window.setTimeout(() => doorLayer.classList.add("is-gone"), 1400);
        // Cruzada la puerta, la ventana de instrucciones toma el relevo;
        // el puntero no se bloquea hasta «Comenzar la visita».
        window.setTimeout(() => {
            if (instrucciones && comenzarBtn) {
                instrucciones.classList.remove("is-hidden");
            } else {
                entrado = true;
                bloquearPuntero();
            }
        }, 1750);
    };

    // ---- Instrucciones -> tomar los mandos (y música según la casilla) ----
    const comenzarVisita = () => {
        if (entrado || saliendo) return;
        entrado = true;
        if (instrucciones) instrucciones.classList.add("is-hidden");
        const chk = document.getElementById("chk-musica");
        if (window.__hiloMusical) window.__hiloMusical.iniciar(!chk || chk.checked);
        bloquearPuntero();
    };
    if (comenzarBtn) comenzarBtn.addEventListener("click", comenzarVisita);

    if (enterBtn) enterBtn.addEventListener("click", abrirPuertas);
    const frame = doorLayer && doorLayer.querySelector(".door-frame");
    if (frame) frame.addEventListener("click", abrirPuertas);
    window.addEventListener("keydown", (e) => {
        if (e.key !== "Enter" || entrado) return;
        if (!abriendo) {
            abrirPuertas();
        } else if (instrucciones && !instrucciones.classList.contains("is-hidden")) {
            comenzarVisita();
        }
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
