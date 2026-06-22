# Standalone Module Service — Implementation Spec

**Author:** B1 (Solution Architect)  
**Date:** 2026-06-23  
**Consumer:** C2 (Implementer)  
**Status:** Ready for implementation

---

## Prerequisites (must be done before any other step)

- Add the Docker socket volume and the compose project env var to the `backend` service in `infra/docker-compose.dev.yml`. Without this, the backend cannot spawn new containers.
- Add `docker compose` (v2 plugin) and `docker` CLI to the backend container's `Dockerfile` (`backend/Dockerfile`).

---

## Decision 1 — Docker socket strategy

**Do this:** Mount `/var/run/docker.sock` into the backend container and call `docker compose` from within the backend process via `subprocess`.

**Do not** add a sidecar agent. The added operational complexity (inter-container RPC, another image to maintain) outweighs the security benefit at this stage.

**Security mitigations required:**
- The install endpoint is already guarded by `_require_superuser`. Keep that gate.
- Validate `MODULE_NAME` strictly (`^[a-z][a-z0-9_-]{1,48}$`) before passing it to any shell call. Use `subprocess` list-form args only — never `shell=True`.
- The backend runs as a non-root user in production; ensure the Docker socket group permission is set (`group: docker` or `666` in dev). Accept this risk for now.

**Required changes to `infra/docker-compose.dev.yml` backend service:**

```yaml
backend:
  volumes:
    - ../backend:/app
    - ../frontend:/frontend:ro
    - ../modules/sdk:/app/modules/sdk:ro
    - ../modules:/home/mahfudi/app-buildify/modules   # ADD — host modules dir, read-write
    - /var/run/docker.sock:/var/run/docker.sock        # ADD — Docker socket
    - ../infra:/home/mahfudi/app-buildify/infra        # ADD — for writing compose + nginx files
  environment:
    ...
    COMPOSE_PROJECT_NAME: App_Buildify                        # ADD
    MODULES_HOST_DIR: /home/mahfudi/app-buildify/modules      # ADD
    INFRA_HOST_DIR: /home/mahfudi/app-buildify/infra          # ADD
    NGINX_CONF_DIR: /home/mahfudi/app-buildify/infra/nginx    # ADD
```

> Note: volumes map **host paths** into the backend container so that the generated `docker-compose.service.yml` files reference correct host paths when Docker (which runs on the host) mounts them.

---

## Decision 2 — Module service directory structure

**Do this:** Extract the standalone tarball to the existing source directory pattern, mirroring the financial module layout exactly:

```
/home/mahfudi/app-buildify/modules/{MODULE_NAME}/
  backend/          <- extracted from tarball backend/
    app/
    requirements.txt
    Dockerfile      <- REQUIRED in the tarball
  frontend/         <- extracted from tarball frontend/ (if present)
  manifest.json     <- kept at module root for reference
```

The existing `upload-install` pipeline copies `backend/` to `/app/modules/{name}` inside the backend container. For standalone mode this path is not used — instead copy directly to the host path via the bind-mounted volume (see §1).

**DB credentials:** pass them as environment variables in the generated compose service (see §5 template). Do not use Docker secrets for dev. The module reads `DATABASE_URL` from its environment, identical to the financial module pattern.

---

## Decision 3 — Port allocation

**Do this:** Use a **static port declared in `manifest.json`**. Dynamic allocation adds complexity and makes the nginx config non-deterministic.

**Port range:** `9001–9099` (9001 = financial, 9002–9099 = uploaded modules).

**Manifest field:**

```json
{
  "name": "hr",
  "deployment": {
    "mode": "standalone",
    "port": 9002
  }
}
```

**Validation rule in install pipeline:** if `manifest.deployment.port` is absent or outside `9001–9099`, reject the upload with HTTP 400 before any files are written.

**Conflict check:** query all `install_status='ready'` modules in the DB and reject if the port is already claimed.

---

## Decision 4 — nginx routing

**Current blocker:** `infra/nginx/app.conf` has a hardcoded allowlist:

