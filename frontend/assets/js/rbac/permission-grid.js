/**
 * Permission Grid Component
 * Manages the permission management UI with CRUD checkboxes and special action badges
 */

import { rbacAPI } from './rbac-api.js';
import { modalManager } from './modal-controller.js';
import { showToast, showLoading, hideLoading } from '../ui-utils.js';

export class PermissionGrid {
  constructor() {
    this.state = {
      currentRoleId: null,
      originalPermissions: new Set(),
      currentPermissions: new Set(),
      groupedPermissions: [],
      filters: {
        category: '',
        scope: '',
        search: ''
      }
    };
    this.mode = 'modal'; // 'modal' or 'inline'
  }

  async open(roleId) {
    try {
      showLoading();

      // Get role details
      const role = await rbacAPI.getRole(roleId);

      // Get grouped permissions with role assignments
      const permsData = await rbacAPI.getGroupedPermissions({ role_id: roleId });

      // Initialize state
      this.state.currentRoleId = roleId;
      this.state.groupedPermissions = permsData.groups || [];
      this.state.originalPermissions = new Set();
      this.state.currentPermissions = new Set();

      // Collect all currently granted permissions
      permsData.groups.forEach(group => {
        ['standard_actions', 'special_actions'].forEach(actionType => {
          Object.values(group[actionType]).forEach(perm => {
            if (perm.granted) {
              this.state.originalPermissions.add(perm.id);
              this.state.currentPermissions.add(perm.id);
            }
          });
        });
      });

      // Show modal
      modalManager.open('permission-management-modal', {
        title: `Manage Permissions: ${role.name}`,
        content: this.render()
      });

      // Setup event listeners after rendering
      this.setupEventListeners();

    } catch (error) {
      console.error('Error loading permission management:', error);
      showToast('Failed to load permission management', 'error');
    } finally {
      hideLoading();
    }
  }

  async openInline(roleId) {
    try {
      this.mode = 'inline';
      showLoading();

      // Get role details
      const role = await rbacAPI.getRole(roleId);

      // Get grouped permissions with role assignments
      const permsData = await rbacAPI.getGroupedPermissions({ role_id: roleId });

      // Initialize state
      this.state.currentRoleId = roleId;
      this.state.groupedPermissions = permsData.groups || [];
      this.state.originalPermissions = new Set();
      this.state.currentPermissions = new Set();

      // Collect all currently granted permissions
      permsData.groups.forEach(group => {
        ['standard_actions', 'special_actions'].forEach(actionType => {
          Object.values(group[actionType]).forEach(perm => {
            if (perm.granted) {
              this.state.originalPermissions.add(perm.id);
              this.state.currentPermissions.add(perm.id);
            }
          });
        });
      });

      // Show inline container
      const container = document.getElementById('inline-permission-management');
      const titleEl = document.getElementById('inline-permission-title');
      const subtitleEl = document.getElementById('inline-permission-subtitle');
      const contentEl = document.getElementById('inline-permission-content');

      if (container && contentEl) {
        container.classList.remove('hidden');
        if (titleEl) titleEl.textContent = `Manage Permissions: ${role.name}`;
        if (subtitleEl) subtitleEl.textContent = `Configure permissions for ${role.name}`;
        contentEl.innerHTML = this.render();

        // Setup event listeners after rendering
        this.setupEventListeners();

        // Scroll to the permission section
        container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }

    } catch (error) {
      console.error('Error loading permission management:', error);
      showToast('Failed to load permission management', 'error');
    } finally {
      hideLoading();
    }
  }

  closeInline() {
    const container = document.getElementById('inline-permission-management');
    if (container) {
      container.classList.add('hidden');
    }
    this.mode = 'modal';
  }

