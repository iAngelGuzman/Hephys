/*
 * Control de usuarios (administrador/control_usuarios.html): buscador,
 * paginación y los modales para crear, editar y activar/desactivar
 * secretarias de grupo. Las validaciones de aquí son una ayuda; las reales
 * están en CrearSecretariaForm / EditarSecretariaForm.
 */
document.addEventListener("DOMContentLoaded", function () {
  const SOLO_LETRAS = /^[A-Za-zÁÉÍÓÚáéíóúÑñÜü\s]+$/;
  const REGEX_CORREO = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

  const formCrear = document.getElementById("formCrearUsuario");
  const formEditar = document.getElementById("formEditarUsuario");
  const formEstado = document.getElementById("formDesactivarUsuario");

  function abrirModal(modal) {
    modal.classList.add("mostrar");
    document.body.classList.add("modal-abierto");
  }

  function cerrarModal(modal) {
    modal.classList.remove("mostrar");
    document.body.classList.remove("modal-abierto");
  }

  document.querySelectorAll("[data-abrir-modal]").forEach(function (boton) {
    boton.addEventListener("click", () =>
      abrirModal(document.getElementById(boton.dataset.abrirModal)),
    );
  });
  document.querySelectorAll("[data-cerrar-modal]").forEach(function (boton) {
    boton.addEventListener("click", () =>
      cerrarModal(boton.closest(".modal-overlay")),
    );
  });


  const buscador = document.getElementById("buscadorUsuario");
  buscador.addEventListener("input", function () {
    const texto = buscador.value.toLowerCase().trim();
    document.querySelectorAll(".tabla tbody tr").forEach(function (fila) {
      if (fila.cells.length === 1) return;
      mostrarElemento(fila, fila.textContent.toLowerCase().includes(texto));
    });
  });

  document
    .getElementById("paginacion-contenedor")
    .addEventListener("click", function (event) {
      const boton = event.target.closest("button[data-pagina]");
      if (!boton) return;
      const parametros = new URLSearchParams(window.location.search);
      parametros.set("page", boton.dataset.pagina);
      window.location.search = parametros.toString();
    });

  document.querySelectorAll("[data-cambiar-estado]").forEach(function (boton) {
    boton.addEventListener("click", function () {
      const activo = boton.dataset.estado === "activo";
      formEstado.action = urlConId(
        formEstado.dataset.urlBase,
        boton.dataset.userid,
      );

      const accion = document.createElement("strong");
      accion.textContent = activo ? "desactivar" : "activar";
      const usuario = document.createElement("strong");
      usuario.textContent = boton.dataset.identificador;
      document
        .getElementById("mensajeModalConfirmacion")
        .replaceChildren(
          "¿Estás seguro de que deseas ",
          accion,
          " al usuario ",
          usuario,
          activo
            ? "? Perderá acceso temporal al sistema."
            : "? Recuperará su acceso al sistema.",
        );

      abrirModal(document.getElementById("modalDesactivarUsuario"));
    });
  });


  document.querySelectorAll("[data-editar-usuario]").forEach(function (boton) {
    boton.addEventListener("click", function () {
      formEditar.action = urlConId(
        formEditar.dataset.urlBase,
        boton.dataset.userid,
      );
      document.getElementById("edit_username").value = boton.dataset.username;
      document.getElementById("edit_first_name").value =
        boton.dataset.firstname;
      document.getElementById("edit_last_name").value = boton.dataset.lastname;
      document.getElementById("edit_email").value = boton.dataset.email;
      document.getElementById("edit_password").value = "";
      abrirModal(document.getElementById("modalEditarUsuario"));
    });
  });


  function validarNombres(event, idNombre, idApellidos) {
    const nombre = document.getElementById(idNombre).value.trim();
    const apellidos = document.getElementById(idApellidos).value.trim();
    if (!SOLO_LETRAS.test(nombre) || !SOLO_LETRAS.test(apellidos)) {
      alert("El nombre y los apellidos solo deben contener letras.");
      event.preventDefault();
      return false;
    }
    return true;
  }


  const btnTogglePassword = document.getElementById("togglePasswordCrear");
  const inputPassword = document.getElementById("crear_password");
  const iconoOjo = document.getElementById("iconoOjoCrear");

  if (btnTogglePassword && inputPassword && iconoOjo) {
    btnTogglePassword.addEventListener("click", function () {
      const tipo =
        inputPassword.getAttribute("type") === "password" ? "text" : "password";
      inputPassword.setAttribute("type", tipo);

      if (tipo === "text") {
        iconoOjo.classList.remove("bi-eye");
        iconoOjo.classList.add("bi-eye-slash");
      } else {
        iconoOjo.classList.remove("bi-eye-slash");
        iconoOjo.classList.add("bi-eye");
      }
    });
  }


  formCrear.addEventListener("submit", function (event) {
    event.preventDefault();

    const emailCrear = document.getElementById("crear_email");
    if (!emailCrear.value.trim()) {
      alert("El correo electrónico no puede estar en blanco.");
      return;
    }

    if (!REGEX_CORREO.test(emailCrear.value.trim())) {
      alert(
        "Por favor, ingresa un correo electrónico válido (ejemplo: usuario@correo.com).",
      );
      return;
    }

    const usernameCrear = document
      .getElementById("crear_username")
      .value.trim();
    if (usernameCrear.length < 8 || usernameCrear.length > 15) {
      alert("El nombre de usuario debe tener entre 8 y 15 caracteres.");
      return;
    }

    if (!validarNombres(event, "crear_first_name", "crear_last_name")) return;

    const passwordVal = document.getElementById("crear_password").value;
    if (passwordVal.length < 8) {
      alert("La contraseña debe tener al menos 8 caracteres.");
      return;
    }

    const contenedorErrorCrear = document.getElementById(
      "contenedor-error-crear",
    );
    if (contenedorErrorCrear) contenedorErrorCrear.innerHTML = "";

    const formData = new FormData(formCrear);
    fetch(formCrear.action, {
      method: "POST",
      body: formData,
      headers: {
        "X-Requested-With": "XMLHttpRequest",
      },
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          window.location.reload();
        } else {
          if (contenedorErrorCrear) {
            contenedorErrorCrear.innerHTML = `<div class="mensaje mensaje--error" role="alert">${data.error}</div>`;
          } else {
            alert(data.error);
          }
        }
      })
      .catch((error) => {
        alert("Ocurrió un error al procesar la solicitud.");
      });
  });

  formEditar.addEventListener("submit", function (event) {
    event.preventDefault();

    const emailEditar = document.getElementById("edit_email");
    if (!emailEditar.value.trim()) {
      alert(
        "Los campos de nombre, apellidos y correo electrónico no pueden estar en blanco.",
      );
      return;
    }

    if (!REGEX_CORREO.test(emailEditar.value.trim())) {
      alert(
        "Por favor, ingresa un correo electrónico válido (ejemplo: usuario@correo.com).",
      );
      return;
    }

    const username = document.getElementById("edit_username").value.trim();
    if (username.length < 8 || username.length > 15) {
      alert("El nombre de usuario debe tener entre 8 y 15 caracteres.");
      return;
    }

    if (!validarNombres(event, "edit_first_name", "edit_last_name")) return;

    const password = document.getElementById("edit_password").value;
    if (password.length > 0 && password.length < 8) {
      alert("La contraseña nueva debe tener al menos 8 caracteres.");
      return;
    }

    const contenedorError = document.getElementById("contenedor-error-editar");
    if (contenedorError) contenedorError.innerHTML = "";

    const formData = new FormData(formEditar);
    fetch(formEditar.action, {
      method: "POST",
      body: formData,
      headers: {
        "X-Requested-With": "XMLHttpRequest",
      },
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          window.location.reload();
        } else {
          if (contenedorError) {
            contenedorError.innerHTML = `<div class="mensaje mensaje--error" role="alert">${data.error}</div>`;
          } else {
            alert(data.error);
          }
        }
      })
      .catch((error) => {
        alert("Ocurrió un error al procesar la solicitud.");
      });
  });
});
