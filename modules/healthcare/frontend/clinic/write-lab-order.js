/* write-lab-order.js — Doctor lab order entry */
(function () {
  'use strict';

  const params = new URLSearchParams(location.search);
  const branchId = params.get('branch_id') || '';
  const encounterId = params.get('encounter_id') || '';
  const PANELS_API = `/api/v1/modules/healthcare_lab/branches/${branchId}/test-panels`;
  const ORDERS_API = `/api/v1/modules/healthcare_lab/branches/${branchId}/orders`;
  const ENCOUNTER_API = `/api/v1/modules/healthcare/branches/${branchId}/encounters/${encounterId}`;

  let selectedPanels = [];
  let searchTimeout = null;

  function fmt(n) { return Number(n).toLocaleString('id-ID'); }

  function updateTatEstimate() {
    const tatEl = document.getElementById('tat-estimate');
    if (!selectedPanels.length) { tatEl.classList.add('hidden'); return; }
    const maxTat = Math.max(...selectedPanels.map(p => p.turnaround_hours || 0));
    tatEl.textContent = `Estimasi selesai: ${maxTat} jam`;
    tatEl.classList.remove('hidden');
  }

  function renderSelectedPanels() {
    const wrap = document.getElementById('selected-panels');
    wrap.innerHTML = selectedPanels.map((p, i) => `
      <div class="selected-panel-row">
        <span class="pname">${p.name}</span>
        <span style="font-size:.8rem;color:var(--color-text-muted)">${p.category} · ${p.sample_type} · ${p.turnaround_hours}j · Rp ${fmt(p.unit_price)}</span>
        ${p.requires_fasting ? '<span class="badge" style="background:var(--color-warning-light);color:var(--color-warning)">🍽 Puasa</span>' : ''}
        <button class="btn-danger-sm" data-idx="${i}">✕</button>
      </div>
    `).join('');
    wrap.querySelectorAll('.btn-danger-sm').forEach(btn => {
      btn.addEventListener('click', () => {
        selectedPanels.splice(parseInt(btn.dataset.idx, 10), 1);
        renderSelectedPanels();
        updateTatEstimate();
      });
    });
    updateTatEstimate();
  }

  function addPanel(panel) {
    if (selectedPanels.some(p => p.id === panel.id)) return;
    selectedPanels.push(panel);
    renderSelectedPanels();
    document.getElementById('panel-search').value = '';
    document.getElementById('autocomplete-list').classList.add('hidden');
  }

  async function searchPanels(q) {
    if (!q.trim()) { document.getElementById('autocomplete-list').classList.add('hidden'); return; }
    try {
      const res = await window.apiFetch(`${PANELS_API}?search=${encodeURIComponent(q)}&is_active=true`);
      const panels = Array.isArray(res) ? res : (res.results || res.data || []);
      const list = document.getElementById('autocomplete-list');
      if (!panels.length) { list.classList.add('hidden'); return; }
      list.innerHTML = panels.slice(0, 10).map(p => `
        <div class="autocomplete-item" data-id="${p.id}">
          <strong>${p.name}</strong> <code style="font-size:.78rem">${p.code}</code>
          <span style="font-size:.78rem;color:var(--color-text-muted)"> · ${p.category} · ${p.sample_type} · ${p.turnaround_hours}j · Rp ${fmt(p.unit_price)}
          ${p.requires_fasting ? ' · 🍽 Puasa' : ''}</span>
        </div>
      `).join('');
      list.classList.remove('hidden');
      list.querySelectorAll('.autocomplete-item').forEach(item => {
        item.addEventListener('click', () => {
          const panel = panels.find(p => String(p.id) === item.dataset.id);
          if (panel) addPanel(panel);
        });
      });
    } catch (e) { console.error('Panel search failed', e); }
  }

  async function loadEncounter() {
    if (!encounterId) {
      document.getElementById('encounter-info').textContent = 'Tidak ada encounter dipilih.';
      return;
    }
    try {
      const enc = await window.apiFetch(ENCOUNTER_API);
      document.getElementById('encounter-info').innerHTML =
        `<strong>${enc.patient_name || enc.patient_masked || '***'}</strong> · ${enc.encounter_date || ''} · ${enc.chief_complaint || ''}`;
    } catch (e) {
      document.getElementById('encounter-info').textContent = `Encounter #${encounterId}`;
    }
  }

  async function submitOrder() {
    if (!selectedPanels.length) { alert('Pilih minimal satu panel.'); return; }
    const priority = document.querySelector('input[name="priority"]:checked').value;
    const payload = {
      encounter_id: encounterId,
      priority,
      clinical_notes: document.getElementById('clinical-notes').value,
      order_lines: selectedPanels.map(p => ({ test_panel_id: p.id })),
    };
    try {
      await window.apiFetch(ORDERS_API, { method: 'POST', body: JSON.stringify(payload) });
      alert('Order lab berhasil dibuat.');
      location.href = `/clinic/lab-orders?branch_id=${branchId}`;
    } catch (e) {
      alert('Gagal membuat order: ' + (e.message || e));
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('panel-search').addEventListener('input', e => {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => searchPanels(e.target.value), 300);
    });
    document.addEventListener('click', e => {
      if (!document.getElementById('autocomplete-list').contains(e.target) &&
          e.target !== document.getElementById('panel-search')) {
        document.getElementById('autocomplete-list').classList.add('hidden');
      }
    });
    document.getElementById('btn-submit').addEventListener('click', submitOrder);
    if (!branchId) { alert('branch_id diperlukan'); return; }
    loadEncounter();
  });
})();