  async openCard(roleId) {
    try {
      this.mode = 'card';
      showLoading();

      // Get role details
      const role = await rbacAPI.getRole(roleId);

      // Get grouped permissions with role assignments
      const permsData = await rbacAPI.getGroupedPermissions({ role_id: roleId });

      // Initialize state
      this.state.currentRoleId = roleId;
      this.state.groupedPermissions = permsData.groups || [];
      this.state.originalPermissions = new Set();
      this.state.currentPermissions = new Set();

      // Collect all currently granted permissions
      permsData.groups.forEach(group => {
        ['standard_actions', 'special_actions'].forEach(actionType => {
          Object.values(group[actionType]).forEach(perm => {
            if (perm.granted) {
              this.state.originalPermissions.add(perm.id);
              this.state.currentPermissions.add(perm.id);
            }
          });
        });
      });

      // Update card content (card is always visible)
      const titleEl = document.getElementById('permission-card-title');
      const subtitleEl = document.getElementById('permission-card-subtitle');
      const contentEl = document.getElementById('permission-card-content');
      const emptyState = document.getElementById('permission-card-empty');

      if (contentEl) {
        // Hide empty state
        if (emptyState) emptyState.classList.add('hidden');

        // Update title and subtitle
        if (titleEl) titleEl.textContent = `${role.name}`;
        if (subtitleEl) subtitleEl.textContent = `Configure permissions for this role`;

        // Render permission grid
        contentEl.innerHTML = this.render();

        // Setup event listeners after rendering
        this.setupEventListeners();
      }

    } catch (error) {
      console.error('Error loading permission management:', error);
      showToast('Failed to load permission management', 'error');
    } finally {
      hideLoading();
    }
  }

  closeCard() {
    // Reset to empty state (card stays visible)
    const titleEl = document.getElementById('permission-card-title');
    const subtitleEl = document.getElementById('permission-card-subtitle');
    const contentEl = document.getElementById('permission-card-content');
    const emptyState = document.getElementById('permission-card-empty');

    if (titleEl) titleEl.textContent = 'Permissions';
    if (subtitleEl) subtitleEl.textContent = 'Select a role to configure permissions';

    if (contentEl) {
      contentEl.innerHTML = `
        <div id="permission-card-empty" class="flex flex-col items-center justify-center py-12 text-center">
          <div class="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
            <i class="ph ph-shield-check text-3xl text-gray-400"></i>
          </div>
          <h4 class="text-lg font-semibold text-gray-900 mb-2">No Role Selected</h4>
          <p class="text-sm text-gray-600 max-w-sm">
            Click the <strong>Configure</strong> button on any role to manage its permissions
          </p>
        </div>
      `;
    }

    this.mode = 'modal';
  }

  render() {
    const { groupedPermissions, filters } = this.state;

    // Apply filters
    let filteredGroups = this.applyFilters(groupedPermissions, filters);

    // Get unique categories and scopes for filters
    const categories = [...new Set(groupedPermissions.map(g => g.category).filter(Boolean))];
    const scopes = [...new Set(groupedPermissions.map(g => g.scope))];

    // Group by category
    const byCategory = this.groupByCategory(filteredGroups);

    return `
      <div class="space-y-6">
        ${this.renderFiltersAndActions(categories, scopes)}
        ${this.renderPermissionGroups(byCategory)}
        ${this.renderSaveActions()}
      </div>
    `;
  }

  renderFiltersAndActions(categories, scopes) {
    const { filters } = this.state;

    return `
      <div class="bg-gray-50 p-4 rounded-lg space-y-3">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Search Resources</label>
            <input type="text" id="perm-search" placeholder="Search..."
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              value="${filters.search}">
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Category</label>
            <select id="perm-category-filter"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
              <option value="">All Categories</option>
              ${categories.map(cat => `<option value="${cat}" ${filters.category === cat ? 'selected' : ''}>${cat}</option>`).join('')}
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Scope</label>
            <select id="perm-scope-filter"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
              <option value="">All Scopes</option>
              ${scopes.map(scope => `<option value="${scope}" ${filters.scope === scope ? 'selected' : ''}>${scope}</option>`).join('')}
            </select>
          </div>
        </div>

        <div class="flex gap-2 flex-wrap">
          <button data-action="select-all-crud"
            class="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
            <i class="ph ph-check-square"></i> Select All CRUD
          </button>
          <button data-action="deselect-all-crud"
            class="px-3 py-1.5 text-sm bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors">
            <i class="ph ph-square"></i> Deselect All CRUD
          </button>
          <button data-action="template-viewer"
            class="px-3 py-1.5 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors">
            <i class="ph ph-eye"></i> Viewer Template
          </button>
          <button data-action="template-editor"
            class="px-3 py-1.5 text-sm bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors">
            <i class="ph ph-pencil"></i> Editor Template
          </button>
          <button data-action="template-manager"
            class="px-3 py-1.5 text-sm bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors">
            <i class="ph ph-crown"></i> Manager Template
          </button>
        </div>
      </div>
    `;
  }

