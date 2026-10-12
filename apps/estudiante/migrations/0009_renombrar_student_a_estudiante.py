import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Student -> Estudiante y related_name student_profile -> perfil_estudiante.
    Es un RENOMBRE (la tabla y los datos se conservan), no borrar y crear.
    """

    dependencies = [
        ("estudiante", "0008_alter_student_carrera"),
        ("secretaria", "0004_renombrar_secretary_a_secretaria"),
        # Las migraciones anteriores de solicitud apuntan a "estudiante.student":
        # deben correr antes del renombre.
        ("solicitud", "0019_storage_comprobantes_sin_ruta_absoluta"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameModel(old_name="Student", new_name="Estudiante"),
        migrations.AlterField(
            model_name="estudiante",
            name="user",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="perfil_estudiante",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Usuario",
            ),
        ),
        migrations.AlterField(
            model_name="estudiante",
            name="secretaria",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="estudiantes_asignados",
                to="secretaria.secretaria",
                verbose_name="Secretario(a) de Grupo",
            ),
        ),
    ]
