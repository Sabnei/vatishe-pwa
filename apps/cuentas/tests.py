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


class GestionAdministradoresTests(TestCase):
    """Alta y gestión de administradores desde la app (RF-001)."""

    def setUp(self):
        self.admin = Usuario.objects.create_superuser(
            username="adm", email="a@x.com", password="x"
        )
        self.inq = Usuario.objects.create_user(
            username="inq", email="i@x.com", password="x", rol=Usuario.Rol.INQUILINO
        )

    def test_inquilino_no_accede_a_administradores(self):
        self.client.force_login(self.inq)
        self.assertEqual(self.client.get("/cuentas/administradores/").status_code, 403)

    def test_admin_crea_otro_admin(self):
        self.client.force_login(self.admin)
        r = self.client.post(
            "/cuentas/administradores/nuevo/",
            {
                "username": "adm2",
                "first_name": "Ana",
                "last_name": "Solis",
                "email": "Adm2@X.com",
                "telefono": "88880000",
                "password1": "Clave123!segura",
                "password2": "Clave123!segura",
            },
        )
        self.assertEqual(r.status_code, 302)
        nuevo = Usuario.objects.get(username="adm2")
        self.assertTrue(nuevo.es_admin)
        self.assertEqual(nuevo.email, "adm2@x.com")
        # Sin marcar la casilla no obtiene acceso al admin de Django.
        self.assertFalse(nuevo.is_staff)
        self.assertTrue(nuevo.check_password("Clave123!segura"))

    def test_promover_inquilino_a_admin(self):
        self.client.force_login(self.admin)
        r = self.client.post(
            "/cuentas/administradores/promover/", {"usuario": self.inq.pk}
        )
        self.assertEqual(r.status_code, 302)
        self.inq.refresh_from_db()
        self.assertTrue(self.inq.es_admin)

    def test_no_puede_desactivarse_a_si_mismo(self):
        self.client.force_login(self.admin)
        self.client.post(f"/cuentas/usuarios/{self.admin.pk}/estado/")
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_no_se_puede_dejar_el_sistema_sin_admin(self):
        otro = Usuario.objects.create_superuser(
            username="adm3", email="a3@x.com", password="x"
        )
        self.admin.is_active = False
        self.admin.save(update_fields=["is_active"])
        self.client.force_login(otro)
        # "otro" es el unico admin activo: degradarlo debe rechazarse.
        self.client.post(f"/cuentas/administradores/{otro.pk}/degradar/")
        otro.refresh_from_db()
        self.assertTrue(otro.es_admin)

    def test_degradar_admin_lo_deja_como_inquilino(self):
        otro = Usuario.objects.create_superuser(
            username="adm4", email="a4@x.com", password="x"
        )
        self.client.force_login(self.admin)
        r = self.client.post(f"/cuentas/administradores/{otro.pk}/degradar/")
        self.assertEqual(r.status_code, 302)
        otro.refresh_from_db()
        self.assertTrue(otro.es_inquilino)
        self.assertFalse(otro.is_staff)
        self.assertTrue(hasattr(otro, "perfil_inquilino"))
