"""Funciones de apoyo sin acceso a base de datos."""

import re
import unicodedata

from apps.administrador.constants import CARRERA_CODES
from apps.estudiante.models import Estudiante


def _normalizar_para_comparar(texto):
    """Mayúsculas, sin acentos y sin espacios/puntuación, para comparar."""
    if not texto:
        return ""
    sin_acentos = "".join(
        c
        for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"[^A-Z0-9]", "", sin_acentos.upper())

_PREFIJOS = ("LICENCIATURAEN", "LICEN")


def _sin_prefijo(clave):
    for prefijo in _PREFIJOS:
        if clave.startswith(prefijo):
            return clave[len(prefijo) :]
    return clave


_CARRERAS_NORMALIZADAS = {
    _sin_prefijo(_normalizar_para_comparar(valor)): valor
    for valor in Estudiante.ProgramaEducativo.values
}

_CARRERAS_POR_SIGLA = {sigla: str(valor) for sigla, valor in CARRERA_CODES.items()}


def normalizar_carrera(texto_detectado):
    """
    Hace coincidir el texto de "carrera" detectado en un PDF (con posibles
    diferencias de mayúsculas, acentos, prefijos como "Lic. en" o la sigla
    sola) con uno de los valores oficiales de Estudiante.ProgramaEducativo,
    para que ExperienciaEducativa.carrera quede siempre con el mismo valor
    que usan los estudiantes en su perfil. Si no encuentra ninguna
    coincidencia razonable, regresa None.
    """
    clave_completa = _normalizar_para_comparar(texto_detectado)
    if not clave_completa:
        return None

    if clave_completa in _CARRERAS_POR_SIGLA:
        return _CARRERAS_POR_SIGLA[clave_completa]

    clave_detectada = _sin_prefijo(clave_completa)
    if not clave_detectada:
        return None

    if clave_detectada in _CARRERAS_NORMALIZADAS:
        return _CARRERAS_NORMALIZADAS[clave_detectada]

    for clave_oficial, valor_oficial in _CARRERAS_NORMALIZADAS.items():
        if clave_oficial in clave_detectada or clave_detectada in clave_oficial:
            return valor_oficial

    return None
