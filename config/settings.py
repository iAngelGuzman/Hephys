"""
Configuración de Django para el sistema de trámites académicos (Hephys).

Todos los valores sensibles o que cambian entre máquinas (llaves, base de
datos, dominios) se leen del archivo ".env" con python-decouple. Este archivo
NO debe editarse para cambiar de base de datos o de entorno: para eso está
el ".env" (ver ".env.example").
"""

import os
from pathlib import Path

from decouple import Csv, config

from config.database import construir_bases_de_datos

BASE_DIR = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Seguridad básica
# ---------------------------------------------------------------------------

# Obligatoria: si no está en el .env, Django no arranca (a propósito).
SECRET_KEY = config("SECRET_KEY")

# En producción debe ser False (es el valor por defecto si no se define).
DEBUG = config("DEBUG", default=False, cast=bool)

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="", cast=Csv())

# Orígenes con https:// desde los que se aceptan formularios (p. ej. el
# dominio de Render). Separados por coma.
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", default="", cast=Csv())


# ---------------------------------------------------------------------------
# Aplicaciones
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    # WhiteNoise también sirve los estáticos con runserver (en lugar del
    # servidor de Django). Con DEBUG=True le dice al navegador que no guarde
    # los CSS/JS en caché, así un .js modificado se ve con solo recargar.
    "whitenoise.runserver_nostatic",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Una sola app de Django contiene las capas documentadas:
    # app/models, app/controllers y app/views.
    "app",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # Después de AuthenticationMiddleware: registra quién hace cada cambio
    # de estado en bitacora_transaccional (HU-25).
    "app.controllers.middleware.AuditoriaMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ---------------------------------------------------------------------------
# Base de datos
# ---------------------------------------------------------------------------
# La configuración vive en config/database.py (capa de conexión centralizada).
# Siempre MySQL con las variables DB_* del .env.
# DB_SSL=True                 -> exige conexión cifrada (necesario en Aiven).

DATABASES = construir_bases_de_datos(BASE_DIR)


# ---------------------------------------------------------------------------
# Caché
# ---------------------------------------------------------------------------
# En la base de datos para que todos los workers de gunicorn compartan los
# mismos datos (lo usa el límite de intentos de inicio de sesión). La tabla
# se crea con:  python manage.py createcachetable

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "cache_sistema",
    }
}


# ---------------------------------------------------------------------------
# Autenticación
# ---------------------------------------------------------------------------

AUTH_USER_MODEL = "app.User"

# A dónde manda @login_required (y @rol_requerido) cuando no hay sesión.
LOGIN_URL = "usuario:login"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# ---------------------------------------------------------------------------
# Internacionalización
# ---------------------------------------------------------------------------

LANGUAGE_CODE = "es-mx"

TIME_ZONE = "America/Mexico_City"

USE_I18N = True

USE_TZ = True


# ---------------------------------------------------------------------------
# Archivos estáticos (CSS, JS, imágenes)
# ---------------------------------------------------------------------------

STATIC_URL = "/static/"

# public/ es el directorio raíz documentado (Semana 1 y 2): ahí viven todos
# los recursos estáticos, compartidos y por módulo.
STATICFILES_DIRS = [BASE_DIR / "public" / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Manifest: collectstatic agrega un hash al nombre de cada archivo
# (base.3f2a1c.css), así el navegador descarga la versión nueva en cuanto
# cambia. OJO: con DEBUG=False, un {% static %} que apunte a un archivo que
# no existe (o con otras mayúsculas) truena la página: el nombre en la
# plantilla debe coincidir EXACTO con el archivo. Requiere correr
# `python manage.py collectstatic --noinput` en el deploy (Render).
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


# ---------------------------------------------------------------------------
# Archivos subidos por los alumnos
# ---------------------------------------------------------------------------
# Los nombres de subcarpeta deben coincidir EXACTAMENTE (mayúsculas
# incluidas) con los que usa guardar_archivo_temporal() en
# app.controllers.servicios_solicitud.py, porque en Linux (donde corre en producción)
# el sistema de archivos distingue mayúsculas de minúsculas.

CARPETA_COMPROBANTES_PAGO = os.path.join(BASE_DIR, "Papeles", "comprobantes_pago")
CARPETA_PAPELES_HORARIOS = os.path.join(BASE_DIR, "Papeles", "horarios")

# Documentos sensibles (certificados, kárdex, programas) y resoluciones
# finales. Viven FUERA de static/ y de MEDIA_ROOT para que no se puedan
# descargar sin pasar por una vista que valide rol y propiedad (CA-01/CA-04).
CARPETA_DOCUMENTOS_SEGUROS = os.path.join(BASE_DIR, "storage", "secure_uploads")
CARPETA_RESOLUCIONES = os.path.join(BASE_DIR, "storage", "resoluciones")


# ---------------------------------------------------------------------------
# Seguridad en producción (solo aplica con DEBUG=False)
# ---------------------------------------------------------------------------

if not DEBUG:
    # Render atiende HTTPS y reenvía a Django por HTTP con este encabezado;
    # sin esto Django cree que la petición no es segura y rechaza el CSRF.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # 0 = desactivado. Solo subirlo cuando el dominio sea definitivo.
    SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=0, cast=int)


# ---------------------------------------------------------------------------
# Logs (se ven en la consola local y en los logs de Render)
# ---------------------------------------------------------------------------

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "[{levelname}] {name}: {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "pdfminer": {"level": "ERROR"},
        "pypdf": {"level": "ERROR"},
    },
}
