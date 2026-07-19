"""Formularios del módulo de pagos."""

from datetime import date

from django import forms

from apps.core.forms import DateInput, EstiloWidgetsMixin
from apps.pagos.models import Abono

EXTENSIONES_PERMITIDAS = {"jpg", "jpeg", "png", "webp", "heic", "heif", "pdf"}


class AbonoForm(EstiloWidgetsMixin, forms.ModelForm):
    """Registro de un abono con su comprobante por el inquilino (RF-005)."""

    class Meta:
        model = Abono
        fields = ["monto", "fecha", "metodo", "referencia", "observaciones", "comprobante"]
        labels = {
            "monto": "Monto del abono (₡)",
            "fecha": "Fecha del pago",
            "metodo": "Método de pago",
            "referencia": "Referencia (opcional)",
            "observaciones": "Observaciones (opcional)",
            "comprobante": "Comprobante de pago",
        }
        widgets = {
            "fecha": DateInput(),
            "metodo": forms.RadioSelect(),
        }

    def __init__(self, *args, cobro=None, **kwargs):
        self.cobro = cobro
        super().__init__(*args, **kwargs)
        self.fields["fecha"].initial = date.today()
        self.fields["comprobante"].widget.attrs["accept"] = "image/*,application/pdf"
        if cobro is not None:
            # Sugiere y limita el monto al saldo que falta por cubrir.
            self.fields["monto"].initial = cobro.saldo_por_cubrir
            self.fields["monto"].widget.attrs["max"] = cobro.saldo_por_cubrir
        self.estilizar_widgets()
        # El radio de método no lleva la clase de input de texto.
        self.fields["metodo"].widget.attrs.pop("class", None)

    def clean_monto(self):
        monto = self.cleaned_data["monto"]
        if monto is None or monto <= 0:
            raise forms.ValidationError("El monto debe ser mayor que cero.")
        # No se permite abonar más de lo que se debe (evita saldos a favor).
        if self.cobro is not None and monto > self.cobro.saldo_por_cubrir:
            raise forms.ValidationError(
                f"El monto no puede superar el saldo por cubrir "
                f"(₡{self.cobro.saldo_por_cubrir:,.0f})."
            )
        return monto

    def clean_comprobante(self):
        archivo = self.cleaned_data.get("comprobante")
        if archivo and hasattr(archivo, "name"):
            ext = archivo.name.rsplit(".", 1)[-1].lower() if "." in archivo.name else ""
            if ext not in EXTENSIONES_PERMITIDAS:
                raise forms.ValidationError("Formato no permitido. Suba una imagen (JPG/PNG) o un PDF.")
        return archivo


class RechazoComprobanteForm(forms.Form):
    """Motivo obligatorio al rechazar un comprobante (RF-006)."""

    motivo = forms.CharField(
        label="Motivo del rechazo",
        widget=forms.Textarea(attrs={"rows": 3, "class": "form-input"}),
    )
