from django.contrib.auth.models import AbstractBaseUser, UserManager
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class User(AbstractBaseUser):
    """
    Tabla ``usuarios`` del modelo relacional.

    ``username`` guarda la matrícula (alumnos) o el número de nómina
    (personal). Se usa ``AbstractBaseUser`` en lugar de ``AbstractUser`` para
    no crear las tablas M2M ``usuarios_groups`` ni
    ``usuarios_user_permissions``: el sistema autoriza por el campo ``rol`` y
    no asigna permisos individuales de Django.

    ``is_active`` es el estado de la cuenta que administra la Secretaría
    Académica (HU-24): False = cuenta deshabilitada, no puede iniciar sesión.
    """

    class Rol(models.TextChoices):
        ALUMNO = "alumno", "Alumno"
        SECRETARIA_GRUPO = "secretaria_grupo", "Secretaría de grupo"
        COORDINADOR = "coordinador", "Coordinación académica"
        ADMINISTRADOR = "administrador", "Secretaría Académica"

    username = models.CharField(
        _("username"),
        max_length=150,
        unique=True,
        help_text=_(
            "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
        ),
        validators=[UnicodeUsernameValidator()],
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )
    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    last_name = models.CharField(_("last name"), max_length=150, blank=True)
    email = models.EmailField(_("email address"), blank=True)
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )
    is_superuser = models.BooleanField(
        _("superuser status"),
        default=False,
        help_text=_(
            "Designates that this user has all permissions without explicitly "
            "assigning them."
        ),
    )
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)
    rol = models.CharField(
        max_length=20,
        choices=Rol.choices,
        default=Rol.ALUMNO,
    )

    objects = UserManager()

    USERNAME_FIELD = "username"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        db_table = "usuarios"
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"

    def __str__(self):
        return f"{self.username} - {self.rol}"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name

    # El sistema no usa permisos por objeto ni grupos de Django: la
    # autorización se resuelve con ``rol`` en los decoradores. Solo el
    # superusuario puede entrar al admin de Django.
    def get_group_permissions(self, obj=None):
        return set()

    def get_user_permissions(self, obj=None):
        return set()

    def get_all_permissions(self, obj=None):
        return set()

    def has_perm(self, perm, obj=None):
        return self.is_active and self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_active and self.is_superuser

    @property
    def matricula_o_nomina(self):
        """Matrícula del alumno o número de nómina del personal."""
        return self.username

    @property
    def nombre(self):
        """Nombre completo, con el mismo formato que la tabla ``usuarios``."""
        return self.get_full_name() or self.username

    @property
    def esta_habilitada(self):
        """Estado de la cuenta (HU-24)."""
        return self.is_active
