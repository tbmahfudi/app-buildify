(async () => {
  const token = sessionStorage.getItem('access_token');
  if (!token) { location.href = '/patient/login'; return; }

  const locale = localStorage.getItem('locale') || 'id-ID';
  await initI18n(locale);
  document.querySelectorAll('[data-i18n]').forEach(el => {
    el.textContent = t(locale, el.dataset.i18n);
  });

  const enc_id = location.pathname.split('/').pop();
  const content = document.getElementById('content');

  function esc(s){ return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;'); }
  function formatDate(d){ return d ? new Date(d).toLocaleDateString(locale,{day:'2-digit',month:'long',year:'numeric'}) : ''; }

  content.innerHTML = `<div style="padding:24px;text-align:center;color:var(--color-muted)">Memuat...</div>`;

  try {
    const enc = await window.apiFetch(`/api/v1/patients/me/encounters/${enc_id}`);

    const summaryHtml = enc.summary
      ? `<div class="detail-value">${esc(enc.summary)}</div>`
      : `<div class="detail-value" style="color:var(--color-muted);font-style:italic">${t(locale,'records.summary_not_shared')}</div>`;

    content.innerHTML = `
      <div class="detail-card">
        <div class="detail-section">
          <div class="detail-label">Klinik</div>
          <div class="detail-value">${esc(enc.clinic_name||'')}</div>
          <div style="font-size:13px;color:var(--color-muted)">${esc(enc.branch_name||'')}</div>
        </div>
        <div class="detail-section">
          <div class="detail-label">Tenaga Medis</div>
          <div class="detail-value">${esc(enc.provider_name||'')}</div>
        </div>
        <div class="detail-section">
          <div class="detail-label">Tanggal Kunjungan</div>
          <div class="detail-value">${formatDate(enc.date)}</div>
        </div>
        <div class="detail-section">
          <div class="detail-label">Jenis Kunjungan</div>
          <span class="badge">${esc(enc.encounter_type||'')}</span>
        </div>
        <div class="detail-section">
          <div class="detail-label">Ringkasan</div>
          ${summaryHtml}
        </div>
      </div>`;

    // Show review button only if completed and no review yet
    if (enc.status === 'completed' && !enc.has_review) {
      const btn = document.createElement('button');
      btn.className = 'btn-review';
      btn.style.marginTop = '12px';
      btn.textContent = t(locale,'review.title');
      btn.addEventListener('click', () => {
        location.href = `/patient/review-new?encounter_id=${enc_id}&branch_id=${enc.branch_id||''}`;
      });
      content.appendChild(btn);
    }
  } catch(e) {
    const is404 = e.status === 404 || (e.message && e.message.includes('404'));
    content.innerHTML = `<div class="error-state">
      ${is404 ? 'Kunjungan tidak ditemukan.' : ('Gagal memuat: ' + (e.message||''))}
    </div>`;
  }
})();
