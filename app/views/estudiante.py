import mimetypes
import os

from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, render
from app.models.solicitud import ComprobantePago, EstadoSolicitud, Solicitud
from app.controllers.decoradores import rol_requerido
from app.models.usuario import User


# Mis solicitudes muestra lo que sigue en trámite; el historial, lo que ya
# terminó (aceptada o rechazada).
ESTADOS_EN_TRAMITE_ALUMNO = (
    EstadoSolicitud.PENDIENTE_ACADEMICA,
    EstadoSolicitud.PENDIENTE,
    EstadoSolicitud.PENDIENTE_FIRMA,
)
ESTADOS_HISTORIAL_ALUMNO = (
    EstadoSolicitud.ACEPTADA,
    EstadoSolicitud.RECHAZADA,
    EstadoSolicitud.RECHAZADA_ACADEMICA,
)


def _lista_solicitudes_alumno(request, estados, es_historial):
    """Tabla de solicitudes del alumno con búsqueda, filtros y paginación."""
    solicitudes = (
        Solicitud.objects.filter(estudiante__user=request.user, estado__in=estados)
        .select_related("estudiante")
        .prefetch_related("comprobantes")
        .order_by("-fecha_solicitud")
    )

    busqueda = request.GET.get("busqueda", "").strip()
    tipo = request.GET.get("tipo", "").strip()
    estado = request.GET.get("estado", "").strip()

    if busqueda:
        q_filter = Q(materia_nombre__icontains=busqueda)
        busqueda_limpia = busqueda.lstrip("Ss").lstrip("0")
        if busqueda_limpia.isdigit():
            q_filter |= Q(id=int(busqueda_limpia))
        solicitudes = solicitudes.filter(q_filter)

    if tipo:
        solicitudes = solicitudes.filter(tipo_tramite=tipo)

    if estado:
        solicitudes = solicitudes.filter(estado=estado)

    paginator = Paginator(solicitudes, 10)
    page_number = request.GET.get("page")
    solicitudes_paginadas = paginator.get_page(page_number)

    solicitudes_data = [sol.a_dict() for sol in solicitudes_paginadas]

    return render(
        request,
        "estudiante/mis_solicitudes.html",
        {
            "solicitudes": solicitudes_paginadas,
            "solicitudes_json": solicitudes_data,
            "busqueda": busqueda,
            "tipo": tipo,
            "estado": estado,
            "es_historial": es_historial,
            "opciones_estado": [
                (valor, EstadoSolicitud(valor).label) for valor in estados
            ],
        },
    )


@rol_requerido(User.Rol.ALUMNO)
def mis_solicitudes(request):
    return _lista_solicitudes_alumno(request, ESTADOS_EN_TRAMITE_ALUMNO, False)


@rol_requerido(User.Rol.ALUMNO)
def historial_solicitudes(request):
    return _lista_solicitudes_alumno(request, ESTADOS_HISTORIAL_ALUMNO, True)


def _solicitudes_visibles(usuario):
    """
    Solicitudes que el usuario tiene permitido ver:
    - alumno: solo las suyas.
    - secretaria de grupo: las de los alumnos que tiene asignados.
    - administrador (Secretaría Académica): todas.
    """
    solicitudes = Solicitud.objects.all()
    if usuario.rol == User.Rol.ALUMNO:
        return solicitudes.filter(estudiante__user=usuario)
    if usuario.rol == User.Rol.SECRETARIA_GRUPO:
        return solicitudes.filter(estudiante__secretaria__user=usuario)
    return solicitudes


@rol_requerido(User.Rol.ALUMNO, User.Rol.SECRETARIA_GRUPO, User.Rol.ADMINISTRADOR)
def ver_horario_pdf(request, solicitud_id):
    """
    Muestra el horario (PDF) que el alumno adjuntó a una solicitud.

    El archivo se busca por el id de la solicitud, nunca por un nombre o
    ruta enviados desde el navegador, así que solo se puede abrir el
    horario de una solicitud que el usuario tiene permitido ver.
    """
    solicitud = get_object_or_404(_solicitudes_visibles(request.user), pk=solicitud_id)

    if not solicitud.ruta_horario:
        raise Http404("Esta solicitud no tiene un horario adjunto.")

    # En la BD se guardó la ruta completa de la máquina donde se subió
    # (puede ser Windows). Solo se usa el nombre del archivo y se busca en
    # la carpeta de horarios configurada en este servidor.
    nombre_archivo = os.path.basename(
        solicitud.ruta_horario.replace("\\", "/")
    )
    ruta_final = os.path.join(settings.CARPETA_PAPELES_HORARIOS, nombre_archivo)

    if not nombre_archivo or not os.path.isfile(ruta_final):
        raise Http404("El horario de esta solicitud ya no está disponible.")

    return FileResponse(
        open(ruta_final, "rb"),
        content_type="application/pdf",
        as_attachment=False,
        filename=nombre_archivo,
    )


@rol_requerido(User.Rol.ALUMNO, User.Rol.SECRETARIA_GRUPO, User.Rol.ADMINISTRADOR)
def ver_comprobante_pdf(request):
    comprobante_id = request.GET.get("id", "").strip()

    if not comprobante_id.isdigit():
        raise Http404("No se especificó un comprobante válido.")

    comprobante = ComprobantePago.objects.filter(
        id=comprobante_id,
        solicitud__in=_solicitudes_visibles(request.user),
    ).first()

    if not comprobante:
        raise Http404("El comprobante no existe o no tienes permiso para verlo.")

    try:
        with comprobante.archivo.open("rb") as f:
            contenido = f.read()
    except Exception:
        raise Http404("Error al leer el archivo.")

    nombre_archivo = os.path.basename(comprobante.archivo.name)
    content_type, _ = mimetypes.guess_type(nombre_archivo)

    response = HttpResponse(
        contenido, content_type=content_type or "application/octet-stream"
    )
    response["Content-Disposition"] = f'inline; filename="{nombre_archivo}"'
    return response


@rol_requerido(User.Rol.ALUMNO, User.Rol.SECRETARIA_GRUPO, User.Rol.ADMINISTRADOR)
def ver_documento_medico(request, solicitud_id):
    """
    Muestra el comprobante médico de un justificante. Se busca por el id de
    la solicitud y solo entre las que el usuario tiene permitido ver.
    """
    solicitud = get_object_or_404(_solicitudes_visibles(request.user), pk=solicitud_id)
    if not solicitud.documento_medico:
        raise Http404("Esta solicitud no tiene un comprobante médico adjunto.")

    try:
        with solicitud.documento_medico.open("rb") as archivo:
            contenido = archivo.read()
    except Exception:
        raise Http404("El comprobante médico ya no está disponible.")

    nombre_archivo = os.path.basename(solicitud.documento_medico.name)
    content_type, _ = mimetypes.guess_type(nombre_archivo)
    response = HttpResponse(
        contenido, content_type=content_type or "application/octet-stream"
    )
    response["Content-Disposition"] = f'inline; filename="{nombre_archivo}"'
    return response
