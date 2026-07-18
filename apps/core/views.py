"""Vistas del núcleo: punto de entrada y despacho por rol."""

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render


@login_required
def inicio(request):
    """Despacha a cada usuario a su panel según el rol (RF-001)."""
    if request.user.es_admin:
        return _dashboard_admin(request)
    return _dashboard_inquilino(request)


def _dashboard_admin(request):
    """Panel del Administrador. Las métricas se enriquecen en fases posteriores."""
    from apps.cuentas.models import Usuario

    contexto = {
        "nav_activo": "inicio",
        "total_inquilinos": Usuario.objects.filter(
            rol=Usuario.Rol.INQUILINO, is_active=True
        ).count(),
        # Métricas de apartamentos/cobros/comprobantes: se conectan en Fases 3-4.
    }
    return render(request, "core/dashboard_admin.html", contexto)


def _dashboard_inquilino(request):
    """Panel del Inquilino. El saldo y los movimientos se conectan en la Fase 4."""
    contexto = {
        "nav_activo": "inicio",
    }
    return render(request, "core/dashboard_inquilino.html", contexto)


@login_required
def proximamente(request):
    """Placeholder para secciones aún no implementadas (se re-cablean por fase)."""
    seccion = request.GET.get("s", "Esta sección")
    return render(request, "core/proximamente.html", {"seccion": seccion})
