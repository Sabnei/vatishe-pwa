"""Modelos de seguridad y usuarios (Módulo 1).

Define el usuario personalizado con rol (Administrador / Inquilino) y el perfil
extendido del inquilino. El rol se resuelve en el propio modelo de usuario para
simplificar el control de acceso en vistas y plantillas.
"""

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UsuarioManager(BaseUserManager):
    """Manager que usa el correo como dato obligatorio y crea usuarios por rol."""

    use_in_migrations = True

    def _crear_usuario(self, username, email, password, **extra_fields):
        if not username:
            raise ValueError(_("El nombre de usuario es obligatorio."))
        email = self.normalize_email(email)
        usuario = self.model(username=username, email=email, **extra_fields)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_user(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("rol", Usuario.Rol.INQUILINO)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._crear_usuario(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("rol", Usuario.Rol.ADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("El superusuario debe tener is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("El superusuario debe tener is_superuser=True."))
        return self._crear_usuario(username, email, password, **extra_fields)


class Usuario(AbstractUser):
    """Usuario del sistema con rol. Solo el Administrador crea usuarios (RF-001)."""

    class Rol(models.TextChoices):
        ADMIN = "ADMIN", _("Administrador")
        INQUILINO = "INQUILINO", _("Inquilino")

    # El correo es obligatorio para el inquilino (RF-002) y para recordatorios.
    email = models.EmailField(_("correo electrónico"), unique=True)
    rol = models.CharField(
        _("rol"), max_length=10, choices=Rol.choices, default=Rol.INQUILINO
    )
    telefono = models.CharField(_("teléfono"), max_length=30, blank=True)

    objects = UsuarioManager()

    class Meta:
        verbose_name = _("usuario")
        verbose_name_plural = _("usuarios")

    def __str__(self):
        nombre = self.get_full_name()
        return f"{nombre} ({self.get_rol_display()})" if nombre else self.username

    @property
    def es_admin(self):
        return self.rol == self.Rol.ADMIN

    @property
    def es_inquilino(self):
        return self.rol == self.Rol.INQUILINO


class PerfilInquilino(models.Model):
    """Datos adicionales del inquilino. Se conserva aunque se desactive (RF-002)."""

    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name="perfil_inquilino",
        verbose_name=_("usuario"),
    )
    cedula = models.CharField(_("cédula"), max_length=30, blank=True)
    telefono_alterno = models.CharField(_("teléfono alterno"), max_length=30, blank=True)
    contacto_emergencia = models.CharField(
        _("contacto de emergencia"), max_length=150, blank=True
    )
    notas = models.TextField(_("notas"), blank=True)
    creado_en = models.DateTimeField(_("creado en"), auto_now_add=True)
    actualizado_en = models.DateTimeField(_("actualizado en"), auto_now=True)

    class Meta:
        verbose_name = _("perfil de inquilino")
        verbose_name_plural = _("perfiles de inquilino")

    def __str__(self):
        return f"Perfil de {self.usuario}"
