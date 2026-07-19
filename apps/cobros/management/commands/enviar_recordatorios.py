"""Comando para enviar recordatorios de pago (RF-010). Ejecutable por cron."""

from datetime import datetime

from django.core.management.base import BaseCommand

from apps.cobros.services import enviar_recordatorios


class Command(BaseCommand):
    help = "Envía recordatorios de pago N días antes del vencimiento (RF-010)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--fecha", type=str, default=None,
            help="Fecha de referencia YYYY-MM-DD (por defecto, hoy).",
        )

    def handle(self, *args, **opciones):
        fecha = None
        if opciones["fecha"]:
            fecha = datetime.strptime(opciones["fecha"], "%Y-%m-%d").date()
        resultado = enviar_recordatorios(fecha)
        self.stdout.write(self.style.SUCCESS(
            f"[enviar_recordatorios] {resultado['enviados']} enviado(s), "
            f"{resultado['omitidos']} omitido(s). Vencimiento objetivo: {resultado['objetivo']}."
        ))
