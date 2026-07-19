"""URLs del módulo de cobros (lado administrador)."""

from django.urls import path

from apps.cobros import views

app_name = "cobros"

urlpatterns = [
    path("", views.CobroListView.as_view(), name="lista"),
    path("generar/", views.GenerarCobrosView.as_view(), name="generar"),
    # Multas (RF-007)
    path("multas/", views.MultaListView.as_view(), name="multas_lista"),
    path("multas/aplicar/", views.AplicarMultasView.as_view(), name="aplicar_multas"),
    path("multas/<int:pk>/", views.MultaDetailView.as_view(), name="multa_detalle"),
    path("multas/<int:pk>/exonerar/", views.ExonerarMultaView.as_view(), name="exonerar_multa"),
    # Cobros
    path("<int:pk>/", views.CobroDetailView.as_view(), name="detalle"),
    path("<int:pk>/ajustar/", views.CobroAjusteView.as_view(), name="ajustar"),
]
