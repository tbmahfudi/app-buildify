(function(){
  'use strict';
  const pathParts = location.pathname.split('/');
  const branchIdx = pathParts.indexOf('branches');
  const BRANCH_ID = branchIdx >= 0 ? pathParts[branchIdx + 1] : new URLSearchParams(location.search).get('branch_id');
  const API_BASE = `/api/v1/modules/healthcare_pharmacy/branches/${BRANCH_ID}/prescriptions`;
  let page=1, phiVisible=false, allItems=[], hasMore=false;

  const SM = {pending:'badge-pending',dispensed:'badge-dispensed',partially_dispensed:'badge-partial',cancelled:'badge-cancelled'};
  const SL = {pending:'Pending',dispensed:'Dispensed',partially_dispensed:'Sebagian Dispensed',cancelled:'Dibatalkan'};
  function statusBadge(s){return `<span class="badge ${SM[s]||''}">${SL[s]||s}</span>`;}
  function escHtml(s){return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
  function patientDisplay(rx){return phiVisible?escHtml(rx.patient_name||rx.patient_id||'—'):'Pasien ••••';}

  async function load(append) {
    const status=document.getElementById('filter-status').value;
    const from=document.getElementById('filter-date-from').value;
    const to=document.getElementById('filter-date-to').value;
    const qp=new URLSearchParams({page,per_page:20});
    if(status)qp.set('status',status);if(from)qp.set('date_from',from);if(to)qp.set('date_to',to);
    try {
      const res=await window.apiFetch(`${API_BASE}?${qp}`);
      const data=await res.json();
      const items=data.data||data.items||data||[];
      hasMore=!!(data.has_more||data.next_page);
      allItems=append?allItems.concat(items):items;
      render();
    } catch(e){console.error(e);}
  }

  function render() {
    const list=document.getElementById('rx-list');
    const empty=document.getElementById('empty-state');
    const lmw=document.getElementById('load-more-wrap');
    list.innerHTML='';
    if(!allItems.length){empty.style.display='';lmw.style.display='none';return;}
    empty.style.display='none';
    allItems.forEach(rx=>{
      const can=['pending','partially_dispensed'].includes(rx.status);
      const card=document.createElement('div');card.className='card';
      card.innerHTML=`
        <div class="card-header"><div class="card-title">${patientDisplay(rx)}</div>${statusBadge(rx.status)}</div>
        <div class="card-meta">Kunjungan: ${escHtml(rx.encounter_date||'—')} &nbsp;|&nbsp; Dokter: ${escHtml(rx.provider_name||'—')} &nbsp;|&nbsp; ${rx.medication_count||0} obat</div>
        <div class="card-footer">
          <span style="font-size:.8rem;color:var(--color-text-secondary)">ID: ${escHtml(String(rx.id))}</span>
          ${can?`<button class="btn btn-primary btn-sm btn-disp" data-id="${rx.id}" data-i18n="pharmacy.dispense">Dispense</button>`:''}
        </div>`;
      list.appendChild(card);
    });
    document.querySelectorAll('.btn-disp').forEach(btn=>{
      btn.addEventListener('click',()=>{location.href=`/clinic/prescriptions/${btn.dataset.id}?branch_id=${BRANCH_ID}`;});
    });
    lmw.style.display=hasMore?'':'none';
  }

  document.getElementById('phi-toggle').addEventListener('click',()=>{
    phiVisible=!phiVisible;
    document.getElementById('phi-toggle').textContent=phiVisible?'Sembunyikan Info Pasien':'Tampilkan Info Pasien';
    render();
  });
  const fresh=()=>{page=1;allItems=[];load(false);};
  document.getElementById('filter-status').addEventListener('change',fresh);
  document.getElementById('filter-date-from').addEventListener('change',fresh);
  document.getElementById('filter-date-to').addEventListener('change',fresh);
  document.getElementById('btn-load-more').addEventListener('click',()=>{page++;load(true);});
  load(false);
})();
