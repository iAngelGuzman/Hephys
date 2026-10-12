import json
import logging

from django.db import transaction
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from apps.estudiante.models import Estudiante
from apps.secretaria.models import Secretaria
from apps.solicitud.constants import MAXIMO_BAJAS
from apps.solicitud.models import ExperienciaEducativaOferta, Solicitud
from apps.usuario.decorators import rol_requerido
from apps.usuario.models import User

logger = logging.getLogger(__name__)


def _perfil_secretaria(request):
    """
    Perfil de la secretaria conectada. Si su usuario tiene el rol pero no
    tiene perfil (p. ej. se creó desde /admin), responde 404 en vez de
    tronar con un error 500.
    """
    return get_object_or_404(Secretaria, user=request.user)


@rol_requerido(User.Rol.SECRETARIA_GRUPO)
def dashboard(request):
    secretaria_perfil = _perfil_secretaria(request)

    solicitudes = (
        Solicitud.objects.select_related("estudiante")
        .prefetch_related("comprobantes")
        .filter(
            estudiante__secretaria=secretaria_perfil, estado=Solicitud.Estado.PENDIENTE
        )
    )

    datos_json = [sol.a_dict() for sol in solicitudes]

    return render(
        request,
        "secretaria/dashboard.html",
        {"solicitudes": solicitudes, "solicitudes_json": datos_json},
    )


class SolicitudNoAprobable(Exception):
    """
    Se lanza DENTRO de la transacción cuando la solicitud no se puede
    aprobar. Al salir de "with transaction.atomic()" con una excepción,
    Django deshace todo lo que se haya guardado (por ejemplo, un cupo ya
    descontado de otro NRC de la misma solicitud).
    """

    def __init__(self, mensaje, status=400):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.status = status


def _descontar_cupos(solicitud):
    """
    Descuenta 1 cupo por cada NRC de una solicitud de alta.

    Es el ÚNICO lugar del sistema donde se descuenta cupo: se hace cuando
    la secretaria de grupo da la aprobación final. Cada oferta se bloquea
    con select_for_update para que dos aprobaciones al mismo tiempo no
    tomen el mismo último lugar.
    """
    nrcs = [nrc.strip() for nrc in solicitud.materia_nrc.split(",") if nrc.strip()]
    if not nrcs:
        raise SolicitudNoAprobable(
            "La solicitud no cuenta con un NRC de materia asociado."
        )

    for nrc in nrcs:
        oferta = (
            ExperienciaEducativaOferta.objects.select_for_update()
            .filter(nrc=nrc)
            .first()
        )
        if oferta is None:
            raise SolicitudNoAprobable(
                f"La oferta con NRC {nrc} no existe en la base de datos.", status=404
            )
        if oferta.cupo <= 0:
            raise SolicitudNoAprobable(
                f"No hay cupos disponibles para la Experiencia Educativa con NRC {nrc}."
            )
        oferta.cupo -= 1
        oferta.save(update_fields=["cupo"])


def _registrar_baja(solicitud):
    """
    Suma 1 a las bajas registradas del alumno al aprobar una baja. Vuelve a
    revisar el límite por si el número de bajas cambió mientras la
    solicitud estaba en trámite.
    """
    estudiante = Estudiante.objects.select_for_update().get(pk=solicitud.estudiante_id)
    if (estudiante.numero_bajas or 0) >= MAXIMO_BAJAS:
        raise SolicitudNoAprobable(
            f"El alumno ya tiene {MAXIMO_BAJAS} bajas registradas, que es el máximo permitido."
        )
    estudiante.numero_bajas = (estudiante.numero_bajas or 0) + 1
    estudiante.save(update_fields=["numero_bajas"])


