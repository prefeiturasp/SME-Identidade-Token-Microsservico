FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=token_ms.settings

RUN apt-get update && apt-get install -y --no-install-recommends \
        curl libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput 2>/dev/null || true

EXPOSE 8003

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -sf http://localhost:8003/api/health/ || exit 1

CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn token_ms.wsgi:application --bind 0.0.0.0:8003 --workers 3 --timeout 60"]
