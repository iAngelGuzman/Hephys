from django.db import migrations


class Migration(migrations.Migration):
    """
    Quita la restricción única (estudiante, materia_nrc) de Solicitud.

    Con ella, un alumno solo podía tener UNA solicitud por NRC en toda su
    vida, y las vistas "reciclaban" la anterior (perdiendo su historial y a
    veces dejando el tipo equivocado). Ahora cada trámite es un registro
    nuevo y los duplicados activos se evitan en las vistas.

    Escrita a mano (no con makemigrations) a propósito: makemigrations
    también metería el cambio de ruta absoluta del FileField de
    ComprobantePago, que depende de la máquina y se corrige en otro paso.
    """

    dependencies = [
        ("solicitud", "0017_merge_folio_motivo_baja"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="solicitud",
            name="unique_solicitud_estudiante_materia",
        ),
    ]
