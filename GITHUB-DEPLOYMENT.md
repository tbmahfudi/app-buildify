# GitHub Deployment Guide

## 🚀 Push Option A MVP to GitHub

### Step 1: Commit All Changes

```bash
# Navigate to your repo root
cd /path/to/app-buildify

# Check status
git status

# Add all new files
git add .

# Commit with descriptive message
git commit -m "feat: Implement Option A MVP - Auth & Org CRUD

- Add User model with JWT authentication
- Implement login, refresh, and me endpoints
- Complete CRUD for companies, branches, departments
- Add RBAC with role-based access control
- Create PostgreSQL and MySQL migrations
- Add seed data for users and organizations
- Integrate frontend auth with auto-refresh
- Add Companies UI with full CRUD operations
- Include Docker Compose for local development
- Add Makefile for quick setup
- Include automated API test script

Test credentials:
- admin@example.com / admin123
- user@example.com / user123
- viewer@example.com / viewer123"

# Push to GitHub
git push origin main
```

### Step 2: Update GitHub Repository Settings

#### Set Repository Secrets (for CI/CD later)
Go to: Settings → Secrets and variables → Actions

Add these secrets:
- `SECRET_KEY` - Generate with: `openssl rand -hex 32`
- `POSTGRES_PASSWORD` - Your production DB password
- `MYSQL_PASSWORD` - Your production DB password (if using MySQL)

### Step 3: Create GitHub Actions (Optional CI/CD)

Create `.github/workflows/backend-tests.yml`:

```yaml
name: Backend Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: testuser
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: testdb
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
    
    - name: Run migrations
      env:
        SQLALCHEMY_DATABASE_URL: postgresql+psycopg2://testuser:testpass@localhost:5432/testdb
        SECRET_KEY: test-secret-key-for-ci
      run: |
        cd backend
        alembic upgrade head
    
    - name: Seed data
      env:
        SQLALCHEMY_DATABASE_URL: postgresql+psycopg2://testuser:testpass@localhost:5432/testdb
      run: |
        cd backend
        python -m app.seeds.seed_org
        python -m app.seeds.seed_users
    
    - name: Run API tests
      env:
        SQLALCHEMY_DATABASE_URL: postgresql+psycopg2://testuser:testpass@localhost:5432/testdb
        SECRET_KEY: test-secret-key-for-ci
      run: |
        cd backend
        uvicorn app.main:app --host 0.0.0.0 --port 8000 &
        sleep 5
        chmod +x test_api.sh
        ./test_api.sh
```

### Step 4: Create Docker Build Workflow

Create `.github/workflows/docker-build.yml`:

```yaml
name: Build and Push Docker Images

on:
  push:
    branches: [ main ]
    tags:
      - 'v*'

env:
  REGISTRY: ghcr.io
  IMAGE_PREFIX: ${{ github.repository_owner }}

jobs:
  build-backend:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
    - uses: actions/checkout@v3
    
    - name: Log in to Container Registry
      uses: docker/login-action@v2
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v4
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}/app-backend
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}
          type=sha
    
    - name: Build and push Backend
      uses: docker/build-push-action@v4
      with:
        context: ./backend
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}

  build-frontend:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
    - uses: actions/checkout@v3
    
    - name: Log in to Container Registry
      uses: docker/login-action@v2
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v4
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}/app-frontend
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}
          type=sha
    
    - name: Build and push Frontend
      uses: docker/build-push-action@v4
      with:
        context: ./frontend
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
```

### Step 5: Update README.md

Update your root `README.md` with badges and info:

```markdown
# app-buildify

[![Backend Tests](https://github.com/YOUR_USERNAME/app-buildify/workflows/Backend%20Tests/badge.svg)](https://github.com/YOUR_USERNAME/app-buildify/actions)
[![Docker Build](https://github.com/YOUR_USERNAME/app-buildify/workflows/Build%20and%20Push%20Docker%20Images/badge.svg)](https://github.com/YOUR_USERNAME/app-buildify/actions)

App-Buildify Mono Repo - NoCode Application Platform

## 🚀 Quick Start

**Option 1: Docker (Recommended)**
```bash
make docker-up
```

**Option 2: Manual**
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env and set SECRET_KEY
alembic upgrade head
python -m app.seeds.seed_org
python -m app.seeds.seed_users
uvicorn app.main:app --reload
```

## 📚 Documentation

