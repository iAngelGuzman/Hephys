import apps.solicitud.models
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    El FileField de ComprobantePago ahora usa una función de storage
    (apps.solicitud.models.storage_comprobantes) en lugar de una ruta
    absoluta. No cambia nada en la base de datos ni mueve archivos: solo
    evita que cada computadora genere su propia migración.
    """

    dependencies = [
        ("solicitud", "0018_quitar_unique_solicitud_estudiante_materia"),
    ]

    operations = [
        migrations.AlterField(
            model_name="comprobantepago",
            name="archivo",
            field=models.FileField(
                storage=apps.solicitud.models.storage_comprobantes,
                upload_to="",
                verbose_name="Papeleta de pago",
            ),
        ),
    ]
