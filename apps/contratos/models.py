"""Modelos del módulo de contratos de arrendamiento (RF-003).

Un contrato vincula un apartamento con un inquilino por un periodo y un monto.
Regla clave: un apartamento no puede tener dos contratos activos a la vez
(garantizado por una restricción de unicidad condicional). Las renovaciones se
enlazan al contrato anterior para conservar el historial.
"""

from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import ModeloBase


class ContratoQuerySet(models.QuerySet):
    def activos(self):
        return self.filter(activo=True)

    def vigentes(self):
        """Contratos activos cuya fecha de vencimiento aún no ha pasado."""
        hoy = timezone.localdate()
        return self.filter(activo=True, fecha_vencimiento__gte=hoy)

    def por_vencer(self, dias=30):
        """Contratos activos que vencen dentro de ``dias`` (alerta del panel)."""
        hoy = timezone.localdate()
        limite = hoy + timedelta(days=dias)
        return self.filter(
            activo=True, fecha_vencimiento__gte=hoy, fecha_vencimiento__lte=limite
        ).order_by("fecha_vencimiento")

    def vencidos(self):
        hoy = timezone.localdate()
        return self.filter(activo=True, fecha_vencimiento__lt=hoy)


class Contrato(ModeloBase):
    """Contrato de arrendamiento de un apartamento a un inquilino (RF-003)."""

    apartamento = models.ForeignKey(
        "apartamentos.Apartamento",
        on_delete=models.PROTECT,
        related_name="contratos",
        verbose_name=_("apartamento"),
    )
    inquilino = models.ForeignKey(
        "cuentas.Usuario",
        on_delete=models.PROTECT,
        related_name="contratos",
        limit_choices_to={"rol": "INQUILINO"},
        verbose_name=_("inquilino"),
    )
    fecha_inicio = models.DateField(_("fecha de inicio"))
    fecha_vencimiento = models.DateField(_("fecha de vencimiento"))
    monto = models.DecimalField(_("monto mensual"), max_digits=12, decimal_places=2)
    activo = models.BooleanField(_("activo"), default=True)
    renovacion_de = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="renovaciones",
        verbose_name=_("renovación de"),
    )
    notas = models.TextField(_("notas"), blank=True)

    objects = ContratoQuerySet.as_manager()

    class Meta:
        verbose_name = _("contrato")
        verbose_name_plural = _("contratos")
        ordering = ["-fecha_inicio"]
        constraints = [
            models.UniqueConstraint(
                fields=["apartamento"],
                condition=Q(activo=True),
                name="un_contrato_activo_por_apartamento",
            )
        ]

    def __str__(self):
        return f"{self.apartamento} · {self.inquilino.get_full_name() or self.inquilino}"

    def clean(self):
        # Validaciones de negocio antes de guardar.
        if self.fecha_inicio and self.fecha_vencimiento:
            if self.fecha_vencimiento <= self.fecha_inicio:
                raise ValidationError(
                    {"fecha_vencimiento": _("La fecha de vencimiento debe ser posterior al inicio.")}
                )
        if self.inquilino_id and getattr(self.inquilino, "rol", None) != "INQUILINO":
            raise ValidationError({"inquilino": _("El usuario seleccionado no es un inquilino.")})
        # Un apartamento no puede tener dos contratos activos a la vez.
        if self.activo and self.apartamento_id:
            otros = Contrato.objects.filter(apartamento=self.apartamento, activo=True)
            if self.pk:
                otros = otros.exclude(pk=self.pk)
            if otros.exists():
                raise ValidationError(
                    _("El apartamento ya tiene un contrato activo. Finalícelo antes de crear otro.")
                )

    # --- Estado del periodo -------------------------------------------------
    @property
    def dias_para_vencer(self):
        return (self.fecha_vencimiento - timezone.localdate()).days

    @property
    def vencido(self):
        return self.activo and self.fecha_vencimiento < timezone.localdate()

    def vence_pronto(self, dias=30):
        return self.activo and 0 <= self.dias_para_vencer <= dias

    @property
    def porcentaje_periodo(self):
        """Porcentaje del periodo transcurrido (0-100), para la barra de progreso."""
        total = (self.fecha_vencimiento - self.fecha_inicio).days
        if total <= 0:
            return 100
        transcurrido = (timezone.localdate() - self.fecha_inicio).days
        return max(0, min(100, round(transcurrido * 100 / total)))

    # --- Acciones -----------------------------------------------------------
    def finalizar(self):
        """Marca el contrato como finalizado (inactivo)."""
        self.activo = False
        self.save(update_fields=["activo", "actualizado_en"])

    def renovar(self, fecha_inicio, fecha_vencimiento, monto, notas=""):
        """Finaliza este contrato y crea uno nuevo enlazado como renovación."""
        self.finalizar()
        return Contrato.objects.create(
            apartamento=self.apartamento,
            inquilino=self.inquilino,
            fecha_inicio=fecha_inicio,
            fecha_vencimiento=fecha_vencimiento,
            monto=monto,
            renovacion_de=self,
            notas=notas,
        )
