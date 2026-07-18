"""Configuración de Django para el proyecto VATISHE.

Toda credencial o parámetro sensible se lee de variables de entorno (con
``python-dotenv`` en local desde un archivo ``.env`` que NO se versiona).
La base de datos por defecto es SQLite en local; en producción se usa la cadena
del pooler de Supabase (Supavisor) vía ``DATABASE_URL``.
"""

import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Carga el archivo .env si existe (solo relevante en desarrollo local).
load_dotenv(BASE_DIR / ".env")


def env_bool(nombre, por_defecto=False):
    return os.getenv(nombre, str(por_defecto)).strip().lower() in {"1", "true", "yes", "on"}


def env_list(nombre, por_defecto=""):
    valor = os.getenv(nombre, por_defecto)
    return [item.strip() for item in valor.split(",") if item.strip()]


# --------------------------------------------------------------------------- #
# Seguridad
# --------------------------------------------------------------------------- #
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "django-insecure-cambia-esta-clave-solo-para-desarrollo-local",
)
DEBUG = env_bool("DEBUG", True)
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")

CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")

# Token compartido para disparar las tareas programadas vía HTTP (cron externo).
CRON_TOKEN = os.getenv("CRON_TOKEN", "")


# --------------------------------------------------------------------------- #
# Aplicaciones
# --------------------------------------------------------------------------- #
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "storages",
]

LOCAL_APPS = [
    "apps.core",
    "apps.cuentas",
    "apps.apartamentos",
    "apps.contratos",
    "apps.cobros",
    "apps.pagos",
    "apps.averias",
    "apps.reportes",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise sirve los estáticos comprimidos en producción.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.configuracion_sistema",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# --------------------------------------------------------------------------- #
# Base de datos
# --------------------------------------------------------------------------- #
# En local, si no hay DATABASE_URL, se usa SQLite. En producción se define
# DATABASE_URL con la cadena del pooler de Supabase (Supavisor).
DATABASE_URL = os.getenv("DATABASE_URL", "")

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=int(os.getenv("DB_CONN_MAX_AGE", "60")),
            ssl_require=env_bool("DB_SSL_REQUIRE", True),
        )
    }
    # Con el pooler de Supabase en modo *transaction* (puerto 6543) hay que
    # desactivar los cursores del lado del servidor.
    if env_bool("DB_DISABLE_SERVER_SIDE_CURSORS", True):
        DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# --------------------------------------------------------------------------- #
# Autenticación
# --------------------------------------------------------------------------- #
AUTH_USER_MODEL = "cuentas.Usuario"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "cuentas:login"
LOGIN_REDIRECT_URL = "core:inicio"
LOGOUT_REDIRECT_URL = "cuentas:login"


# --------------------------------------------------------------------------- #
# Internacionalización (Costa Rica)
# --------------------------------------------------------------------------- #
LANGUAGE_CODE = "es"
TIME_ZONE = "America/Costa_Rica"
USE_I18N = True
USE_TZ = True


# --------------------------------------------------------------------------- #
# Archivos estáticos y multimedia
# --------------------------------------------------------------------------- #
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# Almacenamiento de archivos: Supabase Storage (S3) si hay credenciales; si no,
# disco local (solo desarrollo). Los comprobantes van a un bucket PRIVADO y sus
# URLs requieren sesión activa (se sirven mediante vistas protegidas).
USE_SUPABASE_STORAGE = env_bool("USE_SUPABASE_STORAGE", False)

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

if USE_SUPABASE_STORAGE:
    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    }
    AWS_ACCESS_KEY_ID = os.getenv("SUPABASE_S3_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY = os.getenv("SUPABASE_S3_SECRET_ACCESS_KEY", "")
    AWS_STORAGE_BUCKET_NAME = os.getenv("SUPABASE_S3_BUCKET", "vatishe")
    AWS_S3_ENDPOINT_URL = os.getenv("SUPABASE_S3_ENDPOINT_URL", "")
    AWS_S3_REGION_NAME = os.getenv("SUPABASE_S3_REGION", "us-east-1")
    AWS_S3_ADDRESSING_STYLE = "path"  # requerido por Supabase Storage
    AWS_DEFAULT_ACL = None  # bucket privado
    AWS_QUERYSTRING_AUTH = True  # URLs firmadas y temporales
    AWS_QUERYSTRING_EXPIRE = int(os.getenv("SUPABASE_S3_URL_EXPIRE", "300"))
    AWS_S3_FILE_OVERWRITE = False
else:
    STORAGES["default"] = {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    }
    MEDIA_URL = "media/"
    MEDIA_ROOT = BASE_DIR / "media"

# Límite de subida: comprobantes/fotos se comprimen a <= 1 MB (RNF-002).
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "1"))

# Paginación por defecto en listados (RNF-002).
PAGINACION_POR_PAGINA = int(os.getenv("PAGINACION_POR_PAGINA", "20"))


# --------------------------------------------------------------------------- #
# Correo (Gmail SMTP con contraseña de aplicación)
# --------------------------------------------------------------------------- #
if env_bool("EMAIL_ENABLED", False):
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
    EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
    EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
    EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
else:
    # En desarrollo los correos se imprimen en la consola.
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "VATISHE <no-reply@vatishe.cr>")
SITE_URL = os.getenv("SITE_URL", "http://localhost:8000")


# --------------------------------------------------------------------------- #
# Seguridad en producción
# --------------------------------------------------------------------------- #
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "2592000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
