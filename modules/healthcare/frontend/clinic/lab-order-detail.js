/* lab-order-detail.js — Specimen collection + result entry workflow */
(function () {
  'use strict';

  const pathParts = location.pathname.split('/');
  const orderId = pathParts[pathParts.length - 1] || pathParts[pathParts.length - 2];
  const params = new URLSearchParams(location.search);
  const branchId = params.get('branch_id') || '';
  const ORDER_API = `/api/v1/modules/healthcare_lab/branches/${branchId}/orders/${orderId}`;

  let orderData = null;

  const TL_STEPS = ['ordered', 'specimen_collected', 'processing', 'resulted'];
  const TL_IDS   = ['tl-ordered', 'tl-collected', 'tl-processing', 'tl-resulted'];

  function uuidShort() {
    return Math.random().toString(36).slice(2, 10).toUpperCase();
  }

  function nowLocal() {
    const d = new Date();
    d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
    return d.toISOString().slice(0, 16);
  }

  function priorityClass(p) { return `priority-${p}`; }
  function priorityLabel(p) { return { stat: 'STAT', urgent: 'Urgent', routine: 'Rutin' }[p] || p; }

  function updateTimeline(status) {
    const cur = TL_STEPS.indexOf(status);
    TL_IDS.forEach((id, i) => {
      const step = document.getElementById(id);
      const dot = step.querySelector('.tl-dot');
      const lbl = step.querySelector('.tl-label');
      dot.classList.remove('active', 'done');
      lbl.classList.remove('active');
      if (i < cur) { dot.classList.add('done'); dot.textContent = '✓'; }
      else if (i === cur) { dot.classList.add('active'); lbl.classList.add('active'); }
    });
  }

  function isNumericOutOfRange(value, refRange) {
    if (!refRange || !refRange.includes('-')) return false;
    const num = parseFloat(value);
    if (isNaN(num)) return false;
    const parts = refRange.split('-').map(s => parseFloat(s.trim()));
    if (parts.length !== 2 || isNaN(parts[0]) || isNaN(parts[1])) return false;
    return num < parts[0] || num > parts[1];
  }

  function buildResultLine(line, idx) {
    const refRange = line.reference_range || '';
    const unit = line.result_unit || line.unit || '';
    return `
      <div class="result-row" id="rl-${idx}">
        <h3>${line.test_panel_name || line.panel_name || 'Panel'} ${refRange ? `<small style="font-weight:400;color:var(--color-text-muted)">Ref: ${refRange}</small>` : ''}</h3>
        <div class="inline-fields">
          <div class="form-group">
            <label>Nilai Hasil</label>
            <input type="text" class="rl-value" data-idx="${idx}" data-refrange="${refRange}" value="${line.result_value || ''}"/>
          </div>
          <div class="form-group">
            <label>Satuan</label>
            <input type="text" class="rl-unit" data-idx="${idx}" value="${unit}"/>
          </div>
        </div>
        <div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:8px">
          <label style="font-size:.88rem">
            <input type="checkbox" class="rl-abnormal" data-idx="${idx}" ${line.is_abnormal ? 'checked' : ''}/> Di luar normal
          </label>
          <label style="font-size:.88rem;color:var(--color-danger);font-weight:700">
            <input type="checkbox" class="rl-critical" data-idx="${idx}" ${line.is_critical ? 'checked' : ''}/> Nilai Kritis
          </label>
        </div>
        <div class="form-group">
          <label>Catatan</label>
          <textarea class="rl-notes" data-idx="${idx}" rows="2">${line.notes || ''}</textarea>
        </div>
      </div>
    `;
  }

  function attachResultHandlers() {
    document.querySelectorAll('.rl-value').forEach(inp => {
      inp.addEventListener('input', e => {
        const idx = e.target.dataset.idx;
        const refRange = e.target.dataset.refrange || '';
        const val = e.target.value;
        const abnCb = document.querySelector(`.rl-abnormal[data-idx="${idx}"]`);
        if (abnCb && refRange) abnCb.checked = isNumericOutOfRange(val, refRange);
        updateCriticalBanner();
      });
    });
    document.querySelectorAll('.rl-critical').forEach(cb => {
      cb.addEventListener('change', updateCriticalBanner);
    });
  }

  function updateCriticalBanner() {
    const anyCritical = [...document.querySelectorAll('.rl-critical')].some(c => c.checked);
    document.getElementById('critical-banner').classList.toggle('hidden', !anyCritical);
  }

  function showSection(id) {
    document.getElementById(id).classList.remove('hidden');
  }

  function render(order) {
    orderData = order;
    // Header
    const pBadge = document.getElementById('hdr-priority');
    pBadge.className = `badge ${priorityClass(order.priority)}`;
    pBadge.textContent = priorityLabel(order.priority);
    document.getElementById('hdr-status').textContent = order.status;
    document.getElementById('hdr-date').textContent = order.encounter_date || '-';
    document.getElementById('hdr-provider').textContent = order.provider_name || '-';
    document.getElementById('hdr-patient').textContent = order.patient_masked || order.patient_name_masked || '***';
    const notesEl = document.getElementById('hdr-notes');
    if (order.clinical_notes) notesEl.textContent = `Catatan klinis (internal): ${order.clinical_notes}`;

    // Timeline
    updateTimeline(order.status);

    // Sections
    const lines = order.order_lines || [];

    if (order.status === 'ordered') {
      showSection('specimen-section');
      const sampleTypes = [...new Set(lines.map(l => l.sample_type).filter(Boolean))];
      document.getElementById('sp-sample-type').value = sampleTypes.join(', ');
      document.getElementById('sp-collected-at').value = nowLocal();
      showSection('cancel-section');
    }

    if (order.status === 'specimen_collected' || order.status === 'processing') {
      showSection('results-section');
      const rl = document.getElementById('result-lines');
      rl.innerHTML = lines.map((l, i) => buildResultLine(l, i)).join('');
      attachResultHandlers();
    }

    if (order.status === 'resulted') {
      showSection('release-section');
    }
  }

  async function load() {
    try {
      const res = await window.apiFetch(ORDER_API);
      render(res);
    } catch (e) {
      console.error('Failed to load order detail', e);
    }
  }

  async function submitSpecimen(e) {
    e.preventDefault();
    const payload = {
      sample_type: document.getElementById('sp-sample-type').value,
      collection_datetime: document.getElementById('sp-collected-at').value,
      barcode: document.getElementById('sp-barcode').value,
      notes: document.getElementById('sp-notes').value,
    };
    try {
      await window.apiFetch(`${ORDER_API}/specimens`, { method: 'POST', body: JSON.stringify(payload) });
      load();
    } catch (e) {
      alert('Gagal menyimpan spesimen: ' + (e.message || e));
    }
  }

  async function submitResults() {
    const lines = orderData ? (orderData.order_lines || []) : [];
    const results = lines.map((l, idx) => ({
      order_line_id: l.id,
      result_value: (document.querySelector(`.rl-value[data-idx="${idx}"]`) || {}).value || '',
      result_unit: (document.querySelector(`.rl-unit[data-idx="${idx}"]`) || {}).value || '',
      is_abnormal: (document.querySelector(`.rl-abnormal[data-idx="${idx}"]`) || {}).checked || false,
      is_critical: (document.querySelector(`.rl-critical[data-idx="${idx}"]`) || {}).checked || false,
      notes: (document.querySelector(`.rl-notes[data-idx="${idx}"]`) || {}).value || '',
    }));
    try {
      await window.apiFetch(`${ORDER_API}/results`, { method: 'POST', body: JSON.stringify({ results }) });
      alert('Hasil berhasil disimpan.');
      load();
    } catch (e) {
      alert('Gagal menyimpan hasil: ' + (e.message || e));
    }
  }

  async function releaseResults() {
    try {
      await window.apiFetch(`${ORDER_API}/results/release`, { method: 'POST' });
      alert('Hasil berhasil dirilis ke pasien.');
      load();
    } catch (e) {
      alert('Gagal merilis hasil: ' + (e.message || e));
    }
  }

  async function cancelOrder() {
    if (!confirm('Batalkan order ini?')) return;
    try {
      await window.apiFetch(ORDER_API, { method: 'DELETE' });
      location.href = `/clinic/lab-orders?branch_id=${branchId}`;
    } catch (e) {
      alert('Gagal membatalkan order: ' + (e.message || e));
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('btn-auto-barcode').addEventListener('click', () => {
      document.getElementById('sp-barcode').value = uuidShort();
    });
    document.getElementById('specimen-form').addEventListener('submit', submitSpecimen);
    document.getElementById('btn-submit-results').addEventListener('click', submitResults);
    document.getElementById('btn-release').addEventListener('click', () => {
      document.getElementById('release-modal').classList.remove('hidden');
    });
    document.getElementById('btn-release-cancel').addEventListener('click', () => {
      document.getElementById('release-modal').classList.add('hidden');
    });
    document.getElementById('btn-release-confirm').addEventListener('click', () => {
      document.getElementById('release-modal').classList.add('hidden');
      releaseResults();
    });
    document.getElementById('btn-cancel-order').addEventListener('click', cancelOrder);
    load();
  });
})();
