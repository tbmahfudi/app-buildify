(async () => {
  const token = sessionStorage.getItem('access_token');
  if (!token) { location.href = '/patient/login'; return; }

  const locale = localStorage.getItem('locale') || 'id-ID';
  await initI18n(locale);
  document.querySelectorAll('[data-i18n]').forEach(el => {
    el.textContent = t(locale, el.dataset.i18n);
  });

  // Waitlist banner
  if (typeof checkWaitlistOffers === 'function') {
    checkWaitlistOffers(document.getElementById('waitlist-banner-area'));
  }

  // Profile card
  try {
    const p = await window.apiFetch('/api/v1/patients/me/profile');
    const initials = (p.name || '?').split(' ').map(w => w[0]).join('').slice(0,2).toUpperCase();
    const maskedPhone = p.phone ? p.phone.replace(/(\d{3})\d+(\d{3})/, '$1****$2') : '';
    document.getElementById('profile-card').innerHTML = `
      <div class="avatar">${initials}</div>
      <div>
        <div class="name">${escHtml(p.name || '')}</div>
        <div class="phone">${escHtml(maskedPhone)}</div>
      </div>`;
  } catch(e) {
    document.getElementById('profile-card').innerHTML =
      '<div style="color:var(--color-error);font-size:13px">Gagal memuat profil</div>';
  }

  // Household bar — shows the active patient + link to manage family; highlights
  // when acting on behalf of a dependent.
  try {
    const h = await window.apiFetch('/api/v1/patients/me/household');
    const members = h.members || [];
    const active = members.find(m => m.is_active);
    const bar = document.getElementById('household-bar');
    if (bar && (members.length > 1 || active)) {
      const onBehalf = active && active.relationship && active.relationship !== 'self';
      const left = onBehalf
        ? `<div><div style="font-size:11px;color:var(--color-warning)">Bertindak atas nama</div>
             <div style="font-weight:600;font-size:14px">${escHtml(active.full_name || '')}</div></div>`
        : `<div><div style="font-size:11px;color:var(--color-muted)">Keluarga</div>
             <div style="font-weight:600;font-size:14px">${members.length} anggota</div></div>`;
      bar.innerHTML = left + `<span style="color:var(--color-primary);font-size:13px;font-weight:600">Kelola →</span>`;
      bar.style.display = 'flex';
    }
  } catch (e) { /* non-fatal */ }

  // Summary grid
  const WIDGETS = [
    { key: 'portal.total_visits',          field: 'total_visits',          href: '/patient/records' },
    { key: 'portal.upcoming_appointments', field: 'upcoming_appointments', href: '/patient/appointments' },
    { key: 'portal.active_clinics',        field: 'active_clinics',        href: '/patient/records' },
    { key: 'portal.last_visit',            field: 'last_visit',            href: '/patient/records' },
  ];

  try {
    const s = await window.apiFetch('/api/v1/patients/me/summary');
    document.getElementById('summary-grid').innerHTML = WIDGETS.map(w => `
      <a class="summary-card" href="${w.href}">
        <div class="label">${t(locale, w.key)}</div>
        <div class="value">${escHtml(String(s[w.field] ?? '—'))}</div>
      </a>`).join('');
  } catch(e) {
    document.getElementById('summary-grid').innerHTML =
      '<div style="grid-column:1/-1;color:var(--color-error);font-size:13px;padding:8px">Gagal memuat ringkasan</div>';
  }

  function escHtml(s) {
    return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }
})();
