import mimetypes
import os
import uuid

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction

from app.models.estudiante import Estudiante

from . import reglas
from .constantes_solicitud import PRIMERA_INSCRIPCION, SEGUNDA_INSCRIPCION
from .excepciones_solicitud import (
    ErrorProcesandoHorario,
    HorarioSinMateriasError,
    PapeletaInvalidaError,
    TramiteNoPermitidoError,
)
from app.views.forms.solicitud import ComprobantePagoForm
from .lectores_pdf import extraer_materias_altas_bajas, extraer_materias_horario_examen
from app.models.solicitud import ComprobantePago, Solicitud

CARPETAS_ARCHIVOS = {
    "horarios": settings.CARPETA_PAPELES_HORARIOS,
    "comprobantes_pago": settings.CARPETA_COMPROBANTES_PAGO,
}


def guardar_archivo_temporal(archivo, subcarpeta="horarios"):
    """
    Guarda un archivo subido en la carpeta configurada en settings y
    regresa su ruta completa. Si ya existe un archivo con ese nombre,
    Django le agrega un sufijo (Horario_aB3dE9f.pdf) en vez de sobrescribirlo.
    """
    if hasattr(archivo, "seek"):
        archivo.seek(0)
    storage = FileSystemStorage(location=CARPETAS_ARCHIVOS[subcarpeta])
    nombre_guardado = storage.save(archivo.name, ContentFile(archivo.read()))
    return storage.path(nombre_guardado)


def procesar_horario(archivo_pdf, tipo_modulo="examen"):
    if hasattr(archivo_pdf, "seek"):
        archivo_pdf.seek(0)

    if tipo_modulo in ["bajas", "altas"]:
        materias = extraer_materias_altas_bajas(archivo_pdf, tipo_modulo=tipo_modulo)
        if not materias:
            raise HorarioSinMateriasError(
                "No se encontraron materias válidas o pertenecientes a la facultad en el horario de bajas."
            )
        ruta_horario = guardar_archivo_temporal(archivo_pdf)
        return materias, ruta_horario

    try:
        materias = extraer_materias_horario_examen(archivo_pdf)
    except HorarioSinMateriasError:
        raise
    except Exception as exc:
        raise ErrorProcesandoHorario() from exc

    if not materias:
        raise HorarioSinMateriasError("No se encontraron materias válidas en el PDF.")

    ruta_horario = guardar_archivo_temporal(archivo_pdf)

    return materias, ruta_horario


def procesar_papeletas(request, materias):
    papeletas = {}
    archivos_guardados = {}
    for materia in materias:
        nrc = str(materia["nrc"])
        archivo = request.FILES.get(f"papeleta_{nrc}")
        ruta_temp_previa = request.POST.get(f"papeleta_temp_{nrc}", "")
        folio = request.POST.get(f"folio_{nrc}", "").strip()
        archivo_a_validar = None
        nombre_original_actual = None
        if archivo:
            ruta_guardada = guardar_archivo_temporal(archivo, "comprobantes_pago")
            archivo_a_validar = archivo
            nombre_original_actual = archivo.name
            request.session[f"papeleta_temp_ruta_{nrc}"] = ruta_guardada
            request.session[f"papeleta_temp_nombre_{nrc}"] = nombre_original_actual
            request.session.modified = True
        elif ruta_temp_previa:
            ruta_guardada = request.session.get(f"papeleta_temp_ruta_{nrc}", "")
            nombre_original_actual = request.session.get(
                f"papeleta_temp_nombre_{nrc}", "papeleta.pdf"
            )
            if ruta_guardada and os.path.exists(ruta_guardada):
                with open(ruta_guardada, "rb") as f:
                    contenido = f.read()
                content_type, _ = mimetypes.guess_type(nombre_original_actual)
                archivo_a_validar = SimpleUploadedFile(
                    nombre_original_actual,
                    contenido,
                    content_type=content_type or "application/octet-stream",
                )

        if not archivo_a_validar:
            raise PapeletaInvalidaError(
                f"Falta la papeleta de {materia['materia']}.",
                archivos_guardados=archivos_guardados,
            )
        archivos_guardados[nrc] = {
            "ruta": ruta_guardada,
            "nombre_original": nombre_original_actual,
        }

        form = ComprobantePagoForm(
            data={"folio": folio},
            files={"archivo": archivo_a_validar},
        )
        if not form.is_valid():
            primer_error = next(iter(form.errors.values()))[0]
            raise PapeletaInvalidaError(
                f"{materia['materia']}: {primer_error}",
                archivos_guardados=archivos_guardados,
            )

        folio_limpio = form.cleaned_data["folio"]
        papeletas[nrc] = {
            "ruta": ruta_guardada,
            "folio": folio_limpio,
            "nombre_original": nombre_original_actual,
        }

    return papeletas


