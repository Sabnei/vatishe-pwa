"""Vistas del módulo de averías (RF-008)."""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, View

from apps.apartamentos.models import Apartamento
from apps.averias.forms import GestionAveriaForm, ReportarAveriaForm
from apps.averias.models import Averia, FotoAveria
from apps.core.imagenes import comprimir_imagen
from apps.core.mixins import AdminRequeridoMixin, InquilinoRequeridoMixin
from apps.core.models import RegistroCorreo
from apps.core.notificaciones import enviar_correo


def _apartamentos_del_inquilino(usuario):
    """Apartamentos con contrato activo del inquilino."""
    return Apartamento.objects.filter(
        contratos__inquilino=usuario, contratos__activo=True
    ).distinct()


# --------------------------------------------------------------------------- #
# Inquilino
# --------------------------------------------------------------------------- #
class ReportarAveriaView(InquilinoRequeridoMixin, CreateView):
    """El inquilino reporta una avería con fotos opcionales (RF-008, HU-06)."""

    model = Averia
    form_class = ReportarAveriaForm
    template_name = "averias/reportar.html"

    def dispatch(self, request, *args, **kwargs):
        self.apartamentos = _apartamentos_del_inquilino(request.user)
        if not self.apartamentos.exists():
            messages.error(
                request, "No tiene un apartamento asignado para reportar averías."
            )
            return redirect("core:inicio")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["apartamentos"] = self.apartamentos
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["nav_activo"] = "averias"
        ctx["mis_averias"] = Averia.objects.filter(inquilino=self.request.user)[:5]
        return ctx

    def form_valid(self, form):
        averia = form.save(commit=False)
        averia.inquilino = self.request.user
        averia.save()
        # Fotos opcionales (comprimidas a <= 1 MB).
        for archivo in self.request.FILES.getlist("fotos"):
            FotoAveria.objects.create(averia=averia, imagen=comprimir_imagen(archivo))
        messages.success(self.request, "Avería reportada correctamente.")
        return redirect("averias:detalle", pk=averia.pk)


class MisAveriasView(InquilinoRequeridoMixin, ListView):
    """Listado de averías reportadas por el inquilino (RF-008)."""

    model = Averia
    template_name = "averias/mis_averias.html"
    context_object_name = "averias"
    paginate_by = settings.PAGINACION_POR_PAGINA

    def get_queryset(self):
        return Averia.objects.filter(inquilino=self.request.user).select_related("apartamento")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["nav_activo"] = "averias"
        return ctx


# --------------------------------------------------------------------------- #
# Detalle (inquilino dueño o administrador) y archivo de foto
# --------------------------------------------------------------------------- #
class AveriaDetailView(LoginRequiredMixin, DetailView):
    """Detalle de una avería con su línea de tiempo (inquilino o admin)."""

    model = Averia
    template_name = "averias/detalle.html"
    context_object_name = "averia"

    def get_object(self, queryset=None):
        averia = get_object_or_404(
            Averia.objects.select_related("apartamento", "inquilino").prefetch_related("fotos"),
            pk=self.kwargs["pk"],
        )
        if not (self.request.user.es_admin or averia.inquilino_id == self.request.user.id):
            raise PermissionDenied
        return averia

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["nav_activo"] = "averias"
        ctx["base_template"] = (
            "base_admin.html" if self.request.user.es_admin else "base_inquilino.html"
        )
        return ctx


class FotoAveriaArchivoView(LoginRequiredMixin, View):
    """Sirve la foto de una avería solo a su dueño o al admin (RNF-003)."""

    def get(self, request, pk):
        foto = get_object_or_404(FotoAveria.objects.select_related("averia"), pk=pk)
        if not (request.user.es_admin or foto.averia.inquilino_id == request.user.id):
            raise PermissionDenied
        try:
            archivo = foto.imagen.open("rb")
        except FileNotFoundError:
            raise Http404
        return FileResponse(archivo)


# --------------------------------------------------------------------------- #
# Administrador (RF-008, HU-07)
# --------------------------------------------------------------------------- #
class GestionAveriasView(AdminRequeridoMixin, ListView):
    """Listado de todas las averías con filtro por estado (HU-07)."""

    model = Averia
    template_name = "averias/gestion_lista.html"
    context_object_name = "averias"
    paginate_by = settings.PAGINACION_POR_PAGINA

    def get_queryset(self):
        qs = Averia.objects.select_related("apartamento", "inquilino")
        estado = self.request.GET.get("estado", "")
        if estado:
            qs = qs.filter(estado=estado)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["estado"] = self.request.GET.get("estado", "")
        ctx["estados"] = Averia.Estado.choices
        ctx["nav_activo"] = "averias"
        return ctx


class GestionAveriaDetailView(AdminRequeridoMixin, DetailView):
    """El admin ve y actualiza estado, gasto y notas de una avería (RF-008)."""

    model = Averia
    template_name = "averias/gestion_detalle.html"
    context_object_name = "averia"

    def get_queryset(self):
        return Averia.objects.select_related("apartamento", "inquilino").prefetch_related("fotos")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.setdefault("form", GestionAveriaForm(instance=self.object))
        ctx["nav_activo"] = "averias"
        return ctx

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        estado_anterior = self.object.estado
        form = GestionAveriaForm(request.POST, instance=self.object)
        if form.is_valid():
            averia = form.save(commit=False)
            averia.atendida_por = request.user
            if averia.estado == Averia.Estado.SOLUCIONADO and not averia.fecha_solucion:
                averia.fecha_solucion = timezone.localdate()
            averia.save()
            if averia.estado != estado_anterior:
                self._notificar_cambio(averia)
                messages.success(request, "Estado actualizado. Se notificó al inquilino.")
            else:
                messages.success(request, "Avería actualizada.")
            return redirect("averias:gestion_detalle", pk=averia.pk)
        return self.render_to_response(self.get_context_data(form=form))

    def _notificar_cambio(self, averia):
        inquilino = averia.inquilino
        if not inquilino.email:
            return
        cuerpo = (
            f"Hola {inquilino.get_full_name() or inquilino.username},\n\n"
            f"El estado de su avería reportada ({averia.get_area_display()} · "
            f"{averia.apartamento.codigo}) cambió a: {averia.get_estado_display()}.\n\n"
            f"Puede ver el detalle en la aplicación.\n\nVATISHE"
        )
        enviar_correo(
            tipo=RegistroCorreo.Tipo.AVERIA_ACTUALIZADA,
            destinatario=inquilino.email,
            asunto="VATISHE — Actualización de su avería",
            cuerpo=cuerpo,
            clave_unicidad=f"averia:{averia.pk}:estado:{averia.estado}",
        )
