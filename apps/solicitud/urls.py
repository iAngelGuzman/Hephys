from django.urls import path
from . import views

app_name = "solicitud"

urlpatterns = [
    path(
        "lista-tramites/",
        views.lista_tramites,
        name="lista_tramites",
    ),
]
