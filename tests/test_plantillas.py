from django.test import TestCase


class PlantillasTests(TestCase):
    """Django no entiende una etiqueta {{ }} o {% %} partida en dos líneas:
    la muestra tal cual en la página. Esto lo detecta en todas las plantillas."""

    def test_ninguna_etiqueta_partida_en_varias_lineas(self):
        import re
        from pathlib import Path

        from django.conf import settings

        partida = re.compile(r"\{\{[^}]*\n[^}]*\}\}|\{%[^%]*\n[^%]*%\}")
        rotas = [
            f"{ruta.relative_to(settings.BASE_DIR)}:{texto[:m.start()].count(chr(10)) + 1}"
            for ruta in Path(settings.BASE_DIR).glob("**/templates/**/*.html")
            if "venv" not in ruta.parts
            for texto in [ruta.read_text(encoding="utf-8")]
            for m in partida.finditer(texto)
        ]
        self.assertEqual(rotas, [])

    def test_ningun_atributo_html_fuera_de_su_etiqueta(self):
        """Detecta un atributo suelto como texto (p. ej. si se borró el "<a")."""
        import re
        from html.parser import HTMLParser
        from pathlib import Path

        from django.conf import settings

        class Revisor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.sueltos = []

            def handle_data(self, data):
                if re.search(r'\b(href|class|src|type|name|id)="', data):
                    self.sueltos.append(self.getpos()[0])

        problemas = []
        for ruta in Path(settings.BASE_DIR).glob("**/templates/**/*.html"):
            if "venv" in ruta.parts:
                continue
            texto = re.sub(
                r"\{%.*?%\}|\{\{.*?\}\}|\{#.*?#\}",
                "",
                ruta.read_text(encoding="utf-8"),
                flags=re.S,
            )
            revisor = Revisor()
            revisor.feed(texto)
            problemas += [
                f"{ruta.relative_to(settings.BASE_DIR)} (~línea {linea})"
                for linea in revisor.sueltos
            ]
        self.assertEqual(problemas, [])
