"""Context processors globales disponibles en todas las plantillas."""

from apps.core.models import ConfiguracionSistema


def configuracion_sistema(request):
    """Expone la configuración del sistema y el nombre de la empresa a las plantillas."""
    try:
        config = ConfiguracionSistema.cargar()
    except Exception:
        # Antes de aplicar migraciones la tabla puede no existir aún.
        config = None
    return {
        "config_sistema": config,
        "nombre_empresa": getattr(config, "nombre_empresa", "VATISHE"),
    }