  renderPermissionGroups(byCategory) {
    return `
      <div class="space-y-6 max-h-[60vh] overflow-y-auto">
        ${Object.entries(byCategory).map(([category, groups]) => `
          <div>
            <h3 class="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <i class="ph ph-folder text-blue-600"></i>
              ${category.toUpperCase()}
            </h3>
            <div class="space-y-3">
              ${groups.map(group => this.renderPermissionGroup(group)).join('')}
            </div>
          </div>
        `).join('')}
      </div>
    `;
  }

  renderPermissionGroup(group) {
    const standardActions = ['read', 'create', 'update', 'delete'];

    return `
      <div class="border border-gray-200 rounded-lg p-4 bg-white hover:shadow-sm transition-shadow">
        <div class="flex items-start justify-between mb-3">
          <div>
            <h4 class="font-semibold text-gray-900">${this.formatResourceName(group.resource)}</h4>
            <p class="text-sm text-gray-500">Scope: <span class="font-mono text-xs bg-gray-100 px-2 py-0.5 rounded">${group.scope}</span></p>
          </div>
          <button data-action="toggle-resource" data-key="${group.key}"
            class="text-sm text-blue-600 hover:text-blue-800">
            <i class="ph ph-check-square"></i> Toggle All
          </button>
        </div>

        <!-- Standard CRUD Actions -->
        <div class="mb-3">
          <div class="text-xs font-medium text-gray-500 mb-2">Standard Actions</div>
          <div class="flex flex-wrap gap-2">
            ${standardActions.map(action => {
              const perm = group.standard_actions[action];
              if (!perm) return '';

              const isChecked = this.state.currentPermissions.has(perm.id);
              return `
                <label class="flex items-center gap-2 px-3 py-2 rounded-lg border cursor-pointer transition-all
                  ${isChecked ? 'bg-blue-50 border-blue-300' : 'bg-gray-50 border-gray-300 hover:border-gray-400'}">
                  <input type="checkbox"
                    class="perm-checkbox w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                    data-perm-id="${perm.id}"
                    ${isChecked ? 'checked' : ''}>
                  <span class="text-sm font-medium ${isChecked ? 'text-blue-900' : 'text-gray-700'}">
                    ${action.charAt(0).toUpperCase() + action.slice(1)}
                  </span>
                </label>
              `;
            }).join('')}
          </div>
        </div>

        <!-- Special Actions -->
        ${Object.keys(group.special_actions).length > 0 ? `
          <div>
            <div class="text-xs font-medium text-gray-500 mb-2">Special Actions</div>
            <div class="flex flex-wrap gap-2">
              ${Object.entries(group.special_actions).map(([action, perm]) => {
                const isActive = this.state.currentPermissions.has(perm.id);
                return `
                  <button
                    data-action="toggle-badge" data-perm-id="${perm.id}"
                    class="px-3 py-1.5 rounded-lg text-sm font-medium transition-all
                      ${isActive
                        ? 'bg-green-100 text-green-800 border-2 border-green-400 hover:bg-green-200'
                        : 'bg-gray-100 text-gray-600 border-2 border-gray-300 hover:bg-gray-200'}">
                    <i class="ph ${isActive ? 'ph-check-circle' : 'ph-circle'}"></i>
                    ${action.charAt(0).toUpperCase() + action.slice(1)}
                  </button>
                `;
              }).join('')}
            </div>
          </div>
        ` : ''}
      </div>
    `;
  }

