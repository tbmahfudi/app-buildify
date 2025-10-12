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

# Function to display help
show_help() {
    echo "Docker Compose Management Script"
    echo ""
    echo "Usage: $0 [command] [database_type]"
    echo ""
    echo "Commands:"
    echo "  start       - Start all containers"
    echo "  stop        - Stop all containers"
    echo "  restart     - Restart all containers"
    echo "  migrate     - Run database migrations"
    echo "  logs        - View container logs"
    echo "  clean       - Stop and remove containers and volumes"
    echo "  build       - Build images"
    echo "  shell       - Open backend shell"
    echo "  db-shell    - Open database shell"
    echo "  seed        - Seed database with test data"
    echo "  help        - Show this help message"
    echo ""
    echo "Database types:"
    echo "  postgres    - PostgreSQL (default)"
    echo "  mysql       - MySQL"
    echo ""
    echo "Examples:"
    echo "  $0 start postgres"
    echo "  $0 migrate mysql"
    echo "  $0 stop"
}

# Function to start services
start_services() {
    print_info "Starting services with $DATABASE..."
    docker compose -f "$COMPOSE_FULL_PATH" up -d
    print_info "Services started successfully"
    print_info "Backend: http://localhost:8000"
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
    
    if ! docker compose -f "$COMPOSE_FULL_PATH" exec -T backend alembic upgrade head; then
        print_error "Migration failed"
        exit 1
    fi
    
    print_info "Migrations completed successfully"
}

# Function to view logs
view_logs() {
    print_info "Displaying logs (Ctrl+C to exit)..."
    docker compose -f "$COMPOSE_FULL_PATH" logs -f
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
    
    print_info "Seeding organizations..."
    docker compose -f "$COMPOSE_FULL_PATH" exec -T backend python -m app.seeds.seed_org
    
    print_info "Seeding users..."
    docker compose -f "$COMPOSE_FULL_PATH" exec -T backend python -m app.seeds.seed_users
    
    print_info "Seeding metadata..."
    docker compose -f "$COMPOSE_FULL_PATH" exec -T backend python -m app.seeds.seed_metadata
    
    print_info "Database seeding completed successfully"
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
    migrate)
        validate_database
        if [ ! -f "$COMPOSE_FULL_PATH" ]; then
            print_error "Compose file not found: $COMPOSE_FULL_PATH"
            exit 1
        fi
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
    seed)
        validate_database
        seed_database
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