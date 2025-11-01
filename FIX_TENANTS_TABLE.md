# Fixing "relation 'tenants' does not exist" Error

## Problem

You're seeing this error:
```
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.UndefinedTable) relation "tenants" does not exist
```

This means your database migrations haven't been run yet, so the `tenants` table doesn't exist in your database.

## Quick Fix

### Option 1: Using the Migration Helper Script (Recommended)

We've created a helper script to make this easy:

```bash
cd backend
python run_migrations.py
```

The script will:
- ✓ Detect your database type automatically
- ✓ Test your database connection
- ✓ Run all necessary migrations
- ✓ Create the tenants table and all other required tables

### Option 2: Manual Migration with Alembic

If you prefer to run migrations manually:

```bash
cd backend

# Set your database URL (if not in .env)
export SQLALCHEMY_DATABASE_URL="postgresql://user:password@localhost:5432/appdb"

# Run migrations
alembic upgrade heads
```

### Option 3: Using Docker Compose

If you're using Docker Compose:

```bash
# From project root
./manage.sh migrate postgres
```

Or directly:

```bash
docker compose -f infra/docker-compose.dev.yml exec backend alembic upgrade heads
```

## Setting Up Database Connection

### 1. Create .env File

Create a `.env` file in the `backend` directory:

```bash
cd backend
cp .env.template .env
```

### 2. Configure Database URL

Edit the `.env` file and set your database connection:

**For PostgreSQL:**
```env
SQLALCHEMY_DATABASE_URL=postgresql+psycopg2://username:password@localhost:5432/database_name
```

**For MySQL:**
```env
SQLALCHEMY_DATABASE_URL=mysql+pymysql://username:password@localhost:3306/database_name
```

**For SQLite (Development):**
```env
SQLALCHEMY_DATABASE_URL=sqlite:///./app.db
```

### 3. Run Migrations

After setting up the database URL, run the migration script:

```bash
python run_migrations.py
```

## Common Issues & Solutions

### Issue 1: "No database URL found"

**Solution:** Make sure you have either:
- Created a `.env` file with `SQLALCHEMY_DATABASE_URL`
- Set the `SQLALCHEMY_DATABASE_URL` environment variable
- Passed the database URL as an argument: `python run_migrations.py "postgresql://..."`

### Issue 2: "Database connection failed"

**Solution:** Check that:
- Your database server is running
- Database credentials are correct
- Database host and port are accessible
- The database exists (create it if needed)

For PostgreSQL:
```bash
# Create database
psql -U postgres -c "CREATE DATABASE appdb;"
```

For MySQL:
```bash
# Create database
mysql -u root -p -e "CREATE DATABASE appdb;"
```

### Issue 3: "Permission denied"

**Solution:** Ensure your database user has permission to create tables:

For PostgreSQL:
```sql
GRANT ALL PRIVILEGES ON DATABASE appdb TO your_user;
```

For MySQL:
```sql
GRANT ALL PRIVILEGES ON appdb.* TO 'your_user'@'localhost';
FLUSH PRIVILEGES;
```

### Issue 4: Multiple migration heads

If you see "Multiple heads" error:

```bash
cd backend
alembic merge heads -m "Merge migration heads"
alembic upgrade head
```

## Verifying the Fix

After running migrations, verify the tenants table exists:

**PostgreSQL:**
```bash
psql -U your_user -d appdb -c "\dt tenants"
```

**MySQL:**
```bash
mysql -u your_user -p appdb -e "SHOW TABLES LIKE 'tenants';"
```

**SQLite:**
```bash
sqlite3 app.db ".tables tenants"
```

## What Tables Are Created?

The migration creates these tables:
- `tenants` - Top-level tenant entities for multi-company architecture
- `companies` - Company entities belonging to tenants
- `branches` - Branch locations for companies
- `departments` - Departments within companies
- `users` - User accounts
- `roles` - Role definitions for RBAC
- `permissions` - Permission definitions
- `groups` - User groups
- `user_company_access` - Junction table for user-company relationships
- And various RBAC junction tables

## Migration Structure

The application uses database-specific migrations:
- `pg_*.py` - PostgreSQL migrations
- `mysql_*.py` - MySQL migrations
- `sqlite_*.py` - SQLite migrations

The correct migrations are automatically selected based on your database URL.

## Getting Help

If you continue to experience issues:

1. Check the migration logs for detailed error messages
2. Verify your database server logs
3. Ensure you have the required Python packages installed:
   ```bash
   pip install -r requirements.txt
   ```
4. Review the main `README.md` for more documentation
5. Open an issue on the project repository

## Related Files

- `backend/run_migrations.py` - Migration helper script
- `backend/.env.template` - Environment configuration template
- `backend/alembic.ini` - Alembic configuration
- `backend/app/alembic/env.py` - Alembic environment setup
- `backend/app/alembic/versions/pg_d8e9f0g1h2i3_create_tenants_pg.py` - Tenants table migration
