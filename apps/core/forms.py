"""Utilidades de formularios compartidas entre apps."""

from django import forms

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
