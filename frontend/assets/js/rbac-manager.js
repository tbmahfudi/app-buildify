/**
 * RBAC Manager - Refactored
 * Main orchestrator for RBAC UI - Now much simpler with modular architecture
 */

import { getCurrentUser } from './app.js';
import { showToast, showLoading, hideLoading } from './ui-utils.js';
import { TableController } from './rbac/table-controller.js';
import { modalManager } from './rbac/modal-controller.js';
import { rbacAPI } from './rbac/rbac-api.js';
import { permissionGrid } from './rbac/permission-grid.js';
import { permissionAssignmentHelper } from './rbac/permission-assignment-helper.js';
import { keyboardShortcuts, setupDefaultShortcuts } from './rbac/keyboard-shortcuts.js';

class RBACManager {
  constructor() {
    this.tables = {};
    this.currentTab = 'dashboard';
    this.initPromise = null;
  }

  async init() {
    if (this.initPromise) return this.initPromise;

    this.initPromise = (async () => {
      console.log('Initializing RBAC Manager (Refactored)...');

      try {
        // Setup keyboard shortcuts
        this.setupKeyboardShortcuts();

        // Check if superuser
        const currentUser = getCurrentUser();
        if (currentUser?.is_superuser) {
          await this.setupTenantSelector();
        }

        // Setup tabs
        this.setupTabNavigation();

        // Initialize tables
        this.initializeTables();

        // Load dashboard
        await this.loadDashboard();

        console.log('RBAC Manager initialized successfully');
      } catch (error) {
        console.error('Error initializing RBAC Manager:', error);
        showToast('Failed to initialize RBAC interface', 'error');
        throw error;
      }
    })();

    return this.initPromise;
  }

  setupKeyboardShortcuts() {
    setupDefaultShortcuts(keyboardShortcuts, {
      focusSearch: () => {
        const searchInput = document.querySelector('.rbac-content:not(.hidden) input[type="text"]');
        searchInput?.focus();
      },
      showCommandPalette: () => {
        showToast('Command palette coming soon', 'info');
      },
      closeModal: () => {
        modalManager.closeAll();
      },
      switchTab: (tabName) => {
        document.getElementById(`tab-${tabName}`)?.click();
      },
      newItem: () => {
        if (this.currentTab === 'users') {
          document.getElementById('btn-add-user')?.click();
        }
      },
      save: () => {
        // Save current modal if open
        const saveBtn = document.querySelector('.modal:not(.hidden) [data-action="save"]');
        saveBtn?.click();
      },
      refresh: () => {
        this.refreshCurrentView();
      },
      selectAll: () => {
        const selectAllCheckbox = document.querySelector(`.rbac-content:not(.hidden) input[id$="-select-all"]`);
        if (selectAllCheckbox) {
          selectAllCheckbox.checked = true;
          selectAllCheckbox.dispatchEvent(new Event('change'));
        }
      },
      deselectAll: () => {
        const table = this.tables[this.currentTab];
        table?.clearSelection();
      }
    });
  }

  setupTabNavigation() {
    const tabs = document.querySelectorAll('.rbac-tab');
    tabs.forEach(tab => {
      tab.addEventListener('click', async () => {
        // Update active tab
        tabs.forEach(t => {
          t.classList.remove('active', 'border-blue-600', 'text-blue-600');
          t.classList.add('border-transparent', 'text-gray-500');
        });
        tab.classList.add('active', 'border-blue-600', 'text-blue-600');
        tab.classList.remove('border-transparent', 'text-gray-500');

        // Show corresponding content
        const tabId = tab.id.replace('tab-', '');
        this.currentTab = tabId;
        document.querySelectorAll('.rbac-content').forEach(content => {
          content.classList.add('hidden');
        });
        document.getElementById(`content-${tabId}`).classList.remove('hidden');

        // Load tab data
        await this.loadTabData(tabId);
      });
    });
  }

