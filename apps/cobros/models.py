"""Modelos del módulo de cobros (RF-004).

El cobro es el cargo mensual de un inquilino por su apartamento. Su saldo se
calcula a partir del monto base + multas − abonos aprobados, y su estado se
deriva de ese saldo. Las multas viven en este mismo módulo (Fase 5).
"""

from decimal import Decimal

from django.db import models
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _

from apps.core.models import ModeloBase

MESES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
    7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre",
    12: "Diciembre",
}


class Cobro(ModeloBase):
    """Cargo mensual de un apartamento a su inquilino (RF-004)."""

    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", _("Pendiente")
        PARCIAL = "PARCIAL", _("Parcial")
        PAGADO = "PAGADO", _("Pagado")
        CON_MULTA = "CON_MULTA", _("Con multa")

    apartamento = models.ForeignKey(
        "apartamentos.Apartamento",
        on_delete=models.PROTECT,
        related_name="cobros",
        verbose_name=_("apartamento"),
    )
    inquilino = models.ForeignKey(
        "cuentas.Usuario",
        on_delete=models.PROTECT,
        related_name="cobros",
        verbose_name=_("inquilino"),
    )
    contrato = models.ForeignKey(
        "contratos.Contrato",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cobros",
        verbose_name=_("contrato"),
    )
    anio = models.PositiveIntegerField(_("año"))
    mes = models.PositiveSmallIntegerField(_("mes"))
    monto = models.DecimalField(_("monto base"), max_digits=12, decimal_places=2)
    fecha_vencimiento = models.DateField(_("fecha de vencimiento"))
    estado = models.CharField(
        _("estado"), max_length=12, choices=Estado.choices, default=Estado.PENDIENTE
    )

    class Meta:
        verbose_name = _("cobro")
        verbose_name_plural = _("cobros")
        ordering = ["-anio", "-mes", "apartamento__codigo"]
        constraints = [
            models.UniqueConstraint(
                fields=["apartamento", "anio", "mes"],
                name="un_cobro_por_apartamento_y_periodo",
            )
        ]

    def __str__(self):
        return f"{self.apartamento} · {self.periodo_display}"

    @property
    def periodo_display(self):
        return f"{MESES.get(self.mes, self.mes)} {self.anio}"

    # --- Cálculo de saldo ---------------------------------------------------
    @property
    def total_multas(self):
        """Suma de multas no exoneradas (la relación existe desde la Fase 5)."""
        try:
            total = self.multas.filter(exonerada=False).aggregate(s=Sum("monto"))["s"]
        except Exception:
            total = None
        return total or Decimal("0")

    @property
    def total_abonado(self):
        """Suma de abonos APROBADOS."""
        total = self.abonos.filter(estado_verificacion="APROBADO").aggregate(
            s=Sum("monto")
        )["s"]
        return total or Decimal("0")

    @property
    def total_pendiente_verificacion(self):
        """Suma de abonos aún PENDIENTES de verificación (no afectan el saldo)."""
        total = self.abonos.filter(estado_verificacion="PENDIENTE").aggregate(
            s=Sum("monto")
        )["s"]
        return total or Decimal("0")

    @property
    def cargo_total(self):
        return self.monto + self.total_multas

    @property
    def saldo(self):
        """Saldo confirmado con signo: negativo si hubo sobrepago (uso interno)."""
        return self.cargo_total - self.total_abonado

    @property
    def saldo_pendiente(self):
        """Monto que aún se debe (solo abonos aprobados). Nunca es negativo."""
        return self.saldo if self.saldo > 0 else Decimal("0")

    @property
    def saldo_por_cubrir(self):
        """Monto máximo que se puede abonar todavía.

        Descuenta también lo que ya está pendiente de verificación, para que el
        inquilino no registre abonos que sumen más de lo que debe (RF-005).
        """
        restante = self.cargo_total - self.total_abonado - self.total_pendiente_verificacion
        return restante if restante > 0 else Decimal("0")

    def calcular_estado(self):
        saldo = self.saldo
        if saldo <= 0:
            return self.Estado.PAGADO
        if self.total_abonado > 0:
            return self.Estado.PARCIAL
        if self.total_multas > 0:
            return self.Estado.CON_MULTA
        return self.Estado.PENDIENTE

    def actualizar_estado(self, guardar=True):
        """Recalcula y persiste el estado según el saldo actual."""
        self.estado = self.calcular_estado()
        if guardar:
            self.save(update_fields=["estado", "actualizado_en"])
        return self.estado
