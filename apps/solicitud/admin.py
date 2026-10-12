from django.contrib import admin

from .models import (
    CalendarioMatricula,
    ComprobantePago,
    ExperienciaEducativa,
    ExperienciaEducativaOferta,
    PeriodoTramite,
    Solicitud,
)


@admin.register(ExperienciaEducativa)
class ExperienciaEducativaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "carrera", "creditos", "tiene_prerequisito")
    search_fields = ("nombre", "carrera")
    list_filter = ("carrera", "tiene_prerequisito")


@admin.register(ExperienciaEducativaOferta)
class ExperienciaEducativaOfertaAdmin(admin.ModelAdmin):
    list_display = ("nrc", "nombre_materia", "docente", "bloque_seccion", "cupo")
    search_fields = ("nrc", "experiencia_educativa__nombre", "docente")
    list_filter = ("bloque_seccion",)
    list_select_related = ("experiencia_educativa",)

    @admin.display(description="Nombre de la Experiencia Educativa")
    def nombre_materia(self, obj):
        return obj.experiencia_educativa.nombre


class ComprobantePagoInline(admin.TabularInline):
    model = ComprobantePago
    extra = 0
    fields = ("folio", "archivo", "fecha_subida")
    readonly_fields = ("fecha_subida",)


@admin.register(Solicitud)
class SolicitudAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "estudiante",
        "tipo_tramite",
        "materia_nrc",
        "materia_nombre",
        "estado",
        "fecha_solicitud",
    )
    list_filter = ("tipo_tramite", "estado")
    search_fields = ("estudiante__matricula", "materia_nrc", "materia_nombre")
    list_select_related = ("estudiante",)
    inlines = [ComprobantePagoInline]


@admin.register(PeriodoTramite)
class PeriodoTramiteAdmin(admin.ModelAdmin):
    list_display = ("tipo_tramite", "fecha_apertura", "fecha_cierre")


@admin.register(CalendarioMatricula)
class CalendarioMatriculaAdmin(admin.ModelAdmin):
    list_display = (
        "tipo_tramite",
        "prefijo_matricula",
        "fecha_apertura",
        "fecha_cierre",
    )
