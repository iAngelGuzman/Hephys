const DetalleSolicitud = (function () {
  let solicitudesPorId = {};
  let idActual = null;

  function modal() {
    return document.getElementById("modalSolicitud");
  }

  function recargarDatos() {
    solicitudesPorId = {};
    for (const solicitud of leerJsonScript("solicitudes-data", [])) {
      solicitudesPorId[String(solicitud.id)] = solicitud;
    }
  }

  function poner(id, texto) {
    const elemento = document.getElementById(id);
    if (elemento) elemento.textContent = texto || "-";
  }

  function textoObservaciones(observaciones) {
    if (observaciones.includes("BAJA-LOTE-")) {
      return "Trámite procesado mediante baja masiva en lote";
    }
    if (observaciones.includes("ALTA-LOTE-")) {
      return "Trámite procesado mediante alta masiva en lote";
    }
    return observaciones;
  }

  function crearEnlaceDocumento(texto, url, claseExtra) {
    const item = document.createElement("div");
    item.className = "documento-item";

    const etiqueta = document.createElement("p");
    etiqueta.textContent = texto;

    const enlace = document.createElement("a");
    enlace.href = url;
    enlace.target = "_blank";
    enlace.rel = "noopener";
    enlace.className = "btn-ver-pdf " + claseExtra;
    enlace.textContent = "Abrir";

    item.append(etiqueta, enlace);
    return item;
  }

  function llenarDocumentos(solicitud) {
    const contenedor = document.getElementById("modalDocumentosContenedor");
    const urls = modal().dataset;
    contenedor.replaceChildren();

    if (solicitud.tiene_horario) {
      contenedor.appendChild(
        crearEnlaceDocumento(
          "Horario de clases adjunto:",
          urlConId(urls.urlHorario, solicitud.id),
          "btn-ver-pdf--horario",
        ),
      );
    }

    if (solicitud.tiene_documento_medico) {
      contenedor.appendChild(
        crearEnlaceDocumento(
          "Comprobante médico:",
          urlConId(urls.urlDocumentoMedico, solicitud.id),
          "btn-ver-pdf--horario",
        ),
      );
    }

    for (const papeleta of solicitud.papeletas || []) {
      contenedor.appendChild(
        crearEnlaceDocumento(
          `Papeleta de pago (folio ${papeleta.folio}):`,
          urls.urlComprobante + "?id=" + encodeURIComponent(papeleta.id),
          "btn-ver-pdf--papeleta",
        ),
      );
    }

    if (!contenedor.children.length) {
      const vacio = document.createElement("p");
      vacio.className = "documentos-vacio";
      vacio.textContent = "No hay documentos adjuntos para esta solicitud.";
      contenedor.appendChild(vacio);
    }
  }

  function abrir(id) {
    const solicitud = solicitudesPorId[String(id)];
    if (!solicitud) return;
    idActual = solicitud.id;

    poner("modalFolio", "Folio S" + String(solicitud.id).padStart(5, "0"));
    poner("modalNombre", solicitud.nombre);
    poner("modalMatricula", solicitud.matricula);
    poner("modalCarrera", solicitud.carrera);
    poner("modalTipo", solicitud.tipo_tramite_display);
    poner("modalMateria", solicitud.materia_nombre);
    poner("modalNrc", solicitud.materia_nrc);
    poner("modalMaestro", solicitud.materia_maestro);
    poner("modalInscripcion", solicitud.status_inscripcion);
    poner(
      "modalFolioPago",
      (solicitud.papeletas || [])
        .map((p) => p.folio)
        .filter(Boolean)
        .join(", "),
    );
    poner("modalFecha", solicitud.fecha_solicitud);
    poner("modalEstado", solicitud.estado_display);

    const tipo = solicitud.tipo_tramite;
    const esConstancia = tipo === "constancia";
    const esJustificante = tipo === "justificante";
    for (const dato of modal().querySelectorAll("[data-dato-materia]")) {
      mostrarElemento(dato, !esConstancia && !esJustificante);
    }

    for (const dato of modal().querySelectorAll("[data-dato-justificante]")) {
      mostrarElemento(dato, esJustificante);
    }
    poner("modalInasistencia", solicitud.inasistencia);
    poner(
      "modalDiasAutorizados",
      solicitud.dias_autorizados || "Pendiente de autorizar",
    );

    for (const dato of modal().querySelectorAll("[data-dato-pago]")) {
      mostrarElemento(dato, !esJustificante);
    }
    const motivos = {
      baja: ["Motivo de la baja", solicitud.motivo_baja],
      constancia: [
        "Motivo y especificaciones de la constancia",
        solicitud.motivo_constancia,
      ],
      justificante: [
        "Motivo de la inasistencia",
        solicitud.motivo_justificante,
      ],
    };
    const [etiquetaMotivo, textoMotivo] = motivos[tipo] || ["", ""];
    const motivo = (textoMotivo || "").trim();
    poner("etiquetaMotivo", etiquetaMotivo);
    poner("modalMotivoBaja", motivo);
    mostrarElemento(
      document.getElementById("contenedorMotivoBaja"),
      motivo !== "",
    );

    const observaciones = (solicitud.observaciones || "").trim();
    poner("modalObservaciones", textoObservaciones(observaciones));
    mostrarElemento(
      document.getElementById("contenedorObservaciones"),
      observaciones !== "",
    );

    llenarDocumentos(solicitud);
    mostrar();
  }

  function mostrar() {
    modal().classList.add("mostrar");
    document.body.classList.add("modal-abierto");
  }

  function ocultar() {
    modal().classList.remove("mostrar");
  }

  function cerrar() {
    ocultar();
    document.body.classList.remove("modal-abierto");
  }

  document.addEventListener("DOMContentLoaded", function () {
    if (!modal()) return;
    recargarDatos();
    document.addEventListener("click", function (event) {
      const boton = event.target.closest("[data-abrir-solicitud]");
      if (boton) abrir(boton.dataset.abrirSolicitud);
    });

    modal().addEventListener("click", function (event) {
      if (
        event.target === modal() ||
        event.target.closest("[data-cerrar-modal]")
      ) {
        cerrar();
      }
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && modal().classList.contains("mostrar"))
        cerrar();
    });
  });

  return {
    abrir,
    cerrar,
    mostrar,
    ocultar,
    recargarDatos,
    idActual: () => idActual,
    actual: () => solicitudesPorId[String(idActual)] || null,
  };
})();