  renderSaveActions() {
    const { added, removed } = this.getChanges();

    return `
      <div class="flex justify-between items-center border-t pt-4">
        <div class="text-sm text-gray-600">
          ${added.length === 0 && removed.length === 0
            ? '<span class="font-medium text-gray-600">No changes</span>'
            : `<span class="font-medium">
                 <span class="text-green-600">+${added.length}</span> /
                 <span class="text-red-600">-${removed.length}</span> changes
               </span>`
          }
        </div>
        <div class="flex gap-2">
          <button data-action="cancel"
            class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors">
            Cancel
          </button>
          <button data-action="save"
            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
            <i class="ph ph-floppy-disk"></i> Save Changes
          </button>
        </div>
      </div>
    `;
  }

  setupEventListeners() {
    // Get the correct container based on mode
    let container;
    if (this.mode === 'card') {
      container = document.getElementById('permission-card-content');
    } else if (this.mode === 'inline') {
      container = document.getElementById('inline-permission-content');
    } else {
      container = document.getElementById('permission-management-modal');
    }

    if (!container) return;

    // Delegate all clicks to container
    container.addEventListener('click', (e) => {
      const action = e.target.closest('[data-action]')?.dataset.action;
      if (!action) return;

      switch (action) {
        case 'select-all-crud':
          this.selectAllCRUD();
          break;
        case 'deselect-all-crud':
          this.deselectAllCRUD();
          break;
        case 'template-viewer':
          this.applyTemplate('viewer');
          break;
        case 'template-editor':
          this.applyTemplate('editor');
          break;
        case 'template-manager':
          this.applyTemplate('manager');
          break;
        case 'toggle-resource':
          this.toggleAllForResource(e.target.closest('[data-key]').dataset.key);
          break;
        case 'toggle-badge':
          this.togglePermission(e.target.closest('[data-perm-id]').dataset.permId);
          break;
        case 'save':
          this.save();
          break;
        case 'cancel':
          if (this.mode === 'card') {
            this.closeCard();
          } else if (this.mode === 'inline') {
            this.closeInline();
          } else {
            modalManager.close('permission-management-modal');
          }
          break;
      }
    });

    // Filter changes
    container.querySelector('#perm-search')?.addEventListener('input', this.debounce((e) => {
      this.state.filters.search = e.target.value;
      this.refresh();
    }, 300));

    container.querySelector('#perm-category-filter')?.addEventListener('change', (e) => {
      this.state.filters.category = e.target.value;
      this.refresh();
    });

    container.querySelector('#perm-scope-filter')?.addEventListener('change', (e) => {
      this.state.filters.scope = e.target.value;
      this.refresh();
    });

    // Checkbox changes
    container.querySelectorAll('.perm-checkbox').forEach(checkbox => {
      checkbox.addEventListener('change', (e) => {
        const permId = e.target.dataset.permId;
        if (e.target.checked) {
          this.state.currentPermissions.add(permId);
        } else {
          this.state.currentPermissions.delete(permId);
        }
        this.refresh();
      });
    });
  }

  // Helper methods
  applyFilters(groups, filters) {
    let filtered = groups;

    if (filters.category) {
      filtered = filtered.filter(g => g.category === filters.category);
    }
    if (filters.scope) {
      filtered = filtered.filter(g => g.scope === filters.scope);
    }
    if (filters.search) {
      const search = filters.search.toLowerCase();
      filtered = filtered.filter(g =>
        g.resource.toLowerCase().includes(search) ||
        g.category?.toLowerCase().includes(search)
      );
    }

    return filtered;
  }

  groupByCategory(groups) {
    const byCategory = {};
    groups.forEach(group => {
      const cat = group.category || 'Other';
      if (!byCategory[cat]) byCategory[cat] = [];
      byCategory[cat].push(group);
    });
    return byCategory;
  }

  formatResourceName(resource) {
    return resource.split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  }

