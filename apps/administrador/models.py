from django.db import models


class Carrera(models.Model):
    nombre = models.CharField(max_length=150, unique=True)
    clave = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.nombre


class HorarioExamen(models.Model):
    TIPO_EXAMEN_CHOICES = [
        ("ORD", "Ordinario"),
        ("EXT", "Extraordinario"),
        ("TIT", "Título"),
    ]

    carrera = models.ForeignKey(
        Carrera, on_delete=models.CASCADE, related_name="horarios"
    )
    nrc = models.CharField(max_length=10)
    ee_nombre = models.CharField(max_length=200)  # Experiencia Educativa
    profesor = models.CharField(max_length=200, blank=True, null=True)
    bloque_seccion = models.CharField(max_length=20, blank=True, null=True)
    salon = models.CharField(max_length=50, blank=True, null=True)
    hora = models.TimeField(null=True, blank=True)

    tipo_examen = models.CharField(
        max_length=3, choices=TIPO_EXAMEN_CHOICES, default="EXT"
    )
    fecha_examen = models.DateField()
    fecha_entrega_acta = models.DateField(null=True, blank=True)
    periodo = models.CharField(max_length=50, default="FEBRERO-JULIO 2026")

    class Meta:
        # Cada carrera tiene su propio calendario: el mismo NRC puede
        # publicarse en varias carreras sin que una borre a la otra.
        unique_together = ("carrera", "nrc", "tipo_examen", "periodo")

    def __str__(self):
        return (
            f"{self.nrc} - {self.ee_nombre} ({self.tipo_examen}): {self.fecha_examen}"
        )