```nginx
location ~ ^/api/(v[0-9]+)/(financial|hr|clinic)/(.+)$ {
    proxy_pass http://$2-module:9001/api/$1/$2/$3$is_args$args;
```

Two problems: (1) the allowlist must be expanded for each new module; (2) the proxy target port is hardcoded to `9001`.

**Do this:** Replace the hardcoded location block with a generic include directory pattern.

**Step 4a — rewrite `infra/nginx/app.conf`:**

Remove the existing module location block. Add this directive **before** the `location /api/` block:

```nginx
# Module API routing — one include per installed standalone module
include /etc/nginx/conf.d/modules/*.conf;
```

**Step 4b — per-module conf file** written by the install pipeline to `infra/nginx/modules/{MODULE_NAME}.conf`:

```nginx
location ~ ^/api/(v[0-9]+)/({MODULE_NAME})/(.+)$ {
    proxy_pass http://{MODULE_NAME}-module:{MODULE_PORT}/api/$1/$2/$3$is_args$args;
    proxy_http_version 1.1;
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Host $http_host;
    proxy_set_header X-Forwarded-Port $server_port;
}
```

**Step 4c — nginx graceful reload (zero downtime):**

```python
subprocess.run(
    ['docker', 'exec', 'app_buildify_frontend', 'nginx', '-s', 'reload'],
    check=True
)
```

**Required: mount the modules nginx conf dir into the frontend container** in `infra/docker-compose.dev.yml`:

```yaml
frontend:
  volumes:
    - ../frontend:/usr/share/nginx/html:ro
    - ../modules:/usr/share/nginx/modules:ro
    - ../infra/nginx/app.conf:/etc/nginx/conf.d/default.conf:ro
    - ../infra/nginx/modules:/etc/nginx/conf.d/modules:ro   # ADD THIS
```

Create `infra/nginx/modules/.gitkeep` so the directory exists in the repo.

**Migration:** create `infra/nginx/modules/financial.conf` using the per-module template above with `MODULE_NAME=financial` and `MODULE_PORT=9001`. Remove the old hardcoded block from `app.conf`.

---

## Decision 5 — `docker-compose.service.yml` template

The install pipeline writes this file to `{INFRA_HOST_DIR}/modules/{MODULE_NAME}-compose.yml` on the host.

```yaml
# Auto-generated by upload-install pipeline. Do not edit manually.
name: App_Buildify

services:
  {MODULE_NAME}-module:
    container_name: app_buildify_{MODULE_NAME}
    build:
      context: /home/mahfudi/app-buildify/modules/{MODULE_NAME}/backend
      dockerfile: Dockerfile
    ports:
      - "{MODULE_PORT}:{MODULE_PORT}"
    environment:
      PYTHONPATH: /app
      DATABASE_STRATEGY: shared
      DATABASE_URL: postgresql://appuser:apppass@postgres:5432/appdb
      EVENT_BUS_CONNECTION_STRING: postgresql://appuser:apppass@postgres:5432/appdb
      MODULE_NAME: {MODULE_NAME}
      MODULE_VERSION: {MODULE_VERSION}
      MODULE_PORT: "{MODULE_PORT}"
      DEBUG: "true"
      API_PREFIX: /api/v1
      CORS_ORIGINS: '["http://localhost:8080","http://localhost:3000"]'
    working_dir: /app
    volumes:
      - /home/mahfudi/app-buildify/modules/{MODULE_NAME}/backend:/app
    networks:
      - app_buildify_default
    depends_on:
      postgres:
        condition: service_healthy

networks:
  app_buildify_default:
    external: true
```

> The network name `app_buildify_default` is auto-created by Docker Compose from `name: App_Buildify`. Verify with `docker network ls` after a fresh `docker compose up` before implementing.

---

## Decision 6 — Module Dockerfile template

Place at `modules/template/backend/Dockerfile`. Module tarballs must include a `Dockerfile` in their `backend/` directory; this template is the reference default.

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY app/ ./app/

ARG MODULE_PORT=9000
ENV MODULE_PORT=${MODULE_PORT}

