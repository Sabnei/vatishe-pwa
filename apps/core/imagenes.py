"""Utilidad para comprimir imágenes de comprobantes/averías a <= 1 MB (RNF-002)."""

import io

from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile

try:
    from PIL import Image
except ImportError:  # Pillow siempre está en requirements; guarda por seguridad.
    Image = None

EXTENSIONES_IMAGEN = {"jpg", "jpeg", "png", "webp", "heic", "heif"}


def es_imagen(nombre):
    return nombre.rsplit(".", 1)[-1].lower() in EXTENSIONES_IMAGEN if "." in nombre else False


def comprimir_imagen(archivo, max_mb=None, max_lado=1600):
    """Redimensiona y recomprime una imagen para que pese <= ``max_mb``.

    Devuelve un ``InMemoryUploadedFile`` JPEG. Si el archivo no es imagen o
    Pillow no está disponible, devuelve el archivo original sin cambios.
    """
    if Image is None or not es_imagen(getattr(archivo, "name", "")):
        return archivo

    max_mb = max_mb or getattr(settings, "MAX_UPLOAD_SIZE_MB", 1)
    limite_bytes = int(max_mb * 1024 * 1024)

    imagen = Image.open(archivo)
    if imagen.mode in ("RGBA", "P", "LA"):
        imagen = imagen.convert("RGB")

    # Redimensiona si excede el lado máximo (mantiene proporción).
    imagen.thumbnail((max_lado, max_lado), Image.LANCZOS)

    # Baja la calidad progresivamente hasta cumplir el límite de tamaño.
    calidad = 90
    buffer = io.BytesIO()
    while True:
        buffer.seek(0)
        buffer.truncate(0)
        imagen.save(buffer, format="JPEG", quality=calidad, optimize=True)
        if buffer.tell() <= limite_bytes or calidad <= 40:
            break
        calidad -= 10

    buffer.seek(0)
    nombre_base = getattr(archivo, "name", "comprobante").rsplit(".", 1)[0]
    nombre = f"{nombre_base}.jpg"
    return InMemoryUploadedFile(
        buffer, "comprobante", nombre, "image/jpeg", buffer.getbuffer().nbytes, None
    )
