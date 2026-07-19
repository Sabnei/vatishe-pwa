"""Vistas del módulo de cobros (RF-004)."""

from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, FormView, ListView, UpdateView, View

from apps.cobros.forms import CobroAjusteForm, ExonerarMultaForm, GenerarCobrosForm
from apps.cobros.models import Cobro, Multa
from apps.cobros.services import aplicar_multas, generar_cobros
from apps.core.mixins import AdminRequeridoMixin


class CobroListView(AdminRequeridoMixin, ListView):
    """Listado de cobros con filtros por estado y periodo (RF-004)."""

    model = Cobro
    template_name = "cobros/lista.html"
    context_object_name = "cobros"
    paginate_by = settings.PAGINACION_POR_PAGINA

    def get_queryset(self):
        qs = Cobro.objects.select_related("apartamento", "inquilino")
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(apartamento__codigo__icontains=q)
                | Q(inquilino__first_name__icontains=q)
                | Q(inquilino__last_name__icontains=q)
            )
        estado = self.request.GET.get("estado", "")
        if estado:
            qs = qs.filter(estado=estado)
        mes = self.request.GET.get("mes", "")
        anio = self.request.GET.get("anio", "")
        if mes.isdigit():
            qs = qs.filter(mes=int(mes))
        if anio.isdigit():
            qs = qs.filter(anio=int(anio))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["estado"] = self.request.GET.get("estado", "")
        ctx["mes"] = self.request.GET.get("mes", "")
        ctx["anio"] = self.request.GET.get("anio", "")
        ctx["estados"] = Cobro.Estado.choices
        ctx["nav_activo"] = "cobros"
        return ctx


class CobroDetailView(AdminRequeridoMixin, DetailView):
    model = Cobro
    template_name = "cobros/detalle.html"
    context_object_name = "cobro"

    def get_queryset(self):
        return Cobro.objects.select_related("apartamento", "inquilino", "contrato")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["abonos"] = self.object.abonos.select_related("registrado_por").all()
        ctx["nav_activo"] = "cobros"
        return ctx


class CobroAjusteView(AdminRequeridoMixin, UpdateView):
    """Ajuste manual del monto o vencimiento de un cobro (RF-004)."""

    model = Cobro
    form_class = CobroAjusteForm
    template_name = "cobros/ajuste.html"

    def get_success_url(self):
        return reverse_lazy("cobros:detalle", args=[self.object.pk])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["nav_activo"] = "cobros"
        return ctx

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        self.object.actualizar_estado()
        messages.success(self.request, "Cobro ajustado correctamente.")
        return respuesta


class GenerarCobrosView(AdminRequeridoMixin, FormView):
    """Genera los cobros mensuales de todos los contratos vigentes (RF-004)."""

    template_name = "cobros/generar.html"
    form_class = GenerarCobrosForm
    success_url = reverse_lazy("cobros:lista")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["nav_activo"] = "cobros"
        return ctx

    def form_valid(self, form):
        resultado = generar_cobros(form.cleaned_data["anio"], form.cleaned_data["mes"])
        if resultado["creados"]:
            messages.success(
                self.request,
                f"Se generaron {resultado['creados']} cobro(s). "
                f"{resultado['omitidos']} ya existían.",
            )
        else:
            messages.info(
                self.request,
                f"No se generaron cobros nuevos ({resultado['omitidos']} ya existían).",
            )
        return super().form_valid(form)


# --------------------------------------------------------------------------- #
# Multas por morosidad (RF-007)
# --------------------------------------------------------------------------- #
class MultaListView(AdminRequeridoMixin, ListView):
    """Gestión de multas con filtro por estado (RF-007, HU-09)."""

    model = Multa
    template_name = "cobros/multas_lista.html"
    context_object_name = "multas"
    paginate_by = settings.PAGINACION_POR_PAGINA

    def get_queryset(self):
        qs = Multa.objects.select_related("cobro", "cobro__apartamento", "cobro__inquilino")
        estado = self.request.GET.get("estado", "activas")
        if estado == "activas":
            qs = qs.filter(exonerada=False)
        elif estado == "exoneradas":
            qs = qs.filter(exonerada=True)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["estado"] = self.request.GET.get("estado", "activas")
        ctx["nav_activo"] = "cobros"
        return ctx


class MultaDetailView(AdminRequeridoMixin, DetailView):
    model = Multa
    template_name = "cobros/multa_detalle.html"
    context_object_name = "multa"

    def get_queryset(self):
        return Multa.objects.select_related("cobro", "cobro__apartamento", "cobro__inquilino")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["nav_activo"] = "cobros"
        return ctx


class ExonerarMultaView(AdminRequeridoMixin, FormView):
    """Exonera una multa con un motivo obligatorio (RF-007, HU-09)."""

    template_name = "cobros/exonerar_multa.html"
    form_class = ExonerarMultaForm

    def dispatch(self, request, *args, **kwargs):
        self.multa = get_object_or_404(Multa, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["multa"] = self.multa
        ctx["nav_activo"] = "cobros"
        return ctx

    def form_valid(self, form):
        if not self.multa.exonerada:
            self.multa.exonerar(self.request.user, form.cleaned_data["motivo"])
            messages.success(self.request, "Multa exonerada correctamente.")
        return redirect("cobros:multa_detalle", pk=self.multa.pk)


class AplicarMultasView(AdminRequeridoMixin, View):
    """Aplica manualmente las multas por morosidad a la fecha (RF-007)."""

    def post(self, request):
        resultado = aplicar_multas()
        if resultado["aplicadas"]:
            messages.success(
                request,
                f"Se aplicaron {resultado['aplicadas']} multa(s) por un total de "
                f"₡{resultado['total']:,.0f}.",
            )
        else:
            messages.info(request, "No había cobros vencidos con saldo para multar.")
        return redirect("cobros:multas_lista")
