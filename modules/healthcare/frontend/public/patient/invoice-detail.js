(function(){
  'use strict';
  const _token = sessionStorage.getItem('access_token');
  if (!_token) { window.location.href = '/patient/login'; return; }
  const locale=localStorage.getItem('locale')||'id-ID';
  const invoiceId=location.pathname.split('/').pop();

  function formatIDR(n){return 'Rp '+Number(n||0).toLocaleString('id-ID');}
  function statusBadge(s){
    const map={draft:['badge-draft','billing.status_draft'],finalized:['badge-finalized','billing.status_finalized'],void:['badge-void','billing.status_void']};
    const [cls,key]=map[s]||['badge-draft','billing.status_draft'];
    return `<span class="status-badge ${cls}">${t(locale,key)}</span>`;
  }

  async function loadInvoice(){
    try{
      const inv=await window.apiFetch(`/api/v1/patients/me/invoices/${invoiceId}`);
      document.getElementById('inv-number').textContent=inv.invoice_number||'—';
      document.getElementById('inv-status').innerHTML=statusBadge(inv.status);
      document.getElementById('inv-clinic').textContent=inv.clinic_name||'-';
      document.getElementById('inv-date').textContent=inv.created_at?new Date(inv.created_at).toLocaleDateString('id-ID'):'-';

      const tbody=document.getElementById('line-items-body');
      tbody.innerHTML='';
      (inv.line_items||[]).forEach(li=>{
        const tr=document.createElement('tr');
        tr.innerHTML=`<td>${li.item_name||li.name||'-'}</td><td>${li.quantity}</td><td>${formatIDR(li.unit_price)}</td><td>${formatIDR(li.subtotal||(li.unit_price*li.quantity))}</td>`;
        tbody.appendChild(tr);
      });
      document.getElementById('inv-total').textContent='Total: '+formatIDR(inv.total_amount);

      // Payment status
      const pays=inv.payments||[];
      const paidTotal=pays.reduce((s,p)=>s+(p.amount||0),0);
      const remaining=(inv.total_amount||0)-paidTotal;
      document.getElementById('payment-status').innerHTML=
        `<div>Total Tagihan: <strong>${formatIDR(inv.total_amount)}</strong></div>
         <div>Sudah Dibayar: <strong style="color:var(--color-success-700)">${formatIDR(paidTotal)}</strong></div>
         <div>Sisa: <strong style="color:${remaining>0?'var(--color-danger)':'var(--color-success-700)'}">${formatIDR(remaining)}</strong></div>`;
    }catch(err){
      document.getElementById('inv-number').textContent='Gagal memuat';
    }
  }

  document.getElementById('btn-print').addEventListener('click',async()=>{
    try{
      const res=await window.apiFetch(`/api/v1/patients/me/invoices/${invoiceId}/pdf`);
      const win=window.open('','_blank');
      win.document.write(`<!DOCTYPE html><html><head><title>Invoice ${res.invoice_number||invoiceId}</title>
        <style>body{font-family:sans-serif;max-width:600px;margin:2rem auto;font-size:.9rem}
        table{width:100%;border-collapse:collapse}th,td{padding:.4rem .6rem;border:1px solid #ccc}
        th{background:#f0f0f0}.total{font-weight:700;font-size:1.15rem;text-align:right;margin-top:1rem}
        @media print{button{display:none}}</style></head><body>
        <h2>Invoice ${res.invoice_number||invoiceId}</h2>
        <p>Status: ${res.status||'-'} | Klinik: ${res.clinic_name||'-'} | Tanggal: ${res.created_at||'-'}</p>
        <table><thead><tr><th>Layanan</th><th>Qty</th><th>Harga</th><th>Subtotal</th></tr></thead>
        <tbody>${(res.line_items||[]).map(li=>`<tr><td>${li.item_name||'-'}</td><td>${li.quantity}</td><td>Rp ${Number(li.unit_price||0).toLocaleString('id-ID')}</td><td>Rp ${Number(li.subtotal||0).toLocaleString('id-ID')}</td></tr>`).join('')}</tbody>
        </table><div class="total">Total: Rp ${Number(res.total_amount||0).toLocaleString('id-ID')}</div>
        <br><button onclick="window.print()">Cetak</button></body></html>`);
      win.document.close();
    }catch(err){alert('Gagal: '+err.message);}
  });

  loadInvoice();
})();
