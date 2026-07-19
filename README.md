# VATISHE — PWA de gestión de cobros y pagos de alquiler

Aplicación web progresiva (PWA) para **VATISHE S.R.L.** que centraliza la gestión
de cobros y pagos de alquiler de apartamentos: apartamentos, inquilinos, contratos,
cobros mensuales, abonos con comprobante, verificación, multas por morosidad,
averías y reportes. Trabajo Final de Graduación.

- **Administrador:** gestiona apartamentos, inquilinos, contratos, cobros, multas,
  averías y reportes.
- **Inquilino:** consulta su saldo e historial, registra abonos y sube comprobantes,
  y reporta averías.

Los pagos se realizan **por fuera** (SINPE Móvil, transferencia o depósito); en el
sistema solo se sube el comprobante para que el Administrador lo verifique.

## Stack

- **Backend:** Python 3.12, Django 5.1 (patrón MVT, SSR, monolito).
- **Frontend:** Django Templates + HTML5 + **TailwindCSS** + JavaScript vanilla (sin SPA).
- **PWA:** `manifest.webmanifest` + service worker, instalable y responsive desde 360px.
- **Base de datos:** PostgreSQL gestionado (**Supabase**, pooler Supavisor). SQLite en local.
- **Archivos:** **Supabase Storage** (S3, bucket privado) vía `django-storages` + `boto3`.
- **PDF:** WeasyPrint. **CSV** nativo. **Correo:** Gmail SMTP.
- **Tareas programadas:** management commands ejecutables por cron (sin Celery).
- **Producción:** Gunicorn + WhiteNoise, desplegable en Render con Docker.

## Estructura del proyecto

```
config/                 # proyecto Django (settings, urls, wsgi)
apps/
  core/                 # configuración, notificaciones, PWA, tareas, mixins de rol
  cuentas/              # usuarios (rol Admin/Inquilino), autenticación, perfiles
  apartamentos/         # apartamentos
  contratos/            # contratos de arrendamiento y renovaciones
  cobros/               # cobros mensuales y multas (+ servicios y commands)
  pagos/                # abonos y verificación de comprobantes
  averias/              # reporte y gestión de averías
  reportes/             # reportes de ganancias y morosidad (PDF/CSV)
templates/              # plantillas (base + por app + PWA + PDF)
static/                 # CSS de Tailwind compilado, JS, íconos PWA
bin/tailwindcss         # CLI standalone de Tailwind (no versionado)
scripts/build_css.sh    # compila el CSS
```

## Requisitos

- Python 3.12+
- (Opcional en local) PostgreSQL; por defecto se usa SQLite.
- Para generar PDFs con WeasyPrint hacen falta librerías de sistema
  (libpango, libcairo, libgdk-pixbuf). En el `Dockerfile` ya están incluidas.

## Instalación local

```bash
# 1. Entorno virtual e instalación
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Variables de entorno
cp .env.example .env          # y edítalo (ver sección Variables de entorno)

# 3. Compilar el CSS de Tailwind (usa el CLI standalone en bin/)
./scripts/build_css.sh        # o ./scripts/build_css.sh --watch mientras desarrollas

# 4. Migraciones y usuario administrador
python manage.py migrate
python manage.py createsuperuser        # crea un Admin

# 5. (Opcional) Datos de demostración
python manage.py seed_demo
#   Admin:      admin_demo / Demo1234!
#   Inquilinos: ana / luis / maria  (contraseña: Demo1234!)

# 6. Levantar el servidor
python manage.py runserver
# App:  http://localhost:8000
```

> El `.env` con `DATABASE_URL` vacío usa **SQLite** y guarda los archivos en
> `media/` y los correos en la **consola** — ideal para desarrollo sin credenciales.

## Variables de entorno

Todas las credenciales se leen del entorno (`.env` en local). Ver `.env.example`.

