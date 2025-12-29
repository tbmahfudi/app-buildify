import { apiFetch } from './api.js';

const selectors = {
  addButton: 'btn-add-company',
  saveButton: 'btn-save-company',
  tableBody: '#companies-table tbody',
  modal: 'companyModal',
  form: 'company-form',
  id: 'company-id',
  code: 'company-code',
  name: 'company-name',
  error: 'company-error',
};

document.addEventListener('route:loaded', (event) => {
  if (event.detail.route === 'companies') {
    initCompaniesPage();
  }
});

async function initCompaniesPage() {
  const modal = getModal();
  const addButton = document.getElementById(selectors.addButton);
  const saveButton = document.getElementById(selectors.saveButton);

  if (!modal || !addButton || !saveButton) {
    return;
  }

  if (!modal.dataset.initialized) {
    addButton.addEventListener('click', () => openModal());
    saveButton.addEventListener('click', handleSaveClick);

    modal.querySelectorAll('[data-company-modal-close]').forEach((button) => {
      button.addEventListener('click', closeModal);
    });

    modal.addEventListener('click', (event) => {
      if (event.target === modal) {
        closeModal();
      }
    });

    modal.dataset.initialized = 'true';
  }

  await loadCompanies();
}

async function loadCompanies() {
  const tbody = document.querySelector(selectors.tableBody);
  if (!tbody) {
    return;
  }

  tbody.innerHTML = renderLoadingState();

  try {
    const response = await apiFetch('/org/companies');
    const payload = await response.json();
    renderCompanies(payload.items || []);
  } catch (error) {
    tbody.innerHTML = renderErrorState('Failed to load companies');
    console.error('Failed to load companies:', error);
  }
}

function renderCompanies(companies) {
  const tbody = document.querySelector(selectors.tableBody);
  if (!tbody) {
    return;
  }

  tbody.innerHTML = '';

  if (!companies.length) {
    tbody.innerHTML = renderEmptyState();
    return;
  }

  companies.forEach((company) => {
    const row = document.createElement('tr');
    row.className = 'border-b border-gray-200 hover:bg-gray-50 transition';

    // Create cells with XSS protection
    const codeCell = document.createElement('td');
    codeCell.className = 'px-6 py-4 text-sm font-medium text-gray-900';
    codeCell.textContent = company.code;

    const nameCell = document.createElement('td');
    nameCell.className = 'px-6 py-4 text-sm text-gray-600';
    nameCell.textContent = company.name;

    const dateCell = document.createElement('td');
    dateCell.className = 'px-6 py-4 text-sm text-gray-600';
    dateCell.textContent = formatDate(company.created_at);

    const actionsCell = document.createElement('td');
    actionsCell.className = 'px-6 py-4 text-sm flex gap-2';

    const editBtn = document.createElement('button');
    editBtn.className = 'edit-btn px-3 py-1 text-blue-600 border border-blue-600 rounded hover:bg-blue-50 transition text-sm';
    editBtn.setAttribute('data-company-id', company.id);
    editBtn.innerHTML = '<i class="ph ph-pencil"></i> Edit';

    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'delete-btn px-3 py-1 text-red-600 border border-red-600 rounded hover:bg-red-50 transition text-sm';
    deleteBtn.setAttribute('data-company-id', company.id);
    deleteBtn.innerHTML = '<i class="ph ph-trash"></i> Delete';

    actionsCell.appendChild(editBtn);
    actionsCell.appendChild(deleteBtn);

    row.appendChild(codeCell);
    row.appendChild(nameCell);
    row.appendChild(dateCell);
    row.appendChild(actionsCell);

    tbody.appendChild(row);
  });

  tbody.querySelectorAll('.edit-btn').forEach((button) => {
    button.addEventListener('click', () => editCompany(button.dataset.companyId));
  });

  tbody.querySelectorAll('.delete-btn').forEach((button) => {
    button.addEventListener('click', () => deleteCompany(button.dataset.companyId));
  });
}

