// Construye un cuadro (marco + lienzo + placa) a partir de los datos de una obra
// y lo coloca contra una pared usando el `placement` calculado por slotPlacement.
const PAINTING = {
    defaultSize: 1.0, // m, fallback cuando la obra no trae medidas
    maxSize: 2.4, // m, tope de seguridad por dimensión
    frameThickness: 0.08,
    frameDepth: 0.06,
    centerY: 1.75,
    wallOffset: 0.02, // separación de la pared para evitar z-fighting
    slotMargin: 0.3, // m, aire mínimo entre cuadros contiguos del mismo hueco
};

const PLAQUE = {
    width: 0.5,
    height: 0.18,
    depth: 0.015,
    centerY: 0.9,
};

let _seq = 0;

export function buildPainting(scene, obra, placement) {
    const id = _seq++;
    const parent = new BABYLON.TransformNode(`obra-${id}`, scene);
    parent.position = placement.position.clone();
    parent.rotation.y = placement.rotationY;

    const { width, height } = canvasSize(obra, placement.slotWidth);

    // ---- Marco (caja de madera oscura azulada) ----
    const frameMat = new BABYLON.StandardMaterial(`frameMat-${id}`, scene);
    frameMat.diffuseColor = new BABYLON.Color3(0.08, 0.12, 0.2);
    frameMat.specularColor = new BABYLON.Color3(0.25, 0.3, 0.4);
    frameMat.specularPower = 64;

    const frame = BABYLON.MeshBuilder.CreateBox(
        `frame-${id}`,
        {
            width: width + PAINTING.frameThickness * 2,
            height: height + PAINTING.frameThickness * 2,
            depth: PAINTING.frameDepth,
        },
        scene
    );
    // El centro de la sala es -Z en el espacio local del padre.
    frame.position = new BABYLON.Vector3(
        0,
        PAINTING.centerY,
        -(PAINTING.frameDepth / 2 + PAINTING.wallOffset)
    );
    frame.material = frameMat;
    frame.parent = parent;
    frame.metadata = { obraId: obra.id };

    // ---- Lienzo (textura de la obra desde Cloudinary o placeholder) ----
    const canvasTexture = new BABYLON.Texture(
        obra.imagen_url,
        scene,
        undefined,
        undefined,
        BABYLON.Texture.TRILINEAR_SAMPLINGMODE,
        null,
        (msg, ex) =>
            console.error("[painting] error cargando textura", obra.imagen_url, msg, ex)
    );
    canvasTexture.hasAlpha = false;

    const canvasMat = new BABYLON.StandardMaterial(`canvasMat-${id}`, scene);
    canvasMat.diffuseColor = new BABYLON.Color3(1, 1, 1); // fallback blanco
    canvasMat.diffuseTexture = canvasTexture;
    canvasMat.emissiveTexture = canvasTexture; // que el cuadro brille por sí solo
    canvasMat.emissiveColor = new BABYLON.Color3(0.35, 0.35, 0.35);
    canvasMat.specularColor = new BABYLON.Color3(0, 0, 0);
    // Sin backFaceCulling=false: el lienzo es DOUBLESIDE (ya trae sus dos caras).
    // Quitar el culling dibujaba las dos coincidentes a igual profundidad y podían
    // pelear por el z-buffer en GPU Apple (mismo bug que se corrigió en las paredes).

    const canvasPlane = BABYLON.MeshBuilder.CreatePlane(
        `canvas-${id}`,
        { width, height, sideOrientation: BABYLON.Mesh.DOUBLESIDE },
        scene
    );
    canvasPlane.position = new BABYLON.Vector3(
        0,
        PAINTING.centerY,
        -(PAINTING.frameDepth + PAINTING.wallOffset + 0.001)
    );
    canvasPlane.material = canvasMat;
    canvasPlane.parent = parent;
    // Para la detección de contemplación (scene.js): mirar lienzo o marco cuenta.
    canvasPlane.metadata = { obraId: obra.id };

    // ---- Placa con título / autor·año / descripción ----
    const plaqueMat = new BABYLON.StandardMaterial(`plaqueMat-${id}`, scene);
    plaqueMat.diffuseTexture = createPlaqueTexture(scene, obra, id);
    plaqueMat.specularColor = new BABYLON.Color3(0.05, 0.05, 0.05);
    plaqueMat.emissiveColor = new BABYLON.Color3(0.08, 0.08, 0.08);

    const plaque = BABYLON.MeshBuilder.CreateBox(
        `plaque-${id}`,
        { width: PLAQUE.width, height: PLAQUE.height, depth: PLAQUE.depth },
        scene
    );
    plaque.position = new BABYLON.Vector3(
        0,
        PLAQUE.centerY,
        -(PLAQUE.depth / 2 + PAINTING.wallOffset)
    );
    plaque.material = plaqueMat;
    plaque.parent = parent;

    return parent;
}

// Tamaño del lienzo en metros: medidas reales (cm→m) con topes y recorte al
// ancho de hueco disponible, manteniendo la proporción.
function canvasSize(obra, slotWidth) {
    let w = obra.ancho_cm ? obra.ancho_cm / 100 : PAINTING.defaultSize;
    let h = obra.alto_cm ? obra.alto_cm / 100 : PAINTING.defaultSize;

    const limitW = Math.min(
        PAINTING.maxSize,
        (slotWidth || PAINTING.maxSize) - PAINTING.slotMargin
    );
    if (w > limitW) {
        h *= limitW / w;
        w = limitW;
    }
    if (h > PAINTING.maxSize) {
        w *= PAINTING.maxSize / h;
        h = PAINTING.maxSize;
    }
    return { width: w, height: h };
}

// ---- Texturas dinámicas ----

function createPlaqueTexture(scene, obra, id) {
    const w = 1024;
    const h = 384;
    const tex = new BABYLON.DynamicTexture(
        `plaqueTex-${id}`,
        { width: w, height: h },
        scene,
        false
    );
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
    ctx.fillText(obra.titulo || "Sin título", w / 2, 90);

    // Autor + año
    const anio = obra.anio ? ` · ${obra.anio}` : "";
    ctx.font = "32px 'Cormorant Garamond', Garamond, serif";
    ctx.fillStyle = "#14315c";
    ctx.fillText(`${obra.autor || ""}${anio}`, w / 2, 140);

    // Línea divisoria
    ctx.strokeStyle = "#14315c";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(w / 2 - 120, 170);
    ctx.lineTo(w / 2 + 120, 170);
    ctx.stroke();

    // Descripción (wrap manual)
    if (obra.descripcion) {
        ctx.font = "26px 'Cormorant Garamond', Garamond, serif";
        ctx.fillStyle = "#1f2a3d";
        wrapText(ctx, obra.descripcion, w / 2, 220, w - 100, 34);
    }

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
