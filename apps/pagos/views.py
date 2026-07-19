"""Vistas del módulo de pagos: abonos y verificación de comprobantes."""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import CreateView, DetailView, ListView, View

from apps.cobros.models import Cobro
from apps.core.imagenes import comprimir_imagen
from apps.core.mixins import AdminRequeridoMixin, InquilinoRequeridoMixin
from apps.core.models import RegistroCorreo
from apps.core.notificaciones import enviar_correo
from apps.pagos.forms import AbonoForm, RechazoComprobanteForm
from apps.pagos.models import Abono


# --------------------------------------------------------------------------- #
# Inquilino
# --------------------------------------------------------------------------- #
class MisCobrosView(InquilinoRequeridoMixin, ListView):
    """Cobros del inquilino con su saldo, punto de entrada para abonar (RF-009)."""

    model = Cobro
    template_name = "pagos/mis_cobros.html"
    context_object_name = "cobros"
    paginate_by = settings.PAGINACION_POR_PAGINA

    def get_queryset(self):
        return (
            Cobro.objects.filter(inquilino=self.request.user)
            .select_related("apartamento")
            .order_by("-anio", "-mes")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["nav_activo"] = "abonos"
        return ctx


class RegistrarAbonoView(InquilinoRequeridoMixin, CreateView):
    """El inquilino registra un abono y sube el comprobante (RF-005, HU-01)."""

    model = Abono
    form_class = AbonoForm
    template_name = "pagos/registrar_abono.html"

    def dispatch(self, request, *args, **kwargs):
        # El cobro debe pertenecer al inquilino autenticado.
        self.cobro = get_object_or_404(
            Cobro.objects.select_related("apartamento"),
            pk=kwargs["cobro_pk"],
            inquilino=request.user,
        )
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        # Si ya no queda saldo por cubrir, no tiene sentido registrar otro abono.
        if self.cobro.saldo_por_cubrir <= 0:
            messages.info(
                request,
                "Este cobro ya está cubierto o tiene abonos pendientes de verificación.",
            )
            return redirect("pagos:mis_cobros")
        return super().get(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["cobro"] = self.cobro
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["cobro"] = self.cobro
        ctx["nav_activo"] = "abonos"
        return ctx

    def form_valid(self, form):
        abono = form.save(commit=False)
        abono.cobro = self.cobro
        abono.registrado_por = self.request.user
        # Comprime la imagen del comprobante a <= 1 MB (RNF-002).
        archivo = form.cleaned_data.get("comprobante")
        if archivo:
            abono.comprobante = comprimir_imagen(archivo)
        abono.save()
        messages.success(
            self.request,
            "Abono registrado. Queda pendiente de verificación por el administrador.",
        )
        return redirect("pagos:detalle_abono", pk=abono.pk)


class HistorialPagosView(InquilinoRequeridoMixin, ListView):
    """Historial de abonos del inquilino con su estado (RF-009, HU-02)."""

    model = Abono
    template_name = "pagos/historial.html"
    context_object_name = "abonos"
    paginate_by = settings.PAGINACION_POR_PAGINA

    def get_queryset(self):
        return (
            Abono.objects.filter(cobro__inquilino=self.request.user)
            .select_related("cobro", "cobro__apartamento")
            .order_by("-fecha", "-creado_en")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["nav_activo"] = "historial"
        return ctx


# --------------------------------------------------------------------------- #
# Detalle y archivo (inquilino dueño o administrador)
# --------------------------------------------------------------------------- #
class AbonoDetailView(LoginRequiredMixin, DetailView):
    """Detalle de un abono. Accesible por su inquilino o por el administrador."""

    model = Abono
    template_name = "pagos/detalle_abono.html"
    context_object_name = "abono"

    def get_object(self, queryset=None):
        abono = get_object_or_404(
            Abono.objects.select_related("cobro", "cobro__apartamento", "verificado_por"),
            pk=self.kwargs["pk"],
        )
        if not (self.request.user.es_admin or abono.cobro.inquilino_id == self.request.user.id):
            raise PermissionDenied
        return abono

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["nav_activo"] = "historial"
        ctx["base_template"] = (
            "base_admin.html" if self.request.user.es_admin else "base_inquilino.html"
        )
        return ctx


class ComprobanteArchivoView(LoginRequiredMixin, View):
    """Sirve el archivo del comprobante solo a su dueño o al admin (RNF-003)."""

    def get(self, request, pk):
        abono = get_object_or_404(Abono, pk=pk)
        if not (request.user.es_admin or abono.cobro.inquilino_id == request.user.id):
            raise PermissionDenied
        if not abono.comprobante:
            raise Http404
        try:
            archivo = abono.comprobante.open("rb")
        except FileNotFoundError:
            raise Http404
        return FileResponse(archivo, filename=abono.nombre_archivo)


# --------------------------------------------------------------------------- #
# Administrador — verificación de comprobantes (RF-006)
# --------------------------------------------------------------------------- #
class VerificarComprobantesListView(AdminRequeridoMixin, ListView):
    """Lista de abonos pendientes de verificación (RF-006, HU-03)."""

    model = Abono
    template_name = "pagos/verificar_lista.html"
    context_object_name = "abonos"
    paginate_by = settings.PAGINACION_POR_PAGINA

    def get_queryset(self):
        return (
            Abono.objects.filter(estado_verificacion=Abono.Verificacion.PENDIENTE)
            .select_related("cobro", "cobro__apartamento", "cobro__inquilino")
            .order_by("creado_en")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["nav_activo"] = "verificar"
        return ctx


class VerificarComprobanteView(AdminRequeridoMixin, DetailView):
    """Visualiza un comprobante y permite aprobarlo o rechazarlo (RF-006)."""

    model = Abono
    template_name = "pagos/verificar_detalle.html"
    context_object_name = "abono"

    def get_queryset(self):
        return Abono.objects.select_related("cobro", "cobro__apartamento", "cobro__inquilino")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.setdefault("form_rechazo", RechazoComprobanteForm())
        ctx["nav_activo"] = "verificar"
        return ctx

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        abono = self.object
        accion = request.POST.get("accion")

        if not abono.pendiente:
            messages.info(request, "Este comprobante ya fue verificado.")
            return redirect("pagos:verificar_detalle", pk=abono.pk)

        if accion == "aprobar":
            abono.aprobar(request.user)
            messages.success(request, "Comprobante aprobado. El saldo se actualizó.")
            return redirect("pagos:verificar_lista")

        if accion == "rechazar":
            form = RechazoComprobanteForm(request.POST)
            if form.is_valid():
                abono.rechazar(request.user, form.cleaned_data["motivo"])
                self._notificar_rechazo(abono)
                messages.success(request, "Comprobante rechazado. Se notificó al inquilino.")
                return redirect("pagos:verificar_lista")
            context = self.get_context_data(object=abono, form_rechazo=form)
            return self.render_to_response(context)

        messages.error(request, "Acción no válida.")
        return redirect("pagos:verificar_detalle", pk=abono.pk)

    def _notificar_rechazo(self, abono):
        inquilino = abono.cobro.inquilino
        if not inquilino.email:
            return
        cuerpo = (
            f"Hola {inquilino.get_full_name() or inquilino.username},\n\n"
            f"Su comprobante de abono por ₡{abono.monto:,.0f} del cobro "
            f"{abono.cobro.periodo_display} ({abono.cobro.apartamento.codigo}) fue "
            f"RECHAZADO.\n\nMotivo: {abono.motivo_rechazo}\n\n"
            f"Puede registrar un nuevo abono desde la aplicación.\n\nVATISHE"
        )
        enviar_correo(
            tipo=RegistroCorreo.Tipo.COMPROBANTE_RECHAZADO,
            destinatario=inquilino.email,
            asunto="VATISHE — Comprobante rechazado",
            cuerpo=cuerpo,
            clave_unicidad=f"rechazo:abono:{abono.pk}",
        )
