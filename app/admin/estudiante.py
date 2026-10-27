from django.contrib import admin
from app.models.estudiante import Estudiante


@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    list_display = (
        "matricula",
        "nombres",
        "apellido_paterno",
        "carrera",
        "secretaria",
        "numero_bajas",
    )
    search_fields = ("matricula", "nombres", "apellido_paterno")
    list_filter = ("carrera", "numero_bajas")
