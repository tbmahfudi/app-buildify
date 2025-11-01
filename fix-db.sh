#!/bin/bash
# Quick database migration fix script
# This script helps fix the "relation 'tenants' does not exist" error

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Database Migration Fix Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Navigate to backend directory
cd "$(dirname "$0")/backend"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file not found${NC}"
    echo ""
    echo "Would you like to create one now? (y/n)"
    read -r response

    if [ "$response" = "y" ]; then
        if [ -f ".env.template" ]; then
            cp .env.template .env
            echo -e "${GREEN}✓ Created .env from template${NC}"
            echo ""
            echo -e "${YELLOW}Please edit backend/.env and set your SQLALCHEMY_DATABASE_URL${NC}"
            echo ""
            echo "Examples:"
            echo "  PostgreSQL: SQLALCHEMY_DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/dbname"
            echo "  MySQL:      SQLALCHEMY_DATABASE_URL=mysql+pymysql://user:pass@localhost:3306/dbname"
            echo "  SQLite:     SQLALCHEMY_DATABASE_URL=sqlite:///./app.db"
            echo ""
            echo "Press Enter when ready to continue..."
            read -r
        else
            echo -e "${RED}✗ .env.template not found${NC}"
            exit 1
        fi
    else
        echo -e "${YELLOW}Please create a .env file with your database configuration${NC}"
        exit 1
    fi
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python 3 found${NC}"

# Check if required packages are installed
echo ""
echo "Checking required packages..."

if ! python3 -c "import alembic" 2>/dev/null; then
    echo -e "${YELLOW}Installing required packages...${NC}"
    pip install -q alembic sqlalchemy psycopg2-binary python-dotenv pydantic pydantic-settings pymysql
    echo -e "${GREEN}✓ Packages installed${NC}"
else
    echo -e "${GREEN}✓ Required packages already installed${NC}"
fi

# Run migrations
echo ""
echo -e "${BLUE}Running database migrations...${NC}"
echo ""

if [ -f "run_migrations.py" ]; then
    python3 run_migrations.py "$@"
else
    echo -e "${RED}✗ run_migrations.py not found${NC}"
    echo "Falling back to direct alembic command..."
    alembic upgrade heads
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Migration fix completed!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "The tenants table should now exist in your database."
echo ""
echo "Next steps:"
echo "1. Start your application"
echo "2. If using Docker: ./manage.sh start"
echo "3. If running locally: cd backend && uvicorn app.main:app --reload"
echo ""
