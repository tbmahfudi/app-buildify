/**
 * Base Module Class
 *
 * All frontend modules should extend this class.
 * Provides lifecycle management, route registration, and utility methods.
 */

import { hasPermission } from '../rbac.js';

export class BaseModule {
  /**
   * @param {Object} manifest - Module manifest data
   */
  constructor(manifest) {
    this.manifest = manifest;
    this.name = manifest.name;
    this.displayName = manifest.display_name;
    this.version = manifest.version;
    this.description = manifest.description;
    this.routes = [];
    this.components = new Map();
    this.initialized = false;
  }

  /**
   * Initialize the module
   * Override this method to add custom initialization logic
   *
   * @returns {Promise<void>}
   */
  async init() {
    if (this.initialized) {
      console.warn(`Module ${this.name} already initialized`);
      return;
    }

    console.log(`Initializing module: ${this.name}`);

    // Register routes from manifest
    this.registerRoutes();

    // Load any assets specified in manifest
    await this.loadAssets();

    this.initialized = true;
    console.log(`✓ Module ${this.name} initialized`);
  }

  /**
   * Register module routes from manifest
   * @private
   */
  registerRoutes() {
    if (!this.manifest.routes) {
      return;
    }

    this.routes = this.manifest.routes.map(route => ({
      path: route.path,
      name: route.name,
      component: route.component,
      permission: route.permission,
      menu: route.menu,
      handler: async () => {
        // Load page component dynamically
        return await this.loadPage(route.component);
      }
    }));

    console.log(`Registered ${this.routes.length} routes for ${this.name}`);
  }

  /**
   * Load assets (CSS, icons) specified in manifest
   * @private
   */
  async loadAssets() {
    const assets = this.manifest.assets || {};

    // Load CSS files
    if (assets.css && Array.isArray(assets.css)) {
      for (const cssFile of assets.css) {
        await this.loadCSS(cssFile);
      }
    }
  }

  /**
   * Load a CSS file
   *
   * @param {string} cssPath - Relative path to CSS file
   * @returns {Promise<void>}
   */
  async loadCSS(cssPath) {
    return new Promise((resolve, reject) => {
      const fullPath = `/modules/${this.name}/${cssPath}`;
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = fullPath;

      link.onload = () => {
        console.log(`Loaded CSS: ${fullPath}`);
        resolve();
      };

      link.onerror = () => {
        console.error(`Failed to load CSS: ${fullPath}`);
        reject(new Error(`Failed to load CSS: ${fullPath}`));
      };

      document.head.appendChild(link);
    });
  }

  /**
   * Load a page component dynamically
   *
   * @param {string} componentPath - Relative path to component
   * @returns {Promise<Object|null>} Page component
   */
  async loadPage(componentPath) {
    try {
      const fullPath = `/modules/${this.name}/${componentPath}`;
      console.log(`Loading page: ${fullPath}`);

      const module = await import(fullPath);
      const PageClass = module.default || module;

      if (!PageClass) {
        throw new Error(`No default export found in ${fullPath}`);
      }

      return new PageClass();
    } catch (error) {
      console.error(`Error loading page ${componentPath}:`, error);
      return null;
    }
  }

  /**
   * Load a component dynamically
   *
   * @param {string} componentPath - Relative path to component
   * @returns {Promise<Object|null>} Component
   */
  async loadComponent(componentPath) {
    // Check cache
    if (this.components.has(componentPath)) {
      return this.components.get(componentPath);
    }

    try {
      const fullPath = `/modules/${this.name}/${componentPath}`;
      const module = await import(fullPath);
      const Component = module.default || module;

      // Cache component
      this.components.set(componentPath, Component);

      return Component;
    } catch (error) {
      console.error(`Error loading component ${componentPath}:`, error);
      return null;
    }
  }

  /**
   * Get all routes for this module
   *
   * @returns {Array<Object>} Array of route objects
   */
  getRoutes() {
    return this.routes;
  }

  /**
   * Get menu items from routes
   *
   * @returns {Array<Object>} Array of menu items
   */
  getMenuItems() {
    return this.routes
      .filter(route => route.menu)
      .map(route => ({
        ...route.menu,
        path: route.path,
        name: route.name,
        permission: route.permission
      }));
  }

  /**
   * Check if user has permission to access a route
   *
   * @param {string} routePath - Route path to check
   * @returns {Promise<boolean>} True if user has permission
   */
  async canAccessRoute(routePath) {
    const route = this.routes.find(r => r.path === routePath);

    if (!route) {
      console.warn(`Route ${routePath} not found in module ${this.name}`);
      return false;
    }

    // If no permission required, allow access
    if (!route.permission) {
      return true;
    }

    // Check permission using core RBAC system
    return await hasPermission(route.permission);
  }

  /**
   * Get filtered routes based on user permissions
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
   * Get filtered menu items based on user permissions
   *
   * @returns {Promise<Array<Object>>} Menu items user can access
   */
  async getAccessibleMenuItems() {
    const menuItems = this.getMenuItems();
    const accessibleItems = [];

    for (const item of menuItems) {
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
   * Make an API request to this module's backend
   *
   * @param {string} endpoint - Endpoint path (relative to module API prefix)
   * @param {Object} options - Fetch options
   * @returns {Promise<Response>} Fetch response
   */
  async apiRequest(endpoint, options = {}) {
    const apiPrefix = this.manifest.api?.prefix || `/api/v1/${this.name}`;
    const url = `${apiPrefix}${endpoint}`;

    // Add auth token if available
    const token = localStorage.getItem('token');
    const headers = {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    return await fetch(url, {
      ...options,
      headers
    });
  }

  /**
   * Get module configuration from backend
   *
   * @returns {Promise<Object|null>} Module configuration
   */
  async getConfiguration() {
    try {
      const response = await fetch(`/api/v1/modules/${this.name}/configuration`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        return await response.json();
      }

      return null;
    } catch (error) {
      console.error(`Error fetching configuration for ${this.name}:`, error);
      return null;
    }
  }

  /**
   * Cleanup method called when module is unloaded
   * Override this to add custom cleanup logic
   */
  cleanup() {
    console.log(`Cleaning up module: ${this.name}`);
    this.components.clear();
    this.routes = [];
    this.initialized = false;
  }

  /**
   * Get module info
   *
   * @returns {Object} Module information
   */
  getInfo() {
    return {
      name: this.name,
      displayName: this.displayName,
      version: this.version,
      description: this.description,
      category: this.manifest.category,
      author: this.manifest.author,
      initialized: this.initialized,
      routeCount: this.routes.length
    };
  }

  /**
   * String representation
   *
   * @returns {string}
   */
  toString() {
    return `${this.constructor.name}(name=${this.name}, version=${this.version})`;
  }
}

export default BaseModule;
