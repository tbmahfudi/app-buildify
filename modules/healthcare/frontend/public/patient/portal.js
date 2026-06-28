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
