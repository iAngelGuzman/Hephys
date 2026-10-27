import os
import secrets

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.utils import timezone

from app.models.estudiante import Estudiante


def storage_comprobantes():
    """
    Dónde se guardan las papeletas de pago (settings.CARPETA_COMPROBANTES_PAGO).

    Es una FUNCIÓN a propósito: así las migraciones guardan solo la
    referencia "app.models.solicitud.storage_comprobantes" y no la ruta
    absoluta de la computadora donde se corrió makemigrations
    (C:\\Users\\karen\\..., D:\\Tesis\\...). Con la ruta dentro de la
    migración, cada máquina generaba una migración nueva.
    """
    return FileSystemStorage(location=settings.CARPETA_COMPROBANTES_PAGO)


def storage_justificantes():
    """
    Dónde se guardan los comprobantes médicos de los justificantes. Por
    defecto en Papeles/justificantes; se puede cambiar con
    settings.CARPETA_JUSTIFICANTES (las pruebas usan una carpeta temporal).
    Es una función por la misma razón que storage_comprobantes: para que la
    migración no guarde una ruta absoluta.
    """
    carpeta = getattr(
        settings,
        "CARPETA_JUSTIFICANTES",
        os.path.join(settings.BASE_DIR, "Papeles", "justificantes"),
    )
    return FileSystemStorage(location=carpeta)


def storage_documentos_seguros():
    """
    Zona aislada para documentos sensibles (``storage/secure_uploads``).

    Se conserva porque la migración histórica ``0001_initial`` la referencia
    para construir el campo de ``DocumentoSolicitud`` (modelo eliminado en
    ``0003_limpieza_tablas``). No la usa ningún modelo actual.
    """
    carpeta = getattr(
        settings,
        "CARPETA_DOCUMENTOS_SEGUROS",
        os.path.join(settings.BASE_DIR, "storage", "secure_uploads"),
    )
    return FileSystemStorage(location=carpeta)


def storage_resoluciones():
    """Documentos finales (oficios, constancias firmadas) del trámite."""
    carpeta = getattr(
        settings,
        "CARPETA_RESOLUCIONES",
        os.path.join(settings.BASE_DIR, "storage", "resoluciones"),
    )
    return FileSystemStorage(location=carpeta)


class ExperienciaEducativa(models.Model):
    nombre = models.CharField(max_length=150)
    carrera = models.CharField(
        max_length=150, blank=True, null=True, verbose_name="Carrera"
    )
    creditos = models.PositiveIntegerField(default=0, verbose_name="Créditos")
    tiene_prerequisito = models.BooleanField(
        default=False, verbose_name="¿Tiene prerrequisito?"
    )

    def __str__(self):
        return f"{self.nombre} ({self.carrera or 'General'}) - {self.creditos} créd."


class ExperienciaEducativaOferta(models.Model):
    experiencia_educativa = models.ForeignKey(
        ExperienciaEducativa,
        on_delete=models.CASCADE,
        verbose_name="Experiencia Educativa (Catálogo)",
    )
    nrc = models.CharField(max_length=10, unique=True, verbose_name="NRC")
    docente = models.CharField(
        max_length=200, blank=True, null=True, verbose_name="Catedrático"
    )
    horarios = models.JSONField(default=list, verbose_name="Horarios y Días")
    bloque_seccion = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="Bloque y Sección"
    )
    cupo = models.IntegerField(default=0, verbose_name="Cupo disponible")

    def __str__(self):
        return f"{self.experiencia_educativa.nombre} - NRC: {self.nrc} [Bloque: {self.bloque_seccion}]"


class TipoTramite(models.TextChoices):
    EXTRAORDINARIO = "extraordinario", "Extraordinario"
    SUFICIENCIA = "suficiencia", "Título de Suficiencia"
    BAJA = "baja", "Baja de Experiencias Educativas"
    ALTA = "alta", "Alta de Experiencias Educativas"
    CONSTANCIA = "constancia", "Constancia de Estudios"
    JUSTIFICANTE = "justificante", "Justificante Médico"


class EstadoSolicitud(models.TextChoices):
    PENDIENTE_ACADEMICA = "pendiente_academica", "Pendiente de Revisión Académica"
    RECHAZADA_ACADEMICA = "rechazada_academica", "Rechazada por Secretaría Académica"
    PENDIENTE = "pendiente", "Pendiente con Secretario"
    PENDIENTE_FIRMA = "pendiente_firma", "Pendiente de Firma (Secretaría Académica)"
    ACEPTADA = "aceptada", "Aceptada"
    RECHAZADA = "rechazada", "Rechazada"


