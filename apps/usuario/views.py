from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from apps.estudiante.models import Estudiante
from apps.usuario.forms import RegistroAlumnoForm
from apps.usuario.limite_intentos import (
    MINUTOS_BLOQUEO,
    esta_bloqueado,
    limpiar_intentos,
    registrar_intento_fallido,
)
from apps.usuario.models import User

PAGINA_INICIO_POR_ROL = {
    User.Rol.ALUMNO: "solicitud:lista_tramites",
    User.Rol.SECRETARIA_GRUPO: "secretaria:dashboard",
    User.Rol.ADMINISTRADOR: "administrador:dashboard",
}


def _url_siguiente_segura(request):
    """
    Regresa el ?next= (a dónde quería entrar antes de pedir login) solo si
    apunta a este mismo sitio; así nadie puede usar el login para mandar
    al usuario a una página externa.
    """
    siguiente = request.POST.get("next") or request.GET.get("next")
    if siguiente and url_has_allowed_host_and_scheme(
        siguiente,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return siguiente
    return None


def login_usuario(request):
    if request.user.is_authenticated and request.user.rol in PAGINA_INICIO_POR_ROL:
        return redirect(PAGINA_INICIO_POR_ROL[request.user.rol])

    if request.method != "POST":
        return render(request, "usuario/login.html")

    identificador = request.POST.get("matricula", "").strip()
    password = request.POST.get("password", "")

    if esta_bloqueado(request, identificador):
        messages.error(
            request,
            "Demasiados intentos fallidos. Espera "
            f"{MINUTOS_BLOQUEO} minutos antes de volver a intentarlo.",
        )
        return render(request, "usuario/login.html", status=429)

    # Los alumnos inician sesión con su matrícula (sin importar mayúsculas);
    # secretarias y administradores, con su nombre de usuario.
    estudiante = (
        Estudiante.objects.select_related("user")
        .filter(matricula__iexact=identificador)
        .first()
    )
    username = estudiante.user.username if estudiante else identificador

    usuario = None
    if username and password:
        usuario = authenticate(request, username=username, password=password)

    if usuario is None or usuario.rol not in PAGINA_INICIO_POR_ROL:
        registrar_intento_fallido(request, identificador)
        messages.error(request, "El usuario o la contraseña son incorrectos.")
        return render(request, "usuario/login.html")

    limpiar_intentos(request, identificador)
    login(request, usuario)
    return redirect(
        _url_siguiente_segura(request) or PAGINA_INICIO_POR_ROL[usuario.rol]
    )


def registrar_alumno(request):
    exito = False
    if request.method == "POST":
        form = RegistroAlumnoForm(request.POST)
        if form.is_valid():
            form.save()
            exito = True
            form = RegistroAlumnoForm()
    else:
        form = RegistroAlumnoForm()

    return render(request, "usuario/registrar_alumno.html", {"form": form, "exito": exito})
