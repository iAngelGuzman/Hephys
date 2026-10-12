
document.addEventListener("DOMContentLoaded", function () {
  const cuerpoTabla = document.getElementById("tablaSolicitudes");
  if (!cuerpoTabla) return;

  const buscar = document.getElementById("buscarSolicitud");
  const filtroTipo = document.getElementById("filtroTipo");
  const filtroEstado = document.getElementById("filtroEstado");
  const btnLimpiar = document.getElementById("btnLimpiar");
  const textoPie = document.querySelector(".footer-tabla p");
  const paginacion = document.querySelector(".paginacion");

  const POR_PAGINA = 10;
  let paginaActual = 1;

  const filas = Array.from(cuerpoTabla.querySelectorAll("tr"));
  const filaVacia = filas.find((fila) => fila.querySelector("td[colspan]"));
  const filasDatos = filas.filter((fila) => fila !== filaVacia);

  function filasQueCoinciden() {
    const texto = (buscar ? buscar.value : "").toLowerCase().trim();
    const tipo = filtroTipo ? filtroTipo.value.trim() : "";
    const estado = filtroEstado ? filtroEstado.value.toLowerCase().trim() : "";

    return filasDatos.filter(function (fila) {
      const contenido = fila.textContent.toLowerCase();
      const matricula = (fila.dataset.matricula || "").toLowerCase();
      return (
        (contenido.includes(texto) || matricula.includes(texto)) &&
        (!tipo || fila.dataset.tipo === tipo) &&
        (!estado || (fila.dataset.estado || "").toLowerCase() === estado)
      );
    });
  }

  function crearBoton(
    texto,
    pagina,
    { activo = false, deshabilitado = false } = {},
  ) {
    const boton = document.createElement("button");
    boton.type = "button";
    boton.textContent = texto;
    boton.disabled = deshabilitado;
    if (activo) boton.classList.add("activo");
    boton.addEventListener("click", function () {
      paginaActual = pagina;
      actualizar();
    });
    return boton;
  }

  function dibujarPaginacion(totalPaginas) {
    if (!paginacion) return;
    paginacion.replaceChildren(
      crearBoton("<", paginaActual - 1, { deshabilitado: paginaActual === 1 }),
      ...Array.from({ length: totalPaginas }, (_, i) =>
        crearBoton(String(i + 1), i + 1, { activo: i + 1 === paginaActual }),
      ),
      crearBoton(">", paginaActual + 1, {
        deshabilitado: paginaActual === totalPaginas,
      }),
    );
  }

  function actualizar() {
    const visibles = filasQueCoinciden();
    const total = visibles.length;
    const totalPaginas = Math.max(1, Math.ceil(total / POR_PAGINA));
    paginaActual = Math.min(Math.max(paginaActual, 1), totalPaginas);

    const inicio = (paginaActual - 1) * POR_PAGINA;
    const fin = inicio + POR_PAGINA;
    const pagina = new Set(visibles.slice(inicio, fin));

    filasDatos.forEach((fila) => mostrarElemento(fila, pagina.has(fila)));
    mostrarElemento(filaVacia, total === 0);

    if (textoPie) {
      textoPie.textContent =
        total === 0
          ? "Mostrando 0 de 0 solicitudes"
          : `Mostrando ${inicio + 1} - ${Math.min(fin, total)} de ${total} solicitudes`;
    }
    dibujarPaginacion(totalPaginas);
  }

  function aplicarFiltros() {
    paginaActual = 1;
    actualizar();
  }

  if (buscar) buscar.addEventListener("input", aplicarFiltros);
  if (filtroTipo) filtroTipo.addEventListener("change", aplicarFiltros);
  if (filtroEstado) filtroEstado.addEventListener("change", aplicarFiltros);
  if (btnLimpiar) {
    btnLimpiar.addEventListener("click", function () {
      [buscar, filtroTipo, filtroEstado].forEach((campo) => {
        if (campo) campo.value = "";
      });
      aplicarFiltros();
    });
  }


  const tipoInicial = new URLSearchParams(window.location.search).get("tipo");
  if (
    filtroTipo &&
    tipoInicial &&
    Array.from(filtroTipo.options).some(
      (opcion) => opcion.value === tipoInicial,
    )
  ) {
    filtroTipo.value = tipoInicial;
  }

  actualizar();
});
