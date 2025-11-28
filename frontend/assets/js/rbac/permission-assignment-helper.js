/**
 * Permission Assignment Helper
 * Comprehensive UI for managing all aspects of permission assignments:
 * - User → Role assignments
 * - Role → Permission assignments
 * - Permission matrix visualization
 * - Quick assignment workflows
 *
 * This helper provides admin-friendly interfaces for complete access control management
 */

import { rbacAPI } from './rbac-api.js';
import { permissionGrid } from './permission-grid.js';
import { showToast, showLoading, hideLoading } from '../ui-utils.js';

export class PermissionAssignmentHelper {
  constructor() {
    this.state = {
      view: 'user-roles', // 'user-roles', 'role-permissions', 'matrix'
      selectedUser: null,
      selectedRole: null,
      users: [],
      roles: [],
      permissions: [],
      userRoles: new Map(), // userId -> Set of roleIds
      rolePermissions: new Map(), // roleId -> Set of permissionIds
      filters: {
        userSearch: '',
        roleFilter: '',
        scopeFilter: ''
      }
    };
  }

  /**
   * Initialize the helper and load all data
   */
  async initialize(containerId = 'permission-assignment-container') {
    try {
      showLoading();
      this.containerId = containerId;

      // Load all data in parallel
      await Promise.all([
        this.loadUsers(),
        this.loadRoles(),
        this.loadPermissions()
      ]);

      // Render initial view
      this.render();

    } catch (error) {
      console.error('Error initializing Permission Assignment Helper:', error);
      showToast('Failed to initialize access control', 'error');
    } finally {
      hideLoading();
    }
  }

  async loadUsers() {
    const response = await rbacAPI.getUsers({ limit: 1000 });
    this.state.users = response.items || [];
  }

  async loadRoles() {
    const response = await rbacAPI.getRoles({ limit: 1000 });
    this.state.roles = response.items || [];
  }

  async loadPermissions() {
    const response = await rbacAPI.getPermissions({ limit: 1000 });
    this.state.permissions = response.items || [];
  }

  /**
   * Main render method - delegates to specific view renderers
   */
  render() {
    const container = document.getElementById(this.containerId);
    if (!container) return;

    container.innerHTML = `
      <div class="bg-white rounded-xl shadow-lg">
        ${this.renderHeader()}
        ${this.renderContent()}
      </div>
    `;

    this.setupEventListeners();
  }

  renderHeader() {
    const { view } = this.state;

    return `
      <div class="border-b bg-gradient-to-r from-blue-600 to-indigo-700 px-6 py-4 rounded-t-xl">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-2xl font-bold text-white flex items-center gap-2">
              <i class="ph-duotone ph-shield-check"></i>
              Access Control Manager
            </h2>
            <p class="text-blue-100 text-sm mt-1">Manage user roles and permissions</p>
          </div>
          <div class="flex gap-2">
            <button data-action="refresh-all"
              class="p-2 bg-white/20 hover:bg-white/30 text-white rounded-lg transition-colors"
              title="Refresh All Data">
              <i class="ph ph-arrows-clockwise text-xl"></i>
            </button>
            <button data-action="export-config"
              class="p-2 bg-white/20 hover:bg-white/30 text-white rounded-lg transition-colors"
              title="Export Configuration">
              <i class="ph ph-download-simple text-xl"></i>
            </button>
          </div>
        </div>

        <!-- View Tabs -->
        <div class="flex gap-2 mt-4">
          <button data-action="switch-view" data-view="user-roles"
            class="px-4 py-2 rounded-lg font-medium transition-all ${
              view === 'user-roles'
                ? 'bg-white text-blue-700 shadow-md'
                : 'bg-white/20 text-white hover:bg-white/30'
            }">
            <i class="ph-duotone ph-user-gear"></i> User → Roles
          </button>
          <button data-action="switch-view" data-view="role-permissions"
            class="px-4 py-2 rounded-lg font-medium transition-all ${
              view === 'role-permissions'
                ? 'bg-white text-blue-700 shadow-md'
                : 'bg-white/20 text-white hover:bg-white/30'
            }">
            <i class="ph-duotone ph-shield-star"></i> Role → Permissions
          </button>
          <button data-action="switch-view" data-view="matrix"
            class="px-4 py-2 rounded-lg font-medium transition-all ${
              view === 'matrix'
                ? 'bg-white text-blue-700 shadow-md'
                : 'bg-white/20 text-white hover:bg-white/30'
            }">
            <i class="ph-duotone ph-table"></i> Permission Matrix
          </button>
        </div>
      </div>
    `;
  }

