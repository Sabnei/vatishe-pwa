"""Registro en el admin de Django para cobros y multas."""

from django.contrib import admin

from apps.cobros.models import Cobro, Multa


@admin.register(Cobro)
class CobroAdmin(admin.ModelAdmin):
    list_display = ("apartamento", "inquilino", "periodo_display", "monto", "estado", "fecha_vencimiento")
    list_filter = ("estado", "anio", "mes")
    search_fields = ("apartamento__codigo", "inquilino__first_name", "inquilino__last_name")
    autocomplete_fields = ("apartamento", "inquilino", "contrato")
    date_hierarchy = "fecha_vencimiento"


@admin.register(Multa)
class MultaAdmin(admin.ModelAdmin):
    list_display = ("cobro", "monto", "motivo", "fecha_aplicacion", "exonerada")
    list_filter = ("exonerada", "motivo")
    search_fields = ("cobro__apartamento__codigo",)
    autocomplete_fields = ("cobro", "exonerada_por")
