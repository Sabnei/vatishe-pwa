"""Comando para aplicar multas por morosidad (RF-007). Ejecutable por cron."""

from datetime import datetime

from django.core.management.base import BaseCommand

from apps.cobros.services import aplicar_multas


class Command(BaseCommand):
    help = "Aplica las multas por morosidad a los cobros vencidos con saldo (RF-007)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--fecha", type=str, default=None,
            help="Fecha de referencia YYYY-MM-DD (por defecto, hoy).",
        )

    def handle(self, *args, **opciones):
        fecha = None
        if opciones["fecha"]:
            fecha = datetime.strptime(opciones["fecha"], "%Y-%m-%d").date()
        resultado = aplicar_multas(fecha)
        self.stdout.write(self.style.SUCCESS(
            f"[aplicar_multas] {resultado['aplicadas']} multa(s) aplicada(s) "
            f"por un total de ₡{resultado['total']:,.0f}."
        ))
