# SQLite Setup Guide

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

**Linux/Mac:**
```bash
cd backend
chmod +x setup_sqlite.sh
./setup_sqlite.sh
```

**Windows:**
```bash
cd backend
setup_sqlite.bat
```

### Option 2: Manual Setup

```bash
cd backend

# 1. Create .env
cp .env.example .env
# Edit .env and set SECRET_KEY

# 2. Delete old database (if exists)
rm app.db  # Linux/Mac
del app.db  # Windows

# 3. Run migrations
alembic upgrade head

# 4. Seed data
python -m app.seeds.seed_org
python -m app.seeds.seed_users
python -m app.seeds.seed_metadata

# 5. Start server
uvicorn app.main:app --reload
```

## 🐛 Fixing the "NotImplementedError: No support for ALTER" Error

This error occurs because SQLite has limited ALTER TABLE support. Here's how to fix it:

### Solution 1: Use the Updated Migration

The new migration file `001_create_all_tables_sqlite.py` uses batch mode which is SQLite-compatible.

**Steps:**
1. Delete the database:
   ```bash
   rm app.db
   ```

2. The updated `alembic/env.py` now has `render_as_batch=True` which enables SQLite compatibility.

3. Run migrations:
   ```bash
   alembic upgrade head
   ```

### Solution 2: If You're Stuck Mid-Migration

```bash
# 1. Delete the database completely
rm app.db

# 2. Delete migration history table (if it exists)
rm -rf __pycache__

# 3. Start fresh
alembic upgrade head
python -m app.seeds.seed_org
python -m app.seeds.seed_users
python -m app.seeds.seed_metadata
```

### Solution 3: Check Your alembic/env.py

Make sure it has this line:
```python
context.configure(
    connection=connection,
    target_metadata=target_metadata,
    render_as_batch=True  # ← This is crucial for SQLite
)
```

## 📋 Verification

After setup, verify tables were created:

```bash
# If you have sqlite3 installed
sqlite3 app.db ".tables"
```

You should see:
```
alembic_version    companies         entity_metadata    user_settings
audit_logs         departments       tenant_settings    users
branches
```

Or check table count:
```bash
sqlite3 app.db "SELECT COUNT(*) FROM sqlite_master WHERE type='table';"
```

Should return: 9 (including alembic_version)

## 🔍 Common Issues

### Issue 1: "NotImplementedError: No support for ALTER"

**Cause**: Old migration files don't use batch mode  
**Solution**: Delete `app.db` and run the new migration

```bash
rm app.db
alembic upgrade head
```

### Issue 2: "Target database is not up to date"

**Cause**: Database partially migrated  
**Solution**: Reset completely

```bash
rm app.db
alembic upgrade head
```

### Issue 3: "Table already exists"

**Cause**: Old tables from previous attempt  
**Solution**: Fresh start

```bash
rm app.db
alembic upgrade head
```

### Issue 4: "No module named 'app'"

**Cause**: Wrong directory or Python path issue  
**Solution**: Make sure you're in backend/

```bash
cd backend
python -m app.seeds.seed_org
```

### Issue 5: Database locked

**Cause**: Backend server is still running  
**Solution**: Stop the server first

```bash
# Stop the server (Ctrl+C)
# Then delete and recreate
rm app.db
alembic upgrade head
```

## 📊 Database Location

SQLite database file: `backend/app.db`

This file contains all your data. To backup:
```bash
cp app.db app.db.backup
```

To restore:
```bash
cp app.db.backup app.db
```

## 🔧 Advanced: Inspecting the Database

### View all tables:
```bash
sqlite3 app.db ".tables"
```

### View table schema:
```bash
sqlite3 app.db ".schema companies"
```

### Query data:
```bash
sqlite3 app.db "SELECT * FROM users;"
```

### Count records:
```bash
sqlite3 app.db "SELECT COUNT(*) FROM companies;"
```

### Exit sqlite3:
```bash
.quit
```

## 🎯 Testing Your Setup

### 1. Test Health Endpoint
```bash
curl http://localhost:8000/api/healthz
# Should return: {"status":"ok"}
```

### 2. Test Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}'
# Should return access_token and refresh_token
```

### 3. Test Companies List
```bash
TOKEN="your_token_here"
curl http://localhost:8000/api/org/companies \
  -H "Authorization: Bearer $TOKEN"
# Should return companies array
```

### 4. Run Automated Tests
```bash
cd backend
./test_api.sh
./test_api_option_b.sh
```

## 🚀 Starting the Application

### Backend
```bash
cd backend
uvicorn app.main:app --reload
```

Access at: http://localhost:8000/docs

### Frontend
```bash
cd frontend
python -m http.server 8080
```

Access at: http://localhost:8080

### Login Credentials
- **Admin**: admin@example.com / admin123
- **User**: user@example.com / user123
- **Viewer**: viewer@example.com / viewer123

## 📦 What Gets Created

After successful setup:

```
backend/
├── app.db                 ← SQLite database file
├── .env                   ← Your configuration
└── alembic/
    └── versions/
        └── 001_*.py       ← Applied migration
```

**Database Contents:**
- 2 companies
- 2 branches
- 3 departments
- 3 users
- 3 entity metadata records
- 0 audit logs (will be created on operations)
- User/tenant settings (created on demand)

## 🔄 Resetting Everything

If you want to start completely fresh:

```bash
cd backend

# Delete database
rm app.db

# Delete Python cache
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null

# Run setup again
./setup_sqlite.sh  # or setup_sqlite.bat on Windows
```

## ✅ Success Criteria

Your setup is successful when:

- [ ] `app.db` file exists
- [ ] `alembic upgrade head` completes without errors
- [ ] All 3 seed scripts complete successfully
- [ ] Backend starts: `uvicorn app.main:app --reload`
- [ ] Can access: http://localhost:8000/docs
- [ ] Can login with test credentials
- [ ] Test scripts pass: `./test_api.sh`

## 🎊 You're Ready!

Once everything is set up:

1. **Backend running**: http://localhost:8000
2. **Frontend running**: http://localhost:8080
3. **Can login**: admin@example.com / admin123
4. **All tests pass**: Green checkmarks ✅

Your NoCode platform is ready to use! 🚀

## 🆘 Still Having Issues?

1. Check you're in the correct directory (`backend/`)
2. Verify Python version: `python --version` (should be 3.8+)
3. Verify all dependencies installed: `pip list`
4. Check `.env` file has `SECRET_KEY` set
5. Make sure no other process is using port 8000
6. Check for typos in commands

If all else fails, start completely fresh:
```bash
# Delete everything
rm -rf backend/app.db backend/__pycache__ backend/app/__pycache__

# Reinstall
cd backend
pip install -r requirements.txt

# Run setup script
./setup_sqlite.sh
```