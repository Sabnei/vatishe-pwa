"""URLs del módulo de reportes."""

from django.urls import path

from apps.reportes import views

app_name = "reportes"

urlpatterns = [
    path("ganancias/", views.ReporteGananciasView.as_view(), name="ganancias"),
    path("morosidad/", views.ReporteMorosidadView.as_view(), name="morosidad"),
    path("comprobante/<int:pk>/", views.ComprobanteImprimibleView.as_view(), name="comprobante"),
]
