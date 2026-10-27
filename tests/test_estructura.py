"""
Pruebas de la estructura base documentada (Semana 1 y 2, tabla 2).

Comprueban que existan las carpetas acordadas, que los estáticos se sirvan
desde ``public/``, que los documentos sensibles queden fuera de la zona
pública y que las fachadas de ``app/`` reexporten las tres capas.
"""

from pathlib import Path

from django.conf import settings
from django.db import connection
from django.test import SimpleTestCase, TestCase

BASE_DIR = Path(settings.BASE_DIR)

CARPETAS_DOCUMENTADAS = {
    "app/controllers": "Lógica de negocio y coordinación con la base de datos.",
    "app/models": "Clases de persistencia y transacciones atómicas.",
    "app/views": "Interfaz de usuario y validación visual.",
    "config": "Conexión MySQL y enrutamiento general.",
    "storage/secure_uploads": "Documentos PDF aislados y protegidos.",
    "public": "Raíz de archivos de entrada y recursos estáticos.",
    "tests": "Pruebas automatizadas y validación de seguridad.",
}

TABLAS_DOCUMENTADAS = {
    "usuarios",
    "estudiantes",
    "secretarias",
    "tramites",
    "bitacora_transaccional",
    "comprobantes_pago",
}

TABLAS_ELIMINADAS = {
    "catalogo_tramites",
    "requisitos_tramite",
    "detalle_traspasos",
    "certificados_ingles",
    "observaciones_solicitud",
    "documentos_solicitud",
    "auth_group",
    "auth_group_permissions",
    "usuarios_groups",
    "usuarios_user_permissions",
}


class EstructuraDeCarpetasTests(SimpleTestCase):
    def test_existen_las_carpetas_documentadas(self):
        faltantes = [
            ruta for ruta in CARPETAS_DOCUMENTADAS if not (BASE_DIR / ruta).is_dir()
        ]
        self.assertEqual(
            faltantes,
            [],
            "Faltan carpetas de la estructura base: " + ", ".join(faltantes),
        )

    def test_los_estaticos_se_sirven_desde_public(self):
        esperada = (BASE_DIR / "public" / "static").resolve()
        configuradas = [Path(ruta).resolve() for ruta in settings.STATICFILES_DIRS]

        self.assertIn(esperada, configuradas)
        self.assertTrue((esperada / "css" / "base.css").is_file())
        self.assertFalse((BASE_DIR / "static").exists())

    def test_los_documentos_sensibles_estan_fuera_de_lo_publico(self):
        publico = (BASE_DIR / "public").resolve()
        estaticos = (BASE_DIR / "staticfiles").resolve()
        media = (BASE_DIR / "media").resolve()

        for ruta in (
            settings.CARPETA_DOCUMENTOS_SEGUROS,
            settings.CARPETA_RESOLUCIONES,
        ):
            ruta = Path(ruta).resolve()
            self.assertTrue(ruta.is_dir(), f"No existe la carpeta {ruta}")
            for zona_publica in (publico, estaticos, media):
                self.assertFalse(
                    ruta.is_relative_to(zona_publica),
                    f"{ruta} no debe estar dentro de {zona_publica}",
                )

    def test_las_fachadas_reexportan_las_capas(self):
        from app import controllers, models, views

        # Persistencia
        self.assertTrue(hasattr(models, "Solicitud"))
        self.assertTrue(hasattr(models, "BitacoraTransaccional"))
        self.assertTrue(hasattr(models, "ComprobantePago"))
        # Lógica de negocio
        self.assertTrue(hasattr(controllers, "crear_solicitud_constancia"))
        self.assertTrue(hasattr(controllers, "validar_bajas"))
        self.assertTrue(hasattr(controllers, "registrar_movimiento"))
        # Interfaz
        self.assertTrue(hasattr(views, "login_usuario"))
        self.assertTrue(hasattr(views, "mis_solicitudes"))
        self.assertTrue(hasattr(views, "aprobar_solicitud_secretaria"))


class EsquemaDocumentadoTests(TestCase):
    def test_tablas_documentadas_son_innodb_y_utf8mb4(self):
        if connection.vendor != "mysql":
            self.skipTest("InnoDB y utf8mb4 solo se comprueban sobre MySQL.")

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT TABLE_NAME, ENGINE, TABLE_COLLATION "
                "FROM information_schema.TABLES "
                "WHERE TABLE_SCHEMA = DATABASE()"
            )
            tablas = {
                nombre: (motor, collation)
                for nombre, motor, collation in cursor.fetchall()
            }

        faltantes = TABLAS_DOCUMENTADAS - tablas.keys()
        self.assertEqual(
            faltantes,
            set(),
            "Faltan tablas del modelo relacional: " + ", ".join(sorted(faltantes)),
        )

        for nombre in sorted(TABLAS_DOCUMENTADAS):
            motor, collation = tablas[nombre]
            self.assertEqual(motor, "InnoDB", f"{nombre} no usa InnoDB")
            self.assertTrue(
                collation.startswith("utf8mb4"),
                f"{nombre} usa {collation}, se esperaba utf8mb4",
            )

    def test_las_tablas_en_desuso_no_existen(self):
        existentes = set(connection.introspection.table_names())
        sobrantes = TABLAS_ELIMINADAS & existentes
        self.assertEqual(
            sobrantes,
            set(),
            "Siguen existiendo tablas en desuso: " + ", ".join(sorted(sobrantes)),
        )
