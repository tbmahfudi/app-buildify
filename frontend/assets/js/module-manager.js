/**
 * Module Manager Page
 *
 * UI for managing modules - viewing available modules, enabling/disabling for tenant.
 */

import { getAuthToken } from './api.js';
import { hasPermission } from './rbac.js';

export class ModuleManager {
  constructor() {
    this.availableModules = [];
    this.enabledModules = [];
  }

  /**
   * Render the module manager page
   */
  async render() {
    const container = document.getElementById('app-content');
    if (!container) return;

    // Check permission
    const canManage = await hasPermission('modules:manage:tenant');

    container.innerHTML = `
      <div class="module-manager">
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-2xl font-bold">Module Management</h1>
          ${canManage ? `
            <button id="sync-modules-btn" class="btn btn-secondary">
              <span class="icon">🔄</span>
              Sync Modules
            </button>
          ` : ''}
        </div>

        ${!canManage ? `
          <div class="alert alert-warning">
            You don't have permission to manage modules.
          </div>
        ` : ''}

        <!-- Tabs -->
        <div class="tabs mb-6">
          <button class="tab-btn active" data-tab="available">Available Modules</button>
          <button class="tab-btn" data-tab="enabled">Enabled Modules</button>
        </div>

        <!-- Available Modules Tab -->
        <div id="available-tab" class="tab-content active">
          <div class="mb-4">
            <input type="text" id="search-modules" placeholder="Search modules..."
                   class="input w-full md:w-1/3" />
          </div>

          <div id="available-modules-loading" class="text-center py-8">
            <div class="spinner"></div>
            <p>Loading modules...</p>
          </div>

          <div id="available-modules-list" class="hidden grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          </div>
        </div>

        <!-- Enabled Modules Tab -->
        <div id="enabled-tab" class="tab-content hidden">
          <div id="enabled-modules-loading" class="text-center py-8">
            <div class="spinner"></div>
            <p>Loading enabled modules...</p>
          </div>

          <div id="enabled-modules-list" class="hidden space-y-4">
          </div>
        </div>
      </div>
    `;

    // Setup event listeners
    this.setupEventListeners();

    // Load modules
    await this.loadAvailableModules();
    await this.loadEnabledModules();
  }

