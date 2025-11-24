/**
 * RBAC Management Module
 * Provides comprehensive UI for managing roles, permissions, groups, and user access
 */

import { apiFetch } from './api.js';
import { showToast, showLoading, hideLoading } from './ui-utils.js';
import { getCurrentUser } from './app.js';

// State management
const state = {
  roles: [],
  permissions: [],
  groups: [],
  users: [],
  tenants: [],
  orgStructure: null,
  selectedTenantId: null,
  currentPage: {
    roles: 0,
    permissions: 0,
    groups: 0
  },
  filters: {
    roles: { search: '', type: '', status: '' },
    permissions: { search: '', category: '', status: '' },
    groups: { search: '', type: '', status: '' }
  },
  pageSize: 20
};

/**
 * Initialize RBAC Manager
 */
export async function initRBACManager() {
  console.log('Setting up RBAC Manager...');

  try {
    // Check if user is superuser and setup tenant selector
    const currentUser = getCurrentUser();
    if (currentUser && currentUser.is_superuser) {
      console.log('Superuser detected, loading tenant selector...');
      await setupTenantSelector();
    }

    setupTabNavigation();
    console.log('Tab navigation setup complete');

    setupEventListeners();
    console.log('Event listeners setup complete');

    await loadDashboard();
    console.log('Dashboard loaded');
  } catch (error) {
    console.error('Error during RBAC Manager initialization:', error);
    throw error;
  }
}

/**
 * Setup tab navigation
 */
function setupTabNavigation() {
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
      document.querySelectorAll('.rbac-content').forEach(content => {
        content.classList.add('hidden');
      });
      document.getElementById(`content-${tabId}`).classList.remove('hidden');

      // Load tab data
      await loadTabData(tabId);
    });
  });
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
  // Roles filters
  document.getElementById('roles-search')?.addEventListener('input', debounce(() => {
    state.filters.roles.search = document.getElementById('roles-search').value;
    state.currentPage.roles = 0;
    loadRoles();
  }, 300));

  document.getElementById('roles-type-filter')?.addEventListener('change', () => {
    state.filters.roles.type = document.getElementById('roles-type-filter').value;
    state.currentPage.roles = 0;
    loadRoles();
  });

  document.getElementById('roles-status-filter')?.addEventListener('change', () => {
    state.filters.roles.status = document.getElementById('roles-status-filter').value;
    state.currentPage.roles = 0;
    loadRoles();
  });

  // Permissions filters
  document.getElementById('permissions-search')?.addEventListener('input', debounce(() => {
    state.filters.permissions.search = document.getElementById('permissions-search').value;
    state.currentPage.permissions = 0;
    loadPermissions();
  }, 300));

  document.getElementById('permissions-category-filter')?.addEventListener('change', () => {
    state.filters.permissions.category = document.getElementById('permissions-category-filter').value;
    state.currentPage.permissions = 0;
    loadPermissions();
  });

  document.getElementById('permissions-status-filter')?.addEventListener('change', () => {
    state.filters.permissions.status = document.getElementById('permissions-status-filter').value;
    state.currentPage.permissions = 0;
    loadPermissions();
  });

  // Groups filters
  document.getElementById('groups-search')?.addEventListener('input', debounce(() => {
    state.filters.groups.search = document.getElementById('groups-search').value;
    state.currentPage.groups = 0;
    loadGroups();
  }, 300));

  document.getElementById('groups-type-filter')?.addEventListener('change', () => {
    state.filters.groups.type = document.getElementById('groups-type-filter').value;
    state.currentPage.groups = 0;
    loadGroups();
  });

  document.getElementById('groups-status-filter')?.addEventListener('change', () => {
    state.filters.groups.status = document.getElementById('groups-status-filter').value;
    state.currentPage.groups = 0;
    loadGroups();
  });

  // Pagination
  document.getElementById('roles-prev-page')?.addEventListener('click', () => {
    if (state.currentPage.roles > 0) {
      state.currentPage.roles--;
      loadRoles();
    }
  });

  document.getElementById('roles-next-page')?.addEventListener('click', () => {
    state.currentPage.roles++;
    loadRoles();
  });

  document.getElementById('permissions-prev-page')?.addEventListener('click', () => {
    if (state.currentPage.permissions > 0) {
      state.currentPage.permissions--;
      loadPermissions();
    }
  });

  document.getElementById('permissions-next-page')?.addEventListener('click', () => {
    state.currentPage.permissions++;
    loadPermissions();
  });

  document.getElementById('groups-prev-page')?.addEventListener('click', () => {
    if (state.currentPage.groups > 0) {
      state.currentPage.groups--;
      loadGroups();
    }
  });

  document.getElementById('groups-next-page')?.addEventListener('click', () => {
    state.currentPage.groups++;
    loadGroups();
  });

  // User selection
  document.getElementById('user-select')?.addEventListener('change', async (e) => {
    const userId = e.target.value;
    if (userId) {
      await loadUserAccess(userId);
    } else {
      document.getElementById('user-access-details')?.classList.add('hidden');
    }
  });

  // User management
  document.getElementById('btn-add-user')?.addEventListener('click', () => {
    showUserModal();
  });

  document.getElementById('user-modal-close')?.addEventListener('click', () => {
    closeUserModal();
  });

  document.getElementById('user-cancel-btn')?.addEventListener('click', () => {
    closeUserModal();
  });

  document.getElementById('user-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    await saveUser();
  });

  // Modal close buttons
  document.getElementById('role-modal-close')?.addEventListener('click', () => {
    document.getElementById('role-modal').classList.add('hidden');
  });

  document.getElementById('permission-modal-close')?.addEventListener('click', () => {
    document.getElementById('permission-modal').classList.add('hidden');
  });

  document.getElementById('group-modal-close')?.addEventListener('click', () => {
    document.getElementById('group-modal').classList.add('hidden');
  });
}

/**
 * Load tab data based on tab id
 */
async function loadTabData(tabId) {
  showLoading();
  try {
    switch (tabId) {
      case 'dashboard':
        await loadDashboard();
        break;
      case 'organization':
        await loadOrganizationStructure();
        break;
      case 'roles':
        await loadRoles();
        break;
      case 'permissions':
        await loadPermissions();
        await loadPermissionCategories();
        break;
      case 'groups':
        await loadGroups();
        break;
      case 'users':
        await loadUsers();
        break;
      case 'user-access':
        await loadUsersForAccess();
        break;
    }
  } catch (error) {
    console.error('Error loading tab data:', error);
    showToast('Failed to load data', 'error');
  } finally {
    hideLoading();
  }
}

/**
 * Load dashboard statistics
 */
