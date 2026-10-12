from django.urls import path
from . import views

app_name = "administrador"
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path(
        "configurar-altas-bajas/",
        views.configurar_altas_bajas,
        name="configurar_altas_bajas",
    ),
    path("configurar-examenes/", views.configurar_examenes, name="configurar_examenes"),
    path(
        "eliminar-horario-examenes/",
        views.eliminar_horario_examenes,
        name="eliminar_horario_examenes",
    ),
    path("subir-oferta/", views.subir_oferta_pdf, name="subir_oferta_pdf"),
    path("gestion-cupos/", views.gestion_cupos, name="gestion_cupos"),
    path("usuarios/", views.control_usuarios, name="control_usuarios"),
    path(
        "usuarios/cambiar-estado/<int:user_id>/",
        views.cambiar_estado_usuario,
        name="cambiar_estado_usuario",
    ),
    path("usuarios/crear/", views.crear_secretaria, name="crear_secretaria"),
    path("usuarios/editar/<int:user_id>/", views.editar_usuario, name="editar_usuario"),
    path("pendientes/", views.solicitudes_pendientes, name="solicitudes_pendientes"),
    path("historial/", views.historial_solicitudes, name="historial_solicitudes"),
    path("aprobar/<int:pk>/", views.aprobar_solicitud, name="aprobar_solicitud"),
    path("rechazar/<int:pk>/", views.rechazar_solicitud, name="rechazar_solicitud"),
]
