"""URLs del módulo de averías."""

from django.urls import path

from apps.averias import views

app_name = "averias"

urlpatterns = [
    # Inquilino
    path("reportar/", views.ReportarAveriaView.as_view(), name="reportar"),
    path("mis-averias/", views.MisAveriasView.as_view(), name="mis_averias"),
    path("<int:pk>/", views.AveriaDetailView.as_view(), name="detalle"),
    path("foto/<int:pk>/", views.FotoAveriaArchivoView.as_view(), name="foto"),
    # Administrador
    path("gestion/", views.GestionAveriasView.as_view(), name="gestion_lista"),
    path("gestion/<int:pk>/", views.GestionAveriaDetailView.as_view(), name="gestion_detalle"),
]
