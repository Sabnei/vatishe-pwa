"""Orquestación de las tareas diarias (reutilizable por el command y por HTTP)."""

from datetime import date

from apps.cobros.services import aplicar_multas, enviar_recordatorios, generar_cobros


def ejecutar_tareas_diarias(hoy=None):
    """Genera cobros del mes, aplica multas y envía recordatorios.

    Todas las tareas son idempotentes, así que es seguro ejecutarla a diario.
    Devuelve un resumen serializable.
    """
    hoy = hoy or date.today()
    generacion = generar_cobros(hoy.year, hoy.month)
    multas = aplicar_multas(hoy)
    recordatorios = enviar_recordatorios(hoy)
    return {
        "fecha": hoy.isoformat(),
        "generacion": {"creados": generacion["creados"], "omitidos": generacion["omitidos"]},
        "multas": {"aplicadas": multas["aplicadas"], "total": str(multas["total"])},
        "recordatorios": {
            "enviados": recordatorios["enviados"],
            "omitidos": recordatorios["omitidos"],
        },
    }
