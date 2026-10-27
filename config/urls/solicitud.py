from django.urls import path
from app.views import tramites as views

app_name = "solicitud"

urlpatterns = [
    path(
        "lista-tramites/",
        views.lista_tramites,
        name="lista_tramites",
    ),
]
