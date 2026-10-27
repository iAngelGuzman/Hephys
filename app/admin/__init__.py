"""Registro de los modelos en el panel de administración de Django."""

from . import administrador, estudiante, secretaria, solicitud, usuario  # noqa: F401

__all__ = ["administrador", "estudiante", "secretaria", "solicitud", "usuario"]
