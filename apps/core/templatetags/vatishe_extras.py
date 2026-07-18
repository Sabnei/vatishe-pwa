"""Filtros de plantilla reutilizables de VATISHE."""

from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter
def colones(valor):
    """Formatea un monto como colones costarricenses: ``₡ 250,000``.

    Sin decimales (los alquileres se manejan en montos enteros) y con separador
    de miles. Devuelve ``₡ 0`` ante valores inválidos.
    """
    try:
        numero = Decimal(valor)
    except (InvalidOperation, TypeError, ValueError):
        return "₡ 0"
    entero = int(numero.quantize(Decimal("1")))
    return f"₡ {entero:,.0f}".replace(",", " ")  # espacio duro como separador


@register.filter
def porcentaje(valor):
    """Formatea un número como porcentaje entero: ``85%``."""
    try:
        return f"{int(round(float(valor)))}%"
    except (TypeError, ValueError):
        return "0%"