def crear_comprobante_pago(solicitud, papeleta_data):
    ruta_temporal = papeleta_data["ruta"]
    with open(ruta_temporal, "rb") as archivo_temporal:
        contenido = archivo_temporal.read()

    comprobante = ComprobantePago(
        solicitud=solicitud,
        folio=papeleta_data["folio"],
    )
    comprobante.archivo.save(
        papeleta_data["nombre_original"],
        ContentFile(contenido),
        save=False,
    )
    comprobante.save()

    if os.path.exists(ruta_temporal):
        os.remove(ruta_temporal)

    return comprobante


def _bloquear_estudiante(estudiante):
    return Estudiante.objects.select_for_update().get(pk=estudiante.pk)


def crear_solicitudes_examen(
    estudiante, tipo_examen, materias, papeletas, ruta_horario
):
    """
    Crea una solicitud de extraordinario o título de suficiencia por materia
    (con su papeleta). Los NRC que ya tienen una solicitud activa se omiten
    en silencio: solo pasa si el alumno reenvía el mismo formulario.
    Regresa la lista de ids creados.
    """
    ids_creados = []
    with transaction.atomic():
        estudiante = _bloquear_estudiante(estudiante)
        nrcs_activos = reglas.nrcs_con_solicitud_activa(estudiante)

        for materia in materias:
            nrc = str(materia.get("nrc", ""))
            if nrc in nrcs_activos:
                continue

            solicitud = Solicitud.objects.create(
                estudiante=estudiante,
                tipo_tramite=tipo_examen,
                materia_nrc=nrc,
                materia_nombre=materia.get("materia", ""),
                materia_maestro=materia.get("maestro", ""),
                status_inscripcion=(
                    SEGUNDA_INSCRIPCION
                    if materia.get("es_segunda_inscripcion")
                    else PRIMERA_INSCRIPCION
                ),
                ruta_horario=ruta_horario,
            )

            papeleta = papeletas.get(nrc)
            if papeleta:
                crear_comprobante_pago(solicitud, papeleta)

            ids_creados.append(solicitud.pk)

    return ids_creados


def crear_solicitudes_alta(
    estudiante, materias, horario_actual, vez_inscripcion, ruta_horario
):
    """
    Valida periodo, cruces de horario, materias repetidas y NRC ya
    solicitados; si todo está bien crea una solicitud por materia, todas con
    el mismo lote. Regresa el lote_id.
    """
    if not materias:
        raise TramiteNoPermitidoError(
            "Debes seleccionar al menos una experiencia educativa para dar de alta."
        )

    reglas.validar_tramite_abierto(reglas.TRAMITE_ALTAS, estudiante)
    reglas.validar_altas(horario_actual, materias)

    creditos_previos = sum(int(m.get("creditos") or 0) for m in horario_actual)
    creditos_totales = creditos_previos + sum(
        int(m.get("creditos") or 0) for m in materias
    )
    observaciones = (
        "Alta múltiple de EE. "
        f"Créditos previos: {creditos_previos}, Totales: {creditos_totales}"
    )
    lote_id = f"ALTA-LOTE-{uuid.uuid4()}"

    with transaction.atomic():
        estudiante = _bloquear_estudiante(estudiante)
        reglas.validar_sin_solicitud_activa(estudiante, [m["nrc"] for m in materias])

        for materia in materias:
            Solicitud.objects.create(
                estudiante=estudiante,
                tipo_tramite=Solicitud.TipoTramite.ALTA,
                estado=Solicitud.Estado.PENDIENTE_ACADEMICA,
                materia_nrc=materia["nrc"],
                materia_nombre=materia["materia"],
                materia_maestro=materia["maestro"],
                status_inscripcion=vez_inscripcion[materia["nrc"]],
                lote_id=lote_id,
                ruta_horario=ruta_horario,
                observaciones=observaciones,
            )

    return lote_id


