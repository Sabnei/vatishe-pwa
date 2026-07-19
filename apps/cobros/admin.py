"""Registro en el admin de Django para cobros."""

from django.contrib import admin

from apps.cobros.models import Cobro


@admin.register(Cobro)
class CobroAdmin(admin.ModelAdmin):
    list_display = ("apartamento", "inquilino", "periodo_display", "monto", "estado", "fecha_vencimiento")
    list_filter = ("estado", "anio", "mes")
    search_fields = ("apartamento__codigo", "inquilino__first_name", "inquilino__last_name")
    autocomplete_fields = ("apartamento", "inquilino", "contrato")
    date_hierarchy = "fecha_vencimiento"
