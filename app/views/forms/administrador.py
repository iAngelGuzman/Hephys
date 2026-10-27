import re

from django import forms
from django.contrib.auth.password_validation import validate_password

from app.models.solicitud import CalendarioMatricula, PeriodoTramite
from app.controllers.validadores import validar_archivo_pdf
from app.models.usuario import User

from app.controllers.constantes_administracion import CARRERA_CODES

PATRON_SOLO_LETRAS = r"^[A-Za-zÁÉÍÓÚáéíóúÑñÜü\s]+$"


# Formato que entiende <input type="datetime-local">. Sin él, Django pinta
# la fecha como "27/09/2026 17:38:58", el navegador no la reconoce y el
# campo aparece vacío aunque el periodo ya esté guardado.
FORMATO_DATETIME_LOCAL = "%Y-%m-%dT%H:%M"


def _widget_fecha_hora(clase="form-control"):
    return forms.DateTimeInput(
        format=FORMATO_DATETIME_LOCAL,
        attrs={"type": "datetime-local", "class": clase},
    )


class _RangoFechasMixin:
    """La fecha de cierre debe ser posterior a la de apertura."""

    def clean(self):
        cleaned_data = super().clean()
        apertura = cleaned_data.get("fecha_apertura")
        cierre = cleaned_data.get("fecha_cierre")
        if apertura and cierre and cierre <= apertura:
            self.add_error(
                "fecha_cierre", "La fecha de cierre debe ser posterior a la de apertura."
            )
        return cleaned_data


class PeriodoTramiteForm(_RangoFechasMixin, forms.ModelForm):
    class Meta:
        model = PeriodoTramite
        fields = ["fecha_apertura", "fecha_cierre"]
        widgets = {
            "fecha_apertura": _widget_fecha_hora(),
            "fecha_cierre": _widget_fecha_hora(),
        }


class CalendarioMatriculaForm(_RangoFechasMixin, forms.ModelForm):
    """
    Restricción por prefijo de matrícula (p. ej. solo S23 del 2 al 4 de
    agosto). Sus fechas deben quedar dentro del periodo general del trámite,
    que recibe el formulario en `periodo`.
    """

    class Meta:
        model = CalendarioMatricula
        fields = ["prefijo_matricula", "fecha_apertura", "fecha_cierre"]
        widgets = {
            "prefijo_matricula": forms.TextInput(
                attrs={"class": "input-compacto", "placeholder": "Ej. S23"}
            ),
            "fecha_apertura": _widget_fecha_hora("input-compacto"),
            "fecha_cierre": _widget_fecha_hora("input-compacto"),
        }

    def __init__(self, *args, periodo=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.periodo = periodo

    def clean_prefijo_matricula(self):
        prefijo = self.cleaned_data["prefijo_matricula"].strip().upper()
        if not re.fullmatch(r"S\d{1,8}", prefijo):
            raise forms.ValidationError(
                "El prefijo debe ser la letra S seguida de números (Ej. S23)."
            )
        return prefijo

    def clean(self):
        cleaned_data = super().clean()
        apertura = cleaned_data.get("fecha_apertura")
        cierre = cleaned_data.get("fecha_cierre")
        if self.periodo and apertura and cierre and not (
            self.periodo.fecha_apertura <= apertura
            and cierre <= self.periodo.fecha_cierre
        ):
            raise forms.ValidationError(
                "Las fechas deben quedar dentro del periodo general de "
                f"{self.periodo.tipo_tramite}."
            )
        return cleaned_data


class SubirOfertaPDFForm(forms.Form):
    archivo_pdf = forms.FileField(
        label="Selecciona el PDF de la Oferta Educativa",
        widget=forms.ClearableFileInput(
            attrs={"class": "form-control", "accept": ".pdf"}
        ),
    )

    def clean_archivo_pdf(self):
        return validar_archivo_pdf(self.cleaned_data["archivo_pdf"])


class SubirCalendarioExamenesForm(forms.Form):
    carrera_code = forms.ChoiceField(
        choices=[(codigo, codigo) for codigo in CARRERA_CODES],
        error_messages={"invalid_choice": "Carrera no válida."},
    )
    archivo_horario = forms.FileField(
        error_messages={"required": "Por favor selecciona un archivo PDF."},
    )

    def clean_archivo_horario(self):
        return validar_archivo_pdf(self.cleaned_data["archivo_horario"])


class _DatosSecretariaForm(forms.ModelForm):
    """
    Campos y validaciones comunes para crear y editar una Secretaría de
    Grupo. Todas las reglas viven aquí (servidor); las del navegador son
    solo una ayuda y se pueden saltar.
    """

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in ("first_name", "last_name", "email"):
            self.fields[campo].required = True

    def _validar_letras(self, campo, etiqueta):
        valor = (self.cleaned_data.get(campo) or "").strip()
        if not re.match(PATRON_SOLO_LETRAS, valor):
            raise forms.ValidationError(f"{etiqueta} solo debe contener letras.")
        return valor

    def clean_first_name(self):
        return self._validar_letras("first_name", "El nombre")

    def clean_last_name(self):
        return self._validar_letras("last_name", "El apellido")

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        repetidos = User.objects.filter(username__iexact=username)
        if self.instance.pk:
            repetidos = repetidos.exclude(pk=self.instance.pk)
        if repetidos.exists():
            raise forms.ValidationError(
                f"El nombre de usuario '{username}' ya está en uso."
            )
        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        repetidos = User.objects.filter(email__iexact=email)
        if self.instance.pk:
            repetidos = repetidos.exclude(pk=self.instance.pk)
        if repetidos.exists():
            raise forms.ValidationError(f"El correo '{email}' ya está registrado.")
        return email

    def _validar_password(self, password):
        """Aplica AUTH_PASSWORD_VALIDATORS de settings (mínimo 8, no común...)."""
        usuario_temporal = User(
            username=self.cleaned_data.get("username", ""),
            first_name=self.cleaned_data.get("first_name", ""),
            last_name=self.cleaned_data.get("last_name", ""),
            email=self.cleaned_data.get("email", ""),
        )
        validate_password(password, user=usuario_temporal)


class CrearSecretariaForm(_DatosSecretariaForm):
    password = forms.CharField(strip=False, widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        if password:
            try:
                self._validar_password(password)
            except forms.ValidationError as error:
                self.add_error("password", error)
        return cleaned_data

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.rol = User.Rol.SECRETARIA_GRUPO
        usuario.set_password(self.cleaned_data["password"])
        if commit:
            usuario.save()
        return usuario


class EditarSecretariaForm(_DatosSecretariaForm):
    password = forms.CharField(strip=False, required=False, widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        if password:
            try:
                self._validar_password(password)
            except forms.ValidationError as error:
                self.add_error("password", error)
        return cleaned_data

    def save(self, commit=True):
        usuario = super().save(commit=False)
        if self.cleaned_data.get("password"):
            usuario.set_password(self.cleaned_data["password"])
        if commit:
            usuario.save()
        return usuario


def primer_error(form):
    """Primer mensaje de error del form, para mostrarlo con messages."""
    for errores in form.errors.values():
        return errores[0]
    return "Revisa los datos del formulario."
