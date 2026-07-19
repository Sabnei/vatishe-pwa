"""Formularios del módulo de averías."""

from django import forms

from apps.averias.models import Averia
from apps.core.forms import EstiloWidgetsMixin


class ReportarAveriaForm(EstiloWidgetsMixin, forms.ModelForm):
    """El inquilino reporta una avería (RF-008, HU-06). Las fotos van aparte.

    ``apartamentos`` limita el selector a los apartamentos del inquilino. Si solo
    tiene uno, queda fijado automáticamente.
    """

    class Meta:
        model = Averia
        fields = ["apartamento", "area", "descripcion"]
        labels = {
            "apartamento": "Apartamento",
            "area": "Área afectada",
            "descripcion": "Descripción del problema",
        }
        widgets = {
            "descripcion": forms.Textarea(
                attrs={"rows": 4, "placeholder": "Describe el daño o problema en detalle..."}
            ),
        }

    def __init__(self, *args, apartamentos=None, **kwargs):
        super().__init__(*args, **kwargs)
        if apartamentos is not None:
            self.fields["apartamento"].queryset = apartamentos
            if apartamentos.count() == 1:
                unico = apartamentos.first()
                self.fields["apartamento"].initial = unico
                self.fields["apartamento"].widget = forms.HiddenInput()
                self.fields["apartamento"].disabled = True
                self.instance.apartamento = unico
        self.estilizar_widgets()


class GestionAveriaForm(EstiloWidgetsMixin, forms.ModelForm):
    """El administrador actualiza el estado, gasto y notas de una avería (RF-008)."""

    class Meta:
        model = Averia
        fields = ["estado", "gasto", "notas_admin"]
        labels = {
            "estado": "Estado",
            "gasto": "Gasto de reparación (₡)",
            "notas_admin": "Notas del administrador",
        }
        widgets = {"notas_admin": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.estilizar_widgets()
