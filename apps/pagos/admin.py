"""Registro en el admin de Django para abonos."""

from django.contrib import admin

from apps.pagos.models import Abono


@admin.register(Abono)
class AbonoAdmin(admin.ModelAdmin):
    list_display = ("cobro", "monto", "fecha", "metodo", "estado_verificacion", "verificado_por")
    list_filter = ("estado_verificacion", "metodo")
    search_fields = ("cobro__apartamento__codigo", "referencia")
    autocomplete_fields = ("cobro", "registrado_por", "verificado_por")
    readonly_fields = ("verificado_en",)