ESTADOS_ACTIVOS = (
    EstadoSolicitud.PENDIENTE_ACADEMICA,
    EstadoSolicitud.PENDIENTE,
    EstadoSolicitud.PENDIENTE_FIRMA,
    EstadoSolicitud.ACEPTADA,
)
ESTADOS_RECHAZADA = (EstadoSolicitud.RECHAZADA, EstadoSolicitud.RECHAZADA_ACADEMICA)

# Traducción del estado interno al estatus institucional de cinco valores.
MAPA_ESTATUS_DOCUMENTADO = {
    EstadoSolicitud.PENDIENTE_ACADEMICA: "Solicitado",
    EstadoSolicitud.PENDIENTE: "En Revisión",
    EstadoSolicitud.PENDIENTE_FIRMA: "Dictaminado",
    EstadoSolicitud.ACEPTADA: "Autorizado",
    EstadoSolicitud.RECHAZADA_ACADEMICA: "Rechazado",
    EstadoSolicitud.RECHAZADA: "Rechazado",
}


def generar_folio():
    """
    Folio público único: HPH-AAAAMMDD-XXXXXXXX.

    Se genera con ``secrets`` (no con ``random``) para que no sea predecible:
    adivinar el folio de otro alumno no debe servir para consultar su
    expediente (CA-04).
    """
    fecha = timezone.localdate().strftime("%Y%m%d")
    return f"HPH-{fecha}-{secrets.token_hex(4).upper()}"


def _fecha_iso(fecha):
    return fecha.isoformat() if fecha else ""


def _rango_fechas(inicio, fin):
    """Texto "dd/mm/aaaa" o "dd/mm/aaaa al dd/mm/aaaa" para mostrar."""
    if not inicio:
        return ""
    if not fin or fin == inicio:
        return inicio.strftime("%d/%m/%Y")
    return f"{inicio.strftime('%d/%m/%Y')} al {fin.strftime('%d/%m/%Y')}"


class SolicitudQuerySet(models.QuerySet):
    def activas(self):
        return self.filter(estado__in=ESTADOS_ACTIVOS)


