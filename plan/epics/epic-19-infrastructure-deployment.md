# Epic 19 — Infrastructure & Deployment

> Docker-based containerization, Nginx reverse proxy, database migrations, CI/CD pipeline, and cloud storage.

---

## Feature 19.1 — Docker and Container Setup `[DONE / OPEN]`

### Story 19.1.1 — Development Docker Compose `[DONE]`

#### Backend
*As a developer, I want a single `make docker-up` command to start all services, so that local development is a one-line setup.*
- `docker-compose.yml` (or `infra/docker-compose.dev.yml`) defines services: `postgres`, `redis`, `backend`, `financial-module`, `frontend`, `nginx`
- All services have `healthcheck` configs; `backend` and `financial-module` have `depends_on` with `condition: service_healthy` for postgres and redis
- Volume mounts enable code hot-reload: `./backend:/app` for FastAPI (uvicorn `--reload`); `./frontend:/usr/share/nginx/html` for frontend static files

#### Frontend
*As a developer who just cloned the repo, I want one command to get a working local environment, so that I can start contributing within 5 minutes.*
- No dedicated route — dev setup is a CLI/Makefile concern; documented in `README.md` "Quick Start"

- Quick start steps: `cp backend/.env.example backend/.env` → `make docker-up`
- Services after startup: Frontend at `http://localhost:8080` | API at `http://localhost:8000/api/v1` | Swagger at `http://localhost:8000/api/docs`
- Helper commands: `make docker-logs` (tails all service logs) | `make docker-down` (stops all) | `make health` (calls each service health endpoint)

---

### Story 19.1.2 — Production Docker Compose `[OPEN]`

#### Backend
*As a DevOps engineer, I want a production-hardened Docker Compose file with no bind mounts, tagged images, and proper secrets management, so that production deployments are reproducible.*
- `infra/docker-compose.prod.yml` uses image references: `ghcr.io/{org}/app-backend:{TAG}`, `ghcr.io/{org}/app-frontend:{TAG}`, `ghcr.io/{org}/financial-module:{TAG}`
- Environment variables loaded from `--env-file .env.prod`; no secrets in the Compose file
- Data stored in named volumes (`postgres_data`, `redis_data`); no bind mounts
- Nginx service includes SSL certificate volume mount and sets `HTTPS_ONLY=true`

#### Frontend
*No specific frontend story — production deployment is a DevOps concern.*
- No dedicated route — documented in `docs/deployment/PRODUCTION.md`
- Deployment checklist covers: environment variables | SSL certificate setup | database migration command | health check verification | rollback procedure

---

### Story 19.1.3 — Nginx Routing Configuration `[DONE]`

#### Backend
*As a DevOps engineer, I want Nginx to route all API traffic to the correct backend service based on the URL prefix, so that the single-origin frontend reaches all microservices.*
- `/api/v1/financial/` proxied to `financial-module:9001`; strip prefix
- `/api/` proxied to `backend:8000`
- `/modules/{name}/` serves module frontend static files from the module's `frontend/` directory
- `location /` falls back to `index.html` (SPA hash routing)
- Gzip: `gzip on; gzip_types text/javascript application/json text/css;`

#### Frontend
*As a developer debugging a routing issue, I want the Nginx config to be clearly commented so I can quickly find and update proxy rules, so that routing changes don't require reading nginx.org documentation.*
- No dedicated route — Nginx config is an infrastructure file; no UI involved

- `infra/nginx/nginx.conf`: each `location` block has an inline comment explaining what it routes and why
- Separate `location` blocks for: API | financial module API | module static files | main SPA
- Dev and production configs split: `nginx.dev.conf` | `nginx.prod.conf`

---

## Feature 19.2 — Database Migrations `[DONE]`

### Story 19.2.1 — Alembic Migration Management `[DONE]`

