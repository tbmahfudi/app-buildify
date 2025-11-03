/**
 * Frontend Module Loader
 *
 * Dynamically loads and registers frontend modules based on backend enablement.
 * Modules are loaded only if they are enabled for the current tenant.
 */

import { getAuthToken, apiFetch } from '../../api.js';

class ModuleLoader {
  constructor() {
    this.modules = new Map();
    this.manifests = new Map();
    this.loading = new Set();
    this.loadErrors = new Map();
  }

  /**
   * Fetch enabled modules for current tenant from backend
   *
   * @returns {Promise<Array<string>>} Array of enabled module names
   */
  async fetchEnabledModules() {
    try {
      const token = getAuthToken();
      if (!token) {
        console.warn('No auth token available');
        return [];
      }

      const response = await apiFetch('/modules/enabled/names');

      if (!response.ok) {
        throw new Error(`Failed to fetch enabled modules: ${response.statusText}`);
      }

      const moduleNames = await response.json();
      console.log('Enabled modules:', moduleNames);
      return moduleNames;
    } catch (error) {
      console.error('Error fetching enabled modules:', error);
      return [];
    }
  }

  /**
   * Load a module's manifest.json
   *
   * @param {string} moduleName - Name of the module
   * @returns {Promise<Object|null>} Module manifest or null if failed
   */
  async loadManifest(moduleName) {
    // Return cached manifest if available
    if (this.manifests.has(moduleName)) {
      return this.manifests.get(moduleName);
    }

    try {
      const response = await fetch(`/modules/${moduleName}/manifest.json`);

      if (!response.ok) {
        throw new Error(`Failed to load manifest: ${response.statusText}`);
      }

      const manifest = await response.json();
      this.manifests.set(moduleName, manifest);
      console.log(`Loaded manifest for ${moduleName}`);
      return manifest;
    } catch (error) {
      console.error(`Error loading manifest for ${moduleName}:`, error);
      this.loadErrors.set(moduleName, `Manifest load error: ${error.message}`);
      return null;
    }
  }

  /**
   * Load a module's JavaScript entry point
   *
   * @param {string} moduleName - Name of the module
   * @returns {Promise<Object|null>} Module instance or null if failed
   */
  async loadModule(moduleName) {
    // Return cached module if already loaded
    if (this.modules.has(moduleName)) {
      console.log(`Returning cached module: ${moduleName}`);
      return this.modules.get(moduleName);
    }

    // Check if module is currently loading
    if (this.loading.has(moduleName)) {
      console.warn(`Module ${moduleName} is already being loaded`);
      return null;
    }

    this.loading.add(moduleName);

    try {
      // Load manifest first
      const manifest = await this.loadManifest(moduleName);
      if (!manifest) {
        throw new Error('Failed to load manifest');
      }

      // Determine entry point
      const entryPoint = manifest.entry_point || 'module.js';
      const modulePath = `/modules/${moduleName}/${entryPoint}`;

      console.log(`Loading module from: ${modulePath}`);

      // Dynamic import of module entry point
      const moduleExports = await import(modulePath);

      // Try to find the module class
      // Convention: module.js should export default or have a named export like FinancialModule
      const ModuleClass = moduleExports.default ||
                          moduleExports[`${this._capitalize(moduleName)}Module`] ||
                          moduleExports[this._toPascalCase(moduleName) + 'Module'];

      if (!ModuleClass) {
        throw new Error(`Module class not found in ${modulePath}`);
      }

      // Instantiate module
      const moduleInstance = new ModuleClass(manifest);

      // Initialize module
      if (typeof moduleInstance.init === 'function') {
        await moduleInstance.init();
      }

      // Cache module instance
      this.modules.set(moduleName, moduleInstance);
      console.log(`✓ Successfully loaded module: ${moduleName} (v${manifest.version})`);

      return moduleInstance;
    } catch (error) {
      console.error(`Error loading module ${moduleName}:`, error);
      this.loadErrors.set(moduleName, `Load error: ${error.message}`);
      return null;
    } finally {
      this.loading.delete(moduleName);
    }
  }

