"""Formularios del módulo de cobros."""

from datetime import date

from django import forms

from apps.cobros.models import MESES, Cobro
from apps.core.forms import DateInput, EstiloWidgetsMixin


class GenerarCobrosForm(EstiloWidgetsMixin, forms.Form):
    """Selección de periodo para generar los cobros mensuales (RF-004)."""

    anio = forms.IntegerField(label="Año", min_value=2020, max_value=2100)
    mes = forms.TypedChoiceField(
        label="Mes", coerce=int, choices=[(n, nombre) for n, nombre in MESES.items()]
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        hoy = date.today()
        self.fields["anio"].initial = hoy.year
        self.fields["mes"].initial = hoy.month
        self.estilizar_widgets()


class ExonerarMultaForm(forms.Form):
    """Motivo obligatorio al exonerar una multa (RF-007, HU-09)."""

    motivo = forms.CharField(
        label="Motivo de la exoneración",
        widget=forms.Textarea(attrs={"rows": 3, "class": "form-input"}),
    )


class CobroAjusteForm(EstiloWidgetsMixin, forms.ModelForm):
    """Ajuste manual de un cobro por el Administrador (RF-004)."""

    class Meta:
        model = Cobro
        fields = ["monto", "fecha_vencimiento"]
        labels = {"monto": "Monto base (₡)", "fecha_vencimiento": "Fecha de vencimiento"}
        widgets = {"fecha_vencimiento": DateInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.estilizar_widgets()
