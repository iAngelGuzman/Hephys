"""Middleware que identifica al responsable de cada cambio (HU-25)."""

from .auditoria import (
    establecer_usuario_actual,
    restablecer_usuario_actual,
)


class AuditoriaMiddleware:
    """
    Debe ir DESPUÉS de ``AuthenticationMiddleware`` en ``settings.MIDDLEWARE``:
    en ese punto ``request.user`` ya está resuelto.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = establecer_usuario_actual(getattr(request, "user", None))
        try:
            return self.get_response(request)
        finally:
            restablecer_usuario_actual(token)
