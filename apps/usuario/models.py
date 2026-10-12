from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    class Rol(models.TextChoices):
        ALUMNO = "alumno", "Alumno"
        SECRETARIA_GRUPO = "secretaria_grupo", "Secretaría de grupo"
        ADMINISTRADOR = "administrador", "Secretaría Académica"

    rol = models.CharField(
        max_length=20,
        choices=Rol.choices,
        default=Rol.ALUMNO
    )

    def __str__(self):
        return f"{self.username} - {self.rol}" 