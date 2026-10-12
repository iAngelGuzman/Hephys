from django.contrib import admin
from .models import Secretaria


@admin.register(Secretaria)
class SecretariaAdmin(admin.ModelAdmin):
    list_display = ("user",)
