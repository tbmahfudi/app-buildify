(async () => {
  const token = sessionStorage.getItem('access_token');
  if (!token) { location.href = '/patient/login'; return; }

  const locale = localStorage.getItem('locale') || 'id-ID';
  await initI18n(locale);
  document.querySelectorAll('[data-i18n]').forEach(el => {
    el.textContent = t(locale, el.dataset.i18n);
  });

  let tab = 'upcoming', page = 1, loading = false, done = false;
  const list = document.getElementById('appt-list');
  const sentinel = document.getElementById('sentinel');

  function esc(s){ return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;'); }

  function badgeClass(status) {
    if(status==='upcoming'||status==='confirmed') return 'badge-upcoming';
    if(status==='completed') return 'badge-completed';
    if(status==='cancelled') return 'badge-cancelled';
    return 'badge-type';
  }

  function formatDT(d) {
    if(!d) return '';
    const dt = new Date(d);
    return dt.toLocaleDateString(locale,{day:'2-digit',month:'short',year:'numeric'}) + ' ' +
           dt.toLocaleTimeString(locale,{hour:'2-digit',minute:'2-digit'});
  }

  function renderCard(a) {
    return `<div class="appt-card">
      <div class="appt-card-top">
        <span class="appt-clinic">${esc(a.clinic_name)}</span>
        <span class="badge ${badgeClass(a.status)}">${esc(a.status)}</span>
      </div>
      <div class="appt-meta">
        ${esc(a.branch_name||'')} · ${esc(a.provider_name||'')} · ${formatDT(a.datetime||a.date)}<br/>
        <span class="badge badge-type" style="margin-top:4px;display:inline-block">${esc(a.appointment_type||a.type||'')}</span>
      </div>
      <button class="btn-detail" onclick="location.href='/patient/appointments/${esc(a.appointment_id||a.id)}'"
        data-i18n="appointments.detail_button">${t(locale,'appointments.detail_button')}</button>
    </div>`;
  }

  function emptyKey() {
    return tab==='upcoming' ? 'appointments.empty_upcoming' : 'appointments.empty_past';
  }

  async function loadPage() {
    if(loading||done) return;
    loading = true;

    const skels = document.createElement('div');
    skels.id='skels';
    skels.innerHTML = Array(3).fill('<div class="skeleton skel-card"></div>').join('');
    list.appendChild(skels);

    try {
      const data = await window.apiFetch(`/api/v1/patients/me/appointments?status=${tab}&page=${page}&page_size=10`);
      const items = Array.isArray(data) ? data : (data.items||[]);
      document.getElementById('skels')?.remove();

      if(items.length===0 && page===1) {
        list.innerHTML = `<div class="empty-state">${t(locale,emptyKey())}</div>`;
        done=true; return;
      }
      if(items.length===0) {
        const p=document.createElement('p');
        p.style.cssText='text-align:center;color:var(--color-muted);font-size:13px;padding:12px';
        p.textContent=t(locale,'records.no_more');
        list.appendChild(p);
        done=true; return;
      }

      const frag=document.createDocumentFragment();
      items.forEach(a=>{ const d=document.createElement('div'); d.innerHTML=renderCard(a); frag.appendChild(d.firstElementChild); });
      list.appendChild(frag);

      if(items.length<10) done=true; else page++;
    } catch(e) {
      document.getElementById('skels')?.remove();
      list.innerHTML+=`<div style="padding:16px;color:var(--color-error);font-size:13px">${e.message||'Gagal'}</div>`;
      done=true;
    } finally { loading=false; }
  }

  function switchTab(newTab) {
    tab=newTab; page=1; done=false; loading=false; list.innerHTML='';
    document.getElementById('tab-upcoming').classList.toggle('active', tab==='upcoming');
    document.getElementById('tab-past').classList.toggle('active', tab==='past');
    loadPage();
  }

  document.getElementById('tab-upcoming').addEventListener('click',()=>switchTab('upcoming'));
  document.getElementById('tab-past').addEventListener('click',()=>switchTab('past'));

  const obs=new IntersectionObserver(e=>{if(e[0].isIntersecting)loadPage();},{rootMargin:'200px'});
  obs.observe(sentinel);

  loadPage();
})();
