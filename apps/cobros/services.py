"""Lógica de negocio de cobros: generación mensual automática (RF-004)."""

import calendar
from datetime import date

from apps.cobros.models import Cobro
from apps.contratos.models import Contrato


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
