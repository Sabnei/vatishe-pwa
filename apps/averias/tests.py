"""Tests de averías: creación, cambio de estado y notificación (RF-008)."""

from decimal import Decimal

from django.test import TestCase

from apps.apartamentos.models import Apartamento
from apps.averias.models import Averia
from apps.core.models import RegistroCorreo
from apps.cuentas.models import Usuario


class AveriaTests(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_superuser(username="adm", email="a@x.com", password="x")
        self.inq = Usuario.objects.create_user(username="inq", email="i@x.com", password="x", rol=Usuario.Rol.INQUILINO)
        self.apto = Apartamento.objects.create(codigo="A1", monto_mensual=Decimal("100000"))
        self.averia = Averia.objects.create(
            apartamento=self.apto, inquilino=self.inq, area=Averia.Area.BANO,
            descripcion="Fuga", estado=Averia.Estado.PENDIENTE,
        )

    def test_estado_inicial_pendiente(self):
        self.assertEqual(self.averia.estado, Averia.Estado.PENDIENTE)

    def test_cambio_estado_admin_notifica(self):
        self.client.force_login(self.admin)
        r = self.client.post(
            f"/averias/gestion/{self.averia.pk}/",
            {"estado": "EN_REPARACION", "gasto": "25000", "notas_admin": "En curso"},
        )
        self.assertEqual(r.status_code, 302)
        self.averia.refresh_from_db()
        self.assertEqual(self.averia.estado, Averia.Estado.EN_REPARACION)
        self.assertEqual(self.averia.gasto, Decimal("25000"))
        self.assertTrue(
            RegistroCorreo.objects.filter(
                tipo=RegistroCorreo.Tipo.AVERIA_ACTUALIZADA,
                clave_unicidad=f"averia:{self.averia.pk}:estado:EN_REPARACION",
            ).exists()
        )

    def test_solucionado_fija_fecha(self):
        self.averia.cambiar_estado(Averia.Estado.SOLUCIONADO, self.admin)
        self.assertIsNotNone(self.averia.fecha_solucion)

    def test_inquilino_no_gestiona(self):
        self.client.force_login(self.inq)
        r = self.client.get("/averias/gestion/")
        self.assertEqual(r.status_code, 403)
