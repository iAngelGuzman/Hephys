"""
Sonda de salud del servicio (``/health``).

La usan los monitores y el hosting (Render) para saber si la instancia puede
recibir tráfico. No requiere sesión ni rol: solo comprueba que Django
responda y que la conexión a MySQL siga viva.
"""

from django.db import connection
from django.http import JsonResponse


def base_de_datos_operativa():
    """True si MySQL responde a una consulta mínima."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        return False
    return True


def health(request):
    """
    Responde 200 si la app y la base de datos están operativas.

    Si MySQL no contesta se devuelve 503 para que el balanceador retire la
    instancia en lugar de mandarle solicitudes que van a fallar.
    """
    if not base_de_datos_operativa():
        return JsonResponse(
            {"status": "error", "database": "unavailable"},
            status=503,
        )

    return JsonResponse({"status": "ok", "database": "ok"})
