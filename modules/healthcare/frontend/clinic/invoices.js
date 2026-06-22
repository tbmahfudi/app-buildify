(function(){
  'use strict';
  const locale = localStorage.getItem('locale')||'id-ID';
  const params = new URLSearchParams(location.search);
  const branchId = params.get('branch_id');
  let phiVisible = false;
  let page = 1;
  const PAGE_SIZE = 20;
  let confirmCallback = null;

  function formatIDR(amount){
    if(amount==null) return '-';
    return 'Rp '+Number(amount).toLocaleString('id-ID');
  }
  function statusBadge(s){
    const map={draft:['badge-draft','billing.status_draft'],finalized:['badge-finalized','billing.status_finalized'],void:['badge-void','billing.status_void']};
    const [cls,key]=map[s]||['badge-draft','billing.status_draft'];
    return `<span class="status-badge ${cls}">${t(locale,key)}</span>`;
  }
  function maskPatient(name,id){
    if(phiVisible) return name||id||'-';
    return '<span class="phi-mask">Pasien ••••</span>';
  }

  document.getElementById('page-title').textContent=t(locale,'billing.invoices_title');
  document.getElementById('btn-new-invoice').textContent=t(locale,'billing.new_invoice');
  document.getElementById('th-inv-num').textContent=t(locale,'billing.invoice_number');
  document.getElementById('th-total').textContent=t(locale,'billing.total_amount');

  // PHI toggle
  document.getElementById('phi-toggle').addEventListener('click',function(){
    phiVisible=!phiVisible;
    this.textContent=(phiVisible?'🔓':'🔒')+' '+(phiVisible?'Tampilkan PHI':'Sembunyikan PHI');
    loadInvoices(true);
  });

  document.getElementById('btn-new-invoice').addEventListener('click',function(){
    location.href='/clinic/invoices/new?branch_id='+branchId;
  });

  // Confirm modal helpers
  const overlay=document.getElementById('confirm-modal');
  document.getElementById('confirm-cancel').addEventListener('click',()=>{overlay.classList.remove('open');confirmCallback=null;});
  document.getElementById('confirm-ok').addEventListener('click',()=>{overlay.classList.remove('open');if(confirmCallback)confirmCallback();});
  function openConfirm(msg,cb){
    document.getElementById('confirm-modal-msg').textContent=msg;
    confirmCallback=cb;
    overlay.classList.add('open');
  }

  function buildRows(invoices){
    const tbody=document.getElementById('invoice-tbody');
    if(!invoices.length){
      tbody.innerHTML=`<tr><td colspan="6" class="empty-state">${t(locale,'billing.empty_invoices')}</td></tr>`;
      return;
    }
    const userRole=window.__userRole||'staff';
    invoices.forEach(inv=>{
      const tr=document.createElement('tr');
      const encDate=inv.encounter_date?new Date(inv.encounter_date).toLocaleDateString('id-ID'):'-';
      tr.innerHTML=`
        <td>${inv.invoice_number||'-'}</td>
        <td>${maskPatient(inv.patient_name,inv.patient_id)}</td>
        <td>${encDate}</td>
        <td>${formatIDR(inv.total_amount)}</td>
        <td>${statusBadge(inv.status)}</td>
        <td style="white-space:nowrap">
          <button class="btn btn-secondary btn-sm" data-action="detail" data-id="${inv.id}">Lihat Detail</button>
          ${inv.status==='draft'?`<button class="btn btn-primary btn-sm" data-action="finalize" data-id="${inv.id}" style="margin-left:.25rem">${t(locale,'billing.finalize')}</button>`:''}
          ${(inv.status==='finalized'&&userRole==='manager')?`<button class="btn btn-danger btn-sm" data-action="void" data-id="${inv.id}" style="margin-left:.25rem">${t(locale,'billing.void_invoice')}</button>`:''}
        </td>`;
      tbody.appendChild(tr);
    });
    tbody.addEventListener('click',function(e){
      const btn=e.target.closest('[data-action]');
      if(!btn) return;
      const id=btn.dataset.id;
      const action=btn.dataset.action;
      if(action==='detail') location.href=`/clinic/invoices/${id}?branch_id=${branchId}`;
      if(action==='finalize') openConfirm(t(locale,'billing.finalize_confirm'),()=>doFinalize(id));
      if(action==='void') openConfirm('Batalkan invoice ini?',()=>doVoid(id));
    },{once:true});
  }

  async function doFinalize(id){
    try{
      await window.apiFetch(`/api/v1/modules/healthcare_billing/branches/${branchId}/invoices/${id}/finalize`,{method:'POST'});
      loadInvoices(true);
    }catch(err){alert('Gagal finalisasi: '+err.message);}
  }
  async function doVoid(id){
    try{
      await window.apiFetch(`/api/v1/modules/healthcare_billing/branches/${branchId}/invoices/${id}/void`,{method:'POST'});
      loadInvoices(true);
    }catch(err){alert('Gagal batalkan: '+err.message);}
  }

  async function loadInvoices(reset){
    if(reset){page=1;document.getElementById('invoice-tbody').innerHTML='<tr><td colspan="6" class="empty-state">Memuat data…</td></tr>';}
    const status=document.getElementById('filter-status').value;
    const from=document.getElementById('filter-date-from').value;
    const to=document.getElementById('filter-date-to').value;
    const search=document.getElementById('filter-search').value;
    let url=`/api/v1/modules/healthcare_billing/branches/${branchId}/invoices?page=${page}&page_size=${PAGE_SIZE}`;
    if(status) url+='&status='+status;
    if(from) url+='&date_from='+from;
    if(to) url+='&date_to='+to;
    if(search) url+='&q='+encodeURIComponent(search);
    try{
      const res=await window.apiFetch(url);
      const invoices=res.items||res.data||res||[];
      if(reset) document.getElementById('invoice-tbody').innerHTML='';
      buildRows(invoices);
      const more=document.getElementById('btn-load-more');
      if(invoices.length===PAGE_SIZE){more.style.display='';page++;}else{more.style.display='none';}
    }catch(err){
      document.getElementById('invoice-tbody').innerHTML=`<tr><td colspan="6" class="empty-state" style="color:var(--color-danger)">Gagal memuat: ${err.message}</td></tr>`;
    }
  }

  document.getElementById('btn-filter').addEventListener('click',()=>loadInvoices(true));
  document.getElementById('btn-load-more').addEventListener('click',()=>loadInvoices(false));
  document.getElementById('filter-search').addEventListener('keydown',e=>{if(e.key==='Enter')loadInvoices(true);});

  if(branchId) loadInvoices(true);
  else document.getElementById('invoice-tbody').innerHTML='<tr><td colspan="6" class="empty-state" style="color:var(--color-danger)">branch_id diperlukan</td></tr>';
})();
