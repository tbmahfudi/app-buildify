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
  orgStructure: null,
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
      apiFetch('/api/v1/rbac/roles?limit=1000'),
      apiFetch('/api/v1/rbac/permissions?limit=1000'),
      apiFetch('/api/v1/rbac/groups?limit=1000'),
      apiFetch('/api/v1/org/users?limit=1000')
    ]);

    console.log('API responses received:', { rolesRes, permissionsRes, groupsRes, usersRes });

    // Check if responses are OK
    if (!rolesRes.ok) throw new Error(`Roles API error: ${rolesRes.status}`);
    if (!permissionsRes.ok) throw new Error(`Permissions API error: ${permissionsRes.status}`);
    if (!groupsRes.ok) throw new Error(`Groups API error: ${groupsRes.status}`);
    if (!usersRes.ok) throw new Error(`Users API error: ${usersRes.status}`);

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
    showToast('Failed to load dashboard', 'error');
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
    const response = await apiFetch('/api/v1/rbac/organization-structure');
    const data = await response.json();

    state.orgStructure = data;

    const container = document.getElementById('org-structure-tree');
    if (!container) return;

    let html = `
      <div class="border-l-4 border-blue-500 pl-4">
        <div class="flex items-center gap-3 mb-4">
          <i class="ph-fill ph-buildings text-3xl text-blue-600"></i>
          <div>
            <div class="font-semibold text-lg">${data.tenant.name}</div>
            <div class="text-sm text-gray-600">Tenant</div>
          </div>
        </div>

        <!-- Companies -->
        ${data.companies?.length > 0 ? `
          <div class="ml-6 border-l-4 border-green-500 pl-4 mb-4">
            <div class="font-semibold text-gray-700 mb-2">
              <i class="ph ph-building mr-2"></i>Companies (${data.companies.length})
            </div>
            <div class="space-y-2">
              ${data.companies.map(company => `
                <div class="flex items-center gap-2 text-sm">
                  <i class="ph ph-dot text-green-500"></i>
                  ${company.name}
                  ${!company.is_active ? '<span class="text-xs text-red-500">(Inactive)</span>' : ''}
                </div>
              `).join('')}
            </div>
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

    const response = await apiFetch(`/api/v1/rbac/roles?${params}`);
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
    const response = await apiFetch('/api/v1/rbac/permission-categories');
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

    const response = await apiFetch(`/api/v1/rbac/permissions?${params}`);
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

    const response = await apiFetch(`/api/v1/rbac/groups?${params}`);
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
 * Load users for access management
 */
async function loadUsersForAccess() {
  try {
    const response = await apiFetch('/api/v1/org/users?limit=1000');
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
      apiFetch(`/api/v1/rbac/users/${userId}/roles`),
      apiFetch(`/api/v1/rbac/users/${userId}/permissions`)
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

    const response = await apiFetch(`/api/v1/rbac/roles/${roleId}`);
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
          <h4 class="font-semibold text-gray-900 mb-2">Permissions (${role.permissions?.length || 0})</h4>
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

    const response = await apiFetch(`/api/v1/rbac/permissions/${permissionId}`);
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

    const response = await apiFetch(`/api/v1/rbac/groups/${groupId}`);
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

    const response = await apiFetch(`/api/v1/rbac/users/${userId}/roles/${roleId}`, {
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

// Export functions to window for onclick handlers
window.rbacManager = {
  viewRoleDetails,
  viewPermissionDetails,
  viewGroupDetails,
  removeUserRole
};

export default {
  initRBACManager,
  viewRoleDetails,
  viewPermissionDetails,
  viewGroupDetails,
  removeUserRole
};
