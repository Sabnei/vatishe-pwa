"""Tests de la configuración del sistema editable desde la app (RF-010)."""

from decimal import Decimal

from django.test import TestCase

from apps.core.forms import ConfiguracionSistemaForm
from apps.core.models import ConfiguracionSistema
from apps.cuentas.models import Usuario

URL_CONFIG = "/configuracion/"

DATOS_VALIDOS = {
    "nombre_empresa": "VATISHE S.R.L.",
    "porcentaje_multa": "7.50",
    "monto_multa_fijo": "0",
    "dias_anticipacion_recordatorio": "5",
}


class ConfiguracionSistemaFormTests(TestCase):
    def test_porcentaje_fuera_de_rango_rechazado(self):
        form = ConfiguracionSistemaForm(
            data={**DATOS_VALIDOS, "porcentaje_multa": "150"},
            instance=ConfiguracionSistema.cargar(),
        )
        self.assertFalse(form.is_valid())
        self.assertIn("porcentaje_multa", form.errors)

    def test_montos_negativos_rechazados(self):
        form = ConfiguracionSistemaForm(
            data={**DATOS_VALIDOS, "monto_multa_fijo": "-100"},
            instance=ConfiguracionSistema.cargar(),
        )
        self.assertFalse(form.is_valid())
        self.assertIn("monto_multa_fijo", form.errors)

    def test_dias_anticipacion_con_tope(self):
        form = ConfiguracionSistemaForm(
            data={**DATOS_VALIDOS, "dias_anticipacion_recordatorio": "90"},
            instance=ConfiguracionSistema.cargar(),
        )
        self.assertFalse(form.is_valid())
        self.assertIn("dias_anticipacion_recordatorio", form.errors)


class ConfiguracionSistemaViewTests(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_superuser(
            username="adm", email="a@x.com", password="x"
        )
        self.inq = Usuario.objects.create_user(
            username="inq", email="i@x.com", password="x", rol=Usuario.Rol.INQUILINO
        )

    def test_inquilino_no_accede(self):
        self.client.force_login(self.inq)
        self.assertEqual(self.client.get(URL_CONFIG).status_code, 403)

    def test_anonimo_redirige_a_login(self):
        r = self.client.get(URL_CONFIG)
        self.assertEqual(r.status_code, 302)
        self.assertIn("/cuentas/login/", r["Location"])

    def test_admin_edita_parametros(self):
        self.client.force_login(self.admin)
        r = self.client.post(URL_CONFIG, DATOS_VALIDOS)
        self.assertEqual(r.status_code, 302)
        config = ConfiguracionSistema.cargar()
        self.assertEqual(config.porcentaje_multa, Decimal("7.50"))
        self.assertEqual(config.dias_anticipacion_recordatorio, 5)
        # El singleton nunca crea filas adicionales.
        self.assertEqual(ConfiguracionSistema.objects.count(), 1)

    def test_inquilino_no_puede_guardar(self):
        self.client.force_login(self.inq)
        self.assertEqual(self.client.post(URL_CONFIG, DATOS_VALIDOS).status_code, 403)
        self.assertEqual(
            ConfiguracionSistema.cargar().dias_anticipacion_recordatorio, 3
        )