#### Backend
*As a developer, I want all schema changes managed via Alembic migration files, so that database upgrades are version-controlled and reproducible.*
- `alembic upgrade head` applies all pending migrations; `alembic downgrade -1` reverts one
- Auto-runs at startup via `lifespan` handler in `main.py`
- Migration files in `backend/app/alembic/versions/postgresql/` — 70+ files covering all tables

#### Frontend
*As a developer running migrations manually, I want clear `make` commands and error messages, so that migration issues are diagnosable without Alembic expertise.*
- No dedicated route — migration tooling is a CLI/Makefile concern; no UI involved

- Commands: `make migrate` (upgrade head) | `make migrate-status` (current revision) | `make migrate-history` (migration chain)
- On migration failure: FastAPI `lifespan` catches Alembic errors and logs them clearly; app does NOT start (prevents runtime schema mismatches)

---

### Story 19.2.2 — Module-Specific Alembic Setup `[DONE]`

#### Backend
*As a module developer, I want an independent Alembic environment for my module, so that module schema changes are managed without touching the core platform migrations.*
- Each code module has `backend/alembic/alembic.ini` + `env.py` + `versions/`
- Module `env.py` uses the same `DATABASE_URL` as the core platform; module tables use the module's `table_prefix` to avoid name collisions
- `docker-compose exec financial-module alembic upgrade head` runs module migrations

#### Frontend
*No specific frontend story — Alembic is a developer/DevOps concern.*
- No dedicated route — Makefile exposes module migration commands: `make migrate-financial` | `make migrate-all` (core + all modules in dependency order)

---

## Feature 19.3 — Cloud Storage Integration `[PLANNED]`

### Story 19.3.1 — S3-Compatible File Storage `[PLANNED]`

#### Backend
*As an API, I want a `StorageService` that abstracts file operations over S3-compatible APIs, so that file uploads and downloads work across AWS S3, MinIO, and GCS without code changes.*
- `StorageService` (in `backend/app/core/storage.py`) wraps `boto3` for S3-compatible operations
- Config: `STORAGE_BACKEND` (`local`/`s3`), `S3_BUCKET`, `S3_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `S3_ENDPOINT_URL` (for MinIO)
- `PUT /api/v1/files/upload-url` generates a presigned PUT URL valid for 15 minutes
- `GET /api/v1/files/{key}` generates a presigned GET URL valid for `PRESIGNED_URL_TTL` seconds
- Local fallback: `STORAGE_BACKEND=local` stores files in a `/data/uploads/` volume for development

#### Frontend
*As a developer integrating file upload into a form, I want `StorageService.getUploadUrl(filename)` to return a presigned URL I can PUT the file to directly from the browser, so that large files don't pass through the backend.*
- No dedicated route — `storage-service.js` is a shared service used by `FlexFileUpload` and any attachment-enabled page

- `storage-service.js` API:
  - `getUploadUrl(filename, contentType)` → GET /files/upload-url → `{upload_url, file_key}`
  - `getDownloadUrl(fileKey)` → GET /files/{key} → presigned download URL
- `FlexFileUpload` calls `StorageService.getUploadUrl()` then PUTs directly to the presigned URL (browser → S3)
- On upload complete: `file_key` stored in the entity record via the attachments API

---

### Story 19.3.2 — Entity Record Attachments API `[PLANNED]`

#### Backend
*As an API, I want a standard attachments API for entity records, so that any entity with `supports_attachments = true` can have files attached.*
- `POST /api/v1/dynamic-data/{entity}/records/{id}/attachments` with `{file_key, file_name, content_type, file_size}` creates an attachment metadata record
- `GET /api/v1/dynamic-data/{entity}/records/{id}/attachments` returns attachment list
- `DELETE /api/v1/dynamic-data/{entity}/records/{id}/attachments/{attachment_id}` removes metadata (optionally deletes from storage)

#### Frontend
*As a user viewing a record detail page for an entity that supports attachments, I want an "Attachments" tab where I can drag-and-drop files to attach them and download or delete existing attachments, so that supporting documents are organized with each record.*
- Route: `#/dynamic/{entity}/{id}` → record detail page; "Attachments" FlexTabs tab (rendered only when `entity.supports_attachments = true`)
- Layout: FlexStack(direction=vertical) > drop-zone, attachments-list
  - drop-zone: FlexFileUpload — "Drag files here or click to upload"
  - attachments-list: FlexDataGrid(static) — file icon | File Name | Size | Uploaded By | Upload Date | "Download" link | × delete icon

