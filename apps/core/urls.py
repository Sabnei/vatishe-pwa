"""URLs del núcleo."""

from django.urls import path

from apps.core import views

app_name = "core"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("proximamente/", views.proximamente, name="proximamente"),
]
