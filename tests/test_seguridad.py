"""
Pruebas de los requerimientos de seguridad del modelo relacional.

- CA-04: el folio se genera en el servidor y no es predecible.
- HU-25: la bitácora registra altas y cambios de estado y no se borra.
"""

from django.db.models import ProtectedError
from django.test import TestCase

from app.models import BitacoraTransaccional, Solicitud, User
from app.models.estudiante import Estudiante
from app.models.secretaria import Secretaria


class SeguridadTests(TestCase):
    def setUp(self):
        usuario_secretaria = User.objects.create_user(
            "secretaria-seguridad", password="x", rol=User.Rol.SECRETARIA_GRUPO
        )
        secretaria = Secretaria.objects.create(user=usuario_secretaria)
        usuario = User.objects.create_user(
            "S24000999", password="x", rol=User.Rol.ALUMNO
        )
        self.estudiante = Estudiante.objects.create(
            user=usuario,
            nombres="Ana",
            apellido_paterno="Pérez",
            apellido_materno="López",
            matricula="S24000999",
            carrera=Estudiante.ProgramaEducativo.LIS,
            semestre=3,
            secretaria=secretaria,
            numero_bajas=0,
        )

    def test_el_folio_se_genera_en_el_servidor_y_es_unico(self):
        primera = Solicitud.objects.create(
            estudiante=self.estudiante, tipo_tramite="constancia"
        )
        segunda = Solicitud.objects.create(
            estudiante=self.estudiante, tipo_tramite="justificante"
        )

        self.assertRegex(primera.folio, r"^HPH-\d{8}-[0-9A-F]{8}$")
        self.assertNotEqual(primera.folio, segunda.folio)

    def test_la_bitacora_registra_altas_y_cambios_de_estado(self):
        solicitud = Solicitud.objects.create(
            estudiante=self.estudiante,
            tipo_tramite="constancia",
            estado=Solicitud.Estado.PENDIENTE_ACADEMICA,
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

    def test_la_bitacora_impide_borrar_la_solicitud(self):
        solicitud = Solicitud.objects.create(
            estudiante=self.estudiante, tipo_tramite="constancia"
        )
        self.assertEqual(BitacoraTransaccional.objects.count(), 1)

        with self.assertRaises(ProtectedError):
            solicitud.delete()