- Interactions:
  - drop or select file: `StorageService.getUploadUrl()` called → file PUT to presigned URL → POST /dynamic-data/{entity}/records/{id}/attachments {file_key, file_name, content_type, file_size} → new row appears in attachments-list
  - click "Download" link: GET /files/{key} → presigned download URL → browser download
  - click × delete: FlexModal(size=sm) confirm "Remove [filename] from this record?" → DELETE /dynamic-data/{entity}/records/{id}/attachments/{id} → row removed
  - file exceeds size limit or disallowed type: rejected client-side before presigned URL request; FlexAlert(type=error) inline

- States:
  - loading: attachments-list shows skeleton rows while GET /attachments resolves
  - empty: "No attachments yet" + drop-zone prominently shown
  - uploading: FlexFileUpload chip shows progress bar

---

## Feature 19.4 — CI/CD Pipeline `[PLANNED]`

### Story 19.4.1 — GitHub Actions CI Pipeline `[PLANNED]`

#### Backend
*As a developer, I want every pull request to run automated checks, so that failing tests and lint errors are caught before merging.*
- `.github/workflows/ci.yml`: triggers on `pull_request` to `main` and `develop`
- Jobs (run in parallel where possible):
  - `lint-backend`: `ruff check backend/` + `mypy backend/app/`
  - `test-backend`: `pytest backend/tests/` with coverage; fails if coverage < 80%
  - `lint-frontend`: ESLint on `frontend/assets/js/`
  - `test-frontend`: `vitest run` with coverage; fails if coverage < 80%
- PR is blocked (branch protection rule) if any job fails
- Test results uploaded as workflow artifacts; coverage report as a PR comment

#### Frontend
*As a developer opening a pull request, I want to see the CI status check results directly on the PR page with links to the failure details, so that I know exactly what to fix before requesting a review.*
- No dedicated route — CI results surface in GitHub PR UI via status checks; no platform UI involved

- PR status checks: `lint-backend` | `test-backend` | `lint-frontend` | `test-frontend` — each shows ✓ or ✗ with link to workflow run
- Coverage comment posted automatically on PR: "Coverage changed from X% → Y% (±Z%)"

---

### Story 19.4.2 — GitHub Actions CD Pipeline `[PLANNED]`

#### Backend
*As a DevOps engineer, I want container images automatically built and pushed on merge to main, so that the latest code is always available in the registry.*
- `.github/workflows/cd.yml`: triggers on `push` to `main`
- Build and push `app-backend`, `app-frontend`, `financial-module` images to `ghcr.io/{org}/{image}:{sha}` and `:latest`
- Multi-platform builds: `linux/amd64` and `linux/arm64`
- Deployment job (after images pushed): SSHes to production server and runs `docker-compose pull && docker-compose up -d`

#### Frontend
*As a DevOps engineer after a successful deployment, I want to see the commit SHA in the platform's admin health page so that I can verify which version is running, so that deployment confirmation is self-service.*
- Route: `#/admin/health` → admin health page (Story 13.3.1); version info added to "Platform Version" metric card
- Layout addition (`#/admin` page-header): version FlexBadge(color=neutral) "v1.2.0 (abc1234)"

- Interactions:
  - page load: GET /admin/version → "Platform Version" card populates with `version`, `commit_sha`, `deployed_at`
