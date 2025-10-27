/**
 * User Management Module
 * Handles CRUD operations for users with role management
 */

import { apiFetch } from './api.js';
import { showToast, showLoading, hideLoading } from './ui-utils.js';
import { hasRole, applyRBACToElements } from './rbac.js';

let users = [];
let currentPage = 1;
let pageSize = 25;
let totalUsers = 0;

// Initialize on route load
document.addEventListener('route:loaded', async (e) => {
  if (e.detail.route === 'users') {
    initUsers();
  }
});

function initUsers() {
  // Apply RBAC to UI elements
  applyRBACToElements();

  // Event listeners
  const btnAddUser = document.getElementById('btn-add-user');
  if (btnAddUser) {
    btnAddUser.addEventListener('click', () => showModal());
  }

  document.getElementById('btn-refresh')?.addEventListener('click', loadUsers);
  document.getElementById('btn-close-modal')?.addEventListener('click', hideModal);
  document.getElementById('btn-cancel-modal')?.addEventListener('click', hideModal);
  document.getElementById('user-form')?.addEventListener('submit', saveUser);
  document.getElementById('search-users')?.addEventListener('input', handleSearch);
  document.getElementById('filter-role')?.addEventListener('change', handleFilter);
  document.getElementById('filter-status')?.addEventListener('change', handleFilter);

  // Pagination
  document.getElementById('btn-prev-page')?.addEventListener('click', () => changePage(-1));
  document.getElementById('btn-next-page')?.addEventListener('click', () => changePage(1));

  // Close modal on overlay click
  document.getElementById('modal-overlay')?.addEventListener('click', hideModal);

  // Load initial data
  loadUsers();
}

async function loadUsers() {
  showLoading();

  try {
    // Use the data service endpoint with pagination
    const res = await apiFetch('/data/users/list', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        page: currentPage,
        page_size: pageSize,
        sort: [['created_at', 'desc']]
      })
    });

    if (!res.ok) throw new Error('Failed to load users');

    const data = await res.json();
    users = data.items || [];
    totalUsers = data.total || users.length;

    renderUsers(users);
    updatePagination();
  } catch (err) {
    console.error('Failed to load users:', err);
    showToast('Failed to load users', 'error');
    users = [];
    renderUsers([]);
  } finally {
    hideLoading();
  }
}

function renderUsers(items) {
  const tbody = document.getElementById('users-tbody');
  const emptyState = document.getElementById('empty-state');
  const countEl = document.getElementById('user-count');

  if (!tbody) return;

  if (items.length === 0) {
    tbody.innerHTML = '';
    if (emptyState) emptyState.classList.remove('hidden');
    if (countEl) countEl.textContent = '0 users';
    return;
  }

  if (emptyState) emptyState.classList.add('hidden');
  if (countEl) countEl.textContent = `${totalUsers} users`;

  tbody.innerHTML = items.map(user => {
    const roles = Array.isArray(user.roles) ? user.roles : [];
    const isActive = user.is_active !== false;
    const isSuperuser = user.is_superuser === true;

    return `
      <tr class="hover:bg-gray-50 transition">
        <td class="px-6 py-4">
          <div class="flex items-center">
            <div class="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center mr-3">
              <i class="bi bi-person${isSuperuser ? '-fill-gear text-yellow-600' : '-fill text-blue-600'}"></i>
            </div>
            <div>
              <div class="text-sm font-medium text-gray-900">${escapeHtml(user.email)}</div>
              ${user.full_name ? `<div class="text-xs text-gray-500">${escapeHtml(user.full_name)}</div>` : ''}
            </div>
          </div>
        </td>
        <td class="px-6 py-4">
          <div class="flex flex-wrap gap-1">
            ${isSuperuser ? `
              <span class="inline-flex items-center gap-1 px-2 py-1 bg-yellow-100 text-yellow-800 text-xs font-medium rounded-full">
                <i class="bi bi-shield-fill-check"></i>
                Superuser
              </span>
            ` : ''}
            ${roles.map(role => `
              <span class="inline-flex items-center px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded-full">
                ${escapeHtml(role)}
              </span>
            `).join('')}
            ${roles.length === 0 && !isSuperuser ? '<span class="text-xs text-gray-500">No roles</span>' : ''}
          </div>
        </td>
        <td class="px-6 py-4">
          ${isActive ? `
            <span class="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">
              <i class="bi bi-check-circle-fill"></i>
              Active
            </span>
          ` : `
            <span class="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 text-gray-800 text-xs font-medium rounded-full">
              <i class="bi bi-x-circle-fill"></i>
              Inactive
            </span>
          `}
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
          ${user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-right text-sm">
          <button
            class="inline-flex items-center gap-1 px-3 py-1.5 text-blue-600 hover:bg-blue-50 rounded-lg transition"
            onclick="window.editUser('${user.id}')">
            <i class="bi bi-pencil-square"></i>
            Edit
          </button>
          <button
            class="inline-flex items-center gap-1 px-3 py-1.5 text-red-600 hover:bg-red-50 rounded-lg transition ml-2"
            onclick="window.deleteUser('${user.id}')"
            ${!hasRole('admin') ? 'style="display:none"' : ''}>
            <i class="bi bi-trash"></i>
            Delete
          </button>
        </td>
      </tr>
    `;
  }).join('');
}

