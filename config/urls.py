"""Ruteo raíz del proyecto VATISHE.

Cada módulo expone sus URLs bajo un namespace propio. Las apps que aún no
tienen vistas se irán incorporando por fase.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("cuentas/", include("apps.cuentas.urls")),
    path("apartamentos/", include("apps.apartamentos.urls")),
    path("contratos/", include("apps.contratos.urls")),
    path("cobros/", include("apps.cobros.urls")),
    path("pagos/", include("apps.pagos.urls")),
    path("averias/", include("apps.averias.urls")),
    path("reportes/", include("apps.reportes.urls")),
    path("", include("apps.core.urls")),
]

# En desarrollo se sirven los archivos multimedia desde disco.
if settings.DEBUG and not settings.USE_SUPABASE_STORAGE:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
