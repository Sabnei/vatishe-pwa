"""Vistas del módulo de reportes (RF-011): ganancias y morosidad, PDF/CSV."""

import csv
from datetime import date

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone
from django.views import View

from apps.apartamentos.models import Apartamento
from apps.cobros.models import MESES
from apps.core.mixins import AdminRequeridoMixin
from apps.pagos.models import Abono
from apps.reportes.forms import FiltroGananciasForm
from apps.reportes.services import reporte_ganancias, reporte_morosidad


def _colones(valor):
    """Formatea un Decimal como colones para CSV/PDF."""
    try:
        return f"₡ {int(valor):,}".replace(",", " ")
    except (TypeError, ValueError):
        return "₡ 0"


def _pdf_response(template, contexto, nombre):
    """Genera un PDF con WeasyPrint a partir de una plantilla."""
    from weasyprint import HTML

    html = render_to_string(template, contexto)
    pdf = HTML(string=html).write_pdf()
    resp = HttpResponse(pdf, content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="{nombre}.pdf"'
    return resp


class ReporteGananciasView(AdminRequeridoMixin, View):
    """Reporte de ganancias con filtros y export a PDF/CSV (RF-011, HU-05)."""

    def get(self, request):
        form = FiltroGananciasForm(request.GET or None)
        anio = mes = apartamento = None
        datos = None
        if request.GET and form.is_valid():
            anio = form.cleaned_data["anio"]
            mes = form.cleaned_data.get("mes") or None
            apartamento = form.cleaned_data.get("apartamento")
        else:
            anio = date.today().year
            mes = date.today().month
        datos = reporte_ganancias(anio, mes, apartamento.id if apartamento else None)

        formato = request.GET.get("formato")
        if formato == "csv":
            return self._csv(datos)
        if formato == "pdf":
            return _pdf_response(
                "reportes/ganancias_pdf.html",
                {"datos": datos, "generado": timezone.localtime()},
                f"ganancias_{anio}_{mes or 'anual'}",
            )

        return HttpResponse(
            render_to_string(
                "reportes/ganancias.html",
                {"form": form, "datos": datos, "nav_activo": "reportes", "querystring": request.GET.urlencode()},
                request=request,
            )
        )

    def _csv(self, datos):
        resp = HttpResponse(content_type="text/csv; charset=utf-8")
        nombre = f"ganancias_{datos['anio']}_{datos['mes'] or 'anual'}"
        resp["Content-Disposition"] = f'attachment; filename="{nombre}.csv"'
        resp.write("﻿")  # BOM para que Excel respete los acentos
        w = csv.writer(resp)
        w.writerow(["Reporte de ganancias", f"{datos['mes_nombre']} {datos['anio']}"])
        w.writerow([])
        w.writerow(["Apartamento", "Cargos", "Multas", "Recibido", "Pend. verificación", "Saldo", "Gastos", "Neto", "Estado"])
        for f in datos["filas"]:
            w.writerow([
                f["apartamento"].codigo, f["cargos"], f["multas"], f["recibido"],
                f["pendiente_verif"], f["saldo"], f["gastos"], f["neto"], f["estado"],
            ])
        w.writerow([])
        w.writerow(["TOTALES", datos["total_cargos"], datos["total_multas"],
                    datos["total_recibido"], datos["total_pendiente_verif"],
                    datos["total_saldo"], datos["total_gastos"], datos["ganancia_neta"], ""])
        return resp


class ReporteMorosidadView(AdminRequeridoMixin, View):
    """Reporte de morosidad con export a PDF/CSV (RF-011)."""

    def get(self, request):
        anio = request.GET.get("anio")
        mes = request.GET.get("mes")
        apartamento_id = request.GET.get("apartamento")
        datos = reporte_morosidad(
            anio=int(anio) if anio and anio.isdigit() else None,
            mes=int(mes) if mes and mes.isdigit() else None,
            apartamento_id=int(apartamento_id) if apartamento_id and apartamento_id.isdigit() else None,
        )

        formato = request.GET.get("formato")
        if formato == "csv":
            return self._csv(datos)
        if formato == "pdf":
            return _pdf_response(
                "reportes/morosidad_pdf.html",
                {"datos": datos, "generado": timezone.localtime()},
                "morosidad",
            )
        return HttpResponse(
            render_to_string(
                "reportes/morosidad.html",
                {
                    "datos": datos,
                    "apartamentos": Apartamento.objects.order_by("codigo"),
                    "meses": MESES.items(),
                    "filtro": {"anio": anio or "", "mes": mes or "", "apartamento": apartamento_id or ""},
                    "nav_activo": "reportes",
                    "querystring": request.GET.urlencode(),
                },
                request=request,
            )
        )

    def _csv(self, datos):
        resp = HttpResponse(content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = 'attachment; filename="morosidad.csv"'
        resp.write("﻿")
        w = csv.writer(resp)
        w.writerow(["Reporte de morosidad"])
        w.writerow([])
        w.writerow(["Apartamento", "Inquilino", "Periodo", "Vencimiento", "Días de atraso", "Multas", "Saldo"])
        for f in datos["filas"]:
            c = f["cobro"]
            w.writerow([
                c.apartamento.codigo,
                c.inquilino.get_full_name() or c.inquilino.username,
                c.periodo_display, c.fecha_vencimiento, f["dias_atraso"], f["multas"], f["saldo"],
            ])
        w.writerow([])
        w.writerow(["TOTAL", "", "", "", "", "", datos["total_saldo"]])
        return resp


class ComprobanteImprimibleView(AdminRequeridoMixin, View):
    """Comprobante de abono imprimible en PDF (para el administrador)."""

    def get(self, request, pk):
        abono = get_object_or_404(
            Abono.objects.select_related("cobro", "cobro__apartamento", "cobro__inquilino"),
            pk=pk,
        )
        return _pdf_response(
            "reportes/comprobante_pdf.html",
            {"abono": abono, "generado": timezone.localtime()},
            f"comprobante_{abono.pk}",
        )
