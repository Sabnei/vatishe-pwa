"""Formularios del módulo de apartamentos."""

from django import forms

from apps.apartamentos.models import Apartamento
from apps.core.forms import EstiloWidgetsMixin


class ApartamentoForm(EstiloWidgetsMixin, forms.ModelForm):
    """Alta y edición de apartamentos (RF-002)."""

    class Meta:
        model = Apartamento
        fields = ["codigo", "descripcion", "monto_mensual", "dia_vencimiento", "activo"]
        labels = {
            "codigo": "Número/nombre del apartamento",
            "descripcion": "Descripción",
            "monto_mensual": "Monto mensual (₡)",
            "dia_vencimiento": "Día de vencimiento",
            "activo": "Apartamento activo",
        }
        widgets = {
            "dia_vencimiento": forms.Select(
                choices=[(d, str(d)) for d in range(1, 32)]
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.estilizar_widgets()
