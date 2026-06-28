(async () => {
  const token = sessionStorage.getItem('access_token');
  if (!token) { location.href = '/patient/login'; return; }

  const locale = localStorage.getItem('locale') || 'id-ID';
  await initI18n(locale);
  document.querySelectorAll('[data-i18n]').forEach(el => {
    el.textContent = t(locale, el.dataset.i18n);
  });

  const list = document.getElementById('records-list');
  const sentinel = document.getElementById('sentinel');
  let page = 1, loading = false, done = false;
  let filters = { date_from:'', date_to:'', clinic_name:'' };

  // group by year
  const grouped = {};

  function esc(s){ return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;'); }

  function formatDate(d) {
    if(!d) return '';
    const dt = new Date(d);
    return dt.toLocaleDateString(locale, {day:'2-digit',month:'short',year:'numeric'});
  }

  function renderSkeletons() {
    return Array(3).fill('<div class="skeleton skel-card"></div>').join('');
  }

  function renderEmpty() {
    return `<div class="empty-state">
      <svg viewBox="0 0 24 24"><path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2"/><rect x="9" y="3" width="6" height="4" rx="1"/><line x1="9" y1="12" x2="15" y2="12"/><line x1="9" y1="16" x2="13" y2="16"/></svg>
      <span>${t(locale,'records.empty')}</span>
    </div>`;
  }

  function renderCard(enc) {
    const sum = enc.summary
      ? `<div class="card-summary">${esc(enc.summary)}</div>`
      : `<div class="card-summary not-shared">${t(locale,'records.summary_not_shared')}</div>`;
    return `<a class="encounter-card" href="/patient/encounters/${enc.encounter_id}">
      <div class="card-top">
        <span class="card-clinic">${esc(enc.clinic_name)}</span>
        <span class="badge">${esc(enc.encounter_type||'')}</span>
      </div>
      <div class="card-meta">${esc(enc.branch_name||'')} · ${esc(enc.provider_name||'')} · ${formatDate(enc.date)}</div>
      ${sum}
    </a>`;
  }

  async function loadPage() {
    if (loading || done) return;
    loading = true;

    const skels = document.createElement('div');
    skels.className = 'year-group';
    skels.id = 'skels';
    skels.innerHTML = renderSkeletons();
    list.appendChild(skels);

    try {
      const qs = new URLSearchParams({ page, page_size:10, ...filters });
      Object.keys(filters).forEach(k => { if(!filters[k]) qs.delete(k); });
      const data = await window.apiFetch(`/api/v1/patients/me/encounters?${qs}`);
      const items = Array.isArray(data) ? data : (data.items || []);

      document.getElementById('skels')?.remove();

      if (items.length === 0 && page === 1) {
        list.innerHTML = renderEmpty();
        done = true;
        return;
      }
      if (items.length === 0) {
        const noMore = document.createElement('p');
        noMore.style.cssText = 'text-align:center;color:var(--color-muted);font-size:13px;padding:12px';
        noMore.textContent = t(locale,'records.no_more');
        list.appendChild(noMore);
        done = true;
        return;
      }

      // group by year
      items.forEach(enc => {
        const year = enc.date ? new Date(enc.date).getFullYear() : 'Unknown';
        if (!grouped[year]) grouped[year] = [];
        grouped[year].push(enc);
      });

      // re-render all groups sorted DESC
      list.innerHTML = '';
      Object.keys(grouped).sort((a,b)=>b-a).forEach(year => {
        const sec = document.createElement('div');
        sec.className = 'year-group';
        sec.innerHTML = `<div class="year-label">${year}</div>` +
          grouped[year].map(renderCard).join('');
        list.appendChild(sec);
      });

      if (items.length < 10) { done = true; }
      else page++;
    } catch(e) {
      document.getElementById('skels')?.remove();
      list.innerHTML += `<div style="padding:16px;color:var(--color-error);font-size:13px">${e.message||'Gagal memuat'}</div>`;
      done = true;
    } finally {
      loading = false;
    }
  }

  // Infinite scroll
  const obs = new IntersectionObserver(entries => {
    if (entries[0].isIntersecting) loadPage();
  }, { rootMargin: '200px' });
  obs.observe(sentinel);

  // Filter debounce
  let debTimer;
  function resetAndLoad() {
    clearTimeout(debTimer);
    debTimer = setTimeout(() => {
      filters.date_from   = document.getElementById('f-from').value;
      filters.date_to     = document.getElementById('f-to').value;
      filters.clinic_name = document.getElementById('f-clinic').value;
      page = 1; done = false; loading = false;
      Object.keys(grouped).forEach(k => delete grouped[k]);
      list.innerHTML = '';
      loadPage();
    }, 400);
  }

  document.getElementById('f-from').addEventListener('change', resetAndLoad);
  document.getElementById('f-to').addEventListener('change', resetAndLoad);
  document.getElementById('f-clinic').addEventListener('input', resetAndLoad);

  loadPage();
})();
