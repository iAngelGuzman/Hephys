"""Pruebas del inicio de sesión (paso 3 de la auditoría)."""

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from app.controllers.limite_intentos import MAXIMO_INTENTOS_POR_IP, MAXIMO_INTENTOS_POR_USUARIO
from app.models.usuario import User

SIN_MANIFEST = {
    "STORAGES": {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
}


@override_settings(**SIN_MANIFEST)
class LimiteIntentosTests(TestCase):
    def setUp(self):
        cache.clear()
        User.objects.create_user("secre", password="Clave12345!", rol=User.Rol.SECRETARIA_GRUPO)

    def _intentar(self, password="mala", **encabezados):
        return self.client.post(
            reverse("usuario:login"), {"matricula": "secre", "password": password}, **encabezados
        )

    def test_bloquea_por_ip_despues_de_varios_intentos(self):
        for _ in range(MAXIMO_INTENTOS_POR_IP):
            self._intentar()
        self.assertEqual(self._intentar(password="Clave12345!").status_code, 429)

    def test_cambiar_x_forwarded_for_no_evita_el_bloqueo(self):
        for numero in range(MAXIMO_INTENTOS_POR_IP):
            self._intentar(HTTP_X_FORWARDED_FOR=f"10.0.0.{numero}")
        self.assertEqual(self._intentar(HTTP_X_FORWARDED_FOR="10.0.0.99").status_code, 429)

    def test_bloquea_por_usuario_aunque_cambie_la_ip(self):
        for numero in range(MAXIMO_INTENTOS_POR_USUARIO):
            self._intentar(HTTP_CF_CONNECTING_IP=f"10.0.1.{numero}")
        self.assertEqual(
            self._intentar(password="Clave12345!", HTTP_CF_CONNECTING_IP="10.0.2.1").status_code,
            429,
        )

    def test_login_correcto_limpia_los_intentos(self):
        for _ in range(MAXIMO_INTENTOS_POR_IP - 1):
            self._intentar()
        self.assertEqual(self._intentar(password="Clave12345!").status_code, 302)
        self.client.logout()
        self.assertEqual(self._intentar().status_code, 200)
