from django.contrib import admin

from app.models.solicitud import (
    BitacoraTransaccional,
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


class BitacoraInline(admin.TabularInline):
    model = BitacoraTransaccional
    extra = 0
    can_delete = False
    fields = (
        "estatus_anterior",
        "estatus_nuevo",
        "usuario_responsable",
        "comentarios",
        "fecha_movimiento",
    )
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        # La bitácora es de solo anexar: no se captura a mano.
        return False


@admin.register(Solicitud)
class SolicitudAdmin(admin.ModelAdmin):
    list_display = (
        "folio",
        "id",
        "estudiante",
        "tipo_tramite",
        "estatus_documentado",
        "estado",
        "fecha_solicitud",
    )
    list_filter = ("tipo_tramite", "estado")
    search_fields = (
        "folio",
        "estudiante__matricula",
        "materia_nrc",
        "materia_nombre",
    )
    list_select_related = ("estudiante",)
    readonly_fields = ("folio", "fecha_solicitud", "fecha_actualizacion")
    inlines = [
        ComprobantePagoInline,
        BitacoraInline,
    ]

    @admin.display(description="Estatus")
    def estatus_documentado(self, obj):
        return obj.estatus_documentado


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


@admin.register(BitacoraTransaccional)
class BitacoraTransaccionalAdmin(admin.ModelAdmin):
    list_display = (
        "solicitud",
        "estatus_anterior",
        "estatus_nuevo",
        "usuario_responsable",
        "fecha_movimiento",
    )
    list_filter = ("estatus_nuevo",)
    search_fields = ("solicitud__folio", "comentarios")
    list_select_related = ("solicitud", "usuario_responsable")
    date_hierarchy = "fecha_movimiento"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
