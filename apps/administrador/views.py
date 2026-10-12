import json
import logging
from datetime import date

from django.db import transaction
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET, require_POST
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from apps.administrador.models import HorarioExamen
from apps.administrador.constants import CARRERA_CODES, CUPO_MAXIMO
from apps.estudiante.models import Estudiante
from apps.secretaria.models import Secretaria
from apps.solicitud.models import (
    CalendarioMatricula,
    ExperienciaEducativaOferta,
    Solicitud,
)
from apps.usuario.decorators import rol_requerido
from apps.usuario.models import User
from apps.administrador.forms import (
    CalendarioMatriculaForm,
    CrearSecretariaForm,
    EditarSecretariaForm,
    PeriodoTramiteForm,
    SubirCalendarioExamenesForm,
    SubirOfertaPDFForm,
    primer_error,
)
from apps.administrador.services import (
    eliminar_calendario_matricula,
    guardar_periodo_tramite,
    obtener_periodos_tramite,
    procesar_pdf_horarios,
    procesar_pdf_oferta_educativa,
)
from apps.administrador.exceptions import ErrorProcesandoCalendarioExamenes

logger = logging.getLogger(__name__)


@rol_requerido(User.Rol.ADMINISTRADOR)
def dashboard(request):
    return render(request, "administrador/dashboard_administrador.html")


@rol_requerido(User.Rol.ADMINISTRADOR)
def configurar_altas_bajas(request):
    periodo_altas, periodo_bajas = obtener_periodos_tramite()
    periodos = {"altas": periodo_altas, "bajas": periodo_bajas}

    form_altas = PeriodoTramiteForm(instance=periodo_altas, prefix="altas")
    form_bajas = PeriodoTramiteForm(instance=periodo_bajas, prefix="bajas")
    form_calendario = CalendarioMatriculaForm(periodo=periodo_altas)

    if request.method == "POST":
        tipo = request.POST.get("tipo")

        if tipo in periodos:
            form = guardar_periodo_tramite(tipo, periodos[tipo], request.POST)
            if form.is_valid():
                messages.success(
                    request, f"Periodo de {tipo} actualizado correctamente."
                )
                return redirect("administrador:configurar_altas_bajas")

            if tipo == "altas":
                form_altas = form
            else:
                form_bajas = form

        elif tipo == "calendario_matricula":
            form_calendario = CalendarioMatriculaForm(
                request.POST, periodo=periodo_altas
            )
            if form_calendario.is_valid():
                calendario = form_calendario.save(commit=False)
                calendario.tipo_tramite = "altas"
                calendario.save()
                messages.success(
                    request, "Fechas asignadas correctamente a la matrícula."
                )
                return redirect("administrador:configurar_altas_bajas")

        elif tipo == "eliminar_calendario":
            if eliminar_calendario_matricula(request.POST.get("calendario_id")):
                messages.success(
                    request, "Restricción de matrícula eliminada correctamente."
                )
            else:
                messages.error(request, "La restricción de matrícula ya no existe.")
            return redirect("administrador:configurar_altas_bajas")

    return render(
        request,
        "administrador/altas_bajas/administrar_altas_bajas.html",
        {
            "form_altas": form_altas,
            "form_bajas": form_bajas,
            "form_calendario": form_calendario,
            "calendarios_matriculas": CalendarioMatricula.objects.all(),
        },
    )


@rol_requerido(User.Rol.ADMINISTRADOR)
def subir_oferta_pdf(request):
    if request.method == "POST":
        form = SubirOfertaPDFForm(request.POST, request.FILES)
        if form.is_valid():
            archivo = form.cleaned_data["archivo_pdf"]

            try:
                resultado = procesar_pdf_oferta_educativa(archivo)
            except Exception:
                logger.exception(
                    "Error inesperado al procesar el PDF de oferta educativa"
                )
                messages.error(
                    request,
                    "Ocurrió un error inesperado al procesar el PDF. Verifica"
                    " que sea el archivo correcto e inténtalo de nuevo.",
                )
            else:
                carreras_no_reconocidas = resultado["carreras_no_reconocidas"]
                if carreras_no_reconocidas:
                    messages.warning(
                        request,
                        "La oferta se importó, pero no se reconoció el nombre"
                        " de carrera de este texto tal como aparece en el PDF: "
                        + ", ".join(sorted(carreras_no_reconocidas))
                        + ". Verifica que coincida con el catálogo de carreras"
                        " para que los alumnos vean estas materias al hacer"
                        " una alta.",
                    )
                messages.success(
                    request, "¡La oferta educativa se ha importado correctamente!"
                )
                return redirect("administrador:configurar_altas_bajas")
        else:
            messages.error(request, primer_error(form))
    else:
        form = SubirOfertaPDFForm()

    return render(
        request, "administrador/altas_bajas/subir_oferta.html", {"form": form}
    )


