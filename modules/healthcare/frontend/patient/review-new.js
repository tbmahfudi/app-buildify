(async () => {
  const token = sessionStorage.getItem('access_token');
  if (!token) { location.href = '/patient/login'; return; }

  const locale = localStorage.getItem('locale') || 'id-ID';
  await initI18n(locale);
  document.querySelectorAll('[data-i18n]').forEach(el => {
    el.textContent = t(locale, el.dataset.i18n);
  });

  const params = new URLSearchParams(location.search);
  const encounter_id = params.get('encounter_id');
  const branch_id    = params.get('branch_id');

  let rating = 0;
  const stars   = document.querySelectorAll('.star');
  const textarea = document.getElementById('review-text');
  const counter  = document.getElementById('char-count');
  const btnSub   = document.getElementById('btn-submit');
  const alertEl  = document.getElementById('alert-area');

  // Star interaction
  stars.forEach(s => {
    s.addEventListener('click', () => {
      rating = parseInt(s.dataset.val);
      stars.forEach(st => st.classList.toggle('filled', parseInt(st.dataset.val) <= rating));
    });
    s.addEventListener('mouseenter', () => {
      stars.forEach(st => st.classList.toggle('filled', parseInt(st.dataset.val) <= parseInt(s.dataset.val)));
    });
  });
  document.getElementById('stars').addEventListener('mouseleave', () => {
    stars.forEach(st => st.classList.toggle('filled', parseInt(st.dataset.val) <= rating));
  });

  // Char counter
  textarea.addEventListener('input', () => { counter.textContent = textarea.value.length; });

  function showAlert(type, msg) {
    alertEl.innerHTML = `<div class="flex-alert ${type}">${msg}</div>`;
  }

  btnSub.addEventListener('click', async () => {
    if (!rating) { showAlert('error', 'Pilih bintang terlebih dahulu'); return; }
    btnSub.disabled = true;
    try {
      await window.apiFetch('/api/v1/patients/me/reviews', {
        method: 'POST',
        body: JSON.stringify({ encounter_id, branch_id, rating, text: textarea.value })
      });
      showAlert('success', t(locale, 'review.success'));
      setTimeout(() => { location.href = `/patient/encounters/${encounter_id}`; }, 3000);
    } catch(e) {
      btnSub.disabled = false;
      const msg = e.status === 409
        ? t(locale, 'review.already_reviewed')
        : (e.message || 'Gagal mengirim ulasan');
      showAlert('error', msg);
    }
  });
})();
