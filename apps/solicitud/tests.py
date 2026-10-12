"""
Pruebas de la pantalla de trámites y del historial del alumno.

Correr con:  python manage.py test apps.solicitud
"""

import shutil
import tempfile

from django.test import TestCase, override_settings
from django.urls import reverse

from apps.estudiante.models import Estudiante
from apps.secretaria.models import Secretaria
from apps.solicitud.models import Solicitud
from apps.usuario.models import User

CARPETA_TEMPORAL = tempfile.mkdtemp()

AJUSTES_PRUEBA = {
    "STORAGES": {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    },
    "CARPETA_COMPROBANTES_PAGO": CARPETA_TEMPORAL,
    "CARPETA_PAPELES_HORARIOS": CARPETA_TEMPORAL,
    "CARPETA_JUSTIFICANTES": CARPETA_TEMPORAL,
}


@override_settings(**AJUSTES_PRUEBA)
class BaseTramites(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(CARPETA_TEMPORAL, ignore_errors=True)

    def setUp(self):
        usuario_secretaria = User.objects.create_user(
            "secretaria", password="x", rol=User.Rol.SECRETARIA_GRUPO
        )
        self.secretaria = Secretaria.objects.create(user=usuario_secretaria)
        usuario = User.objects.create_user("S24000001", password="x", rol=User.Rol.ALUMNO)
        self.estudiante = Estudiante.objects.create(
            user=usuario,
            nombres="Ana",
            apellido_paterno="Pérez",
            apellido_materno="López",
            matricula="S24000001",
            carrera=Estudiante.ProgramaEducativo.LIS,
            semestre=3,
            secretaria=self.secretaria,
            numero_bajas=0,
        )
        self.client.force_login(usuario)


class PantallasAlumnoTests(BaseTramites):
    def test_se_ven_todos_los_tramites(self):
        respuesta = self.client.get(reverse("solicitud:lista_tramites"))
        self.assertContains(respuesta, "Justificante Médico")
        self.assertContains(respuesta, "Constancia de Estudios")
        self.assertContains(respuesta, "Examen Extraordinario")
        self.assertContains(respuesta, "Altas / Bajas")

    def test_no_se_puede_entrar_a_los_tramites(self):
        respuesta = self.client.get(reverse("solicitud:lista_tramites"))
        # Los botones "Solicitar" se ven, pero no son enlaces a ningún trámite.
        self.assertContains(respuesta, 'class="btn-solicitar"', count=4)
        self.assertContains(respuesta, 'href="/solicitudes/', count=1)  # solo el menú lateral
        self.assertEqual(self.client.get("/solicitudes/constancia-estudios/").status_code, 404)


class HistorialAlumnoTests(BaseTramites):
    """Mis solicitudes = en trámite; Historial = aceptadas o rechazadas."""

    def setUp(self):
        super().setUp()
        self.en_tramite = Solicitud.objects.create(
            estudiante=self.estudiante,
            tipo_tramite="constancia",
            estado=Solicitud.Estado.PENDIENTE_FIRMA,
        )
        self.aceptada = Solicitud.objects.create(
            estudiante=self.estudiante,
            tipo_tramite="extraordinario",
            estado=Solicitud.Estado.ACEPTADA,
            materia_nombre="Bases de datos",
        )
        self.rechazada = Solicitud.objects.create(
            estudiante=self.estudiante,
            tipo_tramite="justificante",
            estado=Solicitud.Estado.RECHAZADA_ACADEMICA,
        )

    def folios(self, respuesta):
        return {solicitud.id for solicitud in respuesta.context["solicitudes"]}

    def test_mis_solicitudes_solo_muestra_las_que_estan_en_tramite(self):
        respuesta = self.client.get(reverse("estudiante:mis_solicitudes"))
        self.assertEqual(self.folios(respuesta), {self.en_tramite.id})
        self.assertContains(respuesta, reverse("estudiante:historial_solicitudes"))

    def test_historial_muestra_aceptadas_y_rechazadas(self):
        respuesta = self.client.get(reverse("estudiante:historial_solicitudes"))
        self.assertEqual(self.folios(respuesta), {self.aceptada.id, self.rechazada.id})
        self.assertContains(respuesta, "Historial de solicitudes")

    def test_filtro_de_estado_en_historial(self):
        respuesta = self.client.get(
            reverse("estudiante:historial_solicitudes"), {"estado": "aceptada"}
        )
        self.assertEqual(self.folios(respuesta), {self.aceptada.id})
        # El filtro del historial no ofrece estados en trámite.
        self.assertNotContains(respuesta, 'value="pendiente_firma"')

    def test_historial_no_muestra_solicitudes_de_otro_alumno(self):
        otro = User.objects.create_user("S24000002", password="x", rol=User.Rol.ALUMNO)
        self.client.force_login(otro)
        Estudiante.objects.create(
            user=otro,
            nombres="Luis",
            apellido_paterno="Ruiz",
            apellido_materno="Mora",
            matricula="S24000002",
            carrera=Estudiante.ProgramaEducativo.LIS,
            semestre=3,
            secretaria=self.secretaria,
            numero_bajas=0,
        )
        respuesta = self.client.get(reverse("estudiante:historial_solicitudes"))
        self.assertEqual(self.folios(respuesta), set())