@rol_requerido(User.Rol.ADMINISTRADOR)
def gestion_cupos(request):
    if request.method == "POST":
        nrc = request.POST.get("nrc")
        nuevo_cupo = request.POST.get("cupo")

        if nrc and nuevo_cupo is not None:
            try:
                valor_cupo = int(nuevo_cupo)

                if valor_cupo > CUPO_MAXIMO:
                    messages.error(
                        request,
                        "El cupo máximo permitido para una experiencia educativa "
                        f"es de {CUPO_MAXIMO}.",
                    )
                elif valor_cupo < 0:
                    messages.error(request, "El cupo no puede ser un número negativo.")
                else:
                    oferta = ExperienciaEducativaOferta.objects.get(nrc=nrc)
                    oferta.cupo = valor_cupo
                    oferta.save()
                    messages.success(
                        request, f"Cupo actualizado exitosamente para el NRC {nrc}."
                    )
            except ExperienciaEducativaOferta.DoesNotExist:
                messages.error(
                    request, "La experiencia educativa seleccionada no existe."
                )
            except ValueError:
                messages.error(
                    request, "El valor del cupo debe ser un número entero válido."
                )

        anterior = request.META.get("HTTP_REFERER", "")
        if url_has_allowed_host_and_scheme(
            anterior,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return redirect(anterior)
        return redirect("administrador:gestion_cupos")

    ofertas_list = ExperienciaEducativaOferta.objects.all().order_by("nrc")

    carrera_filtro = request.GET.get("carrera", "")
    if carrera_filtro:
        ofertas_list = ofertas_list.filter(
            Q(experiencia_educativa__carrera__icontains=carrera_filtro)
        )

    busqueda = request.GET.get("q", "")
    if busqueda:
        ofertas_list = ofertas_list.filter(
            Q(nrc__icontains=busqueda)
            | Q(experiencia_educativa__nombre__icontains=busqueda)
            | Q(docente__icontains=busqueda)
            | Q(experiencia_educativa__carrera__icontains=busqueda)
        )

    paginator = Paginator(ofertas_list, 15)
    page_number = request.GET.get("page")
    ofertas = paginator.get_page(page_number)

    return render(
        request,
        "administrador/altas_bajas/gestion_cupos.html",
        {
            "ofertas": ofertas,
            "carrera_seleccionada": carrera_filtro,
            "busqueda_seleccionada": busqueda,
            "carreras": Estudiante.ProgramaEducativo.choices,
            "cupo_maximo": CUPO_MAXIMO,
        },
    )


@rol_requerido(User.Rol.ADMINISTRADOR)
def configurar_examenes(request):
    if request.method == "POST":
        form = SubirCalendarioExamenesForm(request.POST, request.FILES)
        if not form.is_valid():
            messages.error(request, primer_error(form))
            return redirect("administrador:configurar_examenes")

        archivo = form.cleaned_data["archivo_horario"]
        carrera_code = form.cleaned_data["carrera_code"]

        try:
            resumen = procesar_pdf_horarios(archivo, carrera_code=carrera_code)
        except ErrorProcesandoCalendarioExamenes as exc:
            messages.error(request, exc.mensaje)
            return redirect("administrador:configurar_examenes")
        except (ValueError, KeyError):
            logger.warning(
                "Formato inesperado en el PDF de exámenes (%s)",
                carrera_code,
                exc_info=True,
            )
            messages.error(
                request,
                "El formato del PDF no coincide con la estructura esperada del calendario de exámenes.",
            )
            return redirect("administrador:configurar_examenes")
        except Exception:
            logger.exception(
                "Error inesperado al procesar el calendario de exámenes (%s)",
                carrera_code,
            )
            messages.error(
                request,
                "Ocurrió un error inesperado al procesar el PDF. Verifica que"
                " sea el calendario de exámenes correcto e inténtalo de nuevo.",
            )
            return redirect("administrador:configurar_examenes")

        eliminados = resumen["eliminados"]
        messages.success(
            request,
            f"Horario publicado para {carrera_code}: "
            f"{resumen['total_nrcs']} NRC procesados "
            f"({resumen['creados']} nuevos, {resumen['actualizados']} actualizados"
            + (f", {eliminados} quitados del horario anterior" if eliminados else "")
            + f") para el periodo {resumen['periodo']}.",
            extra_tags="horario_subido",
        )
        return redirect("administrador:configurar_examenes")

    carreras_con_horario = set(
        HorarioExamen.objects.filter(carrera__clave__isnull=False)
        .values_list("carrera__clave", flat=True)
        .distinct()
    )
    carreras = [
        {
            "codigo": codigo,
            "nombre": nombre,
            "tiene_horario": codigo in carreras_con_horario,
        }
        for codigo, nombre in CARRERA_CODES.items()
    ]

    return render(
        request,
        "administrador/examenes/administrar_examenes.html",
        {"carreras": carreras},
    )


@rol_requerido(User.Rol.ADMINISTRADOR)
def eliminar_horario_examenes(request):
    if request.method != "POST":
        return redirect("administrador:configurar_examenes")

    carrera_code = request.POST.get("carrera_code", "")
    nombre_carrera = CARRERA_CODES.get(carrera_code)

    if not nombre_carrera:
        messages.error(request, "Carrera no válida.")
        return redirect("administrador:configurar_examenes")

    eliminados, _ = HorarioExamen.objects.filter(carrera__clave=carrera_code).delete()

    if eliminados:
        messages.success(
            request,
            f"Se quitó el horario de exámenes de {carrera_code} "
            f"({eliminados} registros eliminados).",
        )
    else:
        messages.info(request, f"No había ningún horario cargado para {carrera_code}.")

    return redirect("administrador:configurar_examenes")


def _secretarias_de_grupo():
    """
    Usuarios que se administran desde "Control de usuarios". Las vistas
    solo pueden actuar sobre estos: nunca sobre alumnos ni sobre otros
    administradores (incluido el propio usuario conectado).
    """
    return User.objects.filter(rol=User.Rol.SECRETARIA_GRUPO)


@rol_requerido(User.Rol.ADMINISTRADOR)
def control_usuarios(request):
    usuarios_list = _secretarias_de_grupo().order_by(
        "first_name", "last_name", "username"
    )

    busqueda = request.GET.get("q", "").strip()
    if busqueda:
        usuarios_list = usuarios_list.filter(
            Q(username__icontains=busqueda)
            | Q(first_name__icontains=busqueda)
            | Q(last_name__icontains=busqueda)
            | Q(email__icontains=busqueda)
        )

    paginator = Paginator(usuarios_list, 15)
    usuarios = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "administrador/control_usuarios.html",
        {
            "usuarios": usuarios,
            "busqueda_seleccionada": busqueda,
        },
    )


