/* lab-results.js — Patient lab results list */
(function () {
  'use strict';

  const API = '/api/v1/patients/me/lab-orders';

  function hasCritical(order) {
    return Array.isArray(order.results) && order.results.some(r => r.is_critical);
  }

  function hasSharedResult(order) {
    return Array.isArray(order.results) && order.results.some(r => r.is_shared !== false);
  }

  function statusLabel(s) {
    const _locale = localStorage.getItem('hc_locale') || 'id-ID';
    const maps = {
      'id-ID': {
        ordered: 'Dipesan', specimen_collected: 'Spesimen Dikumpulkan',
        processing: 'Diproses', resulted: 'Hasil Tersedia', cancelled: 'Dibatalkan'
      },
      'en-US': {
        ordered: 'Ordered', specimen_collected: 'Specimen Collected',
        processing: 'Processing', resulted: 'Results Available', cancelled: 'Cancelled'
      }
    };
    return (maps[_locale] || maps['id-ID'])[s] || s;
  }

  function renderCard(order) {
    const panels = (order.order_lines || []).map(l => l.test_panel_name || l.panel_name || '').filter(Boolean).join(', ');
    const crit = hasCritical(order);
    return `
      <div class="card">
        <div class="card-title">
          ${panels || 'Pemeriksaan Lab'}
          ${crit ? '<span class="badge badge-critical" style="margin-left:8px">Hasil Kritis</span>' : ''}
        </div>
        ${crit ? '<div class="critical-notice">Segera hubungi dokter Anda</div>' : ''}
        <div class="card-meta">
          ${order.encounter_date || ''} · ${order.clinic_name || order.branch_name || ''}
          <span class="badge badge-status" style="margin-left:8px">${statusLabel(order.status)}</span>
          ${order.resulted_at ? ` · Selesai: ${order.resulted_at}` : ''}
        </div>
        <button class="btn btn-primary" data-id="${order.id}">Lihat Hasil</button>
      </div>
    `;
  }

  async function load() {
    const _token = sessionStorage.getItem('access_token');
    if (!_token) { window.location.href = '/patient/login'; return; }
    try {
      const res = await window.apiFetch(API);
      const orders = (Array.isArray(res) ? res : (res.results || res.data || []))
        .filter(o => o.status === 'resulted' && hasSharedResult(o));
      const list = document.getElementById('orders-list');
      const empty = document.getElementById('empty-state');
      if (!orders.length) { empty.classList.remove('hidden'); return; }
      list.innerHTML = orders.map(renderCard).join('');
      list.addEventListener('click', e => {
        const btn = e.target.closest('button[data-id]');
        if (btn) location.href = `/patient/lab-results/${btn.dataset.id}`;
      });
    } catch (e) {
      console.error('Failed to load lab results', e);
    }
  }

  document.addEventListener('DOMContentLoaded', load);
})();
