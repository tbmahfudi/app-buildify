/**
 * Organization Hierarchy Management
 * Handles the display and management of Companies → Branches → Departments hierarchy
 */

import { apiFetch } from './api.js';
import { showToast } from './ui-utils.js';

let currentTenantId = null;
let currentTenantName = null;
let orgData = {
  companies: [],
  branches: [],
  departments: []
};

/**
 * Open organization hierarchy modal for a tenant
 */
export async function openOrganizationHierarchy(tenantId, tenantName) {
  currentTenantId = tenantId;
  currentTenantName = tenantName;

  // Update modal title
  document.getElementById('org-modal-subtitle').textContent = `${tenantName} - Manage companies, branches, and departments`;

  // Show modal
  document.getElementById('modal-overlay').classList.remove('hidden');
  document.getElementById('org-hierarchy-modal').classList.remove('hidden');

  // Load organization data
  await loadOrganizationData();
}

/**
 * Load all organization data for the current tenant
 */
async function loadOrganizationData() {
  try {
    // Load companies, branches, and departments in parallel - filtered by tenant
    const [companiesRes, branchesRes, departmentsRes] = await Promise.all([
      apiFetch(`/org/companies?tenant_id=${currentTenantId}`),
      apiFetch(`/org/branches?tenant_id=${currentTenantId}`),
      apiFetch(`/org/departments?tenant_id=${currentTenantId}`)
    ]);

    orgData.companies = await companiesRes.json();
    orgData.branches = await branchesRes.json();
    orgData.departments = await departmentsRes.json();

    // Render the organization tree
    renderOrganizationTree();
  } catch (error) {
    console.error('Failed to load organization data:', error);
    showToast('Failed to load organization data', 'error');
  }
}

/**
 * Render the organization tree hierarchy
 */
function renderOrganizationTree() {
  const container = document.getElementById('org-tree-container');
  const companies = orgData.companies.items || orgData.companies;

  if (!companies || companies.length === 0) {
    container.innerHTML = `
      <div class="text-center py-12">
        <i class="ph-duotone ph-building text-6xl text-gray-300 mb-4"></i>
        <p class="text-gray-500 mb-4">No companies yet</p>
        <button onclick="window.orgHierarchy.addCompany()" class="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
          <i class="ph ph-plus"></i>
          Add First Company
        </button>
      </div>
    `;
    return;
  }

  let html = '<div class="space-y-4">';

  companies.forEach(company => {
    const companyBranches = (orgData.branches.items || orgData.branches).filter(b => b.company_id === company.id);
    const companyDepartments = (orgData.departments.items || orgData.departments).filter(d => d.company_id === company.id);

    html += `
      <div class="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <!-- Company Header -->
        <div class="flex items-center justify-between p-4 bg-blue-50 border-b border-blue-100">
          <div class="flex items-center gap-3">
            <i class="ph-duotone ph-buildings text-2xl text-blue-600"></i>
            <div>
              <h4 class="font-semibold text-gray-900">${escapeHtml(company.name)}</h4>
              <p class="text-sm text-gray-500">Code: ${escapeHtml(company.code)}</p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <button onclick="window.orgHierarchy.addBranch('${company.id}')"
              class="inline-flex items-center gap-1 px-3 py-1.5 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 transition">
              <i class="ph ph-plus"></i>
              Branch
            </button>
            <button onclick="window.orgHierarchy.addDepartment('${company.id}')"
              class="inline-flex items-center gap-1 px-3 py-1.5 text-sm bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition">
              <i class="ph ph-plus"></i>
              Department
            </button>
            <button onclick="window.orgHierarchy.editCompany('${company.id}')"
              class="p-2 text-gray-600 hover:text-blue-600 transition">
              <i class="ph ph-pencil-simple"></i>
            </button>
            <button onclick="window.orgHierarchy.deleteCompany('${company.id}', '${escapeHtml(company.name)}')"
              class="p-2 text-gray-600 hover:text-red-600 transition">
              <i class="ph ph-trash"></i>
            </button>
          </div>
        </div>

        <!-- Company Body (Branches & Departments) -->
        <div class="p-4 space-y-3">
          ${companyBranches.length > 0 ? `
            <div>
              <h5 class="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                <i class="ph ph-map-pin text-green-600"></i>
                Branches (${companyBranches.length})
              </h5>
              <div class="space-y-2 ml-6">
                ${companyBranches.map(branch => renderBranch(branch, companyDepartments)).join('')}
              </div>
            </div>
          ` : ''}

          ${companyDepartments.filter(d => !d.branch_id).length > 0 ? `
            <div>
              <h5 class="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                <i class="ph ph-users-three text-purple-600"></i>
                Company-Wide Departments (${companyDepartments.filter(d => !d.branch_id).length})
              </h5>
              <div class="space-y-1 ml-6">
                ${companyDepartments.filter(d => !d.branch_id).map(dept => renderDepartment(dept)).join('')}
              </div>
            </div>
          ` : ''}

          ${companyBranches.length === 0 && companyDepartments.length === 0 ? `
            <p class="text-sm text-gray-400 italic">No branches or departments yet</p>
          ` : ''}
        </div>
      </div>
    `;
  });

  html += '</div>';
  container.innerHTML = html;
}