@rol_requerido(User.Rol.ADMINISTRADOR)
@require_POST
def cambiar_estado_usuario(request, user_id):
    usuario = get_object_or_404(_secretarias_de_grupo(), id=user_id)
    usuario.is_active = not usuario.is_active
    usuario.save(update_fields=["is_active"])

    estado = "activado" if usuario.is_active else "desactivado"
    messages.success(
        request, f"El usuario '{usuario.username}' ha sido {estado} exitosamente."
    )
    return redirect("administrador:control_usuarios")


@rol_requerido(User.Rol.ADMINISTRADOR)
@require_POST
def crear_secretaria(request):
    form = CrearSecretariaForm(request.POST)

    if not form.is_valid():
        error_msg = primer_error(form)
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": False, "error": error_msg}, status=400)

        messages.error(request, error_msg)
        usuarios_list = _secretarias_de_grupo().order_by(
            "first_name", "last_name", "username"
        )
        paginator = Paginator(usuarios_list, 15)
        usuarios = paginator.get_page(request.GET.get("page"))

        return render(
            request,
            "administrador/control_usuarios.html",
            {
                "usuarios": usuarios,
                "formCrear": form,
                "abrir_modal_crear": True,
            },
        )

    try:
        with transaction.atomic():
            nuevo_usuario = form.save()
            Secretaria.objects.create(user=nuevo_usuario)
    except Exception:
        logger.exception(
            "Error al registrar la secretaria '%s'",
            form.cleaned_data.get("username", ""),
        )
        error_msg = (
            "Ocurrió un error inesperado al registrar el usuario. Intenta de nuevo."
        )
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": False, "error": error_msg}, status=500)

        messages.error(request, error_msg)
        return redirect("administrador:control_usuarios")

    mensaje_exito = f"La Secretaría de Grupo '{nuevo_usuario.username}' ha sido registrada exitosamente."

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        messages.success(request, mensaje_exito)
        return JsonResponse({"success": True})

    messages.success(request, mensaje_exito)
    return redirect("administrador:control_usuarios")


