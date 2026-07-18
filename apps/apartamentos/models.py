"""Modelos del módulo de apartamentos (RF-002).

El apartamento es la unidad arrendable. Su "inquilino asignado" se deriva del
contrato activo (ver app ``contratos``), de modo que exista una única fuente de
verdad y se cumpla la regla: un apartamento no puede tener dos inquilinos
activos a la vez.
"""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import ModeloBase


class Apartamento(ModeloBase):
    """Unidad arrendable con su monto mensual y día de vencimiento (RF-002)."""

    codigo = models.CharField(
        _("número/nombre"),
        max_length=40,
        unique=True,
        help_text=_("Identificador visible del apartamento, p. ej. «Apto. 101»."),
    )
    descripcion = models.TextField(_("descripción"), blank=True)
    monto_mensual = models.DecimalField(
        _("monto mensual"),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    dia_vencimiento = models.PositiveSmallIntegerField(
        _("día de vencimiento"),
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text=_("Día del mes en que vence el cobro (se ajusta si el mes es más corto)."),
    )
    activo = models.BooleanField(_("activo"), default=True)

    class Meta:
        verbose_name = _("apartamento")
        verbose_name_plural = _("apartamentos")
        ordering = ["codigo"]

    def __str__(self):
        return self.codigo

    @property
    def contrato_activo(self):
        """Contrato vigente del apartamento, o ``None`` si está desocupado."""
        return (
            self.contratos.filter(activo=True)
            .select_related("inquilino")
            .first()
        )

    @property
    def inquilino_activo(self):
        contrato = self.contrato_activo
        return contrato.inquilino if contrato else None

    @property
    def ocupado(self):
        return self.contrato_activo is not None
