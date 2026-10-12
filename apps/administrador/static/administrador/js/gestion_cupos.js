/*
 * Gestión de cupos (administrador/altas_bajas/gestion_cupos.html):
 * filtros, paginación y el modal para ajustar el cupo de un NRC.
 * El máximo de cupo llega del servidor en data-cupo-maximo y se vuelve a
 * validar en la vista.
 */
document.addEventListener("DOMContentLoaded", function () {
  const buscador = document.getElementById("buscadorOferta");
  const filtroCarrera = document.getElementById("filtroCarrera");
  const modal = document.getElementById("modalCupo");
  const formulario = document.getElementById("formModalCupo");
  const inputCupo = document.getElementById("modal-input-cupo");
  const alerta = document.getElementById("alertaModalCupo");
  const cupoMaximo = Number(formulario.dataset.cupoMaximo);

  // --- Filtros y paginación (se recarga la página con los parámetros) ------

  function irA(cambios) {
    const parametros = new URLSearchParams(window.location.search);
    Object.entries(cambios).forEach(function ([clave, valor]) {
      if (valor) parametros.set(clave, valor);
      else parametros.delete(clave);
    });
    window.location.search = parametros.toString();
  }

  filtroCarrera.addEventListener("change", function () {
    irA({ carrera: filtroCarrera.value, q: buscador.value.trim(), page: "1" });
  });

  document.getElementById("paginacion-contenedor").addEventListener("click", function (event) {
    const boton = event.target.closest("button[data-pagina]");
    if (boton) irA({ page: boton.dataset.pagina });
  });

  // El buscador filtra al instante las filas de la página actual.
  buscador.addEventListener("input", function () {
    const texto = buscador.value.toLowerCase().trim();
    document.querySelectorAll("#tablaOfertas tbody tr").forEach(function (fila) {
      if (fila.cells.length === 1) return; // fila de "no hay registros"
      mostrarElemento(fila, fila.textContent.toLowerCase().includes(texto));
    });
  });

  // --- Modal para ajustar el cupo -----------------------------------------------

  function abrirModal(boton) {
    document.getElementById("modal-nrc").value = boton.dataset.nrc;
    document.getElementById("modal-nrc-label").textContent = boton.dataset.nrc;
    document.getElementById("modal-nombre-ee").textContent = `EE: ${boton.dataset.nombre}`;
    document.getElementById("modal-input-carrera").value = filtroCarrera.value;
    document.getElementById("modal-input-q").value = buscador.value.trim();
    document.getElementById("modal-input-page").value = "1";
    inputCupo.value = boton.dataset.cupo;
    mostrarElemento(alerta, false);

    modal.classList.add("mostrar");
    document.body.classList.add("modal-abierto");
  }

  function cerrarModal() {
    modal.classList.remove("mostrar");
    document.body.classList.remove("modal-abierto");
  }

  document.querySelectorAll("[data-ajustar-cupo]").forEach(function (boton) {
    boton.addEventListener("click", () => abrirModal(boton));
  });
  modal.querySelectorAll("[data-cerrar-modal]").forEach(function (boton) {
    boton.addEventListener("click", cerrarModal);
  });

  formulario.addEventListener("submit", function (event) {
    if (Number(inputCupo.value) > cupoMaximo) {
      event.preventDefault();
      mostrarElemento(alerta, true);
      inputCupo.focus();
    }
  });
});
