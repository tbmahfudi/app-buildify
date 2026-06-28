# Healthcare Module — standalone microservice image.
#
# The healthcare routers + SDK depend on the core platform package (app.core.*,
# app.models.base) re-exported through modules.sdk.*. Rather than vendor that
# package, this dev image builds FROM the already-built core backend image so
# the full `app` package and all platform Python deps are present at /app
# (PYTHONPATH=/app). The healthcare source + shared SDK are bind-mounted at
# runtime into /app/modules (see infra/docker-compose.dev.yml) for live reload.
#
# Entry point: modules.healthcare.app.main:app
#
# NOTE (prod hardening — see report follow-ups): for a truly self-contained
# production image, vendor the platform `app` package (or publish it as a wheel)
# and build FROM python:3.11-slim using requirements.txt instead of FROM the
# backend image.
FROM app_buildify-backend:latest

WORKDIR /app

# Ensure healthcare-specific runtime deps are present even if the base image
# pin set ever drifts (redis client is required by the OTP/patient-auth flow).
COPY requirements.txt /tmp/healthcare-requirements.txt
RUN pip install --no-cache-dir "redis>=5.0" "PyJWT>=2.8" "cryptography>=41.0"

EXPOSE 9002

HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:9002/health')"

CMD ["uvicorn", "modules.healthcare.app.main:app", "--host", "0.0.0.0", "--port", "9002"]
