(function(){
  'use strict';
  const _token = sessionStorage.getItem('access_token');
  if (!_token) { window.location.href = '/patient/login'; return; }
  const locale=localStorage.getItem('locale')||'id-ID';

  document.getElementById('page-title').textContent=t(locale,'billing.invoices_title');

  function formatIDR(n){return 'Rp '+Number(n||0).toLocaleString('id-ID');}
  function statusBadge(s){
    const map={draft:['badge-draft','billing.status_draft'],finalized:['badge-finalized','billing.status_finalized'],void:['badge-void','billing.status_void']};
    const [cls,key]=map[s]||['badge-draft','billing.status_draft'];
    return `<span class="status-badge ${cls}">${t(locale,key)}</span>`;
  }

  async function loadInvoices(){
    const el=document.getElementById('invoice-list');
    try{
      const res=await window.apiFetch('/api/v1/patients/me/invoices');
      const items=res.items||res.data||res||[];
      if(!items.length){
        el.innerHTML=`<div class="empty-state">${t(locale,'billing.empty_invoices')}</div>`;
        return;
      }
      el.innerHTML='';
      items.forEach(inv=>{
        const card=document.createElement('div');
        card.className='card invoice-card';
        card.innerHTML=`
          <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:.5rem">
            <div>
              <div style="font-weight:700">${inv.invoice_number||'—'}</div>
              <div style="font-size:.8rem;color:var(--color-neutral-500)">${inv.clinic_name||'-'} · ${inv.created_at?new Date(inv.created_at).toLocaleDateString('id-ID'):'-'}</div>
            </div>
            ${statusBadge(inv.status)}
          </div>
          <div style="font-size:1.1rem;font-weight:700;color:var(--color-primary);margin-bottom:.75rem">${formatIDR(inv.total_amount)}</div>
          <button class="btn btn-secondary btn-sm">Lihat Detail</button>`;
        card.querySelector('button').addEventListener('click',()=>{location.href=`/patient/invoices/${inv.id}`;});
        el.appendChild(card);
      });
    }catch(err){
      el.innerHTML=`<div class="empty-state" style="color:var(--color-danger)">Gagal memuat: ${err.message}</div>`;
    }
  }

  loadInvoices();
})();
