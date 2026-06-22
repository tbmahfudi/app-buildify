/**
 * T-HC-024 — Clinic onboarding wizard
 * 4-step wizard: owner info + OTP | clinic details | DPA | success
 */

import { initI18n, t, translateDOM } from '../i18n.js';
import '../locale-switcher.js';

const SESSION_KEY = 'hc_onboarding_state';
const OTP_COUNTDOWN_SECS = 60;

// ── state ─────────────────────────────────────────────────────────────────────

let currentStep = 1;
let otpSent = false;
let countdownTimer = null;

function loadState() {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY);
    if (raw) return JSON.parse(raw);
  } catch (_) {}
  return {};
}

function saveState(patch) {
  const state = { ...loadState(), ...patch };
  sessionStorage.setItem(SESSION_KEY, JSON.stringify(state));
}

// ── navigation ─────────────────────────────────────────────────────────────────

function goToStep(n) {
  document.querySelectorAll('.hc-step').forEach((el) => el.classList.remove('active'));
  document.getElementById(`step-${n}`).classList.add('active');

  document.querySelectorAll('.hc-stepper__item').forEach((el, i) => {
    el.classList.remove('active', 'done');
    if (i + 1 === n)    el.classList.add('active');
    if (i + 1 < n)      el.classList.add('done');
  });

  currentStep = n;
  saveState({ step: n });
}

// ── validation helpers ────────────────────────────────────────────────────────

function setFieldError(fieldId, hasError) {
  const el = document.getElementById(fieldId);
  if (!el) return;
  el.classList.toggle('has-error', hasError);
}

function validateStep1() {
  const name  = document.getElementById('owner-name').value.trim();
  const email = document.getElementById('email').value.trim();
  const phone = document.getElementById('phone').value.trim();

  let ok = true;

  setFieldError('field-owner-name', !name);
  if (!name) ok = false;

  const emailOk = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  setFieldError('field-email', !emailOk);
  if (!emailOk) ok = false;

  const phoneOk = /^\+?[0-9]{8,15}$/.test(phone.replace(/\s/g, ''));
  setFieldError('field-phone', !phoneOk);
  if (!phoneOk) ok = false;

  return ok;
}

function getOtpValue(rowId) {
  return Array.from(document.querySelectorAll(`#${rowId} .hc-otp-box`))
    .map((b) => b.value)
    .join('');
}

function validateOtp(rowId) {
  return getOtpValue(rowId).length === 6;
}

function validateStep2() {
  const clinicName = document.getElementById('clinic-name').value.trim();
  const specialty  = document.getElementById('specialty').value;
  const city       = document.getElementById('city').value.trim();

  let ok = true;

  setFieldError('field-clinic-name', !clinicName);
  if (!clinicName) ok = false;

  setFieldError('field-specialty', !specialty);
  if (!specialty) ok = false;

  setFieldError('field-city', !city);
  if (!city) ok = false;

  return ok;
}

function validateStep3() {
  const checked = document.getElementById('dpa-consent').checked;
  document.getElementById('field-consent-error').style.display = checked ? 'none' : 'block';
  return checked;
}

// ── OTP ────────────────────────────────────────────────────────────────────────

function buildOtpBoxes(rowId, resendBtnId, countdownId) {
  const row = document.getElementById(rowId);
  if (!row || row.children.length) return; // already built

  for (let i = 0; i < 6; i++) {
    const inp = document.createElement('input');
    inp.type = 'text';
    inp.maxLength = 1;
    inp.inputMode = 'numeric';
    inp.pattern = '[0-9]';
    inp.className = 'hc-otp-box';
    inp.setAttribute('aria-label', `OTP digit ${i + 1}`);

    inp.addEventListener('input', (e) => {
      e.target.value = e.target.value.replace(/\D/g, '');
      if (e.target.value && inp.nextElementSibling) {
        inp.nextElementSibling.focus();
      }
    });

    inp.addEventListener('keydown', (e) => {
      if (e.key === 'Backspace' && !e.target.value && inp.previousElementSibling) {
        inp.previousElementSibling.focus();
      }
    });

    inp.addEventListener('paste', (e) => {
      e.preventDefault();
      const digits = (e.clipboardData.getData('text') || '').replace(/\D/g, '').slice(0, 6);
      const boxes = row.querySelectorAll('.hc-otp-box');
      digits.split('').forEach((d, idx) => {
        if (boxes[idx]) boxes[idx].value = d;
      });
      const next = boxes[Math.min(digits.length, 5)];
      if (next) next.focus();
    });

    row.appendChild(inp);
  }
}

