(function(){
  'use strict';
  const parts=location.pathname.split('/');
  const rxIdx=parts.indexOf('prescriptions');
  const RX_ID=parts[rxIdx+1];
  const BRANCH_ID=new URLSearchParams(location.search).get('branch_id');
  const RX_API=`/api/v1/modules/healthcare_pharmacy/branches/${BRANCH_ID}/prescriptions/${RX_ID}`;
  const role=window.__userRole||'';
  let rxData=null;

  const SM={pending:'badge-pending',dispensed:'badge-dispensed',partially_dispensed:'badge-partial',cancelled:'badge-cancelled'};
  const SL={pending:'Pending',dispensed:'Dispensed',partially_dispensed:'Sebagian',cancelled:'Dibatalkan'};
  function statusBadge(s){return `<span class="badge ${SM[s]||''}">${SL[s]||s}</span>`;}
  function escHtml(s){return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
  function showAlert(id,msg,show=true){const el=document.getElementById(id);if(msg!==undefined)el.innerHTML=msg;el.style.display=show?'block':'none';}

  async function loadRx(){
    try{const res=await window.apiFetch(RX_API);rxData=await res.json();render();}
    catch(e){showAlert('error-alert','Gagal memuat data resep.');}
  }

  function render(){
    if(!rxData)return;
    document.getElementById('rx-header-content').innerHTML=`
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:8px;font-size:.875rem;">
        <div><b>Kunjungan:</b> ${escHtml(rxData.encounter_date||'—')}</div>
        <div><b>Dokter:</b> ${escHtml(rxData.provider_name||'—')}</div>
        <div><b>Pasien:</b> ${escHtml(rxData.patient_name||rxData.patient_id||'—')}</div>
        <div><b>Status:</b> ${statusBadge(rxData.status)}</div>
      </div>`;
    const notes=rxData.notes||'';
    if(notes.toLowerCase().includes('interaksi')||notes.toLowerCase().includes('interaction')){
      showAlert('interaction-panel','<strong>&#9888; Peringatan Interaksi Obat:</strong><br>'+escHtml(notes));
    }
    if(role==='doctor'&&rxData.status!=='cancelled'&&rxData.status!=='dispensed'){
      document.getElementById('btn-cancel-rx').style.display='';
    }
    renderLines();
  }

  function renderLines(){
    const tbody=document.getElementById('lines-tbody');
    tbody.innerHTML='';
    (rxData.lines||[]).forEach((line,idx)=>{
      const rem=(line.quantity_ordered||0)-(line.quantity_dispensed||0);
      const can=['pending','partially_dispensed'].includes(line.status)&&rem>0;
      const tr=document.createElement('tr');
      tr.innerHTML=`
        <td><div style="font-weight:600;">${escHtml(line.medication_name||line.medication?.name||'—')}</div><div style="font-size:.75rem;color:var(--color-text-secondary);">${escHtml(line.medication?.generic_name||'')}</div></td>
        <td>${escHtml(line.dosage_instructions||'—')}</td>
        <td>${line.quantity_ordered||0}</td><td>${line.quantity_dispensed||0}</td>
        <td style="${rem>0?'color:var(--color-warning-dark);font-weight:700;':''}">${rem}</td>
        <td>${statusBadge(line.status)}</td>
        <td>${can?`<input type="number" min="0" max="${rem}" value="${rem}" data-idx="${idx}" class="qi" style="width:70px;"/>`:'—'}</td>
        <td>${can?`<input type="text" data-idx="${idx}" class="bi" placeholder="Batch"/>`:'—'}</td>
        <td>${can?`<input type="date" data-idx="${idx}" class="ei"/>`:'—'}</td>`;
      tbody.appendChild(tr);
    });
  }

  document.getElementById('btn-dispense-all').addEventListener('click',()=>{document.querySelectorAll('.qi').forEach(i=>{i.value=i.max;});});

  document.getElementById('btn-submit').addEventListener('click',async()=>{
    const lines=[];
    document.querySelectorAll('.qi').forEach(inp=>{
      const idx=parseInt(inp.dataset.idx);const line=rxData.lines[idx];
      const batch=document.querySelector(`.bi[data-idx="${idx}"]`)?.value||'';
      const expiry=document.querySelector(`.ei[data-idx="${idx}"]`)?.value||'';
      lines.push({line_id:line.id,quantity_dispensed:parseInt(inp.value)||0,batch_number:batch,expiry_date:expiry});
    });
    if(!lines.length){showAlert('error-alert','Tidak ada item untuk di-dispense.');return;}
    try{
      const res=await window.apiFetch(`${RX_API}/dispense`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({lines})});
      if(res.status===422){const b=await res.json();showAlert('error-alert','Stok tidak mencukupi: '+(b.detail||b.message||''));return;}
      if(!res.ok)throw new Error(await res.text());
      showAlert('success-alert','Dispense berhasil.');showAlert('error-alert','',false);
      setTimeout(()=>location.reload(),1200);
    }catch(e){showAlert('error-alert','Gagal dispense: '+e.message);}
  });

  document.getElementById('btn-cancel-rx').addEventListener('click',async()=>{
    if(!confirm('Batalkan resep ini?'))return;
    try{
      const res=await window.apiFetch(RX_API,{method:'DELETE'});
      if(!res.ok)throw new Error(await res.text());
      showAlert('success-alert','Resep dibatalkan.');setTimeout(()=>history.back(),1200);
    }catch(e){showAlert('error-alert','Gagal membatalkan: '+e.message);}
  });

  loadRx();
})();
