"""Pruebas de la sonda de salud (``/health``)."""

from unittest import mock

from django.test import TestCase


class HealthTests(TestCase):
    def test_responde_ok_con_y_sin_barra_final(self):
        for url in ("/health", "/health/"):
            with self.subTest(url=url):
                respuesta = self.client.get(url)
                self.assertEqual(respuesta.status_code, 200)
                self.assertEqual(
                    respuesta.json(),
                    {"status": "ok", "database": "ok"},
                )

    def test_responde_503_si_la_base_de_datos_falla(self):
        with mock.patch(
            "app.views.salud.base_de_datos_operativa", return_value=False
        ):
            respuesta = self.client.get("/health")

        self.assertEqual(respuesta.status_code, 503)
        self.assertEqual(
            respuesta.json(),
            {"status": "error", "database": "unavailable"},
        )
