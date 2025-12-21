/**
 * Builder Module - Frontend
 *
 * Main module class for the UI Builder module frontend.
 */

export default class BuilderModule {
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
        console.log(`Initializing UI Builder Module v${this.manifest.version}`);

        // Load module configuration from backend
        await this.loadConfiguration();

        // Setup routes
        this.setupRoutes();

        // Setup menu items
        this.setupMenu();

        // Initialize any module-specific services
        this.initializeServices();

        console.log('UI Builder Module initialized');
    }

    /**
     * Setup module routes
     */
    setupRoutes() {
        this.routes = [
            {
                path: '#/builder',
                handler: async () => {
                    const { BuilderPage } = await import('./pages/builder.js');
                    return BuilderPage;
                },
                permission: 'builder:design:tenant'
            },
            {
                path: '#/builder/pages',
                handler: async () => {
                    const { PagesListPage } = await import('./pages/pages-list.js');
                    return PagesListPage;
                },
                permission: 'builder:pages:read:tenant'
            }
        ];
    }

    /**
     * Setup module menu items
     */
    setupMenu() {
        this.menuItems = [
            {
                title: 'Tools',
                icon: 'ph-duotone ph-toolbox',
                iconColor: 'text-purple-600',
                children: [
                    {
                        title: 'UI Builder',
                        route: 'builder',
                        icon: 'ph-duotone ph-code-block',
                        iconColor: 'text-blue-600',
                        permission: 'builder:design:tenant'
                    },
                    {
                        title: 'Pages',
                        route: 'builder/pages',
                        icon: 'ph-duotone ph-files',
                        iconColor: 'text-purple-600',
                        permission: 'builder:pages:read:tenant'
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
            const response = await fetch('/api/v1/builder/config', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            if (response.ok) {
                this.config = await response.json();
            }
        } catch (error) {
            console.error('Error loading builder module configuration:', error);
            // Use defaults from manifest
            this.config = this.manifest.configuration?.defaults || {};
        }
    }

    /**
     * Initialize module services
     */
    initializeServices() {
        // Initialize any background services
        console.log('Builder services initialized');
    }

    /**
     * Cleanup when module is unloaded
     */
    cleanup() {
        console.log('Cleaning up Builder Module');
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