- [Setup Guide](SETUP.md)
- [Implementation Summary](IMPLEMENTATION_SUMMARY.md)
- [Backend README](backend/README.md)
- [API Documentation](http://localhost:8000/docs) (when running)

## 🧪 Test Credentials

- **Admin**: admin@example.com / admin123
- **User**: user@example.com / user123
- **Viewer**: viewer@example.com / viewer123

## ✅ Features (Option A MVP)

### Backend
- ✅ JWT Authentication (login, refresh, me)
- ✅ User Management with RBAC
- ✅ Organization Hierarchy (Companies, Branches, Departments)
- ✅ Complete CRUD APIs
- ✅ Multi-tenant support
- ✅ PostgreSQL & MySQL support

### Frontend
- ✅ Login with auto-refresh tokens
- ✅ Protected routes
- ✅ Companies CRUD interface
- ✅ Responsive Bootstrap UI

### DevOps
- ✅ Docker Compose for local dev
- ✅ Automated migrations
- ✅ Seed data scripts
- ✅ API test automation

## 🏗️ Architecture

```
app-buildify/
├── backend/          # FastAPI + SQLAlchemy
│   ├── app/
│   │   ├── models/   # Database models
│   │   ├── schemas/  # Pydantic schemas
│   │   ├── routers/  # API endpoints
│   │   ├── core/     # Config, auth, dependencies
│   │   ├── alembic/  # Database migrations
│   │   └── seeds/    # Seed data
│   └── Dockerfile
├── frontend/         # Vanilla JS + Bootstrap
│   ├── assets/
│   │   ├── js/       # App logic
│   │   ├── css/      # Styles
│   │   └── templates/ # HTML templates
│   └── index.html
└── infra/            # Deployment configs
    └── nginx/
```

## 🔜 Roadmap

See [tracking spreadsheet] for full feature status.

### Next Up (Option B)
- [ ] Metadata Service
- [ ] Generic CRUD endpoints
- [ ] Audit logging
- [ ] Settings/Preferences API
- [ ] Dashboard with real data

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

[Your License Here]

## 🙋 Support

For issues and questions, please use the GitHub issue tracker.
```

### Step 6: Create Release

After pushing, create a release on GitHub:

```bash
# Tag the release
git tag -a v0.1.0 -m "Release v0.1.0 - Option A MVP Complete

Features:
- JWT Authentication
- Organization CRUD
- RBAC
- Multi-tenant support
- Docker environment
"

# Push the tag
git push origin v0.1.0
```

Then on GitHub:
1. Go to: Releases → Draft a new release
2. Choose tag: v0.1.0
3. Title: "v0.1.0 - Option A MVP"
4. Description:
   ```markdown
   ## 🎉 Option A MVP Complete
   
   This release implements the foundation features for the NoCode platform.
   
   ### ✅ Features
   - JWT Authentication with refresh tokens
   - User management with RBAC
   - Complete organization hierarchy (Companies, Branches, Departments)
   - PostgreSQL and MySQL support
   - Docker Compose development environment
   - Automated test suite
   
   ### 🚀 Quick Start
   ```bash
   make docker-up
   ```
   
   ### 📚 Documentation
   - [Setup Guide](SETUP.md)
   - [API Documentation](http://localhost:8000/docs)
   
   ### 🧪 Test Credentials
   - Admin: admin@example.com / admin123
   - User: user@example.com / user123
   - Viewer: viewer@example.com / viewer123
   ```

### Step 7: Enable GitHub Pages (Optional)

If you want to host frontend as a demo:

1. Go to: Settings → Pages
2. Source: Deploy from a branch
3. Branch: main, folder: /frontend
4. Save

Note: You'll need to configure API_BASE in frontend to point to your hosted backend.

## 📋 Complete Git Commands Summary

```bash
# 1. Stage all changes
git add .

# 2. Check what will be committed
git status

# 3. Commit with detailed message
git commit -m "feat: Implement Option A MVP - Auth & Org CRUD

Complete implementation of authentication system and organization management:

Backend:
- User model with JWT authentication
- Login, refresh, and me endpoints
- RBAC with role-based access control
- Complete CRUD for companies, branches, departments
- PostgreSQL and MySQL migrations
- Database session management
- Seed data for testing

Frontend:
- Auth integration with auto-refresh
- Companies UI with full CRUD
- Protected routes
- Token management

DevOps:
- Docker Compose for local development
- Makefile for quick commands
- Automated API test script
- Comprehensive documentation

Test credentials:
- admin@example.com / admin123 (superuser)
- user@example.com / user123 (regular user)
- viewer@example.com / viewer123 (read-only)
"

# 4. Push to main branch
git push origin main

# 5. Create and push tag
git tag -a v0.1.0 -m "Release v0.1.0 - Option A MVP Complete"
git push origin v0.1.0

# 6. View commit log
git log --oneline -5
```

## 🎯 Next Steps After Push

1. ✅ Verify GitHub Actions run successfully
2. ✅ Check Docker images are built and published
3. ✅ Create GitHub Release from tag
4. ✅ Update project board/issues
5. ✅ Share with team for review
6. ✅ Plan Option B implementation

## 🔍 Verify Deployment

After pushing, check:
- [ ] All files are in repository
- [ ] GitHub Actions pass (if configured)
- [ ] Docker images are published to ghcr.io
- [ ] README displays correctly
- [ ] Documentation is accessible
- [ ] Release is created with proper notes

Your Option A MVP is now on GitHub! 🎊