"""URLs del núcleo."""

from django.urls import path

from apps.core import views

app_name = "core"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("proximamente/", views.proximamente, name="proximamente"),
    path("offline/", views.offline, name="offline"),
    path("ping/", views.ping, name="ping"),
    path("sw.js", views.service_worker, name="service_worker"),
    path("cron/tareas-diarias/", views.cron_tareas_diarias, name="cron_tareas_diarias"),
]
