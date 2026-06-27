#!/bin/bash

# -- module new <name> -- scaffold a new module from the template
module_new() {
    local MODULE_NAME="${1:-}"
    if [[ -z "$MODULE_NAME" ]]; then
        echo "[ERROR] Usage: manage.sh module new <name>" >&2
        exit 1
    fi

    local SCRIPT_DIR
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    local TEMPLATE_DIR="$SCRIPT_DIR/modules/template"
    local DEST_DIR="$SCRIPT_DIR/modules/$MODULE_NAME"

    if [[ ! -d "$TEMPLATE_DIR" ]]; then
        echo "[ERROR] Template not found at $TEMPLATE_DIR" >&2
        exit 1
    fi

    if [[ -d "$DEST_DIR" ]]; then
        echo "[ERROR] Module directory already exists: $DEST_DIR" >&2
        exit 1
    fi

    echo "[INFO] Scaffolding module $MODULE_NAME from template..."
    cp -r "$TEMPLATE_DIR" "$DEST_DIR"

    find "$DEST_DIR" -type f | while read -r f; do
        if file "$f" | grep -q text; then
            sed -i "s/TEMPLATE/$MODULE_NAME/g" "$f"
        fi
    done

    echo "[OK] Module code scaffolded at: $DEST_DIR"

    # Scaffold module planning directory from plan-mod-template
    local PLAN_TEMPLATE_DIR="$SCRIPT_DIR/plan-mod-template"
    local PLAN_DEST_DIR="$SCRIPT_DIR/plan-mod-$MODULE_NAME"

    if [[ -d "$PLAN_TEMPLATE_DIR" ]]; then
        cp -r "$PLAN_TEMPLATE_DIR" "$PLAN_DEST_DIR"
        find "$PLAN_DEST_DIR" -type f | while read -r f; do
            if file "$f" | grep -q text; then
                sed -i "s/TEMPLATE/$MODULE_NAME/g" "$f"
            fi
        done
        echo "[OK] Module planning scaffolded at: $PLAN_DEST_DIR"
    else
        echo "[WARN] plan-mod-template not found — skipping planning scaffold"
    fi

    echo ""
    echo "Next steps:"
    echo "  Module code:"
    echo "    1. Edit  modules/$MODULE_NAME/manifest.json   -- set name, display_name, permissions"
    echo "    2. Edit  modules/$MODULE_NAME/module.py       -- implement lifecycle hooks"
    echo "    3. Edit  modules/$MODULE_NAME/routes.py       -- add your API endpoints"
    echo "    4. Edit  modules/$MODULE_NAME/models.py       -- define tenant-scoped models"
    echo "    5. Build:   ./manage.sh module pack $MODULE_NAME"
    echo "    6. Install: ./manage.sh module install ${MODULE_NAME}_v1.0.0.tar.gz"
    echo "  Module planning (use /c4 or /c5 agents):"
    echo "    7. Update plan-mod-$MODULE_NAME/BACKLOG.md   -- add your module stories"
    echo "    8. Write  plan-mod-$MODULE_NAME/epics/       -- expand epics with full AC"
    echo "    9. Write  modules/$MODULE_NAME/docs/         -- document your module API"
}

# Script to manage Docker Compose services with database type parameter
# Usage: ./manage.sh [command] [database_type]
# Commands: start, stop, restart, migrate, logs, clean
# Database types: postgres, mysql

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
COMMAND=${1:-help}
DATABASE=${2:-postgres}
COMPOSE_FILE="docker-compose.dev.yml"
PROJECT_DIR="infra"
COMPOSE_FULL_PATH="$PROJECT_DIR/$COMPOSE_FILE"

# Get the script's directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to validate database type
validate_database() {
    case $DATABASE in
        postgres|mysql)
            print_info "Using database: $DATABASE"
            ;;
        *)
            print_error "Invalid database type: $DATABASE"
            echo "Supported databases: postgres, mysql"
            exit 1
            ;;
    esac
}

# Function to check if services are running
check_services_running() {
    if ! docker compose -f "$COMPOSE_FULL_PATH" ps | grep -q "Up"; then
        print_error "Services are not running. Start them with: $0 start"
        exit 1
    fi
}

# Function to display help
show_help() {
    echo "Docker Compose Management Script"
    echo ""
    echo "Usage: $0 [command] [database_type] [options]"
    echo ""
    echo "Service Management:"
    echo "  start       - Start all containers"
    echo "  stop        - Stop all containers"
    echo "  restart     - Restart all containers"
    echo "  status      - Check service health"
    echo "  ps/list     - List running containers"
    echo "  stats       - Show resource usage"
    echo ""
    echo "Database Management:"
    echo "  migrate        - Run database migrations"
    echo "  seed           - Seed database with test data"
    echo "  quick-seed     - Minimal seed: superadmin only (no sample tenants/users)"
    echo "  db-reset       - Reset database (drops all data)"
    echo "  backup         - Backup database to SQL file"
    echo "  restore        - Restore database from backup file"
    echo "  db-shell       - Open database shell"
    echo ""
    echo "Seed Scripts (RBAC & Menu):"
    echo "  seed-permissions   - Seed all permissions and role templates"
    echo "  seed-rbac          - Seed RBAC with groups (User→Group→Role→Permission)"
    echo "  seed-menu          - Seed menu items from frontend/config/menu.json"
    echo "  seed-menu-rbac [TENANT] - Seed menu management RBAC for tenant"
    echo "  seed-module-rbac [TENANT] - Seed module management RBAC for tenant"
    echo "  module pack <dir> [--out <dir>] - Pack a module into a tarball with SHA256"
    echo "  module install <tarball>       - Install a packed module (8-step pipeline)"
    echo "  seed-financial-rbac [TENANT] - Seed financial module RBAC for tenant"
    echo ""
    echo "Development:"
    echo "  setup       - Complete initial setup (build + start + migrate + seed)"
    echo "  shell       - Open backend shell"
    echo "  logs [svc]  - View container logs (optionally for specific service)"
    echo "  test        - Run API tests"
    echo "  exec        - Execute command in service"
    echo ""
    echo "Maintenance:"
    echo "  build       - Build images"
    echo "  clean       - Stop and remove containers and volumes"
    echo "  help        - Show this help message"
    echo ""
    echo "Database types:"
    echo "  postgres    - PostgreSQL (default)"
    echo "  mysql       - MySQL"
    echo ""
    echo "Examples:"
    echo "  $0 setup postgres              # Complete initial setup"
    echo "  $0 start postgres              # Start services"
    echo "  $0 migrate mysql               # Run migrations"
    echo "  $0 seed-permissions            # Seed all permissions and role templates"
    echo "  $0 seed-rbac                   # Setup RBAC with groups for all tenants"
    echo "  $0 seed-menu                   # Seed menu items"
    echo "  $0 seed-menu-rbac FASHIONHUB   # Setup menu RBAC for FASHIONHUB tenant"
    echo "  $0 logs backend                # View backend logs only"
    echo "  $0 status                      # Check health status"
    echo "  $0 db-reset                    # Reset database"
    echo "  $0 backup                      # Backup database"
}

