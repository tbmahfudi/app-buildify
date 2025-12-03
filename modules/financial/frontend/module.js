/**
 * Financial Module - Frontend
 *
 * Main module class for the Financial module frontend.
 */

export default class FinancialModule {
    constructor(manifest) {
        this.manifest = manifest;
        this.name = manifest.name;
        this.config = {};
        this.routes = [];
        this.menuItems = [];
    }

    /**
     * Initialize the module
     */
    async init() {
        console.log(`Initializing Financial Module v${this.manifest.version}`);

        // Load module configuration from backend
        await this.loadConfiguration();

        // Setup routes
        this.setupRoutes();

        // Setup menu items
        this.setupMenu();

        // Initialize any module-specific services
        this.initializeServices();

        console.log('Financial Module initialized');
    }

    /**
     * Setup module routes
     */
    setupRoutes() {
        this.routes = [
            {
                path: '#/financial/accounts',
                handler: async () => {
                    const { AccountsPage } = await import('./pages/accounts.js');
                    return AccountsPage;
                },
                permission: 'financial.accounts.view'
            },
            {
                path: '#/financial/customers',
                handler: async () => {
                    const { CustomersPage } = await import('./pages/customers.js');
                    return CustomersPage;
                },
                permission: 'financial.customers.view'
            },
            {
                path: '#/financial/invoices',
                handler: async () => {
                    const { InvoicesPage } = await import('./pages/invoices.js');
                    return InvoicesPage;
                },
                permission: 'financial.invoices.view'
            },
            {
                path: '#/financial/payments',
                handler: async () => {
                    const { PaymentsPage } = await import('./pages/payments.js');
                    return PaymentsPage;
                },
                permission: 'financial.payments.view'
            },
            {
                path: '#/financial/journal-entries',
                handler: async () => {
                    const { JournalEntriesPage } = await import('./pages/journal-entries.js');
                    return JournalEntriesPage;
                },
                permission: 'financial.journal.view'
            },
            {
                path: '#/financial/reports',
                handler: async () => {
                    const { ReportsPage } = await import('./pages/reports.js');
                    return ReportsPage;
                },
                permission: 'financial.reports.view'
            }
        ];
    }

    /**
     * Setup module menu items
     */
    setupMenu() {
        this.menuItems = [
            {
                title: 'Financial',
                icon: 'ph-duotone ph-currency-circle-dollar',
                iconColor: 'text-green-600',
                children: [
                    {
                        title: 'Accounts',
                        route: 'financial/accounts',
                        icon: 'ph-duotone ph-tree-structure',
                        iconColor: 'text-blue-600',
                        permission: 'financial.accounts.view'
                    },
                    {
                        title: 'Customers',
                        route: 'financial/customers',
                        icon: 'ph-duotone ph-user-circle',
                        iconColor: 'text-purple-600',
                        permission: 'financial.customers.view'
                    },
                    {
                        title: 'Invoices',
                        route: 'financial/invoices',
                        icon: 'ph-duotone ph-receipt',
                        iconColor: 'text-orange-600',
                        permission: 'financial.invoices.view'
                    },
                    {
                        title: 'Payments',
                        route: 'financial/payments',
                        icon: 'ph-duotone ph-credit-card',
                        iconColor: 'text-emerald-600',
                        permission: 'financial.payments.view'
                    },
                    {
                        title: 'Journal Entries',
                        route: 'financial/journal-entries',
                        icon: 'ph-duotone ph-notebook',
                        iconColor: 'text-indigo-600',
                        permission: 'financial.journal.view'
                    },
                    {
                        title: 'Reports',
                        route: 'financial/reports',
                        icon: 'ph-duotone ph-chart-line',
                        iconColor: 'text-teal-600',
                        permission: 'financial.reports.view'
                    }
                ]
            }
        ];
    }

    /**
     * Get module routes
     */
    getRoutes() {
        return this.routes;
    }

    /**
     * Get module menu items
     */
    getMenuItems() {
        return this.menuItems;
    }

    /**
     * Load module configuration from backend
     */
    async loadConfiguration() {
        try {
            const response = await fetch('/api/v1/financial/config', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            if (response.ok) {
                this.config = await response.json();
            }
        } catch (error) {
            console.error('Error loading financial module configuration:', error);
            // Use defaults from manifest
            this.config = this.manifest.configuration?.defaults || {};
        }
    }

    /**
     * Initialize module services
     */
    initializeServices() {
        // Initialize any background services, websockets, etc.
    }

    /**
     * Cleanup when module is unloaded
     */
    cleanup() {
        console.log('Cleaning up Financial Module');
        // Cleanup any resources, event listeners, etc.
    }

    /**
     * Get module configuration value
     *
     * @param {string} key - Configuration key
     * @returns {*} - Configuration value
     */
    getConfig(key) {
        return this.config[key];
    }
}
