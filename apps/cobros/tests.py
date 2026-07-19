"""Tests de la lógica de cobros y multas (RF-004/RF-007)."""

from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from apps.apartamentos.models import Apartamento
from apps.cobros.models import Cobro, Multa
from apps.cobros.services import aplicar_multas, generar_cobros
from apps.contratos.models import Contrato
from apps.core.models import ConfiguracionSistema
from apps.cuentas.models import Usuario


def crear_inquilino(username="inq"):
    return Usuario.objects.create_user(
        username=username, email=f"{username}@x.com", password="x", rol=Usuario.Rol.INQUILINO
    )


class GenerarCobrosTests(TestCase):
    def setUp(self):
        self.inq = crear_inquilino()
        self.apto = Apartamento.objects.create(codigo="A1", monto_mensual=Decimal("100000"), dia_vencimiento=1)
        hoy = timezone.localdate()
        Contrato.objects.create(
            apartamento=self.apto, inquilino=self.inq,
            fecha_inicio=hoy - timedelta(days=60), fecha_vencimiento=hoy + timedelta(days=300),
            monto=Decimal("100000"),
        )

    def test_genera_cobro_pendiente(self):
        hoy = timezone.localdate()
        res = generar_cobros(hoy.year, hoy.month)
        self.assertEqual(res["creados"], 1)
        cobro = Cobro.objects.get(apartamento=self.apto, anio=hoy.year, mes=hoy.month)
        self.assertEqual(cobro.estado, Cobro.Estado.PENDIENTE)
        self.assertEqual(cobro.monto, Decimal("100000"))

    def test_generacion_idempotente(self):
        hoy = timezone.localdate()
        generar_cobros(hoy.year, hoy.month)
        res = generar_cobros(hoy.year, hoy.month)
        self.assertEqual(res["creados"], 0)
        self.assertEqual(Cobro.objects.filter(apartamento=self.apto).count(), 1)


class SaldoEstadoTests(TestCase):
    def setUp(self):
        self.inq = crear_inquilino()
        self.apto = Apartamento.objects.create(codigo="A1", monto_mensual=Decimal("100000"), dia_vencimiento=1)
        self.cobro = Cobro.objects.create(
            apartamento=self.apto, inquilino=self.inq, anio=2026, mes=1,
            monto=Decimal("100000"), fecha_vencimiento=date(2026, 1, 1),
        )

    def test_saldo_inicial(self):
        self.assertEqual(self.cobro.saldo_pendiente, Decimal("100000"))
        self.assertEqual(self.cobro.calcular_estado(), Cobro.Estado.PENDIENTE)

    def test_saldo_por_cubrir_nunca_negativo(self):
        self.assertEqual(self.cobro.saldo_por_cubrir, Decimal("100000"))


class MultaTests(TestCase):
    def setUp(self):
        cfg = ConfiguracionSistema.cargar()
        cfg.porcentaje_multa = Decimal("10.00")
        cfg.monto_multa_fijo = Decimal("0")
        cfg.save()
        self.admin = Usuario.objects.create_superuser(username="adm", email="a@x.com", password="x")
        self.inq = crear_inquilino()
        self.apto = Apartamento.objects.create(codigo="A1", monto_mensual=Decimal("100000"), dia_vencimiento=1)
        hoy = timezone.localdate()
        self.cobro = Cobro.objects.create(
            apartamento=self.apto, inquilino=self.inq, anio=2025, mes=1,
            monto=Decimal("100000"), fecha_vencimiento=hoy - timedelta(days=5),
        )

    def test_aplica_multa_porcentaje(self):
        res = aplicar_multas()
        self.assertEqual(res["aplicadas"], 1)
        multa = Multa.objects.get(cobro=self.cobro)
        self.assertEqual(multa.monto, Decimal("10000"))
        self.cobro.refresh_from_db()
        self.assertEqual(self.cobro.estado, Cobro.Estado.CON_MULTA)
        self.assertEqual(self.cobro.saldo_pendiente, Decimal("110000"))

    def test_no_duplica_multa(self):
        aplicar_multas()
        aplicar_multas()
        self.assertEqual(Multa.objects.filter(cobro=self.cobro, exonerada=False).count(), 1)

    def test_exonerar_multa_restaura_saldo(self):
        aplicar_multas()
        multa = Multa.objects.get(cobro=self.cobro)
        multa.exonerar(self.admin, "Error del sistema")
        self.cobro.refresh_from_db()
        self.assertTrue(multa.exonerada)
        self.assertEqual(self.cobro.total_multas, Decimal("0"))
        self.assertEqual(self.cobro.saldo_pendiente, Decimal("100000"))
