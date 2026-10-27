"""
Capa de presentación (``app/views``).

Vistas, formularios y validación visual. Las plantillas viven en
``templates/`` y los recursos estáticos en ``public/static/``.

Las vistas se cargan de forma perezosa para no provocar ciclos con
``app.controllers`` (los servicios usan los formularios de esta capa).
"""

import importlib

_MODULOS = {
    "autenticacion": "autenticacion",
    "estudiante": "estudiante",
    "secretaria": "secretaria",
    "administracion": "administracion",
    "tramites": "tramites",
    "salud": "salud",
    "forms": "forms",
}

_MAPA = {
    # Sonda de salud
    "health": ("salud", "health"),
    # Autenticación
    "login_usuario": ("autenticacion", "login_usuario"),
    "registrar_alumno": ("autenticacion", "registrar_alumno"),
    # Alumno
    "lista_tramites": ("tramites", "lista_tramites"),
    "mis_solicitudes": ("estudiante", "mis_solicitudes"),
    "historial_solicitudes_alumno": ("estudiante", "historial_solicitudes"),
    "ver_horario_pdf": ("estudiante", "ver_horario_pdf"),
    "ver_comprobante_pdf": ("estudiante", "ver_comprobante_pdf"),
    "ver_documento_medico": ("estudiante", "ver_documento_medico"),
    # Secretaría
    "dashboard_secretaria": ("secretaria", "dashboard"),
    "aprobar_solicitud_secretaria": ("secretaria", "aprobar_solicitud"),
    "rechazar_solicitud_secretaria": ("secretaria", "rechazar_solicitud"),
    "historial_solicitudes_secretaria": ("secretaria", "historial_solicitudes"),
    # Administración
    "dashboard_administrador": ("administracion", "dashboard"),
    "configurar_altas_bajas": ("administracion", "configurar_altas_bajas"),
    "subir_oferta_pdf": ("administracion", "subir_oferta_pdf"),
    "gestion_cupos": ("administracion", "gestion_cupos"),
    "configurar_examenes": ("administracion", "configurar_examenes"),
    "eliminar_horario_examenes": ("administracion", "eliminar_horario_examenes"),
    "control_usuarios": ("administracion", "control_usuarios"),
    "cambiar_estado_usuario": ("administracion", "cambiar_estado_usuario"),
    "crear_secretaria": ("administracion", "crear_secretaria"),
    "editar_usuario": ("administracion", "editar_usuario"),
    "solicitudes_pendientes": ("administracion", "solicitudes_pendientes"),
    "aprobar_solicitud_administrador": ("administracion", "aprobar_solicitud"),
    "rechazar_solicitud_administrador": ("administracion", "rechazar_solicitud"),
    "historial_solicitudes_administrador": (
        "administracion",
        "historial_solicitudes",
    ),
}


def __getattr__(nombre):
    if nombre in _MODULOS:
        return importlib.import_module(f"{__name__}.{_MODULOS[nombre]}")
    destino = _MAPA.get(nombre)
    if destino is None:
        raise AttributeError(f"El módulo 'app.views' no tiene '{nombre}'")
    modulo, atributo = destino
    return getattr(importlib.import_module(f"{__name__}.{modulo}"), atributo)


def __dir__():
    return sorted(set(globals()) | set(_MODULOS) | set(_MAPA))


__all__ = sorted(set(_MODULOS) | set(_MAPA))