function startCountdown(countdownId, resendBtnId) {
  clearInterval(countdownTimer);
  let seconds = OTP_COUNTDOWN_SECS;
  const countdownEl = document.getElementById(countdownId);
  const resendBtn   = document.getElementById(resendBtnId);

  if (resendBtn) resendBtn.disabled = true;

  countdownTimer = setInterval(() => {
    if (countdownEl) countdownEl.textContent = t('onboarding.otp.countdown', { s: seconds });
    seconds -= 1;
    if (seconds < 0) {
      clearInterval(countdownTimer);
      if (countdownEl) countdownEl.textContent = '';
      if (resendBtn) resendBtn.disabled = false;
    }
  }, 1000);
}

async function sendOtp() {
  const phone = document.getElementById('phone').value.trim();
  if (!/^\+?[0-9]{8,15}$/.test(phone.replace(/\s/g, ''))) return;

  const btn = document.getElementById('btn-send-otp');
  btn.disabled = true;

  try {
    await window.apiFetch('POST', '/api/v1/clinics/otp/send', { phone });
    otpSent = true;
    document.getElementById('otp-section').style.display = 'block';
    buildOtpBoxes('otp-boxes-1', 'btn-resend-1', 'otp-countdown-1');
    startCountdown('otp-countdown-1', 'btn-resend-1');
    btn.textContent = t('onboarding.otp.sent');
  } catch (err) {
    btn.disabled = false;
    console.error('OTP send failed', err);
  }
}

// ── submit ────────────────────────────────────────────────────────────────────

async function submitRegistration() {
  const body = {
    owner_name:  document.getElementById('owner-name').value.trim(),
    email:       document.getElementById('email').value.trim(),
    phone:       document.getElementById('phone').value.trim(),
    otp:         getOtpValue('otp-boxes-1'),
    clinic_name: document.getElementById('clinic-name').value.trim(),
    specialty:   document.getElementById('specialty').value,
    city:        document.getElementById('city').value.trim(),
    website:     document.getElementById('website').value.trim() || null,
    dpa_consent: true,
  };

  const btn = document.getElementById('btn-submit');
  btn.disabled = true;
  btn.textContent = t('common.submitting');

  try {
    const res = await window.apiFetch('POST', '/api/v1/clinics/register', body);
    saveState({ clinicName: res.clinic_name || body.clinic_name });
    document.getElementById('success-clinic-name').textContent = res.clinic_name || body.clinic_name;
    goToStep(4);
  } catch (err) {
    btn.disabled = false;
    btn.textContent = t('onboarding.step3.submit');
    console.error('Registration failed', err);
  }
}

// ── init ──────────────────────────────────────────────────────────────────────

async function init() {
  await initI18n();
  translateDOM(document);

  // Restore step from session (only restore non-success steps)
  const saved = loadState();
  const resumeStep = saved.step && saved.step < 4 ? saved.step : 1;
  goToStep(resumeStep);

  // Step 1 controls
  document.getElementById('btn-send-otp').addEventListener('click', sendOtp);

  document.getElementById('btn-resend-1').addEventListener('click', async () => {
    await sendOtp();
  });

  document.getElementById('btn-next-1').addEventListener('click', () => {
    if (!validateStep1()) return;
    if (!otpSent) { sendOtp(); return; }
    if (!validateOtp('otp-boxes-1')) {
      // show otp error by highlighting boxes
      document.querySelectorAll('.hc-otp-box').forEach((b) => {
        b.style.borderColor = 'var(--color-danger)';
      });
      return;
    }
    saveState({
      ownerName: document.getElementById('owner-name').value.trim(),
      email:     document.getElementById('email').value.trim(),
      phone:     document.getElementById('phone').value.trim(),
    });
    goToStep(2);
  });

  // Step 2 controls
  document.getElementById('btn-back-2').addEventListener('click', () => goToStep(1));
  document.getElementById('btn-next-2').addEventListener('click', () => {
    if (!validateStep2()) return;
    saveState({
      clinicName: document.getElementById('clinic-name').value.trim(),
      specialty:  document.getElementById('specialty').value,
      city:       document.getElementById('city').value.trim(),
    });
    goToStep(3);
  });

  // Step 3 controls
  document.getElementById('btn-back-3').addEventListener('click', () => goToStep(2));
  document.getElementById('btn-submit').addEventListener('click', () => {
    if (!validateStep3()) return;
    submitRegistration();
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
