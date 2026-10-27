
document.addEventListener("DOMContentLoaded", function () {
  const modalSubida = document.getElementById("modal-confirmar-subida");
  const modalEliminar = document.getElementById("modal-confirmar-eliminar");
  const modalPublicado = document.getElementById("modal-horario-subido");
  const modalAviso = document.getElementById("modal-aviso-horario");
  const formEliminar = document.getElementById("form-eliminar-horario");
  let formularioPendiente = null;

  function abrir(modal) {
    modal.classList.add("mostrar");
    document.body.classList.add("modal-abierto");
  }

  function cerrar(modal) {
    modal.classList.remove("mostrar");
    document.body.classList.remove("modal-abierto");
  }

  document.querySelectorAll("[data-cerrar-modal]").forEach(function (boton) {
    boton.addEventListener("click", () =>
      cerrar(boton.closest(".modal-overlay")),
    );
  });

  function mostrarAviso(texto) {
    document.getElementById("texto-aviso-horario").textContent = texto;
    abrir(modalAviso);
    document.getElementById("btn-cerrar-aviso-horario").focus();
  }

  document
    .getElementById("btn-cerrar-aviso-horario")
    .addEventListener("click", function () {
      cerrar(modalAviso);
    });

  function errorDelArchivo(formulario) {
    const archivo = formulario.querySelector('input[type="file"]').files[0];
    if (!archivo) {
      return `Selecciona el PDF con el horario de exámenes de ${formulario.dataset.carrera} antes de publicarlo.`;
    }
    if (!archivo.name.toLowerCase().endsWith(".pdf")) {
      return `El archivo "${archivo.name}" no es un PDF. Selecciona el horario de exámenes en formato PDF.`;
    }
    return null;
  }

  document.querySelectorAll(".form-horario").forEach(function (formulario) {
    formulario.addEventListener("submit", function (event) {
      const error = errorDelArchivo(formulario);
      if (error) {
        event.preventDefault();
        mostrarAviso(error);
        return;
      }

      if (!formulario.hasAttribute("data-existe")) return; 
      event.preventDefault();
      formularioPendiente = formulario;
      document.getElementById("texto-confirmar-subida").textContent =
        `Ya hay un horario de exámenes cargado para ${formulario.dataset.carrera}. ` +
        "Si continúas, se reemplazará con el nuevo archivo.";
      abrir(modalSubida);
    });
  });

  document
    .getElementById("btn-confirmar-subida")
    .addEventListener("click", function () {
      cerrar(modalSubida);
      if (formularioPendiente) {
        formularioPendiente.submit();
        formularioPendiente = null;
      }
    });

  document.querySelectorAll("[data-quitar-horario]").forEach(function (boton) {
    boton.addEventListener("click", function () {
      document.getElementById("eliminar-carrera-code").value =
        boton.dataset.quitarHorario;
      document.getElementById("texto-confirmar-eliminar").textContent =
        `¿Seguro que deseas quitar el horario de exámenes de ${boton.dataset.nombre}? ` +
        "Esta acción no se puede deshacer.";
      abrir(modalEliminar);
    });
  });
  modalAviso.addEventListener("click", function (event) {
    if (event.target === modalAviso) cerrar(modalAviso);
  });
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && modalAviso.classList.contains("mostrar"))
      cerrar(modalAviso);
  });

  document
    .getElementById("btn-confirmar-eliminar")
    .addEventListener("click", function () {
      cerrar(modalEliminar);
      formEliminar.submit();
    });
  const franjasError = document.querySelectorAll("[data-aviso-modal]");
  if (franjasError.length) {
    franjasError.forEach((franja) => mostrarElemento(franja, false));
    mostrarAviso(
      Array.from(franjasError, (franja) => franja.textContent.trim()).join(" "),
    );
  }

  const mensaje = document.getElementById("mensaje-horario-subido");
  if (mensaje) {
    const botonAceptar = document.getElementById("btn-cerrar-horario-subido");
    document.getElementById("texto-horario-subido").textContent =
      mensaje.content.textContent.trim();

    botonAceptar.addEventListener("click", () => cerrar(modalPublicado));
    modalPublicado.addEventListener("click", function (event) {
      if (event.target === modalPublicado) cerrar(modalPublicado);
    });
    document.addEventListener("keydown", function (event) {
      if (
        event.key === "Escape" &&
        modalPublicado.classList.contains("mostrar")
      )
        cerrar(modalPublicado);
    });

    abrir(modalPublicado);
    botonAceptar.focus();
  }
});
