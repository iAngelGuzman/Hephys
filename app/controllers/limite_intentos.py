"""
Límite de intentos de inicio de sesión (protección contra fuerza bruta).

Se llevan dos cuentas en la caché de Django:

1. Por usuario + IP: después de MAXIMO_INTENTOS_POR_IP contraseñas
   incorrectas desde la misma IP se bloquea ese par. Así nadie puede
   bloquear a otra persona desde su computadora con solo escribir su
   matrícula.
2. Por usuario (desde cualquier IP): un límite más alto,
   MAXIMO_INTENTOS_POR_USUARIO. Protege aunque alguien cambie de IP o la
   falsifique, porque la IP que llega detrás de un proxy nunca es 100%
   confiable.

Los bloqueos duran MINUTOS_BLOQUEO minutos desde el primer intento
fallido. La caché es la base de datos (CACHES en settings.py), así que
todos los workers de gunicorn comparten las mismas cuentas.
"""

from django.core.cache import cache

MAXIMO_INTENTOS_POR_IP = 5
MAXIMO_INTENTOS_POR_USUARIO = 20
MINUTOS_BLOQUEO = 15


def _ip_cliente(request):
    """
    IP real del visitante.

    En Render el tráfico pasa por Cloudflare, que pone la IP del visitante
    en CF-Connecting-IP y no deja que el navegador la cambie. No se usa
    X-Forwarded-For porque Render solo le agrega datos al final y el
    visitante puede escribir lo que quiera al inicio. En local (sin
    proxy) se usa REMOTE_ADDR.
    """
    return (
        request.META.get("HTTP_CF_CONNECTING_IP")
        or request.META.get("REMOTE_ADDR", "")
    ).strip()


def _claves(request, identificador):
    usuario = identificador.strip().lower()
    return (
        (f"login-intentos:ip:{_ip_cliente(request)}:{usuario}", MAXIMO_INTENTOS_POR_IP),
        (f"login-intentos:usuario:{usuario}", MAXIMO_INTENTOS_POR_USUARIO),
    )


def esta_bloqueado(request, identificador):
    return any(
        cache.get(clave, 0) >= maximo for clave, maximo in _claves(request, identificador)
    )


def registrar_intento_fallido(request, identificador):
    for clave, _ in _claves(request, identificador):
        # add() solo crea la clave si no existe; así el tiempo de bloqueo
        # cuenta desde el primer intento fallido y no se reinicia.
        cache.add(clave, 0, timeout=MINUTOS_BLOQUEO * 60)
        try:
            cache.incr(clave)
        except ValueError:
            cache.set(clave, 1, timeout=MINUTOS_BLOQUEO * 60)


def limpiar_intentos(request, identificador):
    cache.delete_many([clave for clave, _ in _claves(request, identificador)])
