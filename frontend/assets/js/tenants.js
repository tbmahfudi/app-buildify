import { apiFetch } from './api.js';
import { showToast } from './ui-utils.js';

let currentTenants = [];
let editingTenantId = null;

document.addEventListener('route:loaded', (event) => {
  if (event.detail.route === 'tenants') {
    initTenantsPage();
  }
});

async function initTenantsPage() {
  setupEventListeners();
  await loadTenants();
}

function setupEventListeners() {
  // Add tenant button
  const addBtn = document.getElementById('btn-add-tenant');
  if (addBtn && !addBtn.dataset.initialized) {
    addBtn.addEventListener('click', () => openFormPanel());
    addBtn.dataset.initialized = 'true';
  }

  // Form panel close buttons
  const closePanelBtn = document.getElementById('btn-close-form-panel');
  const cancelBtn = document.getElementById('btn-cancel-form');
  const backdrop = document.getElementById('form-panel-backdrop');

  if (closePanelBtn && !closePanelBtn.dataset.initialized) {
    closePanelBtn.addEventListener('click', closeFormPanel);
    closePanelBtn.dataset.initialized = 'true';
  }

  if (cancelBtn && !cancelBtn.dataset.initialized) {
    cancelBtn.addEventListener('click', closeFormPanel);
    cancelBtn.dataset.initialized = 'true';
  }

  if (backdrop && !backdrop.dataset.initialized) {
    backdrop.addEventListener('click', closeFormPanel);
    backdrop.dataset.initialized = 'true';
  }

  // Form submission
  const form = document.getElementById('tenant-form');
  if (form && !form.dataset.initialized) {
    form.addEventListener('submit', handleFormSubmit);
    form.dataset.initialized = 'true';
  }

  // Search and filters
  const searchInput = document.getElementById('search-tenants');
  const filterSubscription = document.getElementById('filter-subscription');
  const filterStatus = document.getElementById('filter-status');

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

  // Color picker sync
  const colorInput = document.getElementById('primary-color');
  const colorTextInput = document.getElementById('primary-color-text');

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
  const container = document.getElementById('tenants-container');
  const loadingState = document.getElementById('loading-state');
  const emptyState = document.getElementById('empty-state');

  if (!container) return;

  // Show loading
  loadingState?.classList.remove('hidden');
  container.classList.add('hidden');
  emptyState?.classList.add('hidden');

  try {
    const response = await apiFetch('/org/tenants');
    const payload = await response.json();
    currentTenants = payload.items || [];

    // Hide loading
    loadingState?.classList.add('hidden');

    if (currentTenants.length === 0) {
      emptyState?.classList.remove('hidden');
    } else {
      container.classList.remove('hidden');
      renderTenants(currentTenants);
      updateStats(currentTenants);
    }
  } catch (error) {
    loadingState?.classList.add('hidden');
    console.error('Failed to load tenants:', error);
    showToast('Failed to load tenants', 'error');
  }
}

function renderTenants(tenants) {
  const container = document.getElementById('tenants-container');
  if (!container) return;

  container.innerHTML = tenants.map(tenant => renderTenantCard(tenant)).join('');
}