@rol_requerido(User.Rol.ADMINISTRADOR)
@require_POST
def editar_usuario(request, user_id):
    usuario = get_object_or_404(_secretarias_de_grupo(), id=user_id)
    form = EditarSecretariaForm(request.POST, instance=usuario)

    if not form.is_valid():
        error_msg = primer_error(form)
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": False, "error": error_msg}, status=400)
        messages.error(request, error_msg)
        return redirect("administrador:control_usuarios")

    try:
        usuario = form.save()
    except Exception:
        logger.exception("Error al actualizar el usuario %s", user_id)
        error_msg = (
            "Ocurrió un error inesperado al actualizar el usuario. Intenta de nuevo."
        )
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": False, "error": error_msg}, status=500)
        messages.error(request, error_msg)
        return redirect("administrador:control_usuarios")

    mensaje_exito = (
        f"El usuario '{usuario.username}' ha sido actualizado correctamente."
    )

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        messages.success(request, mensaje_exito)
        return JsonResponse({"success": True})

    messages.success(request, mensaje_exito)
    return redirect("administrador:control_usuarios")


TRAMITES_REVISION_ACADEMICA = [
    Solicitud.TipoTramite.ALTA,
    Solicitud.TipoTramite.BAJA,
    Solicitud.TipoTramite.JUSTIFICANTE,
]
_PENDIENTES_ACADEMICA = Q(
    estado=Solicitud.Estado.PENDIENTE_ACADEMICA,
    tipo_tramite__in=TRAMITES_REVISION_ACADEMICA,
) | Q(
    estado=Solicitud.Estado.PENDIENTE_FIRMA,
    tipo_tramite=Solicitud.TipoTramite.CONSTANCIA,
)


def _pendiente_con_academica(solicitud):
    return (
        solicitud.estado == Solicitud.Estado.PENDIENTE_ACADEMICA
        and solicitud.tipo_tramite in TRAMITES_REVISION_ACADEMICA
    ) or (
        solicitud.estado == Solicitud.Estado.PENDIENTE_FIRMA
        and solicitud.tipo_tramite == Solicitud.TipoTramite.CONSTANCIA
    )


@rol_requerido(User.Rol.ADMINISTRADOR)
@require_GET
def solicitudes_pendientes(request):
    pendientes = (
        Solicitud.objects.filter(_PENDIENTES_ACADEMICA)
        .select_related("estudiante")
        .prefetch_related("comprobantes")
        .order_by("fecha_solicitud")
    )

    solicitudes_list = [sol.a_dict() for sol in pendientes]

    contexto = {"solicitudes": pendientes, "solicitudes_json": solicitudes_list}

    return render(request, "administrador/solicitudes_pendientes.html", contexto)


def _nrcs_sin_cupo(solicitud):
    """
    Revisa (sin descontar nada) que cada NRC de una solicitud de alta
    exista y tenga cupo. Regresa un mensaje de error, o None si todo está
    bien.

    El cupo NO se descuenta aquí: se descuenta una sola vez, cuando la
    secretaria de grupo da la aprobación final (apps/secretaria/views.py,
    _descontar_cupos). Así, si la secretaria rechaza, no se pierde el lugar.
    """
    nrcs = [nrc.strip() for nrc in solicitud.materia_nrc.split(",") if nrc.strip()]
    if not nrcs:
        return "La solicitud no cuenta con un NRC de materia asociado."

    for nrc in nrcs:
        oferta = ExperienciaEducativaOferta.objects.filter(nrc=nrc).first()
        if oferta is None:
            return f"La oferta con NRC {nrc} no existe en la base de datos."
        if oferta.cupo <= 0:
            return (
                f"No hay cupos disponibles para la Experiencia Educativa con NRC {nrc}."
            )
    return None


def _dias_autorizados(request, solicitud):
    """
    Lee del cuerpo JSON los días que autoriza la Secretaría Académica para
    un justificante. Deben estar dentro de los días que pidió el alumno.
    Regresa (inicio, fin, None) o (None, None, mensaje_de_error).
    """
    try:
        datos = json.loads(request.body or b"{}")
        inicio = date.fromisoformat(str(datos.get("fecha_inicio_autorizada", "")))
        fin = date.fromisoformat(str(datos.get("fecha_fin_autorizada", "")))
    except (
        json.JSONDecodeError,
        UnicodeDecodeError,
        TypeError,
        ValueError,
        AttributeError,
    ):
        return None, None, "Indica los días que autorizas para el justificante."

    if inicio > fin:
        return (
            None,
            None,
            "El inicio de los días autorizados no puede ser posterior al fin.",
        )
    if (
        inicio < solicitud.fecha_inicio_inasistencia
        or fin > solicitud.fecha_fin_inasistencia
    ):
        return (
            None,
            None,
            (
                "Los días autorizados deben estar dentro de los días que solicitó el alumno."
            ),
        )
    return inicio, fin, None


