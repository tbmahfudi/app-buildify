/**
 * Module Loader - Option 1: Integrated SPA Modules
 *
 * Dynamically loads and manages modules as ES6 modules.
 * Modules share the same runtime and component library for a seamless UX.
 */

class ModuleLoader {
    constructor() {
        this.modules = new Map();
        this.routes = new Map();
        this.activeModule = null;
    }

    /**
     * Load a module dynamically
     *
     * @param {string} moduleName - Name of the module to load
     * @returns {Promise<Object>} - The loaded module instance
     */
    async loadModule(moduleName) {
        // Check if already loaded
        if (this.modules.has(moduleName)) {
            return this.modules.get(moduleName);
        }

        try {
            // Fetch module manifest
            const manifestResponse = await fetch(`/api/v1/modules/${moduleName}/manifest`);
            if (!manifestResponse.ok) {
                throw new Error(`Failed to fetch manifest for ${moduleName}`);
            }

            const manifest = await manifestResponse.json();

            // Load module bundle
            const moduleUrl = `/modules/${moduleName}/${manifest.frontend.entry_point}`;
            const moduleExport = await import(moduleUrl);

            // Instantiate module
            const ModuleClass = moduleExport.default;
            const moduleInstance = new ModuleClass(manifest);

            // Initialize module
            await moduleInstance.init();

            // Register routes
            this.registerRoutes(moduleName, manifest.routes, moduleInstance);

            // Store module
            this.modules.set(moduleName, {
                instance: moduleInstance,
                manifest: manifest
            });

            console.log(`Module '${moduleName}' loaded successfully`);

            return moduleInstance;

        } catch (error) {
            console.error(`Error loading module '${moduleName}':`, error);
            throw error;
        }
    }

    /**
     * Register routes from module manifest
     *
     * @param {string} moduleName - Module name
     * @param {Array} routes - Routes from manifest
     * @param {Object} moduleInstance - Module instance
     */
    registerRoutes(moduleName, routes, moduleInstance) {
        routes.forEach(route => {
            const routePath = route.path.replace('#/', '');

            this.routes.set(routePath, {
                module: moduleName,
                component: route.component,
                permission: route.permission,
                name: route.name,
                moduleInstance: moduleInstance,
                menu: route.menu
            });

            console.log(`Registered route: ${routePath} -> ${moduleName}/${route.component}`);
        });
    }

    /**
     * Navigate to a route
     *
     * @param {string} path - Route path (without #/)
     */
    async navigate(path) {
        const route = this.routes.get(path);

        if (!route) {
            console.error(`Route not found: ${path}`);
            this.show404();
            return;
        }

        // Check permission
        if (route.permission) {
            const hasPermission = await this.checkPermission(route.permission);
            if (!hasPermission) {
                this.show403();
                return;
            }
        }

        // Load page component
        try {
            const componentUrl = `/modules/${route.module}/frontend/${route.component}`;
            const componentModule = await import(componentUrl);

            const PageClass = componentModule.default;
            const page = new PageClass();

            // Get container
            const container = document.getElementById('app-content');
            if (!container) {
                throw new Error('App content container not found');
            }

            // Clear container
            container.innerHTML = '';

            // Render page
            await page.render(container);

            // Update active module
            this.activeModule = route.module;

            // Update browser URL
            window.location.hash = `#/${path}`;

        } catch (error) {
            console.error(`Error navigating to ${path}:`, error);
            this.showError(error);
        }
    }

    /**
     * Check if user has permission
     *
     * @param {string} permission - Permission code
     * @returns {Promise<boolean>}
     */
    async checkPermission(permission) {
        try {
            const response = await fetch('/api/v1/rbac/check', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({ permission })
            });

            const result = await response.json();
            return result.has_permission;

        } catch (error) {
            console.error('Error checking permission:', error);
            return false;
        }
    }

    /**
     * Load all enabled modules for current tenant
     */
    async loadEnabledModules() {
        try {
            const response = await fetch('/api/v1/module-registry/enabled', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            const modules = await response.json();

            // Load each module
            for (const moduleName of modules) {
                await this.loadModule(moduleName);
            }

            // Build navigation menu
            this.buildNavigationMenu();

        } catch (error) {
            console.error('Error loading enabled modules:', error);
        }
    }

    /**
     * Build navigation menu from loaded modules
     */
    buildNavigationMenu() {
        const menuItems = [];

        // Collect all menu items from routes
        this.routes.forEach((route, path) => {
            if (route.menu) {
                menuItems.push({
                    ...route.menu,
                    path: path,
                    moduleName: route.module
                });
            }
        });

        // Sort by order
        menuItems.sort((a, b) => (a.order || 999) - (b.order || 999));

        // Render menu
        this.renderMenu(menuItems);
    }

    /**
     * Render navigation menu
     *
     * @param {Array} menuItems - Menu items to render
     */
    renderMenu(menuItems) {
        const menuContainer = document.getElementById('app-navigation');
        if (!menuContainer) return;

        const menuHTML = menuItems.map(item => {
            return `
                <a href="#/${item.path}" class="nav-item" data-module="${item.moduleName}">
                    <i class="${item.icon}"></i>
                    <span>${item.label}</span>
                </a>
            `;
        }).join('');

        menuContainer.innerHTML = menuHTML;
    }

    /**
     * Show 404 page
     */
    show404() {
        const container = document.getElementById('app-content');
        container.innerHTML = `
            <div class="error-page">
                <h1>404</h1>
                <p>Page not found</p>
            </div>
        `;
    }

    /**
     * Show 403 page
     */
    show403() {
        const container = document.getElementById('app-content');
        container.innerHTML = `
            <div class="error-page">
                <h1>403</h1>
                <p>Access denied. You don't have permission to view this page.</p>
            </div>
        `;
    }

    /**
     * Show error page
     *
     * @param {Error} error - Error object
     */
    showError(error) {
        const container = document.getElementById('app-content');
        container.innerHTML = `
            <div class="error-page">
                <h1>Error</h1>
                <p>${error.message}</p>
            </div>
        `;
    }

    /**
     * Unload a module
     *
     * @param {string} moduleName - Module name
     */
    unloadModule(moduleName) {
        const module = this.modules.get(moduleName);
        if (!module) return;

        // Call cleanup if available
        if (module.instance.cleanup) {
            module.instance.cleanup();
        }

        // Remove routes
        this.routes.forEach((route, path) => {
            if (route.module === moduleName) {
                this.routes.delete(path);
            }
        });

        // Remove module
        this.modules.delete(moduleName);

        console.log(`Module '${moduleName}' unloaded`);
    }
}

// Create global instance
window.moduleLoader = new ModuleLoader();

// Setup hash change listener
window.addEventListener('hashchange', () => {
    const hash = window.location.hash.replace('#/', '');
    if (hash) {
        window.moduleLoader.navigate(hash);
    }
});

// Initialize on load
document.addEventListener('DOMContentLoaded', async () => {
    await window.moduleLoader.loadEnabledModules();

    // Navigate to initial route
    const initialHash = window.location.hash.replace('#/', '') || 'dashboard';
    window.moduleLoader.navigate(initialHash);
});

export default ModuleLoader;
