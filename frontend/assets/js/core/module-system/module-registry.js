/**
 * Module Registry
 *
 * Manages registration and access to loaded modules.
 * Provides centralized access to module routes, menus, and widgets.
 */

import { hasPermission } from '../rbac.js';

class ModuleRegistry {
  constructor() {
    this.modules = new Map();
    this.routes = [];
    this.menuItems = [];
    this.widgets = [];
  }

  /**
   * Register a module
   *
   * @param {BaseModule} moduleInstance - Module instance to register
   */
  register(moduleInstance) {
    const name = moduleInstance.name;

    if (this.modules.has(name)) {
      console.warn(`Module ${name} is already registered`);
      return;
    }

    this.modules.set(name, moduleInstance);
    console.log(`Registered module: ${name}`);

    // Update routes and menus
    this._updateRoutes();
    this._updateMenuItems();
  }

  /**
   * Unregister a module
   *
   * @param {string} moduleName - Name of module to unregister
   * @returns {boolean} True if unregistered, false if not found
   */
  unregister(moduleName) {
    if (!this.modules.has(moduleName)) {
      return false;
    }

    this.modules.delete(moduleName);
    console.log(`Unregistered module: ${moduleName}`);

    // Update routes and menus
    this._updateRoutes();
    this._updateMenuItems();

    return true;
  }

  /**
   * Get a registered module
   *
   * @param {string} moduleName - Name of the module
   * @returns {BaseModule|null} Module instance or null
   */
  getModule(moduleName) {
    return this.modules.get(moduleName) || null;
  }

  /**
   * Get all registered modules
   *
   * @returns {Array<BaseModule>} Array of module instances
   */
  getAllModules() {
    return Array.from(this.modules.values());
  }

  /**
   * Get all routes from registered modules
   *
   * @returns {Array<Object>} Array of route objects
   */
  getAllRoutes() {
    return this.routes;
  }

  /**
   * Get all accessible routes (filtered by permissions)
   *
   * @returns {Promise<Array<Object>>} Routes user can access
   */
  async getAccessibleRoutes() {
    const accessibleRoutes = [];

    for (const route of this.routes) {
      // If no permission required, include it
      if (!route.permission) {
        accessibleRoutes.push(route);
        continue;
      }

      // Check permission
      const hasAccess = await hasPermission(route.permission);
      if (hasAccess) {
        accessibleRoutes.push(route);
      }
    }

    return accessibleRoutes;
  }

  /**
   * Find a route by path
   *
   * @param {string} path - Route path
   * @returns {Object|null} Route object or null
   */
  findRoute(path) {
    return this.routes.find(r => r.path === path) || null;
  }

  /**
   * Get all menu items from registered modules
   *
   * @returns {Array<Object>} Array of menu items
   */
  getAllMenuItems() {
    return this.menuItems;
  }

  /**
   * Get accessible menu items (filtered by permissions)
   *
   * @returns {Promise<Array<Object>>} Menu items user can access
   */
  async getAccessibleMenuItems() {
    const accessibleItems = [];

    for (const item of this.menuItems) {
      // If no permission required, include it
      if (!item.permission) {
        accessibleItems.push(item);
        continue;
      }

      // Check permission
      const hasAccess = await hasPermission(item.permission);
      if (hasAccess) {
        accessibleItems.push(item);
      }
    }

    return accessibleItems;
  }