function showModal(user = null) {
  const modal = document.getElementById('user-modal');
  const overlay = document.getElementById('modal-overlay');
  const title = document.getElementById('modal-title');
  const passwordContainer = document.getElementById('password-container');
  const passwordRequired = document.getElementById('password-required');
  const passwordHint = document.getElementById('password-hint');
  const passwordInput = document.getElementById('user-password');

  if (!modal || !overlay) return;

  // Apply RBAC to modal elements
  applyRBACToElements(modal);

  title.textContent = user ? 'Edit User' : 'Add User';

  // Set form values
  document.getElementById('user-id').value = user?.id || '';
  document.getElementById('user-email').value = user?.email || '';
  document.getElementById('user-password').value = '';
  document.getElementById('user-fullname').value = user?.full_name || '';
  document.getElementById('user-phone').value = user?.phone || '';
  document.getElementById('user-is-active').checked = user?.is_active !== false;
  document.getElementById('user-is-superuser').checked = user?.is_superuser === true;

  // Handle password field for edit mode
  if (user) {
    passwordRequired.style.display = 'none';
    passwordInput.removeAttribute('required');
    passwordHint.style.display = 'block';
  } else {
    passwordRequired.style.display = 'inline';
    passwordInput.setAttribute('required', 'required');
    passwordHint.style.display = 'none';
  }

  // Set role checkboxes
  const roles = user?.roles || [];
  document.querySelectorAll('.role-checkbox').forEach(checkbox => {
    checkbox.checked = roles.includes(checkbox.value);
  });

  document.getElementById('user-error')?.classList.add('hidden');

  modal.classList.remove('hidden');
  overlay.classList.remove('hidden');

  // Focus first input
  setTimeout(() => document.getElementById('user-email')?.focus(), 100);
}

function hideModal() {
  document.getElementById('user-modal')?.classList.add('hidden');
  document.getElementById('modal-overlay')?.classList.add('hidden');
}

async function saveUser(e) {
  e.preventDefault();

  const id = document.getElementById('user-id').value;
  const email = document.getElementById('user-email').value.trim();
  const password = document.getElementById('user-password').value;
  const fullName = document.getElementById('user-fullname').value.trim();
  const phone = document.getElementById('user-phone').value.trim();
  const isActive = document.getElementById('user-is-active').checked;
  const isSuperuser = document.getElementById('user-is-superuser').checked;

  const errorEl = document.getElementById('user-error');
  const errorMsg = document.getElementById('error-message');
  const saveBtn = document.getElementById('btn-save-user');

  errorEl?.classList.add('hidden');

  // Validate email
  if (!email || !email.includes('@')) {
    errorMsg.textContent = 'Valid email is required';
    errorEl?.classList.remove('hidden');
    return;
  }

  // Validate password for new users
  if (!id && !password) {
    errorMsg.textContent = 'Password is required for new users';
    errorEl?.classList.remove('hidden');
    return;
  }

  // Get selected roles
  const roles = Array.from(document.querySelectorAll('.role-checkbox:checked')).map(cb => cb.value);

  if (roles.length === 0 && !isSuperuser) {
    errorMsg.textContent = 'At least one role is required';
    errorEl?.classList.remove('hidden');
    return;
  }

  const body = {
    email,
    full_name: fullName || null,
    phone: phone || null,
    roles,
    is_active: isActive,
    is_superuser: isSuperuser
  };

  // Only include password if provided
  if (password) {
    body.password = password;
  }

  const url = id ? `/data/users/${id}` : '/data/users';
  const method = id ? 'PUT' : 'POST';

  try {
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<i class="bi bi-arrow-repeat animate-spin"></i> Saving...';

    const res = await apiFetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });

    if (res.ok) {
      hideModal();
      await loadUsers();
      showToast(id ? 'User updated successfully' : 'User created successfully', 'success');
    } else {
      const err = await res.json();
      errorMsg.textContent = err.detail || 'Save failed';
      errorEl?.classList.remove('hidden');
    }
  } catch (err) {
    console.error('Save error:', err);
    errorMsg.textContent = 'Network error. Please try again.';
    errorEl?.classList.remove('hidden');
  } finally {
    saveBtn.disabled = false;
    saveBtn.innerHTML = '<i class="bi bi-check-lg"></i> Save User';
  }
}

