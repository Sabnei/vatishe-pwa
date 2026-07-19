"""Registro en el admin de Django para averías."""

from django.contrib import admin

from apps.averias.models import Averia, FotoAveria


class FotoAveriaInline(admin.TabularInline):
    model = FotoAveria
    extra = 0


@admin.register(Averia)
class AveriaAdmin(admin.ModelAdmin):
    list_display = ("apartamento", "inquilino", "area", "estado", "gasto", "creado_en")
    list_filter = ("estado", "area")
    search_fields = ("apartamento__codigo", "descripcion")
    autocomplete_fields = ("apartamento", "inquilino", "atendida_por")
    inlines = [FotoAveriaInline]
