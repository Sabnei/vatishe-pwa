"""URLs del módulo de apartamentos."""

from django.urls import path

from apps.apartamentos import views

app_name = "apartamentos"

urlpatterns = [
    path("", views.ApartamentoListView.as_view(), name="lista"),
    path("nuevo/", views.ApartamentoCreateView.as_view(), name="nuevo"),
    path("<int:pk>/", views.ApartamentoDetailView.as_view(), name="detalle"),
    path("<int:pk>/editar/", views.ApartamentoUpdateView.as_view(), name="editar"),
    path("<int:pk>/estado/", views.CambiarEstadoApartamentoView.as_view(), name="cambiar_estado"),
]