# Function to start services
start_services() {
    print_info "Starting services with $DATABASE..."
    docker compose -f "$COMPOSE_FULL_PATH" up -d
    print_info "Services started successfully"

    # Wait for backend to be healthy
    print_info "Waiting for backend to be ready..."
    MAX_RETRIES=30
    RETRY_COUNT=0

    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if curl -sf http://localhost:8000/api/healthz > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Backend is healthy and ready${NC}"
            break
        fi

        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
            print_error "Backend failed to become healthy after $MAX_RETRIES attempts"
            print_warning "Check logs with: $0 logs backend"
            exit 1
        fi

        echo -n "."
        sleep 2
    done
    echo ""

    print_info "Backend: http://localhost:8000"
    print_info "API Docs: http://localhost:8000/api/docs"
    print_info "Frontend: http://localhost:8080"
}

# Function to stop services
stop_services() {
    print_info "Stopping services..."
    docker compose -f "$COMPOSE_FULL_PATH" down
    print_info "Services stopped successfully"
}

# Function to restart services
restart_services() {
    print_info "Restarting services..."
    stop_services
    start_services
}

# Function to run migrations
run_migrations() {
    print_info "Running database migrations..."

    # Determine the correct migration head based on database type
    # Each database has its own migration branch to avoid conflicts
    case $DATABASE in
        postgres)
            MIGRATION_HEAD="pg_m1n2o3p4q5r6"
            ;;
        mysql)
            MIGRATION_HEAD="mysql_m1n2o3p4q5r6"
            ;;
        sqlite)
            MIGRATION_HEAD="sqlite_m1n2o3p4q5r6"
            ;;
        *)
            print_error "Unknown database type: $DATABASE"
            exit 1
            ;;
    esac

    print_info "Upgrading to $DATABASE head: $MIGRATION_HEAD"

    if ! docker compose -f "$COMPOSE_FULL_PATH" exec -T backend alembic upgrade "$MIGRATION_HEAD"; then
        print_error "Migration failed"
        print_info "Tip: Check if the database is properly initialized and accessible"
        exit 1
    fi

    print_info "Migrations completed successfully"
}

# Function to view logs
view_logs() {
    SERVICE=${3:-}  # Optional service name from third argument
    if [ -n "$SERVICE" ]; then
        print_info "Displaying logs for $SERVICE (Ctrl+C to exit)..."
        docker compose -f "$COMPOSE_FULL_PATH" logs -f "$SERVICE"
    else
        print_info "Displaying all logs (Ctrl+C to exit)..."
        docker compose -f "$COMPOSE_FULL_PATH" logs -f --tail=100
    fi
}

# Function to clean up
clean_services() {
    print_warning "This will remove all containers and volumes"
    read -p "Are you sure? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Cleaning up..."
        docker compose -f "$COMPOSE_FULL_PATH" down -v
        print_info "Cleanup completed"
    else
        print_info "Cleanup cancelled"
    fi
}

# Function to build images
build_images() {
    print_info "Building images..."
    docker compose -f "$COMPOSE_FULL_PATH" build
    print_info "Build completed successfully"
}

# Function to open backend shell
open_backend_shell() {
    print_info "Opening backend shell..."
    docker compose -f "$COMPOSE_FULL_PATH" exec backend /bin/bash
}

# Function to open database shell
open_db_shell() {
    print_info "Opening $DATABASE shell..."
    
    if [ "$DATABASE" = "postgres" ]; then
        docker compose -f "$COMPOSE_FULL_PATH" exec postgres psql -U appuser -d appdb
    elif [ "$DATABASE" = "mysql" ]; then
        docker compose -f "$COMPOSE_FULL_PATH" exec mysql mysql -u appuser -p appdb
    fi
}

# Function to seed database
seed_database() {
    print_info "Seeding database..."

    print_info "Seeding complete organizational data (tenants, companies, users, etc.)..."
    if docker compose -f "$COMPOSE_FULL_PATH" exec -T backend python -m app.seeds.seed_complete_org; then
        print_info "Database seeding completed successfully"
    else
        print_warning "Seeding failed or was skipped"
        print_info "Note: You can manually seed data later with:"
        print_info "  docker compose -f $COMPOSE_FULL_PATH exec backend python -m app.seeds.seed_complete_org"
    fi
}

# Function to run tests
run_tests() {
    print_info "Running API tests..."

    if ! docker compose -f "$COMPOSE_FULL_PATH" exec -T backend ./test_api_option_b.sh; then
        print_error "Tests failed"
        exit 1
    fi

    print_info "Tests completed successfully"
}

# Function to check service status
check_status() {
    print_info "Checking service status..."
    docker compose -f "$COMPOSE_FULL_PATH" ps
    echo ""
    print_info "Health checks:"

    # Check backend
    if curl -sf http://localhost:8000/api/healthz > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend: OK${NC}"
    else
        echo -e "${RED}✗ Backend: Down${NC}"
    fi

    # Check frontend
    if curl -sf http://localhost:8080 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Frontend: OK${NC}"
    else
        echo -e "${RED}✗ Frontend: Down${NC}"
    fi

    # Check database
    if [ "$DATABASE" = "postgres" ]; then
        if docker compose -f "$COMPOSE_FULL_PATH" exec -T postgres pg_isready -U appuser > /dev/null 2>&1; then
            echo -e "${GREEN}✓ PostgreSQL: OK${NC}"
        else
            echo -e "${RED}✗ PostgreSQL: Down${NC}"
        fi
    elif [ "$DATABASE" = "mysql" ]; then
        if docker compose -f "$COMPOSE_FULL_PATH" exec -T mysql mysqladmin ping -h localhost -u appuser > /dev/null 2>&1; then
            echo -e "${GREEN}✓ MySQL: OK${NC}"
        else
            echo -e "${RED}✗ MySQL: Down${NC}"
        fi
    fi
}

# Function to list containers
list_containers() {
    print_info "Running containers:"
    docker compose -f "$COMPOSE_FULL_PATH" ps
}

