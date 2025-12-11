#!/bin/bash

# Financial Module - Setup Script for Multiple Tenants
# This script sets up financial sample data for TECHSTART and FASHIONHUB tenants

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Financial Module - Multi-Tenant Setup                   ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Function to setup a tenant
setup_tenant() {
    local tenant_code=$1
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Setting up financial data for: $tenant_code"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    python setup_sample_data.py $tenant_code
    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
        echo "✅ $tenant_code setup completed successfully!"
    else
        echo "❌ $tenant_code setup failed with exit code: $exit_code"
        return $exit_code
    fi
    echo ""
}

# Parse command line arguments
if [ $# -eq 0 ]; then
    echo "📋 Available options:"
    echo "  1. Setup TECHSTART"
    echo "  2. Setup FASHIONHUB"
    echo "  3. Setup BOTH tenants"
    echo "  4. Custom tenant code"
    echo ""
    read -p "Enter choice (1-4): " choice

    case $choice in
        1)
            setup_tenant "TECHSTART"
            ;;
        2)
            setup_tenant "FASHIONHUB"
            ;;
        3)
            setup_tenant "TECHSTART"
            setup_tenant "FASHIONHUB"
            ;;
        4)
            read -p "Enter tenant code: " custom_code
            setup_tenant "$custom_code"
            ;;
        *)
            echo "❌ Invalid choice"
            exit 1
            ;;
    esac
else
    # Setup specified tenant(s) from command line
    for tenant in "$@"; do
        setup_tenant "${tenant^^}"  # Convert to uppercase
    done
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Setup Complete!                                          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "🌐 Frontend Access:"
echo "   http://localhost:8080"
echo ""
echo "👤 Login Credentials:"
echo "   TECHSTART users:"
echo "     - ceo@techstart.com / password123"
echo "     - cto@techstart.com / password123"
echo ""
echo "   FASHIONHUB users:"
echo "     - ceo@fashionhub.com / password123"
echo "     - cfo@fashionhub.com / password123"
echo ""
echo "📊 Financial Module Pages:"
echo "   - Dashboard:  #/financial/dashboard"
echo "   - Accounts:   #/financial/accounts"
echo "   - Invoices:   #/financial/invoices"
echo "   - Payments:   #/financial/payments"
echo "   - Reports:    #/financial/reports"
echo ""
