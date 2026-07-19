"""Tests de contratos: restricción de un contrato activo por apartamento (RF-003)."""

from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.apartamentos.models import Apartamento
from apps.contratos.models import Contrato
from apps.cuentas.models import Usuario


class ContratoConstraintTests(TestCase):
    def setUp(self):
        self.apto = Apartamento.objects.create(codigo="A1", monto_mensual=Decimal("100000"))
        self.hoy = timezone.localdate()
        self.i1 = Usuario.objects.create_user(username="i1", email="i1@x.com", password="x", rol=Usuario.Rol.INQUILINO)
        self.i2 = Usuario.objects.create_user(username="i2", email="i2@x.com", password="x", rol=Usuario.Rol.INQUILINO)
        self.c1 = Contrato.objects.create(
            apartamento=self.apto, inquilino=self.i1, fecha_inicio=self.hoy,
            fecha_vencimiento=self.hoy + timedelta(days=365), monto=Decimal("100000"),
        )

    def test_no_dos_contratos_activos(self):
        segundo = Contrato(
            apartamento=self.apto, inquilino=self.i2, fecha_inicio=self.hoy,
            fecha_vencimiento=self.hoy + timedelta(days=100), monto=Decimal("100000"),
        )
        with self.assertRaises(ValidationError):
            segundo.full_clean()

    def test_fecha_vencimiento_posterior(self):
        malo = Contrato(
            apartamento=Apartamento.objects.create(codigo="A2", monto_mensual=Decimal("1")),
            inquilino=self.i2, fecha_inicio=self.hoy, fecha_vencimiento=self.hoy, monto=Decimal("1"),
        )
        with self.assertRaises(ValidationError):
            malo.full_clean()

    def test_renovar_finaliza_anterior(self):
        nuevo = self.c1.renovar(
            fecha_inicio=self.hoy + timedelta(days=365),
            fecha_vencimiento=self.hoy + timedelta(days=730), monto=Decimal("110000"),
        )
        self.c1.refresh_from_db()
        self.assertFalse(self.c1.activo)
        self.assertTrue(nuevo.activo)
        self.assertEqual(nuevo.renovacion_de_id, self.c1.pk)
        self.assertEqual(Contrato.objects.filter(apartamento=self.apto, activo=True).count(), 1)
