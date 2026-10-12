import django.db.models.deletion
from django.db import migrations, models

TIPOS = {
    "Baja de Experiencias Educativas": "baja",
    "Alta de Experiencias Educativas": "alta",
}
ESTADOS = {"aceptado": "aceptada", "rechazado": "rechazada"}


def convertir_valores(apps, schema_editor):
    Solicitud = apps.get_model("solicitud", "Solicitud")
    for viejo, nuevo in TIPOS.items():
        Solicitud.objects.filter(tipo_tramite=viejo).update(tipo_tramite=nuevo)
    for viejo, nuevo in ESTADOS.items():
        Solicitud.objects.filter(estado=viejo).update(estado=nuevo)


def revertir_valores(apps, schema_editor):
    Solicitud = apps.get_model("solicitud", "Solicitud")
    for viejo, nuevo in TIPOS.items():
        Solicitud.objects.filter(tipo_tramite=nuevo).update(tipo_tramite=viejo)
    for viejo, nuevo in ESTADOS.items():
        Solicitud.objects.filter(estado=nuevo).update(estado=viejo)


class Migration(migrations.Migration):
    """
    Solicitud:
    - tipo_examen -> tipo_tramite (también guarda altas y bajas) con valores
      cortos: "Baja de Experiencias Educativas" -> "baja", "Alta ..." -> "alta".
    - estados en femenino (la solicitud): aceptado -> aceptada,
      rechazado -> rechazada.
    - ruta_archivo_temporal -> ruta_horario (no era temporal).
    Los datos existentes se convierten; nada se pierde.
    """

    dependencies = [
        ("solicitud", "0019_storage_comprobantes_sin_ruta_absoluta"),
        ("estudiante", "0009_renombrar_student_a_estudiante"),
    ]

    operations = [
        migrations.AlterField(
            model_name="solicitud",
            name="estudiante",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="solicitudes",
                to="estudiante.estudiante",
            ),
        ),
        migrations.RenameField("solicitud", "tipo_examen", "tipo_tramite"),
        migrations.RenameField("solicitud", "ruta_archivo_temporal", "ruta_horario"),
        # Primero se convierten los valores largos y después se acorta la columna.
        migrations.RunPython(convertir_valores, revertir_valores),
        migrations.AlterField(
            model_name="solicitud",
            name="tipo_tramite",
            field=models.CharField(
                choices=[
                    ("extraordinario", "Extraordinario"),
                    ("suficiencia", "Título de Suficiencia"),
                    ("baja", "Baja de Experiencias Educativas"),
                    ("alta", "Alta de Experiencias Educativas"),
                ],
                default="extraordinario",
                max_length=20,
                verbose_name="Tipo de trámite",
            ),
        ),
        migrations.AlterField(
            model_name="solicitud",
            name="estado",
            field=models.CharField(
                choices=[
                    ("pendiente_academica", "Pendiente de Revisión Académica"),
                    ("rechazada_academica", "Rechazada por Secretaría Académica"),
                    ("pendiente", "Pendiente con Secretario"),
                    ("aceptada", "Aceptada"),
                    ("rechazada", "Rechazada"),
                ],
                default="pendiente",
                max_length=20,
            ),
        ),
    ]
