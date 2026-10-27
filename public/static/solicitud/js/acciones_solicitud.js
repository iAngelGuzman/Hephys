
document.addEventListener("DOMContentLoaded", function () {
  const modalAprobar = document.getElementById("modalConfirmacion");
  const modalRechazar = document.getElementById("modalConfirmacionRechazo");
  if (!modalAprobar || !modalRechazar) return;

  const alertaMotivo = document.getElementById("alertaMotivoVacio");
  const seccionDias = document.getElementById("seccionDiasAutorizados");
  const diasDesde = document.getElementById("diasAutorizadosDesde");
  const diasHasta = document.getElementById("diasAutorizadosHasta");
  const alertaDias = document.getElementById("alertaDiasAutorizados");

  function solicitudActual() {
    return DetalleSolicitud.actual ? DetalleSolicitud.actual() : null;
  }

  function pideDiasAutorizados() {
    const solicitud = solicitudActual();
    return Boolean(
      seccionDias && solicitud && solicitud.tipo_tramite === "justificante",
    );
  }

  function prepararDiasAutorizados() {
    if (!seccionDias) return;
    const mostrar = pideDiasAutorizados();
    mostrarElemento(seccionDias, mostrar);
    mostrarElemento(alertaDias, false);
    if (!mostrar) return;

    const solicitud = solicitudActual();
    document.getElementById("diasSolicitados").textContent =
      solicitud.inasistencia || "-";
    for (const campo of [diasDesde, diasHasta]) {
      campo.min = solicitud.inasistencia_inicio;
      campo.max = solicitud.inasistencia_fin;
    }
    diasDesde.value = solicitud.inasistencia_inicio;
    diasHasta.value = solicitud.inasistencia_fin;
  }

  function leerDiasAutorizados() {
    const desde = diasDesde.value;
    const hasta = diasHasta.value;
    let error = "";
    if (!desde || !hasta) {
      error = "Indica desde y hasta qué día autorizas.";
    } else if (desde > hasta) {
      error = "El primer día autorizado no puede ser posterior al último.";
    } else if (desde < diasDesde.min || hasta > diasHasta.max) {
      error =
        "Los días autorizados deben estar dentro de los que pidió el alumno.";
    }
    if (error) {
      alertaDias.textContent = error;
      mostrarElemento(alertaDias, true);
      return null;
    }
    mostrarElemento(alertaDias, false);
    return { fecha_inicio_autorizada: desde, fecha_fin_autorizada: hasta };
  }


  const textoConfirmacion = document.getElementById("textoConfirmacion");
  const botonConfirmar = document.getElementById("btnConfirmarAprobacion");
  const TEXTO_GENERAL = textoConfirmacion ? textoConfirmacion.textContent : "";
  const BOTON_GENERAL = botonConfirmar ? botonConfirmar.textContent : "";
  const TEXTOS_CONSTANCIA = {
    grupo: [
      "Confirma que verificaste que el alumno está inscrito en el periodo " +
        "actual y que elaboraste la constancia. Se turnará a la Secretaría " +
        "Académica para su firma.",
      "Sí, turnar a firma",
    ],
    academica: [
      "Confirma que la constancia fue firmada y sellada. El alumno podrá " +
        "pasar a recogerla con su secretaria de grupo.",
      "Sí, firmada",
    ],
  };

  function prepararTextoAprobacion() {
    if (!textoConfirmacion || !botonConfirmar) return;
    const solicitud = solicitudActual();
    const textos =
      solicitud && solicitud.tipo_tramite === "constancia"
        ? TEXTOS_CONSTANCIA[modalAprobar.dataset.rol]
        : null;
    textoConfirmacion.textContent = textos ? textos[0] : TEXTO_GENERAL;
    botonConfirmar.textContent = textos ? textos[1] : BOTON_GENERAL;
  }

  function prepararMotivosRechazo() {
    const solicitud = solicitudActual();
    const tipo = solicitud ? solicitud.tipo_tramite : "";
    modalRechazar
      .querySelectorAll("[data-solo-tramite]")
      .forEach((etiqueta) =>
        mostrarElemento(etiqueta, etiqueta.dataset.soloTramite === tipo),
      );
  }
  const casillasMotivo = () =>
    modalRechazar.querySelectorAll('input[name="motivo_rechazo"]');

  function enviar(urlBase, cuerpo, mensajeError) {
    const id = DetalleSolicitud.idActual();
    if (!id) {
      alert("No se ha seleccionado ninguna solicitud.");
      return;
    }

    fetch(urlConId(urlBase, id), {
      method: "POST",
      headers: {
        "X-CSRFToken": obtenerTokenCsrf(),
        "Content-Type": "application/json",
      },
      body: cuerpo ? JSON.stringify(cuerpo) : undefined,
    })
      .then(leerRespuestaJson)
      .then((data) => {
        if (data.success) {
          location.reload();
        } else {
          alert(data.error || mensajeError);
        }
      })
      .catch((error) => {
        console.error("Error al enviar la acción:", error);
        alert(
          "No se pudo conectar con el servidor. Revisa tu conexión e inténtalo de nuevo.",
        );
      });
  }

  document
    .getElementById("btnAbrirAprobacion")
    .addEventListener("click", function () {
      DetalleSolicitud.ocultar();
      prepararDiasAutorizados();
      prepararTextoAprobacion();
      modalAprobar.classList.add("mostrar");
    });

  document
    .getElementById("btnCancelarAprobacion")
    .addEventListener("click", function () {
      modalAprobar.classList.remove("mostrar");
      DetalleSolicitud.mostrar();
    });

  document
    .getElementById("btnConfirmarAprobacion")
    .addEventListener("click", function () {
      let cuerpo = null;
      if (pideDiasAutorizados()) {
        cuerpo = leerDiasAutorizados();
        if (!cuerpo) return;
      }
      enviar(
        modalAprobar.dataset.urlAprobar,
        cuerpo,
        "Hubo un error al aprobar la solicitud.",
      );
    });

  document
    .getElementById("btnAbrirRechazo")
    .addEventListener("click", function () {
      DetalleSolicitud.ocultar();
      mostrarElemento(alertaMotivo, false);
      casillasMotivo().forEach((casilla) => (casilla.checked = false));
      prepararMotivosRechazo();
      modalRechazar.classList.add("mostrar");
    });

  document
    .getElementById("btnCancelarRechazo")
    .addEventListener("click", function () {
      mostrarElemento(alertaMotivo, false);
      modalRechazar.classList.remove("mostrar");
      DetalleSolicitud.mostrar();
    });

  document
    .getElementById("btnConfirmarRechazo")
    .addEventListener("click", function () {
      const motivos = Array.from(casillasMotivo())
        .filter((casilla) => casilla.checked && !casilla.closest(".oculto"))
        .map((casilla) => casilla.value);

      if (motivos.length === 0) {
        mostrarElemento(alertaMotivo, true);
        return;
      }
      mostrarElemento(alertaMotivo, false);

      enviar(
        modalAprobar.dataset.urlRechazar,
        { motivo: motivos.join(". ") },
        "Hubo un error al rechazar la solicitud.",
      );
    });
});
