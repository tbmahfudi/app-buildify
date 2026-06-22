(function(){
  'use strict';
  const locale=localStorage.getItem('locale')||'id-ID';
  const params=new URLSearchParams(location.search);
  const branchId=params.get('branch_id');
  const invoiceId=location.pathname.split('/').pop();
  let invoice=null;
  let phiVisible=false;
  let confirmCb=null;

  function formatIDR(n){return 'Rp '+Number(n||0).toLocaleString('id-ID');}
  function statusBadge(s){
    const map={draft:['badge-draft','billing.status_draft'],finalized:['badge-finalized','billing.status_finalized'],void:['badge-void','billing.status_void']};
    const [cls,key]=map[s]||['badge-draft','billing.status_draft'];
    return `<span class="status-badge ${cls}">${t(locale,key)}</span>`;
  }
  function fmtDate(d){return d?new Date(d).toLocaleDateString('id-ID'):'-';}

  // Confirm modal
  const confirmOverlay=document.getElementById('confirm-modal');
  document.getElementById('confirm-cancel').addEventListener('click',()=>confirmOverlay.classList.remove('open'));
  document.getElementById('confirm-ok').addEventListener('click',()=>{confirmOverlay.classList.remove('open');if(confirmCb)confirmCb();});
  function openConfirm(msg,cb){document.getElementById('confirm-msg').textContent=msg;confirmCb=cb;confirmOverlay.classList.add('open');}

  // Payment modal
  const payOverlay=document.getElementById('payment-modal');
  document.getElementById('pay-cancel').addEventListener('click',()=>payOverlay.classList.remove('open'));
  document.getElementById('lbl-record-payment').textContent=t(locale,'billing.record_payment');
  document.getElementById('lbl-pay-method').textContent=t(locale,'billing.payment_method');
  document.getElementById('pay-date').value=new Date().toISOString().slice(0,10);
  document.getElementById('pay-submit').addEventListener('click',async()=>{
    const amount=parseFloat(document.getElementById('pay-amount').value);
    if(!amount||amount<=0){alert('Masukkan jumlah valid.');return;}
    const payload={amount,payment_method:document.getElementById('pay-method').value,payment_date:document.getElementById('pay-date').value,reference_number:document.getElementById('pay-ref').value||null};
    try{
      await window.apiFetch(`/api/v1/modules/healthcare_billing/branches/${branchId}/invoices/${invoiceId}/payments`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
      payOverlay.classList.remove('open');
      loadInvoice();
    }catch(err){alert('Gagal: '+err.message);}
  });
  document.getElementById('btn-record-payment').addEventListener('click',()=>payOverlay.classList.add('open'));
  document.getElementById('btn-record-payment').textContent=t(locale,'billing.record_payment');

  // PHI toggle
  document.getElementById('phi-toggle').addEventListener('click',function(){
    phiVisible=!phiVisible;
    this.textContent=(phiVisible?'🔓 Sembunyikan':'🔒 Tampilkan');
    renderPatient();
  });
  function renderPatient(){
    const el=document.getElementById('patient-info');
    if(!invoice) return;
    if(phiVisible){
      el.className='';
      el.textContent=invoice.patient_name||invoice.patient_id||'-';
    }else{
      el.className='phi-mask';el.textContent='••••••••';
    }
  }

  function renderInvoice(inv){
    invoice=inv;
    document.getElementById('inv-number').textContent=inv.invoice_number||'—';
    document.getElementById('inv-status').innerHTML=statusBadge(inv.status);
    document.getElementById('inv-created').textContent=fmtDate(inv.created_at);
    document.getElementById('inv-finalized').textContent=fmtDate(inv.finalized_at);
    document.getElementById('inv-voided').textContent=fmtDate(inv.voided_at);
    renderPatient();

    // Line items
    const tbody=document.getElementById('line-items-body');
    tbody.innerHTML='';
    (inv.line_items||[]).forEach(li=>{
      const tr=document.createElement('tr');
      tr.innerHTML=`<td>${li.item_name||li.name||'-'}</td><td>${li.quantity}</td><td>${formatIDR(li.unit_price)}</td><td>${formatIDR(li.subtotal||(li.unit_price*li.quantity))}</td>`;
      tbody.appendChild(tr);
    });
    document.getElementById('inv-total').textContent=formatIDR(inv.total_amount);

    // Payments
    const plist=document.getElementById('payment-list');
    const pays=inv.payments||[];
    if(!pays.length){plist.innerHTML='<div style="color:var(--color-neutral-400);font-size:.875rem">Belum ada pembayaran.</div>';}
    else{
      plist.innerHTML='';
      pays.forEach(p=>{
        const d=document.createElement('div');
        d.style.cssText='display:flex;justify-content:space-between;padding:.4rem 0;border-bottom:1px solid var(--color-border);font-size:.875rem';
        d.innerHTML=`<span>${fmtDate(p.payment_date)} — ${p.payment_method||'-'}${p.reference_number?' ('+p.reference_number+')':''}</span><span style="font-weight:600">${formatIDR(p.amount)}</span>`;
        plist.appendChild(d);
      });
    }

    // Action buttons
    const userRole=window.__userRole||'staff';
    const btnFin=document.getElementById('btn-finalize');
    const btnVoid=document.getElementById('btn-void');
    const btnPay=document.getElementById('btn-record-payment');
    if(inv.status==='draft'){
      btnFin.style.display='';btnFin.textContent=t(locale,'billing.finalize');
      btnFin.onclick=()=>openConfirm(t(locale,'billing.finalize_confirm'),doFinalize);
      btnPay.style.display='';
    }
    if(inv.status==='finalized'){
      btnPay.style.display='';
      if(userRole==='manager'){btnVoid.style.display='';btnVoid.textContent=t(locale,'billing.void_invoice');btnVoid.onclick=()=>openConfirm('Batalkan invoice ini?',doVoid);}
    }
  }

  async function doFinalize(){
    try{await window.apiFetch(`/api/v1/modules/healthcare_billing/branches/${branchId}/invoices/${invoiceId}/finalize`,{method:'POST'});loadInvoice();}
    catch(err){alert('Gagal: '+err.message);}
  }
  async function doVoid(){
    try{await window.apiFetch(`/api/v1/modules/healthcare_billing/branches/${branchId}/invoices/${invoiceId}/void`,{method:'POST'});loadInvoice();}
    catch(err){alert('Gagal: '+err.message);}
  }

  // Print
  document.getElementById('btn-print').addEventListener('click',async()=>{
    try{
      const res=await window.apiFetch(`/api/v1/modules/healthcare_billing/branches/${branchId}/invoices/${invoiceId}/pdf`);
      // Render JSON as printable view
      const win=window.open('','_blank');
      win.document.write(`<!DOCTYPE html><html><head><title>Invoice ${res.invoice_number||invoiceId}</title>
        <style>body{font-family:sans-serif;max-width:700px;margin:2rem auto;font-size:.9rem}
        table{width:100%;border-collapse:collapse}th,td{padding:.4rem .6rem;border:1px solid #ccc;text-align:left}
        th{background:#f0f0f0}.total{font-weight:700;font-size:1.1rem;text-align:right;margin-top:1rem}
        @media print{button{display:none}}</style></head><body>
        <h2>Invoice ${res.invoice_number||invoiceId}</h2>
        <p>Status: ${res.status||'-'} | Tanggal: ${res.created_at||'-'}</p>
        <table><thead><tr><th>Layanan</th><th>Qty</th><th>Harga</th><th>Subtotal</th></tr></thead>
        <tbody>${(res.line_items||[]).map(li=>`<tr><td>${li.item_name||li.name||'-'}</td><td>${li.quantity}</td><td>Rp ${Number(li.unit_price||0).toLocaleString('id-ID')}</td><td>Rp ${Number(li.subtotal||0).toLocaleString('id-ID')}</td></tr>`).join('')}</tbody>
        </table><div class="total">Total: Rp ${Number(res.total_amount||0).toLocaleString('id-ID')}</div>
        <br><button onclick="window.print()">Cetak</button></body></html>`);
      win.document.close();
    }catch(err){alert('Gagal: '+err.message);}
  });

  async function loadInvoice(){
    try{
      const inv=await window.apiFetch(`/api/v1/modules/healthcare_billing/branches/${branchId}/invoices/${invoiceId}`);
      renderInvoice(inv);
    }catch(err){alert('Gagal memuat invoice: '+err.message);}
  }

  loadInvoice();
})();