class Solicitud(models.Model):
    TipoTramite = TipoTramite
    Estado = EstadoSolicitud

    estudiante = models.ForeignKey(
        Estudiante, on_delete=models.CASCADE, related_name="solicitudes"
    )

    tipo_tramite = models.CharField(
        max_length=20,
        choices=TipoTramite.choices,
        default=TipoTramite.EXTRAORDINARIO,
        verbose_name="Tipo de trámite",
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoSolicitud.choices,
        default=EstadoSolicitud.PENDIENTE,
    )

    # --- Campos del modelo relacional documentado (Semana 9 y 10) ---------
    folio = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        verbose_name="Folio de seguimiento",
        help_text="Identificador público de la solicitud (HPH-AAAAMMDD-XXXXXXXX).",
    )
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        null=True,
        blank=True,
        verbose_name="Última actualización",
    )
    revisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="solicitudes_revisadas",
        verbose_name="Responsable de la revisión",
    )
    fecha_dictamen = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha del dictamen",
    )
    motivo_rechazo = models.TextField(
        blank=True,
        null=True,
        verbose_name="Motivo del rechazo",
    )
    documento_resolucion = models.FileField(
        storage=storage_resoluciones,
        upload_to="",
        blank=True,
        verbose_name="Documento de resolución",
    )

    status_inscripcion = models.CharField(max_length=50, blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    motivo_baja = models.TextField(
        blank=True,
        null=True,
        verbose_name="Motivo de la baja",
        help_text="Motivo especificado por el estudiante para la baja de la experiencia educativa.",
    )
    motivo_constancia = models.TextField(
        blank=True,
        null=True,
        verbose_name="Motivo de la constancia",
        help_text="Para qué necesita el alumno la constancia de estudios.",
    )
    
    fecha_inicio_inasistencia = models.DateField(
        blank=True, null=True, verbose_name="Inicio de la inasistencia"
    )
    fecha_fin_inasistencia = models.DateField(
        blank=True, null=True, verbose_name="Fin de la inasistencia"
    )
    
    fecha_inicio_autorizada = models.DateField(
        blank=True, null=True, verbose_name="Inicio autorizado"
    )
    fecha_fin_autorizada = models.DateField(
        blank=True, null=True, verbose_name="Fin autorizado"
    )
    motivo_justificante = models.TextField(
        blank=True,
        null=True,
        verbose_name="Motivo de la inasistencia",
    )
    documento_medico = models.FileField(
        storage=storage_justificantes,
        upload_to="",
        blank=True,
        verbose_name="Comprobante médico",
    )
    lote_id = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="Lote de solicitud",
        help_text=(
            "Identificador interno para agrupar las solicitudes creadas "
            "juntas en un mismo trámite múltiple (alta o baja de varias "
            "materias a la vez). No es visible para el alumno ni la "
            "secretaria."
        ),
    )

    materia_nrc = models.CharField(
        max_length=100, default="", verbose_name="NRC de la materia"
    )
    materia_nombre = models.CharField(
        max_length=150, default="", verbose_name="materia"
    )
    materia_maestro = models.CharField(
        max_length=150, blank=True, default="", verbose_name="maestro"
    )

    ruta_horario = models.CharField(max_length=500, blank=True, null=True)

    objects = SolicitudQuerySet.as_manager()

    class EstatusDocumentado(models.TextChoices):
        """
        Estatus oficiales del expediente (Semana 3 y 4).

        Se conserva el estado interno detallado (``estado``) porque cada
        trámite tiene pasos propios; ``estatus_documentado`` los traduce a
        los cinco estatus que pide la documentación institucional.
        """

        SOLICITADO = "Solicitado", "Solicitado"
        EN_REVISION = "En Revisión", "En Revisión"
        DICTAMINADO = "Dictaminado", "Dictaminado"
        AUTORIZADO = "Autorizado", "Autorizado"
        RECHAZADO = "Rechazado", "Rechazado"

    class Meta:
        db_table = "tramites"
        verbose_name = "solicitud"
        verbose_name_plural = "solicitudes"
        ordering = ["-fecha_solicitud"]
        indexes = [
            models.Index(fields=["estado"], name="idx_tramites_estado"),
            models.Index(fields=["tipo_tramite"], name="idx_tramites_tipo"),
            models.Index(fields=["folio"], name="idx_tramites_folio"),
        ]

    def save(self, *args, **kwargs):
        # El folio se genera en el servidor, nunca se recibe del formulario
        # (CA-02: no se confía en identificadores enviados por el cliente).
        if not self.folio:
            self.folio = generar_folio()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Solicitud {self.folio or self.id} - {self.estudiante}"

    @property
    def estatus_documentado(self):
        """Traduce el estado interno al estatus institucional de 5 valores."""
        return MAPA_ESTATUS_DOCUMENTADO.get(
            self.estado, self.estado
        )

    @property
    def archivo_comprobante(self):
        """
        Ruta del primer comprobante digital de la solicitud.

        Equivale a la columna ``archivo_comprobante`` del modelo documentado;
        aquí los archivos viven en ``ComprobantePago`` para no duplicar
        información.
        """
        if self.documento_medico:
            return self.documento_medico.name
        comprobante = self.comprobantes.first()
        if comprobante and comprobante.archivo:
            return comprobante.archivo.name
        return ""

    def a_dict(self):
        """
        Datos de la solicitud para el JSON que usan las tablas y modales
        (alumno, secretaria y Secretaría Académica). Un solo lugar para que
        las 5 pantallas muestren lo mismo. Para listas, usar
        select_related("estudiante").prefetch_related("comprobantes").
        """
        estudiante = self.estudiante
        return {
            "id": self.id,
            "nombre": " ".join(
                parte
                for parte in (
                    estudiante.nombres,
                    estudiante.apellido_paterno,
                    estudiante.apellido_materno,
                )
                if parte
            ),
            "matricula": estudiante.matricula,
            "carrera": estudiante.carrera,
            "tipo_tramite": self.tipo_tramite,
            "tipo_tramite_display": self.get_tipo_tramite_display(),
            "materia_nombre": self.materia_nombre,
            "materia_nrc": self.materia_nrc,
            "materia_maestro": self.materia_maestro,
            "status_inscripcion": self.status_inscripcion or "-",
            "fecha_solicitud": (
                timezone.localtime(self.fecha_solicitud).strftime("%d/%m/%Y")
                if self.fecha_solicitud
                else ""
            ),
            "estado": self.estado,
            "estado_display": self.get_estado_display(),
            "observaciones": self.observaciones or "",
            "motivo_baja": self.motivo_baja or "",
            "motivo_constancia": self.motivo_constancia or "",
            "motivo_justificante": self.motivo_justificante or "",
            "inasistencia": _rango_fechas(
                self.fecha_inicio_inasistencia, self.fecha_fin_inasistencia
            ),
            "inasistencia_inicio": _fecha_iso(self.fecha_inicio_inasistencia),
            "inasistencia_fin": _fecha_iso(self.fecha_fin_inasistencia),
            "dias_autorizados": _rango_fechas(
                self.fecha_inicio_autorizada, self.fecha_fin_autorizada
            ),
            "tiene_documento_medico": bool(self.documento_medico),
            "tiene_horario": bool(self.ruta_horario),
            "papeletas": [
                {
                    "id": comprobante.id,
                    "folio": comprobante.folio,
                    "nombre": os.path.basename(comprobante.archivo.name),
                }
                for comprobante in self.comprobantes.all()
            ],
        }

    @property
    def materias_lista(self):
        return [
            materia.strip()
            for materia in self.materia_nombre.split(",")
            if materia.strip()
        ]