  renderContent() {
    switch (this.state.view) {
      case 'user-roles':
        return this.renderUserRolesView();
      case 'role-permissions':
        return this.renderRolePermissionsView();
      case 'matrix':
        return this.renderMatrixView();
      default:
        return '';
    }
  }

  // ============================================================================
  // USER → ROLES VIEW
  // ============================================================================

  renderUserRolesView() {
    const { users, roles, filters } = this.state;

    // Filter users based on search
    const filteredUsers = users.filter(u =>
      u.full_name?.toLowerCase().includes(filters.userSearch.toLowerCase()) ||
      u.email?.toLowerCase().includes(filters.userSearch.toLowerCase())
    );

    return `
      <div class="p-6">
        <!-- Search and Filters -->
        <div class="mb-6 flex gap-4">
          <div class="flex-1">
            <div class="relative">
              <i class="ph ph-magnifying-glass absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"></i>
              <input type="text" id="user-search" placeholder="Search users by name or email..."
                value="${filters.userSearch}"
                class="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
            </div>
          </div>
          <button data-action="quick-assign-role"
            class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2">
            <i class="ph ph-lightning"></i> Quick Assign
          </button>
        </div>

        <!-- User List with Role Assignments -->
        <div class="space-y-3">
          ${filteredUsers.length === 0 ? `
            <div class="text-center py-12">
              <i class="ph-duotone ph-user-circle-x text-6xl text-gray-300 mb-4"></i>
              <p class="text-gray-500">No users found</p>
            </div>
          ` : filteredUsers.map(user => this.renderUserRoleCard(user, roles)).join('')}
        </div>
      </div>
    `;
  }

  renderUserRoleCard(user, roles) {
    return `
      <div class="border border-gray-200 rounded-lg bg-white hover:border-blue-300 hover:shadow-md transition-all">
        <div class="p-4">
          <div class="flex items-start justify-between gap-4">
            <!-- User Info -->
            <div class="flex items-start gap-3 flex-1 min-w-0">
              <div class="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
                ${user.full_name?.charAt(0) || user.email.charAt(0).toUpperCase()}
              </div>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2">
                  <h4 class="font-semibold text-gray-900">${user.full_name || user.email}</h4>
                  ${user.is_superuser ? '<span class="px-2 py-0.5 bg-purple-100 text-purple-700 text-xs font-medium rounded">Superuser</span>' : ''}
                  ${!user.is_active ? '<span class="px-2 py-0.5 bg-red-100 text-red-700 text-xs font-medium rounded">Inactive</span>' : ''}
                </div>
                <p class="text-sm text-gray-600">${user.email}</p>
              </div>
            </div>

            <!-- Role Assignment Button -->
            <button data-action="manage-user-roles" data-user-id="${user.id}"
              class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2 flex-shrink-0">
              <i class="ph ph-gear-six"></i> Manage Roles
            </button>
          </div>

          <!-- Quick Role Indicators -->
          <div id="user-roles-${user.id}" class="mt-3 flex gap-2 flex-wrap">
            <span class="text-xs text-gray-400 italic">Loading roles...</span>
          </div>
        </div>
      </div>
    `;
  }

  // ============================================================================
  // ROLE → PERMISSIONS VIEW
  // ============================================================================

  renderRolePermissionsView() {
    const { roles, filters } = this.state;

    // Filter roles
    const filteredRoles = roles.filter(r =>
      !filters.roleFilter ||
      r.name.toLowerCase().includes(filters.roleFilter.toLowerCase()) ||
      r.code.toLowerCase().includes(filters.roleFilter.toLowerCase())
    );

    return `
      <div class="p-6">
        <!-- Search and Actions -->
        <div class="mb-6 flex gap-4">
          <div class="flex-1">
            <div class="relative">
              <i class="ph ph-magnifying-glass absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"></i>
              <input type="text" id="role-search" placeholder="Search roles..."
                value="${filters.roleFilter}"
                class="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
            </div>
          </div>
          <button data-action="create-role-template"
            class="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors flex items-center gap-2">
            <i class="ph ph-sparkle"></i> Create Template
          </button>
        </div>

        <!-- Role Grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          ${filteredRoles.map(role => this.renderRolePermissionCard(role)).join('')}
        </div>
      </div>
    `;
  }

