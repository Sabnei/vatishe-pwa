"""URLs del módulo de contratos."""

from django.urls import path

from apps.contratos import views

app_name = "contratos"

urlpatterns = [
    path("", views.ContratoListView.as_view(), name="lista"),
    path("nuevo/", views.ContratoCreateView.as_view(), name="nuevo"),
    path("mi-contrato/", views.MiContratoView.as_view(), name="mi_contrato"),
    path("<int:pk>/", views.ContratoDetailView.as_view(), name="detalle"),
    path("<int:pk>/finalizar/", views.FinalizarContratoView.as_view(), name="finalizar"),
    path("<int:pk>/renovar/", views.RenovarContratoView.as_view(), name="renovar"),
]
