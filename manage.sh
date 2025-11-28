#!/bin/bash

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
    echo "  quick-seed     - Quick seed with minimal data (users only)"
    echo "  db-reset       - Reset database (drops all data)"
    echo "  backup         - Backup database to SQL file"
    echo "  restore        - Restore database from backup file"
    echo "  db-shell       - Open database shell"
    echo ""
    echo "Seed Scripts (RBAC & Menu):"
    echo "  seed-permissions   - Seed all permissions and role templates"
    echo "  seed-menu          - Seed menu items from frontend/config/menu.json"
    echo "  seed-menu-rbac [TENANT] - Seed menu management RBAC for tenant"
    echo "  seed-module-rbac [TENANT] - Seed module management RBAC for tenant"
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
    if curl -sf http://localhost:8000/health > /dev/null 2>&1 || curl -sf http://localhost:8000/docs > /dev/null 2>&1; then
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

# Function to quick seed (minimal data)
quick_seed_database() {
    print_info "Quick seeding database with minimal data..."

    print_info "Seeding complete organizational data..."
    print_info "Note: Using seed_complete_org (no minimal seed available)"
    if docker compose -f "$COMPOSE_FULL_PATH" exec -T backend python -m app.seeds.seed_complete_org; then
        print_info "Quick seed completed successfully"
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

# Main script logic
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