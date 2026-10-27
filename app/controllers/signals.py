"""
Señales que mantienen la bitácora al día sin tocar cada vista.

* Al crear una solicitud se registra el movimiento inicial.
* Al cambiar ``Solicitud.estado`` se registra el tránsito con el usuario que
  hizo el cambio (lo toma ``AuditoriaMiddleware``).

La bitácora se escribe en la misma transacción que el cambio de estado, por
lo que un rollback deja ambas cosas consistentes.
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .auditoria import registrar_movimiento
from app.models.solicitud import MAPA_ESTATUS_DOCUMENTADO, Solicitud


@receiver(pre_save, sender=Solicitud)
def recordar_estado_anterior(sender, instance, **kwargs):
    """Guarda en memoria el estado que tenía la fila antes de actualizarla."""
    if not instance.pk:
        instance._estado_anterior = None
        return

    instance._estado_anterior = (
        sender.objects.filter(pk=instance.pk)
        .values_list("estado", flat=True)
        .first()
    )


@receiver(post_save, sender=Solicitud)
def escribir_bitacora(sender, instance, created, **kwargs):
    """Anexa el movimiento a la bitácora transaccional."""
    if getattr(instance, "_bitacora_silenciosa", False):
        return

    estatus_nuevo = instance.estatus_documentado

    if created:
        registrar_movimiento(
            instance,
            estatus_anterior="",
            estatus_nuevo=estatus_nuevo,
            comentarios="Registro inicial de la solicitud.",
        )
        return

    estado_anterior = getattr(instance, "_estado_anterior", None)
    if not estado_anterior or estado_anterior == instance.estado:
        return

    comentario = instance.motivo_rechazo or instance.observaciones or ""
    registrar_movimiento(
        instance,
        estatus_anterior=MAPA_ESTATUS_DOCUMENTADO.get(estado_anterior, estado_anterior),
        estatus_nuevo=estatus_nuevo,
        comentarios=comentario,
    )
