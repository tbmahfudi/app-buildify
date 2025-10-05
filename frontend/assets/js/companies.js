import { apiFetch } from './api.js';

document.addEventListener('route:loaded', async (e) => {
  if (e.detail.route === 'companies') {
    let modal, bsModal;
    
    async function loadCompanies() {
      try {
        const res = await apiFetch('/org/companies');
        const data = await res.json();
        renderCompanies(data.items || []);
      } catch (err) {
        console.error('Failed to load companies:', err);
      }
    }
    
    function renderCompanies(companies) {
      const tbody = document.querySelector('#companies-table tbody');
      tbody.innerHTML = '';
      
      companies.forEach(c => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>${c.code}</td>
          <td>${c.name}</td>
          <td>${new Date(c.created_at).toLocaleDateString()}</td>
          <td>
            <button class="btn btn-sm btn-outline-primary edit-btn" data-id="${c.id}">Edit</button>
            <button class="btn btn-sm btn-outline-danger delete-btn" data-id="${c.id}">Delete</button>
          </td>
        `;
        tbody.appendChild(tr);
      });
      
      // Attach event listeners
      document.querySelectorAll('.edit-btn').forEach(btn => {
        btn.addEventListener('click', () => editCompany(btn.dataset.id));
      });
      document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', () => deleteCompany(btn.dataset.id));
      });
    }
    
    function showModal(company = null) {
      modal = document.getElementById('companyModal');
      if (!window.bootstrap) {
        console.error('Bootstrap not loaded');
        return;
      }
      bsModal = new window.bootstrap.Modal(modal);
      
      document.getElementById('company-id').value = company?.id || '';
      document.getElementById('company-code').value = company?.code || '';
      document.getElementById('company-name').value = company?.name || '';
      document.getElementById('company-error').textContent = '';
      
      bsModal.show();
    }
    
    async function editCompany(id) {
      try {
        const res = await apiFetch(`/org/companies/${id}`);
        const company = await res.json();
        showModal(company);
      } catch (err) {
        alert('Failed to load company');
      }
    }
    
    async function deleteCompany(id) {
      if (!confirm('Delete this company?')) return;
      
      try {
        const res = await apiFetch(`/org/companies/${id}`, { method: 'DELETE' });
        if (res.ok) {
          await loadCompanies();
        } else {
          const err = await res.json();
          alert(err.detail || 'Delete failed');
        }
      } catch (err) {
        alert('Delete failed');
      }
    }
    
    async function saveCompany() {
      const id = document.getElementById('company-id').value;
      const code = document.getElementById('company-code').value.trim();
      const name = document.getElementById('company-name').value.trim();
      const errorEl = document.getElementById('company-error');
      
      errorEl.textContent = '';
      
      if (!code || !name) {
        errorEl.textContent = 'All fields are required';
        return;
      }
      
      const body = { code, name };
      const url = id ? `/org/companies/${id}` : '/org/companies';
      const method = id ? 'PUT' : 'POST';
      
      try {
        const res = await apiFetch(url, {
          method,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body)
        });
        
        if (res.ok) {
          bsModal.hide();
          await loadCompanies();
        } else {
          const err = await res.json();
          errorEl.textContent = err.detail || 'Save failed';
        }
      } catch (err) {
        errorEl.textContent = 'Save failed';
      }
    }
    
    // Wire up buttons
    document.getElementById('btn-add-company').addEventListener('click', () => showModal());
    document.getElementById('btn-save-company').addEventListener('click', saveCompany);
    
    // Load initial data
    await loadCompanies();
  }
});