/*
 * Registro de alumnos: la matrícula (data-matricula) solo admite "S" y
 * dígitos, en mayúsculas. Los nombres usan static/js/solo_letras.js.
 * Son ayudas; RegistroAlumnoForm valida lo mismo en el servidor.
 */
document.addEventListener("DOMContentLoaded", function () {
  const NO_MATRICULA = /[^sS0-9]/g;

  document.querySelectorAll("[data-matricula]").forEach(function (campo) {
    campo.addEventListener("input", function () {
      campo.value = campo.value.replace(NO_MATRICULA, "").toUpperCase();
    });
  });
});