  togglePermission(permId) {
    if (this.state.currentPermissions.has(permId)) {
      this.state.currentPermissions.delete(permId);
    } else {
      this.state.currentPermissions.add(permId);
    }
    this.refresh();
  }

  toggleAllForResource(resourceKey) {
    const group = this.state.groupedPermissions.find(g => g.key === resourceKey);
    if (!group) return;

    const allPerms = [
      ...Object.values(group.standard_actions),
      ...Object.values(group.special_actions)
    ].map(p => p.id);

    const allSelected = allPerms.every(id => this.state.currentPermissions.has(id));

    if (allSelected) {
      allPerms.forEach(id => this.state.currentPermissions.delete(id));
    } else {
      allPerms.forEach(id => this.state.currentPermissions.add(id));
    }

    this.refresh();
  }

  selectAllCRUD() {
    this.state.groupedPermissions.forEach(group => {
      ['read', 'create', 'update', 'delete'].forEach(action => {
        if (group.standard_actions[action]) {
          this.state.currentPermissions.add(group.standard_actions[action].id);
        }
      });
    });
    this.refresh();
  }

  deselectAllCRUD() {
    this.state.groupedPermissions.forEach(group => {
      ['read', 'create', 'update', 'delete'].forEach(action => {
        if (group.standard_actions[action]) {
          this.state.currentPermissions.delete(group.standard_actions[action].id);
        }
      });
    });
    this.refresh();
  }

  applyTemplate(templateName) {
    if (templateName === 'viewer') {
      this.state.groupedPermissions.forEach(group => {
        if (group.standard_actions.read) {
          this.state.currentPermissions.add(group.standard_actions.read.id);
        }
      });
    } else if (templateName === 'editor') {
      this.state.groupedPermissions.forEach(group => {
        ['read', 'create', 'update'].forEach(action => {
          if (group.standard_actions[action]) {
            this.state.currentPermissions.add(group.standard_actions[action].id);
          }
        });
      });
    } else if (templateName === 'manager') {
      this.state.groupedPermissions.forEach(group => {
        Object.values(group.standard_actions).forEach(perm => {
          this.state.currentPermissions.add(perm.id);
        });
        if (group.special_actions.export) {
          this.state.currentPermissions.add(group.special_actions.export.id);
        }
        if (group.special_actions.manage) {
          this.state.currentPermissions.add(group.special_actions.manage.id);
        }
      });
    }
    this.refresh();
  }

  getChanges() {
    const added = [...this.state.currentPermissions].filter(
      id => !this.state.originalPermissions.has(id)
    );
    const removed = [...this.state.originalPermissions].filter(
      id => !this.state.currentPermissions.has(id)
    );
    return { added, removed };
  }

  async save() {
    try {
      showLoading();

      const { added, removed } = this.getChanges();

      const result = await rbacAPI.bulkUpdateRolePermissions(
        this.state.currentRoleId,
        added,
        removed
      );

      showToast(`Successfully updated permissions: ${result.granted} granted, ${result.revoked} revoked`, 'success');

      // Close based on mode
      if (this.mode === 'card') {
        this.closeCard();
      } else if (this.mode === 'inline') {
        this.closeInline();
      } else {
        modalManager.close('permission-management-modal');
      }

      // Trigger refresh if handler exists
      if (window.rbacManager?.refreshCurrentView) {
        window.rbacManager.refreshCurrentView();
      }

    } catch (error) {
      console.error('Error saving permissions:', error);
      showToast('Failed to save permissions', 'error');
    } finally {
      hideLoading();
    }
  }

  refresh() {
    let contentId;
    if (this.mode === 'card') {
      contentId = 'permission-card-content';
    } else if (this.mode === 'inline') {
      contentId = 'inline-permission-content';
    } else {
      contentId = 'permission-management-content';
    }
    const content = document.getElementById(contentId);
    if (content) {
      content.innerHTML = this.render();
      this.setupEventListeners();
    }
  }

  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }
}

// Export singleton
export const permissionGrid = new PermissionGrid();
