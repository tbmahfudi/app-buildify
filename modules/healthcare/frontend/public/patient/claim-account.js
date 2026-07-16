/*
 * Patient account claim (ADR-HC-009 D7 / epic-18 Story 18.9.1).
 *
 * Reached when POST /patients/auth/token returns `must_set_password: true` — i.e. this
 * patient's record was migrated from the old phone+OTP-only world by the D7 backfill and
 * the account has no usable password yet. The OTP they just completed is the proof of
 * identity; this page turns that into a durable credential.
 *
 * The page needs a patient token, so it does NOT set window.__PATIENT_PUBLIC — _portal.js
 * bounces to login without one. That is the intended gate: claiming is only possible for
 * someone who has just proved control of the phone on record.
 *
 * Static / no build step. Real backticks only.
 */
(function () {
  'use strict';

  var PATIENT_BASE = '/portal/healthcare/patient/';
  var CLAIM_URL = '/api/v1/patients/auth/claim-account';

  var form = document.getElementById('claim-form');
  var msg = document.getElementById('claim-msg');
  var submit = document.getElementById('claim-submit');
  var emailEl = document.getElementById('claim-email');
  var pwEl = document.getElementById('claim-password');
  var confirmEl = document.getElementById('claim-confirm');

  var locale = window.localStorage.getItem('locale') ||
               window.localStorage.getItem('hc_locale') || 'id-ID';

  function tr(key, fallback) {
    try {
      if (typeof window.t === 'function') {
        var v = window.t(locale, key);
        if (v && v !== key) return v;
      }
    } catch (e) { /* i18n is best-effort; never block the claim on it */ }
    return fallback;
  }

  function show(kind, text, list) {
    msg.className = 'msg ' + kind;
    msg.textContent = text;
    if (list && list.length) {
      var ul = document.createElement('ul');
      list.forEach(function (item) {
        var li = document.createElement('li');
        li.textContent = item;      // textContent, not innerHTML: server strings are data
        ul.appendChild(li);
      });
      msg.appendChild(ul);
    }
  }

  function clearMsg() {
    msg.className = 'msg';
    msg.textContent = '';
  }

  // The backfill seeds a synthetic, non-deliverable address (…@patients.invalid). Showing
  // that back to a patient would be confusing and inviting them to "confirm" it would be
  // wrong — so prefill only a real one.
  (function prefillEmail() {
    var known = window.sessionStorage.getItem('hc_claim_email') || '';
    if (known && known.indexOf('@patients.invalid') === -1) emailEl.value = known;
  })();

  form.addEventListener('submit', async function (ev) {
    ev.preventDefault();
    clearMsg();

    var pw = pwEl.value || '';
    var confirm = confirmEl.value || '';
    var email = (emailEl.value || '').trim();

    if (!pw) {
      show('error', tr('claim.password_required', 'Please choose a password.'));
      return;
    }
    // Caught client-side purely to save a round trip; the server is the authority on the
    // password policy (it runs the same validator registration does).
    if (pw !== confirm) {
      show('error', tr('claim.mismatch', 'Those passwords do not match.'));
      return;
    }

    submit.disabled = true;
    try {
      var body = { password: pw };
      if (email) body.email = email;

      var res = await fetch(CLAIM_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer ' + (
            window.localStorage.getItem('hc_patient_token') ||
            window.sessionStorage.getItem('access_token') || ''
          )
        },
        body: JSON.stringify(body)
      });

      var data = null;
      try { data = await res.json(); } catch (e) { data = null; }

      if (res.ok) {
        window.sessionStorage.removeItem('hc_claim_email');
        show('ok', (data && data.message) ||
          tr('claim.done', 'Your password is set. You can now sign in with it.'));
        form.style.display = 'none';
        setTimeout(function () { window.location.href = PATIENT_BASE + 'portal.html'; }, 1500);
        return;
      }

      // 422 carries the policy failures; surface them verbatim so the patient can act,
      // rather than a vague "invalid password".
      var detail = data && data.detail;
      if (res.status === 422 && detail && detail.errors) {
        show('error', detail.message ||
          tr('claim.weak', 'Password does not meet requirements.'), detail.errors);
      } else if (res.status === 409) {
        show('error', (typeof detail === 'string' ? detail : null) ||
          tr('claim.conflict', 'This account has already been set up.'));
      } else if (res.status === 401) {
        window.location.href = '/portal/healthcare/#login';
      } else {
        show('error', (typeof detail === 'string' ? detail : null) ||
          tr('claim.failed', 'Could not save your password. Please try again.'));
      }
    } catch (e) {
      show('error', tr('claim.network', 'Network error. Please try again.'));
    } finally {
      submit.disabled = false;
    }
  });
})();
