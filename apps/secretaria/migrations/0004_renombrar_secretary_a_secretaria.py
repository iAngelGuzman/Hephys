import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Secretary -> Secretaria y related_name secretary_profile -> perfil_secretaria.
    Es un RENOMBRE (la tabla y los datos se conservan), no borrar y crear.
    """

    dependencies = [
        ("secretaria", "0003_remove_secretary_nombre_area"),
        # Las migraciones anteriores de estudiante apuntan a "secretaria.secretary":
        # deben correr antes del renombre.
        ("estudiante", "0008_alter_student_carrera"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameModel(old_name="Secretary", new_name="Secretaria"),
        migrations.AlterField(
            model_name="secretaria",
            name="user",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="perfil_secretaria",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
