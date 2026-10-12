"""
Reglas de negocio de los trámites de altas, bajas y justificantes.

Todo lo que decide si un alumno PUEDE hacer un trámite vive aquí y se valida
en el servidor. El JavaScript de las plantillas solo repite estas reglas para
avisar antes de enviar; si alguien lo salta, estas funciones siguen
protegiendo el sistema.

Nada de este módulo guarda en la base de datos: solo consulta y valida.
Las funciones validar_*() lanzan TramiteNoPermitidoError con el mensaje que
se le muestra al alumno.
"""

import re
import unicodedata
from datetime import timedelta

from django.utils import timezone

from .constants import (
    MAXIMO_BAJAS,
    MINIMO_CREDITOS,
    PLAZO_JUSTIFICANTE_DIAS_HABILES,
)
from .exceptions import TramiteNoPermitidoError
from .models import CalendarioMatricula, PeriodoTramite, Solicitud

TRAMITE_ALTAS = "altas"
TRAMITE_BAJAS = "bajas"

# Una solicitud "en trámite" ya comprometió un lugar (una baja o un NRC)
# aunque todavía no esté aceptada.
ESTADOS_EN_TRAMITE = (
    Solicitud.Estado.PENDIENTE_ACADEMICA,
    Solicitud.Estado.PENDIENTE,
    Solicitud.Estado.PENDIENTE_FIRMA,
)


# ---------------------------------------------------------------------------
# Periodos
# ---------------------------------------------------------------------------


def _matricula_habilitada(tipo_tramite, matricula, ahora):
    """
    Revisa las restricciones por prefijo de matrícula (CalendarioMatricula).
    Si la Secretaría Académica no definió ninguna para este trámite, todas
    las matrículas están habilitadas.
    """
    reglas = CalendarioMatricula.objects.filter(tipo_tramite=tipo_tramite)
    if not reglas.exists():
        return True

    matricula = (matricula or "").strip().upper()
    if not matricula:
        return False

    for regla in reglas:
        prefijo = regla.prefijo_matricula.strip().upper()
        if matricula.startswith(prefijo) and (
            regla.fecha_apertura <= ahora <= regla.fecha_cierre
        ):
            return True
    return False


def tramite_abierto(tipo_tramite, estudiante, ahora=None):
    """
    True si el periodo general del trámite ("altas" o "bajas") está abierto
    y, además, la matrícula del alumno tiene permitido hacerlo en este
    momento.
    """
    ahora = ahora or timezone.now()
    periodo = PeriodoTramite.objects.filter(tipo_tramite=tipo_tramite).first()
    if periodo is None or not (periodo.fecha_apertura <= ahora <= periodo.fecha_cierre):
        return False
    return _matricula_habilitada(tipo_tramite, estudiante.matricula, ahora)


def validar_tramite_abierto(tipo_tramite, estudiante):
    if not tramite_abierto(tipo_tramite, estudiante):
        raise TramiteNoPermitidoError(
            f"El periodo de {tipo_tramite} no está abierto para tu matrícula."
        )


# ---------------------------------------------------------------------------
# Solicitudes existentes
# ---------------------------------------------------------------------------


def nrcs_con_solicitud_activa(estudiante):
    """NRC que ya tienen una solicitud pendiente o aceptada (de cualquier tipo)."""
    return set(
        Solicitud.objects.activas()
        .filter(estudiante=estudiante)
        .values_list("materia_nrc", flat=True)
    )


def validar_sin_solicitud_activa(estudiante, nrcs):
    repetidos = sorted(set(nrcs) & nrcs_con_solicitud_activa(estudiante))
    if repetidos:
        raise TramiteNoPermitidoError(
            "Ya tienes una solicitud pendiente o aceptada para el NRC "
            + ", ".join(repetidos)
            + "."
        )


# ---------------------------------------------------------------------------
# Bajas
# ---------------------------------------------------------------------------


def nrcs_de_bajas_en_tramite(estudiante):
    return set(
        Solicitud.objects.filter(
            estudiante=estudiante,
            tipo_tramite=Solicitud.TipoTramite.BAJA,
            estado__in=ESTADOS_EN_TRAMITE,
        ).values_list("materia_nrc", flat=True)
    )


def bajas_comprometidas(estudiante):
    """
    Bajas que ya cuentan para el límite: las registradas (numero_bajas, que
    sube cuando la secretaria aprueba una baja) más las que siguen en
    trámite. Sin sumar las pendientes, un alumno podía mandar varias
    solicitudes seguidas y pasarse del límite.
    """
    return (estudiante.numero_bajas or 0) + len(nrcs_de_bajas_en_tramite(estudiante))


def creditos_disponibles_para_baja(estudiante, materias_horario):
    """
    Créditos del horario descontando las materias que ya tienen una baja en
    trámite (esos créditos ya están comprometidos).
    """
    en_tramite = nrcs_de_bajas_en_tramite(estudiante)
    return sum(
        int(m.get("creditos") or 0)
        for m in materias_horario
        if str(m.get("nrc")) not in en_tramite
    )


