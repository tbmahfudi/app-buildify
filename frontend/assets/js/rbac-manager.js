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
    this.selectedCompanyId = null; // null = "All Companies"
    this.companies = [];
  }

  async init() {
    if (this.initPromise) return this.initPromise;

    this.initPromise = (async () => {
      console.log('Initializing RBAC Manager (Refactored)...');

      try {
        // Setup keyboard shortcuts
        this.setupKeyboardShortcuts();

        // Check if tenant admin or superuser
        const currentUser = getCurrentUser();
        if (currentUser?.is_superuser || this.isTenantAdmin(currentUser)) {
          await this.setupCompanySelector();
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
    const filterParams = this.getFilterParams();

    switch (tabId) {
      case 'dashboard':
        await this.loadDashboard();
        break;
      case 'organization':
        await this.loadOrganizationStructure();
        break;
      case 'roles':
        await this.tables.roles.load(filterParams);
        break;
      case 'groups':
        await this.tables.groups.load(filterParams);
        break;
      case 'users':
        await this.tables.users.load(filterParams);
        break;
    }
  }

  async loadDashboard() {
    try {
      const stats = await rbacAPI.getDashboardStats(this.selectedCompanyId);

      document.getElementById('stat-roles').textContent = stats.totalRoles;
      document.getElementById('stat-permissions').textContent = stats.totalPermissions;
      document.getElementById('stat-groups').textContent = stats.totalGroups;
      document.getElementById('stat-users').textContent = stats.totalUsers;

      // Update context header
      this.renderDashboardContext();

      // Render additional insights
      this.renderDashboardInsights(stats);

      const contextText = this.selectedCompanyId
        ? ` - ${this.companies.find(c => c.id === this.selectedCompanyId)?.name || 'Company'}`
        : ' - All Companies';

      console.log(`✓ Dashboard loaded${contextText}`);

    } catch (error) {
      console.error('Error loading dashboard:', error);
      showToast('Failed to load dashboard', 'error');
    }
  }

  renderDashboardContext() {
    const headerEl = document.getElementById('dashboard-context-header');
    if (!headerEl) return;

    if (this.selectedCompanyId) {
      const company = this.companies.find(c => c.id === this.selectedCompanyId);
      if (company) {
        headerEl.innerHTML = `
          <div class="bg-gradient-to-r from-blue-500 to-indigo-600 rounded-xl shadow-lg p-6 text-white">
            <div class="flex items-center justify-between">
              <div>
                <div class="flex items-center gap-3 mb-2">
                  <i class="ph-fill ph-buildings text-3xl"></i>
                  <h2 class="text-2xl font-bold">${company.name}</h2>
                </div>
                <p class="text-blue-100">Company Access Control Overview</p>
              </div>
              <div class="text-right">
                <div class="text-sm text-blue-100">Viewing Company Scope</div>
                <div class="text-xs text-blue-200 mt-1">${company.code || 'N/A'}</div>
              </div>
            </div>
          </div>
        `;
      }
    } else {
      headerEl.innerHTML = `
        <div class="bg-gradient-to-r from-gray-700 to-gray-900 rounded-xl shadow-lg p-6 text-white">
          <div class="flex items-center justify-between">
            <div>
              <div class="flex items-center gap-3 mb-2">
                <i class="ph-fill ph-globe text-3xl"></i>
                <h2 class="text-2xl font-bold">Tenant Overview</h2>
              </div>
              <p class="text-gray-300">All Companies - Organization-wide Statistics</p>
            </div>
            <div class="text-right">
              <div class="text-sm text-gray-300">Viewing All Companies</div>
              <div class="text-xs text-gray-400 mt-1">${this.companies.length} companies total</div>
            </div>
          </div>
        </div>
      `;
    }
  }

  renderDashboardInsights(stats) {
    const insightsEl = document.getElementById('dashboard-insights');
    if (!insightsEl) return;

    const insights = [];

    // Role Distribution Insight
    insights.push(`
      <div class="bg-white rounded-xl shadow p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <i class="ph ph-user-gear text-blue-600"></i>
          Role Distribution
        </h3>
        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-600">System Roles</span>
            <span class="px-3 py-1 bg-red-100 text-red-700 rounded-full text-sm font-medium">Protected</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-600">Custom Roles</span>
            <span class="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm font-medium">Editable</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-600">Total Active</span>
            <span class="text-2xl font-bold text-gray-900">${stats.totalRoles}</span>
          </div>
        </div>
      </div>
    `);

    // Access Control Insight
    const scopeLabel = this.selectedCompanyId ? 'Company' : 'Organization';
    insights.push(`
      <div class="bg-white rounded-xl shadow p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <i class="ph ph-shield-check text-green-600"></i>
          ${scopeLabel} Access Summary
        </h3>
        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-600">Active Users</span>
            <span class="text-2xl font-bold text-gray-900">${stats.totalUsers}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-600">User Groups</span>
            <span class="text-2xl font-bold text-gray-900">${stats.totalGroups}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-600">Permissions</span>
            <span class="text-2xl font-bold text-gray-900">${stats.totalPermissions}</span>
          </div>
        </div>
      </div>
    `);

    insightsEl.innerHTML = insights.join('');
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

      // Load roles and permissions with company filter
      const filterParams = this.getFilterParams();
      const [rolesData, permsData] = await Promise.all([
        rbacAPI.getRoles({ ...filterParams, limit: 100 }),
        rbacAPI.getPermissions({ ...filterParams, limit: 500 })
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
            <div>
              <p class="text-sm text-gray-600 mb-2">
                <strong>${roles.length}</strong> roles × <strong>${permissions.length}</strong> permissions
              </p>
              <div class="flex items-center gap-2 flex-wrap text-xs">
                <span class="text-gray-500">Scopes:</span>
                ${this.renderScopeBadge('all')}
                ${this.renderScopeBadge('tenant')}
                ${this.renderScopeBadge('company')}
                ${this.renderScopeBadge('branch')}
                ${this.renderScopeBadge('own')}
              </div>
            </div>
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
                          ${this.renderScopeBadge(perm.scope)}
                          <span class="text-xs text-gray-500 truncate max-w-[150px]" title="${perm.name}">${perm.name}</span>
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

      const filterParams = this.getFilterParams();
      const [rolesData, permsData] = await Promise.all([
        rbacAPI.getRoles({ ...filterParams, limit: 100 }),
        rbacAPI.getPermissions({ ...filterParams, limit: 500 })
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
    // If company is selected, zoom to that company's structure
    if (this.selectedCompanyId) {
      const selectedCompany = data.companies?.find(c => c.id === this.selectedCompanyId);

      if (!selectedCompany) {
        return `
          <div class="text-center py-12">
            <i class="ph-duotone ph-building-x text-6xl text-gray-300 mb-4"></i>
            <p class="text-gray-500">Company not found</p>
          </div>
        `;
      }

      // Render zoomed company view
      return `
        <div class="space-y-4">
          <!-- Company Header -->
          <div class="p-6 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-lg text-white">
            <div class="flex items-center justify-between">
              <div>
                <h3 class="text-2xl font-bold mb-1">${selectedCompany.name}</h3>
                <p class="text-blue-100 text-sm">${selectedCompany.code || 'Company'}</p>
              </div>
              <div class="text-right">
                <div class="text-sm text-blue-100">Organization Structure</div>
                <div class="text-xs text-blue-200 mt-1">
                  ${selectedCompany.branches?.length || 0} Branches •
                  ${(selectedCompany.branches || []).reduce((sum, b) => sum + (b.departments?.length || 0), 0)} Departments
                </div>
              </div>
            </div>
          </div>

          <!-- Branches -->
          ${selectedCompany.branches?.length > 0 ? `
            <div class="space-y-3">
              ${selectedCompany.branches.map(branch => `
                <div class="border border-gray-200 rounded-lg bg-white hover:shadow-md transition-shadow">
                  <div class="p-4 bg-gray-50 border-b border-gray-200">
                    <div class="flex items-center justify-between">
                      <div class="flex items-center gap-3">
                        <div class="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                          <i class="ph-fill ph-buildings text-green-600 text-xl"></i>
                        </div>
                        <div>
                          <h4 class="font-semibold text-gray-900">${branch.name}</h4>
                          <p class="text-sm text-gray-600">${branch.code || 'Branch'}</p>
                        </div>
                      </div>
                      <span class="px-3 py-1 ${branch.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'} text-xs font-medium rounded-full">
                        ${branch.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                  </div>

                  <!-- Departments -->
                  ${branch.departments?.length > 0 ? `
                    <div class="p-4">
                      <div class="text-xs font-semibold text-gray-500 uppercase mb-3">Departments</div>
                      <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                        ${branch.departments.map(dept => `
                          <div class="p-3 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors">
                            <div class="flex items-center gap-2">
                              <i class="ph ph-users-three text-blue-600"></i>
                              <span class="font-medium text-gray-900">${dept.name}</span>
                            </div>
                            <p class="text-xs text-gray-500 mt-1">${dept.code || ''}</p>
                          </div>
                        `).join('')}
                      </div>
                    </div>
                  ` : '<div class="p-4 text-center text-sm text-gray-500">No departments</div>'}
                </div>
              `).join('')}
            </div>
          ` : `
            <div class="text-center py-12 bg-gray-50 rounded-lg">
              <i class="ph-duotone ph-buildings text-6xl text-gray-300 mb-4"></i>
              <p class="text-gray-500">No branches in this company</p>
            </div>
          `}
        </div>
      `;
    }

    // Full tenant view
    return `
      <div class="space-y-4">
        <!-- Tenant Header -->
        <div class="p-6 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-lg text-white">
          <h3 class="text-2xl font-bold mb-1">${data.tenant?.name || 'Organization'}</h3>
          <p class="text-blue-100 text-sm">Complete Organization Hierarchy</p>
          <div class="text-xs text-blue-200 mt-2">
            ${data.companies?.length || 0} Companies
          </div>
        </div>

        <!-- Companies List -->
        ${data.companies?.length > 0 ? `
          <div class="space-y-3">
            ${data.companies.map(company => `
              <div class="border border-gray-200 rounded-lg bg-white hover:shadow-md transition-shadow">
                <div class="p-4 bg-gray-50 border-b">
                  <div class="flex items-center justify-between">
                    <div class="flex items-center gap-3">
                      <div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                        <i class="ph-fill ph-buildings text-blue-600 text-2xl"></i>
                      </div>
                      <div>
                        <h4 class="font-bold text-gray-900">${company.name}</h4>
                        <p class="text-sm text-gray-600">${company.code || 'Company'}</p>
                      </div>
                    </div>
                    <div class="text-right text-sm text-gray-600">
                      <div>${company.branches?.length || 0} branches</div>
                      <div class="text-xs text-gray-500">${(company.branches || []).reduce((sum, b) => sum + (b.departments?.length || 0), 0)} departments</div>
                    </div>
                  </div>
                </div>

                <!-- Branches Summary -->
                ${company.branches?.length > 0 ? `
                  <div class="p-4">
                    <div class="flex flex-wrap gap-2">
                      ${company.branches.map(branch => `
                        <span class="px-3 py-1 bg-gray-100 text-gray-700 text-sm rounded-full">
                          ${branch.name} (${branch.departments?.length || 0})
                        </span>
                      `).join('')}
                    </div>
                  </div>
                ` : ''}
              </div>
            `).join('')}
          </div>
        ` : `
          <div class="text-center py-12 bg-gray-50 rounded-lg">
            <i class="ph-duotone ph-buildings text-6xl text-gray-300 mb-4"></i>
            <p class="text-gray-500">No companies in this organization</p>
          </div>
        `}
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
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div class="flex items-start gap-3">
                <i class="ph ph-info text-blue-600 text-xl mt-0.5"></i>
                <div class="flex-1">
                  <h4 class="font-semibold text-blue-900 mb-1">RBAC Model</h4>
                  <p class="text-sm text-blue-800">
                    Roles are assigned through group membership. Add users to groups, then assign roles to those groups.
                  </p>
                </div>
              </div>
            </div>

            <div>
              <h4 class="font-semibold text-gray-900 mb-2">Roles via Groups</h4>
              <div class="space-y-2">
                ${roles.roles?.length > 0
                  ? roles.roles.map(r => `
                      <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div class="flex items-center gap-3">
                          <i class="ph ph-users-three text-purple-600"></i>
                          <div>
                            <span class="font-medium text-gray-900">${r.role_name}</span>
                            <span class="text-xs text-gray-500 ml-2">via ${r.group_name}</span>
                          </div>
                        </div>
                        <span class="px-2 py-1 text-xs ${r.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'} rounded-full">
                          ${r.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </div>
                    `).join('')
                  : '<span class="text-sm text-gray-500">No roles assigned. Add user to groups to grant roles.</span>'}
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

  isTenantAdmin(user) {
    // Check if user has tenant_admin role
    return user?.roles?.some(role => role.code === 'tenant_admin');
  }

  isCompanyManager(user) {
    // Check if user has company_manager role
    return user?.roles?.some(role => role.code === 'company_manager');
  }

  getUserCompanyId(user) {
    // Get user's primary company_id
    // Assuming user object has company_id or companies array
    return user?.company_id || user?.companies?.[0]?.id || null;
  }

  getFilterParams() {
    // Return query parameters for company filtering
    return this.selectedCompanyId ? { company_id: this.selectedCompanyId } : {};
  }

  async setupCompanySelector() {
    try {
      const currentUser = getCurrentUser();

      // Load companies
      const response = await rbacAPI.getCompanies({ limit: 1000 });
      this.companies = response.items || [];

      const container = document.getElementById('company-selector-container');
      const selector = document.getElementById('company-selector');

      if (!container || !selector) return;

      // Show container
      container.classList.remove('hidden');

      // Determine if user can switch companies
      const canSwitchCompanies = currentUser?.is_superuser || this.isTenantAdmin(currentUser);

      if (canSwitchCompanies) {
        // Tenant Admin / Superuser: Show dropdown
        selector.innerHTML = '<option value="">All Companies</option>';
        this.companies.forEach(company => {
          const option = document.createElement('option');
          option.value = company.id;
          option.textContent = company.name;
          selector.appendChild(option);
        });

        // Setup change handler
        selector.addEventListener('change', (e) => {
          this.selectedCompanyId = e.target.value || null;
          this.onCompanyChange();
        });

        console.log(`✓ Company selector loaded with ${this.companies.length} companies`);
      } else if (this.isCompanyManager(currentUser)) {
        // Company Manager: Auto-scope to their company
        const userCompanyId = this.getUserCompanyId(currentUser);

        if (userCompanyId) {
          this.selectedCompanyId = userCompanyId;
          const userCompany = this.companies.find(c => c.id === userCompanyId);

          // Replace dropdown with read-only badge
          container.innerHTML = `
            <div class="flex items-center gap-2">
              <label class="text-sm font-medium text-gray-700">
                <i class="ph ph-buildings mr-1"></i>Company Context
              </label>
              <div class="px-4 py-2 bg-blue-50 border border-blue-200 rounded-lg flex items-center gap-2">
                <i class="ph-fill ph-buildings text-blue-600"></i>
                <span class="text-sm font-semibold text-blue-900">${userCompany?.name || 'Your Company'}</span>
                <span class="px-2 py-0.5 bg-blue-200 text-blue-800 text-xs rounded">Scoped</span>
              </div>
            </div>
          `;

          // Update page context to show banner
          this.updatePageContext();

          console.log(`✓ Company manager scoped to: ${userCompany?.name}`);
        }
      }
    } catch (error) {
      console.error('Error setting up company selector:', error);
      showToast('Failed to load companies', 'error');
    }
  }

  updatePageContext() {
    // Update page header to show current company context
    const headerTitle = document.querySelector('header h1 span');
    const headerSubtitle = document.querySelector('header p.text-gray-600');

    if (!headerTitle || !headerSubtitle) return;

    if (this.selectedCompanyId) {
      const company = this.companies.find(c => c.id === this.selectedCompanyId);
      if (company) {
        // Add company context banner
        let contextBanner = document.getElementById('company-context-banner');
        if (!contextBanner) {
          contextBanner = document.createElement('div');
          contextBanner.id = 'company-context-banner';
          contextBanner.className = 'bg-blue-50 border-b border-blue-200 py-2 px-4';

          const header = document.querySelector('header');
          if (header) {
            header.insertAdjacentElement('afterend', contextBanner);
          }
        }

        contextBanner.innerHTML = `
          <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex items-center justify-between text-sm">
              <div class="flex items-center gap-2 text-blue-800">
                <i class="ph-fill ph-funnel text-blue-600"></i>
                <span>Filtered to:</span>
                <strong>${company.name}</strong>
              </div>
              <button onclick="rbacManager.clearCompanyFilter()" class="text-blue-600 hover:text-blue-800 font-medium flex items-center gap-1">
                <i class="ph ph-x-circle"></i>
                <span>View All Companies</span>
              </button>
            </div>
          </div>
        `;
      }
    } else {
      // Remove context banner
      const contextBanner = document.getElementById('company-context-banner');
      if (contextBanner) {
        contextBanner.remove();
      }
    }
  }

  clearCompanyFilter() {
    const selector = document.getElementById('company-selector');
    if (selector) {
      selector.value = '';
      this.selectedCompanyId = null;
      this.onCompanyChange();
    }
  }

  async onCompanyChange() {
    try {
      showLoading();

      // Update page context indicator
      this.updatePageContext();

      // Refresh current view with new company filter
      await this.loadTabData(this.currentTab);

      const companyName = this.selectedCompanyId
        ? this.companies.find(c => c.id === this.selectedCompanyId)?.name
        : 'All Companies';

      showToast(`Viewing: ${companyName}`, 'info');
    } catch (error) {
      console.error('Error changing company:', error);
      showToast('Failed to switch company context', 'error');
    } finally {
      hideLoading();
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

  renderScopeBadge(scope) {
    const scopeConfig = {
      'all': { color: 'purple', icon: 'globe', label: 'System' },
      'tenant': { color: 'blue', icon: 'buildings', label: 'Tenant' },
      'company': { color: 'green', icon: 'building', label: 'Company' },
      'branch': { color: 'yellow', icon: 'office', label: 'Branch' },
      'department': { color: 'orange', icon: 'users-three', label: 'Dept' },
      'own': { color: 'gray', icon: 'user', label: 'Own' }
    };

    const config = scopeConfig[scope] || scopeConfig['tenant'];
    const colorClasses = {
      'purple': 'bg-purple-100 text-purple-700 border-purple-200',
      'blue': 'bg-blue-100 text-blue-700 border-blue-200',
      'green': 'bg-green-100 text-green-700 border-green-200',
      'yellow': 'bg-yellow-100 text-yellow-700 border-yellow-200',
      'orange': 'bg-orange-100 text-orange-700 border-orange-200',
      'gray': 'bg-gray-100 text-gray-700 border-gray-200'
    };

    return `
      <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded border text-xs font-medium ${colorClasses[config.color]}" title="Scope: ${config.label}">
        <i class="ph ph-${config.icon} text-xs"></i>
        <span>${config.label}</span>
      </span>
    `;
  }

  renderRoleTypeBadge(role) {
    const typeConfig = {
      'system': { color: 'red', icon: 'shield-star', label: 'System' },
      'default': { color: 'blue', icon: 'star', label: 'Default' },
      'custom': { color: 'purple', icon: 'pencil', label: 'Custom' }
    };

    const config = typeConfig[role.role_type] || typeConfig['custom'];
    const colorClasses = {
      'red': 'bg-red-100 text-red-700',
      'blue': 'bg-blue-100 text-blue-700',
      'purple': 'bg-purple-100 text-purple-700'
    };

    return `
      <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${colorClasses[config.color]}">
        <i class="ph ph-${config.icon} text-xs"></i>
        <span>${config.label}</span>
      </span>
    `;
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