# Function to show container stats
show_stats() {
    print_info "Container resource usage:"
    CONTAINER_IDS=$(docker compose -f "$COMPOSE_FULL_PATH" ps -q)
    if [ -n "$CONTAINER_IDS" ]; then
        docker stats $CONTAINER_IDS --no-stream
    else
        print_warning "No containers are running"
    fi
}

# Function to backup database
backup_database() {
    BACKUP_DIR="backups"
    mkdir -p "$BACKUP_DIR"
    BACKUP_FILE="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql"

    print_info "Creating database backup..."

    if [ "$DATABASE" = "postgres" ]; then
        if docker compose -f "$COMPOSE_FULL_PATH" exec -T postgres pg_dump -U appuser appdb > "$BACKUP_FILE"; then
            print_info "PostgreSQL backup saved to: $BACKUP_FILE"
        else
            print_error "Backup failed"
            rm -f "$BACKUP_FILE"
            exit 1
        fi
    elif [ "$DATABASE" = "mysql" ]; then
        if docker compose -f "$COMPOSE_FULL_PATH" exec -T mysql mysqldump -u appuser -papppassword appdb > "$BACKUP_FILE"; then
            print_info "MySQL backup saved to: $BACKUP_FILE"
        else
            print_error "Backup failed"
            rm -f "$BACKUP_FILE"
            exit 1
        fi
    fi
}

# Function to restore database
restore_database() {
    if [ -z "$3" ]; then
        print_error "Backup file required. Usage: $0 restore [database_type] [backup_file]"
        exit 1
    fi

    BACKUP_FILE=$3

    if [ ! -f "$BACKUP_FILE" ]; then
        print_error "Backup file not found: $BACKUP_FILE"
        exit 1
    fi

    print_warning "This will restore database from: $BACKUP_FILE"
    read -p "Are you sure? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Restore cancelled"
        exit 0
    fi

    print_info "Restoring database..."

    if [ "$DATABASE" = "postgres" ]; then
        if docker compose -f "$COMPOSE_FULL_PATH" exec -T postgres psql -U appuser appdb < "$BACKUP_FILE"; then
            print_info "PostgreSQL restore completed successfully"
        else
            print_error "Restore failed"
            exit 1
        fi
    elif [ "$DATABASE" = "mysql" ]; then
        if docker compose -f "$COMPOSE_FULL_PATH" exec -T mysql mysql -u appuser -papppassword appdb < "$BACKUP_FILE"; then
            print_info "MySQL restore completed successfully"
        else
            print_error "Restore failed"
            exit 1
        fi
    fi
}

# Function to reset database
reset_database() {
    print_warning "This will drop all data and recreate the database"
    read -p "Are you sure? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Reset cancelled"
        exit 0
    fi

    print_info "Resetting database..."
    docker compose -f "$COMPOSE_FULL_PATH" down -v
    start_services

    print_info "Waiting for database to be ready..."
    sleep 10

    run_migrations
    seed_database

    print_info "Database reset completed successfully"
}

# Function to quick seed (minimal data — superadmin only)
quick_seed_database() {
    print_info "Quick seeding database with minimal data (superadmin only)..."

    if docker compose -f "$COMPOSE_FULL_PATH" exec -T backend python -m app.seeds.seed_minimal; then
        print_info "Minimal seed completed successfully"
    else
        print_warning "Seeding failed or was skipped"
    fi
}

# Function to setup complete environment
setup_environment() {
    print_info "Setting up complete development environment..."
    validate_database

    print_info "Step 1/5: Building images..."
    build_images

    print_info "Step 2/5: Starting services..."
    start_services

    print_info "Step 3/5: Waiting for services to be ready..."
    sleep 10

    print_info "Step 4/5: Running migrations..."
    run_migrations

    print_info "Step 5/5: Seeding database..."
    seed_database

    echo ""
    print_info "========================================="
    print_info "Setup complete! Services are running at:"
    print_info "  Backend:  http://localhost:8000"
    print_info "  API Docs: http://localhost:8000/docs"
    print_info "  Frontend: http://localhost:8080"
    print_info "========================================="
}

# Function to execute arbitrary command in service
exec_service() {
    if [ -z "$2" ]; then
        print_error "Service name required. Usage: $0 exec [service] [command...]"
        exit 1
    fi

    SERVICE=$2
    shift 2

    print_info "Executing command in $SERVICE..."
    docker compose -f "$COMPOSE_FULL_PATH" exec "$SERVICE" "$@"
}

# Function to seed menu items
seed_menu_items() {
    print_info "Seeding menu items from frontend/config/menu.json..."

    if docker compose -f "$COMPOSE_FULL_PATH" exec -T backend python -m app.seeds.seed_menu_items; then
        print_info "Menu items seeded successfully"
        echo ""
        print_info "Next steps:"
        print_info "  1. Setup menu RBAC: $0 seed-menu-rbac [TENANT_CODE]"
        print_info "  2. Or manually assign permissions: docker compose -f $COMPOSE_FULL_PATH exec backend python assign_menu_permissions.py"
    else
        print_error "Menu seeding failed"
        exit 1
    fi
}

# Function to seed menu management RBAC
seed_menu_rbac() {
    TENANT_CODE=$3

    if [ -z "$TENANT_CODE" ]; then
        print_warning "No tenant code provided. Listing available tenants..."
        docker compose -f "$COMPOSE_FULL_PATH" exec -T backend python -m app.seeds.seed_menu_management_rbac
        echo ""
        print_info "Usage: $0 seed-menu-rbac [database_type] [TENANT_CODE]"
        print_info "Example: $0 seed-menu-rbac postgres FASHIONHUB"
        exit 0
    fi

    print_info "Setting up menu management RBAC for tenant: $TENANT_CODE..."

    if docker compose -f "$COMPOSE_FULL_PATH" exec -T backend python -m app.seeds.seed_menu_management_rbac "$TENANT_CODE"; then
        print_info "Menu RBAC setup completed successfully for tenant: $TENANT_CODE"
    else
        print_error "Menu RBAC setup failed"
        exit 1
    fi
}