/**
 * Render a branch with its departments
 */
function renderBranch(branch, allDepartments) {
  const branchDepartments = allDepartments.filter(d => d.branch_id === branch.id);

  return `
    <div class="bg-green-50 rounded-lg p-3 border border-green-100">
      <div class="flex items-center justify-between mb-2">
        <div class="flex items-center gap-2">
          <i class="ph ph-map-pin-line text-green-600"></i>
          <span class="font-medium text-gray-900 text-sm">${escapeHtml(branch.name)}</span>
          <span class="text-xs text-gray-500">(${escapeHtml(branch.code)})</span>
        </div>
        <div class="flex items-center gap-1">
          <button onclick="window.orgHierarchy.addDepartment('${branch.company_id}', '${branch.id}')"
            class="p-1 text-xs text-gray-600 hover:text-purple-600 transition" title="Add Department">
            <i class="ph ph-plus-circle"></i>
          </button>
          <button onclick="window.orgHierarchy.editBranch('${branch.id}')"
            class="p-1 text-xs text-gray-600 hover:text-blue-600 transition" title="Edit">
            <i class="ph ph-pencil-simple-line"></i>
          </button>
          <button onclick="window.orgHierarchy.deleteBranch('${branch.id}', '${escapeHtml(branch.name)}')"
            class="p-1 text-xs text-gray-600 hover:text-red-600 transition" title="Delete">
            <i class="ph ph-trash"></i>
          </button>
        </div>
      </div>
      ${branchDepartments.length > 0 ? `
        <div class="ml-4 space-y-1 mt-2">
          ${branchDepartments.map(dept => renderDepartment(dept)).join('')}
        </div>
      ` : ''}
    </div>
  `;
}

/**
 * Render a department
 */
function renderDepartment(dept) {
  return `
    <div class="bg-purple-50 rounded px-3 py-2 border border-purple-100 flex items-center justify-between text-sm">
      <div class="flex items-center gap-2">
        <i class="ph ph-identification-badge text-purple-600"></i>
        <span class="text-gray-900">${escapeHtml(dept.name)}</span>
        <span class="text-xs text-gray-500">(${escapeHtml(dept.code)})</span>
      </div>
      <div class="flex items-center gap-1">
        <button onclick="window.orgHierarchy.editDepartment('${dept.id}')"
          class="p-1 text-xs text-gray-600 hover:text-blue-600 transition">
          <i class="ph ph-pencil-simple-line"></i>
        </button>
        <button onclick="window.orgHierarchy.deleteDepartment('${dept.id}', '${escapeHtml(dept.name)}')"
          class="p-1 text-xs text-gray-600 hover:text-red-600 transition">
          <i class="ph ph-trash"></i>
        </button>
      </div>
    </div>
  `;
}

/**
 * Add new company
 */
export function addCompany() {
  openEntityModal('company', 'Add Company', null, currentTenantId);
}

/**
 * Edit company
 */
