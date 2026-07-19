"""Comando para generar los cobros mensuales (RF-004). Ejecutable por cron."""

from datetime import date

from django.core.management.base import BaseCommand

from apps.cobros.services import generar_cobros


class Command(BaseCommand):
    help = "Genera los cobros mensuales de los contratos vigentes (RF-004)."

    def add_arguments(self, parser):
        hoy = date.today()
        parser.add_argument("--anio", type=int, default=hoy.year, help="Año del periodo.")
        parser.add_argument("--mes", type=int, default=hoy.month, help="Mes del periodo (1-12).")

    def handle(self, *args, **opciones):
        resultado = generar_cobros(opciones["anio"], opciones["mes"])
        self.stdout.write(self.style.SUCCESS(
            f"[generar_cobros] {resultado['anio']}-{resultado['mes']:02d}: "
            f"{resultado['creados']} creados, {resultado['omitidos']} ya existían."
        ))
