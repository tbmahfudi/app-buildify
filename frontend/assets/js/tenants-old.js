import { apiFetch } from './api.js';

let currentTenants = [];
let editingTenantId = null;

document.addEventListener('route:loaded', (event) => {
  if (event.detail.route === 'tenants') {
    initTenantsPage();
  }
});

async function initTenantsPage() {
  const addButton = document.getElementById('btn-add-tenant');
  const refreshButton = document.getElementById('btn-refresh');
  const searchInput = document.getElementById('search-tenants');
  const filterSubscription = document.getElementById('filter-subscription');
  const filterStatus = document.getElementById('filter-status');

  if (addButton && !addButton.dataset.initialized) {
    addButton.addEventListener('click', () => openModal());
    addButton.dataset.initialized = 'true';
  }

  if (refreshButton && !refreshButton.dataset.initialized) {
    refreshButton.addEventListener('click', () => loadTenants());
    refreshButton.dataset.initialized = 'true';
  }

  if (searchInput && !searchInput.dataset.initialized) {
    searchInput.addEventListener('input', filterTenants);
    searchInput.dataset.initialized = 'true';
  }

  if (filterSubscription && !filterSubscription.dataset.initialized) {
    filterSubscription.addEventListener('change', filterTenants);
    filterSubscription.dataset.initialized = 'true';
  }

  if (filterStatus && !filterStatus.dataset.initialized) {
    filterStatus.addEventListener('change', filterTenants);
    filterStatus.dataset.initialized = 'true';
  }

  initModal();
  await loadTenants();
}

function initModal() {
  const modal = document.getElementById('tenant-modal');
  const overlay = document.getElementById('modal-overlay');
  const closeButton = document.getElementById('btn-close-modal');
  const cancelButton = document.getElementById('btn-cancel');
  const form = document.getElementById('tenant-form');
  const colorInput = document.getElementById('primary-color');
  const colorTextInput = document.getElementById('primary-color-text');

  if (closeButton && !closeButton.dataset.initialized) {
    closeButton.addEventListener('click', closeModal);
    closeButton.dataset.initialized = 'true';
  }

  if (cancelButton && !cancelButton.dataset.initialized) {
    cancelButton.addEventListener('click', closeModal);
    cancelButton.dataset.initialized = 'true';
  }

  if (overlay && !overlay.dataset.initialized) {
    overlay.addEventListener('click', closeModal);
    overlay.dataset.initialized = 'true';
  }

  if (form && !form.dataset.initialized) {
    form.addEventListener('submit', handleFormSubmit);
    form.dataset.initialized = 'true';
  }

  // Sync color picker with text input
  if (colorInput && colorTextInput && !colorInput.dataset.initialized) {
    colorInput.addEventListener('input', (e) => {
      colorTextInput.value = e.target.value;
    });
    colorTextInput.addEventListener('input', (e) => {
      const value = e.target.value;
      if (/^#[0-9A-F]{6}$/i.test(value)) {
        colorInput.value = value;
      }
    });
    colorInput.dataset.initialized = 'true';
  }
}

async function loadTenants() {
  const tbody = document.getElementById('tenants-tbody');
  const emptyState = document.getElementById('empty-state');

  if (!tbody) return;

  tbody.innerHTML = renderLoadingState();
  if (emptyState) emptyState.classList.add('hidden');

  try {
    const response = await apiFetch('/org/tenants');
    const payload = await response.json();
    currentTenants = payload.items || [];
    renderTenants(currentTenants);
  } catch (error) {
    tbody.innerHTML = renderErrorState('Failed to load tenants');
    console.error('Failed to load tenants:', error);
  }
}

