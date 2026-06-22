(function(){
  'use strict';
  const _token = sessionStorage.getItem('access_token');
  if (!_token) { window.location.href = '/patient/login'; return; }
  const parts=location.pathname.split('/');
  const RX_ID=parts[parts.indexOf('prescriptions')+1];
  const API=`/api/v1/patients/me/prescriptions/${RX_ID}`;
  const SM={pending:'badge-pending',dispensed:'badge-dispensed',partially_dispensed:'badge-partial',cancelled:'badge-cancelled'};
  const _locale = localStorage.getItem('hc_locale') || 'id-ID';
  const SL_MAPS = {
    'id-ID': {pending:'Menunggu',dispensed:'Sudah Diberikan',partially_dispensed:'Sebagian',cancelled:'Dibatalkan'},
    'en-US': {pending:'Pending',dispensed:'Dispensed',partially_dispensed:'Partial',cancelled:'Cancelled'},
  };
  const SL = SL_MAPS[_locale] || SL_MAPS['id-ID'];
  function statusBadge(s){return `<span class="badge ${SM[s]||''}">${SL[s]||s}</span>`;}
  function escHtml(s){return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}

  async function load(){
    try{const res=await window.apiFetch(API);const rx=await res.json();render(rx);}
    catch(e){document.getElementById('rx-header').innerHTML='<div style="color:var(--color-danger);">Gagal memuat data.</div>';}
  }

  function render(rx){
    document.getElementById('rx-header').innerHTML=`
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:.875rem;">
        <div><b>Tanggal:</b> ${escHtml(rx.encounter_date||'—')}</div>
        <div><b>Klinik:</b> ${escHtml(rx.clinic_name||'—')}</div>
        <div><b>Dokter:</b> ${escHtml(rx.provider_name||'—')}</div>
        <div><b>Status:</b> ${statusBadge(rx.status)}</div>
      </div>`;
    const c=document.getElementById('lines-container');c.innerHTML='';
    const lines=rx.lines||[];
    if(!lines.length){c.innerHTML='<div style="color:var(--color-text-secondary);text-align:center;padding:16px;">Tidak ada item obat.</div>';return;}
    lines.forEach(line=>{
      const div=document.createElement('div');div.className='line-card';
      div.innerHTML=`
        <div style="display:flex;justify-content:space-between;align-items:flex-start;">
          <div>
            <div style="font-weight:600;">${escHtml(line.medication_name||line.medication?.name||'—')}</div>
            <div style="font-size:.8rem;color:var(--color-text-secondary);">${escHtml(line.dosage_instructions||'—')}</div>
            <div style="font-size:.8rem;color:var(--color-text-secondary);">Jumlah diberikan: ${line.quantity_dispensed||0}</div>
          </div>
          ${statusBadge(line.status)}
        </div>`;
      c.appendChild(div);
    });
  }
  load();
})();
