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

    // Map scopes to icons
    const scopeIcons = {
      'tenant': 'ph-buildings',
      'company': 'ph-building-office',
      'branch': 'ph-git-branch',
      'department': 'ph-users-three',
      'own': 'ph-user-circle',
      'user': 'ph-user'
    };

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
            <div class="flex gap-2 flex-wrap">
              <button data-action="filter-scope" data-scope=""
                title="All Scopes"
                class="px-3 py-2 rounded-lg text-sm font-medium transition-all
                  ${filters.scope === '' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'}">
                <i class="ph ph-stack"></i>
              </button>
              ${scopes.map(scope => {
                const icon = scopeIcons[scope.toLowerCase()] || 'ph-circle';
                const isActive = filters.scope === scope;
                return `
                  <button data-action="filter-scope" data-scope="${scope}"
                    title="${scope.charAt(0).toUpperCase() + scope.slice(1)}"
                    class="px-3 py-2 rounded-lg text-sm font-medium transition-all
                      ${isActive ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'}">
                    <i class="ph ${icon}"></i>
                  </button>
                `;
              }).join('')}
            </div>
          </div>
        </div>

        <div class="flex justify-between items-center gap-2">
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
          <button data-action="new-permission"
            class="px-4 py-1.5 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors flex items-center gap-2">
            <i class="ph ph-plus-circle"></i> New Permission
          </button>
        </div>
      </div>
    `;
  }

  renderPermissionGroups(byCategory) {
    return `
      <div class="space-y-6">
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
    const actionIcons = {
      read: 'ph-eye',
      create: 'ph-plus-circle',
      update: 'ph-pencil-simple',
      delete: 'ph-trash'
    };

    return `
      <div class="border border-gray-200 rounded-lg bg-white hover:border-blue-300 transition-all">
        <div class="px-4 py-2 flex items-center gap-4">
          <!-- Resource Name -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <span class="font-medium text-gray-900 text-sm">${this.formatResourceName(group.resource)}</span>
              <span class="font-mono text-xs bg-gray-100 px-2 py-0.5 rounded text-gray-600">${group.scope}</span>
            </div>
          </div>

          <!-- Standard CRUD Actions as Icons -->
          <div class="flex items-center gap-1">
            ${standardActions.map(action => {
              const perm = group.standard_actions[action];
              if (!perm) return `<div class="w-8 h-8"></div>`;

              const isGranted = this.state.currentPermissions.has(perm.id);
              return `
                <button
                  data-action="toggle-icon" data-perm-id="${perm.id}"
                  title="${action.charAt(0).toUpperCase() + action.slice(1)}"
                  class="w-8 h-8 flex items-center justify-center rounded-lg transition-all
                    ${isGranted
                      ? 'bg-green-100 text-green-700 hover:bg-green-200'
                      : 'bg-gray-100 text-gray-400 hover:bg-gray-200'}">
                  <i class="ph ${actionIcons[action]} text-lg"></i>
                </button>
              `;
            }).join('')}
          </div>

          <!-- Special Actions as Compact Badges -->
          ${Object.keys(group.special_actions).length > 0 ? `
            <div class="flex items-center gap-1">
              ${Object.entries(group.special_actions).map(([action, perm]) => {
                const isActive = this.state.currentPermissions.has(perm.id);
                return `
                  <button
                    data-action="toggle-badge" data-perm-id="${perm.id}"
                    title="${action.charAt(0).toUpperCase() + action.slice(1)}"
                    class="px-2 py-1 rounded text-xs font-medium transition-all
                      ${isActive
                        ? 'bg-purple-100 text-purple-700 hover:bg-purple-200'
                        : 'bg-gray-100 text-gray-500 hover:bg-gray-200'}">
                    ${action.charAt(0).toUpperCase()}
                  </button>
                `;
              }).join('')}
            </div>
          ` : ''}

          <!-- Toggle All Button -->
          <button data-action="toggle-resource" data-key="${group.key}"
            title="Toggle all permissions"
            class="w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:bg-gray-100 hover:text-blue-600 transition-all">
            <i class="ph ph-check-square text-lg"></i>
          </button>
        </div>
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
        case 'filter-scope':
          this.state.filters.scope = e.target.closest('[data-scope]').dataset.scope;
          this.refresh();
          break;
        case 'new-permission':
          this.showNewPermissionDialog();
          break;
        case 'toggle-resource':
          this.toggleAllForResource(e.target.closest('[data-key]').dataset.key);
          break;
        case 'toggle-icon':
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
  }

  showNewPermissionDialog() {
    const categories = [...new Set(this.state.groupedPermissions.map(g => g.category).filter(Boolean))];
    const scopes = ['tenant', 'company', 'branch', 'department', 'own'];
    const actions = ['read', 'create', 'update', 'delete', 'export', 'import', 'manage', 'approve', 'execute'];

    const dialogHtml = `
      <div id="new-permission-modal" class="fixed inset-0 bg-black bg-opacity-50 z-[60] flex items-center justify-center p-4">
        <div class="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
          <div class="p-6 border-b bg-gradient-to-r from-indigo-600 to-indigo-700 flex items-center justify-between">
            <h3 class="text-xl font-semibold text-white flex items-center gap-2">
              <i class="ph ph-plus-circle"></i>
              <span>Create New Permission</span>
            </h3>
            <button data-action="close-new-permission" class="text-white hover:text-gray-200">
              <i class="ph ph-x text-2xl"></i>
            </button>
          </div>

          <div class="p-6 overflow-y-auto max-h-[calc(90vh-180px)]">
            <form id="new-permission-form" class="space-y-4">
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                    Resource Name <span class="text-red-500">*</span>
                  </label>
                  <input type="text" name="resource" required
                    placeholder="e.g., users, projects, invoices"
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500">
                  <p class="text-xs text-gray-500 mt-1">Lowercase, singular noun</p>
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                    Action <span class="text-red-500">*</span>
                  </label>
                  <select name="action" required
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500">
                    <option value="">Select action...</option>
                    ${actions.map(action => `<option value="${action}">${action.charAt(0).toUpperCase() + action.slice(1)}</option>`).join('')}
                  </select>
                </div>
              </div>

              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                    Scope <span class="text-red-500">*</span>
                  </label>
                  <select name="scope" required
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500">
                    ${scopes.map(scope => `<option value="${scope}">${scope.charAt(0).toUpperCase() + scope.slice(1)}</option>`).join('')}
                  </select>
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                    Category
                  </label>
                  <input list="categories" name="category"
                    placeholder="e.g., core, financial, hr"
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500">
                  <datalist id="categories">
                    ${categories.map(cat => `<option value="${cat}">`).join('')}
                  </datalist>
                </div>
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea name="description" rows="3"
                  placeholder="Describe what this permission allows..."
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"></textarea>
              </div>

              <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div class="flex items-start gap-2">
                  <i class="ph ph-info text-blue-600 text-lg"></i>
                  <div class="text-sm text-blue-800">
                    <p class="font-medium mb-1">Permission Code Format</p>
                    <p>Code will be generated as: <span class="font-mono bg-white px-2 py-0.5 rounded">{resource}:{action}:{scope}</span></p>
                    <p class="text-xs mt-1">Example: <span class="font-mono">users:read:tenant</span> or <span class="font-mono">invoices:approve:company</span></p>
                  </div>
                </div>
              </div>
            </form>
          </div>

          <div class="p-6 border-t bg-gray-50 flex justify-end gap-3">
            <button data-action="close-new-permission"
              class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors">
              Cancel
            </button>
            <button data-action="save-new-permission"
              class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors flex items-center gap-2">
              <i class="ph ph-floppy-disk"></i> Create Permission
            </button>
          </div>
        </div>
      </div>
    `;

    // Add modal to body
    document.body.insertAdjacentHTML('beforeend', dialogHtml);

    // Setup event listeners for modal
    const modal = document.getElementById('new-permission-modal');

    modal.addEventListener('click', (e) => {
      const action = e.target.closest('[data-action]')?.dataset.action;

      if (action === 'close-new-permission') {
        modal.remove();
      } else if (action === 'save-new-permission') {
        this.saveNewPermission();
      }
    });

    // Close on backdrop click
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.remove();
      }
    });
  }

  async saveNewPermission() {
    const form = document.getElementById('new-permission-form');

    if (!form.checkValidity()) {
      form.reportValidity();
      return;
    }

    try {
      showLoading();

      const formData = new FormData(form);
      const resource = formData.get('resource').trim().toLowerCase();
      const action = formData.get('action');
      const scope = formData.get('scope');
      const category = formData.get('category')?.trim() || null;
      const description = formData.get('description')?.trim() || null;

      // Generate permission code
      const code = `${resource}:${action}:${scope}`;

      const permissionData = {
        code,
        name: `${action.charAt(0).toUpperCase() + action.slice(1)} ${resource}`,
        resource,
        action,
        scope,
        category,
        description,
        is_active: true
      };

      await rbacAPI.createPermission(permissionData);

      showToast('Permission created successfully', 'success');

      // Close modal
      document.getElementById('new-permission-modal')?.remove();

      // Reload permissions if we're managing a role
      if (this.state.currentRoleId) {
        const role = await rbacAPI.getRole(this.state.currentRoleId);
        const permsData = await rbacAPI.getGroupedPermissions({ role_id: this.state.currentRoleId });
        this.state.groupedPermissions = permsData.groups || [];
        this.refresh();
      }

    } catch (error) {
      console.error('Error creating permission:', error);
      showToast(error.message || 'Failed to create permission', 'error');
    } finally {
      hideLoading();
    }
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
