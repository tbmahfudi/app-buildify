(function(){
  'use strict';
  const params=new URLSearchParams(location.search);
  const BRANCH_ID=params.get('branch_id');
  const ENCOUNTER_ID=params.get('encounter_id');
  const MED_API=`/api/v1/modules/healthcare_pharmacy/branches/${BRANCH_ID}/medications`;
  const INT_API=`/api/v1/modules/healthcare_pharmacy/branches/${BRANCH_ID}/interactions/check`;
  const RX_API=`/api/v1/modules/healthcare_pharmacy/branches/${BRANCH_ID}/prescriptions`;
  let lines=[],severeInteraction=false,searchTimer=null;

  document.getElementById('encounter-info').textContent=`Kunjungan ID: ${ENCOUNTER_ID||'—'}`;
  function escHtml(s){return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
  function showAlert(id,msg,show=true){const el=document.getElementById(id);if(msg!==undefined)el.innerHTML=msg;el.style.display=show?'block':'none';}

  const si=document.getElementById('med-search');
  const al=document.getElementById('ac-list');
  si.addEventListener('input',()=>{
    clearTimeout(searchTimer);const q=si.value.trim();
    if(q.length<2){al.style.display='none';return;}
    searchTimer=setTimeout(()=>fetchMeds(q),300);
  });
  async function fetchMeds(q){
    try{const res=await window.apiFetch(`${MED_API}?search=${encodeURIComponent(q)}&is_active=true`);const data=await res.json();renderAC(data.data||data||[]);}
    catch(e){al.style.display='none';}
  }
  function renderAC(meds){
    al.innerHTML='';if(!meds.length){al.style.display='none';return;}
    meds.forEach(m=>{const item=document.createElement('div');item.className='ac-item';
      item.textContent=`${m.name} — ${m.strength||''}${m.unit?' '+m.unit:''} ${m.form||''} (stok: ${m.stock_quantity||0})`;
      item.addEventListener('click',()=>addLine(m));al.appendChild(item);});
    al.style.display='block';
  }
  document.addEventListener('click',e=>{if(!e.target.closest('.ac-wrap'))al.style.display='none';});

  function addLine(med){
    al.style.display='none';si.value='';
    if(lines.find(l=>l.medication.id===med.id)){alert('Obat ini sudah ditambahkan.');return;}
    lines.push({medication:med,qty:1,dosage_instructions:'',days_supply:''});
    renderLines();checkInteractions();
  }
  function removeLine(idx){lines.splice(idx,1);renderLines();checkInteractions();}

  function renderLines(){
    const tbody=document.getElementById('lines-tbody');
    const empty=document.getElementById('lines-empty');
    tbody.innerHTML='';empty.style.display=lines.length?'none':'';
    lines.forEach((l,idx)=>{
      const tr=document.createElement('tr');
      tr.innerHTML=`
        <td><div style="font-weight:600;">${escHtml(l.medication.name)}</div>
          <div style="font-size:.75rem;color:var(--color-text-secondary);">${escHtml(l.medication.generic_name||'')} ${escHtml(l.medication.strength||'')}${l.medication.unit?' '+l.medication.unit:''} ${escHtml(l.medication.form||'')}</div></td>
        <td><input type="text" value="${escHtml(l.dosage_instructions)}" data-idx="${idx}" class="di" placeholder="misal: 3x1 sesudah makan"/></td>
        <td><input type="number" min="1" value="${l.qty}" data-idx="${idx}" class="qi" style="width:70px;"/></td>
        <td><input type="number" min="1" value="${l.days_supply}" data-idx="${idx}" class="dsi" style="width:70px;"/></td>
        <td><button class="btn btn-danger btn-sm btn-rm" data-idx="${idx}">&#x2715;</button></td>`;
      tbody.appendChild(tr);
    });
    tbody.querySelectorAll('.di').forEach(i=>i.addEventListener('input',e=>{lines[e.target.dataset.idx].dosage_instructions=e.target.value;}));
    tbody.querySelectorAll('.qi').forEach(i=>i.addEventListener('input',e=>{lines[e.target.dataset.idx].qty=parseInt(e.target.value)||1;}));
    tbody.querySelectorAll('.dsi').forEach(i=>i.addEventListener('input',e=>{lines[e.target.dataset.idx].days_supply=parseInt(e.target.value)||'';}));
    tbody.querySelectorAll('.btn-rm').forEach(btn=>btn.addEventListener('click',()=>removeLine(parseInt(btn.dataset.idx))));
  }

  async function checkInteractions(){
    const ids=lines.map(l=>l.medication.id);
    showAlert('interaction-severe','',false);showAlert('interaction-mild','',false);
    document.getElementById('severe-override-wrap').style.display='none';severeInteraction=false;
    if(ids.length<2)return;
    try{
      const res=await window.apiFetch(INT_API,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({medication_ids:ids})});
      const data=await res.json();const ixs=data.interactions||[];
      const severe=ixs.filter(i=>i.severity==='severe');const mild=ixs.filter(i=>i.severity!=='severe');
      if(severe.length){
        severeInteraction=true;
        showAlert('interaction-severe','<strong>&#x26D4; Interaksi obat berbahaya ditemukan &mdash; konfirmasi dokter diperlukan</strong><ul>'+
          severe.map(i=>`<li>${escHtml(i.drug_a)} &#x2194; ${escHtml(i.drug_b)}: ${escHtml(i.description||'')}</li>`).join('')+'</ul>');
        document.getElementById('severe-override-wrap').style.display='';
      }
      if(mild.length){
        showAlert('interaction-mild','<strong>&#x26A0; Perhatian: interaksi obat ditemukan</strong><ul>'+
          mild.map(i=>`<li>${escHtml(i.drug_a)} &#x2194; ${escHtml(i.drug_b)}: ${escHtml(i.description||'')}</li>`).join('')+'</ul>');
      }
    }catch(e){console.warn('Interaction check failed',e);}
  }

  document.getElementById('btn-submit').addEventListener('click',async()=>{
    if(!lines.length){showAlert('error-alert','Tambahkan minimal satu obat.');return;}
    if(severeInteraction&&!document.getElementById('override-check').checked){
      showAlert('error-alert','Konfirmasi interaksi obat berbahaya diperlukan sebelum mengirim resep.');return;}
    const payload={encounter_id:ENCOUNTER_ID,notes:document.getElementById('notes').value.trim(),
      lines:lines.map(l=>({medication_id:l.medication.id,quantity_ordered:l.qty,dosage_instructions:l.dosage_instructions,days_supply:l.days_supply||null}))};
    const url=severeInteraction?`${RX_API}?force=true`:RX_API;
    try{
      const res=await window.apiFetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
      if(!res.ok)throw new Error(await res.text());
      showAlert('success-alert','Resep berhasil dikirim.');showAlert('error-alert','',false);
      setTimeout(()=>history.back(),1500);
    }catch(e){showAlert('error-alert','Gagal mengirim resep: '+e.message);}
  });

  renderLines();
})();