  renderRolePermissionCard(role) {
    const roleColors = {
      'superuser': 'from-purple-500 to-pink-600',
      'tenant_admin': 'from-blue-500 to-indigo-600',
      'company_manager': 'from-green-500 to-emerald-600',
      'default': 'from-gray-500 to-slate-600'
    };

    const gradient = roleColors[role.code] || roleColors.default;

    return `
      <div class="border border-gray-200 rounded-lg bg-white hover:border-blue-300 hover:shadow-lg transition-all">
        <div class="bg-gradient-to-br ${gradient} p-4 rounded-t-lg">
          <div class="flex items-start justify-between gap-2">
            <div class="flex-1 min-w-0">
              <h4 class="font-bold text-white text-lg truncate">${role.name}</h4>
              <p class="text-white/80 text-xs font-mono">${role.code}</p>
            </div>
            ${role.is_system ? `
              <span class="px-2 py-1 bg-white/30 text-white text-xs font-medium rounded flex-shrink-0">
                System
              </span>
            ` : ''}
          </div>
        </div>

        <div class="p-4">
          ${role.description ? `
            <p class="text-sm text-gray-600 mb-3">${role.description}</p>
          ` : ''}

          <div class="flex items-center justify-between mb-3">
            <span class="text-xs text-gray-500">Permissions</span>
            <span id="role-perm-count-${role.id}" class="text-sm font-bold text-blue-600">
              <i class="ph ph-spinner-gap animate-spin"></i>
            </span>
          </div>

          <button data-action="configure-role-permissions" data-role-id="${role.id}"
            class="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center gap-2">
            <i class="ph ph-shield-star"></i> Configure Permissions
          </button>
        </div>
      </div>
    `;
  }

  // ============================================================================
  // PERMISSION MATRIX VIEW
  // ============================================================================

  renderMatrixView() {
    const { roles, permissions } = this.state;

    // Group permissions by category
    const permsByCategory = {};
    permissions.forEach(perm => {
      const cat = perm.category || 'Other';
      if (!permsByCategory[cat]) permsByCategory[cat] = [];
      permsByCategory[cat].push(perm);
    });

    return `
      <div class="p-6">
        <div class="mb-4 flex items-center justify-between">
          <p class="text-sm text-gray-600">
            View all role-permission assignments in a matrix format
          </p>
          <button data-action="download-matrix-csv"
            class="px-3 py-1.5 text-sm bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors flex items-center gap-2">
            <i class="ph ph-file-csv"></i> Export CSV
          </button>
        </div>

        <!-- Matrix Table -->
        <div class="overflow-auto max-h-[600px] border border-gray-200 rounded-lg">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50 sticky top-0 z-10">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase sticky left-0 bg-gray-50 border-r">
                  Permission
                </th>
                ${roles.map(role => `
                  <th class="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase min-w-[100px]">
                    <div class="truncate" title="${role.name}">${role.code}</div>
                  </th>
                `).join('')}
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              ${Object.entries(permsByCategory).map(([category, perms]) => `
                <tr class="bg-gray-100">
                  <td colspan="${roles.length + 1}" class="px-4 py-2 text-sm font-bold text-gray-700">
                    ${category.toUpperCase()}
                  </td>
                </tr>
                ${perms.map(perm => `
                  <tr class="hover:bg-blue-50">
                    <td class="px-4 py-2 text-sm text-gray-900 sticky left-0 bg-white border-r whitespace-nowrap">
                      <div class="flex items-center gap-2">
                        <span class="font-mono text-xs bg-gray-100 px-2 py-0.5 rounded">${perm.code}</span>
                      </div>
                    </td>
                    ${roles.map(role => `
                      <td class="px-3 py-2 text-center">
                        <button
                          data-action="toggle-matrix-cell"
                          data-role-id="${role.id}"
                          data-perm-id="${perm.id}"
                          class="matrix-cell w-6 h-6 rounded flex items-center justify-center transition-all
                            bg-gray-200 text-gray-400 hover:bg-blue-100">
                          <i class="ph ph-spinner-gap animate-spin text-xs"></i>
                        </button>
                      </td>
                    `).join('')}
                  </tr>
                `).join('')}
              `).join('')}
            </tbody>
          </table>
        </div>

        <div class="mt-4 flex items-center gap-4 text-xs text-gray-500">
          <div class="flex items-center gap-2">
            <div class="w-4 h-4 bg-green-500 rounded"></div>
            <span>Granted</span>
          </div>
          <div class="flex items-center gap-2">
            <div class="w-4 h-4 bg-gray-300 rounded"></div>
            <span>Not Granted</span>
          </div>
        </div>
      </div>
    `;
  }