  /**
   * Setup event listeners
   */
  setupEventListeners() {
    // Tab switching
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
      btn.addEventListener('click', (e) => {
        const tab = e.currentTarget.dataset.tab;
        this.switchTab(tab);
      });
    });

    // Search
    const searchInput = document.getElementById('search-modules');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        this.filterModules(e.target.value);
      });
    }

    // Sync button
    const syncBtn = document.getElementById('sync-modules-btn');
    if (syncBtn) {
      syncBtn.addEventListener('click', () => this.syncModules());
    }
  }

  /**
   * Switch between tabs
   */
  switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.tab === tabName);
    });

    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
      content.classList.toggle('active', content.id === `${tabName}-tab`);
      content.classList.toggle('hidden', content.id !== `${tabName}-tab`);
    });
  }

  /**
   * Load available modules from backend
   */
  async loadAvailableModules() {
    const loading = document.getElementById('available-modules-loading');
    const list = document.getElementById('available-modules-list');

    try {
      const response = await fetch('/api/v1/modules/available', {
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to load modules');
      }

      const data = await response.json();
      this.availableModules = data.modules || [];

      // Hide loading, show list
      loading.classList.add('hidden');
      list.classList.remove('hidden');

      // Render modules
      this.renderAvailableModules();
    } catch (error) {
      console.error('Error loading modules:', error);
      loading.innerHTML = `
        <div class="alert alert-error">
          Failed to load modules: ${error.message}
        </div>
      `;
    }
  }

  /**
   * Render available modules
   */
  renderAvailableModules(filteredModules = null) {
    const list = document.getElementById('available-modules-list');
    if (!list) return;

    const modules = filteredModules || this.availableModules;

    if (modules.length === 0) {
      list.innerHTML = `
        <div class="col-span-full text-center py-8 text-gray-500">
          No modules found
        </div>
      `;
      return;
    }

    list.innerHTML = modules.map(module => `
      <div class="card module-card" data-module="${module.name}">
        <div class="card-header">
          <h3 class="text-lg font-semibold">${module.display_name}</h3>
          <span class="badge badge-${this.getStatusColor(module.status)}">
            ${module.status}
          </span>
        </div>
        <div class="card-body">
          <p class="text-sm text-gray-600 mb-2">${module.description || 'No description available'}</p>

          <div class="flex items-center gap-2 text-xs text-gray-500 mb-3">
            <span class="badge badge-sm">${module.category || 'general'}</span>
            <span>v${module.version}</span>
            ${module.subscription_tier ? `
              <span class="badge badge-sm badge-warning">${module.subscription_tier}</span>
            ` : ''}
          </div>

          <div class="flex gap-2">
            ${!module.is_installed ? `
              <button class="btn btn-primary btn-sm" onclick="moduleManager.installModule('${module.name}')">
                Install
              </button>
            ` : module.is_core ? `
              <span class="text-xs text-gray-500">Core Module</span>
            ` : `
              <button class="btn btn-success btn-sm" onclick="moduleManager.enableModule('${module.name}')">
                Enable
              </button>
              <button class="btn btn-error btn-sm" onclick="moduleManager.uninstallModule('${module.name}')">
                Uninstall
              </button>
            `}
          </div>
        </div>
      </div>
    `).join('');
  }

  /**
   * Load enabled modules for tenant
   */
  async loadEnabledModules() {
    const loading = document.getElementById('enabled-modules-loading');
    const list = document.getElementById('enabled-modules-list');

    try {
      const response = await fetch('/api/v1/modules/enabled', {
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to load enabled modules');
      }

      const data = await response.json();
      this.enabledModules = data.modules || [];

      // Hide loading, show list
      loading.classList.add('hidden');
      list.classList.remove('hidden');

      // Render enabled modules
      this.renderEnabledModules();
    } catch (error) {
      console.error('Error loading enabled modules:', error);
      loading.innerHTML = `
        <div class="alert alert-error">
          Failed to load enabled modules: ${error.message}
        </div>
      `;
    }
  }

  /**
   * Render enabled modules
   */
  renderEnabledModules() {
    const list = document.getElementById('enabled-modules-list');
    if (!list) return;

    if (this.enabledModules.length === 0) {
      list.innerHTML = `
        <div class="text-center py-8 text-gray-500">
          No modules enabled
        </div>
      `;
      return;
    }

    list.innerHTML = this.enabledModules.map(module => `
      <div class="card">
        <div class="card-body">
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <h3 class="text-lg font-semibold mb-1">${module.display_name}</h3>
              <p class="text-sm text-gray-600 mb-2">Version ${module.version}</p>
              <p class="text-xs text-gray-500">
                Enabled: ${new Date(module.enabled_at).toLocaleDateString()}
              </p>
            </div>
            <div class="flex gap-2">
              <button class="btn btn-sm btn-secondary" onclick="moduleManager.configureModule('${module.module_name}')">
                Configure
              </button>
              <button class="btn btn-sm btn-warning" onclick="moduleManager.disableModule('${module.module_name}')">
                Disable
              </button>
            </div>
          </div>
        </div>
      </div>
    `).join('');
  }

  /**
   * Filter modules by search term
   */
  filterModules(searchTerm) {
    const term = searchTerm.toLowerCase();
    const filtered = this.availableModules.filter(module =>
      module.name.toLowerCase().includes(term) ||
      module.display_name.toLowerCase().includes(term) ||
      (module.description && module.description.toLowerCase().includes(term)) ||
      (module.category && module.category.toLowerCase().includes(term))
    );

    this.renderAvailableModules(filtered);
  }

  /**
   * Install a module
   */
  async installModule(moduleName) {
    if (!confirm(`Install module "${moduleName}"?`)) return;

    try {
      const response = await fetch('/api/v1/modules/install', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ module_name: moduleName })
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || 'Installation failed');
      }

      alert(`Module "${moduleName}" installed successfully!`);
      await this.loadAvailableModules();
    } catch (error) {
      alert(`Error installing module: ${error.message}`);
    }
  }

  /**
   * Uninstall a module
   */
  async uninstallModule(moduleName) {
    if (!confirm(`Uninstall module "${moduleName}"? This cannot be undone.`)) return;

    try {
      const response = await fetch('/api/v1/modules/uninstall', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ module_name: moduleName })
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || 'Uninstallation failed');
      }

      alert(`Module "${moduleName}" uninstalled successfully!`);
      await this.loadAvailableModules();
    } catch (error) {
      alert(`Error uninstalling module: ${error.message}`);
    }
  }

  /**
   * Enable a module for tenant
   */
  async enableModule(moduleName) {
    try {
      const response = await fetch('/api/v1/modules/enable', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ module_name: moduleName })
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || 'Enable failed');
      }

      alert(`Module "${moduleName}" enabled successfully!`);
      await this.loadEnabledModules();

      // Reload page to load new module
      window.location.reload();
    } catch (error) {
      alert(`Error enabling module: ${error.message}`);
    }
  }

  /**
   * Disable a module for tenant
   */
  async disableModule(moduleName) {
    if (!confirm(`Disable module "${moduleName}"?`)) return;

    try {
      const response = await fetch('/api/v1/modules/disable', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ module_name: moduleName })
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || 'Disable failed');
      }

      alert(`Module "${moduleName}" disabled successfully!`);
      await this.loadEnabledModules();

      // Reload page to unload module
      window.location.reload();
    } catch (error) {
      alert(`Error disabling module: ${error.message}`);
    }
  }

  /**
   * Configure a module
   */
  configureModule(moduleName) {
    alert(`Module configuration UI for "${moduleName}" - To be implemented`);
    // TODO: Implement configuration UI
  }

  /**
   * Sync modules from filesystem
   */
  async syncModules() {
    if (!confirm('Sync modules from filesystem?')) return;

    try {
      const response = await fetch('/api/v1/modules/sync', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`
        }
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || 'Sync failed');
      }

      alert('Modules synced successfully!');
      await this.loadAvailableModules();
    } catch (error) {
      alert(`Error syncing modules: ${error.message}`);
    }
  }

  /**
   * Get status badge color
   */
  getStatusColor(status) {
    const colors = {
      'stable': 'success',
      'beta': 'warning',
      'available': 'info',
      'deprecated': 'error'
    };
    return colors[status] || 'secondary';
  }
}

// Export singleton instance
export const moduleManager = new ModuleManager();

// Make available globally for onclick handlers
window.moduleManager = moduleManager;
