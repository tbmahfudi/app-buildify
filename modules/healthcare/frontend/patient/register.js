/**
 * T-HC-026 — Patient registration wizard (5 steps, mobile-first)
 * < 50 KB target: vanilla JS only, no heavy libraries
 */

import { initI18n, t, translateDOM } from '../i18n.js';

const OTP_SECS = 60;

// ── state ─────────────────────────────────────────────────────────────────────

const state = {
  step:         1,
  phone:        '',
  otpToken:     '',
  accessToken:  '',
  fullName:     '',
};

let countdownTimer = null;

// ── navigation ─────────────────────────────────────────────────────────────────

function goStep(n) {
  document.querySelectorAll('.hc-step').forEach((el) => el.classList.remove('active'));
  document.getElementById(`step-${n}`).classList.add('active');

  const dots = document.querySelectorAll('.hc-dot');
  dots.forEach((d, i) => d.classList.toggle('active', i === n - 1));

  state.step = n;
}

// ── OTP boxes ─────────────────────────────────────────────────────────────────

function buildOtpBoxes() {
  const row = document.getElementById('otp-boxes');
  if (row.children.length) return;

  for (let i = 0; i < 6; i++) {
    const inp = document.createElement('input');
    inp.type = 'text';
    inp.maxLength = 1;
    inp.inputMode = 'numeric';
    inp.className = 'hc-otp-box';
    inp.setAttribute('aria-label', `OTP digit ${i + 1}`);

    inp.addEventListener('input', (e) => {
      e.target.value = e.target.value.replace(/\D/g, '');
      if (e.target.value && inp.nextElementSibling) inp.nextElementSibling.focus();
    });

    inp.addEventListener('keydown', (e) => {
      if (e.key === 'Backspace' && !e.target.value && inp.previousElementSibling) {
        inp.previousElementSibling.focus();
      }
    });

    inp.addEventListener('paste', (e) => {
      e.preventDefault();
      const digits = (e.clipboardData.getData('text') || '').replace(/\D/g, '').slice(0, 6);
      const boxes  = row.querySelectorAll('.hc-otp-box');
      digits.split('').forEach((d, idx) => { if (boxes[idx]) boxes[idx].value = d; });
      const next = boxes[Math.min(digits.length, 5)];
      if (next) next.focus();
    });

    row.appendChild(inp);
  }
}

function getOtpValue() {
  return Array.from(document.querySelectorAll('#otp-boxes .hc-otp-box'))
    .map((b) => b.value)
    .join('');
}

function startCountdown() {
  clearInterval(countdownTimer);
  let secs = OTP_SECS;
  const countdownEl = document.getElementById('otp-countdown');
  const resendBtn   = document.getElementById('btn-resend');
  resendBtn.disabled = true;

  countdownTimer = setInterval(() => {
    if (countdownEl) countdownEl.textContent = t('onboarding.otp.countdown', { s: secs });
    secs -= 1;
    if (secs < 0) {
      clearInterval(countdownTimer);
      if (countdownEl) countdownEl.textContent = '';
      resendBtn.disabled = false;
    }
  }, 1000);
}

// ── validation ─────────────────────────────────────────────────────────────────

function setFieldError(id, hasError) {
  const el = document.getElementById(id);
  if (el) el.classList.toggle('has-error', hasError);
}

function validatePhone() {
  const phone = document.getElementById('phone-input').value.trim();
  const ok = /^\+?[0-9]{8,15}$/.test(phone.replace(/\s/g, ''));
  setFieldError('field-phone', !ok);
  return ok;
}

function validateStep3() {
  const name = document.getElementById('full-name').value.trim();
  const dob  = document.getElementById('dob').value;
  let ok = true;
  setFieldError('field-full-name', !name); if (!name) ok = false;
  setFieldError('field-dob',       !dob);  if (!dob)  ok = false;
  return ok;
}

// ── API calls ─────────────────────────────────────────────────────────────────

async function sendOtp() {
  if (!validatePhone()) return;
  state.phone = document.getElementById('phone-input').value.trim();

  const btn = document.getElementById('btn-send-otp');
  btn.disabled = true;

  try {
    await window.apiFetch('POST', '/api/v1/patients/otp/send', { phone: state.phone });
    buildOtpBoxes();
    document.getElementById('otp-hint').textContent =
      t('patientReg.step2.hint', { phone: state.phone });
    startCountdown();
    goStep(2);
  } catch (err) {
    console.error('OTP send failed', err);
    btn.disabled = false;
  }
}

async function verifyOtp() {
  const otp = getOtpValue();
  if (otp.length !== 6) return;

  const btn = document.getElementById('btn-verify-otp');
  btn.disabled = true;

  try {
    const res = await window.apiFetch('POST', '/api/v1/patients/otp/verify', {
      phone: state.phone,
      otp,
    });
    state.otpToken = res.otp_token || '';
    goStep(3);
  } catch (err) {
    console.error('OTP verify failed', err);
    document.querySelectorAll('.hc-otp-box').forEach((b) => {
      b.style.borderColor = 'var(--color-danger)';
    });
    btn.disabled = false;
  }
}

async function register() {
  if (!validateStep3()) return;
  if (!document.getElementById('patient-consent').checked) {
    document.getElementById('consent-error').style.display = 'block';
    return;
  }

  const gender = document.querySelector('input[name="gender"]:checked');
  const body = {
    phone:         state.phone,
    otp_token:     state.otpToken,
    full_name:     document.getElementById('full-name').value.trim(),
    date_of_birth: document.getElementById('dob').value,
    gender:        gender ? gender.value : null,
    nik:           document.getElementById('nik').value.trim() || null,
    dpa_consent:   true,
  };

  const btn = document.getElementById('btn-register');
  btn.disabled = true;
  btn.textContent = t('common.submitting');

  try {
    const res = await window.apiFetch('POST', '/api/v1/patients/register', body);

    // Store access_token in sessionStorage only
    if (res.access_token) {
      sessionStorage.setItem('access_token', res.access_token);
    }

    state.fullName = body.full_name;
    document.getElementById('success-greeting').textContent =
      t('patientReg.step5.greeting', { name: state.fullName });
    goStep(5);
  } catch (err) {
    console.error('Registration failed', err);
    btn.disabled = false;
    btn.textContent = t('patientReg.step4.register');
  }
}

// ── init ──────────────────────────────────────────────────────────────────────

async function init() {
  await initI18n('id-ID');
  translateDOM(document);

  // Step 1
  document.getElementById('btn-send-otp').addEventListener('click', sendOtp);

  // Step 2
  document.getElementById('btn-verify-otp').addEventListener('click', verifyOtp);
  document.getElementById('btn-resend').addEventListener('click', async () => {
    await window.apiFetch('POST', '/api/v1/patients/otp/send', { phone: state.phone }).catch(() => {});
    startCountdown();
  });

  // Step 3
  document.getElementById('btn-next-3').addEventListener('click', () => {
    if (!validateStep3()) return;
    goStep(4);
  });

  // Step 4
  document.getElementById('patient-consent').addEventListener('change', () => {
    document.getElementById('consent-error').style.display = 'none';
  });
  document.getElementById('btn-register').addEventListener('click', register);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
