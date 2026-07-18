"""Mixins y decoradores de control de acceso por rol (RNF-003).

Centralizan la verificación de rol para las vistas basadas en clase y en función,
de modo que cada vista declare explícitamente quién puede acceder.
"""

from functools import wraps

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


class RolRequeridoMixin(LoginRequiredMixin):
    """Base: exige sesión activa y un rol concreto (definido en ``rol_requerido``)."""

    rol_requerido = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if self.rol_requerido and request.user.rol != self.rol_requerido:
            raise PermissionDenied("No tiene permisos para acceder a esta sección.")
        return super().dispatch(request, *args, **kwargs)


class AdminRequeridoMixin(RolRequeridoMixin):
    """Solo Administradores."""

    rol_requerido = "ADMIN"


class InquilinoRequeridoMixin(RolRequeridoMixin):
    """Solo Inquilinos."""

    rol_requerido = "INQUILINO"


def rol_requerido(rol):
    """Decorador para vistas basadas en función: exige sesión y un rol concreto."""

    def decorador(vista):
        @wraps(vista)
        def envoltura(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("cuentas:login")
            if request.user.rol != rol:
                raise PermissionDenied("No tiene permisos para acceder a esta sección.")
            return vista(request, *args, **kwargs)

        return envoltura

    return decorador


admin_requerido = rol_requerido("ADMIN")
inquilino_requerido = rol_requerido("INQUILINO")