function renderTenantCard(tenant) {
  return `
    <div class="bg-white rounded-xl shadow-sm overflow-hidden border border-gray-200 hover:shadow-md transition-shadow">
      <!-- Card Header -->
      <div class="p-6">
        <div class="flex items-start justify-between">
          <!-- Tenant Info -->
          <div class="flex-1">
            <div class="flex items-center gap-3 mb-2">
              <h3 class="text-xl font-semibold text-gray-900">${escapeHtml(tenant.name)}</h3>
              ${renderTierBadge(tenant.subscription_tier)}
              ${renderStatusBadge(tenant.subscription_status, tenant.is_active)}
            </div>
            <div class="flex items-center gap-4 text-sm text-gray-600">
              <span class="flex items-center gap-1">
                <i class="bi bi-code-square"></i>
                <strong>Code:</strong> ${escapeHtml(tenant.code)}
              </span>
              <span class="flex items-center gap-1">
                <i class="bi bi-calendar3"></i>
                ${formatDate(tenant.created_at)}
              </span>
            </div>
            ${tenant.description ? `<p class="mt-2 text-sm text-gray-600">${escapeHtml(tenant.description)}</p>` : ''}
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-2 ml-4">
            <button onclick="editTenant('${tenant.id}')"
              class="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition" title="Edit Tenant">
              <i class="bi bi-pencil text-lg"></i>
            </button>
            <button onclick="deleteTenant('${tenant.id}', '${escapeHtml(tenant.name)}')"
              class="p-2 text-red-600 hover:bg-red-50 rounded-lg transition" title="Delete Tenant">
              <i class="bi bi-trash text-lg"></i>
            </button>
          </div>
        </div>

        <!-- Compact Usage Stats -->
        <div class="flex items-center gap-6 mt-4 pt-4 border-t border-gray-200 text-sm">
          <div class="flex items-center gap-2 ${tenant.current_companies >= tenant.max_companies ? 'text-red-600' : 'text-gray-700'}">
            <i class="bi bi-building text-lg"></i>
            <span class="font-semibold">${tenant.current_companies}/${tenant.max_companies}</span>
            <span class="text-gray-500 text-xs">Companies</span>
          </div>
          <div class="flex items-center gap-2 ${tenant.current_users >= tenant.max_users ? 'text-red-600' : 'text-gray-700'}">
            <i class="bi bi-people text-lg"></i>
            <span class="font-semibold">${tenant.current_users}/${tenant.max_users}</span>
            <span class="text-gray-500 text-xs">Users</span>
          </div>
          <div class="flex items-center gap-2 ${tenant.current_storage_gb >= tenant.max_storage_gb ? 'text-red-600' : 'text-gray-700'}">
            <i class="bi bi-hdd text-lg"></i>
            <span class="font-semibold">${tenant.current_storage_gb}/${tenant.max_storage_gb} GB</span>
            <span class="text-gray-500 text-xs">Storage</span>
          </div>
        </div>
      </div>

      <!-- Tabbed Content -->
      <div class="border-t border-gray-200">
        <!-- Tab Navigation -->
        <div class="flex border-b border-gray-200 bg-gray-50">
          <button class="tenant-tab active flex-1 px-6 py-3 text-sm font-medium border-b-2 border-blue-600 text-blue-600 bg-white"
            data-tab="details" data-tenant-id="${tenant.id}" onclick="switchTab('${tenant.id}', 'details')">
            <i class="bi bi-info-circle mr-2"></i>Details
          </button>
          <button class="tenant-tab flex-1 px-6 py-3 text-sm font-medium border-b-2 border-transparent text-gray-600 hover:text-gray-900 hover:bg-gray-100"
            data-tab="organization" data-tenant-id="${tenant.id}" onclick="switchTab('${tenant.id}', 'organization')">
            <i class="bi bi-diagram-3 mr-2"></i>Organization
          </button>
          <button class="tenant-tab flex-1 px-6 py-3 text-sm font-medium border-b-2 border-transparent text-gray-600 hover:text-gray-900 hover:bg-gray-100"
            data-tab="settings" data-tenant-id="${tenant.id}" onclick="switchTab('${tenant.id}', 'settings')">
            <i class="bi bi-gear mr-2"></i>Settings
          </button>
        </div>

        <!-- Tab Content -->
        <div class="bg-white">
          <!-- Details Tab -->
          <div class="tab-content px-6 py-4" data-tab="details" data-tenant-id="${tenant.id}">
            ${renderDetailsTab(tenant)}
          </div>

          <!-- Organization Tab -->
          <div class="tab-content hidden px-6 py-4" data-tab="organization" data-tenant-id="${tenant.id}">
            <div id="org-structure-${tenant.id}" class="min-h-[200px]">
              <div class="text-center py-8 text-gray-500">
                <i class="bi bi-hourglass-split text-2xl mb-2"></i>
                <p>Click the Organization tab to load structure</p>
              </div>
            </div>
          </div>

          <!-- Settings Tab -->
          <div class="tab-content hidden px-6 py-4" data-tab="settings" data-tenant-id="${tenant.id}">
            ${renderSettingsTab(tenant)}
          </div>
        </div>
      </div>
    </div>
  `;
}

