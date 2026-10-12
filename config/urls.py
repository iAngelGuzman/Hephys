from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(pattern_name="usuario:login")),
    path("solicitudes/", include("apps.solicitud.urls")),
    path("", include("apps.usuario.urls")),
    path("secretaria/", include("apps.secretaria.urls")),
    path("estudiante/", include("apps.estudiante.urls")),
    path("administrador/", include("apps.administrador.urls")),
]