  initializeTables() {
    // Roles Table - Simplified columns
    this.tables.roles = new TableController({
      name: 'roles',
      endpoint: '/rbac/roles',
      icon: 'user-gear',
      columns: [
        {
          field: 'name',
          render: (role) => `
            <div class="flex items-start gap-3">
              <input type="checkbox" class="row-checkbox w-4 h-4 text-blue-600 rounded mt-1" data-id="${role.id}">
              <div class="flex-1">
                <div class="flex items-center gap-2 mb-1">
                  <span class="font-semibold text-gray-900">${role.name}</span>
                  <span class="px-2 py-0.5 text-xs font-medium rounded-full
                    ${role.role_type === 'system' ? 'bg-red-100 text-red-700' : ''}
                    ${role.role_type === 'default' ? 'bg-blue-100 text-blue-700' : ''}
                    ${role.role_type === 'custom' ? 'bg-purple-100 text-purple-700' : ''}">
                    ${role.role_type}
                  </span>
                  ${role.is_active
                    ? '<span class="px-2 py-0.5 text-xs font-medium rounded-full bg-green-100 text-green-700">Active</span>'
                    : '<span class="px-2 py-0.5 text-xs font-medium rounded-full bg-gray-100 text-gray-600">Inactive</span>'}
                  ${role.is_system ? '<i class="ph ph-lock-simple text-gray-400"></i>' : ''}
                </div>
                <div class="text-sm text-gray-600 font-mono">${role.code}</div>
              </div>
            </div>
          `
        },
        {
          field: 'description',
          render: (role) => `
            <div class="text-sm text-gray-600">
              ${role.description || '<span class="text-gray-400 italic">No description</span>'}
            </div>
          `
        },
        {
          field: 'permissions_count',
          render: (role) => `
            <div class="flex items-center justify-center">
              <span class="inline-flex items-center gap-1 px-3 py-1 text-sm font-semibold rounded-full bg-blue-50 text-blue-700">
                <i class="ph ph-shield-check"></i>
                ${role.permissions?.length || 0}
              </span>
            </div>
          `
        }
      ],
      filters: [
        { id: 'type', label: 'Type' },
        { id: 'status', label: 'Status' }
      ],
      bulkActions: true,
      onRowClick: (role) => this.manageRolePermissions(role.id)
    });

    // Groups Table
    this.tables.groups = new TableController({
      name: 'groups',
      endpoint: '/rbac/groups',
      icon: 'users-three',
      columns: [
        {
          field: 'name',
          render: (group) => `
            <div class="font-medium text-gray-900">${group.name}</div>
            ${group.description ? `<div class="text-sm text-gray-500">${group.description}</div>` : ''}
          `
        },
        {
          field: 'group_type',
          render: (group) => `
            <span class="px-2 py-1 text-xs font-semibold rounded-full bg-purple-100 text-purple-800">
              ${group.group_type}
            </span>
          `
        },
        {
          field: 'members',
          render: (group) => `<span class="text-gray-700">${group.members?.length || 0}</span>`
        },
        {
          field: 'roles',
          render: (group) => `<span class="text-gray-700">${group.roles?.length || 0}</span>`
        },
        {
          field: 'is_active',
          render: (group) => group.is_active
            ? '<span class="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">Active</span>'
            : '<span class="px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">Inactive</span>'
        }
      ],
      filters: [
        { id: 'type', label: 'Type' },
        { id: 'status', label: 'Status' }
      ],
      actions: [
        { icon: 'eye', label: 'View', handler: 'viewGroupDetails', color: 'blue' }
      ],
      onRowClick: (group) => this.viewGroupDetails(group.id)
    });

    // Users Table (merged with User Access functionality)
    this.tables.users = new TableController({
      name: 'users',
      endpoint: '/org/users',
      icon: 'users',
      columns: [
        {
          field: 'full_name',
          render: (user) => `
            <div class="font-medium text-gray-900">${user.full_name || user.email}</div>
            <div class="text-sm text-gray-500">${user.email}</div>
          `
        },
        {
          field: 'roles',
          render: (user) => {
            const roleCount = user.roles?.length || 0;
            return `<span class="text-gray-700">${roleCount} role${roleCount !== 1 ? 's' : ''}</span>`;
          }
        },
        {
          field: 'is_active',
          render: (user) => user.is_active
            ? '<span class="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">Active</span>'
            : '<span class="px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">Inactive</span>'
        },
        {
          field: 'created_at',
          render: (user) => new Date(user.created_at).toLocaleDateString()
        }
      ],
      actions: [
        { icon: 'user-gear', label: 'Manage Access', handler: 'manageUserAccess', color: 'blue' },
        { icon: 'pencil', label: 'Edit', handler: 'editUser', color: 'green' },
        { icon: 'trash', label: 'Delete', handler: 'deleteUser', color: 'red' }
      ],
      onRowClick: (user) => this.manageUserAccess(user.id),
      bulkActions: true
    });
  }