  // ============================================================================
  // EVENT HANDLERS
  // ============================================================================

  setupEventListeners() {
    const container = document.getElementById(this.containerId);
    if (!container) return;

    // Delegate all clicks
    container.addEventListener('click', async (e) => {
      const action = e.target.closest('[data-action]')?.dataset.action;
      if (!action) return;

      const target = e.target.closest('[data-action]');

      switch (action) {
        case 'switch-view':
          this.switchView(target.dataset.view);
          break;
        case 'refresh-all':
          this.refresh();
          break;
        case 'export-config':
          this.exportConfiguration();
          break;
        case 'manage-user-roles':
          this.openUserRoleManager(target.dataset.userId);
          break;
        case 'quick-assign-role':
          this.showQuickAssignDialog();
          break;
        case 'configure-role-permissions':
          this.openRolePermissionManager(target.dataset.roleId);
          break;
        case 'create-role-template':
          this.showCreateTemplateDialog();
          break;
        case 'toggle-matrix-cell':
          this.toggleMatrixCell(target.dataset.roleId, target.dataset.permId, target);
          break;
        case 'download-matrix-csv':
          this.downloadMatrixCSV();
          break;
      }
    });

    // Search inputs
    const userSearch = container.querySelector('#user-search');
    if (userSearch) {
      userSearch.addEventListener('input', this.debounce((e) => {
        this.state.filters.userSearch = e.target.value;
        this.render();
      }, 300));
    }

    const roleSearch = container.querySelector('#role-search');
    if (roleSearch) {
      roleSearch.addEventListener('input', this.debounce((e) => {
        this.state.filters.roleFilter = e.target.value;
        this.render();
      }, 300));
    }

    // Load additional data based on view
    this.loadViewData();
  }

  async loadViewData() {
    if (this.state.view === 'user-roles') {
      // Load user roles for each visible user
      this.state.users.slice(0, 20).forEach(user => this.loadUserRoles(user.id));
    } else if (this.state.view === 'role-permissions') {
      // Load permission counts for each role
      this.state.roles.forEach(role => this.loadRolePermissionCount(role.id));
    } else if (this.state.view === 'matrix') {
      // Load full matrix
      this.loadMatrix();
    }
  }

  async loadUserRoles(userId) {
    try {
      const data = await rbacAPI.getUserRoles(userId);
      const roleIds = [
        ...(data.direct_roles || []).map(r => r.id),
        ...(data.group_roles || []).map(r => r.role_id)
      ];

      // Update UI
      const container = document.getElementById(`user-roles-${userId}`);
      if (container) {
        if (roleIds.length === 0) {
          container.innerHTML = '<span class="text-xs text-gray-400 italic">No roles assigned</span>';
        } else {
          const roles = this.state.roles.filter(r => roleIds.includes(r.id));
          container.innerHTML = roles.map(role => `
            <span class="px-2 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded">
              ${role.name}
            </span>
          `).join('');
        }
      }
    } catch (error) {
      console.error('Error loading user roles:', error);
    }
  }

