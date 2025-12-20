/**
 * Module Manager Page
 *
 * UI for managing modules - viewing available modules, enabling/disabling for tenant.
 */

import { getAuthToken, apiFetch } from './api.js';
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
    const container = document.getElementById('content');
    if (!container) return;

    // Check permission
    const canManage = await hasPermission('modules:manage:tenant');

    container.innerHTML = `
      <div class="module-manager">
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-2xl font-bold">Module Management</h1>
          ${canManage ? `
            <button id="sync-modules-btn" class="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-medium transition">
              <span class="icon">🔄</span>
              Sync Modules
            </button>
          ` : ''}
        </div>

        ${!canManage ? `
          <div class="bg-amber-50 border border-amber-200 text-amber-800 px-4 py-3 rounded-lg">
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
      const response = await apiFetch('/modules/available');

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
        <div class="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg">
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
      <div class="bg-white rounded-lg border border-gray-200 shadow-sm module-card" data-module="${module.name}">
        <div class="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
          <h3 class="text-lg font-semibold">${module.display_name}</h3>
          <span class="px-2 py-1 text-xs font-medium rounded-full ${this.getStatusBadgeClasses(module.status)}">
            ${module.status}
          </span>
        </div>
        <div class="p-4">
          <p class="text-sm text-gray-600 mb-2">${module.description || 'No description available'}</p>

          <div class="flex items-center gap-2 text-xs text-gray-500 mb-3">
            <span class="px-2 py-1 bg-gray-100 rounded text-gray-700">${module.category || 'general'}</span>
            <span>v${module.version}</span>
            ${module.subscription_tier ? `
              <span class="px-2 py-1 bg-amber-100 text-amber-700 rounded">${module.subscription_tier}</span>
            ` : ''}
          </div>

          <div class="flex gap-2">
            ${!module.is_installed ? `
              <button class="px-3 py-1.5 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition" onclick="moduleManager.installModule('${module.name}')">
                Install
              </button>
            ` : module.is_core ? `
              <span class="text-xs text-gray-500">Core Module</span>
            ` : `
              <button class="px-3 py-1.5 text-sm bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition" onclick="moduleManager.enableModule('${module.name}')">
                Enable
              </button>
              <button class="px-3 py-1.5 text-sm bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition" onclick="moduleManager.uninstallModule('${module.name}')">
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
      const response = await apiFetch('/modules/enabled');

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
        <div class="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg">
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
      <div class="bg-white rounded-lg border border-gray-200 shadow-sm">
        <div class="p-4">
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <h3 class="text-lg font-semibold mb-1">${module.display_name}</h3>
              <p class="text-sm text-gray-600 mb-2">Version ${module.version}</p>
              <p class="text-xs text-gray-500">
                Enabled: ${new Date(module.enabled_at).toLocaleDateString()}
              </p>
            </div>
            <div class="flex gap-2">
              <button class="px-3 py-1.5 text-sm bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-medium transition" onclick="moduleManager.configureModule('${module.module_name}')">
                Configure
              </button>
              <button class="px-3 py-1.5 text-sm bg-amber-600 hover:bg-amber-700 text-white rounded-lg font-medium transition" onclick="moduleManager.disableModule('${module.module_name}')">
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
      const response = await apiFetch('/modules/install', {
        method: 'POST',
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
      const response = await apiFetch('/modules/uninstall', {
        method: 'POST',
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
      const response = await apiFetch('/modules/enable', {
        method: 'POST',
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
      const response = await apiFetch('/modules/disable', {
        method: 'POST',
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
      const response = await apiFetch('/modules/sync', {
        method: 'POST'
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
   * Get status badge color (legacy)
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

  /**
   * Get status badge Tailwind classes
   */
  getStatusBadgeClasses(status) {
    const classes = {
      'stable': 'bg-green-100 text-green-700',
      'beta': 'bg-amber-100 text-amber-700',
      'available': 'bg-blue-100 text-blue-700',
      'deprecated': 'bg-red-100 text-red-700'
    };
    return classes[status] || 'bg-gray-100 text-gray-700';
  }
}

// Export singleton instance
export const moduleManager = new ModuleManager();

// Make available globally for onclick handlers
window.moduleManager = moduleManager;
