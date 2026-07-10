/**
 * Frontend Module Loader
 *
 * Dynamically loads and registers frontend modules based on backend enablement.
 * Modules are loaded only if they are enabled for the current tenant.
 */

import { getAuthToken, apiFetch } from '../../api.js';
import { BaseModule } from './base-module.js';

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

      const response = await apiFetch('/module-registry/enabled/names');

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
      // Fetch the full manifest from the module-registry API. NOTE: the
      // endpoint lives under /module-registry/{name}/manifest (returns the
      // complete manifest incl. entry_point + routes); /modules/{name}/manifest
      // does NOT exist (404) — using it left modules with zero registered routes.
      const response = await apiFetch(`/module-registry/${moduleName}/manifest`);

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

      // Dev-mode contract validation (console-warn only; never blocks loading).
      this._validateManifest(moduleName, manifest);

      // Resolve the module instance. Per the ADR "Generic loader" rule:
      //   - If `entry_point` is null/absent, OR
      //   - If importing the declared entry point 404s / fails,
      // we fall back to a generic BaseModule built straight from the manifest,
      // so a manifest-only module (no module.js) still registers its routes
      // instead of failing the whole loader.
      const moduleInstance = await this._resolveModuleInstance(moduleName, manifest);

      // Initialize module (BaseModule.init() registers routes from the manifest).
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
      // Add parent menu items from navigation.menu_items
      if (manifest.navigation && manifest.navigation.menu_items) {
        for (const menuItem of manifest.navigation.menu_items) {
          menuItems.push({
            label: menuItem.label,
            icon: menuItem.icon,
            iconColor: menuItem.icon_color,
            order: menuItem.order,
            parent: null,
            code: menuItem.code,
            moduleName: moduleName,
            permission: menuItem.permission,
            is_parent: menuItem.is_parent || false
          });
        }
      }

      // Add route-based menu items
      if (manifest.routes) {
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
   * Resolve a module instance for a manifest, with graceful degradation.
   *
   * Strategy (ADR):
   *   1. If the manifest declares an `entry_point`, try to dynamic-import it
   *      and instantiate the exported module class (custom init path, e.g.
   *      financial). If that import 404s or the class is missing, fall through.
   *   2. Otherwise (no entry_point, or entry import failed), build a generic
   *      `BaseModule` directly from the manifest. BaseModule.registerRoutes()
   *      maps manifest.routes[] to route handlers, so the module still works.
   *
   * @param {string} moduleName
   * @param {Object} manifest
   * @returns {Promise<Object>} A module instance (custom or generic BaseModule)
   * @private
   */
  async _resolveModuleInstance(moduleName, manifest) {
    const entryPoint = manifest.entry_point;

    if (entryPoint) {
      const modulePath = `/modules/${moduleName}/${entryPoint}`;
      try {
        console.log(`Loading module from: ${modulePath}`);
        const moduleExports = await import(modulePath);

        const ModuleClass = moduleExports.default ||
                            moduleExports[`${this._capitalize(moduleName)}Module`] ||
                            moduleExports[this._toPascalCase(moduleName) + 'Module'];

        if (!ModuleClass) {
          throw new Error(`Module class not found in ${modulePath}`);
        }
        return new ModuleClass(manifest);
      } catch (error) {
        console.warn(
          `Entry point for module "${moduleName}" failed to load (${modulePath}): ` +
          `${error.message}. Falling back to generic BaseModule from manifest.`
        );
        // fall through to generic loader
      }
    } else {
      console.log(
        `Module "${moduleName}" has no entry_point; using generic BaseModule from manifest.`
      );
    }

    // Generic, manifest-driven module.
    return new BaseModule(manifest);
  }

  /**
   * Dev-mode manifest validator. Emits actionable console warnings for
   * non-conformant manifests so authors get feedback instead of silent 404s.
   * Never throws and never blocks loading.
   *
   * Contract source of truth: docs/modules/module-manifest.schema.json (the backend
   * enforces the same rules in core/module_system/manifest_validation.py). Keep the
   * three in sync when the manifest shape changes.
   *
   * Checks (per the Module Frontend Contract):
   *   - missing navigation.menu_items (no top-level menu parent will render)
   *   - menu parent items missing an icon
   *   - routes[].component paths that start with `frontend/` (double-frontend bug)
   *   - routes[].menu.parent that does not match any navigation.menu_items[].code
   *   - no entry_point AND no routes (module would register nothing)
   *
   * @param {string} moduleName
   * @param {Object} manifest
   * @private
   */
  _validateManifest(moduleName, manifest) {
    // Only run in dev mode; silent in production.
    const cfg = (typeof window !== 'undefined' && window.APP_CONFIG) || {};
    const devMode = cfg.devMode === true ||
      (typeof window !== 'undefined' && /^(localhost|127\.0\.0\.1)$/.test(window.location.hostname));
    if (!devMode) return;

    const warn = (msg) => console.warn(`[module-validator:${moduleName}] ${msg}`);
    const nav = manifest.navigation || {};
    const menuItems = Array.isArray(nav.menu_items) ? nav.menu_items : [];
    const routes = Array.isArray(manifest.routes) ? manifest.routes : [];

    if (!menuItems.length) {
      warn('manifest has no navigation.menu_items: no top-level menu parent ' +
           'will render and route menus may orphan.');
    }

    const parentCodes = new Set(menuItems.map(m => m.code));

    for (const item of menuItems) {
      if (!item.icon) {
        warn(`menu_items[code="${item.code}"] is missing an "icon".`);
      }
    }

    if (!manifest.entry_point && !routes.length) {
      warn('manifest has no entry_point and no routes: this module registers nothing.');
    }

    for (const route of routes) {
      const comp = route.component;
      if (typeof comp === 'string' && /^frontend\//.test(comp)) {
        warn(`route "${route.path}" component "${comp}" starts with ` +
             '"frontend/". Paths are relative to frontend/ and MUST NOT include ' +
             'it (causes a double-frontend 404). The loader strips it defensively.');
      }
      const parent = route.menu && route.menu.parent;
      if (parent && !parentCodes.has(parent)) {
        warn(`route "${route.path}" menu.parent "${parent}" does not match ` +
             'any navigation.menu_items[].code (menu item will orphan).');
      }
    }
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