function filterTenants() {
  const searchValue = document.getElementById('search-tenants')?.value.toLowerCase() || '';
  const subscriptionFilter = document.getElementById('filter-subscription')?.value || '';
  const statusFilter = document.getElementById('filter-status')?.value || '';

  const filtered = currentTenants.filter(tenant => {
    const matchesSearch = !searchValue ||
      tenant.name.toLowerCase().includes(searchValue) ||
      tenant.code.toLowerCase().includes(searchValue);

    const matchesSubscription = !subscriptionFilter ||
      tenant.subscription_tier === subscriptionFilter;

    const matchesStatus = !statusFilter ||
      tenant.subscription_status === statusFilter;

    return matchesSearch && matchesSubscription && matchesStatus;
  });

  renderTenants(filtered);
}

function renderTenants(tenants) {
  const tbody = document.getElementById('tenants-tbody');
  const emptyState = document.getElementById('empty-state');
  const tenantCount = document.getElementById('tenant-count');

  if (!tbody) return;

  tbody.innerHTML = '';

  if (tenantCount) {
    tenantCount.textContent = `${tenants.length} tenant${tenants.length !== 1 ? 's' : ''}`;
  }

  if (!tenants.length) {
    if (emptyState) emptyState.classList.remove('hidden');
    tbody.innerHTML = '';
    return;
  }

  if (emptyState) emptyState.classList.add('hidden');

  tenants.forEach((tenant) => {
    const row = document.createElement('tr');
    row.className = 'hover:bg-gray-50 transition';

    // Code cell
    const codeCell = document.createElement('td');
    codeCell.className = 'px-6 py-4 text-sm font-semibold text-gray-900';
    codeCell.textContent = tenant.code;

    // Name cell
    const nameCell = document.createElement('td');
    nameCell.className = 'px-6 py-4 text-sm text-gray-900';
    nameCell.textContent = tenant.name;

    // Subscription cell
    const subscriptionCell = document.createElement('td');
    subscriptionCell.className = 'px-6 py-4 text-sm';
    const tierBadge = document.createElement('span');
    tierBadge.className = getTierBadgeClass(tenant.subscription_tier);
    tierBadge.textContent = capitalizeFirst(tenant.subscription_tier);
    subscriptionCell.appendChild(tierBadge);

    // Status cell
    const statusCell = document.createElement('td');
    statusCell.className = 'px-6 py-4 text-sm';
    const statusBadge = document.createElement('span');
    statusBadge.className = getStatusBadgeClass(tenant.subscription_status);
    statusBadge.textContent = capitalizeFirst(tenant.subscription_status);
    if (!tenant.is_active) {
      const inactiveBadge = document.createElement('span');
      inactiveBadge.className = 'ml-2 px-2 py-0.5 text-xs font-medium rounded-full bg-gray-200 text-gray-700';
      inactiveBadge.textContent = 'Inactive';
      statusCell.appendChild(inactiveBadge);
    }
    statusCell.appendChild(statusBadge);

    // Usage cell
    const usageCell = document.createElement('td');
    usageCell.className = 'px-6 py-4 text-sm text-gray-600';
    usageCell.innerHTML = `
      <div class="text-xs space-y-1">
        <div>Users: ${tenant.current_users}/${tenant.max_users}</div>
        <div>Companies: ${tenant.current_companies}/${tenant.max_companies}</div>
      </div>
    `;

    // Date cell
    const dateCell = document.createElement('td');
    dateCell.className = 'px-6 py-4 text-sm text-gray-600';
    dateCell.textContent = formatDate(tenant.created_at);

    // Organization cell
    const orgCell = document.createElement('td');
    orgCell.className = 'px-6 py-4 text-sm text-center';

    const orgBtn = document.createElement('button');
    orgBtn.className = 'inline-flex items-center gap-1 px-3 py-1.5 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition';
    orgBtn.innerHTML = '<i class="ph ph-tree-structure"></i> View';
    orgBtn.title = 'View Organization Hierarchy';
    orgBtn.addEventListener('click', () => {
      if (window.orgHierarchy) {
        window.orgHierarchy.open(tenant.id, tenant.name);
      }
    });

    orgCell.appendChild(orgBtn);

    // Actions cell
    const actionsCell = document.createElement('td');
    actionsCell.className = 'px-6 py-4 text-sm text-right';

    const actionsDiv = document.createElement('div');
    actionsDiv.className = 'flex items-center justify-end gap-2';

    const editBtn = document.createElement('button');
    editBtn.className = 'p-2 text-blue-600 hover:bg-blue-50 rounded transition';
    editBtn.innerHTML = '<i class="ph ph-pencil"></i>';
    editBtn.title = 'Edit';
    editBtn.addEventListener('click', () => editTenant(tenant.id));

    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'p-2 text-red-600 hover:bg-red-50 rounded transition';
    deleteBtn.innerHTML = '<i class="ph ph-trash"></i>';
    deleteBtn.title = 'Delete';
    deleteBtn.addEventListener('click', () => deleteTenant(tenant.id, tenant.name));

    actionsDiv.appendChild(editBtn);
    actionsDiv.appendChild(deleteBtn);
    actionsCell.appendChild(actionsDiv);

    row.appendChild(codeCell);
    row.appendChild(nameCell);
    row.appendChild(subscriptionCell);
    row.appendChild(statusCell);
    row.appendChild(usageCell);
    row.appendChild(dateCell);
    row.appendChild(orgCell);
    row.appendChild(actionsCell);

    tbody.appendChild(row);
  });
}

