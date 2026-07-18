"""Vistas del módulo de apartamentos (RF-002)."""

from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView, View

from apps.apartamentos.forms import ApartamentoForm
from apps.apartamentos.models import Apartamento
from apps.core.mixins import AdminRequeridoMixin


class ApartamentoListView(AdminRequeridoMixin, ListView):
    """Listado de apartamentos con búsqueda y filtro (RF-002)."""

    model = Apartamento
    template_name = "apartamentos/lista.html"
    context_object_name = "apartamentos"
    paginate_by = settings.PAGINACION_POR_PAGINA

    def get_queryset(self):
        qs = Apartamento.objects.all()
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(codigo__icontains=q)
                | Q(descripcion__icontains=q)
                | Q(contratos__inquilino__first_name__icontains=q)
                | Q(contratos__inquilino__last_name__icontains=q)
            ).distinct()
        estado = self.request.GET.get("estado", "")
        if estado == "activos":
            qs = qs.filter(activo=True)
        elif estado == "inactivos":
            qs = qs.filter(activo=False)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["estado"] = self.request.GET.get("estado", "")
        ctx["nav_activo"] = "apartamentos"
        total = Apartamento.objects.filter(activo=True).count()
        ocupados = (
            Apartamento.objects.filter(activo=True, contratos__activo=True)
            .distinct()
            .count()
        )
        ctx["total_activos"] = total
        ctx["ocupados"] = ocupados
        ctx["ocupacion"] = round(ocupados * 100 / total) if total else 0
        return ctx


class ApartamentoCreateView(AdminRequeridoMixin, CreateView):
    model = Apartamento
    form_class = ApartamentoForm
    template_name = "apartamentos/form.html"
    success_url = reverse_lazy("apartamentos:lista")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["nav_activo"] = "apartamentos"
        ctx["titulo"] = "Nuevo apartamento"
        return ctx

    def form_valid(self, form):
        messages.success(self.request, f"Apartamento «{form.instance.codigo}» creado.")
        return super().form_valid(form)


class ApartamentoUpdateView(AdminRequeridoMixin, UpdateView):
    model = Apartamento
    form_class = ApartamentoForm
    template_name = "apartamentos/form.html"

    def get_success_url(self):
        return reverse_lazy("apartamentos:detalle", args=[self.object.pk])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["nav_activo"] = "apartamentos"
        ctx["titulo"] = "Editar apartamento"
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Apartamento actualizado.")
        return super().form_valid(form)


class ApartamentoDetailView(AdminRequeridoMixin, DetailView):
    model = Apartamento
    template_name = "apartamentos/detalle.html"
    context_object_name = "apartamento"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["nav_activo"] = "apartamentos"
        ctx["contrato_activo"] = self.object.contrato_activo
        ctx["historial"] = self.object.contratos.select_related("inquilino").all()
        return ctx


class CambiarEstadoApartamentoView(AdminRequeridoMixin, View):
    """Activa o desactiva un apartamento (conserva su historial)."""

    def post(self, request, pk):
        apto = get_object_or_404(Apartamento, pk=pk)
        if apto.activo and apto.ocupado:
            messages.error(
                request,
                "No se puede desactivar: el apartamento tiene un contrato activo. "
                "Finalice el contrato primero.",
            )
            return redirect("apartamentos:detalle", pk=pk)
        apto.activo = not apto.activo
        apto.save(update_fields=["activo", "actualizado_en"])
        messages.success(
            request, f"Apartamento {'activado' if apto.activo else 'desactivado'}."
        )
        return redirect("apartamentos:detalle", pk=pk)
