from django.db import migrations


class Migration(migrations.Migration):
    """
    Quita de ComprobantePago los campos que ninguna pantalla ni vista usa:
    nombre_declarado, monto y verificado. La papeleta se valida con el folio
    y el archivo; la aprobación queda en el estado de la Solicitud.
    """

    dependencies = [
        ("solicitud", "0020_tipo_tramite_estados_y_ruta_horario"),
    ]

    operations = [
        migrations.RemoveField(model_name="comprobantepago", name="nombre_declarado"),
        migrations.RemoveField(model_name="comprobantepago", name="monto"),
        migrations.RemoveField(model_name="comprobantepago", name="verificado"),
    ]
