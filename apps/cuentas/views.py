"""Vistas del módulo de seguridad y usuarios (Módulo 1)."""

from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView, View

from apps.core.mixins import AdminRequeridoMixin, InquilinoRequeridoMixin
from apps.cuentas.forms import EditarInquilinoForm, MiPerfilForm, NuevoInquilinoForm
from apps.cuentas.models import Usuario


class GestionUsuariosView(AdminRequeridoMixin, ListView):
    """Listado paginado de inquilinos con búsqueda (RF-001)."""

    model = Usuario
    template_name = "cuentas/gestion_usuarios.html"
    context_object_name = "inquilinos"
    paginate_by = settings.PAGINACION_POR_PAGINA

    def get_queryset(self):
        qs = (
            Usuario.objects.filter(rol=Usuario.Rol.INQUILINO)
            .select_related("perfil_inquilino")
            .order_by("first_name", "last_name", "username")
        )
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
                | Q(username__icontains=q)
                | Q(email__icontains=q)
            )
        estado = self.request.GET.get("estado", "")
        if estado == "activos":
            qs = qs.filter(is_active=True)
        elif estado == "inactivos":
            qs = qs.filter(is_active=False)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["estado"] = self.request.GET.get("estado", "")
        ctx["total_activos"] = Usuario.objects.filter(
            rol=Usuario.Rol.INQUILINO, is_active=True
        ).count()
        return ctx


class NuevoInquilinoView(AdminRequeridoMixin, CreateView):
    """Alta de un inquilino por el Administrador (RF-001/RF-002)."""

    model = Usuario
    form_class = NuevoInquilinoForm
    template_name = "cuentas/nuevo_inquilino.html"
    success_url = reverse_lazy("cuentas:gestion_usuarios")

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        messages.success(
            self.request,
            f"Inquilino «{self.object.get_full_name()}» creado correctamente.",
        )
        return respuesta


class PerfilInquilinoAdminView(AdminRequeridoMixin, DetailView):
    """Ficha de un inquilino vista por el Administrador."""

    model = Usuario
    template_name = "cuentas/perfil_inquilino_admin.html"
    context_object_name = "inquilino"

    def get_queryset(self):
        return Usuario.objects.filter(rol=Usuario.Rol.INQUILINO).select_related(
            "perfil_inquilino"
        )


class EditarInquilinoView(AdminRequeridoMixin, UpdateView):
    """Edición de datos de un inquilino por el Administrador."""

    model = Usuario
    form_class = EditarInquilinoForm
    template_name = "cuentas/editar_inquilino.html"
    context_object_name = "inquilino"

    def get_queryset(self):
        return Usuario.objects.filter(rol=Usuario.Rol.INQUILINO)

    def get_success_url(self):
        return reverse_lazy("cuentas:perfil_inquilino_admin", args=[self.object.pk])

    def form_valid(self, form):
        messages.success(self.request, "Datos del inquilino actualizados.")
        return super().form_valid(form)


class CambiarEstadoInquilinoView(AdminRequeridoMixin, View):
    """Activa o desactiva un inquilino. Al desactivar se conservan sus datos (RF-002)."""

    def post(self, request, pk):
        inquilino = get_object_or_404(Usuario, pk=pk, rol=Usuario.Rol.INQUILINO)
        inquilino.is_active = not inquilino.is_active
        inquilino.save(update_fields=["is_active"])
        estado = "activado" if inquilino.is_active else "desactivado"
        messages.success(request, f"Inquilino {estado} correctamente.")
        destino = request.POST.get("next")
        if destino:
            return redirect(destino)
        return redirect("cuentas:perfil_inquilino_admin", pk=pk)


class MiPerfilView(InquilinoRequeridoMixin, UpdateView):
    """El Inquilino consulta y edita sus propios datos de contacto (RF-009)."""

    model = Usuario
    form_class = MiPerfilForm
    template_name = "cuentas/mi_perfil.html"
    success_url = reverse_lazy("cuentas:mi_perfil")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Perfil actualizado correctamente.")
        return super().form_valid(form)