function renderEmptyState() {
  return `
    <tr>
      <td colspan="4" class="px-6 py-8 text-center text-gray-500">
        <i class="ph ph-tray text-2xl block mb-2"></i>
        <p>No companies found</p>
      </td>
    </tr>
  `;
}

function renderLoadingState() {
  return `
    <tr>
      <td colspan="4" class="px-6 py-8 text-center text-gray-500">
        <div class="flex items-center justify-center gap-2">
          <span class="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></span>
          Loading companies...
        </div>
      </td>
    </tr>
  `;
}

function renderErrorState(message) {
  return `
    <tr>
      <td colspan="4" class="px-6 py-8 text-center text-red-600">${message}</td>
    </tr>
  `;
}

function openModal(company = null) {
  const modal = getModal();
  const form = document.getElementById(selectors.form);
  const errorEl = document.getElementById(selectors.error);
  if (!modal || !form || !errorEl) {
    return;
  }

  form.reset();
  form.querySelector(`#${selectors.id}`).value = company?.id ?? '';
  form.querySelector(`#${selectors.code}`).value = company?.code ?? '';
  form.querySelector(`#${selectors.name}`).value = company?.name ?? '';

  errorEl.textContent = '';
  errorEl.classList.add('hidden');

  modal.classList.remove('hidden');
}

function closeModal() {
  const modal = getModal();
  if (modal) {
    modal.classList.add('hidden');
  }
}

async function editCompany(id) {
  if (!id) {
    return;
  }

  try {
    const response = await apiFetch(`/org/companies/${id}`);
    const company = await response.json();
    openModal(company);
  } catch (error) {
    console.error('Failed to load company', error);
    alert('Failed to load company details');
  }
}

async function deleteCompany(id) {
  if (!id) {
    return;
  }

  const confirmed = window.confirm('Are you sure you want to delete this company?');
  if (!confirmed) {
    return;
  }

  try {
    const response = await apiFetch(`/org/companies/${id}`, { method: 'DELETE' });
    if (response.ok) {
      await loadCompanies();
    } else {
      const error = await safeJson(response);
      alert((error && error.detail) || 'Delete failed');
    }
  } catch (error) {
    console.error('Delete failed', error);
    alert('Delete failed');
  }
}

async function handleSaveClick(event) {
  event.preventDefault();

  const form = document.getElementById(selectors.form);
  const errorEl = document.getElementById(selectors.error);
  const saveButton = document.getElementById(selectors.saveButton);

  if (!form || !errorEl || !saveButton) {
    return;
  }

  const id = form.querySelector(`#${selectors.id}`).value.trim();
  const code = form.querySelector(`#${selectors.code}`).value.trim();
  const name = form.querySelector(`#${selectors.name}`).value.trim();

  errorEl.textContent = '';
  errorEl.classList.add('hidden');

  if (!code || !name) {
    errorEl.textContent = 'All fields are required';
    errorEl.classList.remove('hidden');
    return;
  }

  const url = id ? `/org/companies/${id}` : '/org/companies';
  const method = id ? 'PUT' : 'POST';
  const payload = { code, name };

  saveButton.disabled = true;
  saveButton.classList.add('opacity-60');

  try {
    const response = await apiFetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (response.ok) {
      closeModal();
      await loadCompanies();
    } else {
      const error = await safeJson(response);
      errorEl.textContent = (error && error.detail) || 'Save failed';
      errorEl.classList.remove('hidden');
    }
  } catch (error) {
    console.error('Save failed', error);
    errorEl.textContent = 'Save failed';
    errorEl.classList.remove('hidden');
  } finally {
    saveButton.disabled = false;
    saveButton.classList.remove('opacity-60');
  }
}

function getModal() {
  return document.getElementById(selectors.modal);
}

function formatDate(value) {
  if (!value) {
    return '—';
  }
  try {
    return new Date(value).toLocaleDateString();
  } catch (error) {
    return value;
  }
}

async function safeJson(response) {
  try {
    return await response.json();
  } catch (_) {
    return null;
  }
}
