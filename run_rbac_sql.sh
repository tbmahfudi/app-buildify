#!/bin/bash

# Script to run RBAC verification and cleanup SQL scripts
# Usage: ./run_rbac_sql.sh [verify|cleanup|cleanup-interactive]

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="infra/docker-compose.dev.yml"

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to run SQL file
run_sql() {
    local sql_file=$1
    local description=$2

    print_info "$description"
    echo ""

    docker compose -f "$COMPOSE_FILE" exec -T postgres psql -U appuser -d appdb < "$sql_file"

    echo ""
    print_info "Done!"
}

# Main script
case ${1:-help} in
    verify)
        run_sql "backend/app/seeds/verify_rbac.sql" "Running RBAC verification..."
        ;;

    cleanup)
        run_sql "backend/app/seeds/cleanup_rbac.sql" "Running comprehensive RBAC analysis..."
        echo ""
        print_warning "To actually delete user_roles records, edit cleanup_rbac.sql and uncomment the DELETE statement"
        ;;

    cleanup-interactive)
        print_warning "This will run interactive cleanup. You'll be prompted for confirmation."
        echo ""
        docker compose -f "$COMPOSE_FILE" exec -i postgres psql -U appuser -d appdb < backend/app/seeds/cleanup_user_roles.sql
        ;;

    help|--help|-h|*)
        echo "RBAC SQL Script Runner"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  verify              - Quick verification (read-only, safe)"
        echo "  cleanup             - Comprehensive analysis (safe, cleanup commented out)"
        echo "  cleanup-interactive - Interactive cleanup with confirmation (destructive)"
        echo "  help                - Show this help"
        echo ""
        echo "Examples:"
        echo "  $0 verify              # Check if users are in groups"
        echo "  $0 cleanup             # Full analysis"
        echo "  $0 cleanup-interactive # Delete user_roles with confirmation"
        echo ""
        ;;
esac
