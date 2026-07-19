"""Tests de seguridad y control de acceso por rol (RF-001, RNF-003)."""

from django.test import TestCase

from apps.cuentas.models import Usuario


class RolTests(TestCase):
    def test_propiedades_de_rol(self):
        admin = Usuario.objects.create_superuser(username="adm", email="a@x.com", password="x")
        inq = Usuario.objects.create_user(username="inq", email="i@x.com", password="x", rol=Usuario.Rol.INQUILINO)
        self.assertTrue(admin.es_admin)
        self.assertFalse(admin.es_inquilino)
        self.assertTrue(inq.es_inquilino)
        self.assertFalse(inq.es_admin)

    def test_email_obligatorio_unico(self):
        Usuario.objects.create_user(username="a", email="dup@x.com", password="x", rol=Usuario.Rol.INQUILINO)
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            Usuario.objects.create_user(username="b", email="dup@x.com", password="x", rol=Usuario.Rol.INQUILINO)


class LoginConEmailTests(TestCase):
    def setUp(self):
        self.u = Usuario.objects.create_user(
            username="pedro", email="Pedro@Example.com", password="Clave123!",
            rol=Usuario.Rol.INQUILINO,
        )

    def test_login_por_username(self):
        self.assertTrue(self.client.login(username="pedro", password="Clave123!"))

    def test_login_por_email(self):
        self.assertTrue(self.client.login(username="pedro@example.com", password="Clave123!"))

    def test_login_password_incorrecta(self):
        self.assertFalse(self.client.login(username="pedro@example.com", password="mala"))


class AccesoRolTests(TestCase):
    def setUp(self):
        self.inq = Usuario.objects.create_user(username="inq", email="i@x.com", password="x", rol=Usuario.Rol.INQUILINO)
        self.admin = Usuario.objects.create_superuser(username="adm", email="a@x.com", password="x")

    def test_inquilino_bloqueado_en_admin(self):
        self.client.force_login(self.inq)
        for url in ["/cuentas/usuarios/", "/apartamentos/", "/contratos/", "/cobros/", "/pagos/verificar/", "/reportes/ganancias/"]:
            self.assertEqual(self.client.get(url).status_code, 403, url)

    def test_admin_accede(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get("/cuentas/usuarios/").status_code, 200)
        self.assertEqual(self.client.get("/apartamentos/").status_code, 200)

    def test_anonimo_redirige_a_login(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 302)
        self.assertIn("/cuentas/login/", r["Location"])
