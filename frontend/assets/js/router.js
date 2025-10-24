/**
 * Unified Router for NoCode Platform
 * Handles hash-based routing with proper guards
 */

class Router {
  constructor() {
    this.routes = new Map();
    this.currentRoute = null;
    this.beforeEach = null;
  }

  /**
   * Register a route
   */
  addRoute(path, handler) {
    this.routes.set(path, handler);
  }

  /**
   * Set navigation guard
   */
  setBeforeEach(guard) {
    this.beforeEach = guard;
  }

  /**
   * Navigate to a route
   */
  async navigate(path) {
    // Run guard
    if (this.beforeEach) {
      const canNavigate = await this.beforeEach(path);
      if (!canNavigate) {
        console.warn(`Navigation to ${path} blocked by guard`);
        return;
      }
    }

    // Get handler
    const handler = this.routes.get(path) || this.routes.get('404');
    
    if (!handler) {
      console.error(`No handler for route: ${path}`);
      return;
    }

    // Update current route
    this.currentRoute = path;

    // Execute handler
    try {
      await handler();
      
      // Dispatch event for route-specific JS
      document.dispatchEvent(new CustomEvent('route:loaded', { 
        detail: { route: path } 
      }));
    } catch (error) {
      console.error(`Error loading route ${path}:`, error);
      this.showError(error.message);
    }
  }

  /**
   * Load template from file
   */
  async loadTemplate(templateName) {
    const contentEl = document.getElementById('content');
    
    // Show loading state
    contentEl.innerHTML = `
      <div class="flex items-center justify-center h-full">
        <div class="text-center">
          <div class="inline-block">
            <div class="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
          </div>
          <p class="mt-3 text-gray-600">Loading...</p>
        </div>
      </div>
    `;

    try {
      const response = await fetch(`/assets/templates/${templateName}.html`);
      
      if (!response.ok) {
        throw new Error(`Template not found: ${templateName}`);
      }
      
      const html = await response.text();
      contentEl.innerHTML = html;
      
    } catch (error) {
      contentEl.innerHTML = `
        <div class="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <strong class="text-yellow-800">Page not found:</strong>
          <p class="text-yellow-700">${templateName}</p>
        </div>
      `;
      throw error;
    }
  }

  /**
   * Show error
   */
  showError(message) {
    const contentEl = document.getElementById('content');
    contentEl.innerHTML = `
      <div class="p-4 bg-red-50 border border-red-200 rounded-lg">
        <strong class="text-red-800">Error:</strong>
        <p class="text-red-700">${message}</p>
      </div>
    `;
  }

  /**
   * Initialize router
   */
  init() {
    // Handle hash changes
    window.addEventListener('hashchange', () => {
      const hash = window.location.hash.slice(1) || 'dashboard';
      this.navigate(hash);
    });

    // Handle initial load
    const initialRoute = window.location.hash.slice(1) || 'dashboard';
    this.navigate(initialRoute);
  }

  /**
   * Programmatic navigation
   */
  push(path) {
    window.location.hash = path;
  }
}

// Export singleton
export const router = new Router();