function renderDetailsTab(tenant) {
  return `
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div>
        <h4 class="text-sm font-semibold text-gray-700 mb-3">Contact Information</h4>
        <dl class="space-y-2 text-sm">
          <div class="flex justify-between">
            <dt class="text-gray-600">Name:</dt>
            <dd class="font-medium text-gray-900">${tenant.contact_name || 'Not set'}</dd>
          </div>
          <div class="flex justify-between">
            <dt class="text-gray-600">Email:</dt>
            <dd class="font-medium text-gray-900">${tenant.contact_email || 'Not set'}</dd>
          </div>
          <div class="flex justify-between">
            <dt class="text-gray-600">Phone:</dt>
            <dd class="font-medium text-gray-900">${tenant.contact_phone || 'Not set'}</dd>
          </div>
        </dl>
      </div>
      <div>
        <h4 class="text-sm font-semibold text-gray-700 mb-3">Subscription Details</h4>
        <dl class="space-y-2 text-sm">
          <div class="flex justify-between">
            <dt class="text-gray-600">Tier:</dt>
            <dd class="font-medium text-gray-900">${capitalizeFirst(tenant.subscription_tier)}</dd>
          </div>
          <div class="flex justify-between">
            <dt class="text-gray-600">Status:</dt>
            <dd class="font-medium text-gray-900">${capitalizeFirst(tenant.subscription_status)}</dd>
          </div>
          <div class="flex justify-between">
            <dt class="text-gray-600">Trial:</dt>
            <dd class="font-medium text-gray-900">${tenant.is_trial ? 'Yes' : 'No'}</dd>
          </div>
        </dl>
      </div>
    </div>
  `;
}

function renderSettingsTab(tenant) {
  return `
    <div class="space-y-4">
      <div class="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200">
        <div>
          <h4 class="font-medium text-gray-900">Primary Color</h4>
          <p class="text-sm text-gray-600">${tenant.primary_color || 'Not set'}</p>
        </div>
        ${tenant.primary_color ? `<div class="w-12 h-12 rounded-lg border border-gray-300" style="background-color: ${tenant.primary_color}"></div>` : ''}
      </div>
      <div class="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200">
        <div>
          <h4 class="font-medium text-gray-900">Logo URL</h4>
          <p class="text-sm text-gray-600 truncate max-w-md">${tenant.logo_url || 'Not set'}</p>
        </div>
      </div>
    </div>
  `;
}

function renderTierBadge(tier) {
  const colors = {
    trial: 'bg-yellow-100 text-yellow-700',
    free: 'bg-gray-100 text-gray-700',
    basic: 'bg-blue-100 text-blue-700',
    premium: 'bg-purple-100 text-purple-700',
    enterprise: 'bg-orange-100 text-orange-700'
  };

  return `<span class="px-3 py-1 text-xs font-semibold rounded-full ${colors[tier] || colors.free}">${capitalizeFirst(tier)}</span>`;
}

function renderStatusBadge(status, isActive) {
  const colors = {
    active: 'bg-green-100 text-green-700',
    suspended: 'bg-orange-100 text-orange-700',
    cancelled: 'bg-red-100 text-red-700'
  };

  let badges = `<span class="px-3 py-1 text-xs font-semibold rounded-full ${colors[status] || colors.active}">${capitalizeFirst(status)}</span>`;

  if (!isActive) {
    badges += `<span class="px-3 py-1 text-xs font-semibold rounded-full bg-gray-200 text-gray-700">Inactive</span>`;
  }

  return badges;
}

function updateStats(tenants) {
  const total = tenants.length;
  const active = tenants.filter(t => t.is_active).length;
  const trial = tenants.filter(t => t.is_trial).length;
  const premium = tenants.filter(t => ['premium', 'enterprise'].includes(t.subscription_tier)).length;

  document.getElementById('stat-total').textContent = total;
  document.getElementById('stat-active').textContent = active;
  document.getElementById('stat-trial').textContent = trial;
  document.getElementById('stat-premium').textContent = premium;
}

function filterTenants() {
  const searchValue = document.getElementById('search-tenants')?.value.toLowerCase() || '';
  const subscriptionFilter = document.getElementById('filter-subscription')?.value || '';
  const statusFilter = document.getElementById('filter-status')?.value || '';

  const filtered = currentTenants.filter(tenant => {
    const matchesSearch = !searchValue ||
      tenant.name.toLowerCase().includes(searchValue) ||
      tenant.code.toLowerCase().includes(searchValue) ||
      (tenant.contact_email && tenant.contact_email.toLowerCase().includes(searchValue));

    const matchesSubscription = !subscriptionFilter ||
      tenant.subscription_tier === subscriptionFilter;

    const matchesStatus = !statusFilter ||
      tenant.subscription_status === statusFilter;

    return matchesSearch && matchesSubscription && matchesStatus;
  });

  renderTenants(filtered);
  updateStats(filtered);
}

