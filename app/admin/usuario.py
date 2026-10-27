from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from app.models.usuario import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Información personal", {"fields": ("first_name", "last_name", "email")}),
        (
            "Permisos",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                )
            },
        ),
        ("Fechas importantes", {"fields": ("last_login", "date_joined")}),
        ("Información adicional", {"fields": ("rol",)}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "password1", "password2", "rol"),
            },
        ),
    )

    list_display = ("username", "email", "first_name", "last_name", "rol", "is_staff")
    list_filter = ("is_staff", "is_superuser", "is_active", "rol")
    filter_horizontal = ()
