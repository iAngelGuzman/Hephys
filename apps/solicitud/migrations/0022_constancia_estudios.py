from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("solicitud", "0021_quitar_campos_sin_uso_comprobantepago"),
    ]

    operations = [
        migrations.AddField(
            model_name="solicitud",
            name="motivo_constancia",
            field=models.TextField(
                blank=True,
                help_text="Para qué necesita el alumno la constancia de estudios.",
                null=True,
                verbose_name="Motivo de la constancia",
            ),
        ),
        migrations.AlterField(
            model_name="solicitud",
            name="tipo_tramite",
            field=models.CharField(
                choices=[
                    ("extraordinario", "Extraordinario"),
                    ("suficiencia", "Título de Suficiencia"),
                    ("baja", "Baja de Experiencias Educativas"),
                    ("alta", "Alta de Experiencias Educativas"),
                    ("constancia", "Constancia de Estudios"),
                ],
                default="extraordinario",
                max_length=20,
                verbose_name="Tipo de trámite",
            ),
        ),
    ]