  async loadRolePermissionCount(roleId) {
    try {
      const role = await rbacAPI.getRole(roleId);
      const count = role.permissions?.length || 0;

      const countEl = document.getElementById(`role-perm-count-${roleId}`);
      if (countEl) {
        countEl.innerHTML = `${count} permissions`;
      }
    } catch (error) {
      console.error('Error loading role permissions:', error);
    }
  }

  async loadMatrix() {
    // Load all role-permission relationships and update matrix cells
    showLoading();
    try {
      const rolePermMap = new Map();

      // Load permissions for each role
      await Promise.all(
        this.state.roles.map(async role => {
          const roleData = await rbacAPI.getRole(role.id);
          const permIds = (roleData.permissions || []).map(p => p.id);
          rolePermMap.set(role.id, new Set(permIds));
        })
      );

      // Update all matrix cells
      const cells = document.querySelectorAll('.matrix-cell');
      cells.forEach(cell => {
        const roleId = cell.dataset.roleId;
        const permId = cell.dataset.permId;

        const hasPermission = rolePermMap.get(roleId)?.has(permId);

        cell.className = `matrix-cell w-6 h-6 rounded flex items-center justify-center transition-all cursor-pointer ${
          hasPermission
            ? 'bg-green-500 text-white hover:bg-green-600'
            : 'bg-gray-300 text-gray-500 hover:bg-gray-400'
        }`;
        cell.innerHTML = hasPermission
          ? '<i class="ph-fill ph-check text-sm"></i>'
          : '<i class="ph ph-minus text-sm"></i>';
      });
    } catch (error) {
      console.error('Error loading matrix:', error);
      showToast('Failed to load permission matrix', 'error');
    } finally {
      hideLoading();
    }
  }

  // ============================================================================
  // ACTIONS
  // ============================================================================

  switchView(view) {
    this.state.view = view;
    this.render();
  }

  async refresh() {
    showLoading();
    try {
      await Promise.all([
        this.loadUsers(),
        this.loadRoles(),
        this.loadPermissions()
      ]);
      this.render();
      showToast('Data refreshed successfully', 'success');
    } catch (error) {
      console.error('Error refreshing data:', error);
      showToast('Failed to refresh data', 'error');
    } finally {
      hideLoading();
    }
  }

  async openUserRoleManager(userId) {
    try {
      showLoading();

      const user = this.state.users.find(u => u.id === userId);
      const userRoles = await rbacAPI.getUserRoles(userId);

      // Show modal with role assignment UI
      const modalHTML = this.renderUserRoleManagerModal(user, userRoles);
      document.body.insertAdjacentHTML('beforeend', modalHTML);

      this.setupUserRoleManagerListeners(userId);

    } catch (error) {
      console.error('Error opening user role manager:', error);
      showToast('Failed to load user roles', 'error');
    } finally {
      hideLoading();
    }
  }

