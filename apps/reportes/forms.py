"""Formularios de filtros de reportes."""

from datetime import date

from django import forms

from apps.apartamentos.models import Apartamento
from apps.cobros.models import MESES
from apps.core.forms import EstiloWidgetsMixin


class FiltroGananciasForm(EstiloWidgetsMixin, forms.Form):
    """Filtros del reporte de ganancias: año, mes (opcional) y apartamento."""

    anio = forms.IntegerField(label="Año", min_value=2020, max_value=2100)
    mes = forms.TypedChoiceField(
        label="Mes",
        required=False,
        coerce=int,
        choices=[("", "Todo el año")] + [(n, nombre) for n, nombre in MESES.items()],
    )
    apartamento = forms.ModelChoiceField(
        label="Apartamento",
        required=False,
        queryset=Apartamento.objects.all().order_by("codigo"),
        empty_label="Todos",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.data:
            self.fields["anio"].initial = date.today().year
            self.fields["mes"].initial = date.today().month
        self.estilizar_widgets()
