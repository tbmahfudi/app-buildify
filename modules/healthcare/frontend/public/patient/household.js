(async () => {
  const token = sessionStorage.getItem('access_token') || localStorage.getItem('hc_patient_token');
  if (!token) { location.href = '/patient/login'; return; }

  const locale = localStorage.getItem('locale') || 'id-ID';
  try { if (typeof initI18n === 'function') await initI18n(locale); } catch (e) {}
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const v = (typeof t === 'function') ? t(locale, el.dataset.i18n) : '';
    if (v) el.textContent = v;
  });

  const REL_LABEL = { self: 'Diri Sendiri', spouse: 'Pasangan', child: 'Anak', parent: 'Orang Tua', other: 'Lainnya' };
  const REL_BASIS = { child: 'parental_guardian', spouse: 'spousal', parent: 'delegated_adult', other: 'delegated_adult' };

  function escHtml(s) {
    return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
  function alertMsg(kind, msg) {
    document.getElementById('alert-area').innerHTML =
      `<div class="flex-alert ${kind}">${escHtml(msg)}</div>`;
    if (kind !== 'error') setTimeout(() => { document.getElementById('alert-area').innerHTML = ''; }, 4000);
  }

  async function loadHousehold() {
    const box = document.getElementById('members');
    try {
      const h = await window.apiFetch('/api/v1/patients/me/household');
      const members = h.members || [];
      box.innerHTML = members.map(m => {
        const initials = (m.full_name || '?').split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();
        const rel = REL_LABEL[m.relationship] || m.relationship;
        const activeChip = m.is_active ? '<span class="chip">Aktif</span>' : '';
        const switchBtn = m.is_active ? ''
          : `<button class="btn btn-ghost" data-switch="${escHtml(m.patient_id)}">Beralih</button>`;
        return `<div class="member ${m.is_active ? 'active' : ''}">
            <div class="avatar">${escHtml(initials)}</div>
            <div style="flex:1">
              <div class="name">${escHtml(m.full_name)}${activeChip}</div>
              <div class="rel">${escHtml(rel)}</div>
            </div>${switchBtn}
          </div>`;
      }).join('') || '<div class="muted" style="padding:16px">Belum ada anggota keluarga.</div>';

      box.querySelectorAll('[data-switch]').forEach(b => {
        b.addEventListener('click', () => switchTo(b.getAttribute('data-switch'), b));
      });
    } catch (e) {
      box.innerHTML = `<div class="flex-alert error">Gagal memuat keluarga: ${escHtml(e.message)}</div>`;
    }
  }

  async function switchTo(patientId, btn) {
    if (btn) { btn.disabled = true; btn.textContent = '…'; }
    try {
      const r = await window.apiFetch('/api/v1/patients/auth/switch', {
        method: 'POST', body: JSON.stringify({ patient_id: patientId }),
      });
      // Adopt the new active-patient token everywhere apiFetch/pages read it.
      localStorage.setItem('hc_patient_token', r.access_token);
      sessionStorage.setItem('access_token', r.access_token);
      location.href = '/patient/portal';
    } catch (e) {
      alertMsg('error', 'Gagal beralih: ' + e.message);
      if (btn) { btn.disabled = false; btn.textContent = 'Beralih'; }
    }
  }

  // Collapsible sections
  document.querySelectorAll('[data-toggle]').forEach(t => {
    t.addEventListener('click', () => {
      document.getElementById(t.getAttribute('data-toggle')).classList.toggle('open');
    });
  });

  // Add-dependent form
  document.getElementById('add-form').addEventListener('submit', async (ev) => {
    ev.preventDefault();
    const f = ev.target;
    if (!f.consent.checked) { alertMsg('error', 'Persetujuan diperlukan.'); return; }
    const relationship = f.relationship.value;
    const btn = f.querySelector('button[type=submit]');
    btn.disabled = true;
    try {
      await window.apiFetch('/api/v1/patients/me/household/dependents', {
        method: 'POST',
        body: JSON.stringify({
          full_name: f.full_name.value.trim(),
          date_of_birth: f.date_of_birth.value,
          phone: f.phone.value.trim(),
          gender: f.gender.value,
          relationship: relationship,
          basis: REL_BASIS[relationship] || 'delegated_adult',
          consent_version: 'v1',
          consent_accepted: true,
        }),
      });
      f.reset();
      f.classList.remove('open');
      alertMsg('success', 'Anggota keluarga berhasil didaftarkan.');
      loadHousehold();
    } catch (e) {
      alertMsg('error', 'Gagal mendaftarkan: ' + e.message);
    } finally {
      btn.disabled = false;
    }
  });

  // Link-existing form
  document.getElementById('link-form').addEventListener('submit', async (ev) => {
    ev.preventDefault();
    const f = ev.target;
    const relationship = f.relationship.value;
    const btn = f.querySelector('button[type=submit]');
    btn.disabled = true;
    try {
      const r = await window.apiFetch('/api/v1/patients/me/household/link', {
        method: 'POST',
        body: JSON.stringify({
          patient_id: f.patient_id.value.trim(),
          branch_id: f.branch_id.value.trim(),
          relationship: relationship,
          basis: REL_BASIS[relationship] || 'delegated_adult',
        }),
      });
      f.reset();
      f.classList.remove('open');
      alertMsg('info', (r && r.message) || 'Permintaan tautan dikirim untuk persetujuan klinik.');
    } catch (e) {
      alertMsg('error', 'Gagal mengirim permintaan: ' + e.message);
    } finally {
      btn.disabled = false;
    }
  });

  loadHousehold();
})();
