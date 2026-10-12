import json

from django import template

register = template.Library()


@register.filter
def a_json(valor):
    """
    Convierte un valor de Python (lista, dict...) a texto JSON válido.

    El resultado NO se marca como seguro: Django lo escapa al ponerlo en un
    atributo HTML (data-horarios="{{ m.horarios|a_json }}"), así que ninguna
    comilla o "<" que venga del PDF puede romper el atributo. En JavaScript
    basta con JSON.parse(elemento.getAttribute("data-horarios")).

    Para bloques completos de datos usar el filtro nativo |json_script.
    """
    return json.dumps(valor, ensure_ascii=False)
