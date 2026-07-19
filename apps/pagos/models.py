"""Modelos del módulo de pagos: abonos y comprobantes (RF-005/RF-006).

El inquilino registra un abono con su comprobante; queda PENDIENTE de
verificación y no afecta el saldo hasta que el Administrador lo aprueba. El
comprobante se guarda en almacenamiento privado (Supabase Storage en prod) y se
sirve solo mediante una vista protegida (requiere sesión).
"""

import os
import uuid

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import ModeloBase


def ruta_comprobante(instance, filename):
    """Ruta privada del comprobante: comprobantes/<inquilino>/<uuid>.<ext>."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "dat"
    inquilino_id = instance.cobro.inquilino_id if instance.cobro_id else "sin_inquilino"
    return f"comprobantes/{inquilino_id}/{uuid.uuid4().hex}.{ext}"


class Abono(ModeloBase):
    """Abono registrado por el inquilino, pendiente de verificación (RF-005)."""

    class Metodo(models.TextChoices):
        SINPE = "SINPE", _("SINPE Móvil")
        TRANSFERENCIA = "TRANSFERENCIA", _("Transferencia")
        DEPOSITO = "DEPOSITO", _("Depósito")

    class Verificacion(models.TextChoices):
        PENDIENTE = "PENDIENTE", _("Pendiente")
        APROBADO = "APROBADO", _("Aprobado")
        RECHAZADO = "RECHAZADO", _("Rechazado")

    cobro = models.ForeignKey(
        "cobros.Cobro",
        on_delete=models.CASCADE,
        related_name="abonos",
        verbose_name=_("cobro"),
    )
    monto = models.DecimalField(_("monto"), max_digits=12, decimal_places=2)
    fecha = models.DateField(_("fecha del pago"))
    metodo = models.CharField(_("método"), max_length=15, choices=Metodo.choices)
    referencia = models.CharField(_("referencia"), max_length=80, blank=True)
    observaciones = models.TextField(_("observaciones"), blank=True)
    comprobante = models.FileField(
        _("comprobante"), upload_to=ruta_comprobante
    )
    estado_verificacion = models.CharField(
        _("estado de verificación"),
        max_length=10,
        choices=Verificacion.choices,
        default=Verificacion.PENDIENTE,
    )
    motivo_rechazo = models.TextField(_("motivo de rechazo"), blank=True)
    registrado_por = models.ForeignKey(
        "cuentas.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        related_name="abonos_registrados",
        verbose_name=_("registrado por"),
    )
    verificado_por = models.ForeignKey(
        "cuentas.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="abonos_verificados",
        verbose_name=_("verificado por"),
    )
    verificado_en = models.DateTimeField(_("verificado en"), null=True, blank=True)

    class Meta:
        verbose_name = _("abono")
        verbose_name_plural = _("abonos")
        ordering = ["-fecha", "-creado_en"]

    def __str__(self):
        return f"Abono {self.monto} · {self.cobro}"

    # --- Estado -------------------------------------------------------------
    @property
    def pendiente(self):
        return self.estado_verificacion == self.Verificacion.PENDIENTE

    @property
    def aprobado(self):
        return self.estado_verificacion == self.Verificacion.APROBADO

    @property
    def rechazado(self):
        return self.estado_verificacion == self.Verificacion.RECHAZADO

    @property
    def nombre_archivo(self):
        return os.path.basename(self.comprobante.name) if self.comprobante else ""

    @property
    def es_pdf(self):
        return self.comprobante and self.comprobante.name.lower().endswith(".pdf")

    # --- Acciones de verificación (RF-006) ----------------------------------
    def aprobar(self, admin):
        self.estado_verificacion = self.Verificacion.APROBADO
        self.motivo_rechazo = ""
        self.verificado_por = admin
        self.verificado_en = timezone.now()
        self.save(update_fields=[
            "estado_verificacion", "motivo_rechazo", "verificado_por",
            "verificado_en", "actualizado_en",
        ])
        self.cobro.actualizar_estado()

    def rechazar(self, admin, motivo):
        self.estado_verificacion = self.Verificacion.RECHAZADO
        self.motivo_rechazo = motivo
        self.verificado_por = admin
        self.verificado_en = timezone.now()
        self.save(update_fields=[
            "estado_verificacion", "motivo_rechazo", "verificado_por",
            "verificado_en", "actualizado_en",
        ])
        self.cobro.actualizar_estado()
