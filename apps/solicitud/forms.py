import os
import re

from django import forms
from PIL import Image

from django.utils import timezone

from .constants import MOTIVO_CONSTANCIA_OTRO, MOTIVOS_CONSTANCIA
from .reglas import validar_fechas_justificante
from .validadores import validar_archivo_pdf

TAMANO_MAXIMO_MB = 10

EXTENSIONES_COMPROBANTE_VALIDAS = (".jpg", ".jpeg", ".png")
CONTENT_TYPES_COMPROBANTE_VALIDOS = (
    "image/jpeg",
    "image/png",
)


class HorarioUploadForm(forms.Form):
    horario = forms.FileField(
        label="Horario de clases (PDF)",
        error_messages={"required": "Debes subir tu horario de clases en PDF."},
    )

    def clean_horario(self):
        return validar_archivo_pdf(self.cleaned_data["horario"])


class ComprobantePagoForm(forms.Form):
    archivo = forms.FileField(
        label="Papeleta de pago (Foto JPG o PNG)",
        widget=forms.ClearableFileInput(attrs={"accept": "image/jpeg, image/png"}),
        error_messages={"required": "Debes subir tu papeleta de pago."},
    )
    folio = forms.CharField(
        label="Folio de pago",
        max_length=7,
        error_messages={
            "required": "Debes indicar el folio que aparece en tu papeleta.",
            "max_length": "El folio debe tener máximo 7 caracteres.",
        },
    )

    def clean_archivo(self):
        archivo = self.cleaned_data["archivo"]
        nombre_original, ext = os.path.splitext(archivo.name.lower())
        if (
            ext not in EXTENSIONES_COMPROBANTE_VALIDAS
            or archivo.content_type not in CONTENT_TYPES_COMPROBANTE_VALIDOS
        ):
            raise forms.ValidationError(
                "La papeleta debe ser una imagen/foto (JPG o PNG)."
            )
        limite_bytes = TAMANO_MAXIMO_MB * 1024 * 1024
        if archivo.size > limite_bytes:
            raise forms.ValidationError(
                f"El archivo no debe pesar más de {TAMANO_MAXIMO_MB} MB."
            )
        try:
            img = Image.open(archivo)
            img.verify()
        except Exception:
            raise forms.ValidationError(
                "El archivo está corrupto o no es una imagen válida."
            )

        archivo.seek(0)

        return archivo

    def clean_folio(self):
        folio = self.cleaned_data["folio"].strip()

        if not re.fullmatch(r"\d{7}", folio):
            raise forms.ValidationError(
                "El folio debe tener exactamente 7 dígitos numéricos, tal como aparece en la papeleta."
            )

        return folio


class SolicitudConstanciaForm(forms.Form):
    motivo = forms.CharField(
        label="¿Para qué necesitas la constancia?",
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "placeholder": "Escribe detalladamente para qué requieres la constancia...",
            }
        ),
        error_messages={
            "required": "Escribe para qué necesitas la constancia.",
        },
    )
    detalle = forms.CharField(
        label="Datos que debe incluir la constancia",
        required=False,
        max_length=300,
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "maxlength": "300",
                "placeholder": (
                    "Ej. periodo escolar, promedio, horario o el nombre de la "
                    "institución a la que va dirigida."
                ),
            }
        ),
        error_messages={
            "max_length": "Las especificaciones deben tener máximo 300 caracteres.",
        },
    )

    def clean(self):
        datos = super().clean()
        motivo = (datos.get("motivo") or "").strip()
        detalle = (datos.get("detalle") or "").strip()
        datos["motivo"] = motivo
        datos["detalle"] = detalle
        if not motivo:
            self.add_error(
                "motivo",
                "Escribe para qué necesitas la constancia.",
            )
        return datos

    def motivo_completo(self):
        """
        Texto que se guarda en la solicitud.
        """
        motivo = self.cleaned_data["motivo"]
        detalle = self.cleaned_data["detalle"]
        return f"{motivo}. Especificaciones: {detalle}" if detalle else motivo


EXTENSIONES_DOCUMENTO_MEDICO = (".pdf", ".jpg", ".jpeg", ".png")


class SolicitudJustificanteForm(forms.Form):
    """
    Datos del justificante médico: días de inasistencia, motivo y el
    comprobante médico escaneado (PDF) o en foto (JPG o PNG).
    """

    fecha_inicio = forms.DateField(
        label="Primer día de inasistencia",
        widget=forms.DateInput(attrs={"type": "date"}),
        error_messages={
            "required": "Indica el primer día que faltaste.",
            "invalid": "Escribe una fecha válida.",
        },
    )
    fecha_fin = forms.DateField(
        label="Último día de inasistencia",
        widget=forms.DateInput(attrs={"type": "date"}),
        error_messages={
            "required": "Indica el último día que faltaste.",
            "invalid": "Escribe una fecha válida.",
        },
    )
    motivo = forms.CharField(
        label="Motivo de la inasistencia",
        max_length=300,
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "maxlength": "300",
                "placeholder": "Ej. Consulta e incapacidad por infección respiratoria.",
            }
        ),
        error_messages={
            "required": "Describe brevemente el motivo de tu inasistencia.",
            "max_length": "El motivo debe tener máximo 300 caracteres.",
        },
    )
    documento = forms.FileField(
        label="Comprobante médico (PDF, JPG o PNG)",
        error_messages={"required": "Debes adjuntar tu comprobante médico."},
    )

    def clean_motivo(self):
        motivo = self.cleaned_data["motivo"].strip()
        if not motivo:
            raise forms.ValidationError(
                "Describe brevemente el motivo de tu inasistencia."
            )
        return motivo

    def clean_documento(self):
        archivo = self.cleaned_data["documento"]
        _, ext = os.path.splitext(archivo.name.lower())
        if ext not in EXTENSIONES_DOCUMENTO_MEDICO:
            raise forms.ValidationError(
                "El comprobante médico debe ser un PDF o una foto (JPG o PNG)."
            )
        if archivo.size > TAMANO_MAXIMO_MB * 1024 * 1024:
            raise forms.ValidationError(
                f"El archivo no debe pesar más de {TAMANO_MAXIMO_MB} MB."
            )
        if ext == ".pdf":
            archivo = validar_archivo_pdf(archivo)
        else:
            try:
                Image.open(archivo).verify()
            except Exception:
                raise forms.ValidationError(
                    "El archivo está dañado o no es una imagen válida."
                )
        archivo.seek(0)
        return archivo

    def clean(self):
        datos = super().clean()
        inicio = datos.get("fecha_inicio")
        fin = datos.get("fecha_fin")
        if inicio and fin:
            error = validar_fechas_justificante(inicio, fin, timezone.localdate())
            if error:
                self.add_error("fecha_fin", error)
        return datos
