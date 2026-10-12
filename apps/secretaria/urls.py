from django.urls import path

from . import views

app_name = "secretaria"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path(
        "aprobar/<int:solicitud_id>/", views.aprobar_solicitud, name="aprobar_solicitud"
    ),
    path(
        "rechazar/<int:solicitud_id>/",
        views.rechazar_solicitud,
        name="rechazar_solicitud",
    ),
    path(
        "historial-solicitudes/",
        views.historial_solicitudes,
        name="historial_solicitudes",
    ),
]
