"""Vistas del módulo de contratos (RF-003)."""

from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import CreateView, DetailView, FormView, ListView, TemplateView, View

from apps.apartamentos.models import Apartamento
from apps.contratos.forms import ContratoForm, RenovarContratoForm
from apps.contratos.models import Contrato
from apps.core.mixins import AdminRequeridoMixin, InquilinoRequeridoMixin


class ContratoListView(AdminRequeridoMixin, ListView):
    """Gestión de contratos con filtros y alerta de vencimiento (RF-003, HU-08)."""

    model = Contrato
    template_name = "contratos/lista.html"
    context_object_name = "contratos"
    paginate_by = settings.PAGINACION_POR_PAGINA

    def get_queryset(self):
        qs = Contrato.objects.select_related("apartamento", "inquilino")
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(apartamento__codigo__icontains=q)
                | Q(inquilino__first_name__icontains=q)
                | Q(inquilino__last_name__icontains=q)
            )
        estado = self.request.GET.get("estado", "activos")
        if estado == "activos":
            qs = qs.filter(activo=True)
        elif estado == "finalizados":
            qs = qs.filter(activo=False)
        elif estado == "por_vencer":
            qs = qs.por_vencer(dias=30)
        elif estado == "vencidos":
            qs = qs.vencidos()
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["estado"] = self.request.GET.get("estado", "activos")
        ctx["nav_activo"] = "contratos"
        ctx["total_por_vencer"] = Contrato.objects.por_vencer(dias=30).count()
        return ctx


class ContratoCreateView(AdminRequeridoMixin, CreateView):
    """Alta de contrato. Si viene ?apartamento=<pk>, se fija ese apartamento."""

    model = Contrato
    form_class = ContratoForm
    template_name = "contratos/form.html"

    def _apartamento_preseleccionado(self):
        pk = self.request.GET.get("apartamento")
        if pk:
            return get_object_or_404(Apartamento, pk=pk, activo=True)
        return None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        apto = self._apartamento_preseleccionado()
        if apto:
            kwargs["apartamento"] = apto
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["nav_activo"] = "contratos"
        ctx["titulo"] = "Nuevo contrato"
        ctx["apartamento_fijo"] = self._apartamento_preseleccionado()
        return ctx

    def get_success_url(self):
        return reverse("contratos:detalle", args=[self.object.pk])

    def form_valid(self, form):
        messages.success(self.request, "Contrato registrado correctamente.")
        return super().form_valid(form)


class ContratoDetailView(AdminRequeridoMixin, DetailView):
    model = Contrato
    template_name = "contratos/detalle.html"
    context_object_name = "contrato"

    def get_queryset(self):
        return Contrato.objects.select_related("apartamento", "inquilino")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["nav_activo"] = "contratos"
        return ctx


class FinalizarContratoView(AdminRequeridoMixin, View):
    def post(self, request, pk):
        contrato = get_object_or_404(Contrato, pk=pk)
        if contrato.activo:
            contrato.finalizar()
            messages.success(request, "Contrato finalizado.")
        return redirect("contratos:detalle", pk=pk)


class RenovarContratoView(AdminRequeridoMixin, FormView):
    """Renueva un contrato: lo finaliza y crea uno nuevo enlazado (RF-003)."""

    template_name = "contratos/renovar.html"
    form_class = RenovarContratoForm

    def dispatch(self, request, *args, **kwargs):
        self.contrato = get_object_or_404(Contrato, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        return {"monto": self.contrato.monto}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["nav_activo"] = "contratos"
        ctx["contrato"] = self.contrato
        return ctx

    def form_valid(self, form):
        self.nuevo = self.contrato.renovar(
            fecha_inicio=form.cleaned_data["fecha_inicio"],
            fecha_vencimiento=form.cleaned_data["fecha_vencimiento"],
            monto=form.cleaned_data["monto"],
            notas=form.cleaned_data.get("notas", ""),
        )
        messages.success(self.request, "Contrato renovado correctamente.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("contratos:detalle", args=[self.nuevo.pk])


class MiContratoView(InquilinoRequeridoMixin, TemplateView):
    """El inquilino consulta su contrato vigente y su historial (RF-003)."""

    template_name = "contratos/mi_contrato.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        contratos = (
            Contrato.objects.filter(inquilino=self.request.user)
            .select_related("apartamento")
            .order_by("-fecha_inicio")
        )
        # Un inquilino puede tener varios contratos activos (uno por apartamento).
        ctx["contratos_activos"] = contratos.filter(activo=True)
        ctx["historial"] = contratos.filter(activo=False)
        ctx["nav_activo"] = "contrato"
        return ctx
