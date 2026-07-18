"""Modelos del núcleo: configuración del sistema y registro de correos.

- ConfiguracionSistema: singleton con parámetros globales (porcentaje de multa,
  días de anticipación del recordatorio). Editable solo por el Administrador.
- RegistroCorreo: bitácora de correos enviados para evitar duplicados (RF-010).
"""

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class ModeloBase(models.Model):
    """Base abstracta con marcas de tiempo reutilizable por el resto de apps."""

    creado_en = models.DateTimeField(_("creado en"), auto_now_add=True)
    actualizado_en = models.DateTimeField(_("actualizado en"), auto_now=True)

    class Meta:
        abstract = True


class ConfiguracionSistema(ModeloBase):
    """Parámetros globales del sistema (patrón singleton: siempre pk=1)."""

    SINGLETON_ID = 1

    porcentaje_multa = models.DecimalField(
        _("porcentaje de multa por morosidad"),
        max_digits=5,
        decimal_places=2,
        default=Decimal("10.00"),
        validators=[MinValueValidator(Decimal("0"))],
        help_text=_("Porcentaje aplicado sobre el saldo pendiente al vencer (RF-007)."),
    )
    monto_multa_fijo = models.DecimalField(
        _("monto fijo de multa"),
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0"))],
        help_text=_("Si es mayor que 0, se usa en lugar del porcentaje."),
    )
    dias_anticipacion_recordatorio = models.PositiveIntegerField(
        _("días de anticipación del recordatorio"),
        default=3,
        help_text=_("Días antes del vencimiento para enviar el recordatorio (RF-010)."),
    )
    nombre_empresa = models.CharField(
        _("nombre de la empresa"), max_length=150, default="VATISHE S.R.L."
    )

    class Meta:
        verbose_name = _("configuración del sistema")
        verbose_name_plural = _("configuración del sistema")

    def __str__(self):
        return _("Configuración del sistema")

    def save(self, *args, **kwargs):
        # Fuerza el patrón singleton.
        self.pk = self.SINGLETON_ID
        super().save(*args, **kwargs)

    @classmethod
    def cargar(cls):
        """Devuelve la configuración, creándola con valores por defecto si no existe."""
        obj, _creado = cls.objects.get_or_create(pk=cls.SINGLETON_ID)
        return obj

    @property
    def usa_monto_fijo(self):
        return self.monto_multa_fijo > 0


class RegistroCorreo(ModeloBase):
    """Bitácora de correos automáticos para evitar envíos duplicados (RF-010)."""

    class Tipo(models.TextChoices):
        RECORDATORIO = "RECORDATORIO", _("Recordatorio de pago")
        COMPROBANTE_RECHAZADO = "COMP_RECHAZADO", _("Comprobante rechazado")
        AVERIA_ACTUALIZADA = "AVERIA_ACT", _("Avería actualizada")

    tipo = models.CharField(_("tipo"), max_length=20, choices=Tipo.choices)
    destinatario = models.EmailField(_("destinatario"))
    asunto = models.CharField(_("asunto"), max_length=255)
    # Clave lógica para deduplicar (p. ej. "recordatorio:cobro:42").
    clave_unicidad = models.CharField(_("clave de unicidad"), max_length=120, blank=True)
    exitoso = models.BooleanField(_("enviado con éxito"), default=True)
    detalle_error = models.TextField(_("detalle de error"), blank=True)

    class Meta:
        verbose_name = _("registro de correo")
        verbose_name_plural = _("registros de correo")
        ordering = ["-creado_en"]
        indexes = [models.Index(fields=["tipo", "clave_unicidad"])]

    def __str__(self):
        return f"{self.get_tipo_display()} → {self.destinatario}"
