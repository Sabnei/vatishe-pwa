"""URLs del módulo de cobros (lado administrador)."""

from django.urls import path

from apps.cobros import views

app_name = "cobros"

urlpatterns = [
    path("", views.CobroListView.as_view(), name="lista"),
    path("generar/", views.GenerarCobrosView.as_view(), name="generar"),
    path("<int:pk>/", views.CobroDetailView.as_view(), name="detalle"),
    path("<int:pk>/ajustar/", views.CobroAjusteView.as_view(), name="ajustar"),
]