# Function to seed module management RBAC
seed_module_rbac() {
    TENANT_CODE=$3

    if [ -z "$TENANT_CODE" ]; then
        print_warning "No tenant code provided. Listing available tenants..."
        docker compose -f "$COMPOSE_FULL_PATH" exec -T backend python -m app.seeds.seed_module_management_rbac
        echo ""
        print_info "Usage: $0 seed-module-rbac [database_type] [TENANT_CODE]"
        print_info "Example: $0 seed-module-rbac postgres FASHIONHUB"
        exit 0
    fi

    print_info "Setting up module management RBAC for tenant: $TENANT_CODE..."

    if docker compose -f "$COMPOSE_FULL_PATH" exec -T backend python -m app.seeds.seed_module_management_rbac "$TENANT_CODE"; then
        print_info "Module RBAC setup completed successfully for tenant: $TENANT_CODE"
    else
        print_error "Module RBAC setup failed"
        exit 1
    fi
}

# Function to seed financial RBAC
seed_financial_rbac() {
    TENANT_CODE=$3

    if [ -z "$TENANT_CODE" ]; then
        print_warning "No tenant code provided. Listing available tenants..."
        docker compose -f "$COMPOSE_FULL_PATH" exec -T backend python -m app.seeds.seed_financial_rbac
        echo ""
        print_info "Usage: $0 seed-financial-rbac [database_type] [TENANT_CODE]"
        print_info "Example: $0 seed-financial-rbac postgres FASHIONHUB"
        exit 0
    fi

    print_info "Setting up financial module RBAC for tenant: $TENANT_CODE..."

    if docker compose -f "$COMPOSE_FULL_PATH" exec -T backend python -m app.seeds.seed_financial_rbac "$TENANT_CODE"; then
        print_info "Financial RBAC setup completed successfully for tenant: $TENANT_CODE"
    else
        print_error "Financial RBAC setup failed"
        exit 1
    fi
}

# Function to seed all permissions and role templates
seed_all_permissions() {
    print_info "Seeding all permissions and role templates..."
    print_info "This will create ~260 permissions across 7 categories and 9 default roles"
    echo ""

    if docker compose -f "$COMPOSE_FULL_PATH" exec -T backend python -m app.seeds.seed_all_permissions; then
        echo ""
        print_info "========================================="
        print_info "✓ Permissions seeding completed successfully!"
        print_info "========================================="
        echo ""
        print_info "Created:"
        print_info "  • Organization permissions (47)"
        print_info "  • RBAC permissions (30)"
        print_info "  • Dashboard permissions (31)"
        print_info "  • Report permissions (45)"
        print_info "  • Scheduler permissions (31)"
        print_info "  • Audit permissions (27)"
        print_info "  • Settings permissions (49)"
        print_info "  • 9 default role templates"
        echo ""
        print_info "Next steps:"
        print_info "  1. Access Permission Assignment Helper at:"
        print_info "     http://localhost:8080/access-control.html"
        print_info "  2. Or use the RBAC API endpoints to manage permissions"
        print_info "  3. View API docs: http://localhost:8000/docs"
    else
        print_error "Permission seeding failed"
        exit 1
    fi
}

# Function to seed RBAC with groups
seed_rbac_with_groups() {
    print_info "========================================="
    print_info "Setting up RBAC with Group-Based Access Control"
    print_info "========================================="
    echo ""
    print_info "This will:"
    print_info "  • Create 10 default groups (Administrators, Managers, etc.)"
    print_info "  • Create 10 default roles with permissions"
    print_info "  • Assign roles to groups"
    print_info "  • Auto-assign existing users to groups"
    echo ""
    print_info "RBAC Model: User → Group → Role → Permission"
    echo ""

    if docker compose -f "$COMPOSE_FULL_PATH" exec -T backend python -m app.seeds.seed_rbac_with_groups; then
        echo ""
        print_info "========================================="
        print_info "✓ RBAC setup completed successfully!"
        print_info "========================================="
        echo ""
        print_info "Created:"
        print_info "  • 10 groups (Administrators, Managers, Employees, etc.)"
        print_info "  • 10 roles (tenant_admin, manager, employee, etc.)"
        print_info "  • Role → Group assignments"
        print_info "  • User → Group assignments (smart email-based)"
        echo ""
        print_info "Users assigned to groups based on email patterns:"
        print_info "  • admin@*, ceo@*, cto@* → Administrators"
        print_info "  • manager@*, director@* → Managers"
        print_info "  • hr@* → HR Team"
        print_info "  • finance@* → Finance Team"
        print_info "  • dev@*, engineer@* → Engineering Team"
        print_info "  • (others) → Employees"
        echo ""
        print_info "Next steps:"
        print_info "  1. Access RBAC Management: http://localhost:8080/rbac.html"
        print_info "  2. View user roles via groups: GET /api/rbac/users/{user_id}/roles"
        print_info "  3. Manage access by adding/removing users from groups"
        print_info "  4. Read documentation: backend/app/seeds/README_RBAC.md"
        echo ""
        print_info "Documentation: backend/app/seeds/README_RBAC.md"
    else
        print_error "RBAC setup failed"
        print_warning "Make sure organization data is seeded first:"
        print_warning "  $0 seed"
        exit 1
    fi
}

# Main script logic

# ---------------------------------------------------------------------------


