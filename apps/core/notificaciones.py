"""Envío de correos con bitácora para evitar duplicados (RF-010)."""

from django.conf import settings
from django.core.mail import send_mail

from apps.core.models import RegistroCorreo


def enviar_correo(tipo, destinatario, asunto, cuerpo, clave_unicidad="", evitar_duplicado=False):
    """Envía un correo y lo registra en la bitácora.

    Si ``evitar_duplicado`` es True y ya existe un envío exitoso con la misma
    ``clave_unicidad``, no se vuelve a enviar (útil para recordatorios).
    Devuelve el ``RegistroCorreo`` creado, o ``None`` si se omitió por duplicado.
    """
    if evitar_duplicado and clave_unicidad:
        ya_enviado = RegistroCorreo.objects.filter(
            tipo=tipo, clave_unicidad=clave_unicidad, exitoso=True
        ).exists()
        if ya_enviado:
            return None

    exitoso = True
    detalle_error = ""
    try:
        send_mail(
            asunto,
            cuerpo,
            settings.DEFAULT_FROM_EMAIL,
            [destinatario],
            fail_silently=False,
        )
    except Exception as exc:  # noqa: BLE001 - se registra el error para diagnóstico
        exitoso = False
        detalle_error = str(exc)

    return RegistroCorreo.objects.create(
        tipo=tipo,
        destinatario=destinatario,
        asunto=asunto,
        clave_unicidad=clave_unicidad,
        exitoso=exitoso,
        detalle_error=detalle_error,
    )