  async loadTabData(tabId) {
    switch (tabId) {
      case 'dashboard':
        await this.loadDashboard();
        break;
      case 'organization':
        await this.loadOrganizationStructure();
        break;
      case 'roles':
        await this.tables.roles.load();
        break;
      case 'groups':
        await this.tables.groups.load();
        break;
      case 'users':
        await this.tables.users.load();
        break;
    }
  }

  async loadDashboard() {
    try {
      const stats = await rbacAPI.getDashboardStats();

      document.getElementById('stat-roles').textContent = stats.totalRoles;
      document.getElementById('stat-permissions').textContent = stats.totalPermissions;
      document.getElementById('stat-groups').textContent = stats.totalGroups;
      document.getElementById('stat-users').textContent = stats.totalUsers;

      // Load charts if needed
      // ...

    } catch (error) {
      console.error('Error loading dashboard:', error);
      showToast('Failed to load dashboard', 'error');
    }
  }

  async loadOrganizationStructure() {
    try {
      showLoading();
      const data = await rbacAPI.getOrganizationStructure();

      const container = document.getElementById('org-structure-tree');
      if (container) {
        container.innerHTML = this.renderOrgStructure(data);
      }

    } catch (error) {
      console.error('Error loading organization:', error);
      showToast('Failed to load organization structure', 'error');
    } finally {
      hideLoading();
    }
  }

