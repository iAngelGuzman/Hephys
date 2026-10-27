"""
Capa de lógica de negocio (``app/controllers``).

Coordina la interfaz (``app/views``) con la persistencia (``app/models``):
valida reglas académicas, calcula cupos y créditos, procesa PDF y deja la
bitácora dentro de la misma transacción que el cambio de estado.

Los módulos se cargan de forma perezosa para evitar ciclos de importación
(por ejemplo, los servicios usan formularios y los formularios usan reglas).
"""

import importlib

_MAPA = {
    # Solicitudes
    "guardar_archivo_temporal": "servicios_solicitud",
    "procesar_horario": "servicios_solicitud",
    "procesar_papeletas": "servicios_solicitud",
    "crear_comprobante_pago": "servicios_solicitud",
    "crear_solicitudes_examen": "servicios_solicitud",
    "crear_solicitudes_alta": "servicios_solicitud",
    "crear_solicitudes_baja": "servicios_solicitud",
    "crear_solicitud_constancia": "servicios_solicitud",
    "crear_solicitud_justificante": "servicios_solicitud",
    # Reglas académicas
    "tramite_abierto": "reglas",
    "validar_tramite_abierto": "reglas",
    "nrcs_con_solicitud_activa": "reglas",
    "validar_sin_solicitud_activa": "reglas",
    "nrcs_de_bajas_en_tramite": "reglas",
    "bajas_comprometidas": "reglas",
    "creditos_disponibles_para_baja": "reglas",
    "validar_bajas": "reglas",
    "validar_altas": "reglas",
    "dias_habiles_transcurridos": "reglas",
    "validar_fechas_justificante": "reglas",
    "normalizar_texto": "reglas",
    # Auditoría
    "establecer_usuario_actual": "auditoria",
    "restablecer_usuario_actual": "auditoria",
    "obtener_usuario_actual": "auditoria",
    "registrar_movimiento": "auditoria",
    # Validación y PDF
    "validar_archivo_pdf": "validadores",
    "extraer_materias_horario_examen": "lectores_pdf",
    "limpiar_materias_examen": "lectores_pdf",
    "extraer_materias_altas_bajas": "lectores_pdf",
    # Administración
    "obtener_periodos_tramite": "servicios_administracion",
    "guardar_periodo_tramite": "servicios_administracion",
    "eliminar_calendario_matricula": "servicios_administracion",
    "procesar_pdf_oferta_educativa": "servicios_administracion",
    "procesar_pdf_horarios": "servicios_administracion",
    "obtener_horarios_examen_vigentes": "servicios_administracion",
    "normalizar_carrera": "normalizacion",
    # Seguridad
    "rol_requerido": "decoradores",
    "esta_bloqueado": "limite_intentos",
    "registrar_intento_fallido": "limite_intentos",
    "limpiar_intentos": "limite_intentos",
    "MAXIMO_INTENTOS_POR_IP": "limite_intentos",
    "MAXIMO_INTENTOS_POR_USUARIO": "limite_intentos",
    "MINUTOS_BLOQUEO": "limite_intentos",
    # Middleware
    "AuditoriaMiddleware": "middleware",
}


def __getattr__(nombre):
    modulo = _MAPA.get(nombre)
    if modulo is None:
        raise AttributeError(f"El módulo 'app.controllers' no tiene '{nombre}'")
    return getattr(importlib.import_module(f"{__name__}.{modulo}"), nombre)


def __dir__():
    return sorted(set(globals()) | set(_MAPA))


__all__ = sorted(_MAPA)
