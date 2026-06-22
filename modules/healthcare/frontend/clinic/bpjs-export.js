(function(){
  'use strict';
  const locale=localStorage.getItem('locale')||'id-ID';
  const params=new URLSearchParams(location.search);
  const branchId=params.get('branch_id');
  const BASE=`/api/v1/modules/healthcare_billing/branches/${branchId}/bpjs-exports`;

  document.getElementById('page-title').textContent=t(locale,'billing.bpjs_export_title');
  document.getElementById('warning-text').textContent=t(locale,'billing.bpjs_warning');
  document.getElementById('btn-generate').textContent=t(locale,'billing.generate_export');

  // Default period = current month
  const now=new Date();
  document.getElementById('period-input').value=`${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}`;

  function formatIDR(n){return 'Rp '+Number(n||0).toLocaleString('id-ID');}
  function statusBadge(s){
    const map={pending:['badge-draft','Menunggu'],processing:['badge-draft','Proses'],completed:['badge-finalized','Selesai'],failed:['badge-void','Gagal']};
    const [cls,label]=map[s]||['badge-draft',s||'-'];
    return `<span class="status-badge ${cls}">${label}</span>`;
  }

  async function loadExports(){
    const tbody=document.getElementById('exports-tbody');
    tbody.innerHTML='<tr><td colspan="6" class="empty-state">Memuat…</td></tr>';
    try{
      const res=await window.apiFetch(BASE+'?page_size=50');
      const items=res.items||res.data||res||[];
      if(!items.length){tbody.innerHTML='<tr><td colspan="6" class="empty-state">Belum ada ekspor.</td></tr>';return;}
      tbody.innerHTML='';
      items.forEach(exp=>{
        const tr=document.createElement('tr');
        tr.innerHTML=`
          <td>${exp.export_period||'-'}</td>
          <td>${exp.record_count!=null?exp.record_count:'-'}</td>
          <td>${formatIDR(exp.total_amount)}</td>
          <td>${statusBadge(exp.status)}</td>
          <td>${exp.generated_at?new Date(exp.generated_at).toLocaleString('id-ID'):'-'}</td>
          <td><button class="btn btn-secondary btn-sm" data-dl="${exp.id}" ${exp.status!=='completed'?'disabled':''}>Download</button></td>`;
        tr.querySelector('[data-dl]').addEventListener('click',async()=>{
          try{
            const resp=await window.apiFetch(`${BASE}/${exp.id}/download`,{responseType:'blob'});
            // If blob returned
            let blob=resp;
            if(!(resp instanceof Blob)) blob=new Blob([JSON.stringify(resp)],{type:'application/json'});
            const url=URL.createObjectURL(blob);
            const a=document.createElement('a');a.href=url;a.download=`bpjs_${exp.export_period}.json`;a.click();
            URL.revokeObjectURL(url);
          }catch(err){alert('Gagal download: '+err.message);}
        });
        tbody.appendChild(tr);
      });
    }catch(err){
      tbody.innerHTML=`<tr><td colspan="6" class="empty-state" style="color:var(--color-danger)">Gagal: ${err.message}</td></tr>`;
    }
  }

  document.getElementById('btn-generate').addEventListener('click',async()=>{
    const period=document.getElementById('period-input').value;
    if(!period){alert('Pilih periode terlebih dahulu.');return;}
    const spinner=document.getElementById('generate-spinner');
    const btn=document.getElementById('btn-generate');
    spinner.style.display='block';btn.disabled=true;
    try{
      await window.apiFetch(BASE,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({export_period:period})});
      loadExports();
    }catch(err){alert('Gagal generate: '+err.message);}
    finally{spinner.style.display='none';btn.disabled=false;}
  });

  loadExports();
})();
