from django.db import models
from app.models.usuario import User
from app.models.secretaria import Secretaria


class Estudiante(models.Model):
    class ProgramaEducativo(models.TextChoices):
        LIS = (
            "Lic. en Ingeniería de Software",
            "Lic. en Ingeniería de Software",
        )
        IT = (
            "Lic. en Ingeniería en Sistemas y Tecnologías de la Información",
            "Lic. en Ingeniería en Sistemas y Tecnologías de la Información",
        )
        LICIC = (
            "Lic. en Ingeniería de Ciberseguridad e Infraestructura de Cómputo",
            "Lic. en Ingeniería de Ciberseguridad e Infraestructura de Cómputo",
        )
        LINCID = (
            "Lic. en Ingeniería en Ciencia de Datos",
            "Lic. en Ingeniería en Ciencia de Datos",
        )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="perfil_estudiante",
        verbose_name="Usuario",
    )

    nombres = models.CharField(max_length=50, verbose_name="Nombre(s)")
    apellido_paterno = models.CharField(max_length=50, verbose_name="Apellido Paterno")
    apellido_materno = models.CharField(max_length=50, verbose_name="Apellido Materno")

    matricula = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Matrícula",
    )

    carrera = models.CharField(
        max_length=100,
        choices=ProgramaEducativo.choices,
        verbose_name="Programa Educativo / Carrera",
    )

    semestre = models.PositiveIntegerField(default=1)

    secretaria = models.ForeignKey(
        Secretaria,
        on_delete=models.PROTECT,
        related_name="estudiantes_asignados",
        verbose_name="Secretario(a) de Grupo",
    )

    numero_bajas = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "estudiantes"
        verbose_name = "estudiante"
        verbose_name_plural = "estudiantes"
        ordering = ["matricula"]

    def __str__(self):
        return self.matricula