async function editUser(id) {
  try {
    showLoading();
    const res = await apiFetch(`/data/users/${id}`);
    if (!res.ok) throw new Error('Failed to load user');

    const user = await res.json();
    showModal(user);
  } catch (err) {
    console.error('Failed to load user:', err);
    showToast('Failed to load user', 'error');
  } finally {
    hideLoading();
  }
}

async function deleteUser(id) {
  if (!confirm('Are you sure you want to delete this user? This action cannot be undone.')) {
    return;
  }

  showLoading();

  try {
    const res = await apiFetch(`/data/users/${id}`, { method: 'DELETE' });

    if (res.ok) {
      await loadUsers();
      showToast('User deleted successfully', 'success');
    } else {
      const err = await res.json();
      showToast(err.detail || 'Delete failed', 'error');
    }
  } catch (err) {
    console.error('Delete error:', err);
    showToast('Network error. Please try again.', 'error');
  } finally {
    hideLoading();
  }
}

function handleSearch(e) {
  const query = e.target.value.toLowerCase();
  applyFilters({ search: query });
}

function handleFilter() {
  const role = document.getElementById('filter-role')?.value;
  const status = document.getElementById('filter-status')?.value;
  applyFilters({ role, status });
}

async function applyFilters({ search = '', role = '', status = '' } = {}) {
  showLoading();

  try {
    const filters = [];

    // Build filters based on selections
    if (search) {
      filters.push({
        field: 'email',
        operator: 'like',
        value: `%${search}%`
      });
    }

    if (role) {
      // Note: This is a simplification. Backend may need custom handling for array fields
      filters.push({
        field: 'roles',
        operator: 'contains',
        value: role
      });
    }

    if (status) {
      filters.push({
        field: 'is_active',
        operator: 'eq',
        value: status === 'active'
      });
    }

    const res = await apiFetch('/data/users/list', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        filters: filters.length > 0 ? filters : undefined,
        page: 1,
        page_size: pageSize,
        sort: [['created_at', 'desc']]
      })
    });

    if (!res.ok) throw new Error('Failed to filter users');

    const data = await res.json();
    users = data.items || [];
    totalUsers = data.total || users.length;
    currentPage = 1;

    renderUsers(users);
    updatePagination();
  } catch (err) {
    console.error('Filter error:', err);
    showToast('Failed to apply filters', 'error');
  } finally {
    hideLoading();
  }
}

function changePage(delta) {
  const newPage = currentPage + delta;
  const maxPage = Math.ceil(totalUsers / pageSize);

  if (newPage < 1 || newPage > maxPage) return;

  currentPage = newPage;
  loadUsers();
}

function updatePagination() {
  const pageStart = (currentPage - 1) * pageSize + 1;
  const pageEnd = Math.min(currentPage * pageSize, totalUsers);
  const maxPage = Math.ceil(totalUsers / pageSize);

  document.getElementById('page-start').textContent = totalUsers > 0 ? pageStart : 0;
  document.getElementById('page-end').textContent = pageEnd;
  document.getElementById('total-users').textContent = totalUsers;
  document.getElementById('page-info').textContent = `Page ${currentPage} of ${maxPage || 1}`;

  const btnPrev = document.getElementById('btn-prev-page');
  const btnNext = document.getElementById('btn-next-page');

  if (btnPrev) btnPrev.disabled = currentPage <= 1;
  if (btnNext) btnNext.disabled = currentPage >= maxPage;
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Expose functions for inline onclick handlers
window.editUser = editUser;
window.deleteUser = deleteUser;