export async function editCompany(companyId) {
  try {
    const response = await apiFetch(`/org/companies/${companyId}`);
    const company = await response.json();
    openEntityModal('company', 'Edit Company', company, currentTenantId);
  } catch (error) {
    showToast('Failed to load company', 'error');
  }
}

/**
 * Delete company
 */
export async function deleteCompany(companyId, companyName) {
  if (!confirm(`Are you sure you want to delete "${companyName}"? This will also delete all branches and departments.`)) {
    return;
  }

  try {
    const response = await apiFetch(`/org/companies/${companyId}`, { method: 'DELETE' });
    if (response.ok) {
      showToast('Company deleted successfully', 'success');
      await loadOrganizationData();
    } else {
      throw new Error('Delete failed');
    }
  } catch (error) {
    showToast('Failed to delete company', 'error');
  }
}

/**
 * Add branch
 */
export function addBranch(companyId) {
  openEntityModal('branch', 'Add Branch', null, currentTenantId, companyId);
}

/**
 * Edit branch
 */
export async function editBranch(branchId) {
  try {
    const response = await apiFetch(`/org/branches/${branchId}`);
    const branch = await response.json();
    openEntityModal('branch', 'Edit Branch', branch, currentTenantId, branch.company_id);
  } catch (error) {
    showToast('Failed to load branch', 'error');
  }
}

/**
 * Delete branch
 */
export async function deleteBranch(branchId, branchName) {
  if (!confirm(`Are you sure you want to delete "${branchName}"? This will also delete all departments in this branch.`)) {
    return;
  }

  try {
    const response = await apiFetch(`/org/branches/${branchId}`, { method: 'DELETE' });
    if (response.ok) {
      showToast('Branch deleted successfully', 'success');
      await loadOrganizationData();
    } else {
      throw new Error('Delete failed');
    }
  } catch (error) {
    showToast('Failed to delete branch', 'error');
  }
}

/**
 * Add department
 */
export function addDepartment(companyId, branchId = null) {
  openEntityModal('department', 'Add Department', null, currentTenantId, companyId, branchId);
}

/**
 * Edit department
 */
export async function editDepartment(departmentId) {
  try {
    const response = await apiFetch(`/org/departments/${departmentId}`);
    const department = await response.json();
    openEntityModal('department', 'Edit Department', department, currentTenantId, department.company_id, department.branch_id);
  } catch (error) {
    showToast('Failed to load department', 'error');
  }
}

/**
 * Delete department
 */
export async function deleteDepartment(departmentId, departmentName) {
  if (!confirm(`Are you sure you want to delete "${departmentName}"?`)) {
    return;
  }

  try {
    const response = await apiFetch(`/org/departments/${departmentId}`, { method: 'DELETE' });
    if (response.ok) {
      showToast('Department deleted successfully', 'success');
      await loadOrganizationData();
    } else {
      throw new Error('Delete failed');
    }
  } catch (error) {
    showToast('Failed to delete department', 'error');
  }
}

/**
 * Open entity (company/branch/department) modal
 */
function openEntityModal(entityType, title, entityData, tenantId, companyId = null, branchId = null) {
  const modal = document.getElementById('org-entity-modal');
  const form = document.getElementById('org-entity-form');

  // Set modal title
  document.getElementById('org-entity-modal-title').textContent = title;

  // Set hidden fields
  document.getElementById('org-entity-type').value = entityType;
  document.getElementById('org-entity-id').value = entityData?.id || '';
  document.getElementById('org-entity-tenant-id').value = tenantId;
  document.getElementById('org-entity-parent-id').value = companyId || '';

  // Set form fields
  document.getElementById('org-entity-code').value = entityData?.code || '';
  document.getElementById('org-entity-name').value = entityData?.name || '';
  document.getElementById('org-entity-description').value = entityData?.description || '';

  // Add entity-specific fields
  const extraFields = document.getElementById('org-entity-extra-fields');
  extraFields.innerHTML = '';

  if (entityType === 'branch') {
    extraFields.innerHTML = `
      <input type="hidden" name="company_id" value="${companyId}">
    `;
  } else if (entityType === 'department') {
    extraFields.innerHTML = `
      <input type="hidden" name="company_id" value="${companyId}">
      ${branchId ? `<input type="hidden" name="branch_id" value="${branchId}">` : ''}
    `;
  }

  // Show modal
  modal.classList.remove('hidden');
}

