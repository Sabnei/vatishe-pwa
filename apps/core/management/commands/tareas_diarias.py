"""Comando combinado de tareas diarias (cron): genera cobros, aplica multas y
envía recordatorios. Diseñado para ejecutarse una vez al día por cron.

    python manage.py tareas_diarias

No depende de Celery; el camino por cron funciona por sí solo.
"""

from django.core.management.base import BaseCommand

from apps.core.tareas import ejecutar_tareas_diarias


class Command(BaseCommand):
    help = "Ejecuta las tareas diarias: generar cobros, aplicar multas y enviar recordatorios."

    def handle(self, *args, **opciones):
        resumen = ejecutar_tareas_diarias()
        g, m, r = resumen["generacion"], resumen["multas"], resumen["recordatorios"]
        self.stdout.write(self.style.SUCCESS(
            f"[tareas_diarias {resumen['fecha']}] "
            f"cobros: {g['creados']} creados/{g['omitidos']} existentes · "
            f"multas: {m['aplicadas']} (₡{m['total']}) · "
            f"recordatorios: {r['enviados']} enviados/{r['omitidos']} omitidos."
        ))