function getTierBadgeClass(tier) {
  const baseClass = 'px-2 py-0.5 text-xs font-medium rounded-full';
  switch (tier) {
    case 'free':
      return `${baseClass} bg-gray-100 text-gray-700`;
    case 'basic':
      return `${baseClass} bg-blue-100 text-blue-700`;
    case 'premium':
      return `${baseClass} bg-purple-100 text-purple-700`;
    case 'enterprise':
      return `${baseClass} bg-yellow-100 text-yellow-700`;
    default:
      return `${baseClass} bg-gray-100 text-gray-700`;
  }
}

function getStatusBadgeClass(status) {
  const baseClass = 'px-2 py-0.5 text-xs font-medium rounded-full';
  switch (status) {
    case 'active':
      return `${baseClass} bg-green-100 text-green-700`;
    case 'suspended':
      return `${baseClass} bg-orange-100 text-orange-700`;
    case 'cancelled':
      return `${baseClass} bg-red-100 text-red-700`;
    default:
      return `${baseClass} bg-gray-100 text-gray-700`;
  }
}

function capitalizeFirst(str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

function formatDate(dateString) {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}

function renderLoadingState() {
  return `
    <tr>
      <td colspan="7" class="px-6 py-12 text-center text-gray-500">
        <div class="flex items-center justify-center gap-2">
          <span class="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></span>
          Loading tenants...
        </div>
      </td>
    </tr>
  `;
}

function renderErrorState(message) {
  return `
    <tr>
      <td colspan="7" class="px-6 py-12 text-center text-red-500">
        <i class="ph ph-warning-circle text-2xl block mb-2"></i>
        <p>${message}</p>
      </td>
    </tr>
  `;
}

function openModal(tenant = null) {
  const modal = document.getElementById('tenant-modal');
  const overlay = document.getElementById('modal-overlay');
  const modalTitle = document.getElementById('modal-title');
  const form = document.getElementById('tenant-form');

  if (!modal || !overlay || !form) return;

  editingTenantId = tenant?.id || null;

  if (tenant) {
    modalTitle.textContent = 'Edit Tenant';
    populateForm(tenant);
  } else {
    modalTitle.textContent = 'Add Tenant';
    form.reset();
    document.getElementById('is-active').checked = true;
    document.getElementById('subscription-tier').value = 'free';
    document.getElementById('subscription-status').value = 'active';
  }

  modal.classList.remove('hidden');
  overlay.classList.remove('hidden');
}

function closeModal() {
  const modal = document.getElementById('tenant-modal');
  const overlay = document.getElementById('modal-overlay');
  const form = document.getElementById('tenant-form');

  if (modal) modal.classList.add('hidden');
  if (overlay) overlay.classList.add('hidden');
  if (form) form.reset();

  editingTenantId = null;
}

function populateForm(tenant) {
  document.getElementById('tenant-name').value = tenant.name || '';
  document.getElementById('tenant-code').value = tenant.code || '';
  document.getElementById('tenant-description').value = tenant.description || '';
  document.getElementById('subscription-tier').value = tenant.subscription_tier || 'free';
  document.getElementById('subscription-status').value = tenant.subscription_status || 'active';
  document.getElementById('max-companies').value = tenant.max_companies || 10;
  document.getElementById('max-users').value = tenant.max_users || 500;
  document.getElementById('max-storage').value = tenant.max_storage_gb || 10;
  document.getElementById('contact-name').value = tenant.contact_name || '';
  document.getElementById('contact-email').value = tenant.contact_email || '';
  document.getElementById('contact-phone').value = tenant.contact_phone || '';
  document.getElementById('logo-url').value = tenant.logo_url || '';

  if (tenant.primary_color) {
    document.getElementById('primary-color').value = tenant.primary_color;
    document.getElementById('primary-color-text').value = tenant.primary_color;
  }

  document.getElementById('is-active').checked = tenant.is_active ?? true;
  document.getElementById('is-trial').checked = tenant.is_trial ?? false;
}

async function handleFormSubmit(event) {
  event.preventDefault();

  const formData = new FormData(event.target);
  const data = {
    name: formData.get('name'),
    code: formData.get('code').toUpperCase(),
    description: formData.get('description') || null,
    subscription_tier: formData.get('subscription_tier'),
    subscription_status: formData.get('subscription_status'),
    max_companies: parseInt(formData.get('max_companies')),
    max_users: parseInt(formData.get('max_users')),
    max_storage_gb: parseInt(formData.get('max_storage_gb')),
    contact_name: formData.get('contact_name') || null,
    contact_email: formData.get('contact_email') || null,
    contact_phone: formData.get('contact_phone') || null,
    logo_url: formData.get('logo_url') || null,
    primary_color: formData.get('primary_color') || null,
    is_active: formData.get('is_active') === 'on',
    is_trial: formData.get('is_trial') === 'on'
  };

  try {
    let response;
    if (editingTenantId) {
      response = await apiFetch(`/org/tenants/${editingTenantId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
    } else {
      response = await apiFetch('/org/tenants', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
    }

    if (response.ok) {
      closeModal();
      await loadTenants();
      showNotification(
        editingTenantId ? 'Tenant updated successfully' : 'Tenant created successfully',
        'success'
      );
    } else {
      const error = await response.json();
      showNotification(error.detail || 'Failed to save tenant', 'error');
    }
  } catch (error) {
    console.error('Failed to save tenant:', error);
    showNotification('Failed to save tenant', 'error');
  }
}

async function editTenant(tenantId) {
  try {
    const response = await apiFetch(`/org/tenants/${tenantId}`);
    if (response.ok) {
      const tenant = await response.json();
      openModal(tenant);
    } else {
      showNotification('Failed to load tenant details', 'error');
    }
  } catch (error) {
    console.error('Failed to load tenant:', error);
    showNotification('Failed to load tenant details', 'error');
  }
}

async function deleteTenant(tenantId, tenantName) {
  if (!confirm(`Are you sure you want to delete the tenant "${tenantName}"? This action cannot be undone and will delete all associated data.`)) {
    return;
  }

  try {
    const response = await apiFetch(`/org/tenants/${tenantId}`, {
      method: 'DELETE'
    });

    if (response.ok) {
      await loadTenants();
      showNotification('Tenant deleted successfully', 'success');
    } else {
      const error = await response.json();
      showNotification(error.detail || 'Failed to delete tenant', 'error');
    }
  } catch (error) {
    console.error('Failed to delete tenant:', error);
    showNotification('Failed to delete tenant', 'error');
  }
}

function showNotification(message, type = 'info') {
  // Check if notification system exists
  if (window.showToast) {
    window.showToast(message, type);
  } else {
    // Fallback to alert
    alert(message);
  }
}
