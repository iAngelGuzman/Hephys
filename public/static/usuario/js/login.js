// Cierra el modal de error del inicio de sesión.
document.addEventListener("DOMContentLoaded", function () {
  const boton = document.getElementById("btnCerrarError");
  const modal = document.getElementById("errorModal");
  if (!boton || !modal) return;

  boton.addEventListener("click", function () {
    modal.remove();
  });
});