def crear_solicitudes_baja(estudiante, materias_horario, nrcs, motivo, ruta_horario):
    """
    Valida periodo, motivo, NRC ya solicitados, límite de bajas y mínimo de
    créditos (contando las bajas que siguen en trámite); si todo está bien
    crea una solicitud por materia, todas con el mismo lote. Regresa la
    lista de solicitudes creadas.
    """
    materias_por_nrc = {
        str(m.get("nrc")): m for m in materias_horario if m.get("materia")
    }
    nrcs = [nrc for nrc in dict.fromkeys(nrcs) if nrc in materias_por_nrc]

    if not nrcs:
        raise TramiteNoPermitidoError(
            "Debes seleccionar al menos una materia de tu horario para dar de baja."
        )
    if not motivo:
        raise TramiteNoPermitidoError("Debes escribir el motivo de la baja.")

    reglas.validar_tramite_abierto(reglas.TRAMITE_BAJAS, estudiante)
    lote_id = f"BAJA-LOTE-{uuid.uuid4()}"

    with transaction.atomic():
        estudiante = _bloquear_estudiante(estudiante)
        reglas.validar_sin_solicitud_activa(estudiante, nrcs)
        bajas_previas = reglas.bajas_comprometidas(estudiante)
        creditos_previos = reglas.creditos_disponibles_para_baja(
            estudiante, materias_horario
        )
        creditos_restantes = reglas.validar_bajas(estudiante, materias_horario, nrcs)

        observaciones = (
            "Baja múltiple de EE. "
            f"Bajas registradas o en trámite: {bajas_previas}. "
            f"Créditos previos: {creditos_previos}, Restantes: {creditos_restantes}"
        )

        return [
            Solicitud.objects.create(
                estudiante=estudiante,
                tipo_tramite=Solicitud.TipoTramite.BAJA,
                estado=Solicitud.Estado.PENDIENTE_ACADEMICA,
                materia_nrc=nrc,
                materia_nombre=materias_por_nrc[nrc]["materia"],
                materia_maestro=materias_por_nrc[nrc].get("maestro", ""),
                status_inscripcion=materias_por_nrc[nrc].get(
                    "status_inscripcion", PRIMERA_INSCRIPCION
                ),
                ruta_horario=ruta_horario,
                lote_id=lote_id,
                motivo_baja=motivo,
                observaciones=observaciones,
            )
            for nrc in nrcs
        ]


def crear_solicitud_constancia(estudiante, motivo, papeleta):
    """
    Crea la solicitud de constancia de estudios con su papeleta de pago.
    `papeleta` es el ComprobantePagoForm ya validado.

    Flujo: la secretaria de grupo la revisa y la elabora (pasa a
    "pendiente de firma") y la Secretaría Académica la firma y sella
    (queda "aceptada"). Solo se permite una constancia en trámite a la vez,
    para evitar solicitudes (y pagos) duplicados por un doble clic o un
    reenvío del formulario.
    Regresa la solicitud creada.
    """
    with transaction.atomic():
        estudiante = _bloquear_estudiante(estudiante)

        if Solicitud.objects.filter(
            estudiante=estudiante,
            tipo_tramite=Solicitud.TipoTramite.CONSTANCIA,
            estado__in=reglas.ESTADOS_EN_TRAMITE,
        ).exists():
            raise TramiteNoPermitidoError(
                "Ya tienes una solicitud de constancia de estudios en revisión. "
                "Espera a que se resuelva antes de solicitar otra."
            )

        solicitud = Solicitud.objects.create(
            estudiante=estudiante,
            tipo_tramite=Solicitud.TipoTramite.CONSTANCIA,
            estado=Solicitud.Estado.PENDIENTE,
            motivo_constancia=motivo,
        )

        archivo = papeleta.cleaned_data["archivo"]
        archivo.seek(0)
        comprobante = ComprobantePago(
            solicitud=solicitud,
            folio=papeleta.cleaned_data["folio"],
        )
        comprobante.archivo.save(archivo.name, archivo, save=False)
        comprobante.save()

    return solicitud


def crear_solicitud_justificante(estudiante, form):
    """
    Crea la solicitud de justificante médico con su comprobante. `form` es
    el SolicitudJustificanteForm ya validado. Queda pendiente de revisión
    de la Secretaría Académica, que autoriza los días; después pasa a la
    secretaria de grupo, que elabora el justificante.

    No se permite otra solicitud en trámite que se empalme con los mismos
    días, para evitar justificantes duplicados.
    Regresa la solicitud creada.
    """
    inicio = form.cleaned_data["fecha_inicio"]
    fin = form.cleaned_data["fecha_fin"]

    with transaction.atomic():
        estudiante = _bloquear_estudiante(estudiante)

        if Solicitud.objects.filter(
            estudiante=estudiante,
            tipo_tramite=Solicitud.TipoTramite.JUSTIFICANTE,
            estado__in=reglas.ESTADOS_EN_TRAMITE,
            fecha_inicio_inasistencia__lte=fin,
            fecha_fin_inasistencia__gte=inicio,
        ).exists():
            raise TramiteNoPermitidoError(
                "Ya tienes un justificante en revisión que incluye algunos de "
                "esos días. Espera a que se resuelva."
            )

        solicitud = Solicitud(
            estudiante=estudiante,
            tipo_tramite=Solicitud.TipoTramite.JUSTIFICANTE,
            estado=Solicitud.Estado.PENDIENTE_ACADEMICA,
            fecha_inicio_inasistencia=inicio,
            fecha_fin_inasistencia=fin,
            motivo_justificante=form.cleaned_data["motivo"],
        )
        archivo = form.cleaned_data["documento"]
        archivo.seek(0)
        solicitud.documento_medico.save(archivo.name, archivo, save=False)
        solicitud.save()

    return solicitud
