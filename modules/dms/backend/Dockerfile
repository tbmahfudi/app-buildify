FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .
# manifest.json lives one level up (modules/dms/manifest.json), outside this
# build context. In dev it is bind-mounted to /app/manifest.json (see compose).
# For a packaged prod image, build with context=modules/dms and copy it in.

EXPOSE 9003

HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:9003/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9003"]
