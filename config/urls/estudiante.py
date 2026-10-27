from django.urls import path
from app.views import estudiante as views

app_name = "estudiante"

urlpatterns = [
    path("mis-solicitudes/", views.mis_solicitudes, name="mis_solicitudes"),
    path("historial/", views.historial_solicitudes, name="historial_solicitudes"),
    path(
        "ver-horario/<int:solicitud_id>/",
        views.ver_horario_pdf,
        name="ver_horario_pdf",
    ),
    path("ver-comprobante/", views.ver_comprobante_pdf, name="ver_comprobante_pdf"),
    path(
        "ver-documento-medico/<int:solicitud_id>/",
        views.ver_documento_medico,
        name="ver_documento_medico",
    ),
]
