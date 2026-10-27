import re

from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from app.models.estudiante import Estudiante
from app.models.secretaria import Secretaria
from app.models.usuario import User

PATRON_SOLO_LETRAS = r"^[A-Za-zÁÉÍÓÚáéíóúÑñÜü\s]+$"
PATRON_SOLO_LETRAS_HTML = "[A-Za-zÁÉÍÓÚáéíóúÑñÜü\\s]+"

# La matrícula es "S" + año de ingreso (2 dígitos) + 6 dígitos. Se aceptan
# años desde MATRICULA_ANIO_MINIMO hasta el año actual, así no hay que
# tocar el código cada año nuevo.
MATRICULA_ANIO_MINIMO = 20
SEMESTRE_MINIMO = 1
SEMESTRE_MAXIMO = 10


def _anio_actual_dos_digitos():
    return timezone.localdate().year % 100


def _widget_solo_letras():
    return forms.TextInput(
        attrs={
            "class": "form-control",
            "pattern": PATRON_SOLO_LETRAS_HTML,
            # static/js/solo_letras.js quita lo que no sea letra mientras se escribe.
            "data-solo-letras": "",
            "title": "Solo se permiten letras y espacios",
        }
    )


class RegistroAlumnoForm(forms.ModelForm):
    password = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "minlength": "8",
                "autocomplete": "new-password",
            }
        ),
        help_text="Mínimo 8 caracteres. No puede ser solo números ni una contraseña común.",
    )

    class Meta:
        model = Estudiante
        fields = [
            "nombres",
            "apellido_paterno",
            "apellido_materno",
            "matricula",
            "carrera",
            "semestre",
            "secretaria",
        ]
        widgets = {
            "nombres": _widget_solo_letras(),
            "apellido_paterno": _widget_solo_letras(),
            "apellido_materno": _widget_solo_letras(),
            "matricula": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "S24000000",
                    # usuario/js/registro.js deja solo "S" y dígitos, en mayúsculas.
                    "data-matricula": "",
                    "minlength": "9",
                    "maxlength": "9",
                }
            ),
            "carrera": forms.Select(attrs={"class": "form-select"}),
            "semestre": forms.Select(
                choices=[
                    (i, f"{i}° Semestre")
                    for i in range(SEMESTRE_MINIMO, SEMESTRE_MAXIMO + 1)
                ],
                attrs={"class": "form-select"},
            ),
            "secretaria": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Solo se puede elegir una secretaria con la cuenta activa.
        self.fields["secretaria"].queryset = Secretaria.objects.filter(
            user__is_active=True
        ).select_related("user")

        anio_maximo = _anio_actual_dos_digitos()
        self.fields["matricula"].widget.attrs.update(
            {
                "pattern": "[Ss][0-9]{8}",
                "title": (
                    "Debe iniciar con S, seguido del año de ingreso "
                    f"({MATRICULA_ANIO_MINIMO} a {anio_maximo:02d}) y 6 dígitos "
                    "(9 caracteres en total)"
                ),
            }
        )

    # --- Nombres -----------------------------------------------------------

    def _validar_letras(self, campo, etiqueta):
        valor = (self.cleaned_data.get(campo) or "").strip()
        if valor and not re.match(PATRON_SOLO_LETRAS, valor):
            raise ValidationError(f"El campo {etiqueta} solo debe contener letras.")
        return valor

    def clean_nombres(self):
        return self._validar_letras("nombres", "Nombre(s)")

    def clean_apellido_paterno(self):
        return self._validar_letras("apellido_paterno", "Apellido Paterno")

    def clean_apellido_materno(self):
        return self._validar_letras("apellido_materno", "Apellido Materno")

    # --- Matrícula y semestre ----------------------------------------------

    def clean_matricula(self):
        matricula = (self.cleaned_data.get("matricula") or "").strip().upper()
        anio_maximo = _anio_actual_dos_digitos()

        coincidencia = re.fullmatch(r"S(\d{2})\d{6}", matricula)
        if not coincidencia:
            raise ValidationError(
                "La matrícula debe tener 9 caracteres: la letra 'S' seguida de "
                "8 dígitos (Ej. S24000000)."
            )

        anio_ingreso = int(coincidencia.group(1))
        if not MATRICULA_ANIO_MINIMO <= anio_ingreso <= anio_maximo:
            raise ValidationError(
                f"El año de ingreso de la matrícula debe estar entre "
                f"{MATRICULA_ANIO_MINIMO} y {anio_maximo:02d}."
            )

        # La matrícula también es el usuario para iniciar sesión.
        if (
            Estudiante.objects.filter(matricula__iexact=matricula).exists()
            or User.objects.filter(username__iexact=matricula).exists()
        ):
            raise ValidationError("Ya existe una cuenta registrada con esta matrícula.")

        return matricula

    def clean_semestre(self):
        semestre = self.cleaned_data.get("semestre")
        if semestre is None or not SEMESTRE_MINIMO <= semestre <= SEMESTRE_MAXIMO:
            raise ValidationError(
                f"El semestre debe estar entre {SEMESTRE_MINIMO} y {SEMESTRE_MAXIMO}."
            )
        return semestre

    # --- Contraseña --------------------------------------------------------

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")

        if password:
            # Usuario temporal para que el validador de "parecido a tus datos"
            # compare la contraseña contra la matrícula y el nombre.
            usuario_temporal = User(
                username=cleaned_data.get("matricula", ""),
                first_name=cleaned_data.get("nombres", ""),
                last_name=cleaned_data.get("apellido_paterno", ""),
            )
            try:
                validate_password(password, user=usuario_temporal)
            except ValidationError as error:
                self.add_error("password", error)

        return cleaned_data

    # --- Guardado ----------------------------------------------------------

    def save(self, commit=True):
        """
        Crea el usuario (login = matrícula) y el perfil de estudiante en una
        sola transacción: si algo falla, no queda un usuario sin perfil.
        """
        if not commit:
            raise ValueError(
                "RegistroAlumnoForm siempre guarda el usuario y el perfil juntos; "
                "llama a save() sin commit=False."
            )

        datos = self.cleaned_data
        with transaction.atomic():
            usuario = User.objects.create_user(
                username=datos["matricula"],
                password=datos["password"],
                first_name=datos["nombres"],
                last_name=f"{datos['apellido_paterno']} {datos['apellido_materno']}".strip(),
                rol=User.Rol.ALUMNO,
            )
            estudiante = super().save(commit=False)
            estudiante.user = usuario
            estudiante.save()

        return estudiante
