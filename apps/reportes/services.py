"""Cálculo de los reportes de ganancias y morosidad (RF-011)."""

from decimal import Decimal

from django.utils import timezone

from apps.averias.models import Averia
from apps.cobros.models import MESES, Cobro


def _cero():
    return Decimal("0")


def reporte_ganancias(anio, mes=None, apartamento_id=None):
    """Consolida ingresos por apartamento y periodo (RF-011).

    Distingue lo cobrado (cargos + multas), lo efectivamente recibido (abonos
    aprobados), lo pendiente de verificación, el saldo y los gastos de
    reparación. La ganancia neta = recibido − gastos.
    """
    cobros = Cobro.objects.filter(anio=anio).select_related("apartamento", "inquilino")
    if mes:
        cobros = cobros.filter(mes=mes)
    if apartamento_id:
        cobros = cobros.filter(apartamento_id=apartamento_id)

    filas = {}
    for cobro in cobros:
        fila = filas.setdefault(
            cobro.apartamento_id,
            {
                "apartamento": cobro.apartamento,
                "cargos": _cero(),
                "multas": _cero(),
                "recibido": _cero(),
                "pendiente_verif": _cero(),
                "saldo": _cero(),
                "gastos": _cero(),
                "n_cobros": 0,
            },
        )
        fila["cargos"] += cobro.monto
        fila["multas"] += cobro.total_multas
        fila["recibido"] += cobro.total_abonado
        fila["pendiente_verif"] += cobro.total_pendiente_verificacion
        fila["saldo"] += cobro.saldo_pendiente
        fila["n_cobros"] += 1

    # Gastos de reparación del periodo (por fecha de reporte).
    gastos_qs = Averia.objects.filter(creado_en__year=anio)
    if mes:
        gastos_qs = gastos_qs.filter(creado_en__month=mes)
    if apartamento_id:
        gastos_qs = gastos_qs.filter(apartamento_id=apartamento_id)
    for averia in gastos_qs.select_related("apartamento"):
        if averia.apartamento_id in filas:
            filas[averia.apartamento_id]["gastos"] += averia.gasto
        elif averia.gasto:
            filas[averia.apartamento_id] = {
                "apartamento": averia.apartamento,
                "cargos": _cero(), "multas": _cero(), "recibido": _cero(),
                "pendiente_verif": _cero(), "saldo": _cero(),
                "gastos": averia.gasto, "n_cobros": 0,
            }

    filas_lista = sorted(filas.values(), key=lambda f: f["apartamento"].codigo)
    for f in filas_lista:
        esperado = f["cargos"] + f["multas"]
        if f["saldo"] <= 0 and f["n_cobros"]:
            f["estado"] = "PAGADO"
        elif f["recibido"] > 0:
            f["estado"] = "PARCIAL"
        else:
            f["estado"] = "PENDIENTE"
        f["esperado"] = esperado
        f["neto"] = f["recibido"] - f["gastos"]

    total_cargos = sum((f["cargos"] for f in filas_lista), _cero())
    total_multas = sum((f["multas"] for f in filas_lista), _cero())
    total_recibido = sum((f["recibido"] for f in filas_lista), _cero())
    total_pendiente_verif = sum((f["pendiente_verif"] for f in filas_lista), _cero())
    total_saldo = sum((f["saldo"] for f in filas_lista), _cero())
    total_gastos = sum((f["gastos"] for f in filas_lista), _cero())
    total_esperado = total_cargos + total_multas
    pct = int(total_recibido * 100 / total_esperado) if total_esperado else 0

    return {
        "anio": anio,
        "mes": mes,
        "mes_nombre": MESES.get(mes) if mes else "Todo el año",
        "apartamento_id": apartamento_id,
        "filas": filas_lista,
        "total_cargos": total_cargos,
        "total_multas": total_multas,
        "total_esperado": total_esperado,
        "total_recibido": total_recibido,
        "total_pendiente_verif": total_pendiente_verif,
        "total_saldo": total_saldo,
        "total_gastos": total_gastos,
        "ganancia_neta": total_recibido - total_gastos,
        "pct_recaudado": pct,
        # Anillo de progreso (circunferencia 2·π·70 ≈ 440).
        "anillo_total": 440,
        "anillo_offset": round(440 * (100 - pct) / 100, 1),
    }


def reporte_morosidad(anio=None, mes=None, apartamento_id=None, solo_vencidos=True):
    """Lista los cobros con saldo pendiente (morosidad), ordenados por saldo."""
    hoy = timezone.localdate()
    cobros = Cobro.objects.exclude(estado=Cobro.Estado.PAGADO).select_related(
        "apartamento", "inquilino"
    )
    if anio:
        cobros = cobros.filter(anio=anio)
    if mes:
        cobros = cobros.filter(mes=mes)
    if apartamento_id:
        cobros = cobros.filter(apartamento_id=apartamento_id)
    if solo_vencidos:
        cobros = cobros.filter(fecha_vencimiento__lt=hoy)

    filas = []
    total = _cero()
    for cobro in cobros:
        saldo = cobro.saldo_pendiente
        if saldo <= 0:
            continue
        filas.append(
            {
                "cobro": cobro,
                "saldo": saldo,
                "multas": cobro.total_multas,
                "dias_atraso": (hoy - cobro.fecha_vencimiento).days,
            }
        )
        total += saldo

    filas.sort(key=lambda f: f["saldo"], reverse=True)
    return {
        "anio": anio,
        "mes": mes,
        "mes_nombre": MESES.get(mes) if mes else "Todos",
        "filas": filas,
        "total_saldo": total,
        "n_morosos": len(filas),
    }