class PeriodoTramite(models.Model):
    TRAMITE_CHOICES = [
        ("altas", "Altas de Experiencias Educativas"),
        ("bajas", "Bajas de Experiencias Educativas"),
        ("extraordinario", "Exámenes Extraordinarios"),
        ("suficiencia", "Títulos de Suficiencia"),
    ]

    tipo_tramite = models.CharField(
        max_length=50,
        choices=TRAMITE_CHOICES,
        unique=True,
        verbose_name="Tipo de Trámite",
    )
    fecha_apertura = models.DateTimeField(verbose_name="Fecha y hora de apertura")
    fecha_cierre = models.DateTimeField(verbose_name="Fecha y hora de cierre")

    def __str__(self):
        return f"{self.get_tipo_tramite_display()} (Apertura: {self.fecha_apertura} - Cierre: {self.fecha_cierre})"


class CalendarioMatricula(models.Model):
    TIPO_TRAMITE_CHOICES = [
        ("altas", "Altas"),
        ("bajas", "Bajas"),
    ]
    tipo_tramite = models.CharField(max_length=10, choices=TIPO_TRAMITE_CHOICES)
    prefijo_matricula = models.CharField(max_length=20, help_text="Ej: S23, S24, etc.")
    fecha_apertura = models.DateTimeField()
    fecha_cierre = models.DateTimeField()

    def __str__(self):
        return f"{self.tipo_tramite} - {self.prefijo_matricula} ({self.fecha_apertura.date()})"


class ComprobantePago(models.Model):
    solicitud = models.ForeignKey(
        Solicitud, on_delete=models.CASCADE, related_name="comprobantes"
    )
    folio = models.CharField(max_length=7, verbose_name="Folio de pago")
    archivo = models.FileField(
        storage=storage_comprobantes,
        upload_to="",
        verbose_name="Papeleta de pago",
    )
    fecha_subida = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "comprobantes_pago"
        verbose_name = "comprobante de pago"
        verbose_name_plural = "comprobantes de pago"

    def __str__(self):
        return f"Folio {self.folio} - {self.solicitud}"


# ===========================================================================
# Modelo relacional documentado (Semanas 9, 10 y 12)
# ===========================================================================


class BitacoraTransaccional(models.Model):
    """
    Tabla ``bitacora_transaccional`` (HU-25 y trazabilidad ACID).

    Cada alta de solicitud y cada cambio de estado deja un renglón con el
    usuario responsable. Es append-only: la aplicación no la edita ni la
    borra. Se escribe dentro de la misma transacción que el cambio, así que
    si el cambio se revierte, la bitácora también.
    """

    solicitud = models.ForeignKey(
        Solicitud,
        # PROTECT: la bitácora es evidencia de auditoría; no debe desaparecer
        # si alguien borra el trámite. Coincide con el FK sin cascada del
        # modelo documentado (RESTRICT en MySQL).
        on_delete=models.PROTECT,
        related_name="bitacora",
        db_column="id_tramite",
        verbose_name="Solicitud",
    )
    usuario_responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimientos_bitacora",
        db_column="id_usuario_responsable",
        verbose_name="Usuario responsable",
    )
    estatus_anterior = models.CharField(
        max_length=50, blank=True, verbose_name="Estatus anterior"
    )
    estatus_nuevo = models.CharField(max_length=50, verbose_name="Estatus nuevo")
    comentarios = models.TextField(blank=True, verbose_name="Comentarios")
    fecha_movimiento = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "bitacora_transaccional"
        verbose_name = "movimiento de bitácora"
        verbose_name_plural = "bitácora transaccional"
        ordering = ["-fecha_movimiento", "-id"]
        indexes = [
            models.Index(fields=["solicitud", "fecha_movimiento"], name="idx_bitacora_sol_fecha"),
        ]

    def __str__(self):
        return (
            f"{self.solicitud_id}: {self.estatus_anterior or '-'} -> "
            f"{self.estatus_nuevo}"
        )
