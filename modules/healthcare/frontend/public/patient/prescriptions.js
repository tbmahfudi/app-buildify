(function(){
  'use strict';
  const _token = sessionStorage.getItem('access_token');
  if (!_token) { window.location.href = '/patient/login'; return; }
  const API='/api/v1/patients/me/prescriptions';
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
    try{const res=await window.apiFetch(API);const data=await res.json();render(data.data||data||[]);}
    catch(e){console.error(e?.message || 'Request failed');}
  }

  function render(items){
    const list=document.getElementById('rx-list');
    const empty=document.getElementById('empty-state');
    list.innerHTML='';
    if(!items.length){empty.style.display='';return;}
    empty.style.display='none';
    items.forEach(rx=>{
      const names=(rx.lines||[]).map(l=>l.medication_name||l.medication?.name||'?').join(', ');
      const card=document.createElement('div');card.className='card';
      card.innerHTML=`
        <div class="card-header"><div class="card-title">${escHtml(rx.clinic_name||'Klinik')}</div>${statusBadge(rx.status)}</div>
        <div class="card-meta">Tanggal: ${escHtml(rx.encounter_date||'—')}<br/>Obat: ${escHtml(names||'—')}</div>
        <div class="card-footer"><a href="/patient/prescriptions/${rx.id}" class="btn btn-primary btn-sm">Lihat Detail</a></div>`;
      list.appendChild(card);
    });
  }
  load();
})();
