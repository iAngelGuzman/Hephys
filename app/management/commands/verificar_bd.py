"""
Comprueba que la conexión a MySQL funciona y que el esquema está completo.

Uso:
    python manage.py verificar_bd

Sirve como evidencia para la tesis (Semana 8): muestra motor, versión,
juego de caracteres, modo estricto, motor transaccional de las tablas y si
las tablas del modelo relacional existen.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import connection

TABLAS_REQUERIDAS = (
    "usuarios",
    "estudiantes",
    "secretarias",
    "tramites",
    "bitacora_transaccional",
    "comprobantes_pago",
)

TABLAS_EN_DESUSO = (
    "detalle_traspasos",
    "documentos_solicitud",
    "certificados_ingles",
    "catalogo_tramites",
    "requisitos_tramite",
    "observaciones_solicitud",
    "auth_group",
    "auth_group_permissions",
    "usuarios_groups",
    "usuarios_user_permissions",
)


class Command(BaseCommand):
    help = "Verifica la conexión a MySQL y la estructura de la base de datos."

    def handle(self, *args, **options):
        try:
            connection.ensure_connection()
        except Exception as error:  # pragma: no cover - depende del servidor
            raise CommandError(
                "No se pudo conectar a la base de datos. Revisa las variables "
                f"DB_* del archivo .env.\nDetalle: {error}"
            ) from error

        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]

            cursor.execute("SELECT DATABASE()")
            base = cursor.fetchone()[0]

            cursor.execute("SELECT @@character_set_database, @@collation_database")
            charset, collation = cursor.fetchone()

            cursor.execute("SELECT @@sql_mode")
            sql_mode = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT TABLE_NAME, ENGINE
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = DATABASE()
                ORDER BY TABLE_NAME
                """
            )
            tablas = cursor.fetchall()

        self.stdout.write(self.style.SUCCESS("Conexión correcta"))
        self.stdout.write(f"  Motor:        {connection.vendor} ({connection.settings_dict['ENGINE']})")
        self.stdout.write(f"  Base:         {base}")
        self.stdout.write(f"  Servidor:     MySQL {version}")
        self.stdout.write(f"  Charset:      {charset} / {collation}")
        self.stdout.write(f"  sql_mode:     {sql_mode}")
        self.stdout.write(f"  Tablas:       {len(tablas)}")

        if "STRICT_TRANS_TABLES" not in sql_mode:
            self.stdout.write(
                self.style.WARNING(
                    "  Aviso: el modo estricto no está activo en esta conexión."
                )
            )

        existentes = {nombre for nombre, _ in tablas}
        faltantes = [tabla for tabla in TABLAS_REQUERIDAS if tabla not in existentes]
        if faltantes:
            self.stdout.write(
                self.style.WARNING(
                    "  Faltan tablas (corre `python manage.py migrate`): "
                    + ", ".join(faltantes)
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("  Estructura del modelo relacional completa.")
            )

        en_desuso = [tabla for tabla in TABLAS_EN_DESUSO if tabla in existentes]
        if en_desuso:
            self.stdout.write(
                self.style.WARNING(
                    "  Aviso: siguen existiendo tablas en desuso: "
                    + ", ".join(en_desuso)
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("  No hay tablas en desuso.")
            )

        no_innodb = [
            (nombre, motor)
            for nombre, motor in tablas
            if motor and motor.upper() != "INNODB"
        ]
        if no_innodb:
            self.stdout.write(
                self.style.WARNING(
                    "  Aviso: estas tablas no usan InnoDB (sin transacciones): "
                    + ", ".join(f"{n} ({m})" for n, m in no_innodb)
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("  Todas las tablas usan InnoDB (ACID).")
            )
