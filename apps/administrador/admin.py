from django.contrib import admin

from .models import Carrera, HorarioExamen


@admin.register(Carrera)
class CarreraAdmin(admin.ModelAdmin):
    list_display = ("nombre", "clave")


@admin.register(HorarioExamen)
class HorarioExamenAdmin(admin.ModelAdmin):
    list_display = (
        "nrc",
        "ee_nombre",
        "carrera",
        "tipo_examen",
        "fecha_examen",
        "periodo",
    )
    list_filter = ("carrera", "tipo_examen", "periodo")
    search_fields = ("nrc", "ee_nombre", "profesor")
