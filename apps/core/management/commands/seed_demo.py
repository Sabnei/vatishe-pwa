"""Carga datos de demostración para probar y presentar VATISHE.

Idempotente: se puede correr varias veces sin duplicar. Con ``--reset`` elimina
primero los datos de demo (usuarios/apartamentos con prefijos de demo).

    python manage.py seed_demo
    python manage.py seed_demo --reset
"""

import io
from datetime import date, timedelta
from decimal import Decimal

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.apartamentos.models import Apartamento
from apps.averias.models import Averia
from apps.cobros.models import Cobro
from apps.cobros.services import aplicar_multas, generar_cobros
from apps.contratos.models import Contrato
from apps.core.models import ConfiguracionSistema
from apps.cuentas.models import PerfilInquilino, Usuario
from apps.pagos.models import Abono

CODIGOS_DEMO = ["A-101", "A-102", "A-201"]
USERS_DEMO = ["ana", "luis", "maria", "admin_demo"]


def _imagen_demo():
    """Genera una imagen JPEG mínima para usar como comprobante de demo."""
    try:
        from PIL import Image

        buf = io.BytesIO()
        Image.new("RGB", (600, 800), (210, 200, 190)).save(buf, "JPEG")
        return ContentFile(buf.getvalue(), name="comprobante_demo.jpg")
    except Exception:
        return ContentFile(b"demo", name="comprobante_demo.txt")


