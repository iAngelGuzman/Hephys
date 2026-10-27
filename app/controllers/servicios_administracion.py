from django.db import transaction
from django.utils import timezone

from app.models.solicitud import (
    CalendarioMatricula,
    ExperienciaEducativa,
    ExperienciaEducativaOferta,
    PeriodoTramite,
)

from app.views.forms.administrador import PeriodoTramiteForm
from .constantes_administracion import CARRERA_CODES
from .lectores_pdf_administracion import extraer_ofertas_pdf, extraer_registros_calendario
from app.models.administrador import Carrera, HorarioExamen


def obtener_periodos_tramite():
    """
    Obtiene los periodos generales de altas y bajas, creándolos con fechas
    por defecto (ahora-ahora) si todavía no existen.
    """
    periodo_altas, _ = PeriodoTramite.objects.get_or_create(
        tipo_tramite="altas",
        defaults={"fecha_apertura": timezone.now(), "fecha_cierre": timezone.now()},
    )
    periodo_bajas, _ = PeriodoTramite.objects.get_or_create(
        tipo_tramite="bajas",
        defaults={"fecha_apertura": timezone.now(), "fecha_cierre": timezone.now()},
    )
    return periodo_altas, periodo_bajas


def guardar_periodo_tramite(tipo, instancia, datos_post):
    """
    Valida y, si es válido, guarda el formulario del periodo general
    (altas o bajas). Devuelve el form para que la vista decida qué hacer
    (redirigir si es válido, o volver a mostrarlo con errores si no).
    """
    form = PeriodoTramiteForm(datos_post, instance=instancia, prefix=tipo)
    if form.is_valid():
        form.save()
    return form


def eliminar_calendario_matricula(calendario_id):
    """
    Elimina una restricción de calendario de matrícula por su id. Regresa
    True si existía. Un id que no es número se trata como inexistente.
    """
    if not str(calendario_id).isdigit():
        return False
    eliminados, _ = CalendarioMatricula.objects.filter(id=calendario_id).delete()
    return eliminados > 0


def procesar_pdf_oferta_educativa(archivo_pdf):
    """
    Importa el PDF de oferta educativa: crea/actualiza ExperienciaEducativa
    y ExperienciaEducativaOferta. Regresa los textos de carrera del PDF que
    no se reconocieron, para avisarle al admin.
    """
    ofertas, carreras_no_reconocidas = extraer_ofertas_pdf(archivo_pdf)

    with transaction.atomic():
        for oferta in ofertas:
            ee_base = ExperienciaEducativa.objects.filter(
                nombre=oferta["nombre_ee"]
            ).first()
            if not ee_base:
                ee_base = ExperienciaEducativa.objects.create(
                    nombre=oferta["nombre_ee"],
                    carrera=oferta["carrera"],
                    creditos=0,
                    tiene_prerequisito=False,
                )

            ExperienciaEducativaOferta.objects.update_or_create(
                nrc=oferta["nrc"],
                defaults={
                    "experiencia_educativa": ee_base,
                    "docente": oferta["docente"],
                    "horarios": oferta["horarios"],
                    "bloque_seccion": oferta["bloque_seccion"],
                },
            )

    return {"carreras_no_reconocidas": carreras_no_reconocidas}


def procesar_pdf_horarios(archivo_pdf, carrera_code=None):

    registros, carrera_nombre_pdf, periodo = extraer_registros_calendario(archivo_pdf)

    carrera = None
    if carrera_code:
        nombre_oficial = CARRERA_CODES.get(
            carrera_code, carrera_nombre_pdf or carrera_code
        )
        carrera, _ = Carrera.objects.get_or_create(
            clave=carrera_code, defaults={"nombre": nombre_oficial}
        )
    elif carrera_nombre_pdf:
        carrera, _ = Carrera.objects.get_or_create(nombre=carrera_nombre_pdf)

    creados = 0
    actualizados = 0
    nrcs_procesados = set()

    tipos_examen = (
        ("ORD", "fecha_ordinario", "acta_ordinario"),
        ("EXT", "fecha_extraordinario", "acta_extraordinario"),
        ("TIT", "fecha_titulo", "acta_titulo"),
    )

    with transaction.atomic():
        ids_vigentes = []
        for registro in registros:
            nrcs_procesados.add(registro["nrc"])
            for tipo, campo_fecha, campo_acta in tipos_examen:
                fecha = registro[campo_fecha]
                if not fecha:
                    continue

                horario, fue_creado = HorarioExamen.objects.update_or_create(
                    carrera=carrera,
                    nrc=registro["nrc"],
                    tipo_examen=tipo,
                    periodo=periodo,
                    defaults={
                        "ee_nombre": registro["ee_nombre"] or "",
                        "profesor": registro["profesor"],
                        "bloque_seccion": registro["bloque_seccion"],
                        "salon": registro["salon"],
                        "hora": registro["hora"],
                        "fecha_examen": fecha,
                        "fecha_entrega_acta": registro.get(campo_acta),
                    },
                )
                ids_vigentes.append(horario.pk)
                if fue_creado:
                    creados += 1
                else:
                    actualizados += 1

        # Subir un PDF nuevo REEMPLAZA el calendario de ESA carrera: se quitan
        # los exámenes que ya no vienen en el PDF. Las demás carreras no se tocan.
        eliminados, _ = (
            HorarioExamen.objects.filter(carrera=carrera)
            .exclude(pk__in=ids_vigentes)
            .delete()
        )

    return {
        "carrera": carrera.nombre if carrera else carrera_nombre_pdf,
        "periodo": periodo,
        "total_nrcs": len(nrcs_procesados),
        "creados": creados,
        "actualizados": actualizados,
        "eliminados": eliminados,
    }


TIPO_EXAMEN_SOLICITUD_A_CODIGO = {
    "extraordinario": "EXT",
    "suficiencia": "TIT",
}


def obtener_horarios_examen_vigentes(tipo_examen_solicitud, carrera_nombre=None):

    codigo = TIPO_EXAMEN_SOLICITUD_A_CODIGO.get(tipo_examen_solicitud)
    if not codigo:
        return {}

    consulta = HorarioExamen.objects.filter(
        tipo_examen=codigo, fecha_examen__gte=timezone.localdate()
    )
    if carrera_nombre:
        consulta = consulta.filter(carrera__nombre=carrera_nombre)

    disponibles = {}
    for horario in consulta:
        actual = disponibles.get(horario.nrc)
        if actual is None or horario.fecha_examen < actual.fecha_examen:
            disponibles[horario.nrc] = horario
    return disponibles
