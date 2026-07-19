"""Tests del reporte de ganancias (RF-011)."""

from datetime import date
from decimal import Decimal

from django.test import TestCase

from apps.apartamentos.models import Apartamento
from apps.cobros.models import Cobro
from apps.cuentas.models import Usuario
from apps.pagos.models import Abono
from apps.reportes.services import reporte_ganancias


class ReporteGananciasTests(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_superuser(username="adm", email="a@x.com", password="x")
        self.i1 = Usuario.objects.create_user(username="i1", email="i1@x.com", password="x", rol=Usuario.Rol.INQUILINO)
        self.i2 = Usuario.objects.create_user(username="i2", email="i2@x.com", password="x", rol=Usuario.Rol.INQUILINO)
        self.a1 = Apartamento.objects.create(codigo="A1", monto_mensual=Decimal("250000"))
        self.a2 = Apartamento.objects.create(codigo="A2", monto_mensual=Decimal("250000"))
        self.c1 = Cobro.objects.create(apartamento=self.a1, inquilino=self.i1, anio=2026, mes=3,
                                       monto=Decimal("250000"), fecha_vencimiento=date(2026, 3, 1))
        self.c2 = Cobro.objects.create(apartamento=self.a2, inquilino=self.i2, anio=2026, mes=3,
                                       monto=Decimal("250000"), fecha_vencimiento=date(2026, 3, 1))
        ab = Abono.objects.create(cobro=self.c1, monto=Decimal("250000"), fecha=date(2026, 3, 2),
                                  metodo=Abono.Metodo.SINPE, registrado_por=self.i1, comprobante="x.jpg")
        ab.aprobar(self.admin)

    def test_totales(self):
        d = reporte_ganancias(2026, 3)
        self.assertEqual(d["total_esperado"], Decimal("500000"))
        self.assertEqual(d["total_recibido"], Decimal("250000"))
        self.assertEqual(d["total_saldo"], Decimal("250000"))
        self.assertEqual(d["pct_recaudado"], 50)
        self.assertEqual(len(d["filas"]), 2)

    def test_filtro_por_apartamento(self):
        d = reporte_ganancias(2026, 3, self.a1.id)
        self.assertEqual(len(d["filas"]), 1)
        self.assertEqual(d["total_recibido"], Decimal("250000"))

    def test_pdf_admin(self):
        self.client.force_login(self.admin)
        r = self.client.get("/reportes/ganancias/?anio=2026&mes=3&formato=pdf")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Content-Type"], "application/pdf")
        self.assertEqual(r.content[:4], b"%PDF")
