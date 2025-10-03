import { apiFetch } from './api.js';

document.addEventListener('route:loaded', async (e) => {
  if (e.detail.route === 'datatable') {
    const cfg = await (await fetch('assets/config/datatable.sample.json')).json();
    const table = document.getElementById('grid');
    const thead = table.querySelector('thead tr');
    thead.innerHTML = '';
    cfg.columns.forEach(c => {
      const th = document.createElement('th'); th.textContent = c.title; thead.appendChild(th);
    });
    async function fetchPage(page=1) {
      const req = { entity: cfg.entity, filters: cfg.filters || [], sort: cfg.sort || [], page, page_size: cfg.pageSize||25 };
      const res = await apiFetch('/meta/data/search', { method:'POST', headers: { 'Content-Type':'application/json' }, body: JSON.stringify(req)});
      const j = await res.json();
      renderRows(j.rows || []);
    }
    function renderRows(rows) {
      const tbody = table.querySelector('tbody'); tbody.innerHTML = '';
      rows.forEach(r => {
        const tr = document.createElement('tr');
        cfg.columns.forEach(c => { const td = document.createElement('td'); td.textContent = (r[c.field] ?? ''); tr.appendChild(td); });
        tbody.appendChild(tr);
      });
    }
    fetchPage(1);
  }
});
