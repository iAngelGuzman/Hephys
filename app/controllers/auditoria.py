"""
Bitácora transaccional de solicitudes (HU-25).

El usuario responsable se guarda en una ``ContextVar`` que llena el
middleware en cada petición. Así cualquier cambio de estado —venga de la
vista que venga— queda atribuido a la persona autenticada, sin tener que
pasar el ``request`` por todos los servicios.

En procesos sin petición (comandos, tareas) el usuario queda en ``None`` y la
bitácora registra el movimiento como automático.
"""

import contextvars

_usuario_actual = contextvars.ContextVar("hephys_usuario_actual", default=None)


def establecer_usuario_actual(usuario):
    """Guarda el usuario de la petición actual. Regresa el token."""
    return _usuario_actual.set(usuario)


def restablecer_usuario_actual(token):
    """Restaura el valor anterior al terminar la petición."""
    _usuario_actual.reset(token)


def obtener_usuario_actual():
    """Usuario autenticado de la petición, o None."""
    usuario = _usuario_actual.get()
    if usuario is not None and getattr(usuario, "is_authenticated", False):
        return usuario
    return None


def registrar_movimiento(
    solicitud,
    estatus_anterior,
    estatus_nuevo,
    comentarios="",
    usuario=None,
):
    """
    Inserta un renglón en ``bitacora_transaccional``.

    No usa ``update_or_create`` ni permite editar: la bitácora es de solo
    anexar. Se llama desde la señal ``post_save`` de ``Solicitud`` y desde los
    servicios que cambian el estado.
    """
    # Import local para que este módulo pueda cargarse desde señales sin
    # provocar importaciones circulares.
    from app.models.solicitud import BitacoraTransaccional

    if usuario is None:
        usuario = obtener_usuario_actual()

    return BitacoraTransaccional.objects.create(
        solicitud=solicitud,
        usuario_responsable=usuario,
        estatus_anterior=estatus_anterior or "",
        estatus_nuevo=estatus_nuevo or "",
        comentarios=comentarios or "",
    )