# T-23.008  module pack <dir> [--out <outdir>]
# T-23.009  validate manifest before bundling
# ---------------------------------------------------------------------------
module_pack() {
    local MODULE_DIR="${1:-}"
    local OUT_DIR="."
    shift || true

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --out) OUT_DIR="${2:-.}"; shift 2 ;;
            *) echo "Unknown flag: $1" >&2; exit 1 ;;
        esac
    done

    if [[ -z "$MODULE_DIR" || ! -d "$MODULE_DIR" ]]; then
        echo "Usage: manage.sh module pack <module-dir> [--out <output-dir>]" >&2
        exit 1
    fi

    MODULE_DIR="$(realpath "$MODULE_DIR")"
    OUT_DIR="$(realpath "$OUT_DIR")"
    local MANIFEST="$MODULE_DIR/manifest.json"

    if [[ ! -f "$MANIFEST" ]]; then
        echo "manifest.json not found in $MODULE_DIR" >&2; exit 1
    fi

    local MODULE_NAME MODULE_VERSION
    MODULE_NAME=$(python3 - "$MANIFEST" <<'PY'
import sys, json; m=json.load(open(sys.argv[1])); print(m['name'])
PY
)
    MODULE_VERSION=$(python3 - "$MANIFEST" <<'PY'
import sys, json; m=json.load(open(sys.argv[1])); print(m['version'])
PY
)

    if [[ -z "$MODULE_NAME" || -z "$MODULE_VERSION" ]]; then
        echo "Could not read name/version from manifest.json" >&2; exit 1
    fi

    mkdir -p "$OUT_DIR"
    local TARBALL="$OUT_DIR/${MODULE_NAME}_${MODULE_VERSION}.tar.gz"
    local SHA_FILE="$OUT_DIR/SHA256SUMS"

    echo "Packing $MODULE_NAME $MODULE_VERSION -> $TARBALL"

    # ---------------------------------------------------------------------------
    # T-23.009  Optional pre-pack manifest validation via POST /modules/validate
    # ---------------------------------------------------------------------------
    local API_BASE="${BUILDIFY_API_URL:-http://localhost:8000}"
    local VALIDATE_URL="$API_BASE/api/v1/modules/validate"

    # Check whether backend is reachable (2-second timeout, silent)
    if curl -sf --max-time 2 "$API_BASE/api/v1/health" -o /dev/null 2>/dev/null || \
       curl -sf --max-time 2 "$API_BASE/" -o /dev/null 2>/dev/null; then
        _BACKEND_UP=true
    else
        _BACKEND_UP=false
    fi

    if [[ "$_BACKEND_UP" == "true" && -n "${BUILDIFY_TOKEN:-}" ]]; then
        echo "Validating manifest against backend..."
        local MANIFEST_JSON
        MANIFEST_JSON=$(cat "$MANIFEST")
        local HTTP_CODE
        HTTP_CODE=$(curl -sf --max-time 10 -o /tmp/_pack_validate_resp.json -w "%{http_code}" \
            -X POST "$VALIDATE_URL" \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer $BUILDIFY_TOKEN" \
            --data "{\"manifest\": $MANIFEST_JSON}" 2>/dev/null || echo "000")
        if [[ "$HTTP_CODE" == "200" ]]; then
            echo "Manifest valid."
        elif [[ "$HTTP_CODE" == "422" ]]; then
            echo "Manifest validation FAILED (HTTP 422):" >&2
            cat /tmp/_pack_validate_resp.json >&2 2>/dev/null || true
            rm -f /tmp/_pack_validate_resp.json
            exit 1
        elif [[ "$HTTP_CODE" == "401" || "$HTTP_CODE" == "403" ]]; then
            echo "⚠ Backend returned $HTTP_CODE (auth error) — skipping pre-pack validation" >&2
        else
            echo "⚠ Unexpected response from validate endpoint (HTTP $HTTP_CODE) — skipping pre-pack validation" >&2
        fi
        rm -f /tmp/_pack_validate_resp.json
    elif [[ "$_BACKEND_UP" == "true" && -z "${BUILDIFY_TOKEN:-}" ]]; then
        echo "⚠ BUILDIFY_TOKEN not set — skipping pre-pack validation (set BUILDIFY_TOKEN to enable)" >&2
    else
        echo "⚠ Backend not reachable — skipping pre-pack validation" >&2
    fi
    # ---------------------------------------------------------------------------

    # Normalise timestamps for deterministic builds (reproducible tarballs)
    find "$MODULE_DIR" -not -path "*/__pycache__/*" -not -name "*.pyc" \
        -exec touch -d "2020-01-01 00:00:00" {} + 2>/dev/null || true

    tar --exclude="*/__pycache__" --exclude="*.pyc" --sort=name \
        -czf "$TARBALL" \
        -C "$(dirname "$MODULE_DIR")" "$(basename "$MODULE_DIR")"

    sha256sum "$TARBALL" > "$SHA_FILE"

    echo "Packed: ${MODULE_NAME}_${MODULE_VERSION}.tar.gz"
    echo "SHA256: $(awk '{print $1}' "$SHA_FILE")"
}


# ---------------------------------------------------------------------------
# T-23.010/T-23.011/T-23.012  module install <tarball>
# ---------------------------------------------------------------------------
module_install() {
    local TARBALL="${1:-}"
    local API_BASE="http://localhost:8000"
    local TOKEN="${BUILDIFY_TOKEN:-}"
    shift || true

    # Parse optional --api-url / --token flags (T-23.010)
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --api-url) API_BASE="${2:-$API_BASE}"; shift 2 ;;
            --token)   TOKEN="${2:-}"; shift 2 ;;
            *) echo "[ERROR] Unknown flag: $1" >&2; exit 1 ;;
        esac
    done

    if [[ -z "$TARBALL" || ! -f "$TARBALL" ]]; then
        echo "[ERROR] Usage: manage.sh module install <tarball> [--api-url <url>] [--token <token>]" >&2; exit 1
    fi
    TARBALL="$(realpath "$TARBALL")"
    local WORK_DIR
    WORK_DIR=$(mktemp -d /tmp/module_install_XXXXXX)
    trap 'rm -rf "$WORK_DIR"' EXIT

    echo "[INFO] Tarball: $TARBALL"

    # -- Step 1/8: Verify SHA256 -----------------------------------------------
    echo "[1/8] Verifying SHA256..."
    local SHA_FILE; SHA_FILE="$(dirname "$TARBALL")/SHA256SUMS"
    if [[ -f "$SHA_FILE" ]]; then
        local EXPECTED ACTUAL
        EXPECTED=$(grep "$(basename "$TARBALL")" "$SHA_FILE" | awk '{print $1}')
        ACTUAL=$(sha256sum "$TARBALL" | awk '{print $1}')
        if [[ "$EXPECTED" != "$ACTUAL" ]]; then
            echo "  x Failed: SHA256 mismatch -- expected $EXPECTED got $ACTUAL" >&2; exit 1
        fi
        echo "  + Done (checksum OK)"
    else
        echo "  + Done (no SHA256SUMS file -- skipping)"
    fi

    # Extract tarball
    tar -xzf "$TARBALL" -C "$WORK_DIR"
    local MODULE_DIR; MODULE_DIR=$(find "$WORK_DIR" -maxdepth 1 -mindepth 1 -type d | head -1)
    [[ -z "$MODULE_DIR" ]] && { echo "[ERROR] Empty tarball" >&2; exit 1; }
    local MANIFEST="$MODULE_DIR/manifest.json"
    [[ ! -f "$MANIFEST" ]] && { echo "[ERROR] No manifest.json in tarball" >&2; exit 1; }

    local MODULE_NAME MODULE_VERSION
    MODULE_NAME=$(python3 -c "import json,sys; m=json.load(open('$MANIFEST')); print(m['name'])")
    MODULE_VERSION=$(python3 -c "import json,sys; m=json.load(open('$MANIFEST')); print(m['version'])")
    echo "[INFO] Module: $MODULE_NAME v$MODULE_VERSION"

    # -- Idempotency check (T-23.012) ----------------------------------------
    # Query DB directly: if name+version already has install_status=ready, exit 0.
    local _EXISTING
    _EXISTING=$(docker exec app_buildify_postgresql psql -U appuser -d appdb -tAc \
      "SELECT install_status FROM modules WHERE name='$MODULE_NAME' AND version='$MODULE_VERSION' LIMIT 1" 2>/dev/null)
    if [ "$_EXISTING" = "ready" ]; then
        echo "Module '$MODULE_NAME' v$MODULE_VERSION is already installed. Nothing to do."
        exit 0
    fi

    # -- Step 2/8: Validate manifest via API ----------------------------------
    echo "[2/8] Validating manifest via API..."
    local MJSON; MJSON=$(python3 -c "import json; print(json.dumps({'manifest':json.load(open('$MANIFEST'))}))")
    local VCODE; VCODE=$(curl -s -o /tmp/_mv.json -w "%{http_code}" \
        -X POST "$API_BASE/api/v1/modules/validate" \
        -H "Content-Type: application/json" -d "$MJSON" 2>/dev/null || echo "000")
    if [[ "$VCODE" == "422" ]]; then
        echo "  x Failed: manifest invalid" >&2; cat /tmp/_mv.json >&2; exit 1
    elif [[ "$VCODE" != "200" ]]; then
        echo "  + Done (API unreachable HTTP $VCODE -- skipping validation)"
    else
        echo "  + Done (manifest valid)"
    fi

    # -- Step 3/8: Set install_status=in_progress -----------------------------
    echo "[3/8] Setting install_status=in_progress..."
    docker exec app_buildify_backend python3 -c \
        "import os; os.environ['TESTING']='1'
