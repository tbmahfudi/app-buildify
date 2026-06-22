(function(){
  'use strict';
  const locale=localStorage.getItem('locale')||'id-ID';
  const params=new URLSearchParams(location.search);
  const branchId=params.get('branch_id');
  let lineItems=[];
  let searchTimer=null;

  document.getElementById('page-title').textContent=t(locale,'billing.new_invoice');
  document.getElementById('btn-add-item').textContent=t(locale,'billing.add_item');

  function formatIDR(n){return 'Rp '+Number(n||0).toLocaleString('id-ID');}

  // ── Patient search autocomplete ──────────────────────────────────
  const patSearch=document.getElementById('patient-search');
  const sugg=document.getElementById('patient-suggestions');
  patSearch.addEventListener('input',function(){
    clearTimeout(searchTimer);
    if(!this.value.trim()){sugg.style.display='none';return;}
    searchTimer=setTimeout(async()=>{
      try{
        const res=await window.apiFetch(`/api/v1/patients?q=${encodeURIComponent(this.value)}&page_size=10`);
        const list=res.items||res.data||res||[];
        if(!list.length){sugg.style.display='none';return;}
        sugg.innerHTML='';
        list.forEach(p=>{
          const d=document.createElement('div');
          d.textContent=`${p.name||p.full_name||'-'} — ${p.id}`;
          d.style.cssText='padding:.45rem .75rem;cursor:pointer;font-size:.875rem';
          d.addEventListener('mousedown',()=>{
            document.getElementById('patient-id').value=p.id;
            patSearch.value=p.name||p.full_name||'-';
            const sel=document.getElementById('patient-selected');
            sel.textContent='✓ Pasien dipilih: '+(p.name||p.full_name||p.id);
            sel.style.display='';
            sugg.style.display='none';
          });
          sugg.appendChild(d);
        });
        sugg.style.display='';
      }catch(_){sugg.style.display='none';}
    },300);
  });
  document.addEventListener('click',e=>{if(!sugg.contains(e.target)&&e.target!==patSearch)sugg.style.display='none';});

  // ── Line items ───────────────────────────────────────────────────
  function recalc(){
    const total=lineItems.reduce((s,i)=>s+(i.unit_price*i.quantity),0);
    document.getElementById('total-row').textContent='Total: '+formatIDR(total);
  }
  function renderLines(){
    const tbody=document.getElementById('line-items-body');
    tbody.innerHTML='';
    if(!lineItems.length){
      tbody.innerHTML='<tr id="empty-line-row"><td colspan="5" style="text-align:center;color:var(--color-neutral-400);padding:.75rem">Belum ada item.</td></tr>';
      recalc();return;
    }
    lineItems.forEach((item,idx)=>{
      const tr=document.createElement('tr');
      tr.innerHTML=`
        <td>${item.name}</td>
        <td><input type="number" min="1" value="${item.quantity}" style="width:65px;padding:.3rem;border:1px solid var(--color-border);border-radius:4px" data-idx="${idx}"/></td>
        <td>${formatIDR(item.unit_price)}</td>
        <td id="sub-${idx}">${formatIDR(item.unit_price*item.quantity)}</td>
        <td><button class="btn btn-danger btn-sm" data-remove="${idx}">✕</button></td>`;
      tbody.appendChild(tr);
    });
    tbody.querySelectorAll('input[type=number]').forEach(inp=>{
      inp.addEventListener('input',function(){
        const i=+this.dataset.idx;
        lineItems[i].quantity=Math.max(1,+this.value||1);
        document.getElementById('sub-'+i).textContent=formatIDR(lineItems[i].unit_price*lineItems[i].quantity);
        recalc();
      });
    });
    tbody.querySelectorAll('[data-remove]').forEach(btn=>{
      btn.addEventListener('click',function(){lineItems.splice(+this.dataset.remove,1);renderLines();});
    });
    recalc();
  }

  // ── Service item modal ───────────────────────────────────────────
  const serviceModal=document.getElementById('service-modal');
  let allServices=[];
  document.getElementById('btn-add-item').addEventListener('click',async()=>{
    serviceModal.classList.add('open');
    document.getElementById('service-search').value='';
    if(!allServices.length){
      document.getElementById('service-list').innerHTML='<div style="padding:.5rem;color:var(--color-neutral-400)">Memuat…</div>';
      try{
        const res=await window.apiFetch(`/api/v1/modules/healthcare_billing/branches/${branchId}/service-items?is_active=true&page_size=200`);
        allServices=res.items||res.data||res||[];
      }catch(err){
        document.getElementById('service-list').innerHTML=`<div style="color:var(--color-danger);padding:.5rem">Gagal memuat: ${err.message}</div>`;
        return;
      }
    }
    renderServiceList(allServices);
  });
  document.getElementById('service-modal-close').addEventListener('click',()=>serviceModal.classList.remove('open'));
  document.getElementById('service-search').addEventListener('input',function(){
    const q=this.value.toLowerCase();
    renderServiceList(allServices.filter(s=>(s.name||'').toLowerCase().includes(q)||(s.code||'').toLowerCase().includes(q)));
  });
  function renderServiceList(items){
    const el=document.getElementById('service-list');
    if(!items.length){el.innerHTML='<div style="padding:.5rem;color:var(--color-neutral-400)">Tidak ditemukan.</div>';return;}
    el.innerHTML='';
    items.forEach(s=>{
      const d=document.createElement('div');
      d.style.cssText='display:flex;justify-content:space-between;align-items:center;padding:.5rem .75rem;border-bottom:1px solid var(--color-border)';
      d.innerHTML=`<div><div style="font-weight:500">${s.name}</div><div style="font-size:.8rem;color:var(--color-neutral-500)">${s.code||''}</div></div>
        <div style="display:flex;align-items:center;gap:.75rem"><span style="font-size:.875rem">${formatIDR(s.unit_price)}</span>
        <button class="btn btn-primary btn-sm">Pilih</button></div>`;
      d.querySelector('button').addEventListener('click',()=>{
        lineItems.push({id:s.id,name:s.name,code:s.code,unit_price:s.unit_price,quantity:1});
        renderLines();
        serviceModal.classList.remove('open');
      });
      el.appendChild(d);
    });
  }

  // ── Save draft ───────────────────────────────────────────────────
  document.getElementById('btn-save-draft').addEventListener('click',async()=>{
    const lineErr=document.getElementById('line-error');
    if(!lineItems.length){lineErr.style.display='';return;}
    lineErr.style.display='none';
    const patientId=document.getElementById('patient-id').value;
    if(!patientId){alert('Pilih pasien terlebih dahulu.');return;}
    const payload={
      patient_id:patientId,
      encounter_id:document.getElementById('encounter-id').value||null,
      insurance_profile_id:document.getElementById('insurance-profile-id').value||null,
      notes:document.getElementById('notes').value,
      line_items:lineItems.map(i=>({service_item_id:i.id,quantity:i.quantity}))
    };
    const btn=document.getElementById('btn-save-draft');
    btn.disabled=true;btn.textContent='Menyimpan…';
    try{
      const res=await window.apiFetch(`/api/v1/modules/healthcare_billing/branches/${branchId}/invoices`,{
        method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)
      });
      const id=res.id||res.invoice_id;
      location.href=`/clinic/invoices/${id}?branch_id=${branchId}`;
    }catch(err){
      alert('Gagal menyimpan: '+err.message);
      btn.disabled=false;btn.textContent='Simpan Draft';
    }
  });
})();
