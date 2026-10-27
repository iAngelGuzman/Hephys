/*
 * Botón del "ojito" para mostrar u ocultar la contraseña (login y registro).
 * El botón indica qué campo controla: data-mostrar-password="id_del_input".
 */
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("[data-mostrar-password]").forEach(function (boton) {
    const campo = document.getElementById(boton.dataset.mostrarPassword);
    const icono = boton.querySelector("i");
    if (!campo) return;

    boton.addEventListener("click", function () {
      const oculta = campo.type === "password";
      campo.type = oculta ? "text" : "password";
      boton.setAttribute("aria-label", oculta ? "Ocultar contraseña" : "Mostrar contraseña");
      if (icono) {
        icono.classList.toggle("bi-eye", !oculta);
        icono.classList.toggle("bi-eye-slash", oculta);
      }
    });
  });
});
