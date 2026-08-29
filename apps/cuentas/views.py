"""Vistas del módulo de seguridad y usuarios (Módulo 1)."""

from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView, View

from apps.core.mixins import AdminRequeridoMixin, InquilinoRequeridoMixin
from apps.cuentas.forms import (
    EditarAdminForm,
    EditarInquilinoForm,
    MiPerfilForm,
    NuevoAdminForm,
    NuevoInquilinoForm,
    PromoverAdminForm,
)
from apps.cuentas.models import PerfilInquilino, Usuario


def _admins_activos():
    """Administradores activos del sistema (para no quedarse sin ninguno)."""
    return Usuario.objects.filter(rol=Usuario.Rol.ADMIN, is_active=True)


def _es_ultimo_admin(usuario):
    """True si al desactivar o degradar a ``usuario`` no quedaria ningun admin activo."""
    if usuario.rol != Usuario.Rol.ADMIN or not usuario.is_active:
        return False
    return not _admins_activos().exclude(pk=usuario.pk).exists()


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
        ctx["total_admins"] = _admins_activos().count()
        ctx["nav_activo"] = "inquilinos"
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


class CambiarEstadoUsuarioView(AdminRequeridoMixin, View):
    """Activa o desactiva un usuario. Al desactivar se conservan sus datos (RF-002).

    Protege dos casos: un administrador no puede desactivarse a si mismo ni dejar
    al sistema sin ningun administrador activo.
    """

    def post(self, request, pk):
        usuario = get_object_or_404(Usuario, pk=pk)
        destino = request.POST.get("next")
        if usuario.is_active and usuario.pk == request.user.pk:
            messages.error(request, "No puede desactivar su propia cuenta.")
        elif _es_ultimo_admin(usuario):
            messages.error(
                request, "Debe existir al menos un administrador activo en el sistema."
            )
        else:
            usuario.is_active = not usuario.is_active
            usuario.save(update_fields=["is_active"])
            etiqueta = "Administrador" if usuario.es_admin else "Inquilino"
            estado = "activado" if usuario.is_active else "desactivado"
            messages.success(request, f"{etiqueta} {estado} correctamente.")
        if destino:
            return redirect(destino)
        if usuario.es_admin:
            return redirect("cuentas:editar_admin", pk=pk)
        return redirect("cuentas:perfil_inquilino_admin", pk=pk)


class GestionAdminsView(AdminRequeridoMixin, ListView):
    """Listado de administradores del sistema (RF-001)."""

    model = Usuario
    template_name = "cuentas/gestion_admins.html"
    context_object_name = "administradores"
    paginate_by = settings.PAGINACION_POR_PAGINA

    def get_queryset(self):
        qs = Usuario.objects.filter(rol=Usuario.Rol.ADMIN).order_by(
            "first_name", "last_name", "username"
        )
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
                | Q(username__icontains=q)
                | Q(email__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["nav_activo"] = "inquilinos"
        ctx["q"] = self.request.GET.get("q", "")
        ctx["total_activos"] = _admins_activos().count()
        ctx["form_promover"] = PromoverAdminForm()
        return ctx


class NuevoAdminView(AdminRequeridoMixin, CreateView):
    """Alta de un nuevo administrador desde la app (RF-001)."""

    model = Usuario
    form_class = NuevoAdminForm
    template_name = "cuentas/nuevo_admin.html"
    success_url = reverse_lazy("cuentas:gestion_admins")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["nav_activo"] = "inquilinos"
        return ctx

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        nombre = self.object.get_full_name() or self.object.username
        messages.success(self.request, f"Administrador «{nombre}» creado correctamente.")
        return respuesta


class EditarAdminView(AdminRequeridoMixin, UpdateView):
    """Edicion de un administrador (datos y acceso al admin de Django)."""

    model = Usuario
    form_class = EditarAdminForm
    template_name = "cuentas/editar_admin.html"
    context_object_name = "administrador"

    def get_queryset(self):
        return Usuario.objects.filter(rol=Usuario.Rol.ADMIN)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["nav_activo"] = "inquilinos"
        ctx["es_ultimo_admin"] = _es_ultimo_admin(self.object)
        return ctx

    def get_success_url(self):
        return reverse_lazy("cuentas:gestion_admins")

    def form_valid(self, form):
        messages.success(self.request, "Datos del administrador actualizados.")
        return super().form_valid(form)


class PromoverAdminView(AdminRequeridoMixin, View):
    """Convierte un inquilino existente en administrador (RF-001)."""

    def post(self, request):
        form = PromoverAdminForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Seleccione un inquilino valido.")
            return redirect("cuentas:gestion_admins")
        usuario = form.cleaned_data["usuario"]
        usuario.rol = Usuario.Rol.ADMIN
        usuario.save(update_fields=["rol"])
        nombre = usuario.get_full_name() or usuario.username
        messages.success(request, f"«{nombre}» ahora es administrador.")
        return redirect("cuentas:gestion_admins")


class DegradarAdminView(AdminRequeridoMixin, View):
    """Devuelve a un administrador el rol de inquilino (conserva su historial)."""

    def post(self, request, pk):
        usuario = get_object_or_404(Usuario, pk=pk, rol=Usuario.Rol.ADMIN)
        if usuario.pk == request.user.pk:
            messages.error(
                request, "No puede quitarse a si mismo el rol de administrador."
            )
            return redirect("cuentas:editar_admin", pk=pk)
        if _es_ultimo_admin(usuario):
            messages.error(
                request, "Debe existir al menos un administrador activo en el sistema."
            )
            return redirect("cuentas:editar_admin", pk=pk)
        usuario.rol = Usuario.Rol.INQUILINO
        usuario.is_staff = False
        usuario.is_superuser = False
        usuario.save(update_fields=["rol", "is_staff", "is_superuser"])
        PerfilInquilino.objects.get_or_create(usuario=usuario)
        nombre = usuario.get_full_name() or usuario.username
        messages.success(request, f"«{nombre}» paso a ser inquilino.")
        return redirect("cuentas:gestion_admins")


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
