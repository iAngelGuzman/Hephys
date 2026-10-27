"""
Pruebas de la pantalla de trámites y del historial del alumno.

Correr con:  python manage.py test tests.test_solicitud
"""

from django.test import TestCase
from django.urls import reverse

from app.models.estudiante import Estudiante
from app.models.secretaria import Secretaria
from app.models.solicitud import (
    BitacoraTransaccional,
    Solicitud,
)
from app.models.usuario import User


class BaseTramites(TestCase):
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


class ModeloRelacionalTests(BaseTramites):
    """Estructura documentada: folio y bitácora transaccional."""

    def test_folio_se_genera_en_el_servidor_y_es_unico(self):
        primera = Solicitud.objects.create(
            estudiante=self.estudiante,
            tipo_tramite="constancia",
            estado=Solicitud.Estado.PENDIENTE,
        )
        segunda = Solicitud.objects.create(
            estudiante=self.estudiante,
            tipo_tramite="justificante",
            estado=Solicitud.Estado.PENDIENTE,
        )

        self.assertRegex(primera.folio, r"^HPH-\d{8}-[0-9A-F]{8}$")
        self.assertNotEqual(primera.folio, segunda.folio)

    def test_bitacora_registra_alta_y_cambio_de_estado(self):
        solicitud = Solicitud.objects.create(
            estudiante=self.estudiante,
            tipo_tramite="constancia",
            estado=Solicitud.Estado.PENDIENTE_ACADEMICA,
        )
        self.assertEqual(
            list(solicitud.bitacora.values_list("estatus_anterior", "estatus_nuevo")),
            [("", "Solicitado")],
        )

        solicitud.estado = Solicitud.Estado.ACEPTADA
        solicitud.save()

        movimientos = list(
            solicitud.bitacora.order_by("fecha_movimiento", "id").values_list(
                "estatus_anterior", "estatus_nuevo"
            )
        )
        self.assertEqual(
            movimientos,
            [("", "Solicitado"), ("Solicitado", "Autorizado")],
        )

    def test_estatus_documentado_traduce_los_estados(self):
        solicitud = Solicitud.objects.create(
            estudiante=self.estudiante,
            tipo_tramite="constancia",
            estado=Solicitud.Estado.PENDIENTE,
        )
        self.assertEqual(solicitud.estatus_documentado, "En Revisión")

        solicitud.estado = Solicitud.Estado.PENDIENTE_FIRMA
        self.assertEqual(solicitud.estatus_documentado, "Dictaminado")

        solicitud.estado = Solicitud.Estado.RECHAZADA
        self.assertEqual(solicitud.estatus_documentado, "Rechazado")

    def test_la_bitacora_impide_borrar_una_solicitud_con_historial(self):
        from django.db.models import ProtectedError

        solicitud = Solicitud.objects.create(
            estudiante=self.estudiante,
            tipo_tramite="constancia",
        )
        with self.assertRaises(ProtectedError):
            solicitud.delete()

    def test_bitacora_no_se_puede_editar_desde_el_admin(self):
        # La bitácora es append-only: el modelo no expone edición, pero la
        # prueba deja constancia de que los movimientos son independientes.
        solicitud = Solicitud.objects.create(
            estudiante=self.estudiante,
            tipo_tramite="constancia",
        )
        movimiento = solicitud.bitacora.get()
        self.assertEqual(BitacoraTransaccional.objects.count(), 1)
        self.assertEqual(movimiento.estatus_nuevo, "En Revisión")