@rol_requerido(User.Rol.ADMINISTRADOR)
@require_POST
def aprobar_solicitud(request, pk):
    try:
        with transaction.atomic():
            solicitud = get_object_or_404(Solicitud.objects.select_for_update(), id=pk)

            if not _pendiente_con_academica(solicitud):
                return JsonResponse(
                    {
                        "success": False,
                        "error": "Esta solicitud ya fue procesada anteriormente.",
                    },
                    status=409,
                )

            if solicitud.tipo_tramite == Solicitud.TipoTramite.CONSTANCIA:
                solicitud.estado = Solicitud.Estado.ACEPTADA
                solicitud.observaciones = (
                    solicitud.observaciones or ""
                ) + " | Firmada y sellada por Secretaría Académica."
                solicitud.save(update_fields=["estado", "observaciones"])
                return JsonResponse(
                    {"success": True, "nuevo_estado": solicitud.get_estado_display()}
                )

            if solicitud.tipo_tramite == Solicitud.TipoTramite.ALTA:
                error_cupo = _nrcs_sin_cupo(solicitud)
                if error_cupo:
                    return JsonResponse(
                        {"success": False, "error": error_cupo}, status=400
                    )

            campos = ["estado", "observaciones"]
            if solicitud.tipo_tramite == Solicitud.TipoTramite.JUSTIFICANTE:
                inicio, fin, error_dias = _dias_autorizados(request, solicitud)
                if error_dias:
                    return JsonResponse(
                        {"success": False, "error": error_dias}, status=400
                    )
                solicitud.fecha_inicio_autorizada = inicio
                solicitud.fecha_fin_autorizada = fin
                campos += ["fecha_inicio_autorizada", "fecha_fin_autorizada"]

            solicitud.estado = Solicitud.Estado.PENDIENTE
            solicitud.observaciones = (
                solicitud.observaciones or ""
            ) + " | Aprobado por Secretaría Académica."
            solicitud.save(update_fields=campos)

    except Http404:
        raise
    except Exception:
        logger.exception("Error inesperado al aprobar la solicitud académica %s", pk)
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


@rol_requerido(User.Rol.ADMINISTRADOR)
@require_POST
def rechazar_solicitud(request, pk):
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

    try:
        with transaction.atomic():
            solicitud = get_object_or_404(Solicitud.objects.select_for_update(), id=pk)

            if not _pendiente_con_academica(solicitud):
                return JsonResponse(
                    {
                        "success": False,
                        "error": "Esta solicitud ya fue procesada anteriormente.",
                    },
                    status=409,
                )

            solicitud.estado = Solicitud.Estado.RECHAZADA_ACADEMICA
            solicitud.observaciones = (
                solicitud.observaciones or ""
            ) + f" | Rechazado por Secretaría Académica: {motivo}"
            solicitud.save(update_fields=["estado", "observaciones"])

    except Http404:
        raise
    except Exception:
        logger.exception("Error inesperado al rechazar la solicitud académica %s", pk)
        return JsonResponse(
            {
                "success": False,
                "error": "Ocurrió un error inesperado al rechazar la solicitud. Intenta de nuevo.",
            },
            status=500,
        )

    return JsonResponse({"success": True})


@rol_requerido(User.Rol.ADMINISTRADOR)
def historial_solicitudes(request):
    historial_qs = (
        Solicitud.objects.filter(
            (
                Q(tipo_tramite__in=TRAMITES_REVISION_ACADEMICA)
                & ~Q(estado=Solicitud.Estado.PENDIENTE_ACADEMICA)
            )
            | Q(
                tipo_tramite=Solicitud.TipoTramite.CONSTANCIA,
                estado__in=[
                    Solicitud.Estado.ACEPTADA,
                    Solicitud.Estado.RECHAZADA_ACADEMICA,
                ],
            )
        )
        .select_related("estudiante")
        .prefetch_related("comprobantes")
        .order_by("-fecha_solicitud")
    )

    datos_historial = [solicitud.a_dict() for solicitud in historial_qs]

    contexto = {
        "historial": historial_qs,
        "historial_json": datos_historial,
    }

    return render(request, "administrador/historial_solicitudes_admin.html", contexto)
