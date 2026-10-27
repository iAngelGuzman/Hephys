"""
Conexión centralizada a la base de datos (capa ``config/``).

Este módulo es el único lugar del proyecto que conoce cómo se conecta Django
con MySQL. ``config/settings.py`` solo lo llama; ninguna vista, modelo o
servicio abre conexiones por su cuenta.

Parámetros alineados con la documentación técnica del proyecto (Semana 8):

* Driver: MySQL (``django.db.backends.mysql`` -> mysqlclient).
* Juego de caracteres: ``utf8mb4`` (acentos, ñ y emojis sin corrupción).
* Modo estricto: MySQL rechaza datos truncados o inválidos en lugar de
  guardarlos a medias (equivalente a ``PDO::ATTR_ERRMODE`` estricto).
* Emulación de consultas desactivada: Django/mysqlclient usan sentencias
  preparadas nativas, lo que neutraliza la inyección SQL.
* Credenciales solo en ``.env``: nunca en el código ni en git.

Todas las variables se leen con python-decouple desde el archivo ``.env``.
"""

from decouple import config

MOTOR_MYSQL = "django.db.backends.mysql"

# Modo estricto de MySQL: cualquier INSERT/UPDATE con un dato inválido,
# truncado o fuera de rango se rechaza con error (no se guarda "lo que se
# pueda"). Es el comportamiento que exige la integridad transaccional ACID.
MODO_ESTRICTO_MYSQL = "STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION,ERROR_FOR_DIVISION_BY_ZERO"


def construir_opciones_mysql():
    """
    Opciones de conexión de mysqlclient.

    ``charset``          -> utf8mb4 en cada conexión.
    ``init_command``     -> activa el modo estricto en cada conexión nueva.
    ``isolation_level``  -> READ COMMITTED; evita lecturas sucias cuando dos
                            secretarias actualizan la misma solicitud.
    ``ssl_mode``         -> REQUIRED cuando el proveedor exige TLS (Aiven).
    ``ssl``              -> ruta al certificado CA, si el proveedor la pide.
    """
    opciones = {
        "charset": "utf8mb4",
        "init_command": f"SET sql_mode='{MODO_ESTRICTO_MYSQL}'",
        "isolation_level": "read committed",
    }

    if config("DB_SSL", default=False, cast=bool):
        # mysqlclient >= 2.2.4 acepta ssl_mode directamente.
        opciones["ssl_mode"] = "REQUIRED"
        ruta_ca = config("DB_SSL_CA", default="").strip()
        if ruta_ca:
            opciones["ssl"] = {"ca": ruta_ca}

    return opciones


def construir_bases_de_datos(base_dir):
    """
    Regresa el diccionario ``DATABASES`` que espera Django.

    ``base_dir`` se recibe como argumento para no duplicar la ruta del
    proyecto y para que las pruebas puedan construir la configuración sin
    depender de ``settings``. La única base soportada es MySQL.
    """
    return {
        "default": {
            "ENGINE": MOTOR_MYSQL,
            # Nombre de la base creada con database/hephys_db.sql
            "NAME": config("DB_NAME", default="hephys_db"),
            "USER": config("DB_USER", default="hephys_user"),
            "PASSWORD": config("DB_PASSWORD", default=""),
            "HOST": config("DB_HOST", default="localhost"),
            "PORT": config("DB_PORT", default="3306"),
            "CONN_MAX_AGE": config("DB_CONN_MAX_AGE", default=60, cast=int),
            "CONN_HEALTH_CHECKS": True,
            "OPTIONS": construir_opciones_mysql(),
            "TEST": {
                # La base de pruebas se crea y destruye sola; nunca toca
                # los datos reales de hephys_db.
                "CHARSET": "utf8mb4",
                "COLLATION": "utf8mb4_unicode_ci",
            },
        }
    }