async function loadDashboard() {
  console.log('Loading dashboard...');
  try {
    // Load all data for statistics
    const [rolesRes, permissionsRes, groupsRes, usersRes] = await Promise.all([
      apiFetch('/rbac/roles?limit=1000'),
      apiFetch('/rbac/permissions?limit=1000'),
      apiFetch('/rbac/groups?limit=1000'),
      apiFetch('/org/users?limit=1000')
    ]);

    console.log('API responses received:', { rolesRes, permissionsRes, groupsRes, usersRes });

    // Check if responses are OK with specific error messages
    const checkResponse = (res, name) => {
      if (!res.ok) {
        if (res.status === 403) {
          throw new Error(`Access forbidden - you don't have permission to access ${name}`);
        } else if (res.status === 401) {
          throw new Error('Unauthorized - please log in again');
        } else {
          throw new Error(`${name} API error: HTTP ${res.status}`);
        }
      }
    };

    checkResponse(rolesRes, 'Roles');
    checkResponse(permissionsRes, 'Permissions');
    checkResponse(groupsRes, 'Groups');
    checkResponse(usersRes, 'Users');

    const rolesData = await rolesRes.json();
    const permissionsData = await permissionsRes.json();
    const groupsData = await groupsRes.json();
    const usersData = await usersRes.json();

    console.log('Dashboard data loaded:', { rolesData, permissionsData, groupsData, usersData });

    // Update stat cards
    const statRoles = document.getElementById('stat-roles');
    const statPermissions = document.getElementById('stat-permissions');
    const statGroups = document.getElementById('stat-groups');
    const statUsers = document.getElementById('stat-users');

    if (statRoles) statRoles.textContent = rolesData.total || rolesData.items?.length || 0;
    if (statPermissions) statPermissions.textContent = permissionsData.total || permissionsData.items?.length || 0;
    if (statGroups) statGroups.textContent = groupsData.total || groupsData.items?.length || 0;
    if (statUsers) statUsers.textContent = usersData.total || usersData.items?.length || 0;

    console.log('Stat cards updated');

    // Count roles by type
    const rolesByType = {};
    rolesData.items?.forEach(role => {
      rolesByType[role.role_type] = (rolesByType[role.role_type] || 0) + 1;
    });

    // Count permissions by category
    const permissionsByCategory = {};
    permissionsData.items?.forEach(perm => {
      if (perm.category) {
        permissionsByCategory[perm.category] = (permissionsByCategory[perm.category] || 0) + 1;
      }
    });

    // Render charts
    renderBarChart('chart-roles-by-type', rolesByType, 'blue');
    renderBarChart('chart-permissions-by-category', permissionsByCategory, 'green');

  } catch (error) {
    console.error('Error loading dashboard:', error);
    showToast(error.message || 'Failed to load dashboard', 'error');
  }
}

/**
 * Render a simple bar chart
 */
function renderBarChart(elementId, data, color) {
  const container = document.getElementById(elementId);
  if (!container) return;

  const total = Object.values(data).reduce((sum, val) => sum + val, 0);
  const maxValue = Math.max(...Object.values(data));

  let html = '';
  for (const [key, value] of Object.entries(data).sort((a, b) => b[1] - a[1])) {
    const percentage = (value / maxValue) * 100;
    html += `
      <div class="flex items-center gap-3">
        <div class="w-32 text-sm text-gray-700 font-medium">${key}</div>
        <div class="flex-1 bg-gray-200 rounded-full h-6 overflow-hidden">
          <div class="bg-${color}-500 h-full flex items-center justify-end px-2 text-white text-xs font-semibold rounded-full transition-all duration-300"
               style="width: ${percentage}%">
            ${value}
          </div>
        </div>
      </div>
    `;
  }

  container.innerHTML = html || '<div class="text-gray-500 text-sm">No data available</div>';
}

/**
 * Load organization structure
 */
async function loadOrganizationStructure() {
  try {
    // Add tenant_id parameter if selected
    const url = state.selectedTenantId
      ? `/rbac/organization-structure?tenant_id=${state.selectedTenantId}`
      : '/rbac/organization-structure';

    const response = await apiFetch(url);
    const data = await response.json();

    state.orgStructure = data;

    const container = document.getElementById('org-structure-tree');
    if (!container) return;

    // Handle case where no tenant exists
    if (!data.tenant) {
      container.innerHTML = `
        <div class="text-center p-8 bg-gray-50 rounded-lg">
          <i class="ph ph-buildings text-5xl text-gray-400 mb-3"></i>
          <p class="text-gray-600 font-medium">No tenant data available</p>
          <p class="text-gray-500 text-sm mt-2">Please create a tenant or assign one to your account.</p>
        </div>
      `;
      return;
    }

    let html = `
      <div class="border-l-4 border-blue-500 pl-4">
        <div class="flex items-center gap-3 mb-4">
          <i class="ph-fill ph-buildings text-3xl text-blue-600"></i>
          <div>
            <div class="font-semibold text-lg">${data.tenant.name}</div>
            <div class="text-sm text-gray-600">Tenant</div>
          </div>
        </div>

        <!-- Companies with Branches and Departments -->
        ${data.companies?.length > 0 ? `
          <div class="ml-6 space-y-4">
            <div class="font-semibold text-gray-700 mb-2">
              <i class="ph ph-building mr-2"></i>Companies (${data.companies.length})
            </div>
            ${data.companies.map(company => `
              <div class="border-l-4 border-green-500 pl-4">
                <div class="flex items-center gap-2 text-sm font-medium mb-2">
                  <i class="ph-fill ph-building text-green-600"></i>
                  ${company.name}
                  ${!company.is_active ? '<span class="text-xs text-red-500">(Inactive)</span>' : ''}
                </div>

                <!-- Company-level Departments -->
                ${company.departments?.length > 0 ? `
                  <div class="ml-4 mb-3">
                    <div class="text-xs text-gray-500 mb-1">Company Departments:</div>
                    ${company.departments.map(dept => `
                      <div class="flex items-center gap-2 text-xs ml-2">
                        <i class="ph ph-identification-card text-amber-500"></i>
                        ${dept.name} <span class="text-gray-400">(${dept.code})</span>
                        ${!dept.is_active ? '<span class="text-red-500">(Inactive)</span>' : ''}
                      </div>
                    `).join('')}
                  </div>
                ` : ''}

                <!-- Branches -->
                ${company.branches?.length > 0 ? `
                  <div class="ml-4 space-y-3">
                    ${company.branches.map(branch => `
                      <div class="border-l-4 border-teal-400 pl-3 py-1">
                        <div class="flex items-center gap-2 text-xs font-medium mb-1">
                          <i class="ph-fill ph-tree-structure text-teal-600"></i>
                          ${branch.name} <span class="text-gray-400">(${branch.code})</span>
                          ${!branch.is_active ? '<span class="text-red-500">(Inactive)</span>' : ''}
                        </div>

                        <!-- Branch Departments -->
                        ${branch.departments?.length > 0 ? `
                          <div class="ml-4 mt-1">
                            ${branch.departments.map(dept => `
                              <div class="flex items-center gap-2 text-xs ml-2">
                                <i class="ph ph-identification-card text-amber-500"></i>
                                ${dept.name} <span class="text-gray-400">(${dept.code})</span>
                                ${!dept.is_active ? '<span class="text-red-500">(Inactive)</span>' : ''}
                              </div>
                            `).join('')}
                          </div>
                        ` : ''}
                      </div>
                    `).join('')}
                  </div>
                ` : ''}

                ${company.branches?.length === 0 && company.departments?.length === 0 ? `
                  <div class="text-xs text-gray-400 ml-4">No branches or departments</div>
                ` : ''}
              </div>
            `).join('')}
          </div>
        ` : ''}

        <!-- Groups -->
        ${data.groups?.length > 0 ? `
          <div class="ml-6 border-l-4 border-purple-500 pl-4 mb-4">
            <div class="font-semibold text-gray-700 mb-2">
              <i class="ph ph-users-three mr-2"></i>Groups (${data.groups.length})
            </div>
            <div class="space-y-2">
              ${data.groups.slice(0, 10).map(group => `
                <div class="flex items-center gap-2 text-sm">
                  <i class="ph ph-dot text-purple-500"></i>
                  ${group.name}
                  <span class="text-xs text-gray-500">(${group.group_type}, ${group.member_count} members)</span>
                  ${!group.is_active ? '<span class="text-xs text-red-500">(Inactive)</span>' : ''}
                </div>
              `).join('')}
              ${data.groups.length > 10 ? `<div class="text-sm text-gray-500">...and ${data.groups.length - 10} more</div>` : ''}
            </div>
          </div>
        ` : ''}

        <!-- Users -->
        ${data.users?.length > 0 ? `
          <div class="ml-6 border-l-4 border-orange-500 pl-4">
            <div class="font-semibold text-gray-700 mb-2">
              <i class="ph ph-users mr-2"></i>Users (${data.users.length})
            </div>
            <div class="text-sm text-gray-600">
              ${data.users.filter(u => u.is_active).length} active users
              ${data.users.filter(u => u.is_superuser).length > 0 ? `, ${data.users.filter(u => u.is_superuser).length} superuser(s)` : ''}
            </div>
          </div>
        ` : ''}
      </div>
    `;

    container.innerHTML = html;

  } catch (error) {
    console.error('Error loading organization structure:', error);
    showToast('Failed to load organization structure', 'error');
  }
}

