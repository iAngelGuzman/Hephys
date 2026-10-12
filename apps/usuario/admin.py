from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from apps.usuario.models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Información adicional", {"fields": ("rol",)}),)

    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Información adicional", {"fields": ("rol",)}),
    )

    list_display = ("username", "email", "first_name", "last_name", "rol", "is_staff")
    list_filter = UserAdmin.list_filter + ("rol",)