def validar_bajas(estudiante, materias_horario, nrcs_nuevos):
    """Límite de bajas y mínimo de créditos, contando las bajas en trámite."""
    total_bajas = bajas_comprometidas(estudiante) + len(nrcs_nuevos)
    if total_bajas > MAXIMO_BAJAS:
        raise TramiteNoPermitidoError(
            f"Con esta solicitud tendrías {total_bajas} bajas entre registradas "
            f"y en trámite; el máximo permitido es {MAXIMO_BAJAS}."
        )

    creditos_a_baja = sum(
        int(m.get("creditos") or 0)
        for m in materias_horario
        if str(m.get("nrc")) in nrcs_nuevos
    )
    restantes = (
        creditos_disponibles_para_baja(estudiante, materias_horario) - creditos_a_baja
    )
    if restantes < MINIMO_CREDITOS:
        raise TramiteNoPermitidoError(
            f"No se puede realizar la baja. Quedarías con {restantes} créditos "
            f"y el mínimo requerido es {MINIMO_CREDITOS}."
        )
    return restantes


# ---------------------------------------------------------------------------
# Altas: cruces de horario y materias repetidas
# ---------------------------------------------------------------------------

_RE_HORA = re.compile(r"(\d{1,2})(?::(\d{2}))?")
_RE_RANGO = re.compile(r"(\d{1,2}(?::\d{2})?)\s*[-–]\s*(\d{1,2}(?::\d{2})?)")


def normalizar_texto(texto):
    """Minúsculas, sin acentos ni signos: para comparar nombres de materias."""
    if not texto:
        return ""
    sin_acentos = "".join(
        c
        for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"[^a-z0-9\s]", "", sin_acentos.lower()).strip()


def _a_minutos(texto):
    coincidencia = _RE_HORA.search(texto or "")
    if not coincidencia:
        return None
    horas = int(coincidencia.group(1))
    minutos = int(coincidencia.group(2) or 0)
    return horas * 60 + minutos


def _bloques_horario(horarios):
    """
    Convierte la lista de horarios de una materia en (día, inicio, fin) en
    minutos. Acepta los dos formatos que existen en el sistema:
    - horario del alumno: {"dia": "Lunes", "inicio": "07:00", "fin": "09:00"}
    - oferta educativa:   {"dia": "Lunes", "hora": "7:00-9:00"}
    """
    bloques = []
    for horario in horarios or []:
        dia = normalizar_texto(horario.get("dia", ""))[:3]
        if not dia:
            continue
        if horario.get("inicio") and horario.get("fin"):
            inicio, fin = _a_minutos(horario["inicio"]), _a_minutos(horario["fin"])
        else:
            rango = _RE_RANGO.search(horario.get("hora") or "")
            if not rango:
                continue
            inicio, fin = _a_minutos(rango.group(1)), _a_minutos(rango.group(2))
        if inicio is not None and fin is not None and inicio < fin:
            bloques.append((dia, inicio, fin))
    return bloques


def _se_cruzan(bloques_a, bloques_b):
    return any(
        dia_a == dia_b and inicio_a < fin_b and fin_a > inicio_b
        for dia_a, inicio_a, fin_a in bloques_a
        for dia_b, inicio_b, fin_b in bloques_b
    )


def validar_altas(horario_actual, materias_nuevas):
    """
    Las materias a dar de alta no deben repetirse por nombre (entre ellas ni
    con el horario actual) ni cruzarse de horario (entre ellas ni con el
    horario actual).
    """
    nombres_actuales = {normalizar_texto(m.get("materia")) for m in horario_actual}
    vistos = set()
    for materia in materias_nuevas:
        nombre = normalizar_texto(materia.get("materia"))
        if nombre in nombres_actuales or nombre in vistos:
            raise TramiteNoPermitidoError(
                f"La materia {materia.get('materia')} está repetida en tu selección "
                "o ya está en tu horario."
            )
        vistos.add(nombre)

    bloques_actuales = [
        (m, _bloques_horario(m.get("horarios"))) for m in horario_actual
    ]
    bloques_nuevos = [(m, _bloques_horario(m.get("horarios"))) for m in materias_nuevas]

    for indice, (materia, bloques) in enumerate(bloques_nuevos):
        for otra, otros_bloques in bloques_actuales + bloques_nuevos[:indice]:
            if _se_cruzan(bloques, otros_bloques):
                raise TramiteNoPermitidoError(
                    f"La materia {materia.get('materia')} (NRC {materia.get('nrc')}) "
                    f"se cruza de horario con {otra.get('materia')} "
                    f"(NRC {otra.get('nrc')})."
                )


# ---------------------------------------------------------------------------
# Justificante médico
# ---------------------------------------------------------------------------


def dias_habiles_transcurridos(desde, hasta):
    """
    Días hábiles (lunes a viernes) que pasaron DESPUÉS de `desde` y hasta
    `hasta`, incluido. Ejemplo: del viernes al lunes siguiente es 1.
    No considera días festivos.
    """
    dias = 0
    actual = desde
    while actual < hasta:
        actual += timedelta(days=1)
        if actual.weekday() < 5:
            dias += 1
    return dias


def validar_fechas_justificante(inicio, fin, hoy):
    """
    Regresa el mensaje de error de las fechas de inasistencia, o None si son
    válidas: el inicio no puede ser posterior al fin, el fin no puede ser
    futuro y la solicitud debe hacerse dentro del plazo de días hábiles.
    """
    if inicio > fin:
        return "La fecha de inicio no puede ser posterior a la fecha de fin."
    if fin > hoy:
        return "Solo puedes justificar días que ya pasaron."
    if dias_habiles_transcurridos(fin, hoy) > PLAZO_JUSTIFICANTE_DIAS_HABILES:
        return (
            "El justificante debe solicitarse dentro de los primeros "
            f"{PLAZO_JUSTIFICANTE_DIAS_HABILES} días hábiles después de tu "
            "último día de inasistencia."
        )
    return None
