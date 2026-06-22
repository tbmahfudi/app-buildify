/* lab-orders.js — Lab Order Queue */
(function () {
  'use strict';

  const params = new URLSearchParams(location.search);
  const branchId = params.get('branch_id') || location.pathname.split('/').slice(-2, -1)[0] || '';
  const API_BASE = `/api/v1/modules/healthcare_lab/branches/${branchId}/orders`;

  let currentPage = 1;
  let hasMore = false;

  const PRIORITY_ORDER = { stat: 0, urgent: 1, routine: 2 };

  function priorityClass(p) {
    return `priority-${p}`;
  }

  function statusClass(s) {
    if (s === 'resulted') return 'status-resulted';
    if (s === 'cancelled') return 'status-cancelled';
    return 'status-badge';
  }

  function statusLabel(s) {
    const map = {
      ordered: 'Ordered', specimen_collected: 'Spesimen Dikumpulkan',
      processing: 'Diproses', resulted: 'Selesai', cancelled: 'Dibatalkan'
    };
    return map[s] || s;
  }

  function priorityLabel(p) {
    return { stat: 'STAT', urgent: 'Urgent', routine: 'Rutin' }[p] || p;
  }

  function hasCritical(order) {
    return Array.isArray(order.results) && order.results.some(r => r.is_critical);
  }

  function actionButton(order) {
    if (order.status === 'ordered') {
      return `<button class="btn btn-primary btn-action" data-id="${order.id}" data-action="collect">Kumpulkan Spesimen</button>`;
    }
    if (order.status === 'specimen_collected' || order.status === 'processing') {
      return `<button class="btn btn-primary btn-action" data-id="${order.id}" data-action="results">Input Hasil</button>`;
    }
    return '';
  }

  function renderCard(order) {
    const panels = (order.order_lines || []).map(l => l.test_panel_name || l.panel_name || '').filter(Boolean).join(', ');
    const critical = hasCritical(order) ? '<span class="badge critical-badge">KRITIS</span>' : '';
    return `
      <div class="order-card">
        <div class="order-card-header">
          <span class="badge ${priorityClass(order.priority)}">${priorityLabel(order.priority)}</span>
          <span class="badge ${statusClass(order.status)}">${statusLabel(order.status)}</span>
          ${critical}
        </div>
        <div class="order-card-meta">
          Pasien: <strong>${order.patient_masked || order.patient_name_masked || '***'}</strong>
          &nbsp;·&nbsp; ${order.encounter_date || ''}
          &nbsp;·&nbsp; dr. ${order.provider_name || '-'}
        </div>
        <div class="order-card-panels">${panels || '-'}</div>
        <div class="order-card-footer">
          ${actionButton(order)}
        </div>
      </div>
    `;
  }

  function sortOrders(orders) {
    return [...orders].sort((a, b) => {
      const pa = PRIORITY_ORDER[a.priority] ?? 9;
      const pb = PRIORITY_ORDER[b.priority] ?? 9;
      return pa - pb;
    });
  }

  async function load(page = 1, append = false) {
    const status = document.getElementById('filter-status').value;
    const priority = document.getElementById('filter-priority').value;
    const dateFrom = document.getElementById('filter-date-from').value;
    const dateTo = document.getElementById('filter-date-to').value;
    const qs = new URLSearchParams({ page });
    if (status) qs.set('status', status);
    if (priority) qs.set('priority', priority);
    if (dateFrom) qs.set('date_from', dateFrom);
    if (dateTo) qs.set('date_to', dateTo);
    try {
      const res = await window.apiFetch(`${API_BASE}?${qs}`);
      const orders = sortOrders(Array.isArray(res) ? res : (res.results || res.data || []));
      hasMore = !!res.next;
      const list = document.getElementById('orders-list');
      if (!append) list.innerHTML = '';
      if (!orders.length && !append) {
        list.innerHTML = '<p style="text-align:center;color:var(--color-text-muted);padding:40px">Tidak ada order ditemukan.</p>';
      } else {
        list.insertAdjacentHTML('beforeend', orders.map(renderCard).join(''));
      }
      document.getElementById('btn-load-more').classList.toggle('hidden', !hasMore);
    } catch (e) {
      console.error('Failed to load orders', e);
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('btn-search').addEventListener('click', () => {
      currentPage = 1;
      load(1, false);
    });
    document.getElementById('btn-load-more').addEventListener('click', () => {
      currentPage++;
      load(currentPage, true);
    });
    document.getElementById('orders-list').addEventListener('click', e => {
      const btn = e.target.closest('.btn-action');
      if (!btn) return;
      const id = btn.dataset.id;
      location.href = `/clinic/lab-orders/${id}?branch_id=${branchId}`;
    });
    if (!branchId) { alert('branch_id diperlukan'); return; }
    load();
  });
})();