/**
 * Load roles
 */
async function loadRoles() {
  try {
    const params = new URLSearchParams({
      skip: state.currentPage.roles * state.pageSize,
      limit: state.pageSize
    });

    if (state.filters.roles.search) params.append('search', state.filters.roles.search);
    if (state.filters.roles.type) params.append('role_type', state.filters.roles.type);
    if (state.filters.roles.status) params.append('is_active', state.filters.roles.status === 'active');

    const response = await apiFetch(`/rbac/roles?${params}`);
    const data = await response.json();

    state.roles = data.items || [];

    const tbody = document.getElementById('roles-table-body');
    if (!tbody) return;

    if (state.roles.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="7" class="px-6 py-12 text-center text-gray-500">
            <i class="ph ph-user-gear text-4xl mb-2"></i>
            <div>No roles found</div>
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = state.roles.map(role => `
      <tr class="hover:bg-gray-50">
        <td class="px-6 py-4">
          <div class="font-medium text-gray-900">${role.name}</div>
          <div class="text-sm text-gray-500">${role.code}</div>
          ${role.description ? `<div class="text-xs text-gray-400 mt-1">${role.description}</div>` : ''}
        </td>
        <td class="px-6 py-4">
          <span class="px-2 py-1 text-xs font-semibold rounded-full
            ${role.role_type === 'system' ? 'bg-red-100 text-red-800' : ''}
            ${role.role_type === 'default' ? 'bg-blue-100 text-blue-800' : ''}
            ${role.role_type === 'custom' ? 'bg-purple-100 text-purple-800' : ''}">
            ${role.role_type}
          </span>
          ${role.is_system ? '<i class="ph ph-lock-simple text-gray-400 ml-1" title="System role"></i>' : ''}
        </td>
        <td class="px-6 py-4">
          <button class="text-blue-600 hover:text-blue-800" onclick="rbacManager.viewRoleDetails('${role.id}')">
            View
          </button>
        </td>
        <td class="px-6 py-4">
          <button class="text-blue-600 hover:text-blue-800" onclick="rbacManager.viewRoleDetails('${role.id}')">
            View
          </button>
        </td>
        <td class="px-6 py-4">
          <button class="text-blue-600 hover:text-blue-800" onclick="rbacManager.viewRoleDetails('${role.id}')">
            View
          </button>
        </td>
        <td class="px-6 py-4">
          ${role.is_active
            ? '<span class="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">Active</span>'
            : '<span class="px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">Inactive</span>'}
        </td>
        <td class="px-6 py-4">
          <button class="text-blue-600 hover:text-blue-800" onclick="rbacManager.viewRoleDetails('${role.id}')">
            <i class="ph ph-eye"></i> View
          </button>
        </td>
      </tr>
    `).join('');

    // Update pagination
    updatePagination('roles', data);

  } catch (error) {
    console.error('Error loading roles:', error);
    showToast('Failed to load roles', 'error');
  }
}

/**
 * Load permission categories
 */
async function loadPermissionCategories() {
  try {
    const response = await apiFetch('/rbac/permission-categories');
    const data = await response.json();

    const select = document.getElementById('permissions-category-filter');
    if (!select) return;

    // Keep the "All Categories" option
    const options = '<option value="">All Categories</option>' +
      (data.categories || []).map(cat => `<option value="${cat.name}">${cat.name} (${cat.count})</option>`).join('');

    select.innerHTML = options;

  } catch (error) {
    console.error('Error loading permission categories:', error);
  }
}

/**
 * Load permissions
 */
async function loadPermissions() {
  try {
    const params = new URLSearchParams({
      skip: state.currentPage.permissions * state.pageSize,
      limit: state.pageSize
    });

    if (state.filters.permissions.search) params.append('search', state.filters.permissions.search);
    if (state.filters.permissions.category) params.append('category', state.filters.permissions.category);
    if (state.filters.permissions.status) params.append('is_active', state.filters.permissions.status === 'active');

    const response = await apiFetch(`/rbac/permissions?${params}`);
    const data = await response.json();

    state.permissions = data.items || [];

    const tbody = document.getElementById('permissions-table-body');
    if (!tbody) return;

    if (state.permissions.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="7" class="px-6 py-12 text-center text-gray-500">
            <i class="ph ph-key text-4xl mb-2"></i>
            <div>No permissions found</div>
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = state.permissions.map(perm => `
      <tr class="hover:bg-gray-50">
        <td class="px-6 py-4">
          <code class="text-sm font-mono text-gray-900">${perm.code}</code>
        </td>
        <td class="px-6 py-4">
          <div class="font-medium text-gray-900">${perm.name}</div>
          ${perm.description ? `<div class="text-xs text-gray-400 mt-1">${perm.description}</div>` : ''}
        </td>
        <td class="px-6 py-4">
          <span class="px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
            ${perm.category || 'N/A'}
          </span>
        </td>
        <td class="px-6 py-4">
          <button class="text-blue-600 hover:text-blue-800" onclick="rbacManager.viewPermissionDetails('${perm.id}')">
            View
          </button>
        </td>
        <td class="px-6 py-4 text-center">
          ${perm.is_system ? '<i class="ph ph-check text-green-600"></i>' : '<i class="ph ph-x text-gray-400"></i>'}
        </td>
        <td class="px-6 py-4">
          ${perm.is_active
            ? '<span class="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">Active</span>'
            : '<span class="px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">Inactive</span>'}
        </td>
        <td class="px-6 py-4">
          <button class="text-blue-600 hover:text-blue-800" onclick="rbacManager.viewPermissionDetails('${perm.id}')">
            <i class="ph ph-eye"></i> View
          </button>
        </td>
      </tr>
    `).join('');

    // Update pagination
    updatePagination('permissions', data);

  } catch (error) {
    console.error('Error loading permissions:', error);
    showToast('Failed to load permissions', 'error');
  }
}

/**
 * Load groups
 */
async function loadGroups() {
  try {
    const params = new URLSearchParams({
      skip: state.currentPage.groups * state.pageSize,
      limit: state.pageSize
    });

    if (state.filters.groups.search) params.append('search', state.filters.groups.search);
    if (state.filters.groups.type) params.append('group_type', state.filters.groups.type);
    if (state.filters.groups.status) params.append('is_active', state.filters.groups.status === 'active');

    const response = await apiFetch(`/rbac/groups?${params}`);
    const data = await response.json();

    state.groups = data.items || [];

    const tbody = document.getElementById('groups-table-body');
    if (!tbody) return;

    if (state.groups.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="6" class="px-6 py-12 text-center text-gray-500">
            <i class="ph ph-users-three text-4xl mb-2"></i>
            <div>No groups found</div>
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = state.groups.map(group => `
      <tr class="hover:bg-gray-50">
        <td class="px-6 py-4">
          <div class="font-medium text-gray-900">${group.name}</div>
          ${group.description ? `<div class="text-xs text-gray-400 mt-1">${group.description}</div>` : ''}
        </td>
        <td class="px-6 py-4">
          <span class="px-2 py-1 text-xs font-semibold rounded-full
            ${group.group_type === 'team' ? 'bg-blue-100 text-blue-800' : ''}
            ${group.group_type === 'department' ? 'bg-green-100 text-green-800' : ''}
            ${group.group_type === 'project' ? 'bg-purple-100 text-purple-800' : ''}
            ${group.group_type === 'custom' ? 'bg-gray-100 text-gray-800' : ''}">
            ${group.group_type}
          </span>
        </td>
        <td class="px-6 py-4">
          <button class="text-blue-600 hover:text-blue-800" onclick="rbacManager.viewGroupDetails('${group.id}')">
            View
          </button>
        </td>
        <td class="px-6 py-4">
          <button class="text-blue-600 hover:text-blue-800" onclick="rbacManager.viewGroupDetails('${group.id}')">
            View
          </button>
        </td>
        <td class="px-6 py-4">
          ${group.is_active
            ? '<span class="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">Active</span>'
            : '<span class="px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">Inactive</span>'}
        </td>
        <td class="px-6 py-4">
          <button class="text-blue-600 hover:text-blue-800" onclick="rbacManager.viewGroupDetails('${group.id}')">
            <i class="ph ph-eye"></i> View
          </button>
        </td>
      </tr>
    `).join('');

    // Update pagination
    updatePagination('groups', data);

  } catch (error) {
    console.error('Error loading groups:', error);
    showToast('Failed to load groups', 'error');
  }
}

/**
 * Load users table for user management
 */
async function loadUsers() {
  try {
    const response = await apiFetch('/org/users?limit=1000');
    const data = await response.json();

    state.users = data.items || [];

    const tbody = document.getElementById('users-table-body');
    const emptyState = document.getElementById('users-empty-state');
    if (!tbody) return;

    // Update showing/total counts
    const showing = document.getElementById('users-showing');
    const total = document.getElementById('users-total');
    if (showing) showing.textContent = state.users.length;
    if (total) total.textContent = state.users.length;

    if (state.users.length === 0) {
      tbody.classList.add('hidden');
      emptyState?.classList.remove('hidden');
      return;
    }

    tbody.classList.remove('hidden');
    emptyState?.classList.add('hidden');

    tbody.innerHTML = state.users.map(user => {
      const createdDate = user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A';
      const userRoles = user.roles ? user.roles.map(r => r.name || r).join(', ') : 'None';

      return `
        <tr class="hover:bg-gray-50">
          <td class="px-4 py-3">
            <div class="flex items-center gap-2">
              <div class="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                <i class="ph ph-user text-blue-600"></i>
              </div>
              <div>
                <div class="font-medium text-gray-900">${user.full_name || 'N/A'}</div>
                ${user.is_superuser ? '<span class="text-xs text-purple-600 font-semibold">Superuser</span>' : ''}
              </div>
            </div>
          </td>
          <td class="px-4 py-3">
            <div class="text-sm text-gray-900">${user.email}</div>
          </td>
          <td class="px-4 py-3">
            <div class="text-sm text-gray-600">${userRoles}</div>
          </td>
          <td class="px-4 py-3">
            ${user.is_active
              ? '<span class="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">Active</span>'
              : '<span class="px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">Inactive</span>'}
          </td>
          <td class="px-4 py-3">
            <div class="text-sm text-gray-600">${createdDate}</div>
          </td>
          <td class="px-4 py-3 text-right">
            <div class="flex items-center justify-end gap-2">
              <button class="text-purple-600 hover:text-purple-800" onclick="rbacManager.manageUserAccess('${user.id}')" title="Manage roles & permissions">
                <i class="ph ph-shield-check"></i>
              </button>
              <button class="text-blue-600 hover:text-blue-800" onclick="rbacManager.editUser('${user.id}')" title="Edit user">
                <i class="ph ph-pencil"></i>
              </button>
              <button class="text-red-600 hover:text-red-800" onclick="rbacManager.deleteUser('${user.id}')" title="Delete user">
                <i class="ph ph-trash"></i>
              </button>
            </div>
          </td>
        </tr>
      `;
    }).join('');

  } catch (error) {
    console.error('Error loading users:', error);
    showToast('Failed to load users', 'error');
  }
}

/**
 * Load users for access management
 */
async function loadUsersForAccess() {
  try {
    const response = await apiFetch('/org/users?limit=1000');
    const data = await response.json();

    state.users = data.items || [];

    const select = document.getElementById('user-select');
    if (!select) return;

    select.innerHTML = '<option value="">Choose a user...</option>' +
      state.users.map(user => `
        <option value="${user.id}">${user.email} - ${user.full_name || 'N/A'}</option>
      `).join('');

  } catch (error) {
    console.error('Error loading users:', error);
    showToast('Failed to load users', 'error');
  }
}

/**
 * Load user access details
 */
async function loadUserAccess(userId) {
  try {
    showLoading();

    const [rolesRes, permissionsRes] = await Promise.all([
      apiFetch(`/rbac/users/${userId}/roles`),
      apiFetch(`/rbac/users/${userId}/permissions`)
    ]);

    const rolesData = await rolesRes.json();
    const permissionsData = await permissionsRes.json();

    // Show details section
    document.getElementById('user-access-details').classList.remove('hidden');

    // Render direct roles
    const directRolesContainer = document.getElementById('user-direct-roles');
    if (rolesData.direct_roles?.length > 0) {
      directRolesContainer.innerHTML = rolesData.direct_roles.map(role => `
        <div class="flex items-center justify-between p-3 bg-white rounded-lg border border-gray-200">
          <div class="flex items-center gap-2">
            <i class="ph ph-user-gear text-blue-600"></i>
            <div>
              <div class="font-medium text-sm">${role.name}</div>
              <div class="text-xs text-gray-500">${role.code}</div>
            </div>
          </div>
          <button class="text-red-600 hover:text-red-800 text-sm" onclick="rbacManager.removeUserRole('${userId}', '${role.id}')">
            <i class="ph ph-x"></i>
          </button>
        </div>
      `).join('');
    } else {
      directRolesContainer.innerHTML = '<div class="text-sm text-gray-500">No direct roles assigned</div>';
    }

    // Render group roles
    const groupsContainer = document.getElementById('user-groups');
    if (rolesData.group_roles?.length > 0) {
      const groupsMap = new Map();
      rolesData.group_roles.forEach(gr => {
        if (!groupsMap.has(gr.group_id)) {
          groupsMap.set(gr.group_id, {
            id: gr.group_id,
            name: gr.group_name,
            roles: []
          });
        }
        groupsMap.get(gr.group_id).roles.push({
          id: gr.role_id,
          name: gr.role_name,
          code: gr.role_code
        });
      });

      groupsContainer.innerHTML = Array.from(groupsMap.values()).map(group => `
        <div class="p-3 bg-white rounded-lg border border-gray-200">
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-2">
              <i class="ph ph-users-three text-purple-600"></i>
              <div class="font-medium text-sm">${group.name}</div>
            </div>
          </div>
          <div class="text-xs text-gray-600 ml-6">
            ${group.roles.map(r => r.name).join(', ')}
          </div>
        </div>
      `).join('');
    } else {
      groupsContainer.innerHTML = '<div class="text-sm text-gray-500">No group memberships</div>';
    }

    // Render effective permissions
    const permissionsContainer = document.getElementById('user-permissions');
    if (permissionsData.permissions?.length > 0) {
      permissionsContainer.innerHTML = permissionsData.permissions.map(perm => `
        <span class="px-3 py-1 text-xs font-mono bg-green-100 text-green-800 rounded-full" title="${perm.description || ''}">
          ${perm.code}
        </span>
      `).join('');
    } else {
      permissionsContainer.innerHTML = '<div class="text-sm text-gray-500">No permissions</div>';
    }

  } catch (error) {
    console.error('Error loading user access:', error);
    showToast('Failed to load user access', 'error');
  } finally {
    hideLoading();
  }
}

/**
 * View role details
 */
async function viewRoleDetails(roleId) {
  try {
    showLoading();

    const response = await apiFetch(`/rbac/roles/${roleId}`);
    const role = await response.json();

    const modal = document.getElementById('role-modal');
    const title = document.getElementById('role-modal-title');
    const content = document.getElementById('role-modal-content');

    title.textContent = role.name;

    content.innerHTML = `
      <div class="space-y-6">
        <!-- Basic Info -->
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
            <div class="col-span-2">
              <dt class="text-sm text-gray-500">Description</dt>
              <dd class="text-sm text-gray-700">${role.description || 'N/A'}</dd>
            </div>
          </dl>
        </div>

        <!-- Permissions -->
        <div>
          <div class="flex items-center justify-between mb-2">
            <h4 class="font-semibold text-gray-900">Permissions (${role.permissions?.length || 0})</h4>
            <button onclick="rbacManager.manageRolePermissions('${role.id}')"
              class="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
              <i class="ph ph-gear"></i> Manage Permissions
            </button>
          </div>
          <div class="flex flex-wrap gap-2">
            ${role.permissions?.length > 0
              ? role.permissions.map(p => `
                  <span class="px-3 py-1 text-xs font-mono bg-blue-100 text-blue-800 rounded-full" title="${p.name}">
                    ${p.code}
                  </span>
                `).join('')
              : '<span class="text-sm text-gray-500">No permissions assigned</span>'}
          </div>
        </div>

        <!-- Direct Users -->
        <div>
          <h4 class="font-semibold text-gray-900 mb-2">Direct Users (${role.users?.length || 0})</h4>
          <div class="space-y-2">
            ${role.users?.length > 0
              ? role.users.slice(0, 10).map(u => `
                  <div class="flex items-center gap-2 text-sm">
                    <i class="ph ph-user-circle text-gray-400"></i>
                    <span>${u.email}</span>
                    <span class="text-gray-500">${u.full_name || ''}</span>
                  </div>
                `).join('')
              : '<span class="text-sm text-gray-500">No direct user assignments</span>'}
            ${role.users?.length > 10 ? `<div class="text-sm text-gray-500">...and ${role.users.length - 10} more</div>` : ''}
          </div>
        </div>

        <!-- Groups -->
        <div>
          <h4 class="font-semibold text-gray-900 mb-2">Groups (${role.groups?.length || 0})</h4>
          <div class="space-y-2">
            ${role.groups?.length > 0
              ? role.groups.map(g => `
                  <div class="flex items-center gap-2 text-sm">
                    <i class="ph ph-users-three text-gray-400"></i>
                    <span>${g.name}</span>
                    <span class="text-xs text-gray-500">(${g.group_type})</span>
                  </div>
                `).join('')
              : '<span class="text-sm text-gray-500">No group assignments</span>'}
          </div>
        </div>
      </div>
    `;

    modal.classList.remove('hidden');

  } catch (error) {
    console.error('Error viewing role details:', error);
    showToast('Failed to load role details', 'error');
  } finally {
    hideLoading();
  }
}

/**
 * View permission details
 */
async function viewPermissionDetails(permissionId) {
  try {
    showLoading();

    const response = await apiFetch(`/rbac/permissions/${permissionId}`);
    const perm = await response.json();

    const modal = document.getElementById('permission-modal');
    const title = document.getElementById('permission-modal-title');
    const content = document.getElementById('permission-modal-content');

    title.textContent = perm.name;

    content.innerHTML = `
      <div class="space-y-6">
        <!-- Basic Info -->
        <div>
          <h4 class="font-semibold text-gray-900 mb-2">Basic Information</h4>
          <dl class="grid grid-cols-2 gap-4">
            <div class="col-span-2">
              <dt class="text-sm text-gray-500">Code</dt>
              <dd class="text-sm font-mono text-gray-900">${perm.code}</dd>
            </div>
            <div>
              <dt class="text-sm text-gray-500">Category</dt>
              <dd class="text-sm font-medium text-gray-900">${perm.category || 'N/A'}</dd>
            </div>
            <div>
              <dt class="text-sm text-gray-500">System Permission</dt>
              <dd class="text-sm font-medium text-gray-900">${perm.is_system ? 'Yes' : 'No'}</dd>
            </div>
            <div class="col-span-2">
              <dt class="text-sm text-gray-500">Description</dt>
              <dd class="text-sm text-gray-700">${perm.description || 'N/A'}</dd>
            </div>
          </dl>
        </div>

        <!-- Roles -->
        <div>
          <h4 class="font-semibold text-gray-900 mb-2">Assigned to Roles (${perm.roles?.length || 0})</h4>
          <div class="space-y-2">
            ${perm.roles?.length > 0
              ? perm.roles.map(r => `
                  <div class="flex items-center gap-2 text-sm">
                    <i class="ph ph-user-gear text-gray-400"></i>
                    <span>${r.name}</span>
                    <span class="text-xs text-gray-500">${r.code}</span>
                  </div>
                `).join('')
              : '<span class="text-sm text-gray-500">Not assigned to any roles</span>'}
          </div>
        </div>
      </div>
    `;

    modal.classList.remove('hidden');

  } catch (error) {
    console.error('Error viewing permission details:', error);
    showToast('Failed to load permission details', 'error');
  } finally {
    hideLoading();
  }
}

/**
 * View group details
 */
async function viewGroupDetails(groupId) {
  try {
    showLoading();

    const response = await apiFetch(`/rbac/groups/${groupId}`);
    const group = await response.json();

    const modal = document.getElementById('group-modal');
    const title = document.getElementById('group-modal-title');
    const content = document.getElementById('group-modal-content');

    title.textContent = group.name;

    content.innerHTML = `
      <div class="space-y-6">
        <!-- Basic Info -->
        <div>
          <h4 class="font-semibold text-gray-900 mb-2">Basic Information</h4>
          <dl class="grid grid-cols-2 gap-4">
            <div>
              <dt class="text-sm text-gray-500">Type</dt>
              <dd class="text-sm font-medium text-gray-900">${group.group_type}</dd>
            </div>
            <div>
              <dt class="text-sm text-gray-500">Status</dt>
              <dd class="text-sm font-medium text-gray-900">${group.is_active ? 'Active' : 'Inactive'}</dd>
            </div>
            <div class="col-span-2">
              <dt class="text-sm text-gray-500">Description</dt>
              <dd class="text-sm text-gray-700">${group.description || 'N/A'}</dd>
            </div>
          </dl>
        </div>

        <!-- Members -->
        <div>
          <h4 class="font-semibold text-gray-900 mb-2">Members (${group.members?.length || 0})</h4>
          <div class="space-y-2">
            ${group.members?.length > 0
              ? group.members.slice(0, 10).map(m => `
                  <div class="flex items-center gap-2 text-sm">
                    <i class="ph ph-user-circle text-gray-400"></i>
                    <span>${m.email}</span>
                    <span class="text-gray-500">${m.full_name || ''}</span>
                  </div>
                `).join('')
              : '<span class="text-sm text-gray-500">No members</span>'}
            ${group.members?.length > 10 ? `<div class="text-sm text-gray-500">...and ${group.members.length - 10} more</div>` : ''}
          </div>
        </div>

        <!-- Roles -->
        <div>
          <h4 class="font-semibold text-gray-900 mb-2">Roles (${group.roles?.length || 0})</h4>
          <div class="space-y-2">
            ${group.roles?.length > 0
              ? group.roles.map(r => `
                  <div class="flex items-center gap-2 text-sm">
                    <i class="ph ph-user-gear text-gray-400"></i>
                    <span>${r.name}</span>
                    <span class="text-xs text-gray-500">${r.code}</span>
                  </div>
                `).join('')
              : '<span class="text-sm text-gray-500">No roles assigned</span>'}
          </div>
        </div>

        <!-- Effective Permissions -->
        <div>
          <h4 class="font-semibold text-gray-900 mb-2">Effective Permissions (${group.effective_permissions?.length || 0})</h4>
          <div class="flex flex-wrap gap-2">
            ${group.effective_permissions?.length > 0
              ? group.effective_permissions.map(p => `
                  <span class="px-3 py-1 text-xs font-mono bg-green-100 text-green-800 rounded-full">
                    ${p}
                  </span>
                `).join('')
              : '<span class="text-sm text-gray-500">No permissions</span>'}
          </div>
        </div>
      </div>
    `;

    modal.classList.remove('hidden');

  } catch (error) {
    console.error('Error viewing group details:', error);
    showToast('Failed to load group details', 'error');
  } finally {
    hideLoading();
  }
}

/**
 * Remove role from user
 */
async function removeUserRole(userId, roleId) {
  if (!confirm('Are you sure you want to remove this role from the user?')) {
    return;
  }

  try {
    showLoading();

    const response = await apiFetch(`/rbac/users/${userId}/roles/${roleId}`, {
      method: 'DELETE'
    });

    if (response.ok) {
      showToast('Role removed successfully', 'success');
      await loadUserAccess(userId);
    } else {
      throw new Error('Failed to remove role');
    }

  } catch (error) {
    console.error('Error removing role:', error);
    showToast('Failed to remove role', 'error');
  } finally {
    hideLoading();
  }
}

/**
 * Update pagination controls
 */
function updatePagination(type, data) {
  const showingStart = document.getElementById(`${type}-showing-start`);
  const showingEnd = document.getElementById(`${type}-showing-end`);
  const total = document.getElementById(`${type}-total`);
  const prevBtn = document.getElementById(`${type}-prev-page`);
  const nextBtn = document.getElementById(`${type}-next-page`);

  if (showingStart) showingStart.textContent = data.skip + 1;
  if (showingEnd) showingEnd.textContent = Math.min(data.skip + data.items.length, data.total);
  if (total) total.textContent = data.total;

  if (prevBtn) {
    prevBtn.disabled = state.currentPage[type] === 0;
  }

  if (nextBtn) {
    nextBtn.disabled = data.skip + data.items.length >= data.total;
  }
}

/**
 * Setup tenant selector for superusers
 */
async function setupTenantSelector() {
  try {
    // Fetch all tenants
    const response = await apiFetch('/org/tenants?limit=1000');
    const data = await response.json();

    state.tenants = data.items || [];

    // Show the tenant selector container
    const container = document.getElementById('tenant-selector-container');
    if (container) {
      container.classList.remove('hidden');
    }

    // Populate the selector
    const selector = document.getElementById('tenant-selector');
    if (selector && state.tenants.length > 0) {
      selector.innerHTML = '<option value="">All Tenants</option>' +
        state.tenants.map(t => `<option value="${t.id}">${t.name}</option>`).join('');

      // Add change event listener
      selector.addEventListener('change', async (e) => {
        state.selectedTenantId = e.target.value || null;
        console.log('Tenant changed to:', state.selectedTenantId);

        // Reload current tab data
        const activeTab = document.querySelector('.rbac-tab.active');
        if (activeTab) {
          const tabId = activeTab.id.replace('tab-', '');
          await loadTabData(tabId);
        }
      });

      console.log(`Tenant selector loaded with ${state.tenants.length} tenants`);
    }
  } catch (error) {
    console.error('Error loading tenants:', error);
  }
}

/**
 * Debounce helper
 */
function debounce(func, wait) {
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

/**
 * Show user modal for create/edit
 */
function showUserModal(userId = null) {
  const modal = document.getElementById('user-modal');
  const title = document.getElementById('user-modal-title');
  const form = document.getElementById('user-form');
  const passwordSection = document.getElementById('password-section');

  if (!modal || !form) return;

  // Reset form
  form.reset();
  document.getElementById('user-id').value = '';

  if (userId) {
    // Edit mode
    title.textContent = 'Edit User';
    passwordSection.querySelector('label').textContent = 'Password';
    passwordSection.querySelector('p').classList.remove('hidden');
    document.getElementById('user-password').required = false;

    // Load user data
    const user = state.users.find(u => u.id === userId);
    if (user) {
      document.getElementById('user-id').value = user.id;
      document.getElementById('user-email').value = user.email;
      document.getElementById('user-fullname').value = user.full_name || '';
      document.getElementById('user-is-active').value = user.is_active ? 'true' : 'false';
      document.getElementById('user-is-superuser').checked = user.is_superuser || false;
    }
  } else {
    // Create mode
    title.textContent = 'Add User';
    passwordSection.querySelector('label').textContent = 'Password *';
    passwordSection.querySelector('p').classList.add('hidden');
    document.getElementById('user-password').required = true;
  }

  modal.classList.remove('hidden');
}

/**
 * Close user modal
 */
function closeUserModal() {
  const modal = document.getElementById('user-modal');
  if (modal) {
    modal.classList.add('hidden');
  }
}

/**
 * Save user (create or update)
 */
async function saveUser() {
  const userId = document.getElementById('user-id').value;
  const email = document.getElementById('user-email').value;
  const fullName = document.getElementById('user-fullname').value;
  const password = document.getElementById('user-password').value;
  const isActive = document.getElementById('user-is-active').value === 'true';
  const isSuperuser = document.getElementById('user-is-superuser').checked;

  if (!email) {
    showToast('Email is required', 'error');
    return;
  }

  if (!userId && !password) {
    showToast('Password is required for new users', 'error');
    return;
  }

  try {
    showLoading();

    const userData = {
      email,
      full_name: fullName || null,
      is_active: isActive,
      is_superuser: isSuperuser
    };

    // Only include password if provided
    if (password) {
      userData.password = password;
    }

    let response;
    if (userId) {
      // Update existing user
      response = await apiFetch(`/org/users/${userId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(userData)
      });
    } else {
      // Create new user
      response = await apiFetch('/org/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(userData)
      });
    }

    if (response.ok) {
      showToast(userId ? 'User updated successfully' : 'User created successfully', 'success');
      closeUserModal();
      await loadUsers();
    } else {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to save user');
    }
  } catch (error) {
    console.error('Error saving user:', error);
    showToast(error.message || 'Failed to save user', 'error');
  } finally {
    hideLoading();
  }
}

/**
 * Edit user
 */
async function editUser(userId) {
  showUserModal(userId);
}

/**
 * Delete user
 */
async function deleteUser(userId) {
  const user = state.users.find(u => u.id === userId);
  const userName = user ? (user.full_name || user.email) : 'this user';

  if (!confirm(`Are you sure you want to delete ${userName}?`)) {
    return;
  }

  try {
    showLoading();
    const response = await apiFetch(`/org/users/${userId}`, {
      method: 'DELETE'
    });

    if (response.ok) {
      showToast('User deleted successfully', 'success');
      await loadUsers();
    } else {
      throw new Error('Failed to delete user');
    }
  } catch (error) {
    console.error('Error deleting user:', error);
    showToast('Failed to delete user', 'error');
  } finally {
    hideLoading();
  }
}

/**
 * Switch to User Access tab and load user's RBAC settings
 */
async function manageUserAccess(userId) {
  // Switch to User Access tab
  const userAccessTab = document.getElementById('tab-user-access');
  if (userAccessTab) {
    userAccessTab.click();

    // Wait a bit for tab to switch
    setTimeout(async () => {
      const userSelect = document.getElementById('user-select');
      if (userSelect) {
        userSelect.value = userId;
        // Trigger change event to load user access
        await loadUserAccess(userId);
      }
    }, 100);
  }
}

/**
 * State for permission management
 */
const permissionState = {
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

/**
 * Show permission management modal for a role
 */
async function manageRolePermissions(roleId) {
  try {
    showLoading();

    // Get role details
    const roleResponse = await apiFetch(`/rbac/roles/${roleId}`);
    const role = await roleResponse.json();

    // Get grouped permissions with role assignments
    const params = new URLSearchParams({ role_id: roleId });
    const permsResponse = await apiFetch(`/rbac/permissions/grouped?${params}`);
    const permsData = await permsResponse.json();

    // Initialize permission state
    permissionState.currentRoleId = roleId;
    permissionState.groupedPermissions = permsData.groups || [];
    permissionState.originalPermissions = new Set();
    permissionState.currentPermissions = new Set();

    // Collect all currently granted permissions
    permsData.groups.forEach(group => {
      ['standard_actions', 'special_actions'].forEach(actionType => {
        Object.values(group[actionType]).forEach(perm => {
          if (perm.granted) {
            permissionState.originalPermissions.add(perm.id);
            permissionState.currentPermissions.add(perm.id);
          }
        });
      });
    });

    // Show modal
    const modal = document.getElementById('permission-management-modal');
    const title = document.getElementById('permission-management-title');
    const content = document.getElementById('permission-management-content');

    title.textContent = `Manage Permissions: ${role.name}`;

    // Render permission grid
    renderPermissionGrid(content);

    modal.classList.remove('hidden');

  } catch (error) {
    console.error('Error loading permission management:', error);
    showToast('Failed to load permission management', 'error');
  } finally {
    hideLoading();
  }
}

/**
 * Render the permission management grid
 */
function renderPermissionGrid(container) {
  const { groupedPermissions, filters } = permissionState;

  // Apply filters
  let filteredGroups = groupedPermissions;
  if (filters.category) {
    filteredGroups = filteredGroups.filter(g => g.category === filters.category);
  }
  if (filters.scope) {
    filteredGroups = filteredGroups.filter(g => g.scope === filters.scope);
  }
  if (filters.search) {
    const search = filters.search.toLowerCase();
    filteredGroups = filteredGroups.filter(g =>
      g.resource.toLowerCase().includes(search) ||
      g.category?.toLowerCase().includes(search)
    );
  }

  // Get unique categories and scopes for filters
  const categories = [...new Set(groupedPermissions.map(g => g.category).filter(Boolean))];
  const scopes = [...new Set(groupedPermissions.map(g => g.scope))];

  // Group by category
  const byCategory = {};
  filteredGroups.forEach(group => {
    const cat = group.category || 'Other';
    if (!byCategory[cat]) byCategory[cat] = [];
    byCategory[cat].push(group);
  });

  container.innerHTML = `
    <div class="space-y-6">
      <!-- Filters and Quick Actions -->
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
          <button onclick="rbacManager.selectAllCRUD()"
            class="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            <i class="ph ph-check-square"></i> Select All CRUD
          </button>
          <button onclick="rbacManager.deselectAllCRUD()"
            class="px-3 py-1.5 text-sm bg-gray-600 text-white rounded-lg hover:bg-gray-700">
            <i class="ph ph-square"></i> Deselect All CRUD
          </button>
          <button onclick="rbacManager.applyTemplate('viewer')"
            class="px-3 py-1.5 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700">
            <i class="ph ph-eye"></i> Viewer Template
          </button>
          <button onclick="rbacManager.applyTemplate('editor')"
            class="px-3 py-1.5 text-sm bg-purple-600 text-white rounded-lg hover:bg-purple-700">
            <i class="ph ph-pencil"></i> Editor Template
          </button>
          <button onclick="rbacManager.applyTemplate('manager')"
            class="px-3 py-1.5 text-sm bg-orange-600 text-white rounded-lg hover:bg-orange-700">
            <i class="ph ph-crown"></i> Manager Template
          </button>
        </div>
      </div>

      <!-- Permission Groups -->
      <div class="space-y-6 max-h-[60vh] overflow-y-auto">
        ${Object.entries(byCategory).map(([category, groups]) => `
          <div>
            <h3 class="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <i class="ph ph-folder text-blue-600"></i>
              ${category.toUpperCase()}
            </h3>
            <div class="space-y-3">
              ${groups.map(group => renderPermissionGroup(group)).join('')}
            </div>
          </div>
        `).join('')}
      </div>

      <!-- Save/Cancel Actions -->
      <div class="flex justify-between items-center border-t pt-4">
        <div class="text-sm text-gray-600">
          <span id="changes-indicator" class="font-medium"></span>
        </div>
        <div class="flex gap-2">
          <button onclick="rbacManager.closePermissionManagement()"
            class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50">
            Cancel
          </button>
          <button onclick="rbacManager.savePermissions()"
            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            <i class="ph ph-floppy-disk"></i> Save Changes
          </button>
        </div>
      </div>
    </div>
  `;

  // Setup event listeners
  setupPermissionEventListeners();
  updateChangesIndicator();
}

/**
 * Render a single permission group (resource)
 */
function renderPermissionGroup(group) {
  const standardActions = ['read', 'create', 'update', 'delete'];

  return `
    <div class="border border-gray-200 rounded-lg p-4 bg-white hover:shadow-sm transition-shadow">
      <div class="flex items-start justify-between mb-3">
        <div>
          <h4 class="font-semibold text-gray-900">${formatResourceName(group.resource)}</h4>
          <p class="text-sm text-gray-500">Scope: <span class="font-mono text-xs bg-gray-100 px-2 py-0.5 rounded">${group.scope}</span></p>
        </div>
        <button onclick="rbacManager.toggleAllForResource('${group.key}')"
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

            const isChecked = permissionState.currentPermissions.has(perm.id);
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
              const isActive = permissionState.currentPermissions.has(perm.id);
              return `
                <button
                  onclick="rbacManager.togglePermission('${perm.id}')"
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

/**
 * Format resource name for display
 */
function formatResourceName(resource) {
  return resource.split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

/**
 * Setup event listeners for permission management
 */
function setupPermissionEventListeners() {
  // Search filter
  document.getElementById('perm-search')?.addEventListener('input', debounce((e) => {
    permissionState.filters.search = e.target.value;
    const content = document.getElementById('permission-management-content');
    renderPermissionGrid(content);
  }, 300));

  // Category filter
  document.getElementById('perm-category-filter')?.addEventListener('change', (e) => {
    permissionState.filters.category = e.target.value;
    const content = document.getElementById('permission-management-content');
    renderPermissionGrid(content);
  });

  // Scope filter
  document.getElementById('perm-scope-filter')?.addEventListener('change', (e) => {
    permissionState.filters.scope = e.target.value;
    const content = document.getElementById('permission-management-content');
    renderPermissionGrid(content);
  });

  // Checkbox changes
  document.querySelectorAll('.perm-checkbox').forEach(checkbox => {
    checkbox.addEventListener('change', (e) => {
      const permId = e.target.dataset.permId;
      if (e.target.checked) {
        permissionState.currentPermissions.add(permId);
      } else {
        permissionState.currentPermissions.delete(permId);
      }
      updateChangesIndicator();
    });
  });
}

/**
 * Toggle a single permission (for badges)
 */
function togglePermission(permId) {
  if (permissionState.currentPermissions.has(permId)) {
    permissionState.currentPermissions.delete(permId);
  } else {
    permissionState.currentPermissions.add(permId);
  }

  const content = document.getElementById('permission-management-content');
  renderPermissionGrid(content);
}

/**
 * Toggle all permissions for a resource
 */
function toggleAllForResource(resourceKey) {
  const group = permissionState.groupedPermissions.find(g => g.key === resourceKey);
  if (!group) return;

  // Collect all permission IDs for this resource
  const allPerms = [
    ...Object.values(group.standard_actions),
    ...Object.values(group.special_actions)
  ].map(p => p.id);

  // Check if all are currently selected
  const allSelected = allPerms.every(id => permissionState.currentPermissions.has(id));

  // Toggle: if all selected, deselect all; otherwise, select all
  if (allSelected) {
    allPerms.forEach(id => permissionState.currentPermissions.delete(id));
  } else {
    allPerms.forEach(id => permissionState.currentPermissions.add(id));
  }

  const content = document.getElementById('permission-management-content');
  renderPermissionGrid(content);
}

/**
 * Select all CRUD permissions
 */
function selectAllCRUD() {
  permissionState.groupedPermissions.forEach(group => {
    ['read', 'create', 'update', 'delete'].forEach(action => {
      if (group.standard_actions[action]) {
        permissionState.currentPermissions.add(group.standard_actions[action].id);
      }
    });
  });

  const content = document.getElementById('permission-management-content');
  renderPermissionGrid(content);
}

/**
 * Deselect all CRUD permissions
 */
function deselectAllCRUD() {
  permissionState.groupedPermissions.forEach(group => {
    ['read', 'create', 'update', 'delete'].forEach(action => {
      if (group.standard_actions[action]) {
        permissionState.currentPermissions.delete(group.standard_actions[action].id);
      }
    });
  });

  const content = document.getElementById('permission-management-content');
  renderPermissionGrid(content);
}

/**
 * Apply permission template
 */
function applyTemplate(templateName) {
  if (templateName === 'viewer') {
    // Only read permissions
    permissionState.groupedPermissions.forEach(group => {
      if (group.standard_actions.read) {
        permissionState.currentPermissions.add(group.standard_actions.read.id);
      }
    });
  } else if (templateName === 'editor') {
    // Read, create, update
    permissionState.groupedPermissions.forEach(group => {
      ['read', 'create', 'update'].forEach(action => {
        if (group.standard_actions[action]) {
          permissionState.currentPermissions.add(group.standard_actions[action].id);
        }
      });
    });
  } else if (templateName === 'manager') {
    // All CRUD + common special actions
    permissionState.groupedPermissions.forEach(group => {
      Object.values(group.standard_actions).forEach(perm => {
        permissionState.currentPermissions.add(perm.id);
      });
      // Add export if available
      if (group.special_actions.export) {
        permissionState.currentPermissions.add(group.special_actions.export.id);
      }
      if (group.special_actions.manage) {
        permissionState.currentPermissions.add(group.special_actions.manage.id);
      }
    });
  }

  const content = document.getElementById('permission-management-content');
  renderPermissionGrid(content);
}

/**
 * Update changes indicator
 */
function updateChangesIndicator() {
  const indicator = document.getElementById('changes-indicator');
  if (!indicator) return;

  const added = [...permissionState.currentPermissions].filter(
    id => !permissionState.originalPermissions.has(id)
  );
  const removed = [...permissionState.originalPermissions].filter(
    id => !permissionState.currentPermissions.has(id)
  );

  if (added.length === 0 && removed.length === 0) {
    indicator.textContent = 'No changes';
    indicator.className = 'font-medium text-gray-600';
  } else {
    indicator.innerHTML = `
      <span class="text-green-600">+${added.length}</span> /
      <span class="text-red-600">-${removed.length}</span> changes
    `;
    indicator.className = 'font-medium';
  }
}

/**
 * Save permission changes
 */
async function savePermissions() {
  try {
    showLoading();

    const added = [...permissionState.currentPermissions].filter(
      id => !permissionState.originalPermissions.has(id)
    );
    const removed = [...permissionState.originalPermissions].filter(
      id => !permissionState.currentPermissions.has(id)
    );

    const response = await apiFetch(
      `/rbac/roles/${permissionState.currentRoleId}/permissions/bulk`,
      {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          grant_ids: added,
          revoke_ids: removed
        })
      }
    );

    if (response.ok) {
      const result = await response.json();
      showToast(`Successfully updated permissions: ${result.granted} granted, ${result.revoked} revoked`, 'success');
      closePermissionManagement();

      // Reload roles to reflect changes
      await loadRoles();
    } else {
      throw new Error('Failed to save permissions');
    }

  } catch (error) {
    console.error('Error saving permissions:', error);
    showToast('Failed to save permissions', 'error');
  } finally {
    hideLoading();
  }
}

/**
 * Close permission management modal
 */
function closePermissionManagement() {
  const modal = document.getElementById('permission-management-modal');
  modal.classList.add('hidden');

  // Reset state
  permissionState.currentRoleId = null;
  permissionState.originalPermissions.clear();
  permissionState.currentPermissions.clear();
  permissionState.groupedPermissions = [];
  permissionState.filters = { category: '', scope: '', search: '' };
}

// Export functions to window for onclick handlers
window.rbacManager = {
  viewRoleDetails,
  viewPermissionDetails,
  viewGroupDetails,
  removeUserRole,
  editUser,
  deleteUser,
  manageUserAccess,
  manageRolePermissions,
  togglePermission,
  toggleAllForResource,
  selectAllCRUD,
  deselectAllCRUD,
  applyTemplate,
  savePermissions,
  closePermissionManagement
};

export default {
  initRBACManager,
  viewRoleDetails,
  manageRolePermissions,
  viewPermissionDetails,
  viewGroupDetails,
  removeUserRole,
  editUser,
  deleteUser,
  manageUserAccess
};
