/**
 * Enhanced Module Manager Page
 *
 * UI for managing modules with improved styling and UX
 */

import { apiFetch } from './api.js';
import { hasPermission, isSuperuser } from './rbac.js';
import { showToast } from './ui-utils.js';

export class ModuleManager {
  constructor() {
    this.availableModules = [];
    this.enabledModules = [];
    this.tenants = [];
  }

  /**
   * Render the module manager page
   */
  async render() {
    const container = document.getElementById('content');
    if (!container) return;

    // Check permissions
    const canManage = await hasPermission('modules:manage:tenant');
    const isSuperUser = isSuperuser();

    container.innerHTML = `
      <div class="module-manager px-6 py-8 max-w-7xl mx-auto">
        <!-- Header -->
        <div class="flex items-center justify-between mb-8">
          <div>
            <h1 class="text-3xl font-bold text-gray-900 flex items-center gap-3">
              <i class="ph ph-package text-blue-600"></i>
              Module Management
            </h1>
            <p class="text-gray-600 mt-2">Install and configure modules for your platform</p>
          </div>
          ${isSuperUser ? `
            <button id="sync-modules-btn" class="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition shadow-sm">
              <i class="ph ph-arrows-clockwise"></i>
              <span>Sync Modules</span>
            </button>
          ` : ''}
        </div>

        ${!canManage ? `
          <div class="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6 rounded-r-lg">
            <div class="flex items-center gap-3">
              <i class="ph ph-warning text-yellow-600 text-xl"></i>
              <p class="text-yellow-800">You don't have permission to manage modules.</p>
            </div>
          </div>
        ` : ''}

        ${isSuperUser ? `
          <div class="bg-blue-50 border-l-4 border-blue-400 p-4 mb-6 rounded-r-lg">
            <div class="flex items-center gap-3">
              <i class="ph ph-shield-check text-blue-600 text-xl"></i>
              <div>
                <p class="text-blue-900 font-medium">Superuser Mode</p>
                <p class="text-blue-700 text-sm">You can install/uninstall modules platform-wide</p>
              </div>
            </div>
          </div>
        ` : ''}

        <!-- Tabs -->
        <div class="border-b border-gray-200 mb-6">
          <div class="flex gap-4">
            <button class="tab-btn active px-4 py-3 font-medium text-blue-600 border-b-2 border-blue-600 transition" data-tab="available">
              Available Modules
            </button>
            <button class="tab-btn px-4 py-3 font-medium text-gray-600 hover:text-gray-900 border-b-2 border-transparent hover:border-gray-300 transition" data-tab="enabled">
              Enabled Modules
            </button>
          </div>
        </div>

        <!-- Available Modules Tab -->
        <div id="available-tab" class="tab-content active">
          <div class="mb-6">
            <div class="relative">
              <i class="ph ph-magnifying-glass absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"></i>
              <input type="text" id="search-modules" placeholder="Search modules by name, category, or description..."
                     class="pl-10 pr-4 py-2 border border-gray-300 rounded-lg w-full focus:ring-2 focus:ring-blue-500 focus:border-transparent transition" />
            </div>
          </div>

          <div id="available-modules-loading" class="text-center py-16">
            <div class="inline-block">
              <div class="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            </div>
            <p class="mt-4 text-gray-600 font-medium">Loading modules...</p>
          </div>

          <div id="available-modules-list" class="hidden grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          </div>
        </div>

        <!-- Enabled Modules Tab -->
        <div id="enabled-tab" class="tab-content hidden">
          <div id="enabled-modules-loading" class="text-center py-16">
            <div class="inline-block">
              <div class="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            </div>
            <p class="mt-4 text-gray-600 font-medium">Loading enabled modules...</p>
          </div>

          <div id="enabled-modules-list" class="hidden space-y-4">
          </div>
        </div>
      </div>
    `;

    // Setup event listeners
    this.setupEventListeners();

    // Load tenants if superuser
    if (isSuperUser) {
      await this.loadTenants();
    }

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
      if (btn.dataset.tab === tabName) {
        btn.classList.add('active', 'text-blue-600', 'border-blue-600');
        btn.classList.remove('text-gray-600', 'border-transparent');
      } else {
        btn.classList.remove('active', 'text-blue-600', 'border-blue-600');
        btn.classList.add('text-gray-600', 'border-transparent');
      }
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
      const response = await apiFetch('/module-registry/available');

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
        <div class="bg-red-50 border-l-4 border-red-500 p-4 rounded-r-lg">
          <div class="flex items-center gap-3">
            <i class="ph ph-x-circle text-red-600 text-xl"></i>
            <div>
              <p class="text-red-900 font-medium">Failed to load modules</p>
              <p class="text-red-700 text-sm">${error.message}</p>
            </div>
          </div>
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
    const isSuperUser = isSuperuser();

    if (modules.length === 0) {
      list.innerHTML = `
        <div class="col-span-full text-center py-16">
          <i class="ph ph-package text-gray-300 text-6xl"></i>
          <p class="text-gray-500 mt-4">No modules found</p>
        </div>
      `;
      return;
    }

    list.innerHTML = modules.map(module => `
      <div class="bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition overflow-hidden" data-module="${module.name}">
        <!-- Module Header -->
        <div class="p-5 border-b border-gray-100">
          <div class="flex items-start justify-between mb-2">
            <h3 class="text-lg font-semibold text-gray-900">${module.display_name}</h3>
            ${this.getStatusBadge(module)}
          </div>
          <p class="text-sm text-gray-600 line-clamp-2">${module.description || 'No description available'}</p>
        </div>

        <!-- Module Body -->
        <div class="p-5">
          <div class="flex items-center gap-2 mb-4 flex-wrap">
            <span class="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-md">
              <i class="ph ph-tag"></i>
              ${module.category || 'general'}
            </span>
            <span class="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-md">
              <i class="ph ph-git-branch"></i>
              v${module.version}
            </span>
            ${module.subscription_tier ? `
              <span class="inline-flex items-center gap-1 px-2 py-1 bg-amber-100 text-amber-700 text-xs rounded-md">
                <i class="ph ph-crown"></i>
                ${module.subscription_tier}
              </span>
            ` : ''}
          </div>

          <!-- Actions -->
          <div class="flex gap-2">
            ${!module.is_installed ? `
              ${isSuperUser ? `
                <button class="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition text-sm font-medium"
                        onclick="moduleManager.installModule('${module.name}')">
                  <i class="ph ph-download-simple"></i>
                  Install
                </button>
              ` : `
                <div class="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-gray-100 text-gray-500 rounded-lg text-sm">
                  <i class="ph ph-lock"></i>
                  Not Installed
                </div>
              `}
            ` : module.is_core ? `
              <div class="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-gray-100 text-gray-600 rounded-lg text-sm">
                <i class="ph ph-shield-checkered"></i>
                Core Module
              </div>
            ` : `
              <button class="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition text-sm font-medium"
                      onclick="moduleManager.showEnableModuleModal('${module.name}')">
                <i class="ph ph-check-circle"></i>
                Enable
              </button>
              ${isSuperUser ? `
                <button class="flex items-center justify-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition text-sm font-medium"
                        onclick="moduleManager.uninstallModule('${module.name}')">
                  <i class="ph ph-trash"></i>
                </button>
              ` : ''}
            `}
          </div>
        </div>
      </div>
    `).join('');
  }