EXPOSE ${MODULE_PORT}

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen(f'http://localhost:{MODULE_PORT}/health')"

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${MODULE_PORT}"]
```

> Use `sh -c` so the shell expands `$MODULE_PORT` at runtime from the environment variable injected by the compose service. The financial module uses a hardcoded port in CMD — standalone modules must use this env-var pattern.

---

## Decision 7 — Install pipeline changes

Insert the following branch in `backend/app/routers/admin_modules.py` **after** the manifest is read and the DB record is created as `in_progress`, **replacing** the existing embedded copy block for standalone mode. Add module-level constants `COMPOSE_TEMPLATE` and `NGINX_TEMPLATE` (strings from §5 and §4b).

```python
import re, subprocess, pathlib

STANDALONE_PORT_RANGE = range(9001, 9100)
MODULE_NAME_RE = re.compile(r'^[a-z][a-z0-9_-]{1,48}$')

# ... inside upload_install(), after DB record created as in_progress ...

deployment = manifest.get('deployment', {})
deploy_mode = deployment.get('mode', 'embedded')

if deploy_mode == 'standalone':
    # 1. Validate module name format
    if not MODULE_NAME_RE.match(name):
        raise ValueError(f"Invalid module name: {name!r}")

    # 2. Validate and claim port
    port = deployment.get('port')
    if not isinstance(port, int) or port not in STANDALONE_PORT_RANGE:
        raise ValueError(f"manifest.deployment.port must be an int in 9001-9099, got {port!r}")

    used_ports = [
        int(m.manifest['deployment']['port'])
        for m in db.query(Module).filter(
            Module.install_status == 'ready',
            Module.name != name,
        ).all()
        if m.manifest and isinstance(m.manifest.get('deployment', {}).get('port'), int)
    ]
    if port in used_ports:
        raise ValueError(f"Port {port} is already claimed by another module")

    # 3. Copy module source to host modules dir (via bind-mounted volume)
    modules_host_dir = os.environ['MODULES_HOST_DIR']
    dest_backend = os.path.join(modules_host_dir, name, 'backend')

    backend_src = os.path.join(module_dir, 'backend')
    if not os.path.isdir(backend_src):
        raise ValueError("Standalone module tarball must contain a backend/ directory")
    if not os.path.exists(os.path.join(backend_src, 'Dockerfile')):
        raise ValueError("Standalone module backend/ must contain a Dockerfile")

    if os.path.exists(dest_backend):
        shutil.rmtree(dest_backend)
    shutil.copytree(backend_src, dest_backend)

    frontend_src = os.path.join(module_dir, 'frontend')
    if os.path.isdir(frontend_src):
        dest_frontend = os.path.join(modules_host_dir, name, 'frontend')
        if os.path.exists(dest_frontend):
            shutil.rmtree(dest_frontend)
        shutil.copytree(frontend_src, dest_frontend)

    # 4. Write per-module docker-compose file
    infra_host_dir = os.environ['INFRA_HOST_DIR']
    compose_dir = os.path.join(infra_host_dir, 'modules')
    os.makedirs(compose_dir, exist_ok=True)
    compose_file = os.path.join(compose_dir, f'{name}-compose.yml')
    compose_content = (COMPOSE_TEMPLATE
                       .replace('{MODULE_NAME}', name)
                       .replace('{MODULE_PORT}', str(port))
                       .replace('{MODULE_VERSION}', version))
    with open(compose_file, 'w') as f:
        f.write(compose_content)

    # 5. Write per-module nginx conf
    nginx_modules_dir = os.environ['NGINX_CONF_DIR'] + '/modules'
    os.makedirs(nginx_modules_dir, exist_ok=True)
    nginx_conf_path = os.path.join(nginx_modules_dir, f'{name}.conf')
    nginx_content = (NGINX_TEMPLATE
                     .replace('{MODULE_NAME}', name)
                     .replace('{MODULE_PORT}', str(port)))
    with open(nginx_conf_path, 'w') as f:
        f.write(nginx_content)

    # 6. Run DB migrations if present (same logic as embedded path)
    alembic_src = os.path.join(module_dir, 'alembic', 'versions')
    if os.path.isdir(alembic_src):
        # ... existing alembic migration copy + run logic ...
        pass

    # 7. Build and start the module container
    result = subprocess.run(
        ['docker', 'compose', '-f', compose_file, 'up', '-d', '--build'],
        capture_output=True, text=True, timeout=300
    )
    if result.returncode != 0:
        raise RuntimeError(f"docker compose up failed:\n{result.stderr}")

    # 8. Reload nginx (graceful, zero downtime)
    result = subprocess.run(
        ['docker', 'exec', 'app_buildify_frontend', 'nginx', '-s', 'reload'],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        raise RuntimeError(f"nginx reload failed:\n{result.stderr}")

    # 9. Health-check the new service
    _wait_for_module_health(name, port, timeout=120)

    # 10. Fall through to existing "Mark ready" + registry sync block

else:
    # --- existing embedded logic (unchanged) ---
    backend_src = os.path.join(module_dir, 'backend')
    if os.path.isdir(backend_src):
        dest = f'/app/modules/{name}'
        if os.path.exists(dest):
            shutil.rmtree(dest)
        shutil.copytree(backend_src, dest)
    # ... rest of existing embedded path unchanged ...
```

---

## Decision 8 — Health check

**Do this:** HTTP poll the module's `/health` endpoint directly from the backend process. Docker inspect is slower and less meaningful than an actual HTTP liveness check.

```python
import urllib.request, time, socket

def _wait_for_module_health(module_name: str, port: int, timeout: int = 120):
    url = f'http://localhost:{port}/health'
    deadline = time.time() + timeout
    last_err = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=3) as resp:
                if resp.status == 200:
                    return  # healthy
        except (urllib.error.URLError, socket.timeout, ConnectionRefusedError) as e:
            last_err = e
        time.sleep(3)
    raise RuntimeError(
        f"Module {module_name!r} did not become healthy within {timeout}s "
        f"(last error: {last_err})"
    )