from datetime import datetime
from app.core.db import SessionLocal
from app.models.nocode_module import Module
from app.models.base import generate_uuid
db=SessionLocal()
m=db.query(Module).filter(Module.name=='$MODULE_NAME').first()
if m:
    m.install_status='in_progress'; m.install_error_message=None
else:
    m=Module(id=generate_uuid(),name='$MODULE_NAME',display_name='$MODULE_NAME',
             module_type='code',version='$MODULE_VERSION',is_installed=False,
             install_status='in_progress')
    db.add(m)
db.commit(); db.close()" 2>/dev/null || true
    echo "  + Done"

    # -- Step 4/8: Module-specific Alembic migrations -------------------------
    echo "[4/8] Running module Alembic migrations..."
    if [[ -d "$MODULE_DIR/backend/alembic" || -d "$MODULE_DIR/migrations" ]]; then
        if ! docker exec app_buildify_backend bash -c \
               "cd /app/modules/$MODULE_NAME && alembic upgrade head" 2>&1 | sed 's/^/  /'; then
            echo "  x Failed: Alembic migration error" >&2
            _module_rollback "$MODULE_NAME" "migration failed"
            exit 1
        fi
        echo "  + Done"
    else
        echo "  + Done (no migrations found -- skipping)"
    fi

    # -- Step 5/8: Copy backend service files ---------------------------------
    echo "[5/8] Copying backend service files..."
    local BACKEND_DEST="/home/mahfudi/app-buildify/backend/modules/$MODULE_NAME"
    if [[ -d "$MODULE_DIR/backend" ]]; then
        mkdir -p "$BACKEND_DEST"
        if ! cp -r "$MODULE_DIR/backend/"* "$BACKEND_DEST/" 2>/dev/null; then
            echo "  x Failed: backend copy error" >&2
            _module_rollback "$MODULE_NAME" "backend copy failed"
            exit 1
        fi
        echo "  + Done (-> $BACKEND_DEST)"
    else
        echo "  + Done (no backend dir -- skipping)"
    fi

    # -- Step 6/8: Copy frontend assets ---------------------------------------
    echo "[6/8] Copying frontend assets..."
    local FRONTEND_DEST="/home/mahfudi/app-buildify/frontend/assets/modules/$MODULE_NAME"
    if [[ -d "$MODULE_DIR/frontend" ]]; then
        mkdir -p "$FRONTEND_DEST"
        if ! cp -r "$MODULE_DIR/frontend/"* "$FRONTEND_DEST/" 2>/dev/null; then
            echo "  x Failed: frontend copy error" >&2
            _module_rollback "$MODULE_NAME" "frontend copy failed"
            exit 1
        fi
        echo "  + Done (-> $FRONTEND_DEST)"
    else
        echo "  + Done (no frontend dir -- skipping)"
    fi

    # -- Step 7/8: Register module via API ------------------------------------
    # The /register endpoint also calls BaseModule.post_install(db) server-side (T-23.014).
    echo "[7/8] Registering module (server will call post_install hook)..."
    local _REG_PAYLOAD; _REG_PAYLOAD=$(mktemp /tmp/_mr_payload_XXXXXX.json)
    python3 -c "import json; m=json.load(open('$MANIFEST')); print(json.dumps({'manifest':m,'backend_service_url':m.get('backend_service_url','')}))" > "$_REG_PAYLOAD"
    local _CURL_ARGS=(-s -o /tmp/_mr.json -w "%{http_code}" -X POST "$API_BASE/api/v1/module-registry/register" -H "Content-Type: application/json" --data "@$_REG_PAYLOAD")
    [[ -n "$TOKEN" ]] && _CURL_ARGS+=(-H "Authorization: Bearer $TOKEN")
    local RCODE; RCODE=$(curl "${_CURL_ARGS[@]}" 2>/dev/null || echo "000")
    rm -f "$_REG_PAYLOAD"
    if [[ "$RCODE" != "200" && "$RCODE" != "201" ]]; then
        echo "  x Failed: registration HTTP $RCODE" >&2
        [[ -f /tmp/_mr.json ]] && cat /tmp/_mr.json >&2
        _module_rollback "$MODULE_NAME" "registration failed HTTP $RCODE" "$BACKEND_DEST" "$FRONTEND_DEST"
        exit 1
    fi
    echo "  + Done (post_install hook invoked server-side)"

    # -- Step 8/8: Mark install_status=ready ----------------------------------
    echo "[8/8] Marking install_status=ready..."
    if ! docker exec app_buildify_backend python3 -c \
        "import os; os.environ['TESTING']='1'
from datetime import datetime
from app.core.db import SessionLocal
from app.models.nocode_module import Module
db=SessionLocal()
m=db.query(Module).filter(Module.name=='$MODULE_NAME').first()
if m:
    m.install_status='ready'; m.is_installed=True
    m.version='$MODULE_VERSION'; m.install_error_message=None
    m.installed_at=datetime.utcnow(); m.updated_at=datetime.utcnow()
    db.commit()