  /**
   * Get status badge HTML
   */
  getStatusBadge(module) {
    const statusConfig = {
      'stable': { color: 'bg-green-100 text-green-700', icon: 'ph-check-circle' },
      'beta': { color: 'bg-yellow-100 text-yellow-700', icon: 'ph-warning' },
      'available': { color: 'bg-blue-100 text-blue-700', icon: 'ph-info' },
      'deprecated': { color: 'bg-red-100 text-red-700', icon: 'ph-x-circle' }
    };

    const config = statusConfig[module.status] || statusConfig['available'];

    return `
      <span class="inline-flex items-center gap-1 px-2 py-1 ${config.color} text-xs font-medium rounded-md">
        <i class="ph ${config.icon}"></i>
        ${module.status}
      </span>
    `;
  }

  /**
   * Load enabled modules for tenant
   */
  async loadEnabledModules() {
    const loading = document.getElementById('enabled-modules-loading');
    const list = document.getElementById('enabled-modules-list');
    const isSuperUser = isSuperuser();

    try {
      // Superusers see all tenant modules, regular users see only their tenant's modules
      const endpoint = isSuperUser ? '/module-registry/enabled/all-tenants' : '/module-registry/enabled';
      console.log(`Loading enabled modules from endpoint: ${endpoint} (superuser: ${isSuperUser})`);

      const response = await apiFetch(endpoint);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error('Failed to load enabled modules:', response.status, errorData);
        throw new Error(errorData.detail || 'Failed to load enabled modules');
      }

      const data = await response.json();
      console.log('Enabled modules response:', data);
      this.enabledModules = data.modules || [];
      console.log(`Loaded ${this.enabledModules.length} enabled modules`);

      // Hide loading, show list
      loading.classList.add('hidden');
      list.classList.remove('hidden');

      // Render enabled modules
      this.renderEnabledModules();
    } catch (error) {
      console.error('Error loading enabled modules:', error);
      loading.innerHTML = `
        <div class="bg-red-50 border-l-4 border-red-500 p-4 rounded-r-lg">
          <div class="flex items-center gap-3">
            <i class="ph ph-x-circle text-red-600 text-xl"></i>
            <div>
              <p class="text-red-900 font-medium">Failed to load enabled modules</p>
              <p class="text-red-700 text-sm">${error.message}</p>
            </div>
          </div>
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

    const isSuperUser = isSuperuser();

    if (this.enabledModules.length === 0) {
      list.innerHTML = `
        <div class="text-center py-16">
          <i class="ph ph-package text-gray-300 text-6xl"></i>
          <p class="text-gray-500 mt-4 text-lg">No modules enabled</p>
          <p class="text-gray-400 text-sm mt-2">Enable modules from the Available Modules tab</p>
        </div>
      `;
      return;
    }

    list.innerHTML = this.enabledModules.map(module => `
      <div class="bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition p-5">
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <div class="flex items-center gap-3 mb-2">
              <h3 class="text-lg font-semibold text-gray-900">${module.display_name}</h3>
              <span class="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded-md">
                <i class="ph ph-check-circle"></i>
                Enabled
              </span>
              ${module.tenant_name ? `
                <span class="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded-md">
                  <i class="ph ph-building"></i>
                  ${module.tenant_name}
                </span>
              ` : ''}
            </div>
            <div class="flex items-center gap-4 text-sm text-gray-600 mb-3 flex-wrap">
              <span class="flex items-center gap-1">
                <i class="ph ph-git-branch"></i>
                Version ${module.version}
              </span>
              <span class="flex items-center gap-1">
                <i class="ph ph-calendar"></i>
                Enabled ${new Date(module.enabled_at).toLocaleDateString()}
              </span>
              ${module.tenant_code ? `
                <span class="flex items-center gap-1">
                  <i class="ph ph-tag"></i>
                  ${module.tenant_code}
                </span>
              ` : ''}
            </div>
          </div>
          <div class="flex gap-2">
            <button class="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition text-sm font-medium"
                    onclick="moduleManager.configureModule('${module.module_name}')">
              <i class="ph ph-gear"></i>
              Configure
            </button>
            <button class="flex items-center gap-2 px-4 py-2 bg-yellow-100 text-yellow-700 rounded-lg hover:bg-yellow-200 transition text-sm font-medium"
                    onclick="moduleManager.disableModule('${module.module_name}', '${module.tenant_id || ''}')">
              <i class="ph ph-power"></i>
              Disable
            </button>
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
    if (!confirm(`Install module "${moduleName}"?\n\nThis will make the module available platform-wide.`)) return;

    try {
      const response = await apiFetch('/module-registry/install', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ module_name: moduleName })
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || 'Installation failed');
      }

      showToast(`Module "${moduleName}" installed successfully!`, 'success');
      await this.loadAvailableModules();
    } catch (error) {
      showToast(`Error installing module: ${error.message}`, 'error');
    }
  }

  /**
   * Uninstall a module
   */
  async uninstallModule(moduleName) {
    if (!confirm(`Uninstall module "${moduleName}"?\n\nThis will remove the module platform-wide. This action cannot be undone.`)) return;

    try {
      const response = await apiFetch('/module-registry/uninstall', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ module_name: moduleName })
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || 'Uninstallation failed');
      }

      showToast(`Module "${moduleName}" uninstalled successfully!`, 'success');
      await this.loadAvailableModules();
    } catch (error) {
      showToast(`Error uninstalling module: ${error.message}`, 'error');
    }
  }

  /**
   * Load tenants list (for superusers)
   */
  async loadTenants() {
    try {
      const response = await apiFetch('/org/tenants');

      if (!response.ok) {
        throw new Error('Failed to load tenants');
      }

      const data = await response.json();
      this.tenants = data.items || [];
      console.log(`Loaded ${this.tenants.length} tenants`);
    } catch (error) {
      console.error('Error loading tenants:', error);
      this.tenants = [];
    }
  }

  /**
   * Show tenant selection modal and enable module
   */
  async showEnableModuleModal(moduleName) {
    const isSuperUser = isSuperuser();

    // If not a superuser or no tenants, enable for current tenant directly
    if (!isSuperUser || this.tenants.length === 0) {
      return this.enableModule(moduleName, null);
    }

    // Show modal for tenant selection
    const modalHtml = `
      <div id="enable-module-modal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
          <div class="p-6 border-b border-gray-200">
            <h3 class="text-xl font-semibold text-gray-900">Enable Module</h3>
            <p class="text-sm text-gray-600 mt-1">Select a tenant to enable "${moduleName}" for</p>
          </div>

          <div class="p-6">
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Select Tenant
            </label>
            <select id="tenant-select" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
              <option value="">Current Tenant (Default)</option>
              ${this.tenants.map(tenant => `
                <option value="${tenant.id}">${tenant.name} (${tenant.code})</option>
              `).join('')}
            </select>

            <div class="mt-4 p-3 bg-blue-50 border-l-4 border-blue-400 rounded-r-lg">
              <p class="text-sm text-blue-800">
                <strong>Note:</strong> As a superuser, you can enable modules for any tenant.
                Leave as "Current Tenant" to enable for your own tenant.
              </p>
            </div>
          </div>

          <div class="p-6 border-t border-gray-200 flex gap-3 justify-end">
            <button id="cancel-enable" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition font-medium">
              Cancel
            </button>
            <button id="confirm-enable" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium">
              Enable Module
            </button>
          </div>
        </div>
      </div>
    `;

    // Add modal to page
    const modalContainer = document.createElement('div');
    modalContainer.innerHTML = modalHtml;
    document.body.appendChild(modalContainer);

    // Setup modal event listeners
    const modal = document.getElementById('enable-module-modal');
    const tenantSelect = document.getElementById('tenant-select');
    const cancelBtn = document.getElementById('cancel-enable');
    const confirmBtn = document.getElementById('confirm-enable');

    const closeModal = () => {
      modalContainer.remove();
    };

    cancelBtn.addEventListener('click', closeModal);
    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeModal();
    });

    confirmBtn.addEventListener('click', async () => {
      const selectedTenantId = tenantSelect.value || null;
      closeModal();
      await this.enableModule(moduleName, selectedTenantId);
    });
  }

  /**
   * Enable a module for tenant
   */
  async enableModule(moduleName, tenantId = null) {
    try {
      const requestBody = { module_name: moduleName };

      // Add tenant_id if provided
      if (tenantId) {
        requestBody.tenant_id = tenantId;
      }

      const response = await apiFetch('/module-registry/enable', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || 'Enable failed');
      }

      showToast(`Module "${moduleName}" enabled successfully! Reloading page...`, 'success');
      await this.loadEnabledModules();

      // Reload page to load new module
      setTimeout(() => window.location.reload(), 2000);
    } catch (error) {
      showToast(`Error enabling module: ${error.message}`, 'error');
    }
  }

  /**
   * Disable a module for tenant
   */
  async disableModule(moduleName) {
    if (!confirm(`Disable module "${moduleName}"?\n\nThis will remove the module from your tenant.`)) return;

    try {
      const response = await apiFetch('/module-registry/disable', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ module_name: moduleName })
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || 'Disable failed');
      }

      showToast(`Module "${moduleName}" disabled successfully! Reloading page...`, 'success');
      await this.loadEnabledModules();

      // Reload page to unload module
      setTimeout(() => window.location.reload(), 2000);
    } catch (error) {
      showToast(`Error disabling module: ${error.message}`, 'error');
    }
  }

  /**
   * Configure a module
   */
  configureModule(moduleName) {
    showToast(`Module configuration UI for "${moduleName}" - Coming soon`, 'info');
    // TODO: Implement configuration UI with modal
  }

  /**
   * Sync modules from filesystem
   */
  async syncModules() {
    if (!confirm('Sync modules from filesystem?\n\nThis will discover new modules and update existing ones.')) return;

    try {
      showToast('Syncing modules...', 'info');

      const response = await apiFetch('/module-registry/sync', {
        method: 'POST'
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || 'Sync failed');
      }

      showToast('Modules synced successfully!', 'success');
      await this.loadAvailableModules();
    } catch (error) {
      showToast(`Error syncing modules: ${error.message}`, 'error');
    }
  }
}

// Export singleton instance
export const moduleManager = new ModuleManager();

// Make available globally for onclick handlers
window.moduleManager = moduleManager;