  /**
   * Build hierarchical menu structure
   *
   * @param {Array<Object>} flatMenuItems - Flat array of menu items
   * @returns {Array<Object>} Hierarchical menu structure
   */
  buildMenuHierarchy(flatMenuItems) {
    const menuMap = new Map();
    const rootItems = [];

    // First pass: Create all items
    for (const item of flatMenuItems) {
      const menuItem = {
        ...item,
        children: []
      };
      menuMap.set(item.path, menuItem);
    }

    // Second pass: Build hierarchy
    for (const item of flatMenuItems) {
      const menuItem = menuMap.get(item.path);

      if (item.menu && item.menu.parent) {
        // Find parent and add as child
        const parentPath = item.menu.parent;
        const parent = Array.from(menuMap.values()).find(
          m => m.menu?.label === parentPath || m.path === parentPath
        );

        if (parent) {
          parent.children.push(menuItem);
        } else {
          // Parent not found, add to root
          rootItems.push(menuItem);
        }
      } else {
        // No parent, add to root
        rootItems.push(menuItem);
      }
    }

    return rootItems;
  }

  /**
   * Get dashboard widgets from all modules
   *
   * @returns {Array<Object>} Array of widget configurations
   */
  getDashboardWidgets() {
    const widgets = [];

    for (const module of this.modules.values()) {
      const navigation = module.manifest.navigation || {};
      const dashboardWidgets = navigation.dashboard_widgets || [];

      for (const widget of dashboardWidgets) {
        widgets.push({
          ...widget,
          moduleName: module.name,
          moduleDisplayName: module.displayName
        });
      }
    }

    return widgets;
  }

  /**
   * Get accessible dashboard widgets (filtered by permissions)
   *
   * @returns {Promise<Array<Object>>} Widgets user can access
   */
  async getAccessibleDashboardWidgets() {
    const widgets = this.getDashboardWidgets();
    const accessibleWidgets = [];

    for (const widget of widgets) {
      // If no permission required, include it
      if (!widget.permission) {
        accessibleWidgets.push(widget);
        continue;
      }

      // Check permission
      const hasAccess = await hasPermission(widget.permission);
      if (hasAccess) {
        accessibleWidgets.push(widget);
      }
    }

    return accessibleWidgets;
  }

  /**
   * Check if a module is registered
   *
   * @param {string} moduleName - Name of the module
   * @returns {boolean} True if registered
   */
  isModuleRegistered(moduleName) {
    return this.modules.has(moduleName);
  }

  /**
   * Get module count
   *
   * @returns {number} Number of registered modules
   */
  getModuleCount() {
    return this.modules.size;
  }

  /**
   * Update routes from all modules
   * @private
   */
  _updateRoutes() {
    this.routes = [];

    for (const module of this.modules.values()) {
      const moduleRoutes = module.getRoutes();
      for (const route of moduleRoutes) {
        this.routes.push({
          ...route,
          moduleName: module.name,
          moduleDisplayName: module.displayName
        });
      }
    }

    console.log(`Updated routes: ${this.routes.length} total`);
  }

  /**
   * Update menu items from all modules
   * @private
   */
  _updateMenuItems() {
    this.menuItems = [];

    for (const module of this.modules.values()) {
      const moduleMenuItems = module.getMenuItems();
      for (const item of moduleMenuItems) {
        this.menuItems.push({
          ...item,
          moduleName: module.name,
          moduleDisplayName: module.displayName
        });
      }
    }

    // Sort by order
    this.menuItems.sort((a, b) => (a.order || 999) - (b.order || 999));

    console.log(`Updated menu items: ${this.menuItems.length} total`);
  }

  /**
   * Clear all registered modules
   */
  clear() {
    for (const module of this.modules.values()) {
      if (typeof module.cleanup === 'function') {
        module.cleanup();
      }
    }

    this.modules.clear();
    this.routes = [];
    this.menuItems = [];
    this.widgets = [];

    console.log('Cleared all registered modules');
  }

  /**
   * Get registry statistics
   *
   * @returns {Object} Statistics object
   */
  getStatistics() {
    return {
      moduleCount: this.modules.size,
      routeCount: this.routes.length,
      menuItemCount: this.menuItems.length,
      widgetCount: this.getDashboardWidgets().length,
      modules: Array.from(this.modules.keys())
    };
  }
}

// Create and export singleton instance
export const moduleRegistry = new ModuleRegistry();
export default moduleRegistry;
