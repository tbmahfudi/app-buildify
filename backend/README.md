# Backend Package (Org + Alembic + Seeds)

## DB URLs
- PostgreSQL: `postgresql+psycopg2://user:pass@host/db`
- MySQL: `mysql+pymysql://user:pass@host/db`
- SQLite (dev): `sqlite:///./app.db`

## Migrations
Start a fresh DB with ONE of these chains:

**PostgreSQL**
```bash
export SQLALCHEMY_DATABASE_URL=postgresql+psycopg2://user:pass@localhost/app
alembic upgrade +pg_0d5ad21b0f
```

**MySQL**
```bash
export SQLALCHEMY_DATABASE_URL=mysql+pymysql://user:pass@localhost/app
alembic upgrade +mysql_8c4ee763aa
```

## Seed
```bash
export SQLALCHEMY_DATABASE_URL=...  # same as migrated DB
python -m app.seeds.seed_org
```

## Run the API
```bash
uvicorn app.main:app --reload
```