@rol_requerido(User.Rol.SECRETARIA_GRUPO)
@require_POST
def aprobar_solicitud(request, solicitud_id):
    secretaria_perfil = _perfil_secretaria(request)

    try:
        with transaction.atomic():
            solicitud = get_object_or_404(
                Solicitud.objects.select_for_update(),
                id=solicitud_id,
                estudiante__secretaria=secretaria_perfil,
            )

            if solicitud.estado != Solicitud.Estado.PENDIENTE:
                raise SolicitudNoAprobable(
                    "Esta solicitud ya fue procesada anteriormente.", status=409
                )

            if solicitud.tipo_tramite == Solicitud.TipoTramite.ALTA:
                _descontar_cupos(solicitud)

            if solicitud.tipo_tramite == Solicitud.TipoTramite.BAJA:
                _registrar_baja(solicitud)

            campos = ["estado"]
            if solicitud.tipo_tramite == Solicitud.TipoTramite.CONSTANCIA:
                solicitud.estado = Solicitud.Estado.PENDIENTE_FIRMA
                solicitud.observaciones = (
                    solicitud.observaciones or ""
                ) + " | Revisada y elaborada por la secretaria de grupo."
                campos.append("observaciones")
            else:
                solicitud.estado = Solicitud.Estado.ACEPTADA
            solicitud.save(update_fields=campos)

    except SolicitudNoAprobable as error:
        return JsonResponse(
            {"success": False, "error": error.mensaje}, status=error.status
        )
    except Http404:
        raise
    except Exception:
        logger.exception("Error inesperado al aprobar la solicitud %s", solicitud_id)
        return JsonResponse(
            {
                "success": False,
                "error": "Ocurrió un error inesperado al aprobar la solicitud. Intenta de nuevo.",
            },
            status=500,
        )

    return JsonResponse(
        {"success": True, "nuevo_estado": solicitud.get_estado_display()}
    )


@rol_requerido(User.Rol.SECRETARIA_GRUPO)
@require_POST
def rechazar_solicitud(request, solicitud_id):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        data = None

    if not isinstance(data, dict):
        return JsonResponse(
            {"success": False, "error": "La solicitud enviada no es válida."},
            status=400,
        )

    motivo = str(data.get("motivo", "")).strip()
    if not motivo:
        return JsonResponse(
            {"success": False, "error": "El motivo es obligatorio."}, status=400
        )

    secretaria_perfil = _perfil_secretaria(request)

    try:
        with transaction.atomic():
            solicitud = get_object_or_404(
                Solicitud.objects.select_for_update(),
                id=solicitud_id,
                estudiante__secretaria=secretaria_perfil,
            )

            if solicitud.estado != Solicitud.Estado.PENDIENTE:
                raise SolicitudNoAprobable(
                    "Esta solicitud ya fue procesada anteriormente.", status=409
                )

            solicitud.estado = Solicitud.Estado.RECHAZADA
            solicitud.observaciones = motivo
            solicitud.save(update_fields=["estado", "observaciones"])

    except SolicitudNoAprobable as error:
        return JsonResponse(
            {"success": False, "error": error.mensaje}, status=error.status
        )
    except Http404:
        raise
    except Exception:
        logger.exception("Error inesperado al rechazar la solicitud %s", solicitud_id)
        return JsonResponse(
            {
                "success": False,
                "error": "Ocurrió un error inesperado al rechazar la solicitud. Intenta de nuevo.",
            },
            status=500,
        )

    return JsonResponse({"success": True})


@rol_requerido(User.Rol.SECRETARIA_GRUPO)
def historial_solicitudes(request):
    secretaria_perfil = _perfil_secretaria(request)
    solicitudes = (
        Solicitud.objects.select_related("estudiante")
        .prefetch_related("comprobantes")
        .filter(estudiante__secretaria=secretaria_perfil)
        .filter(
            Q(estado__in=[Solicitud.Estado.ACEPTADA, Solicitud.Estado.RECHAZADA])
            | Q(
                tipo_tramite=Solicitud.TipoTramite.CONSTANCIA,
                estado__in=[
                    Solicitud.Estado.PENDIENTE_FIRMA,
                    Solicitud.Estado.RECHAZADA_ACADEMICA,
                ],
            )
        )
        .order_by("-fecha_solicitud")
    )

    datos_json = [sol.a_dict() for sol in solicitudes]

    return render(
        request,
        "secretaria/historial_solicitudes.html",
        {"solicitudes": solicitudes, "solicitudes_json": datos_json},
    )
