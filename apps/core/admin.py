"""Registro en el admin de Django para la configuración y los correos."""

from django.contrib import admin

from apps.core.models import ConfiguracionSistema, RegistroCorreo


@admin.register(ConfiguracionSistema)
class ConfiguracionSistemaAdmin(admin.ModelAdmin):
    list_display = (
        "nombre_empresa",
        "porcentaje_multa",
        "monto_multa_fijo",
        "dias_anticipacion_recordatorio",
    )

    def has_add_permission(self, request):
        # Singleton: no se permite crear más de una fila.
        return not ConfiguracionSistema.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(RegistroCorreo)
class RegistroCorreoAdmin(admin.ModelAdmin):
    list_display = ("tipo", "destinatario", "asunto", "exitoso", "creado_en")
    list_filter = ("tipo", "exitoso")
    search_fields = ("destinatario", "asunto", "clave_unicidad")
    readonly_fields = ("creado_en", "actualizado_en")
