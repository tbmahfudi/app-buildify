# TEMPLATE Module Migrations

Place Alembic migration scripts in this directory.

## Naming convention

```
NNN_short_description.py
```

e.g. `001_initial_template_tables.py`

## Generating a migration

```bash
# From the project root:
manage.sh module pack TEMPLATE          # build the module
manage.sh module install TEMPLATE_v1.0.0.tar.gz   # installs & runs migrations
```

Or manually during development:
```bash
cd backend
alembic revision --autogenerate -m "initial_template_tables"
alembic upgrade head
```

## Important rules

- Every migration must be reversible (implement `downgrade()`).
- Never drop columns in a migration — mark them deprecated first.
- All tables must include `tenant_id` (see `models.py`).
