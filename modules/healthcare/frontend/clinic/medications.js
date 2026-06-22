(function(){
  'use strict';
  const pathParts = location.pathname.split('/');
  const branchIdx = pathParts.indexOf('branches');
  const BRANCH_ID = branchIdx >= 0 ? pathParts[branchIdx + 1] : new URLSearchParams(location.search).get('branch_id');
  const API_BASE = `/api/v1/modules/healthcare_pharmacy/branches/${BRANCH_ID}/medications`;
  const locale = window.__locale || 'id-ID';
  let allMeds = [];

  async function loadMedications() {
    try {
      const res = await window.apiFetch(API_BASE);
      const data = await res.json();
      allMeds = data.data || data || [];
      renderTable(); checkLowStock(); populateCategoryFilter();
    } catch(e) { console.error('Failed to load medications', e); }
  }

  function populateCategoryFilter() {
    const cats = [...new Set(allMeds.map(m => m.category).filter(Boolean))];
    const sel = document.getElementById('filter-category');
    while(sel.options.length > 1) sel.remove(1);
    cats.forEach(c => { const o = document.createElement('option'); o.value=c; o.textContent=categoryLabel(c); sel.appendChild(o); });
  }

  const CAT = {analgesic:'Analgesik',antibiotic:'Antibiotik',antihypertensive:'Antihipertensi',antidiabetic:'Antidiabetik',vitamin:'Vitamin & Suplemen',other:'Lainnya'};
  function categoryLabel(c) { return CAT[c] || c; }
  function escHtml(s) { return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
  function formatIDR(n) { return 'Rp ' + Number(n).toLocaleString('id-ID'); }

  function checkLowStock() {
    const low = allMeds.filter(m => m.stock_quantity <= m.minimum_stock && m.is_active);
    const banner = document.getElementById('low-stock-banner');
    if(low.length) {
      banner.style.display = 'block';
      banner.textContent = (typeof t === 'function' ? t(locale,'pharmacy.low_stock_warning') : 'Beberapa obat hampir habis stok') + ` (${low.length} item)`;
    } else { banner.style.display = 'none'; }
  }

  function filteredMeds() {
    const cat = document.getElementById('filter-category').value;
    const lowOnly = document.getElementById('filter-low-stock').checked;
    const search = document.getElementById('filter-search').value.toLowerCase();
    return allMeds.filter(m => {
      if(cat && m.category !== cat) return false;
      if(lowOnly && m.stock_quantity > m.minimum_stock) return false;
      if(search && !((m.name||'').toLowerCase().includes(search)||(m.generic_name||'').toLowerCase().includes(search))) return false;
      return true;
    });
  }

  function renderTable() {
    const meds = filteredMeds();
    const tbody = document.getElementById('med-tbody');
    const empty = document.getElementById('empty-state');
    tbody.innerHTML = '';
    if(!meds.length) { empty.style.display=''; return; }
    empty.style.display = 'none';
    meds.forEach(m => {
      const isLow = m.stock_quantity <= m.minimum_stock;
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${escHtml(m.name)}</td>
        <td>${escHtml(m.generic_name||'—')}</td>
        <td><span class="badge badge-cat">${escHtml(categoryLabel(m.category))}</span></td>
        <td>${escHtml(m.form||'—')}</td>
        <td>${escHtml((m.strength||'')+(m.unit?' '+m.unit:''))}</td>
        <td class="${isLow?'stock-low':''}">${m.stock_quantity}${isLow?' ⚠':''} <small style="color:var(--color-text-secondary)">(min:${m.minimum_stock})</small></td>
        <td>${formatIDR(m.unit_price)}</td>
        <td><span class="badge ${m.is_active?'badge-active':'badge-inactive'}">${m.is_active?'Aktif':'Nonaktif'}</span></td>
        <td><button class="btn btn-sm btn-secondary btn-adj" data-id="${m.id}">±</button></td>
      `;
      tr.addEventListener('click', e => { if(e.target.classList.contains('btn-adj')) return; openMedModal(m); });
      tbody.appendChild(tr);
    });
    document.querySelectorAll('.btn-adj').forEach(btn => {
      btn.addEventListener('click', e => { e.stopPropagation(); const med=allMeds.find(m=>String(m.id)===btn.dataset.id); if(med) openStockModal(med); });
    });
  }

  function openMedModal(med) {
    const e = !!med;
    document.getElementById('med-modal-title').textContent = e ? 'Edit Obat' : 'Tambah Obat';
    const f = (id,v) => document.getElementById(id).value = v;
    f('med-id', e?med.id:''); f('med-name',e?med.name||'':''); f('med-generic-name',e?med.generic_name||'':'');
    f('med-brand-name',e?med.brand_name||'':''); f('med-category',e?med.category||'other':'other');
    f('med-form',e?med.form||'tablet':'tablet'); f('med-strength',e?med.strength||'':'');
    f('med-unit',e?med.unit||'':''); f('med-min-stock',e?med.minimum_stock||0:0);
    f('med-unit-price',e?med.unit_price||0:0);
    document.getElementById('med-active').checked = e ? !!med.is_active : true;
    document.getElementById('med-modal').classList.add('open');
  }

  document.getElementById('btn-add-med').addEventListener('click', () => openMedModal(null));
  document.getElementById('med-modal-cancel').addEventListener('click', () => document.getElementById('med-modal').classList.remove('open'));
  document.getElementById('med-modal-save').addEventListener('click', async () => {
    const id = document.getElementById('med-id').value;
    const g = id => document.getElementById(id).value;
    const payload = {
      name:g('med-name').trim(), generic_name:g('med-generic-name').trim(), brand_name:g('med-brand-name').trim(),
      category:g('med-category'), form:g('med-form'), strength:g('med-strength').trim(), unit:g('med-unit').trim(),
      minimum_stock:parseInt(g('med-min-stock'))||0, unit_price:parseFloat(g('med-unit-price'))||0,
      is_active:document.getElementById('med-active').checked,
    };
    if(!payload.name) { alert('Nama obat wajib diisi'); return; }
    try {
      const res = await window.apiFetch(id?`${API_BASE}/${id}`:API_BASE, {method:id?'PUT':'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
      if(!res.ok) throw new Error(await res.text());
      document.getElementById('med-modal').classList.remove('open');
      await loadMedications();
    } catch(e) { alert('Gagal menyimpan: '+e.message); }
  });

  function openStockModal(med) {
    document.getElementById('stock-med-id').value = med.id;
    document.getElementById('stock-med-name').textContent = med.name+' (stok saat ini: '+med.stock_quantity+')';
    document.getElementById('stock-delta').value=''; document.getElementById('stock-reason').value='';
    document.getElementById('stock-modal').classList.add('open');
  }
  document.getElementById('stock-modal-cancel').addEventListener('click', () => document.getElementById('stock-modal').classList.remove('open'));
  document.getElementById('stock-modal-save').addEventListener('click', async () => {
    const id = document.getElementById('stock-med-id').value;
    const delta = parseInt(document.getElementById('stock-delta').value);
    const reason = document.getElementById('stock-reason').value.trim();
    if(isNaN(delta)) { alert('Jumlah penyesuaian harus diisi'); return; }
    if(!reason) { alert('Alasan harus diisi'); return; }
    try {
      const res = await window.apiFetch(`${API_BASE}/${id}/stock-adjust`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({adjustment:delta,reason})});
      if(!res.ok) throw new Error(await res.text());
      document.getElementById('stock-modal').classList.remove('open');
      await loadMedications();
    } catch(e) { alert('Gagal menyesuaikan stok: '+e.message); }
  });

  document.getElementById('filter-category').addEventListener('change', renderTable);
  document.getElementById('filter-low-stock').addEventListener('change', renderTable);
  document.getElementById('filter-search').addEventListener('input', renderTable);
  ['med-modal','stock-modal'].forEach(id => document.getElementById(id).addEventListener('click', e => { if(e.target.id===id) document.getElementById(id).classList.remove('open'); }));
  loadMedications();
})();
