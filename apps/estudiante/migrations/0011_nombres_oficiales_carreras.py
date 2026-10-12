from django.db import migrations, models

NOMBRES = {
    "Ingeniería de Software": "Lic. en Ingeniería de Software",
    "Ingeniería en Sistemas y Tecnologías de la Información": (
        "Lic. en Ingeniería en Sistemas y Tecnologías de la Información"
    ),
    "Ingeniería de Ciberseguridad e Infraestructura de Cómputo": (
        "Lic. en Ingeniería de Ciberseguridad e Infraestructura de Cómputo"
    ),
    "Ingeniería en Ciencia de Datos": "Lic. en Ingeniería en Ciencia de Datos",
}

SIGLAS = {
    "LIS": "Lic. en Ingeniería de Software",
    "LISTI": "Lic. en Ingeniería en Sistemas y Tecnologías de la Información",
    "LICIC": "Lic. en Ingeniería de Ciberseguridad e Infraestructura de Cómputo",
    "LINCID": "Lic. en Ingeniería en Ciencia de Datos",
}


def _renombrar(apps, equivalencias):
    """
    Cambia el nombre de la carrera en los datos que ya están guardados:
    alumnos, catálogo de experiencias educativas y carreras del calendario
    de exámenes. Sin esto, los registros viejos dejarían de coincidir con
    la carrera del alumno (oferta para altas y calendario de exámenes).
    """
    Estudiante = apps.get_model("estudiante", "Estudiante")
    ExperienciaEducativa = apps.get_model("solicitud", "ExperienciaEducativa")
    Carrera = apps.get_model("administrador", "Carrera")

    for anterior, nuevo in equivalencias.items():
        Estudiante.objects.filter(carrera=anterior).update(carrera=nuevo)
        ExperienciaEducativa.objects.filter(carrera=anterior).update(carrera=nuevo)
        if not Carrera.objects.filter(nombre=nuevo).exists():
            Carrera.objects.filter(nombre=anterior).update(nombre=nuevo)


def actualizar_nombres(apps, schema_editor):
    _renombrar(apps, NOMBRES)

    Carrera = apps.get_model("administrador", "Carrera")
    for sigla, nombre in SIGLAS.items():
        if not Carrera.objects.filter(nombre=nombre).exclude(clave=sigla).exists():
            Carrera.objects.filter(clave=sigla).update(nombre=nombre)


def revertir_nombres(apps, schema_editor):
    _renombrar(apps, {nuevo: anterior for anterior, nuevo in NOMBRES.items()})


class Migration(migrations.Migration):

    dependencies = [
        ("estudiante", "0010_quitar_carreras_no_vigentes"),
        ("solicitud", "0021_quitar_campos_sin_uso_comprobantepago"),
        ("administrador", "0002_horario_por_carrera"),
    ]

    operations = [
        migrations.AlterField(
            model_name="estudiante",
            name="carrera",
            field=models.CharField(
                choices=[
                    (
                        "Lic. en Ingeniería de Software",
                        "Lic. en Ingeniería de Software",
                    ),
                    (
                        "Lic. en Ingeniería en Sistemas y Tecnologías de la Información",
                        "Lic. en Ingeniería en Sistemas y Tecnologías de la Información",
                    ),
                    (
                        "Lic. en Ingeniería de Ciberseguridad e Infraestructura de Cómputo",
                        "Lic. en Ingeniería de Ciberseguridad e Infraestructura de Cómputo",
                    ),
                    (
                        "Lic. en Ingeniería en Ciencia de Datos",
                        "Lic. en Ingeniería en Ciencia de Datos",
                    ),
                ],
                max_length=100,
                verbose_name="Programa Educativo / Carrera",
            ),
        ),
        migrations.RunPython(actualizar_nombres, revertir_nombres),
    ]
