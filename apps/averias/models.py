"""Modelos del módulo de averías (RF-008).

El inquilino reporta una avería (con fotos opcionales); el Administrador cambia
su estado y registra el gasto de reparación. Cada cambio de estado notifica al
inquilino. Las fotos se guardan en almacenamiento privado.
"""

import uuid

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import ModeloBase


def ruta_foto_averia(instance, filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
    apto = instance.averia.apartamento_id if instance.averia_id else "s"
    return f"averias/{apto}/{uuid.uuid4().hex}.{ext}"


class Averia(ModeloBase):
    """Reporte de avería de un apartamento (RF-008)."""

    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", _("Pendiente")
        EN_REPARACION = "EN_REPARACION", _("En reparación")
        SOLUCIONADO = "SOLUCIONADO", _("Solucionado")

    class Area(models.TextChoices):
        COCINA = "COCINA", _("Cocina")
        BANO = "BANO", _("Baño")
        SALA = "SALA", _("Sala")
        DORMITORIO = "DORMITORIO", _("Dormitorio")
        EXTERIOR = "EXTERIOR", _("Área exterior")
        OTRO = "OTRO", _("Otro")

    apartamento = models.ForeignKey(
        "apartamentos.Apartamento",
        on_delete=models.PROTECT,
        related_name="averias",
        verbose_name=_("apartamento"),
    )
    inquilino = models.ForeignKey(
        "cuentas.Usuario",
        on_delete=models.PROTECT,
        related_name="averias",
        verbose_name=_("inquilino"),
    )
    area = models.CharField(_("área afectada"), max_length=12, choices=Area.choices)
    descripcion = models.TextField(_("descripción"))
    estado = models.CharField(
        _("estado"), max_length=15, choices=Estado.choices, default=Estado.PENDIENTE
    )
    gasto = models.DecimalField(
        _("gasto de reparación"), max_digits=12, decimal_places=2, default=0
    )
    notas_admin = models.TextField(_("notas del administrador"), blank=True)
    atendida_por = models.ForeignKey(
        "cuentas.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="averias_atendidas",
        verbose_name=_("atendida por"),
    )
    fecha_solucion = models.DateField(_("fecha de solución"), null=True, blank=True)

    class Meta:
        verbose_name = _("avería")
        verbose_name_plural = _("averías")
        ordering = ["-creado_en"]

    def __str__(self):
        return f"{self.get_area_display()} · {self.apartamento}"

    @property
    def icono(self):
        """Icono de Material Symbols según el área (para la UI)."""
        return {
            "COCINA": "kitchen",
            "BANO": "bathroom",
            "SALA": "weekend",
            "DORMITORIO": "bed",
            "EXTERIOR": "yard",
            "OTRO": "build",
        }.get(self.area, "build")

    def cambiar_estado(self, nuevo_estado, admin, gasto=None, notas=None):
        """Actualiza el estado (y opcionalmente gasto/notas) y marca al responsable."""
        self.estado = nuevo_estado
        self.atendida_por = admin
        if gasto is not None:
            self.gasto = gasto
        if notas is not None:
            self.notas_admin = notas
        if nuevo_estado == self.Estado.SOLUCIONADO and not self.fecha_solucion:
            self.fecha_solucion = timezone.localdate()
        self.save()


class FotoAveria(ModeloBase):
    """Foto adjunta a un reporte de avería (privada)."""

    averia = models.ForeignKey(
        Averia, on_delete=models.CASCADE, related_name="fotos", verbose_name=_("avería")
    )
    imagen = models.FileField(_("imagen"), upload_to=ruta_foto_averia)

    class Meta:
        verbose_name = _("foto de avería")
        verbose_name_plural = _("fotos de avería")

    def __str__(self):
        return f"Foto de {self.averia}"
