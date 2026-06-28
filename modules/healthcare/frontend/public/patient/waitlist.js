/**
 * T-HC-041 — Waitlist UI
 * Route: /patient/waitlist
 */

import { initI18n, t, translateDOM } from '../i18n.js';
import '../locale-switcher.js';

const API_WAITLIST = '/api/v1/patients/me/waitlist';
const API_APPOINTMENTS = '/api/v1/patients/me/appointments';
const OFFER_DURATION_SECS = 15 * 60; // 15 minutes

// ── state ─────────────────────────────────────────────────────────────────────

let entries = [];
let offerEntry = null;
let countdownTimer = null;
let countdownRemaining = OFFER_DURATION_SECS;
let pendingLeaveId = null;

// ── status badge ──────────────────────────────────────────────────────────────

const STATUS_BADGE = {
  waiting:  { cls: 'hc-badge--waiting',  key: 'waitlist.status_waiting' },
  offered:  { cls: 'hc-badge--offered',  key: 'waitlist.status_offered' },
  expired:  { cls: 'hc-badge--expired',  key: 'waitlist.status_expired' },
  removed:  { cls: 'hc-badge--removed',  key: 'waitlist.status_removed' },
  accepted: { cls: 'hc-badge--accepted', key: 'waitlist.status_accepted' },
};

function badgeHTML(status) {
  const info = STATUS_BADGE[status] || { cls: '', key: status };
  return `<span class="hc-badge ${info.cls}">${t(info.key)}</span>`;
}

// ── offer card + countdown ────────────────────────────────────────────────────

function showOfferCard(entry) {
  offerEntry = entry;
  const section = document.getElementById('offer-section');
  section.style.display = 'block';

  document.getElementById('offer-clinic').textContent =
    entry.clinic_name || entry.clinic_slug || '—';

  const slot = entry.offered_slot || {};
  document.getElementById('offer-details').textContent =
    `${entry.branch_name || '—'} · ${slot.date || '—'} ${slot.start_time || ''} · ${t('booking.type_' + (entry.appointment_type || 'general'))}`;

  // Calculate remaining from offer_expires_at if available
  if (entry.offer_expires_at) {
    const expiresAt = new Date(entry.offer_expires_at).getTime();
    countdownRemaining = Math.max(0, Math.floor((expiresAt - Date.now()) / 1000));
  } else {
    countdownRemaining = OFFER_DURATION_SECS;
  }

  startCountdown();
}

function hideOfferCard() {
  document.getElementById('offer-section').style.display = 'none';
  stopCountdown();
  offerEntry = null;
}

function startCountdown() {
  stopCountdown();
  updateCountdownUI();
  countdownTimer = setInterval(() => {
    countdownRemaining = Math.max(0, countdownRemaining - 1);
    updateCountdownUI();
    if (countdownRemaining === 0) {
      stopCountdown();
      hideOfferCard();
      showAlert('warning', t('waitlist.status_expired'));
      loadWaitlist();
    }
  }, 1000);
}

function stopCountdown() {
  if (countdownTimer) { clearInterval(countdownTimer); countdownTimer = null; }
}

function updateCountdownUI() {
  const mins = Math.floor(countdownRemaining / 60);
  const secs = countdownRemaining % 60;
  document.getElementById('countdown-time').textContent =
    `${String(mins).padStart(2,'0')}:${String(secs).padStart(2,'0')}`;
  const pct = (countdownRemaining / OFFER_DURATION_SECS) * 100;
  document.getElementById('countdown-bar').style.width = `${pct}%`;
}

// ── render waitlist entries ───────────────────────────────────────────────────

function renderEntries() {
  const container = document.getElementById('waitlist-container');
  container.innerHTML = '';

  const nonOffered = entries.filter((e) => e.status !== 'offered');
  if (!nonOffered.length) {
    container.innerHTML = `<div class="hc-empty">${t('waitlist.empty')} — <a href="/public/clinics.html">${t('availability.title')}</a></div>`;
    return;
  }

  nonOffered.forEach((entry) => {
    const card = document.createElement('div');
    card.className = 'hc-wl-card';
    card.innerHTML = `
      <div class="hc-wl-card__info">
        <div class="hc-wl-card__clinic">${entry.clinic_name || entry.clinic_slug || '—'}</div>
        <div class="hc-wl-card__type">${entry.branch_name || '—'} · ${t('booking.type_' + (entry.appointment_type || 'general'))}</div>
      </div>
      ${badgeHTML(entry.status)}
    `;

    if (entry.status === 'waiting') {
      const btn = document.createElement('button');
      btn.className = 'hc-btn hc-btn--danger';
      btn.textContent = t('waitlist.leave');
      btn.addEventListener('click', () => openLeaveModal(entry.id));
      card.appendChild(btn);
    }

    container.appendChild(card);
  });
}

