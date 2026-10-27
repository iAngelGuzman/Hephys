from django.contrib import admin
from app.models.secretaria import Secretaria


@admin.register(Secretaria)
class SecretariaAdmin(admin.ModelAdmin):
    list_display = ("user",)
