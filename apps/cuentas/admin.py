"""Registro en el admin de Django para usuarios y perfiles."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from apps.cuentas.models import PerfilInquilino, Usuario


class PerfilInquilinoInline(admin.StackedInline):
    model = PerfilInquilino
    can_delete = False
    verbose_name_plural = "Perfil de inquilino"
    extra = 0


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    inlines = [PerfilInquilinoInline]
    list_display = ("username", "get_full_name", "email", "rol", "is_active")
    list_filter = ("rol", "is_active", "is_staff")
    search_fields = ("username", "first_name", "last_name", "email")
    fieldsets = UserAdmin.fieldsets + (
        ("Datos VATISHE", {"fields": ("rol", "telefono")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Datos VATISHE", {"fields": ("email", "rol", "telefono")}),
    )


@admin.register(PerfilInquilino)
class PerfilInquilinoAdmin(admin.ModelAdmin):
    list_display = ("usuario", "cedula", "telefono_alterno")
    search_fields = ("usuario__username", "cedula")
