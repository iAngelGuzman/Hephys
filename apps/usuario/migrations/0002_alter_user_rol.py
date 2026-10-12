from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [

        ('usuario', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(

            model_name='user',
            name='rol',
            field=models.CharField(choices=[('alumno', 'Alumno'), ('secretaria_grupo', 'Secretaría de grupo'), ('administrador', 'Secretaría Académica')], default='alumno', max_length=20),
        ),
    ]
