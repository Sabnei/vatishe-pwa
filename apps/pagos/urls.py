"""URLs del módulo de pagos (inquilino y verificación del administrador)."""

from django.urls import path

from apps.pagos import views

app_name = "pagos"

urlpatterns = [
    # Inquilino
    path("mis-cobros/", views.MisCobrosView.as_view(), name="mis_cobros"),
    path("cobro/<int:cobro_pk>/abonar/", views.RegistrarAbonoView.as_view(), name="registrar_abono"),
    path("historial/", views.HistorialPagosView.as_view(), name="historial"),
    path("abono/<int:pk>/", views.AbonoDetailView.as_view(), name="detalle_abono"),
    path("abono/<int:pk>/comprobante/", views.ComprobanteArchivoView.as_view(), name="comprobante"),
    # Administrador
    path("verificar/", views.VerificarComprobantesListView.as_view(), name="verificar_lista"),
    path("verificar/<int:pk>/", views.VerificarComprobanteView.as_view(), name="verificar_detalle"),
]