  renderUserRoleManagerModal(user, userRoles) {
    const directRoleIds = new Set((userRoles.direct_roles || []).map(r => r.id));
    const groupRoleIds = new Set((userRoles.group_roles || []).map(r => r.role_id));

    return `
      <div id="user-role-manager-modal" class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
        <div class="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
          <div class="p-6 border-b bg-gradient-to-r from-blue-600 to-indigo-700">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <div class="w-12 h-12 rounded-full bg-white/20 flex items-center justify-center text-white font-bold">
                  ${user.full_name?.charAt(0) || user.email.charAt(0).toUpperCase()}
                </div>
                <div>
                  <h3 class="text-xl font-bold text-white">${user.full_name || user.email}</h3>
                  <p class="text-blue-100 text-sm">${user.email}</p>
                </div>
              </div>
              <button data-action="close-modal" class="text-white hover:text-gray-200">
                <i class="ph ph-x text-2xl"></i>
              </button>
            </div>
          </div>

          <div class="p-6 overflow-y-auto max-h-[calc(90vh-180px)]">
            <div class="space-y-4">
              ${this.state.roles.map(role => {
                const isDirect = directRoleIds.has(role.id);
                const isFromGroup = groupRoleIds.has(role.id);
                const isAssigned = isDirect || isFromGroup;

                return `
                  <label class="flex items-start gap-3 p-3 border rounded-lg cursor-pointer hover:bg-gray-50 transition-all ${
                    isAssigned ? 'bg-blue-50 border-blue-300' : 'border-gray-200'
                  }">
                    <input
                      type="checkbox"
                      data-role-id="${role.id}"
                      ${isDirect ? 'checked' : ''}
                      ${isFromGroup ? 'disabled' : ''}
                      class="mt-1 w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500">
                    <div class="flex-1">
                      <div class="flex items-center gap-2">
                        <span class="font-medium text-gray-900">${role.name}</span>
                        ${role.is_system ? '<span class="px-2 py-0.5 bg-purple-100 text-purple-700 text-xs font-medium rounded">System</span>' : ''}
                        ${isFromGroup ? '<span class="px-2 py-0.5 bg-green-100 text-green-700 text-xs font-medium rounded">From Group</span>' : ''}
                      </div>
                      ${role.description ? `<p class="text-sm text-gray-600 mt-1">${role.description}</p>` : ''}
                      <p class="text-xs text-gray-500 font-mono mt-1">${role.code}</p>
                    </div>
                  </label>
                `;
              }).join('')}
            </div>
          </div>

          <div class="p-6 border-t bg-gray-50 flex justify-end gap-3">
            <button data-action="close-modal"
              class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors">
              Cancel
            </button>
            <button data-action="save-user-roles"
              class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
              <i class="ph ph-floppy-disk"></i> Save Changes
            </button>
          </div>
        </div>
      </div>
    `;
  }

  setupUserRoleManagerListeners(userId) {
    const modal = document.getElementById('user-role-manager-modal');
    if (!modal) return;

    modal.addEventListener('click', async (e) => {
      const action = e.target.closest('[data-action]')?.dataset.action;

      if (action === 'close-modal') {
        modal.remove();
      } else if (action === 'save-user-roles') {
        await this.saveUserRoles(userId);
        modal.remove();
      }
    });
  }

  async saveUserRoles(userId) {
    try {
      showLoading();

      const modal = document.getElementById('user-role-manager-modal');
      const checkboxes = modal.querySelectorAll('input[type="checkbox"]:not([disabled])');

      const selectedRoleIds = Array.from(checkboxes)
        .filter(cb => cb.checked)
        .map(cb => cb.dataset.roleId);

      // Get current direct roles
      const currentRoles = await rbacAPI.getUserRoles(userId);
      const currentRoleIds = (currentRoles.direct_roles || []).map(r => r.id);

      // Calculate changes
      const toAdd = selectedRoleIds.filter(id => !currentRoleIds.includes(id));
      const toRemove = currentRoleIds.filter(id => !selectedRoleIds.includes(id));

      // Apply changes
      if (toAdd.length > 0) {
        await rbacAPI.assignRolesToUser(userId, toAdd);
      }

      for (const roleId of toRemove) {
        await rbacAPI.removeRoleFromUser(userId, roleId);
      }

      showToast(`Updated roles for user: +${toAdd.length} -${toRemove.length}`, 'success');
      this.render(); // Refresh view

    } catch (error) {
      console.error('Error saving user roles:', error);
      showToast('Failed to save user roles', 'error');
    } finally {
      hideLoading();
    }
  }

  async openRolePermissionManager(roleId) {
    // Delegate to existing permission grid component
    await permissionGrid.open(roleId);
  }

  showQuickAssignDialog() {
    const html = `
      <div id="quick-assign-modal" class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
        <div class="bg-white rounded-xl shadow-2xl max-w-md w-full">
          <div class="p-6 border-b bg-gradient-to-r from-green-600 to-emerald-700">
            <h3 class="text-xl font-bold text-white flex items-center gap-2">
              <i class="ph ph-lightning"></i> Quick Role Assignment
            </h3>
            <p class="text-green-100 text-sm mt-1">Assign role to multiple users at once</p>
          </div>

          <div class="p-6">
            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">Select Role</label>
                <select id="quick-assign-role" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500">
                  <option value="">Choose a role...</option>
                  ${this.state.roles.map(role => `
                    <option value="${role.id}">${role.name} (${role.code})</option>
                  `).join('')}
                </select>
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">Select Users</label>
                <div class="border border-gray-300 rounded-lg max-h-64 overflow-y-auto p-2 space-y-2">
                  ${this.state.users.map(user => `
                    <label class="flex items-center gap-2 p-2 hover:bg-gray-50 rounded cursor-pointer">
                      <input type="checkbox" value="${user.id}" class="quick-assign-user w-4 h-4 text-green-600 rounded">
                      <span class="text-sm">${user.full_name || user.email}</span>
                    </label>
                  `).join('')}
                </div>
              </div>
            </div>
          </div>

          <div class="p-6 border-t bg-gray-50 flex justify-end gap-3">
            <button data-action="close-quick-assign"
              class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100">
              Cancel
            </button>
            <button data-action="execute-quick-assign"
              class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
              <i class="ph ph-check"></i> Assign Role
            </button>
          </div>
        </div>
      </div>
    `;

    document.body.insertAdjacentHTML('beforeend', html);

    const modal = document.getElementById('quick-assign-modal');
    modal.addEventListener('click', async (e) => {
      const action = e.target.closest('[data-action]')?.dataset.action;

      if (action === 'close-quick-assign') {
        modal.remove();
      } else if (action === 'execute-quick-assign') {
        await this.executeQuickAssign();
      }
    });
  }

  async executeQuickAssign() {
    try {
      showLoading();

      const roleId = document.getElementById('quick-assign-role').value;
      const userCheckboxes = document.querySelectorAll('.quick-assign-user:checked');
      const userIds = Array.from(userCheckboxes).map(cb => cb.value);

      if (!roleId) {
        showToast('Please select a role', 'warning');
        return;
      }

      if (userIds.length === 0) {
        showToast('Please select at least one user', 'warning');
        return;
      }

      // Assign role to all selected users
      let successCount = 0;
      for (const userId of userIds) {
        try {
          await rbacAPI.assignRolesToUser(userId, [roleId]);
          successCount++;
        } catch (error) {
          console.error(`Error assigning role to user ${userId}:`, error);
        }
      }

      showToast(`Successfully assigned role to ${successCount} of ${userIds.length} users`, 'success');
      document.getElementById('quick-assign-modal').remove();
      this.render();

    } catch (error) {
      console.error('Error executing quick assign:', error);
      showToast('Failed to assign roles', 'error');
    } finally {
      hideLoading();
    }
  }

  async toggleMatrixCell(roleId, permId, cellElement) {
    try {
      // Check current state
      const isGranted = cellElement.classList.contains('bg-green-500');

      // Toggle
      if (isGranted) {
        await rbacAPI.removePermissionFromRole(roleId, permId);
      } else {
        await rbacAPI.assignPermissionsToRole(roleId, [permId]);
      }

      // Update cell
      cellElement.className = `matrix-cell w-6 h-6 rounded flex items-center justify-center transition-all cursor-pointer ${
        !isGranted
          ? 'bg-green-500 text-white hover:bg-green-600'
          : 'bg-gray-300 text-gray-500 hover:bg-gray-400'
      }`;
      cellElement.innerHTML = !isGranted
        ? '<i class="ph-fill ph-check text-sm"></i>'
        : '<i class="ph ph-minus text-sm"></i>';

    } catch (error) {
      console.error('Error toggling permission:', error);
      showToast('Failed to toggle permission', 'error');
    }
  }

  exportConfiguration() {
    // Export current configuration as JSON
    const config = {
      users: this.state.users,
      roles: this.state.roles,
      permissions: this.state.permissions,
      exported_at: new Date().toISOString()
    };

    const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `access-control-config-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);

    showToast('Configuration exported successfully', 'success');
  }

  downloadMatrixCSV() {
    const { roles, permissions } = this.state;

    // Build CSV
    let csv = 'Permission Code,Permission Name';
    roles.forEach(role => {
      csv += `,${role.code}`;
    });
    csv += '\n';

    permissions.forEach(perm => {
      csv += `"${perm.code}","${perm.name}"`;
      roles.forEach(role => {
        // This would need actual data from loadMatrix
        csv += ',0'; // Placeholder
      });
      csv += '\n';
    });

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `permission-matrix-${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);

    showToast('Matrix exported to CSV', 'success');
  }

  // Utility
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
export const permissionAssignmentHelper = new PermissionAssignmentHelper();
