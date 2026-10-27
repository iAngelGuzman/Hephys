"""
Capa de persistencia (``app/models``).

Todos los modelos del sistema viven aquí y pertenecen a la app Django
``app``. Las tablas conservan los nombres del modelo relacional documentado
(``usuarios``, ``estudiantes``, ``tramites``, etc.).

Las consultas se hacen con el ORM (sentencias preparadas) y los cambios de
estado con ``transaction.atomic()``.
"""

from .administrador import Carrera, HorarioExamen
from .estudiante import Estudiante
from .secretaria import Secretaria
from .solicitud import (
    ESTADOS_ACTIVOS,
    ESTADOS_RECHAZADA,
    MAPA_ESTATUS_DOCUMENTADO,
    BitacoraTransaccional,
    CalendarioMatricula,
    ComprobantePago,
    EstadoSolicitud,
    ExperienciaEducativa,
    ExperienciaEducativaOferta,
    PeriodoTramite,
    Solicitud,
    TipoTramite,
    generar_folio,
)
from .usuario import User

__all__ = [
    # Usuarios y perfiles
    "User",
    "Estudiante",
    "Secretaria",
    # Solicitudes
    "Solicitud",
    "TipoTramite",
    "EstadoSolicitud",
    "ESTADOS_ACTIVOS",
    "ESTADOS_RECHAZADA",
    "MAPA_ESTATUS_DOCUMENTADO",
    "generar_folio",
    "ComprobantePago",
    "BitacoraTransaccional",
    # Periodos, oferta y exámenes
    "PeriodoTramite",
    "CalendarioMatricula",
    "ExperienciaEducativa",
    "ExperienciaEducativaOferta",
    "Carrera",
    "HorarioExamen",
]
