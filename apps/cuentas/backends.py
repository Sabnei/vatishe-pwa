"""Backend de autenticación que permite iniciar sesión con usuario o correo."""

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q


class UsuarioOEmailBackend(ModelBackend):
    """Autentica con el nombre de usuario o el correo (indistintamente).

    El correo es único, así que la búsqueda es inequívoca. Se ejecuta el hasheo
    aunque el usuario no exista para no filtrar por tiempo qué correos existen.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        Usuario = get_user_model()
        if username is None:
            username = kwargs.get(Usuario.USERNAME_FIELD)
        if username is None or password is None:
            return None
        try:
            usuario = Usuario.objects.get(
                Q(username__iexact=username) | Q(email__iexact=username)
            )
        except Usuario.DoesNotExist:
            # Mitiga ataques de temporización (igual que ModelBackend).
            Usuario().set_password(password)
            return None
        except Usuario.MultipleObjectsReturned:
            # Caso extremo: un username coincide con el email de otro usuario.
            usuario = (
                Usuario.objects.filter(
                    Q(username__iexact=username) | Q(email__iexact=username)
                )
                .order_by("id")
                .first()
            )
        if usuario.check_password(password) and self.user_can_authenticate(usuario):
            return usuario
        return None
