# Run migrations (use 'heads' to upgrade all branches: PostgreSQL, MySQL, SQLite)
docker-compose -f infra/docker-compose.dev.yml exec backend alembic upgrade heads

# Seed data
docker-compose exec backend python -m app.seeds.seed_org
docker-compose exec backend python -m app.seeds.seed_users
docker-compose exec backend python -m app.seeds.seed_metadata

# Test
docker-compose exec backend ./test_api_option_b.sh