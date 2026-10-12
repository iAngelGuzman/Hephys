from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("solicitud", "0014_solicitud_lote_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="comprobantepago",
            name="folio",
            field=models.CharField(max_length=7, verbose_name="Folio de pago"),
        ),
    ]
