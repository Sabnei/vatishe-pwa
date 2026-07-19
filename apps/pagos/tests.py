"""Tests de pagos: verificación de comprobantes, saldo y privacidad (RF-005/006)."""

import io
from datetime import date
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.apartamentos.models import Apartamento
from apps.cobros.models import Cobro
from apps.cuentas.models import Usuario
from apps.pagos.forms import AbonoForm
from apps.pagos.models import Abono


def _imagen():
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (300, 300), (120, 120, 120)).save(buf, "JPEG")
    return SimpleUploadedFile("r.jpg", buf.getvalue(), content_type="image/jpeg")


class VerificacionTests(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_superuser(username="adm", email="a@x.com", password="x")
        self.inq = Usuario.objects.create_user(username="inq", email="i@x.com", password="x", rol=Usuario.Rol.INQUILINO)
        self.apto = Apartamento.objects.create(codigo="A1", monto_mensual=Decimal("100000"))
        self.cobro = Cobro.objects.create(
            apartamento=self.apto, inquilino=self.inq, anio=2026, mes=1,
            monto=Decimal("100000"), fecha_vencimiento=date(2026, 1, 1),
        )

    def test_abono_pendiente_no_afecta_saldo(self):
        Abono.objects.create(cobro=self.cobro, monto=Decimal("100000"), fecha=date(2026, 1, 2),
                             metodo=Abono.Metodo.SINPE, registrado_por=self.inq, comprobante="x.jpg")
        self.assertEqual(self.cobro.saldo_pendiente, Decimal("100000"))

    def test_aprobar_actualiza_saldo_y_estado(self):
        ab = Abono.objects.create(cobro=self.cobro, monto=Decimal("100000"), fecha=date(2026, 1, 2),
                                  metodo=Abono.Metodo.SINPE, registrado_por=self.inq, comprobante="x.jpg")
        ab.aprobar(self.admin)
        self.cobro.refresh_from_db()
        self.assertEqual(self.cobro.saldo_pendiente, Decimal("0"))
        self.assertEqual(self.cobro.estado, Cobro.Estado.PAGADO)

    def test_rechazar_no_afecta_saldo(self):
        ab = Abono.objects.create(cobro=self.cobro, monto=Decimal("100000"), fecha=date(2026, 1, 2),
                                  metodo=Abono.Metodo.SINPE, registrado_por=self.inq, comprobante="x.jpg")
        ab.rechazar(self.admin, "Ilegible")
        self.cobro.refresh_from_db()
        self.assertTrue(ab.rechazado)
        self.assertEqual(self.cobro.saldo_pendiente, Decimal("100000"))

    def test_form_bloquea_sobrepago(self):
        form = AbonoForm(
            data={"monto": "150000", "fecha": "2026-01-02", "metodo": "SINPE"},
            files={"comprobante": _imagen()}, cobro=self.cobro,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("monto", form.errors)


class PrivacidadComprobanteTests(TestCase):
    def setUp(self):
        self.inq = Usuario.objects.create_user(username="inq", email="i@x.com", password="x", rol=Usuario.Rol.INQUILINO)
        self.otro = Usuario.objects.create_user(username="otro", email="o@x.com", password="x", rol=Usuario.Rol.INQUILINO)
        apto = Apartamento.objects.create(codigo="A1", monto_mensual=Decimal("100000"))
        cobro = Cobro.objects.create(apartamento=apto, inquilino=self.inq, anio=2026, mes=1,
                                     monto=Decimal("100000"), fecha_vencimiento=date(2026, 1, 1))
        self.abono = Abono.objects.create(cobro=cobro, monto=Decimal("50000"), fecha=date(2026, 1, 2),
                                          metodo=Abono.Metodo.SINPE, registrado_por=self.inq, comprobante=_imagen())

    def test_ajeno_no_ve_comprobante(self):
        self.client.force_login(self.otro)
        r = self.client.get(f"/pagos/abono/{self.abono.pk}/comprobante/")
        self.assertEqual(r.status_code, 403)

    def test_dueno_ve_comprobante(self):
        self.client.force_login(self.inq)
        r = self.client.get(f"/pagos/abono/{self.abono.pk}/comprobante/")
        self.assertEqual(r.status_code, 200)