/**
 * Save entity (company/branch/department)
 */
async function saveEntity(formData) {
  const entityType = formData.get('entity_type');
  const entityId = formData.get('entity_id');
  const isEdit = !!entityId;

  const payload = {
    code: formData.get('code'),
    name: formData.get('name'),
    description: formData.get('description') || null
  };

  if (entityType === 'branch' || entityType === 'department') {
    payload.company_id = formData.get('company_id');
  }

  if (entityType === 'department' && formData.get('branch_id')) {
    payload.branch_id = formData.get('branch_id');
  }

  try {
    let endpoint = `/org/${entityType === 'company' ? 'companies' : entityType === 'branch' ? 'branches' : 'departments'}`;
    if (isEdit) {
      endpoint += `/${entityId}`;
    }

    const response = await apiFetch(endpoint, {
      method: isEdit ? 'PUT' : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (response.ok) {
      showToast(`${entityType.charAt(0).toUpperCase() + entityType.slice(1)} ${isEdit ? 'updated' : 'created'} successfully`, 'success');
      closeEntityModal();
      await loadOrganizationData();
    } else {
      const error = await response.json();
      throw new Error(error.detail || 'Save failed');
    }
  } catch (error) {
    showToast(`Failed to save ${entityType}: ${error.message}`, 'error');
  }
}

/**
 * Close entity modal
 */
function closeEntityModal() {
  document.getElementById('org-entity-modal').classList.add('hidden');
  document.getElementById('org-entity-form').reset();
}

/**
 * Close organization hierarchy modal
 */
function closeOrgHierarchyModal() {
  document.getElementById('org-hierarchy-modal').classList.add('hidden');
  document.getElementById('modal-overlay').classList.add('hidden');
  currentTenantId = null;
  currentTenantName = null;
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

/**
 * Initialize event listeners
 */
document.addEventListener('DOMContentLoaded', () => {
  // Close buttons
  document.getElementById('btn-close-org-modal')?.addEventListener('click', closeOrgHierarchyModal);
  document.getElementById('btn-close-org-hierarchy')?.addEventListener('click', closeOrgHierarchyModal);
  document.getElementById('btn-close-org-entity-modal')?.addEventListener('click', closeEntityModal);
  document.getElementById('btn-cancel-org-entity')?.addEventListener('click', closeEntityModal);

  // Add company from hierarchy modal
  document.getElementById('btn-add-company-from-hierarchy')?.addEventListener('click', addCompany);

  // Entity form submission
  document.getElementById('org-entity-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    await saveEntity(formData);
  });

  // Handle overlay click - close org hierarchy modal if it's open
  const overlay = document.getElementById('modal-overlay');
  if (overlay) {
    overlay.addEventListener('click', (e) => {
      const orgModal = document.getElementById('org-hierarchy-modal');
      const entityModal = document.getElementById('org-entity-modal');

      // If org hierarchy modal is visible, close it
      if (orgModal && !orgModal.classList.contains('hidden')) {
        closeOrgHierarchyModal();
        e.stopPropagation();
      }
      // If entity modal is visible, close it
      else if (entityModal && !entityModal.classList.contains('hidden')) {
        closeEntityModal();
        e.stopPropagation();
      }
    });
  }

  // Prevent modal content clicks from closing the modal
  document.getElementById('org-hierarchy-modal')?.addEventListener('click', (e) => {
    e.stopPropagation();
  });
  document.getElementById('org-entity-modal')?.addEventListener('click', (e) => {
    e.stopPropagation();
  });
});

// Export functions for global access
window.orgHierarchy = {
  open: openOrganizationHierarchy,
  addCompany,
  editCompany,
  deleteCompany,
  addBranch,
  editBranch,
  deleteBranch,
  addDepartment,
  editDepartment,
  deleteDepartment
};