// ── leave modal ───────────────────────────────────────────────────────────────

function openLeaveModal(entryId) {
  pendingLeaveId = entryId;
  document.getElementById('leave-modal').classList.add('open');
}

function closeLeaveModal() {
  document.getElementById('leave-modal').classList.remove('open');
  pendingLeaveId = null;
}

async function confirmLeave() {
  if (!pendingLeaveId) return;
  const btn = document.getElementById('btn-confirm-leave');
  btn.disabled = true;

  try {
    const res = await window.apiFetch(`${API_WAITLIST}/${pendingLeaveId}`, { method: 'DELETE' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    entries = entries.filter((e) => e.id !== pendingLeaveId);
    renderEntries();
    closeLeaveModal();
  } catch (err) {
    showAlert('error', t('common.error') + ': ' + err.message);
    closeLeaveModal();
  } finally {
    btn.disabled = false;
  }
}

// ── accept / decline offer ────────────────────────────────────────────────────

async function acceptOffer() {
  if (!offerEntry) return;
  const btn = document.getElementById('btn-accept-offer');
  btn.disabled = true;

  try {
    const res = await window.apiFetch(API_APPOINTMENTS, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ offered_slot_id: offerEntry.offered_slot?.id || offerEntry.offered_slot_id }),
    });

    if (!res.ok) {
      const err = await res.json();
      showAlert('error', err.detail || t('common.error'));
      return;
    }

    const data = await res.json();
    const newId = data.id || data.appointment_id;
    location.href = `/patient/appointments/${newId}`;
  } catch (err) {
    showAlert('error', t('common.error') + ': ' + err.message);
    btn.disabled = false;
  }
}

async function declineOffer() {
  if (!offerEntry) return;
  const btn = document.getElementById('btn-decline-offer');
  btn.disabled = true;

  try {
    const res = await window.apiFetch(`${API_WAITLIST}/${offerEntry.id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    hideOfferCard();
    entries = entries.filter((e) => e.id !== offerEntry?.id);
    renderEntries();
  } catch (err) {
    showAlert('error', t('common.error') + ': ' + err.message);
  } finally {
    btn.disabled = false;
  }
}

// ── alerts ────────────────────────────────────────────────────────────────────

function showAlert(type, msg) {
  const container = document.getElementById('alert-container');
  const el = document.createElement('flex-alert');
  el.setAttribute('type', type);
  el.textContent = msg;
  container.innerHTML = '';
  container.appendChild(el);
}

// ── API ───────────────────────────────────────────────────────────────────────

async function loadWaitlist() {
  try {
    const res = await window.apiFetch(API_WAITLIST);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    entries = data.entries || data || [];

    const offered = entries.find((e) => e.status === 'offered');
    if (offered) {
      showOfferCard(offered);
    } else {
      hideOfferCard();
    }

    renderEntries();
  } catch (err) {
    console.error('waitlist: load failed', err);
    showAlert('error', t('common.error') + ': ' + err.message);
  }
}

// ── init ──────────────────────────────────────────────────────────────────────

async function init() {
  const _token = sessionStorage.getItem('access_token');
  if (!_token) { window.location.href = '/patient/login'; }

  await initI18n('id-ID');
  translateDOM(document);

  document.getElementById('btn-accept-offer').addEventListener('click', acceptOffer);
  document.getElementById('btn-decline-offer').addEventListener('click', declineOffer);
  document.getElementById('btn-cancel-leave').addEventListener('click', closeLeaveModal);
  document.getElementById('btn-confirm-leave').addEventListener('click', confirmLeave);
  document.getElementById('leave-modal').addEventListener('click', (e) => {
    if (e.target === e.currentTarget) closeLeaveModal();
  });

  await loadWaitlist();
}

document.addEventListener('DOMContentLoaded', init);
window.addEventListener('beforeunload', stopCountdown);
