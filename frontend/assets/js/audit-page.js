import { AuditWidget } from './audit-widget.js';
import { apiFetch } from './api.js';

document.addEventListener('route:loaded', async (e) => {
  if (e.detail.route === 'audit') {
    initAuditPage();
  }
});

async function loadStats() {
  try {
    const res = await apiFetch('/audit/stats/summary');
    if (!res.ok) return;
    const s = await res.json();
    const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val ?? 0; };
    set('stat-total',   s.total_events   ?? s.total   ?? 0);
    set('stat-success', s.success_count  ?? s.success  ?? 0);
    set('stat-failure', s.failure_count  ?? s.failures ?? 0);
    set('stat-users',   s.unique_users   ?? s.users    ?? 0);
  } catch { /* non-fatal — stats bar stays at 0 */ }
}

function initAuditPage() {
  const container = document.getElementById('audit-container');

  const widget = new AuditWidget(container, {
    showFilters: true,
    pageSize: 20
  });

  widget.render();
  loadStats();

  // Refresh button reloads both the list and the stats bar
  document.getElementById('btn-refresh-audit').onclick = () => {
    widget.refresh();
    loadStats();
  };
}
