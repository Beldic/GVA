import { ROOM } from "./room.js";

const PAINTING = {
    width: 1.2,
    height: 1.2,
    frameThickness: 0.08,
    frameDepth: 0.06,
    centerY: 1.75,
    wallOffset: 0.02, // separación de la pared para evitar z-fighting
    textureUrl: "/frontend-assets/images/afesol4.png",
};

const PLAQUE = {
    width: 0.5,
    height: 0.18,
    depth: 0.015,
    centerY: 0.9,
};

const TEXT = {
    title: "Sin título",
    author: "Autor AFESOL",
    year: "2026",
    description:
        "Esta es una obra de prueba para el piloto de la Galería Virtual de Arte. " +
        "El contenido definitivo será gestionado desde el panel de administración.",
};

export function buildPainting(scene) {
    const wallZ = ROOM.depth / 2;

    // ---- Marco (caja de madera oscura azulada) ----
    const frameMat = new BABYLON.StandardMaterial("frameMat", scene);
    frameMat.diffuseColor = new BABYLON.Color3(0.08, 0.12, 0.2);
    frameMat.specularColor = new BABYLON.Color3(0.25, 0.3, 0.4);
    frameMat.specularPower = 64;

    const frame = BABYLON.MeshBuilder.CreateBox(
        "paintingFrame",
        {
            width: PAINTING.width + PAINTING.frameThickness * 2,
            height: PAINTING.height + PAINTING.frameThickness * 2,
            depth: PAINTING.frameDepth,
        },
        scene
    );
    frame.position = new BABYLON.Vector3(
        0,
        PAINTING.centerY,
        wallZ - PAINTING.frameDepth / 2 - PAINTING.wallOffset
    );
    frame.material = frameMat;

    // ---- Lienzo (textura del logo placeholder) ----
    const canvasTexture = new BABYLON.Texture(
        PAINTING.textureUrl,
        scene,
        undefined,
        undefined,
        BABYLON.Texture.TRILINEAR_SAMPLINGMODE,
        () => console.info("[painting] textura cargada", PAINTING.textureUrl),
        (msg, ex) => console.error("[painting] error cargando textura", msg, ex)
    );
    canvasTexture.hasAlpha = false;

    const canvasMat = new BABYLON.StandardMaterial("canvasMat", scene);
    canvasMat.diffuseColor = new BABYLON.Color3(1, 1, 1); // fallback blanco
    canvasMat.diffuseTexture = canvasTexture;
    canvasMat.emissiveTexture = canvasTexture; // que el cuadro brille por sí solo
    canvasMat.emissiveColor = new BABYLON.Color3(0.35, 0.35, 0.35);
    canvasMat.specularColor = new BABYLON.Color3(0, 0, 0);
    canvasMat.backFaceCulling = false;

    const canvasPlane = BABYLON.MeshBuilder.CreatePlane(
        "paintingCanvas",
        {
            width: PAINTING.width,
            height: PAINTING.height,
            sideOrientation: BABYLON.Mesh.DOUBLESIDE,
        },
        scene
    );
    canvasPlane.position = new BABYLON.Vector3(
        0,
        PAINTING.centerY,
        wallZ - PAINTING.frameDepth - PAINTING.wallOffset - 0.001
    );
    // Sin rotación: el Plane de Babylon ya mira hacia -Z por defecto,
    // que es justamente hacia el centro de la sala.
    canvasPlane.material = canvasMat;

    // ---- Placa con título / autor / texto ----
    const plaqueMat = new BABYLON.StandardMaterial("plaqueMat", scene);
    plaqueMat.diffuseTexture = createPlaqueTexture(scene);
    plaqueMat.specularColor = new BABYLON.Color3(0.05, 0.05, 0.05);
    plaqueMat.emissiveColor = new BABYLON.Color3(0.08, 0.08, 0.08);

    const plaque = BABYLON.MeshBuilder.CreateBox(
        "plaque",
        { width: PLAQUE.width, height: PLAQUE.height, depth: PLAQUE.depth },
        scene
    );
    plaque.position = new BABYLON.Vector3(
        0,
        PLAQUE.centerY,
        wallZ - PLAQUE.depth / 2 - PAINTING.wallOffset
    );
    plaque.material = plaqueMat;
}

// ---- Texturas dinámicas ----

function createPlaqueTexture(scene) {
    const w = 1024;
    const h = 384;
    const tex = new BABYLON.DynamicTexture("plaqueTex", { width: w, height: h }, scene, false);
    const ctx = tex.getContext();

    // Fondo crema con leve gradiente
    const grad = ctx.createLinearGradient(0, 0, 0, h);
    grad.addColorStop(0, "#f7f4ec");
    grad.addColorStop(1, "#e8e2d2");
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, w, h);

    // Borde sutil
    ctx.strokeStyle = "#0a1f3d";
    ctx.lineWidth = 4;
    ctx.strokeRect(8, 8, w - 16, h - 16);

    // Título
    ctx.fillStyle = "#0a1f3d";
    ctx.textAlign = "center";
    ctx.font = "italic 64px 'Cormorant Garamond', Garamond, serif";
    ctx.fillText(TEXT.title, w / 2, 90);

    // Autor + año
    ctx.font = "32px 'Cormorant Garamond', Garamond, serif";
    ctx.fillStyle = "#14315c";
    ctx.fillText(`${TEXT.author} · ${TEXT.year}`, w / 2, 140);

    // Línea divisoria
    ctx.strokeStyle = "#14315c";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(w / 2 - 120, 170);
    ctx.lineTo(w / 2 + 120, 170);
    ctx.stroke();

    // Descripción (wrap manual)
    ctx.font = "26px 'Cormorant Garamond', Garamond, serif";
    ctx.fillStyle = "#1f2a3d";
    wrapText(ctx, TEXT.description, w / 2, 220, w - 100, 34);

    tex.update();
    return tex;
}

function wrapText(ctx, text, x, y, maxWidth, lineHeight) {
    const words = text.split(" ");
    let line = "";
    let cursorY = y;
    for (let i = 0; i < words.length; i++) {
        const testLine = line + words[i] + " ";
        const { width } = ctx.measureText(testLine);
        if (width > maxWidth && i > 0) {
            ctx.fillText(line.trim(), x, cursorY);
            line = words[i] + " ";
            cursorY += lineHeight;
        } else {
            line = testLine;
        }
    }
    ctx.fillText(line.trim(), x, cursorY);
}
