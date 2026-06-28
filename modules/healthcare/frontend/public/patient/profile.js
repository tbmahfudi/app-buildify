(async () => {
  const token = sessionStorage.getItem('access_token');
  if (!token) { location.href = '/patient/login'; return; }

  const locale = localStorage.getItem('locale') || 'id-ID';
  await initI18n(locale);
  document.querySelectorAll('[data-i18n]').forEach(el => {
    el.textContent = t(locale, el.dataset.i18n);
  });

  let profile = {};
  let editMode = false;

  const fg       = document.getElementById('field-group');
  const btnEdit  = document.getElementById('btn-edit');
  const btnSave  = document.getElementById('btn-save');
  const alertEl  = document.getElementById('alert-area');

  function esc(s){ return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;'); }

  function maskPhone(p){
    return p ? p.replace(/(\+?\d{2,3})(\d+)(\d{3})/, '$1****$3') : '';
  }

  function renderDisplay() {
    fg.innerHTML = `
      <div class="field-row">
        <span class="field-label">${t(locale,'profile.name')}</span>
        <span class="field-value muted">${esc(profile.name)}</span>
      </div>
      <div class="field-row">
        <span class="field-label">${t(locale,'profile.dob')}</span>
        <span class="field-value muted">${esc(profile.dob)}</span>
      </div>
      <div class="field-row">
        <span class="field-label">${t(locale,'profile.phone')}</span>
        <span class="field-value muted">${esc(maskPhone(profile.phone))}</span>
      </div>
      <div class="field-row">
        <span class="field-label">${t(locale,'profile.email')}</span>
        <span class="field-value">${esc(profile.email)}</span>
      </div>
      <div class="field-row">
        <span class="field-label">${t(locale,'profile.address')}</span>
        <span class="field-value">${esc(profile.address)}</span>
      </div>
      <div class="field-row">
        <span class="field-label">${t(locale,'profile.locale')}</span>
        <span class="field-value">${esc(profile.locale)}</span>
      </div>`;
  }

  function renderEdit() {
    fg.innerHTML = `
      <div class="field-row">
        <span class="field-label">${t(locale,'profile.name')}</span>
        <span class="field-value muted">${esc(profile.name)}</span>
      </div>
      <div class="field-row">
        <span class="field-label">${t(locale,'profile.dob')}</span>
        <span class="field-value muted">${esc(profile.dob)}</span>
      </div>
      <div class="field-row">
        <span class="field-label">${t(locale,'profile.phone')}</span>
        <span class="field-value muted">${esc(maskPhone(profile.phone))}</span>
      </div>
      <div class="field-row">
        <label class="field-label" for="inp-email">${t(locale,'profile.email')}</label>
        <input id="inp-email" type="email" value="${esc(profile.email||'')}"/>
      </div>
      <div class="field-row">
        <label class="field-label" for="inp-address">${t(locale,'profile.address')}</label>
        <input id="inp-address" type="text" value="${esc(profile.address||'')}"/>
      </div>
      <div class="field-row">
        <label class="field-label" for="sel-locale">${t(locale,'profile.locale')}</label>
        <select id="sel-locale">
          <option value="id-ID" ${profile.locale==='id-ID'?'selected':''}>Bahasa Indonesia</option>
          <option value="en-US" ${profile.locale==='en-US'?'selected':''}>English</option>
        </select>
      </div>`;
  }

  function showAlert(type, msg) {
    alertEl.innerHTML = `<div class="flex-alert ${type}">${msg}</div>`;
    if (type === 'success') setTimeout(() => alertEl.innerHTML='', 3000);
  }

  try {
    profile = await window.apiFetch('/api/v1/patients/me/profile');
    renderDisplay();
  } catch(e) {
    fg.innerHTML = '<div style="padding:16px;color:var(--color-error)">Gagal memuat profil</div>';
  }

  btnEdit.addEventListener('click', () => {
    editMode = !editMode;
    if (editMode) { renderEdit(); btnSave.style.display='block'; btnEdit.textContent=t(locale,'records.empty').includes('?')?'Batal':'Batal'; btnEdit.textContent='Batal'; }
    else { renderDisplay(); btnSave.style.display='none'; btnEdit.textContent=t(locale,'profile.edit'); }
  });

  btnSave.addEventListener('click', async () => {
    const payload = {
      email:   document.getElementById('inp-email')?.value || profile.email,
      address: document.getElementById('inp-address')?.value || profile.address,
      locale:  document.getElementById('sel-locale')?.value || profile.locale,
    };
    try {
      profile = await window.apiFetch('/api/v1/patients/me/profile', { method:'PUT', body: JSON.stringify(payload) });
      editMode = false;
      renderDisplay();
      btnSave.style.display='none';
      btnEdit.textContent = t(locale,'profile.edit');
      showAlert('success', t(locale,'profile.saved'));
      // sync locale if changed
      if (payload.locale !== locale) {
        localStorage.setItem('locale', payload.locale);
      }
    } catch(e) {
      showAlert('error', e.message || 'Gagal menyimpan');
    }
  });
})();
