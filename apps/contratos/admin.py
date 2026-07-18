"""Registro en el admin de Django para contratos."""

from django.contrib import admin

from apps.contratos.models import Contrato


@admin.register(Contrato)
class ContratoAdmin(admin.ModelAdmin):
    list_display = (
        "apartamento",
        "inquilino",
        "fecha_inicio",
        "fecha_vencimiento",
        "monto",
        "activo",
    )
    list_filter = ("activo",)
    search_fields = ("apartamento__codigo", "inquilino__first_name", "inquilino__last_name")
    autocomplete_fields = ("apartamento", "inquilino", "renovacion_de")
    date_hierarchy = "fecha_inicio"
