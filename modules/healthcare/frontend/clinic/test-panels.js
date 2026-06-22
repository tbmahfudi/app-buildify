/* test-panels.js — Lab Test Catalog Management */
(function () {
  'use strict';

  const locale = localStorage.getItem('locale') || 'id-ID';
  const params = new URLSearchParams(location.search);
  const branchId = params.get('branch_id') || '';
  const API_BASE = `/api/v1/modules/healthcare_lab/branches/${branchId}/test-panels`;

  let allPanels = [];

  function fmt(n) {
    return Number(n).toLocaleString('id-ID');
  }

  function categoryBadge(cat) {
    return `<span class="badge badge-${cat}">${cat}</span>`;
  }

  function render(panels) {
    const tbody = document.getElementById('panels-body');
    const empty = document.getElementById('empty-state');
    if (!panels.length) {
      tbody.innerHTML = '';
      empty.classList.remove('hidden');
      return;
    }
    empty.classList.add('hidden');
    tbody.innerHTML = panels.map(p => `
      <tr data-id="${p.id}">
        <td><code>${p.code}</code></td>
        <td>${p.name}</td>
        <td>${categoryBadge(p.category)}</td>
        <td>${p.sample_type}</td>
        <td style="text-align:center">${p.turnaround_hours}</td>
        <td style="text-align:right">Rp ${fmt(p.unit_price)}</td>
        <td style="text-align:center">${p.requires_fasting ? '<span class="fasting-icon" title="Puasa diperlukan">🍽</span>' : ''}</td>
        <td><span class="badge badge-${p.is_active ? 'active' : 'inactive'}">${p.is_active ? 'Aktif' : 'Nonaktif'}</span></td>
      </tr>
    `).join('');
    tbody.querySelectorAll('tr').forEach(row => {
      row.addEventListener('click', () => openModal(row.dataset.id));
    });
  }

  function applyFilters() {
    const cat = document.getElementById('filter-category').value;
    const smp = document.getElementById('filter-sample').value;
    const activeOnly = document.getElementById('filter-active').checked;
    let list = allPanels;
    if (cat) list = list.filter(p => p.category === cat);
    if (smp) list = list.filter(p => p.sample_type === smp);
    if (activeOnly) list = list.filter(p => p.is_active);
    render(list);
  }

  async function load() {
    try {
      const res = await window.apiFetch(`${API_BASE}?branch_id=${branchId}`);
      allPanels = Array.isArray(res) ? res : (res.results || res.data || []);
      applyFilters();
    } catch (e) {
      console.error('Failed to load test panels', e);
    }
  }

  function openModal(id) {
    const panel = id ? allPanels.find(p => String(p.id) === String(id)) : null;
    document.getElementById('modal-title').textContent = panel ? 'Edit Panel' : 'Tambah Panel';
    document.getElementById('panel-id').value = panel ? panel.id : '';
    document.getElementById('f-name').value = panel ? panel.name : '';
    document.getElementById('f-code').value = panel ? panel.code : '';
    document.getElementById('f-category').value = panel ? panel.category : 'hematologi';
    document.getElementById('f-sample').value = panel ? panel.sample_type : 'darah';
    document.getElementById('f-tat').value = panel ? panel.turnaround_hours : '';
    document.getElementById('f-price').value = panel ? panel.unit_price : '';
    document.getElementById('f-fasting').checked = panel ? !!panel.requires_fasting : false;
    document.getElementById('f-active').checked = panel ? !!panel.is_active : true;
    document.getElementById('modal-overlay').classList.remove('hidden');
  }

  function closeModal() {
    document.getElementById('modal-overlay').classList.add('hidden');
  }

  async function savePanel(e) {
    e.preventDefault();
    const id = document.getElementById('panel-id').value;
    const payload = {
      name: document.getElementById('f-name').value.trim(),
      code: document.getElementById('f-code').value.trim(),
      category: document.getElementById('f-category').value,
      sample_type: document.getElementById('f-sample').value,
      turnaround_hours: parseInt(document.getElementById('f-tat').value, 10),
      unit_price: parseFloat(document.getElementById('f-price').value),
      requires_fasting: document.getElementById('f-fasting').checked,
      is_active: document.getElementById('f-active').checked,
    };
    try {
      if (id) {
        await window.apiFetch(`${API_BASE}/${id}`, { method: 'PUT', body: JSON.stringify(payload) });
      } else {
        await window.apiFetch(API_BASE, { method: 'POST', body: JSON.stringify(payload) });
      }
      closeModal();
      load();
    } catch (e) {
      alert('Gagal menyimpan panel: ' + (e.message || e));
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('page-title').textContent = 'Panel Pemeriksaan Lab';
    document.getElementById('btn-add').textContent = 'Tambah Panel';
    document.getElementById('btn-add').addEventListener('click', () => openModal(null));
    document.getElementById('btn-cancel').addEventListener('click', closeModal);
    document.getElementById('modal-overlay').addEventListener('click', e => {
      if (e.target === document.getElementById('modal-overlay')) closeModal();
    });
    document.getElementById('panel-form').addEventListener('submit', savePanel);
    document.getElementById('filter-category').addEventListener('change', applyFilters);
    document.getElementById('filter-sample').addEventListener('change', applyFilters);
    document.getElementById('filter-active').addEventListener('change', applyFilters);
    if (!branchId) { alert('branch_id diperlukan'); return; }
    load();
  });
})();
