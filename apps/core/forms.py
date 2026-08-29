"""Utilidades de formularios compartidas entre apps."""

from django import forms

from apps.core.models import ConfiguracionSistema

INPUT_CLASS = "form-input"


class EstiloWidgetsMixin:
    """Aplica las clases del design system a los widgets del formulario.

    Se usa en los formularios de las distintas apps para mantener una apariencia
    coherente sin repetir clases en cada campo.
    """

    def estilizar_widgets(self):
        for campo in self.fields.values():
            widget = campo.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "h-5 w-5 rounded accent-accent")
            elif isinstance(widget, forms.Textarea):
                widget.attrs.setdefault("class", INPUT_CLASS)
                widget.attrs.setdefault("rows", 3)
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs.setdefault("class", INPUT_CLASS + " bg-surface-lowest")
            else:
                widget.attrs.setdefault("class", INPUT_CLASS)


class DateInput(forms.DateInput):
    """Input de fecha nativo del navegador (type=date)."""

    input_type = "date"


class ConfiguracionSistemaForm(EstiloWidgetsMixin, forms.ModelForm):
    """Edición de los parámetros globales desde la app (sin usar el admin de Django)."""

    class Meta:
        model = ConfiguracionSistema
        fields = [
            "nombre_empresa",
            "porcentaje_multa",
            "monto_multa_fijo",
            "dias_anticipacion_recordatorio",
        ]
        labels = {
            "nombre_empresa": "Nombre de la empresa",
            "porcentaje_multa": "Porcentaje de multa (%)",
            "monto_multa_fijo": "Monto fijo de multa (₡)",
            "dias_anticipacion_recordatorio": "Días de anticipación del recordatorio",
        }
        help_texts = {
            "porcentaje_multa": "Se aplica sobre el saldo pendiente al vencer el cobro.",
            "monto_multa_fijo": "Si es mayor que 0, se cobra este monto en lugar del porcentaje.",
            "dias_anticipacion_recordatorio": "Días antes del vencimiento para enviar el recordatorio por correo.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["porcentaje_multa"].widget.attrs.update({"step": "0.01", "min": "0"})
        self.fields["monto_multa_fijo"].widget.attrs.update({"step": "0.01", "min": "0"})
        self.fields["dias_anticipacion_recordatorio"].widget.attrs.update(
            {"min": "0", "max": "60"}
        )
        self.estilizar_widgets()

    def clean_porcentaje_multa(self):
        valor = self.cleaned_data["porcentaje_multa"]
        if valor < 0 or valor > 100:
            raise forms.ValidationError("El porcentaje debe estar entre 0 y 100.")
        return valor

    def clean_monto_multa_fijo(self):
        valor = self.cleaned_data["monto_multa_fijo"]
        if valor < 0:
            raise forms.ValidationError("El monto no puede ser negativo.")
        return valor

    def clean_dias_anticipacion_recordatorio(self):
        valor = self.cleaned_data["dias_anticipacion_recordatorio"]
        if valor > 60:
            raise forms.ValidationError("Máximo 60 días de anticipación.")
        return valor
