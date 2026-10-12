from django.contrib.auth.views import LogoutView
from django.urls import path
from . import views

app_name = "usuario"
urlpatterns = [
    path(
        "login/",
        views.login_usuario,
        name="login",
    ),
    path(
        "logout/",
        LogoutView.as_view(next_page="usuario:login"),
        name="logout",
    ),
    path("registro/", views.registrar_alumno, name="registrar_alumno"),
]
