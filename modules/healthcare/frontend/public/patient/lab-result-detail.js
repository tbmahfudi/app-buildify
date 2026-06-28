/* lab-result-detail.js — Patient result detail (read-only) */
(function () {
  'use strict';

  const pathParts = location.pathname.split('/');
  const orderId = pathParts[pathParts.length - 1] || pathParts[pathParts.length - 2];
  const API = `/api/v1/patients/me/lab-orders/${orderId}/results`;
  const ORDER_API = `/api/v1/patients/me/lab-orders/${orderId}`;

  function renderResults(data) {
    const wrap = document.getElementById('results-wrap');
    // Group by panel
    const byPanel = {};
    (data.results || data || []).forEach(r => {
      const key = r.test_panel_name || r.panel_name || 'Pemeriksaan';
      if (!byPanel[key]) byPanel[key] = [];
      byPanel[key].push(r);
    });

    wrap.innerHTML = Object.entries(byPanel).map(([panel, rows]) => {
      const hasCrit = rows.some(r => r.is_critical);
      return `
        <div class="section">
          <h2 style="font-size:1rem;font-weight:700;margin-bottom:8px">${panel}</h2>
          ${hasCrit ? '<div class="critical-notice"><span class="badge badge-critical">KRITIS</span> Segera hubungi dokter Anda</div>' : ''}
          <table>
            <thead>
              <tr><th>Pemeriksaan</th><th>Hasil</th><th>Satuan</th><th>Referensi</th><th>Keterangan</th></tr>
            </thead>
            <tbody>
              ${rows.map(r => `
                <tr>
                  <td>${r.test_name || r.name || '-'}</td>
                  <td>${r.result_value || '-'}</td>
                  <td>${r.result_unit || r.unit || '-'}</td>
                  <td>${r.reference_range || '-'}</td>
                  <td>
                    ${r.is_critical ? '<span class="badge badge-critical">KRITIS</span>' : ''}
                    ${r.is_abnormal && !r.is_critical ? '<span class="badge badge-abnormal">Di luar normal</span>' : ''}
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `;
    }).join('');
  }

  async function load() {
    const _token = sessionStorage.getItem('access_token');
    if (!_token) { window.location.href = '/patient/login'; return; }
    try {
      const [order, resultData] = await Promise.all([
        window.apiFetch(ORDER_API),
        window.apiFetch(API),
      ]);
      const panels = (order.order_lines || []).map(l => l.test_panel_name || l.panel_name || '').filter(Boolean).join(', ');
      document.getElementById('order-info').innerHTML =
        `${panels || 'Pemeriksaan Lab'} · ${order.encounter_date || ''} · ${order.clinic_name || order.branch_name || ''}`;
      renderResults(resultData);
    } catch (e) {
      console.error('Failed to load result detail', e);
    }
  }

  document.addEventListener('DOMContentLoaded', load);
})();
