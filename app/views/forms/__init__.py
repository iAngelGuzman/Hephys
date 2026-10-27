"""Formularios de la interfaz, agrupados por área."""

import importlib

_MAPA = {
    "RegistroAlumnoForm": "usuario",
    "HorarioUploadForm": "solicitud",
    "ComprobantePagoForm": "solicitud",
    "SolicitudConstanciaForm": "solicitud",
    "SolicitudJustificanteForm": "solicitud",
    "PeriodoTramiteForm": "administrador",
    "CalendarioMatriculaForm": "administrador",
    "SubirOfertaPDFForm": "administrador",
    "SubirCalendarioExamenesForm": "administrador",
    "CrearSecretariaForm": "administrador",
    "EditarSecretariaForm": "administrador",
}


def __getattr__(nombre):
    if nombre in {"usuario", "solicitud", "administrador"}:
        return importlib.import_module(f"{__name__}.{nombre}")
    modulo = _MAPA.get(nombre)
    if modulo is None:
        raise AttributeError(f"El módulo 'app.views.forms' no tiene '{nombre}'")
    return getattr(importlib.import_module(f"{__name__}.{modulo}"), nombre)


def __dir__():
    return sorted(set(globals()) | set(_MAPA))


__all__ = sorted(_MAPA)
