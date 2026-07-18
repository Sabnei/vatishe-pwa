"""Formularios del módulo de seguridad y usuarios."""

from django import forms
from django.contrib.auth.forms import (
    PasswordChangeForm,
    PasswordResetForm,
    SetPasswordForm,
)
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from apps.cuentas.models import PerfilInquilino, Usuario

# Clases de estilo reutilizables para alinear los widgets con el tema.
_INPUT = "form-input"


class _EstiloWidgetsMixin:
    """Aplica las clases del design system a todos los widgets del formulario."""

    def _estilizar(self):
        for campo in self.fields.values():
            widget = campo.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "h-5 w-5 rounded accent-accent")
            elif isinstance(widget, forms.Textarea):
                widget.attrs.setdefault("class", _INPUT)
                widget.attrs.setdefault("rows", 3)
            else:
                widget.attrs.setdefault("class", _INPUT)


class CambiarContrasenaForm(_EstiloWidgetsMixin, PasswordChangeForm):
    """Cambio de contraseña estilizado con el tema."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._estilizar()


class EstablecerContrasenaForm(_EstiloWidgetsMixin, SetPasswordForm):
    """Definición de nueva contraseña tras recuperación, estilizada."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._estilizar()


class RecuperarContrasenaForm(_EstiloWidgetsMixin, PasswordResetForm):
    """Solicitud de recuperación por correo, estilizada."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._estilizar()


class NuevoInquilinoForm(_EstiloWidgetsMixin, forms.ModelForm):
    """Alta de un inquilino por el Administrador (RF-001/RF-002).

    Crea el ``Usuario`` con rol INQUILINO y su ``PerfilInquilino`` asociado.
    El correo es obligatorio para recordatorios y notificaciones.
    """

    password1 = forms.CharField(
        label="Contraseña", widget=forms.PasswordInput, strip=False
    )
    password2 = forms.CharField(
        label="Confirmar contraseña", widget=forms.PasswordInput, strip=False
    )
    cedula = forms.CharField(label="Cédula", max_length=30, required=False)
    telefono_alterno = forms.CharField(
        label="Teléfono alterno", max_length=30, required=False
    )

    class Meta:
        model = Usuario
        fields = ["username", "first_name", "last_name", "email", "telefono"]
        labels = {
            "username": "Usuario",
            "first_name": "Nombre",
            "last_name": "Apellidos",
            "email": "Correo electrónico",
            "telefono": "Teléfono",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True
        self.fields["first_name"].required = True
        self._estilizar()

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if Usuario.objects.filter(email__iexact=email).exists():
            raise ValidationError("Ya existe un usuario con este correo.")
        return email

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise ValidationError("Las contraseñas no coinciden.")
        validate_password(p2)
        return p2

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.rol = Usuario.Rol.INQUILINO
        usuario.set_password(self.cleaned_data["password1"])
        if commit:
            usuario.save()
            PerfilInquilino.objects.create(
                usuario=usuario,
                cedula=self.cleaned_data.get("cedula", ""),
                telefono_alterno=self.cleaned_data.get("telefono_alterno", ""),
            )
        return usuario


class EditarInquilinoForm(_EstiloWidgetsMixin, forms.ModelForm):
    """Edición de datos de un inquilino por el Administrador."""

    cedula = forms.CharField(label="Cédula", max_length=30, required=False)
    telefono_alterno = forms.CharField(
        label="Teléfono alterno", max_length=30, required=False
    )
    contacto_emergencia = forms.CharField(
        label="Contacto de emergencia", max_length=150, required=False
    )
    notas = forms.CharField(label="Notas", widget=forms.Textarea, required=False)

    class Meta:
        model = Usuario
        fields = ["username", "first_name", "last_name", "email", "telefono"]
        labels = {
            "username": "Usuario",
            "first_name": "Nombre",
            "last_name": "Apellidos",
            "email": "Correo electrónico",
            "telefono": "Teléfono",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True
        perfil = getattr(self.instance, "perfil_inquilino", None)
        if perfil:
            self.fields["cedula"].initial = perfil.cedula
            self.fields["telefono_alterno"].initial = perfil.telefono_alterno
            self.fields["contacto_emergencia"].initial = perfil.contacto_emergencia
            self.fields["notas"].initial = perfil.notas
        self._estilizar()

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if Usuario.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Ya existe otro usuario con este correo.")
        return email

    def save(self, commit=True):
        usuario = super().save(commit=commit)
        if commit:
            perfil, _ = PerfilInquilino.objects.get_or_create(usuario=usuario)
            perfil.cedula = self.cleaned_data.get("cedula", "")
            perfil.telefono_alterno = self.cleaned_data.get("telefono_alterno", "")
            perfil.contacto_emergencia = self.cleaned_data.get("contacto_emergencia", "")
            perfil.notas = self.cleaned_data.get("notas", "")
            perfil.save()
        return usuario


class MiPerfilForm(_EstiloWidgetsMixin, forms.ModelForm):
    """Edición del propio perfil por el Inquilino (datos de contacto)."""

    cedula = forms.CharField(label="Cédula", max_length=30, required=False)
    telefono_alterno = forms.CharField(
        label="Teléfono alterno", max_length=30, required=False
    )
    contacto_emergencia = forms.CharField(
        label="Contacto de emergencia", max_length=150, required=False
    )

    class Meta:
        model = Usuario
        fields = ["first_name", "last_name", "telefono"]
        labels = {
            "first_name": "Nombre",
            "last_name": "Apellidos",
            "telefono": "Teléfono",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        perfil = getattr(self.instance, "perfil_inquilino", None)
        if perfil:
            self.fields["cedula"].initial = perfil.cedula
            self.fields["telefono_alterno"].initial = perfil.telefono_alterno
            self.fields["contacto_emergencia"].initial = perfil.contacto_emergencia
        self._estilizar()

    def save(self, commit=True):
        usuario = super().save(commit=commit)
        if commit:
            perfil, _ = PerfilInquilino.objects.get_or_create(usuario=usuario)
            perfil.cedula = self.cleaned_data.get("cedula", "")
            perfil.telefono_alterno = self.cleaned_data.get("telefono_alterno", "")
            perfil.contacto_emergencia = self.cleaned_data.get("contacto_emergencia", "")
            perfil.save()
        return usuario
