# Getting Started

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Docker | 24+ | Container runtime |
| Docker Compose | 2.0+ | Multi-container orchestration |
| Python | 3.11+ | Backend development |
| Node.js | 18+ | Frontend testing |
| Make | Any | Build commands |

---

## Quick Start (Docker)

### 1. Clone and Configure

```bash
git clone <repo-url> app-buildify
cd app-buildify
cp backend/.env.example backend/.env
```

Edit `backend/.env` with your settings:

```env
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/buildify
REDIS_URL=redis://redis:6379
JWT_SECRET_KEY=your-secret-key-change-in-production
DEBUG=true
ENVIRONMENT=development
```

### 2. Start All Services

```bash
make docker-up
# or directly:
docker-compose up -d
```

### 3. Run Database Migrations

```bash
make migrate-pg
# or:
docker-compose exec core-platform alembic upgrade head
```

### 4. Seed Initial Data

```bash
make seed
# This creates default tenant, admin user, roles, and permissions
```

### 5. Access the Application

| Service | URL | Notes |
|---------|-----|-------|
| Frontend | http://localhost | Main application UI |
| Backend API | http://localhost/api/v1 | REST API |
| API Docs (Swagger) | http://localhost:8000/docs | Interactive API explorer |
| API Docs (Redoc) | http://localhost:8000/redoc | Alternative docs |

**Default admin credentials** (from seed):
- Email: `admin@example.com`
- Password: `Admin@123`

> **Change the default password immediately after first login.**

---

## Local Development Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate          # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # Edit with local DB config
alembic upgrade head
python -m app.seeds.seed_org       # Seed organization
python -m app.seeds.seed_users     # Seed users
uvicorn app.main:app --reload --port 8000
```

### Frontend

No build step is required for development — the frontend is pure vanilla JavaScript.

Open `frontend/index.html` directly in a browser, or serve via the Docker container:

```bash
docker-compose up frontend
```

For running frontend tests:

```bash
npm install
npm test
# or with UI:
npm run test:ui
```

---

## Make Commands Reference

| Command | Description |
|---------|-------------|
| `make setup` | Install all dependencies |
| `make migrate-pg` | Run PostgreSQL migrations |
| `make migrate-mysql` | Run MySQL migrations |
| `make seed` | Seed the database with default data |
| `make run` | Run backend locally with hot-reload |
| `make docker-up` | Start all Docker services |
| `make docker-down` | Stop all Docker services |
| `make docker-logs` | Tail Docker container logs |
| `make clean` | Remove build artifacts |

---

## Project Structure

```
app-buildify/
├── backend/          # FastAPI Core Platform
├── frontend/         # Vanilla JS + Flex Component Library
├── modules/
│   └── financial/    # Example pluggable module
├── infra/
│   └── nginx/        # API Gateway config
├── docs/             # All documentation
├── tests/            # Integration tests
├── scripts/          # Utility shell/Python scripts
├── docker-compose.yml
└── Makefile
```

---

## First Steps After Setup

1. **Log in** with the admin account at http://localhost
2. **Create a tenant** if one doesn't exist (`/org/tenants`)
3. **Create a company** under the tenant (`/org/companies`)
4. **Create roles and assign permissions** (`/rbac`)
5. **Invite users** and assign them roles (`/users`)
6. **Design a data model** (`/nocode/data-model`)
7. **Enable modules** if needed (`/modules`)

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| DB connection refused | Ensure postgres container is healthy: `docker-compose ps` |
| Redis connection refused | Check redis container: `docker-compose logs redis` |
| Migration fails | Check `DATABASE_URL` in `.env` and run `alembic current` |
| 401 on API calls | Token may be expired — log in again or check `JWT_SECRET_KEY` |
| Module not visible | Re-register module and reload: `POST /api/v1/modules/register` |
