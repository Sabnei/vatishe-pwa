"""Lógica de negocio de cobros: generación mensual y multas (RF-004/RF-007)."""

import calendar
from datetime import date
from decimal import Decimal

from django.utils import timezone

from apps.cobros.models import Cobro, Multa
from apps.contratos.models import Contrato
from apps.core.models import ConfiguracionSistema


def calcular_fecha_vencimiento(anio, mes, dia):
    """Fecha de vencimiento del periodo, ajustando el día si el mes es más corto."""
    ultimo_dia = calendar.monthrange(anio, mes)[1]
    return date(anio, mes, min(dia, ultimo_dia))


def generar_cobros(anio, mes):
    """Genera el cobro mensual pendiente de cada contrato vigente.

    Idempotente: no duplica cobros ya existentes para el mismo apartamento y
    periodo (gracias a la restricción de unicidad). Devuelve un resumen con la
    cantidad de cobros creados y omitidos.

    Se considera "vigente" el contrato activo cuyo periodo cubre el mes indicado
    (inicio en o antes del fin de mes, y vencimiento en o después del inicio).
    """
    primer_dia = date(anio, mes, 1)
    ultimo_dia = date(anio, mes, calendar.monthrange(anio, mes)[1])

    contratos = (
        Contrato.objects.filter(
            activo=True,
            fecha_inicio__lte=ultimo_dia,
            fecha_vencimiento__gte=primer_dia,
        )
        .select_related("apartamento", "inquilino")
    )

    creados = 0
    omitidos = 0
    for contrato in contratos:
        apto = contrato.apartamento
        vencimiento = calcular_fecha_vencimiento(anio, mes, apto.dia_vencimiento)
        _, creado = Cobro.objects.get_or_create(
            apartamento=apto,
            anio=anio,
            mes=mes,
            defaults={
                "inquilino": contrato.inquilino,
                "contrato": contrato,
                "monto": contrato.monto,
                "fecha_vencimiento": vencimiento,
                "estado": Cobro.Estado.PENDIENTE,
            },
        )
        if creado:
            creados += 1
        else:
            omitidos += 1

    return {"creados": creados, "omitidos": omitidos, "anio": anio, "mes": mes}


def aplicar_multas(fecha=None):
    """Aplica el recargo por morosidad a los cobros vencidos con saldo (RF-007).

    Se ejecuta idealmente el día siguiente al vencimiento (por cron, Fase 8).
    Idempotente: no aplica una segunda multa de morosidad a un cobro que ya
    tiene una multa activa (no exonerada). El monto es fijo o un porcentaje del
    saldo pendiente, según la configuración del sistema.

    Devuelve un resumen con la cantidad de multas aplicadas y el total.
    """
    hoy = fecha or timezone.localdate()
    config = ConfiguracionSistema.cargar()

    # Cobros vencidos y no pagados.
    candidatos = (
        Cobro.objects.filter(fecha_vencimiento__lt=hoy)
        .exclude(estado=Cobro.Estado.PAGADO)
        .select_related("apartamento")
    )

    aplicadas = 0
    total = Decimal("0")
    for cobro in candidatos:
        if cobro.saldo_pendiente <= 0:
            continue
        # Evita duplicar la multa de morosidad si ya existe una activa.
        if cobro.multas.filter(exonerada=False, motivo="Morosidad").exists():
            continue

        if config.usa_monto_fijo:
            monto = config.monto_multa_fijo
            porcentaje = None
        else:
            porcentaje = config.porcentaje_multa
            monto = (cobro.saldo_pendiente * porcentaje / Decimal("100")).quantize(
                Decimal("1")
            )
        if monto <= 0:
            continue

        Multa.objects.create(
            cobro=cobro,
            monto=monto,
            porcentaje=porcentaje,
            motivo="Morosidad",
            fecha_aplicacion=hoy,
        )
        cobro.actualizar_estado()
        aplicadas += 1
        total += monto

    return {"aplicadas": aplicadas, "total": total, "fecha": hoy}
