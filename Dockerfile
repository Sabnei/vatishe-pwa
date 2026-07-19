# --- VATISHE — imagen de producción -----------------------------------------
FROM python:3.12-slim

# Evita prompts y buffering; salida de logs inmediata.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Librerías de sistema requeridas por WeasyPrint (PDF) y psycopg2.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libcairo2 \
        libgdk-pixbuf-2.0-0 \
        libffi8 \
        libjpeg62-turbo \
        libpq5 \
        fonts-dejavu-core \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instala dependencias de Python primero (mejor caché).
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copia el proyecto (incluye el CSS de Tailwind ya compilado en static/css/).
COPY . .

# Recolecta los estáticos (WhiteNoise los sirve comprimidos).
RUN DJANGO_COLLECTSTATIC=1 SECRET_KEY=build-only DEBUG=False \
    python manage.py collectstatic --noinput

# Puerto que expone Gunicorn (Render usa $PORT).
ENV PORT=8000
EXPOSE 8000

# Arranca: aplica migraciones y levanta Gunicorn.
CMD sh -c "python manage.py migrate --noinput && \
    gunicorn config.wsgi:application --bind 0.0.0.0:${PORT} \
    --workers 2 --timeout 120 --max-requests 500 --max-requests-jitter 50"
