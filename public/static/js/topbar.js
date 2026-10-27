// Menú desplegable del usuario en la barra superior (templates/topbar.html).
document.addEventListener("DOMContentLoaded", function () {
  const boton = document.getElementById("btnMenuUsuario");
  const menu = document.getElementById("userDropdown");
  const contenedor = document.querySelector(".user-menu");
  if (!boton || !menu || !contenedor) return;

  boton.addEventListener("click", function () {
    menu.classList.toggle("show");
  });

  // Se cierra al hacer clic en cualquier otra parte de la página.
  document.addEventListener("click", function (event) {
    if (!contenedor.contains(event.target)) {
      menu.classList.remove("show");
    }
  });
});