function openFormPanel(tenant = null) {
  const panel = document.getElementById('tenant-form-panel');
  const backdrop = document.getElementById('form-panel-backdrop');
  const title = document.getElementById('form-panel-title');
  const form = document.getElementById('tenant-form');

  editingTenantId = tenant?.id || null;

  if (tenant) {
    title.textContent = 'Edit Tenant';
    populateForm(tenant);
  } else {
    title.textContent = 'Add New Tenant';
    form.reset();
    document.getElementById('is-active').checked = true;
    document.getElementById('subscription-tier').value = 'free';
    document.getElementById('subscription-status').value = 'active';
  }

  // Slide in panel
  panel.classList.remove('translate-x-full');
  backdrop.classList.remove('hidden');
  backdrop.classList.add('opacity-100');
}

function closeFormPanel() {
  const panel = document.getElementById('tenant-form-panel');
  const backdrop = document.getElementById('form-panel-backdrop');
  const form = document.getElementById('tenant-form');

  panel.classList.add('translate-x-full');
  backdrop.classList.remove('opacity-100');
  setTimeout(() => {
    backdrop.classList.add('hidden');
  }, 300);

  form.reset();
  editingTenantId = null;
}

function populateForm(tenant) {
  document.getElementById('tenant-name').value = tenant.name || '';
  document.getElementById('tenant-code').value = tenant.code || '';
  document.getElementById('tenant-description').value = tenant.description || '';
  document.getElementById('subscription-tier').value = tenant.subscription_tier || 'free';
  document.getElementById('subscription-status').value = tenant.subscription_status || 'active';
  document.getElementById('max-companies').value = tenant.max_companies || 1;
  document.getElementById('max-users').value = tenant.max_users || 5;
  document.getElementById('max-storage').value = tenant.max_storage_gb || 1;
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
      closeFormPanel();
      await loadTenants();
      showToast(editingTenantId ? 'Tenant updated successfully' : 'Tenant created successfully', 'success');
    } else {
      const error = await response.json();
      showToast(error.detail || 'Failed to save tenant', 'error');
    }
  } catch (error) {
    console.error('Failed to save tenant:', error);
    showToast('Failed to save tenant', 'error');
  }
}

async function editTenant(tenantId) {
  try {
    const response = await apiFetch(`/org/tenants/${tenantId}`);
    if (response.ok) {
      const tenant = await response.json();
      openFormPanel(tenant);
    } else {
      showToast('Failed to load tenant details', 'error');
    }
  } catch (error) {
    console.error('Failed to load tenant:', error);
    showToast('Failed to load tenant details', 'error');
  }
}

async function deleteTenant(tenantId, tenantName) {
  if (!confirm(`Are you sure you want to delete "${tenantName}"? This action cannot be undone.`)) {
    return;
  }

  try {
    const response = await apiFetch(`/org/tenants/${tenantId}`, {
      method: 'DELETE'
    });

    if (response.ok) {
      await loadTenants();
      showToast('Tenant deleted successfully', 'success');
    } else {
      const error = await response.json();
      showToast(error.detail || 'Failed to delete tenant', 'error');
    }
  } catch (error) {
    console.error('Failed to delete tenant:', error);
    showToast('Failed to delete tenant', 'error');
  }
}


function switchTab(tenantId, tabName) {
  const tabs = document.querySelectorAll(`.tenant-tab[data-tenant-id="${tenantId}"]`);
  const contents = document.querySelectorAll(`.tab-content[data-tenant-id="${tenantId}"]`);

  // Update tab styles
  tabs.forEach(tab => {
    if (tab.dataset.tab === tabName) {
      tab.classList.add('active', 'border-blue-600', 'text-blue-600', 'bg-white');
      tab.classList.remove('border-transparent', 'text-gray-600');
    } else {
      tab.classList.remove('active', 'border-blue-600', 'text-blue-600', 'bg-white');
      tab.classList.add('border-transparent', 'text-gray-600');
    }
  });

  // Show/hide content
  contents.forEach(content => {
    if (content.dataset.tab === tabName) {
      content.classList.remove('hidden');
    } else {
      content.classList.add('hidden');
    }
  });

  // Load organization structure when organization tab is clicked
  if (tabName === 'organization') {
    loadOrganizationStructure(tenantId);
  }
}

