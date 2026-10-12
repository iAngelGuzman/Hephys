from django.db import models
from apps.usuario.models import User


class Secretaria(models.Model):

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="perfil_secretaria"
    )

    class Meta:
        verbose_name = "Secretaria"
        verbose_name_plural = "Secretarias"

    def __str__(self):
        return self.user.get_full_name() or self.user.username
