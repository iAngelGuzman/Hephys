// Buscador de la pantalla "Trámites Escolares" (filtra las tarjetas).
document.addEventListener("DOMContentLoaded", function () {
  const buscador = document.getElementById("buscador-tramites");
  const tarjetas = document.querySelectorAll(".tramite-card");
  const sinResultados = document.getElementById("sin-resultados");
  if (!buscador) return;

  buscador.addEventListener("input", function () {
    const texto = buscador.value.toLowerCase().trim();
    let encontrados = 0;

    tarjetas.forEach(function (tarjeta) {
      const coincide =
        tarjeta.dataset.nombre.includes(texto) ||
        tarjeta.dataset.descripcion.includes(texto);
      mostrarElemento(tarjeta, coincide);
      if (coincide) encontrados++;
    });

    sinResultados.hidden = encontrados > 0;
  });
});
