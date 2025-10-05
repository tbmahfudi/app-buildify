.PHONY: help setup migrate seed run clean docker-up docker-down

help:
	@echo "Available commands:"
	@echo "  make setup        - Install dependencies and setup environment"
	@echo "  make migrate-pg   - Run PostgreSQL migrations"
	@echo "  make migrate-mysql - Run MySQL migrations"
	@echo "  make seed         - Seed database with test data"
	@echo "  make run          - Run backend server"
	@echo "  make docker-up    - Start Docker environment"
	@echo "  make docker-down  - Stop Docker environment"
	@echo "  make clean        - Clean up artifacts"

setup:
	@echo "Setting up backend..."
	cd backend && pip install -r requirements.txt
	@if [ ! -f backend/.env ]; then \
		cp backend/.env.example backend/.env; \
		echo "Created backend/.env - please update SECRET_KEY"; \
	fi

migrate-pg:
	@echo "Running PostgreSQL migrations..."
	cd backend && alembic upgrade pg_a1b2c3d4e5f6

migrate-mysql:
	@echo "Running MySQL migrations..."
	cd backend && alembic upgrade mysql_f6e5d4c3b2a1

seed:
	@echo "Seeding database..."
	cd backend && python -m app.seeds.seed_org
	cd backend && python -m app.seeds.seed_users
	cd backend && python -m app.seeds.seed_metadata

run:
	@echo "Starting backend server..."
	cd backend && uvicorn app.main:app --reload

docker-up:
	@echo "Starting Docker environment..."
	docker-compose -f docker-compose.dev.yml up -d
	@echo "Waiting for database to be ready..."
	sleep 5
	@echo "Running migrations..."
	docker-compose -f docker-compose.dev.yml exec backend alembic upgrade head
	@echo "Seeding data..."
	docker-compose -f docker-compose.dev.yml exec backend python -m app.seeds.seed_org
	docker-compose -f docker-compose.dev.yml exec backend python -m app.seeds.seed_users
	@echo ""
	@echo "✅ Environment ready!"
	@echo "Frontend: http://localhost:8080"
	@echo "Backend:  http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"

docker-down:
	docker-compose -f docker-compose.dev.yml down

docker-logs:
	docker-compose -f docker-compose.dev.yml logs -f

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf backend/.venv
	rm -f backend/app.db