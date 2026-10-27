"""Pruebas del panel de la Secretaría Académica (paso 3 de la auditoría)."""

import json
from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from app.models.estudiante import Estudiante
from app.models.secretaria import Secretaria
from app.models.solicitud import (
    CalendarioMatricula,
    ExperienciaEducativa,
    ExperienciaEducativaOferta,
    PeriodoTramite,
    Solicitud,
)
from app.models.usuario import User

SIN_MANIFEST = {
    "STORAGES": {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
}


def pdf_falso(nombre="oferta.pdf"):
    return SimpleUploadedFile(nombre, b"esto no es un pdf", content_type="application/pdf")


@override_settings(**SIN_MANIFEST)
class AdministradorTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user("admin", password="x", rol=User.Rol.ADMINISTRADOR)
        self.client.force_login(self.admin)

    # --- Rechazar ----------------------------------------------------------

    def _solicitud(self, estado):
        secretaria = Secretaria.objects.create(
            user=User.objects.create_user("sec", password="x", rol=User.Rol.SECRETARIA_GRUPO)
        )
        estudiante = Estudiante.objects.create(
            user=User.objects.create_user("S24000001", password="x"),
            nombres="Ana", apellido_paterno="P", apellido_materno="L",
            matricula="S24000001", carrera=Estudiante.ProgramaEducativo.LIS,
            secretaria=secretaria,
        )
        return Solicitud.objects.create(
            estudiante=estudiante, tipo_tramite="baja", estado=estado, materia_nrc="1"
        )

    def _rechazar(self, solicitud, cuerpo):
        return self.client.post(
            reverse("administrador:rechazar_solicitud", args=[solicitud.pk]),
            data=cuerpo,
            content_type="application/json",
        )

    def test_rechazar_ya_procesada_responde_409(self):
        solicitud = self._solicitud(Solicitud.Estado.PENDIENTE)
        respuesta = self._rechazar(solicitud, json.dumps({"motivo": "x"}))
        self.assertEqual(respuesta.status_code, 409)
        self.assertIn("ya fue procesada", respuesta.json()["error"])

    def test_rechazar_con_json_que_no_es_objeto(self):
        solicitud = self._solicitud(Solicitud.Estado.PENDIENTE_ACADEMICA)
        self.assertEqual(self._rechazar(solicitud, "[1, 2]").status_code, 400)

    def test_rechazar_solo_por_post(self):
        solicitud = self._solicitud(Solicitud.Estado.PENDIENTE_ACADEMICA)
        respuesta = self.client.get(reverse("administrador:rechazar_solicitud", args=[solicitud.pk]))
        self.assertEqual(respuesta.status_code, 405)

    def test_rechazar_valido(self):
        solicitud = self._solicitud(Solicitud.Estado.PENDIENTE_ACADEMICA)
        self.assertEqual(self._rechazar(solicitud, json.dumps({"motivo": "x"})).status_code, 200)
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, Solicitud.Estado.RECHAZADA_ACADEMICA)

    # --- Periodos y calendario por matrícula -------------------------------

    def test_periodo_con_cierre_antes_de_apertura_se_rechaza(self):
        url = reverse("administrador:configurar_altas_bajas")
        respuesta = self.client.post(url, {
            "tipo": "altas",
            "altas-fecha_apertura": "2026-12-01T10:00",
            "altas-fecha_cierre": "2026-01-01T10:00",
        })
        self.assertContains(respuesta, "posterior a la de apertura")
        periodo = PeriodoTramite.objects.get(tipo_tramite="altas")
        self.assertLess(periodo.fecha_apertura, periodo.fecha_cierre + timedelta(seconds=1))

    def test_periodo_guardado_se_muestra_en_el_campo(self):
        url = reverse("administrador:configurar_altas_bajas")
        self.client.post(url, {
            "tipo": "altas",
            "altas-fecha_apertura": "2026-08-01T08:00",
            "altas-fecha_cierre": "2026-08-10T18:00",
        })
        self.assertContains(self.client.get(url), 'value="2026-08-01T08:00"')

    def _calendario(self, prefijo, apertura, cierre):
        return self.client.post(reverse("administrador:configurar_altas_bajas"), {
            "tipo": "calendario_matricula",
            "prefijo_matricula": prefijo,
            "fecha_apertura": apertura,
            "fecha_cierre": cierre,
        })

    def test_calendario_valida_prefijo_y_fechas(self):
        self.client.post(reverse("administrador:configurar_altas_bajas"), {
            "tipo": "altas",
            "altas-fecha_apertura": "2026-08-01T08:00",
            "altas-fecha_cierre": "2026-08-10T18:00",
        })
        self.assertContains(self._calendario("23", "2026-08-02T08:00", "2026-08-03T08:00"), "letra S")
        self.assertContains(self._calendario("S23", "2026-07-02T08:00", "2026-08-03T08:00"), "dentro del periodo")
        self.assertContains(self._calendario("S23", "fecha-mala", "2026-08-03T08:00"), "error-campo")
        self.assertEqual(CalendarioMatricula.objects.count(), 0)

        self._calendario("s23", "2026-08-02T08:00", "2026-08-03T08:00")
        calendario = CalendarioMatricula.objects.get()
        self.assertEqual((calendario.prefijo_matricula, calendario.tipo_tramite), ("S23", "altas"))

    def test_eliminar_calendario_con_id_invalido(self):
        respuesta = self.client.post(
            reverse("administrador:configurar_altas_bajas"),
            {"tipo": "eliminar_calendario", "calendario_id": "abc"},
            follow=True,
        )
        self.assertContains(respuesta, "ya no existe")

    # --- Archivos PDF ------------------------------------------------------

    def test_oferta_rechaza_archivo_que_no_es_pdf(self):
        respuesta = self.client.post(
            reverse("administrador:subir_oferta_pdf"), {"archivo_pdf": pdf_falso()}
        )
        self.assertContains(respuesta, "no es un PDF válido")

    def test_calendario_examenes_valida_carrera_y_pdf(self):
        url = reverse("administrador:configurar_examenes")
        respuesta = self.client.post(
            url, {"carrera_code": "XYZ", "archivo_horario": pdf_falso()}, follow=True
        )
        self.assertContains(respuesta, "Carrera no válida")
        respuesta = self.client.post(
            url, {"carrera_code": "LIS", "archivo_horario": pdf_falso()}, follow=True
        )
        self.assertContains(respuesta, "no es un PDF válido")

    # --- Cupos -------------------------------------------------------------

    def test_cupos_no_redirige_a_otro_sitio(self):
        ee = ExperienciaEducativa.objects.create(nombre="Calculo", carrera="x")
        ExperienciaEducativaOferta.objects.create(experiencia_educativa=ee, nrc="1", cupo=1)
        respuesta = self.client.post(
            reverse("administrador:gestion_cupos"),
            {"nrc": "1", "cupo": "3"},
            HTTP_REFERER="https://sitio-malicioso.com/",
        )
        self.assertRedirects(respuesta, reverse("administrador:gestion_cupos"))
