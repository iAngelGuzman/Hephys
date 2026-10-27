from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

from app.views.salud import health

urlpatterns = [
    path("admin/", admin.site.urls),
    # Sonda de salud (con y sin barra final: los monitores usan /health).
    path("health", health, name="health"),
    path("health/", health, name="health_con_barra"),
    path("", RedirectView.as_view(pattern_name="usuario:login")),
    path("solicitudes/", include("config.urls.solicitud")),
    path("", include("config.urls.usuario")),
    path("secretaria/", include("config.urls.secretaria")),
    path("estudiante/", include("config.urls.estudiante")),
    path("administrador/", include("config.urls.administrador")),
]