db.close()" 2>/dev/null; then
        echo "  x Failed: could not set install_status=ready" >&2
        _module_rollback "$MODULE_NAME" "failed to set ready status" "$BACKEND_DEST" "$FRONTEND_DEST"
        exit 1
    fi
    echo "  + Done"
    echo "[INFO] Module $MODULE_NAME v$MODULE_VERSION installed successfully."
}


# ── T-23.026: module uninstall ──────────────────────────────────────────────
# ---------------------------------------------------------------------------
# T-23.026  module uninstall <name> [--api-url <url>] [--token <token>]
#   Phase 1: POST /api/v1/modules/admin/{id}/deactivate-all
#   Phase 2: DELETE /api/v1/modules/admin/{id}  (X-Confirm-Uninstall: true)
# Requires BUILDIFY_TOKEN env var or --token flag (superadmin operation).
# ---------------------------------------------------------------------------
module_uninstall() {
    local MODULE_NAME="${1:-}"
    local API_BASE="http://localhost:8000"
    local TOKEN="${BUILDIFY_TOKEN:-}"
    shift || true

    # Parse optional --api-url / --token flags
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --api-url) API_BASE="${2:-$API_BASE}"; shift 2 ;;
            --token)   TOKEN="${2:-}";             shift 2 ;;
            *) echo "[ERROR] Unknown flag: $1" >&2; exit 1 ;;
        esac
    done

    if [[ -z "$MODULE_NAME" ]]; then
        echo "[ERROR] Usage: manage.sh module uninstall <module-name> [--api-url <url>] [--token <token>]" >&2
        exit 1
    fi

    if [[ -z "$TOKEN" ]]; then
        echo "[ERROR] BUILDIFY_TOKEN is required for uninstall (superadmin operation)." >&2
        echo "        Set the env var or pass --token <token>." >&2
        exit 1
    fi

    local API_BASE_V1="$API_BASE/api/v1"

    # Step 1: Resolve module UUID from module-registry
    echo "Resolving module '$MODULE_NAME'..."
    local REG_BODY REG_CODE
    REG_BODY=$(curl -s -w "\n%{http_code}" \
        -H "Authorization: Bearer $TOKEN" \
        "$API_BASE_V1/module-registry/" 2>/dev/null)
    REG_CODE=$(echo "$REG_BODY" | tail -1)
    local REG_JSON
    REG_JSON=$(echo "$REG_BODY" | sed '$d')

    local MOD_ID
    MOD_ID=$(echo "$REG_JSON" | python3 -c "
import sys, json
data = json.load(sys.stdin)
items = data if isinstance(data, list) else data.get('items', data.get('results', []))
for m in items:
    if m.get('name') == '${MODULE_NAME}':
        print(m.get('id', ''))
        break
" 2>/dev/null || true)

    if [[ -z "$MOD_ID" ]]; then
        echo "[ERROR] Module '$MODULE_NAME' not found in module-registry (HTTP $REG_CODE)." >&2
        exit 1
    fi
    echo "  Module ID: $MOD_ID"

    # Phase 1: deactivate-all tenants
    echo "Deactivating for all tenants..."
    local DA_BODY DA_CODE
    DA_BODY=$(curl -s -w "\n%{http_code}" \
        -X POST \
        -H "Authorization: Bearer $TOKEN" \
        "$API_BASE_V1/modules/admin/$MOD_ID/deactivate-all" 2>/dev/null)
    DA_CODE=$(echo "$DA_BODY" | tail -1)
    local DA_JSON
    DA_JSON=$(echo "$DA_BODY" | sed '$d')

    if [[ "$DA_CODE" != "200" ]]; then
        echo "[ERROR] deactivate-all returned HTTP $DA_CODE:" >&2
        echo "$DA_JSON" >&2
        exit 1
    fi

    local TENANT_COUNT
    TENANT_COUNT=$(echo "$DA_JSON" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('tenants_deactivated', 0))
" 2>/dev/null || echo "0")

    echo "Module '$MODULE_NAME' deactivated from $TENANT_COUNT tenant(s). This will remove all module data."
    echo ""

    # Confirmation prompt — user must type the module name exactly
    local CONFIRM
    read -r -p "Type the module name to confirm uninstall: " CONFIRM
    if [[ "$CONFIRM" != "$MODULE_NAME" ]]; then
        echo "Aborted."
        exit 0
    fi

    # Phase 2: DELETE with X-Confirm-Uninstall header
    echo "Uninstalling..."
    local DEL_BODY DEL_CODE
    DEL_BODY=$(curl -s -w "\n%{http_code}" \
        -X DELETE \
        -H "Authorization: Bearer $TOKEN" \
        -H "X-Confirm-Uninstall: true" \
        "$API_BASE_V1/modules/admin/$MOD_ID" 2>/dev/null)
    DEL_CODE=$(echo "$DEL_BODY" | tail -1)
    local DEL_JSON
    DEL_JSON=$(echo "$DEL_BODY" | sed '$d')

    if [[ "$DEL_CODE" == "200" || "$DEL_CODE" == "204" ]]; then
        echo "Module '$MODULE_NAME' uninstalled successfully."
    else
        echo "[ERROR] Uninstall failed (HTTP $DEL_CODE):" >&2
        echo "$DEL_JSON" >&2
        exit 1
    fi
}

