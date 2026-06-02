(() => {
    const body = document.body;
    const enterBtn = document.getElementById("enter-btn");
    const doorFrame = document.querySelector(".door-frame");
    const enterLink = document.getElementById("enter-link");

    if (!enterBtn || !doorFrame || !enterLink) return;

    let opened = false;

    const openDoors = () => {
        if (opened) return;
        opened = true;
        body.classList.add("is-opening");

        // Tras la animación de apertura, fade a blanco y redirige
        window.setTimeout(() => {
            body.classList.add("is-entering");
        }, 1500);

        window.setTimeout(() => {
            window.location.href = enterLink.href;
        }, 2300);
    };

    enterBtn.addEventListener("click", openDoors);
    doorFrame.addEventListener("click", openDoors);

    // Soporte teclado: Enter o Espacio sobre el botón ya funciona;
    // añadimos atajo global a Enter desde la página
    window.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !opened) {
            openDoors();
        }
    });
})();
