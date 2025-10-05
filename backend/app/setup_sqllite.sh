#!/bin/bash

# SQLite Setup Script for NoCode Platform
# This script sets up the database and seeds data for SQLite

set -e  # Exit on error

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}SQLite Setup for NoCode Platform${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Check if app.db exists
if [ -f "app.db" ]; then
    echo -e "${BLUE}Existing database found.${NC}"
    read -p "Do you want to delete it and start fresh? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}Removing old database...${NC}"
        rm app.db
        echo -e "${GREEN}✓ Database removed${NC}"
    else
        echo -e "${BLUE}Keeping existing database.${NC}"
        echo -e "${BLUE}Note: Migrations may fail if already applied.${NC}"
    fi
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${BLUE}Creating .env file...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ .env created${NC}"
    echo -e "${RED}⚠ WARNING: Please set SECRET_KEY in .env before running!${NC}"
    echo -e "Generate one with: openssl rand -hex 32"
    echo ""
    exit 1
fi

# Run migrations
echo -e "${BLUE}Running database migrations...${NC}"
alembic upgrade head

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Migrations completed${NC}"
else
    echo -e "${RED}✗ Migrations failed${NC}"
    echo ""
    echo "Common issues:"
    echo "1. Database already migrated - try deleting app.db and running again"
    echo "2. alembic not installed - run: pip install alembic"
    echo "3. Wrong directory - make sure you're in backend/"
    exit 1
fi

# Seed organizations
echo ""
echo -e "${BLUE}Seeding organizations...${NC}"
python -m app.seeds.seed_org

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Organizations seeded${NC}"
else
    echo -e "${RED}✗ Organization seeding failed${NC}"
    exit 1
fi

# Seed users
echo ""
echo -e "${BLUE}Seeding users...${NC}"
python -m app.seeds.seed_users

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Users seeded${NC}"
else
    echo -e "${RED}✗ User seeding failed${NC}"
    exit 1
fi

# Seed metadata
echo ""
echo -e "${BLUE}Seeding metadata...${NC}"
python -m app.seeds.seed_metadata

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Metadata seeded${NC}"
else
    echo -e "${RED}✗ Metadata seeding failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}✓ Setup Complete!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "Next steps:"
echo "1. Start the backend:"
echo "   uvicorn app.main:app --reload"
echo ""
echo "2. Access API docs:"
echo "   http://localhost:8000/docs"
echo ""
echo "3. Test credentials:"
echo "   admin@example.com / admin123"
echo "   user@example.com / user123"
echo "   viewer@example.com / viewer123"
echo ""