| Variable | Descripción |
|---|---|
| `SECRET_KEY` | Clave secreta de Django. |
| `DEBUG` | `True` en local, `False` en producción. |
| `ALLOWED_HOSTS` | Hosts permitidos (coma-separados). |
| `CSRF_TRUSTED_ORIGINS` | Orígenes HTTPS de confianza en producción. |
| `SITE_URL` | URL pública (enlaces de correos). |
| `DATABASE_URL` | Cadena del pooler de Supabase (puerto 6543). Vacío → SQLite. |
| `DB_DISABLE_SERVER_SIDE_CURSORS` | `True` con el pooler en modo *transaction*. |
| `USE_SUPABASE_STORAGE` | `True` para guardar archivos en Supabase Storage. |
| `SUPABASE_S3_ACCESS_KEY_ID` / `SUPABASE_S3_SECRET_ACCESS_KEY` | Claves S3 de Supabase Storage. |
| `SUPABASE_S3_BUCKET` / `SUPABASE_S3_ENDPOINT_URL` / `SUPABASE_S3_REGION` | Bucket privado y endpoint S3. |
| `BREVO_API_KEY` | API key de Brevo. Si está definida, se envía por Brevo (API HTTP). |
| `EMAIL_ENABLED` | `True` para enviar por Gmail SMTP en local; `False` → consola. |
| `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` | Correo y contraseña de aplicación de Gmail. |
| `DEFAULT_FROM_EMAIL` | Remitente de los correos. |
| `CRON_TOKEN` | Token para el endpoint de tareas programadas por HTTP. |
| `MAX_UPLOAD_SIZE_MB` | Tamaño máximo de comprobantes (compresión de imágenes). |
| `PAGINACION_POR_PAGINA` | Registros por página en los listados (20). |

## Tareas programadas (cron)

Se implementan como management commands (no dependen de Celery):

```bash
python manage.py generar_cobros [--anio 2026 --mes 7]   # cobros del mes (RF-004)
python manage.py aplicar_multas [--fecha 2026-07-19]    # morosidad (RF-007)
python manage.py enviar_recordatorios [--fecha ...]     # recordatorios (RF-010)
python manage.py tareas_diarias                         # las tres de una vez
```

En producción, dos opciones:

1. **Cron del sistema / Render Cron Job:** ejecutar `tareas_diarias` una vez al día.
2. **Cron externo por HTTP** (para hosting gratuito sin cron nativo): un servicio
   externo hace `POST` diario a `/cron/tareas-diarias/` con el header
   `X-Cron-Token: <CRON_TOKEN>`.

## Tests

```bash
python manage.py test
```

Cubren la lógica crítica: generación de cobros, saldo/estado, multas y exoneración,
verificación de comprobantes, bloqueo de sobrepago, privacidad de comprobantes,
restricción de contrato único activo, averías y control de acceso por rol.

## Despliegue (Render + Supabase)

1. **Supabase:** crea un proyecto; obtén la cadena del **pooler** (Transaction, 6543)
   para `DATABASE_URL`; crea un **bucket privado** `vatishe` en Storage y una
   **S3 access key** para las variables `SUPABASE_S3_*`.
2. **Correo (Brevo):** Render (y muchos hostings gratuitos) **bloquea el SMTP saliente**,
   así que en producción se envía por la **API HTTP de Brevo** (gratis, 300 correos/día).
   Crea una cuenta en brevo.com, **verifica el remitente** (p. ej. tu Gmail) y genera una
   **API key**; ponla en `BREVO_API_KEY`. En local puedes seguir usando Gmail SMTP
   (`EMAIL_ENABLED=True`) o dejar los correos en consola.
3. **Render:** conecta el repositorio; el `render.yaml` define el servicio web (Docker).
   Completa en el panel las variables marcadas como `sync: false`. Render construye la
   imagen (que instala las libs de WeasyPrint, recolecta estáticos y aplica migraciones
   al arrancar) y sirve con Gunicorn + WhiteNoise.
4. **Dominio:** ajusta `ALLOWED_HOSTS` y `CSRF_TRUSTED_ORIGINS` con tu dominio.
5. **Primer uso:** crea el Admin con `python manage.py createsuperuser` (o corre
   `seed_demo` para datos de prueba) desde la shell de Render.

### Respaldo de la base de datos (RNF-004)

Supabase realiza respaldos automáticos gestionados. Para un respaldo manual:

```bash
# Exportar (usa la cadena de conexión directa de Supabase, no el pooler)
pg_dump "postgresql://USUARIO:CONTRASENA@HOST:5432/postgres" -Fc -f respaldo_vatishe.dump

# Restaurar
pg_restore --clean --no-owner -d "postgresql://.../postgres" respaldo_vatishe.dump
```

## Licencia

Proyecto académico (Trabajo Final de Graduación). Uso educativo.
