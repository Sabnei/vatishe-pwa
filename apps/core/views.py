"""Vistas del núcleo: punto de entrada y despacho por rol."""

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST


@login_required
def inicio(request):
    """Despacha a cada usuario a su panel según el rol (RF-001)."""
    if request.user.es_admin:
        return _dashboard_admin(request)
    return _dashboard_inquilino(request)


def _dashboard_admin(request):
    """Panel del Administrador con métricas y alertas en vivo."""
    from apps.apartamentos.models import Apartamento
    from apps.averias.models import Averia
    from apps.cobros.models import Cobro
    from apps.contratos.models import Contrato
    from apps.cuentas.models import Usuario
    from apps.pagos.models import Abono

    contratos_por_vencer = Contrato.objects.por_vencer(dias=30).select_related(
        "apartamento", "inquilino"
    )
    pendientes_verificacion = (
        Abono.objects.filter(estado_verificacion=Abono.Verificacion.PENDIENTE)
        .select_related("cobro", "cobro__apartamento", "cobro__inquilino")
    )
    cobros_pendientes = Cobro.objects.exclude(estado=Cobro.Estado.PAGADO).count()
    contexto = {
        "nav_activo": "inicio",
        "total_inquilinos": Usuario.objects.filter(
            rol=Usuario.Rol.INQUILINO, is_active=True
        ).count(),
        "total_apartamentos": Apartamento.objects.filter(activo=True).count(),
        "cobros_pendientes": cobros_pendientes,
        "num_por_verificar": pendientes_verificacion.count(),
        "comprobantes_pendientes": pendientes_verificacion[:5],
        "contratos_por_vencer": contratos_por_vencer[:5],
        "num_por_vencer": contratos_por_vencer.count(),
        "num_averias_pendientes": Averia.objects.exclude(
            estado=Averia.Estado.SOLUCIONADO
        ).count(),
    }
    return render(request, "core/dashboard_admin.html", contexto)


def _dashboard_inquilino(request):
    """Panel del Inquilino con su saldo y el cobro del mes en vivo."""
    from datetime import date
    from decimal import Decimal

    from apps.cobros.models import Cobro
    from apps.pagos.models import Abono

    cobros = Cobro.objects.filter(inquilino=request.user)
    # Saldo total pendiente = suma de saldos pendientes (nunca negativos; un
    # sobrepago en un cobro no reduce la deuda de otro).
    saldo_total = sum(
        (c.saldo_pendiente for c in cobros.exclude(estado=Cobro.Estado.PAGADO)),
        Decimal("0"),
    )
    hoy = date.today()
    cobro_mes = cobros.filter(anio=hoy.year, mes=hoy.month).first()
    contexto = {
        "nav_activo": "inicio",
        "saldo_total": saldo_total,
        "cobro_mes": cobro_mes,
        "al_dia": saldo_total <= 0,
        "abonos_recientes": (
            Abono.objects.filter(cobro__inquilino=request.user).select_related("cobro")[:3]
        ),
    }
    return render(request, "core/dashboard_inquilino.html", contexto)


@login_required
def proximamente(request):
    """Placeholder para secciones aún no implementadas (se re-cablean por fase)."""
    seccion = request.GET.get("s", "Esta sección")
    return render(request, "core/proximamente.html", {"seccion": seccion})


def service_worker(request):
    """Sirve el service worker en la raíz para que su scope sea todo el sitio."""
    respuesta = render(request, "pwa/sw.js", content_type="application/javascript")
    respuesta["Service-Worker-Allowed"] = "/"
    respuesta["Cache-Control"] = "no-cache"
    return respuesta


def offline(request):
    """Página mostrada por el service worker cuando no hay conexión (PWA)."""
    return render(request, "offline.html")


@csrf_exempt
@require_POST
def cron_tareas_diarias(request):
    """Dispara las tareas diarias por HTTP, protegido con CRON_TOKEN.

    Pensado para hosting sin cron nativo (p. ej. Render free): un cron externo
    hace POST a esta URL con el token. Sin token válido responde 403.
    """
    from apps.core.tareas import ejecutar_tareas_diarias

    token = request.headers.get("X-Cron-Token") or request.POST.get("token", "")
    if not settings.CRON_TOKEN or token != settings.CRON_TOKEN:
        return HttpResponseForbidden("Token inválido.")
    return JsonResponse({"ok": True, "resultado": ejecutar_tareas_diarias()})
