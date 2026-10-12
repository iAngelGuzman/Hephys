/*
 * "Mis solicitudes" del alumno: los filtros y la paginación se resuelven en
 * el servidor. Al cambiar un filtro se pide la misma página con fetch y se
 * reemplazan la tabla, la paginación, el texto de resultados y el JSON del
 * modal de detalle, sin recargar toda la página.
 */
document.addEventListener("DOMContentLoaded", function () {
  const formulario = document.getElementById("filtros");
  if (!formulario) return;

  const busqueda = document.getElementById("busqueda");
  const tipo = document.getElementById("tipo");
  const estado = document.getElementById("estado");
  const url = formulario.action;

  // Partes de la página que cambian con cada búsqueda.
  const IDS_A_REEMPLAZAR = [
    "tabla-solicitudes",
    "paginacion-contenedor",
    "texto-resultados",
    "solicitudes-data",
  ];

  let temporizador;

  function parametros(pagina) {
    const datos = new URLSearchParams();
    if (busqueda.value.trim()) datos.set("busqueda", busqueda.value.trim());
    if (tipo.value) datos.set("tipo", tipo.value);
    if (estado.value) datos.set("estado", estado.value);
    if (pagina > 1) datos.set("page", pagina);
    return datos.toString();
  }

  function filtrar(pagina = 1) {
    clearTimeout(temporizador);
    temporizador = setTimeout(function () {
      const consulta = parametros(pagina);
      const destino = consulta ? url + "?" + consulta : url;

      fetch(destino, { headers: { "X-Requested-With": "XMLHttpRequest" } })
        .then((response) => response.text())
        .then(function (html) {
          const nuevo = new DOMParser().parseFromString(html, "text/html");
          for (const id of IDS_A_REEMPLAZAR) {
            const actual = document.getElementById(id);
            const reemplazo = nuevo.getElementById(id);
            if (actual && reemplazo) actual.innerHTML = reemplazo.innerHTML;
          }
          DetalleSolicitud.recargarDatos();
          window.history.pushState({}, "", destino);
        })
        .catch((error) => console.error("Error al filtrar:", error));
    }, 300);
  }

  busqueda.addEventListener("input", () => filtrar(1));
  tipo.addEventListener("change", () => filtrar(1));
  estado.addEventListener("change", () => filtrar(1));
  formulario.addEventListener("submit", function (event) {
    event.preventDefault();
    filtrar(1);
  });

  document.getElementById("paginacion-contenedor").addEventListener("click", function (event) {
    const boton = event.target.closest("button[data-pagina]");
    if (boton) filtrar(Number(boton.dataset.pagina));
  });
});
