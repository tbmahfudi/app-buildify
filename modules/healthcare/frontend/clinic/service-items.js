(function(){
  'use strict';
  const locale=localStorage.getItem('locale')||'id-ID';
  const params=new URLSearchParams(location.search);
  const branchId=params.get('branch_id');
  const BASE=`/api/v1/modules/healthcare_billing/branches/${branchId}/service-items`;

  document.getElementById('page-title').textContent=t(locale,'billing.service_items_title');

  function formatIDR(n){return 'Rp '+Number(n||0).toLocaleString('id-ID');}
  function catBadge(c){
    const colors={konsultasi:'var(--color-primary)',tindakan:'var(--color-info)',obat:'var(--color-success-700)',lab:'var(--color-warning-700)',lainnya:'var(--color-neutral-600)'};
    return `<span style="background:${colors[c]||'var(--color-neutral-300)'};color:#fff;padding:2px 8px;border-radius:10px;font-size:.78rem">${c||'-'}</span>`;
  }

  async function loadItems(){
    const cat=document.getElementById('filter-category').value;
    const activeOnly=document.getElementById('filter-active-only').checked;
    let url=BASE+'?page_size=200';
    if(cat) url+='&category='+cat;
    if(activeOnly) url+='&is_active=true';
    const tbody=document.getElementById('items-tbody');
    tbody.innerHTML='<tr><td colspan="6" class="empty-state">Memuat…</td></tr>';
    try{
      const res=await window.apiFetch(url);
      const items=res.items||res.data||res||[];
      if(!items.length){tbody.innerHTML='<tr><td colspan="6" class="empty-state">Tidak ada data.</td></tr>';return;}
      tbody.innerHTML='';
      items.forEach(item=>{
        const tr=document.createElement('tr');
        tr.innerHTML=`
          <td>${item.code||'-'}</td>
          <td>${item.name||'-'}</td>
          <td>${catBadge(item.category)}</td>
          <td>${formatIDR(item.unit_price)}</td>
          <td>
            <label style="display:inline-flex;align-items:center;gap:.4rem;cursor:pointer">
              <input type="checkbox" ${item.is_active?'checked':''} data-toggle="${item.id}"/>
              ${item.is_active?'Aktif':'Nonaktif'}
            </label>
          </td>
          <td><button class="btn btn-secondary btn-sm" data-edit="${item.id}">Edit</button></td>`;
        // Toggle active
        tr.querySelector('[data-toggle]').addEventListener('change',async function(){
          await window.apiFetch(`${BASE}/${item.id}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({is_active:this.checked})});
          loadItems();
        });
        // Edit
        tr.querySelector('[data-edit]').addEventListener('click',()=>openModal(item));
        tbody.appendChild(tr);
      });
    }catch(err){
      tbody.innerHTML=`<tr><td colspan="6" class="empty-state" style="color:var(--color-danger)">Gagal: ${err.message}</td></tr>`;
    }
  }

  // Modal
  const modal=document.getElementById('item-modal');
  document.getElementById('item-cancel').addEventListener('click',()=>modal.classList.remove('open'));
  document.getElementById('btn-add').addEventListener('click',()=>openModal(null));

  function openModal(item){
    document.getElementById('modal-title').textContent=item?'Edit Layanan':'Tambah Layanan';
    document.getElementById('item-id').value=item?item.id:'';
    document.getElementById('item-name').value=item?item.name:'';
    document.getElementById('item-code').value=item?item.code:'';
    document.getElementById('item-price').value=item?item.unit_price:'';
    document.getElementById('item-category').value=item?item.category:'konsultasi';
    const codeNotice=document.getElementById('code-notice');
    const codeInput=document.getElementById('item-code');
    if(item&&item.used_in_invoice){
      codeInput.readOnly=true;codeNotice.style.display='';
    }else{
      codeInput.readOnly=false;codeNotice.style.display='none';
    }
    modal.classList.add('open');
  }

  document.getElementById('item-submit').addEventListener('click',async()=>{
    const id=document.getElementById('item-id').value;
    const payload={
      name:document.getElementById('item-name').value,
      code:document.getElementById('item-code').value,
      unit_price:parseFloat(document.getElementById('item-price').value)||0,
      category:document.getElementById('item-category').value,
    };
    if(!payload.name){alert('Nama wajib diisi.');return;}
    try{
      if(id){await window.apiFetch(`${BASE}/${id}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});}
      else{await window.apiFetch(BASE,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});}
      modal.classList.remove('open');loadItems();
    }catch(err){alert('Gagal: '+err.message);}
  });

  document.getElementById('btn-filter').addEventListener('click',loadItems);
  document.getElementById('filter-active-only').addEventListener('change',loadItems);
  loadItems();
})();