```

> The backend container reaches `localhost:{port}` because the module port is published to the host and the backend shares the host network stack in dev. If rootless Docker is adopted later, switch to `http://{module_name}-module:{port}/health` using the Docker bridge network.

Every standalone module **must** implement a `GET /health` endpoint returning HTTP 200. Document this in `modules/template/`.

---

## Implementation Checklist for C2

1. **`infra/docker-compose.dev.yml`** — `backend` service: add Docker socket volume, host modules volume, host infra volume, and four env vars (`COMPOSE_PROJECT_NAME`, `MODULES_HOST_DIR`, `INFRA_HOST_DIR`, `NGINX_CONF_DIR`).

2. **`infra/docker-compose.dev.yml`** — `frontend` service: add `../infra/nginx/modules:/etc/nginx/conf.d/modules:ro` volume.

3. **`backend/Dockerfile`** — install `docker-ce-cli` and `docker-compose-plugin` (or equivalent `docker compose` v2) into the image.

4. **`infra/nginx/app.conf`** — replace the hardcoded `(financial|hr|clinic)` location block with `include /etc/nginx/conf.d/modules/*.conf;` before the `location /api/` block.

5. **`infra/nginx/modules/financial.conf`** — create using the §4b template with `MODULE_NAME=financial` and `MODULE_PORT=9001`.

6. **`infra/nginx/modules/.gitkeep`** — create so the directory is tracked.

7. **`infra/modules/.gitkeep`** — create directory; add `infra/modules/*-compose.yml` to `.gitignore` (generated files must not be committed).

8. **`modules/template/backend/Dockerfile`** — create from §6 template.

9. **`backend/app/routers/admin_modules.py`** — add `COMPOSE_TEMPLATE`, `NGINX_TEMPLATE` constants, `_wait_for_module_health()` function, and the standalone branch in `upload_install()` (§7), including module name regex and port conflict validation.

10. **Verify Docker network name** by running `docker network ls | grep -i buildify` after a fresh `docker compose up`. Confirm the exact name used in generated compose files matches.

11. **Smoke test:** pack a minimal standalone tarball with `manifest.deployment.mode = standalone` and `port = 9002`, upload via the admin UI, confirm the container starts on 9002, and confirm `GET /api/v1/{module_name}/health` returns 200 through nginx.