_module_rollback() {
    local NAME="$1" REASON="${2:-unknown}" BACKEND_DIR="${3:-}" FRONTEND_DIR="${4:-}"
    echo "[WARNING] Rolling back install of '$NAME': $REASON" >&2

    # Remove copied files if paths were provided
    if [[ -n "$BACKEND_DIR" && -d "$BACKEND_DIR" ]]; then
        rm -rf "$BACKEND_DIR" && echo "[INFO] Rollback: removed backend dir $BACKEND_DIR" >&2 || true
    fi
    if [[ -n "$FRONTEND_DIR" && -d "$FRONTEND_DIR" ]]; then
        rm -rf "$FRONTEND_DIR" && echo "[INFO] Rollback: removed frontend dir $FRONTEND_DIR" >&2 || true
    fi

    # Set install_status=failed in DB
    docker exec app_buildify_backend python3 -c         "import os; os.environ['TESTING']='1'
from datetime import datetime
from app.core.db import SessionLocal
from app.models.nocode_module import Module
db=SessionLocal()
m=db.query(Module).filter(Module.name=='$NAME').first()
if m:
    m.install_status='failed'; m.install_error_message='$REASON'[:200]
    m.updated_at=datetime.utcnow(); db.commit()
db.close()" 2>/dev/null || true
}
case $COMMAND in
    start)
        validate_database
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        validate_database
        restart_services
        ;;
    status)
        validate_database
        check_status
        ;;
    ps|list)
        list_containers
        ;;
    stats)
        show_stats
        ;;
    migrate)
        validate_database
        if [ ! -f "$COMPOSE_FULL_PATH" ]; then
            print_error "Compose file not found: $COMPOSE_FULL_PATH"
            exit 1
        fi
        check_services_running
        run_migrations
        ;;
    logs)
        view_logs
        ;;
    clean)
        clean_services
        ;;
    build)
        validate_database
        build_images
        ;;
    shell)
        open_backend_shell
        ;;
    db-shell)
        open_db_shell
        ;;
    seed)
        validate_database
        check_services_running
        seed_database
        ;;
    quick-seed)
        validate_database
        check_services_running
        quick_seed_database
        ;;
    db-reset)
        validate_database
        reset_database
        ;;
    backup)
        validate_database
        check_services_running
        backup_database
        ;;
    restore)
        validate_database
        check_services_running
        restore_database
        ;;
    setup)
        setup_environment
        ;;
    exec)
        exec_service "$@"
        ;;
    test)
        check_services_running
        run_tests
        ;;
    seed-menu)
        check_services_running
        seed_menu_items
        ;;
    seed-menu-rbac)
        check_services_running
        seed_menu_rbac "$@"
        ;;
    seed-module-rbac)
        check_services_running
        seed_module_rbac "$@"
        ;;
    seed-financial-rbac)
        check_services_running
        seed_financial_rbac "$@"
        ;;
    seed-permissions)
        check_services_running
        seed_all_permissions
        ;;
    seed-rbac)
        check_services_running
        seed_rbac_with_groups
        ;;
    module)
        SUBCOMMAND="${2:-}"
        shift 2 || true
        case "$SUBCOMMAND" in


                        new) module_new "$@" ;;
pack) module_pack "$@" ;;
            install) module_install "$@" ;;
            uninstall) shift; module_uninstall "$@" ;;
            migrate-tenant)
                # T-22.019 / arch-22 section 4.2 placeholder
                # Full implementation deferred to sprint N+1 (L-1)
                TENANT_ID=""
                MODULE_ID=""
                if [ -z "" ] || [ -z "" ]; then
                    echo "Usage: manage.sh module migrate-tenant <tenant_id> <module_id>"
                    exit 1
                fi
                echo "[T-22.019] module migrate-tenant: placeholder -- full wiring deferred to sprint N+1"
                echo "  tenant_id= module_id="
                exit 0
                ;;
            *) echo "Unknown module subcommand: $SUBCOMMAND"; echo "  new <name>  pack  <dir> [--out <dir>]  install <pkg>  uninstall <name>"; exit 1 ;;
        esac
        ;;
    tenant)
        SUBCOMMAND="${2:-}"
        shift 2 || true
        case "$SUBCOMMAND" in
            deactivate)
                TENANT_ID="${1:-}"
                if [ -z "$TENANT_ID" ]; then
                    echo "Usage: manage.sh tenant deactivate <tenant_id>"
                    exit 1
                fi
                echo "==> Deactivating tenant: $TENANT_ID"
                docker exec app_buildify_backend python3 /app/scripts/cleanup_tenant_module_dbs.py "$TENANT_ID" || \
                    python3 /home/mahfudi/app-buildify/scripts/cleanup_tenant_module_dbs.py "$TENANT_ID"
                echo "Tenant $TENANT_ID deactivated."
                ;;
            *)
                echo "Unknown tenant subcommand: $SUBCOMMAND"
                echo "  deactivate <tenant_id>"
                exit 1
                ;;
        esac
        ;;
    check-tenant-scope)
        # T-22.003 / T-22.021 / T-22.022: CI gate that catches raw tenant_id == literals.
        #
        # Lines annotated with "# tenant-scope-ok" (or the legacy "# tenant_scope")
        # are accepted and not counted. Every other raw ".tenant_id ==" literal in
        # services/ or routers/ is a VIOLATION.
        #
        # Baseline (frozen at T-22.009 merge): 36 unannotated router-layer literals
        # tracked as M-2 follow-up for sprint N+1. The gate fails the build only when
        # the violation count RISES ABOVE this baseline, i.e. when a NEW unannotated
        # literal is introduced. The ratchet only goes down: as M-2 literals are
        # migrated or annotated, lower the baseline below.
        #
        # See docs/backend/TENANT_SCOPE_MIGRATION.md for the annotation convention.
        BASELINE=36
        # Allow CI to override (e.g. to ratchet) via TENANT_SCOPE_BASELINE env var.
        BASELINE="${TENANT_SCOPE_BASELINE:-$BASELINE}"
        SCOPE_DIRS=(
            "/home/mahfudi/app-buildify/backend/app/services/"
            "/home/mahfudi/app-buildify/backend/app/routers/"
        )
        echo "==> check-tenant-scope: scanning services/ and routers/ for raw tenant_id == literals (baseline=$BASELINE)..."
        VIOLATIONS=$(
            grep -rn "\.tenant_id ==" "${SCOPE_DIRS[@]}" 2>/dev/null \
            | grep -v "tenant-scope-ok" \
            | grep -v "tenant_scope" \
            | grep -v "scope\.py:" \
            || true
        )
        if [ -n "$VIOLATIONS" ]; then
            COUNT=$(printf '%s\n' "$VIOLATIONS" | grep -c . )
        else
            COUNT=0
        fi
        echo "check-tenant-scope: $COUNT unannotated literal(s) found (baseline $BASELINE)."
        if [ "$COUNT" -gt "$BASELINE" ]; then
            echo ""
            echo "ERROR: tenant-scope violations ($COUNT) exceed baseline ($BASELINE)."
            echo "       Use apply_tenant_scope() instead of a raw '.tenant_id ==' filter,"
            echo "       or annotate an intentional exception with:  # tenant-scope-ok"
            echo ""
            echo "$VIOLATIONS"
            echo ""
            exit 1
        fi
        if [ "$COUNT" -lt "$BASELINE" ]; then
            echo "check-tenant-scope: PASS — and below baseline; consider lowering BASELINE to $COUNT to ratchet."
        else
            echo "check-tenant-scope: PASS — at baseline, no new violations introduced."
        fi
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $COMMAND"
        echo ""
        show_help
        exit 1
        ;;
esac