class Command(BaseCommand):
    help = "Carga datos de demostración (idempotente)."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Elimina los datos de demo antes de crearlos.")

    def handle(self, *args, **opciones):
        if opciones["reset"]:
            self._reset()

        # Configuración del sistema.
        cfg = ConfiguracionSistema.cargar()
        cfg.porcentaje_multa = Decimal("10.00")
        cfg.dias_anticipacion_recordatorio = 3
        cfg.save()

        # Administrador de demo.
        admin, creado = Usuario.objects.get_or_create(
            username="admin_demo",
            defaults={"email": "admin_demo@vatishe.cr", "rol": Usuario.Rol.ADMIN,
                      "first_name": "Admin", "last_name": "Demo",
                      "is_staff": True, "is_superuser": True},
        )
        if creado:
            admin.set_password("Demo1234!")
            admin.save()

        # Inquilinos.
        inquilinos = {}
        for username, nombre, apellido in [
            ("ana", "Ana", "Mora"), ("luis", "Luis", "Vargas"), ("maria", "María", "Rojas"),
        ]:
            u, creado = Usuario.objects.get_or_create(
                username=username,
                defaults={"email": f"{username}@example.com", "rol": Usuario.Rol.INQUILINO,
                          "first_name": nombre, "last_name": apellido, "telefono": "8888-0000"},
            )
            if creado:
                u.set_password("Demo1234!")
                u.save()
            PerfilInquilino.objects.get_or_create(usuario=u, defaults={"cedula": "1-1111-1111"})
            inquilinos[username] = u

        # Apartamentos.
        aptos = {}
        for codigo, monto, dia in [("A-101", 250000, 1), ("A-102", 180000, 5), ("A-201", 300000, 15)]:
            a, _ = Apartamento.objects.get_or_create(
                codigo=codigo,
                defaults={"monto_mensual": Decimal(monto), "dia_vencimiento": dia,
                          "descripcion": f"Apartamento {codigo} de demostración."},
            )
            aptos[codigo] = a

        hoy = timezone.localdate()
        inicio = hoy.replace(day=1) - timedelta(days=90)

        # Contratos activos (A-101 → Ana, A-102 → Luis). A-201 queda desocupado.
        self._contrato(aptos["A-101"], inquilinos["ana"], inicio, hoy + timedelta(days=300), 250000)
        self._contrato(aptos["A-102"], inquilinos["luis"], inicio, hoy + timedelta(days=300), 180000)

        # Cobros: mes anterior y mes actual.
        mes_ant = (hoy.replace(day=1) - timedelta(days=1))
        generar_cobros(mes_ant.year, mes_ant.month)
        generar_cobros(hoy.year, hoy.month)

        # Ana paga completo el mes actual (abono aprobado).
        cobro_ana = Cobro.objects.filter(apartamento=aptos["A-101"], anio=hoy.year, mes=hoy.month).first()
        if cobro_ana and not cobro_ana.abonos.exists():
            ab = Abono.objects.create(
                cobro=cobro_ana, monto=cobro_ana.saldo_por_cubrir, fecha=hoy,
                metodo=Abono.Metodo.SINPE, referencia="DEMO-001",
                registrado_por=inquilinos["ana"], comprobante=_imagen_demo(),
            )
            ab.aprobar(admin)

        # Luis: abono parcial pendiente de verificación en el mes actual.
        cobro_luis = Cobro.objects.filter(apartamento=aptos["A-102"], anio=hoy.year, mes=hoy.month).first()
        if cobro_luis and not cobro_luis.abonos.exists():
            Abono.objects.create(
                cobro=cobro_luis, monto=Decimal("90000"), fecha=hoy,
                metodo=Abono.Metodo.TRANSFERENCIA, referencia="DEMO-002",
                registrado_por=inquilinos["luis"], comprobante=_imagen_demo(),
            )

        # Cobro vencido de Luis (mes anterior) con multa por morosidad.
        cobro_venc = Cobro.objects.filter(apartamento=aptos["A-102"], anio=mes_ant.year, mes=mes_ant.month).first()
        if cobro_venc:
            cobro_venc.fecha_vencimiento = hoy - timedelta(days=8)
            cobro_venc.save(update_fields=["fecha_vencimiento"])
        aplicar_multas(hoy)

        # Averías.
        if not Averia.objects.filter(apartamento=aptos["A-101"]).exists():
            Averia.objects.create(
                apartamento=aptos["A-101"], inquilino=inquilinos["ana"], area=Averia.Area.COCINA,
                descripcion="Fuga en el grifo de la cocina.", estado=Averia.Estado.PENDIENTE,
            )
        if not Averia.objects.filter(apartamento=aptos["A-102"]).exists():
            Averia.objects.create(
                apartamento=aptos["A-102"], inquilino=inquilinos["luis"], area=Averia.Area.BANO,
                descripcion="Azulejo suelto con filtración.", estado=Averia.Estado.EN_REPARACION,
                gasto=Decimal("35000"), atendida_por=admin,
            )

        self.stdout.write(self.style.SUCCESS(
            "Datos de demo cargados.\n"
            "  Admin:      admin_demo / Demo1234!\n"
            "  Inquilinos: ana / luis / maria  (contraseña: Demo1234!)\n"
            "  Apartamentos: A-101 (Ana), A-102 (Luis), A-201 (desocupado)"
        ))

    def _contrato(self, apto, inquilino, inicio, fin, monto):
        if not Contrato.objects.filter(apartamento=apto, activo=True).exists():
            Contrato.objects.create(
                apartamento=apto, inquilino=inquilino, fecha_inicio=inicio,
                fecha_vencimiento=fin, monto=Decimal(monto),
            )

    def _reset(self):
        Abono.objects.filter(cobro__apartamento__codigo__in=CODIGOS_DEMO).delete()
        Averia.objects.filter(apartamento__codigo__in=CODIGOS_DEMO).delete()
        Cobro.objects.filter(apartamento__codigo__in=CODIGOS_DEMO).delete()
        Contrato.objects.filter(apartamento__codigo__in=CODIGOS_DEMO).delete()
        Apartamento.objects.filter(codigo__in=CODIGOS_DEMO).delete()
        Usuario.objects.filter(username__in=USERS_DEMO).delete()
        self.stdout.write(self.style.WARNING("Datos de demo previos eliminados."))
