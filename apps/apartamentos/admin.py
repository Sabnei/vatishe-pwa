"""Registro en el admin de Django para apartamentos."""

from django.contrib import admin

from apps.apartamentos.models import Apartamento


@admin.register(Apartamento)
class ApartamentoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "monto_mensual", "dia_vencimiento", "activo", "ocupado")
    list_filter = ("activo",)
    search_fields = ("codigo", "descripcion")

    @admin.display(boolean=True, description="Ocupado")
    def ocupado(self, obj):
        return obj.ocupado