async function loadOrganizationStructure(tenantId) {
  const container = document.getElementById(`org-structure-${tenantId}`);
  if (!container) return;

  // Check if already loaded
  if (container.dataset.loaded === 'true') return;

  // Show loading state
  container.innerHTML = `
    <div class="text-center py-8 text-gray-500">
      <i class="bi bi-hourglass-split text-2xl mb-2 animate-spin"></i>
      <p>Loading organization structure...</p>
    </div>
  `;

  try {
    // Load companies, branches, and departments for this tenant
    const [companiesRes, branchesRes, departmentsRes] = await Promise.all([
      apiFetch(`/org/companies?tenant_id=${tenantId}`),
      apiFetch(`/org/branches?tenant_id=${tenantId}`),
      apiFetch(`/org/departments?tenant_id=${tenantId}`)
    ]);

    const [companiesData, branchesData, departmentsData] = await Promise.all([
      companiesRes.json(),
      branchesRes.json(),
      departmentsRes.json()
    ]);

    const companies = companiesData.items || [];
    const branches = branchesData.items || [];
    const departments = departmentsData.items || [];

    // Render the organization structure
    container.innerHTML = renderOrganizationStructure(companies, branches, departments);
    container.dataset.loaded = 'true';
  } catch (error) {
    console.error('Failed to load organization structure:', error);
    container.innerHTML = `
      <div class="text-center py-8 text-red-500">
        <i class="bi bi-exclamation-triangle text-2xl mb-2"></i>
        <p>Failed to load organization structure</p>
        <button onclick="loadOrganizationStructure('${tenantId}')"
          class="mt-3 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          Retry
        </button>
      </div>
    `;
  }
}

function renderOrganizationStructure(companies, branches, departments) {
  if (companies.length === 0) {
    return `
      <div class="text-center py-8 text-gray-500">
        <i class="bi bi-building text-4xl mb-3 opacity-50"></i>
        <p class="text-lg font-medium">No organizations yet</p>
        <p class="text-sm mt-1">Create your first company to get started</p>
      </div>
    `;
  }

  let html = '<div class="space-y-4">';

  companies.forEach(company => {
    const companyBranches = branches.filter(b => b.company_id === company.id);

    html += `
      <div class="border border-gray-200 rounded-lg overflow-hidden">
        <!-- Company Header -->
        <div class="bg-blue-50 px-4 py-3 flex items-center gap-3">
          <i class="bi bi-building text-blue-600 text-xl"></i>
          <div class="flex-1">
            <h4 class="font-semibold text-gray-900">${escapeHtml(company.name)}</h4>
            ${company.description ? `<p class="text-sm text-gray-600">${escapeHtml(company.description)}</p>` : ''}
          </div>
          <span class="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">${companyBranches.length} Branches</span>
        </div>

        <!-- Branches -->
        ${companyBranches.length > 0 ? `
          <div class="bg-white">
            ${companyBranches.map(branch => {
              const branchDepartments = departments.filter(d => d.branch_id === branch.id);
              return `
                <div class="border-t border-gray-200">
                  <!-- Branch Header -->
                  <div class="bg-green-50 px-4 py-2 flex items-center gap-3 pl-8">
                    <i class="bi bi-diagram-2 text-green-600"></i>
                    <div class="flex-1">
                      <h5 class="font-medium text-gray-900">${escapeHtml(branch.name)}</h5>
                      ${branch.description ? `<p class="text-xs text-gray-600">${escapeHtml(branch.description)}</p>` : ''}
                    </div>
                    <span class="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">${branchDepartments.length} Departments</span>
                  </div>

                  <!-- Departments -->
                  ${branchDepartments.length > 0 ? `
                    <div class="bg-gray-50 px-4 py-2 pl-16">
                      <div class="space-y-1">
                        ${branchDepartments.map(dept => `
                          <div class="flex items-center gap-2 text-sm py-1">
                            <i class="bi bi-diagram-3 text-purple-600"></i>
                            <span class="text-gray-900">${escapeHtml(dept.name)}</span>
                            ${dept.description ? `<span class="text-gray-500 text-xs">- ${escapeHtml(dept.description)}</span>` : ''}
                          </div>
                        `).join('')}
                      </div>
                    </div>
                  ` : ''}
                </div>
              `;
            }).join('')}
          </div>
        ` : `
          <div class="px-4 py-3 text-sm text-gray-500 italic">
            No branches yet
          </div>
        `}
      </div>
    `;
  });

  html += '</div>';
  return html;
}

function viewOrganization(tenantId, tenantName) {
  if (window.orgHierarchy) {
    window.orgHierarchy.open(tenantId, tenantName);
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

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Export functions for global access
window.editTenant = editTenant;
window.deleteTenant = deleteTenant;
window.switchTab = switchTab;
window.loadOrganizationStructure = loadOrganizationStructure;
window.viewOrganization = viewOrganization;