  /**
   * Load all enabled modules
   *
   * @returns {Promise<Map>} Map of loaded modules
   */
  async loadAllModules() {
    console.log('Loading all enabled modules...');

    const enabledModules = await this.fetchEnabledModules();

    if (enabledModules.length === 0) {
      console.log('No enabled modules found');
      return this.modules;
    }

    // Load modules in parallel
    const loadPromises = enabledModules.map(moduleName =>
      this.loadModule(moduleName).catch(error => {
        console.error(`Failed to load ${moduleName}:`, error);
        return null;
      })
    );

    await Promise.all(loadPromises);

    console.log(`✓ Loaded ${this.modules.size} modules successfully`);

    if (this.loadErrors.size > 0) {
      console.warn(`Failed to load ${this.loadErrors.size} modules:`,
        Array.from(this.loadErrors.entries()));
    }

    return this.modules;
  }

  /**
   * Get a loaded module by name
   *
   * @param {string} moduleName - Name of the module
   * @returns {Object|null} Module instance or null
   */
  getModule(moduleName) {
    return this.modules.get(moduleName) || null;
  }

  /**
   * Get all loaded modules
   *
   * @returns {Array<Object>} Array of module instances
   */
  getAllModules() {
    return Array.from(this.modules.values());
  }

  /**
   * Get all routes from loaded modules
   *
   * @returns {Array<Object>} Array of route objects
   */
  getAllRoutes() {
    const routes = [];

    for (const module of this.modules.values()) {
      if (typeof module.getRoutes === 'function') {
        const moduleRoutes = module.getRoutes();
        routes.push(...moduleRoutes);
      }
    }

    return routes;
  }

  /**
   * Get all menu items from loaded modules
   *
   * @returns {Array<Object>} Array of menu item objects
   */
  getAllMenuItems() {
    const menuItems = [];

    for (const [moduleName, manifest] of this.manifests.entries()) {
      if (!manifest.routes) continue;

      for (const route of manifest.routes) {
        if (route.menu) {
          menuItems.push({
            ...route.menu,
            path: route.path,
            name: route.name,
            moduleName: moduleName,
            permission: route.permission
          });
        }
      }
    }

    // Sort by order
    menuItems.sort((a, b) => (a.order || 999) - (b.order || 999));

    return menuItems;
  }

  /**
   * Get dashboard widgets from all modules
   *
   * @returns {Array<Object>} Array of widget configurations
   */
  getDashboardWidgets() {
    const widgets = [];

    for (const [moduleName, manifest] of this.manifests.entries()) {
      const navigation = manifest.navigation || {};
      const dashboardWidgets = navigation.dashboard_widgets || [];

      for (const widget of dashboardWidgets) {
        widgets.push({
          ...widget,
          moduleName: moduleName
        });
      }
    }

    return widgets;
  }

  /**
   * Reload a specific module (useful for development)
   *
   * @param {string} moduleName - Name of module to reload
   * @returns {Promise<Object|null>} Reloaded module instance
   */
  async reloadModule(moduleName) {
    console.log(`Reloading module: ${moduleName}`);

    // Remove from caches
    this.modules.delete(moduleName);
    this.manifests.delete(moduleName);
    this.loadErrors.delete(moduleName);

    // Load again
    return await this.loadModule(moduleName);
  }

  /**
   * Unload a module
   *
   * @param {string} moduleName - Name of module to unload
   * @returns {boolean} True if unloaded, false if wasn't loaded
   */
  unloadModule(moduleName) {
    if (this.modules.has(moduleName)) {
      const module = this.modules.get(moduleName);

      // Call cleanup if available
      if (typeof module.cleanup === 'function') {
        module.cleanup();
      }

      this.modules.delete(moduleName);
      this.manifests.delete(moduleName);
      console.log(`Unloaded module: ${moduleName}`);
      return true;
    }

    return false;
  }

  /**
   * Check if a module is loaded
   *
   * @param {string} moduleName - Name of the module
   * @returns {boolean} True if loaded
   */
  isModuleLoaded(moduleName) {
    return this.modules.has(moduleName);
  }

  /**
   * Get load errors
   *
   * @returns {Map} Map of module names to error messages
   */
  getLoadErrors() {
    return new Map(this.loadErrors);
  }

  /**
   * Helper: Capitalize first letter
   * @private
   */
  _capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
  }

  /**
   * Helper: Convert to PascalCase (e.g., user-management -> UserManagement)
   * @private
   */
  _toPascalCase(str) {
    return str
      .split(/[-_]/)
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join('');
  }
}

// Create and export singleton instance
export const moduleLoader = new ModuleLoader();
export default moduleLoader;
