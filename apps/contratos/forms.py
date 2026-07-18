"""Formularios del módulo de contratos."""

from django import forms

from apps.apartamentos.models import Apartamento
from apps.contratos.models import Contrato
from apps.core.forms import DateInput, EstiloWidgetsMixin
from apps.cuentas.models import Usuario


class ContratoForm(EstiloWidgetsMixin, forms.ModelForm):
    """Registro de un contrato de arrendamiento (RF-003).

    Si se pasa ``apartamento`` al construir el formulario, el apartamento queda
    fijado (alta desde la ficha del apartamento) y no se muestra el selector.
    """

    class Meta:
        model = Contrato
        fields = ["apartamento", "inquilino", "fecha_inicio", "fecha_vencimiento", "monto", "notas"]
        labels = {
            "apartamento": "Apartamento",
            "inquilino": "Inquilino",
            "fecha_inicio": "Fecha de inicio",
            "fecha_vencimiento": "Fecha de vencimiento",
            "monto": "Monto mensual (₡)",
            "notas": "Notas",
        }
        widgets = {
            "fecha_inicio": DateInput(),
            "fecha_vencimiento": DateInput(),
        }

    def __init__(self, *args, apartamento=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo inquilinos activos pueden asignarse.
        self.fields["inquilino"].queryset = Usuario.objects.filter(
            rol=Usuario.Rol.INQUILINO, is_active=True
        ).order_by("first_name", "last_name")
        # Apartamentos activos que no tengan ya un contrato activo (salvo el propio).
        libres = Apartamento.objects.filter(activo=True).exclude(
            contratos__activo=True
        )
        if self.instance and self.instance.apartamento_id:
            libres = Apartamento.objects.filter(
                pk__in=list(libres.values_list("pk", flat=True))
                + [self.instance.apartamento_id]
            )
        self.fields["apartamento"].queryset = libres.order_by("codigo")

        if apartamento is not None:
            self.fields["apartamento"].initial = apartamento
            self.fields["apartamento"].disabled = True
            self.fields["apartamento"].widget = forms.HiddenInput()
            self.instance.apartamento = apartamento
            if not self.instance.pk and apartamento.monto_mensual:
                self.fields["monto"].initial = apartamento.monto_mensual

        self.estilizar_widgets()


class RenovarContratoForm(EstiloWidgetsMixin, forms.Form):
    """Datos para renovar un contrato existente (RF-003)."""

    fecha_inicio = forms.DateField(label="Fecha de inicio", widget=DateInput())
    fecha_vencimiento = forms.DateField(label="Fecha de vencimiento", widget=DateInput())
    monto = forms.DecimalField(label="Monto mensual (₡)", max_digits=12, decimal_places=2)
    notas = forms.CharField(label="Notas", required=False, widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.estilizar_widgets()

    def clean(self):
        datos = super().clean()
        inicio = datos.get("fecha_inicio")
        vence = datos.get("fecha_vencimiento")
        if inicio and vence and vence <= inicio:
            self.add_error("fecha_vencimiento", "La fecha de vencimiento debe ser posterior al inicio.")
        return datos
