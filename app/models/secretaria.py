from django.db import models
from app.models.usuario import User


class Secretaria(models.Model):

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="perfil_secretaria"
    )

    class Meta:
        db_table = "secretarias"
        verbose_name = "Secretaria"
        verbose_name_plural = "Secretarias"

    def __str__(self):
        return self.user.get_full_name() or self.user.username
