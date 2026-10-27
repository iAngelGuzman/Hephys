/*
 * Campos marcados con data-solo-letras: al escribir o pegar se quitan los
 * números y signos (nombres y apellidos). Es solo una ayuda; el servidor
 * valida lo mismo en el formulario de Django.
 */
document.addEventListener("DOMContentLoaded", function () {
  const NO_LETRAS = /[^A-Za-zÁÉÍÓÚáéíóúÑñÜü\s]/g;

  document.querySelectorAll("[data-solo-letras]").forEach(function (campo) {
    campo.addEventListener("input", function () {
      campo.value = campo.value.replace(NO_LETRAS, "");
    });
  });
});
