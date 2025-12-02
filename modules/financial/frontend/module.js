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
    }

    /**
     * Initialize the module
     */
    async init() {
        console.log(`Initializing Financial Module v${this.manifest.version}`);

        // Load module configuration from backend
        await this.loadConfiguration();

        // Initialize any module-specific services
        this.initializeServices();

        console.log('Financial Module initialized');
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
            this.config = this.manifest.configuration.defaults;
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