  async openPermissionMatrix() {
    try {
      showLoading();

      const modal = document.getElementById('permission-matrix-modal');
      const content = document.getElementById('permission-matrix-content');

      if (!modal) {
        showToast('Permission Matrix modal not found', 'error');
        return;
      }

      // Show modal
      modal.classList.remove('hidden');

      // Load roles and permissions
      const [rolesData, permsData] = await Promise.all([
        rbacAPI.getRoles({ limit: 100 }),
        rbacAPI.getPermissions({ limit: 500 })
      ]);

      const roles = rolesData.items || [];
      const permissions = permsData.items || [];

      // Group permissions by category
      const permsByCategory = {};
      permissions.forEach(perm => {
        const cat = perm.category || 'Other';
        if (!permsByCategory[cat]) permsByCategory[cat] = [];
        permsByCategory[cat].push(perm);
      });

      // Render matrix
      content.innerHTML = `
        <div class="h-full flex flex-col">
          <div class="mb-4 flex items-center justify-between flex-shrink-0">
            <p class="text-sm text-gray-600">
              <strong>${roles.length}</strong> roles × <strong>${permissions.length}</strong> permissions
            </p>
            <div class="flex items-center gap-4 text-xs text-gray-500">
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

          <div class="flex-1 overflow-auto border border-gray-200 rounded-lg">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50 sticky top-0 z-10">
                <tr>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase sticky left-0 bg-gray-50 border-r min-w-[250px]">
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
                          <span class="text-xs text-gray-500">${perm.name}</span>
                        </div>
                      </td>
                      ${roles.map(role => `
                        <td class="px-3 py-2 text-center">
                          <button
                            data-action="toggle-matrix-cell"
                            data-role-id="${role.id}"
                            data-perm-id="${perm.id}"
                            class="matrix-cell-${role.id}-${perm.id} w-6 h-6 rounded flex items-center justify-center transition-all mx-auto
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
        </div>
      `;

      // Load matrix data (lazy load per role to avoid overwhelming the browser)
      this.loadMatrixData(roles, permissions);

      // Setup click handlers for matrix cells
      content.addEventListener('click', async (e) => {
        const button = e.target.closest('[data-action="toggle-matrix-cell"]');
        if (!button) return;

        const roleId = button.dataset.roleId;
        const permId = button.dataset.permId;

        await this.toggleMatrixCell(roleId, permId, button);
      });

      console.log('✓ Permission Matrix loaded successfully');

    } catch (error) {
      console.error('Error loading Permission Matrix:', error);
      showToast('Failed to load Permission Matrix', 'error');
    } finally {
      hideLoading();
    }
  }

  async loadMatrixData(roles, permissions) {
    try {
      // Load role permissions in batches to avoid overwhelming the browser
      const batchSize = 5;
      for (let i = 0; i < roles.length; i += batchSize) {
        const batch = roles.slice(i, i + batchSize);

        await Promise.all(
          batch.map(async role => {
            try {
              const roleData = await rbacAPI.getRole(role.id);
              const permIds = new Set((roleData.permissions || []).map(p => p.id));

              // Update cells for this role
              permissions.forEach(perm => {
                const cell = document.querySelector(`.matrix-cell-${role.id}-${perm.id}`);
                if (cell) {
                  const hasPermission = permIds.has(perm.id);
                  cell.className = `matrix-cell-${role.id}-${perm.id} w-6 h-6 rounded flex items-center justify-center transition-all cursor-pointer mx-auto ${
                    hasPermission
                      ? 'bg-green-500 text-white hover:bg-green-600'
                      : 'bg-gray-300 text-gray-500 hover:bg-gray-400'
                  }`;
                  cell.innerHTML = hasPermission
                    ? '<i class="ph-fill ph-check text-sm"></i>'
                    : '<i class="ph ph-minus text-sm"></i>';
                }
              });
            } catch (error) {
              console.error(`Error loading permissions for role ${role.id}:`, error);
            }
          })
        );

        // Small delay between batches to keep UI responsive
        await new Promise(resolve => setTimeout(resolve, 50));
      }
    } catch (error) {
      console.error('Error loading matrix data:', error);
    }
  }

  async toggleMatrixCell(roleId, permId, cellElement) {
    try {
      const isGranted = cellElement.classList.contains('bg-green-500');

      if (isGranted) {
        await rbacAPI.removePermissionFromRole(roleId, permId);
      } else {
        await rbacAPI.assignPermissionsToRole(roleId, [permId]);
      }

      // Update cell
      cellElement.className = cellElement.className.replace(
        isGranted ? 'bg-green-500 text-white hover:bg-green-600' : 'bg-gray-300 text-gray-500 hover:bg-gray-400',
        !isGranted ? 'bg-green-500 text-white hover:bg-green-600' : 'bg-gray-300 text-gray-500 hover:bg-gray-400'
      );
      cellElement.innerHTML = !isGranted
        ? '<i class="ph-fill ph-check text-sm"></i>'
        : '<i class="ph ph-minus text-sm"></i>';

      showToast(`Permission ${!isGranted ? 'granted' : 'revoked'}`, 'success');

    } catch (error) {
      console.error('Error toggling permission:', error);
      showToast('Failed to toggle permission', 'error');
    }
  }

  closePermissionMatrix() {
    const modal = document.getElementById('permission-matrix-modal');
    if (modal) {
      modal.classList.add('hidden');
    }
  }

  async exportMatrixCSV() {
    try {
      showLoading();

      const [rolesData, permsData] = await Promise.all([
        rbacAPI.getRoles({ limit: 100 }),
        rbacAPI.getPermissions({ limit: 500 })
      ]);

      const roles = rolesData.items || [];
      const permissions = permsData.items || [];

      // Load all role permissions
      const rolePermMap = new Map();
      await Promise.all(
        roles.map(async role => {
          const roleData = await rbacAPI.getRole(role.id);
          const permIds = new Set((roleData.permissions || []).map(p => p.id));
          rolePermMap.set(role.id, permIds);
        })
      );

      // Build CSV
      let csv = 'Permission Code,Permission Name,Category';
      roles.forEach(role => {
        csv += `,${role.code}`;
      });
      csv += '\n';

      permissions.forEach(perm => {
        csv += `"${perm.code}","${perm.name}","${perm.category || 'Other'}"`;
        roles.forEach(role => {
          const hasPermission = rolePermMap.get(role.id)?.has(perm.id) ? '1' : '0';
          csv += `,${hasPermission}`;
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

    } catch (error) {
      console.error('Error exporting matrix:', error);
      showToast('Failed to export matrix', 'error');
    } finally {
      hideLoading();
    }
  }

  renderOrgStructure(data) {
    // Simple org structure renderer
    return `
      <div class="space-y-4">
        <div class="p-4 bg-blue-50 rounded-lg">
          <h4 class="font-semibold text-gray-900">${data.tenant?.name || 'Organization'}</h4>
        </div>
        ${data.companies?.map(company => `
          <div class="ml-6 p-4 border-l-2 border-gray-300">
            <div class="font-medium text-gray-900">${company.name}</div>
            <div class="text-sm text-gray-500 mt-1">
              ${company.branches?.length || 0} branches,
              ${company.departments?.length || 0} departments
            </div>
          </div>
        `).join('') || ''}
      </div>
    `;
  }

  async viewRoleDetails(roleId) {
    try {
      showLoading();
      const role = await rbacAPI.getRole(roleId);

      modalManager.open('role-modal', {
        title: role.name,
        content: `
          <div class="space-y-6">
            <div>
              <h4 class="font-semibold text-gray-900 mb-2">Basic Information</h4>
              <dl class="grid grid-cols-2 gap-4">
                <div>
                  <dt class="text-sm text-gray-500">Code</dt>
                  <dd class="text-sm font-medium text-gray-900">${role.code}</dd>
                </div>
                <div>
                  <dt class="text-sm text-gray-500">Type</dt>
                  <dd class="text-sm font-medium text-gray-900">${role.role_type}</dd>
                </div>
              </dl>
            </div>

            <div>
              <div class="flex items-center justify-between mb-2">
                <h4 class="font-semibold text-gray-900">Permissions (${role.permissions?.length || 0})</h4>
                <button onclick="rbacManager.manageRolePermissions('${role.id}')"
                  class="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                  <i class="ph ph-gear"></i> Manage Permissions
                </button>
              </div>
              <div class="flex flex-wrap gap-2">
                ${role.permissions?.length > 0
                  ? role.permissions.map(p => `
                      <span class="px-3 py-1 text-xs font-mono bg-blue-100 text-blue-800 rounded-full">${p.code}</span>
                    `).join('')
                  : '<span class="text-sm text-gray-500">No permissions assigned</span>'}
              </div>
            </div>
          </div>
        `
      });

    } catch (error) {
      console.error('Error loading role details:', error);
      showToast('Failed to load role details', 'error');
    } finally {
      hideLoading();
    }
  }

  async viewGroupDetails(groupId) {
    try {
      showLoading();
      const group = await rbacAPI.getGroup(groupId);

      modalManager.open('group-modal', {
        title: group.name,
        content: `
          <div class="space-y-6">
            <div>
              <h4 class="font-semibold text-gray-900 mb-2">Members (${group.members?.length || 0})</h4>
              <div class="space-y-2">
                ${group.members?.length > 0
                  ? group.members.slice(0, 10).map(m => `
                      <div class="flex items-center gap-2 text-sm">
                        <i class="ph ph-user-circle text-gray-400"></i>
                        <span>${m.email}</span>
                      </div>
                    `).join('')
                  : '<span class="text-sm text-gray-500">No members</span>'}
              </div>
            </div>

            <div>
              <h4 class="font-semibold text-gray-900 mb-2">Roles (${group.roles?.length || 0})</h4>
              <div class="flex flex-wrap gap-2">
                ${group.roles?.length > 0
                  ? group.roles.map(r => `
                      <span class="px-3 py-1 text-xs bg-purple-100 text-purple-800 rounded-full">${r.name}</span>
                    `).join('')
                  : '<span class="text-sm text-gray-500">No roles assigned</span>'}
              </div>
            </div>
          </div>
        `
      });

    } catch (error) {
      console.error('Error loading group details:', error);
      showToast('Failed to load group details', 'error');
    } finally {
      hideLoading();
    }
  }

  manageRolePermissions(roleId) {
    permissionGrid.openCard(roleId);
  }

  closePermissionCard() {
    permissionGrid.closeCard();
  }

  async manageUserAccess(userId) {
    // Show user access management in a modal or side panel
    try {
      showLoading();
      const [roles, permissions] = await Promise.all([
        rbacAPI.getUserRoles(userId),
        rbacAPI.getUserPermissions(userId)
      ]);

      modalManager.open('user-modal', {
        title: `User Access: ${roles.email}`,
        content: `
          <div class="space-y-6">
            <div>
              <h4 class="font-semibold text-gray-900 mb-2">Direct Roles</h4>
              <div class="flex flex-wrap gap-2">
                ${roles.direct_roles?.length > 0
                  ? roles.direct_roles.map(r => `
                      <span class="px-3 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">${r.name}</span>
                    `).join('')
                  : '<span class="text-sm text-gray-500">No direct roles</span>'}
              </div>
            </div>

            <div>
              <h4 class="font-semibold text-gray-900 mb-2">Effective Permissions (${permissions.permissions?.length || 0})</h4>
              <div class="flex flex-wrap gap-2 max-h-48 overflow-y-auto">
                ${permissions.permissions?.map(p => `
                  <span class="px-2 py-1 text-xs font-mono bg-green-100 text-green-800 rounded">${p.code}</span>
                `).join('')}
              </div>
            </div>
          </div>
        `
      });

    } catch (error) {
      console.error('Error loading user access:', error);
      showToast('Failed to load user access', 'error');
    } finally {
      hideLoading();
    }
  }

  editUser(userId) {
    showToast('User edit coming soon', 'info');
  }

  async deleteUser(userId) {
    if (!confirm('Are you sure you want to delete this user?')) return;

    try {
      showLoading();
      await rbacAPI.deleteUser(userId);
      showToast('User deleted successfully', 'success');
      this.tables.users.refresh();
    } catch (error) {
      console.error('Error deleting user:', error);
      showToast('Failed to delete user', 'error');
    } finally {
      hideLoading();
    }
  }

  async setupTenantSelector() {
    // Superuser tenant selector logic
    const container = document.getElementById('tenant-selector-container');
    if (container) {
      container.classList.remove('hidden');
    }
  }

  refreshCurrentView() {
    const table = this.tables[this.currentTab];
    if (table) {
      table.refresh();
    } else {
      this.loadTabData(this.currentTab);
    }
  }
}

// Create instance
const rbacManager = new RBACManager();

// Expose to global scope for onclick handlers
window.rbacManager = rbacManager;

// Export initialization function for route handlers
export async function initRBACManager() {
  return await rbacManager.init();
}

// Export instance
export { rbacManager };
export default rbacManager;
