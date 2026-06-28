/**
 * T-HC-039 — Patient Reschedule and Cancel UI
 * Route: /patient/appointments/:appointment_id
 */

import { initI18n, t, translateDOM } from '../i18n.js';
import '../locale-switcher.js';

const pathParts = location.pathname.split('/').filter(Boolean);
const APPOINTMENT_ID = pathParts[pathParts.length - 1] || '';
const API_APPT = `/api/v1/patients/me/appointments/${APPOINTMENT_ID}`;

function formatDate(dateStr, locale) {
  return new Date(dateStr).toLocaleDateString(locale === 'id-ID' ? 'id-ID' : 'en-US', {
    year: 'numeric', month: 'long', day: 'numeric'
  });
}

// ── state ─────────────────────────────────────────────────────────────────────

let apptData = null;
const rsState = {
  year: new Date().getFullYear(),
  month: new Date().getMonth(),
  date: null,
  slot: null,
};

// ── status badge ──────────────────────────────────────────────────────────────

const STATUS_MAP = {
  confirmed:   { cls: 'hc-badge--confirmed',   key: 'appointment.status_confirmed' },
  checked_in:  { cls: 'hc-badge--checked_in',  key: 'appointment.status_checked_in' },
  in_progress: { cls: 'hc-badge--in_progress', key: 'appointment.status_in_progress' },
  completed:   { cls: 'hc-badge--completed',   key: 'appointment.status_completed' },
  cancelled:   { cls: 'hc-badge--cancelled',   key: 'appointment.status_cancelled' },
  no_show:     { cls: 'hc-badge--no_show',     key: 'appointment.status_no_show' },
};

function badgeHTML(status) {
  const info = STATUS_MAP[status] || { cls: '', key: status };
  return `<span class="hc-badge ${info.cls}">${t(info.key)}</span>`;
}

// ── render detail card ────────────────────────────────────────────────────────

function renderCard(data) {
  const card = document.getElementById('detail-card');
  card.innerHTML = `
    <div class="hc-card__row"><span class="hc-card__label">Klinik</span><span class="hc-card__value">${data.clinic_name || '—'}</span></div>
    <div class="hc-card__row"><span class="hc-card__label">Cabang</span><span class="hc-card__value">${data.branch_name || '—'}</span></div>
    <div class="hc-card__row"><span class="hc-card__label">Tanggal</span><span class="hc-card__value">${data.date || '—'}</span></div>
    <div class="hc-card__row"><span class="hc-card__label">Waktu</span><span class="hc-card__value">${data.start_time || data.time || '—'}</span></div>
    <div class="hc-card__row"><span class="hc-card__label">Jenis</span><span class="hc-card__value">${data.appointment_type || '—'}</span></div>
    <div class="hc-card__row"><span class="hc-card__label">Status</span><span class="hc-card__value">${badgeHTML(data.status)}</span></div>
  `;

  const actionable = !['cancelled', 'completed', 'no_show'].includes(data.status);
  document.getElementById('action-buttons').style.display = actionable ? 'flex' : 'none';
  document.getElementById('cancelled-notice').style.display = data.status === 'cancelled' ? 'block' : 'none';
}

// ── alerts ────────────────────────────────────────────────────────────────────

function showAlert(type, msg) {
  const el = document.createElement('flex-alert');
  el.setAttribute('type', type);
  el.textContent = msg;
  const container = document.getElementById('alert-container');
  container.innerHTML = '';
  container.appendChild(el);
}

function clearAlert() {
  document.getElementById('alert-container').innerHTML = '';
}

// ── load appointment ──────────────────────────────────────────────────────────

async function loadAppointment() {
  try {
    const res = await window.apiFetch(API_APPT);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    apptData = await res.json();
    renderCard(apptData);
  } catch (err) {
    showAlert('error', t('common.error') + ': ' + err.message);
  }
}

// ── Reschedule ────────────────────────────────────────────────────────────────

function openRescheduleModal() {
  rsState.year = new Date().getFullYear();
  rsState.month = new Date().getMonth();
  rsState.date = null;
  rsState.slot = null;
  document.getElementById('rs-slot-grid').innerHTML = '';
  document.getElementById('btn-confirm-rs').disabled = true;
  renderRsCal();
  document.getElementById('reschedule-modal').classList.add('open');
}

function closeRescheduleModal() {
  document.getElementById('reschedule-modal').classList.remove('open');
}

function toDateStr(d) {
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
}

function renderRsCal() {
  const { year, month } = rsState;
  document.getElementById('rs-cal-month').textContent = new Date(rsState.year, rsState.month, 1).toLocaleDateString(localStorage.getItem('hc_locale') === 'id-ID' ? 'id-ID' : 'en-US', { year: 'numeric', month: 'long' });
  const grid = document.getElementById('rs-cal-days');
  grid.innerHTML = '';

  const today = new Date(); today.setHours(0,0,0,0);
  const firstDay = new Date(year, month, 1).getDay();
  const startOffset = (firstDay + 6) % 7;
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const daysInPrev = new Date(year, month, 0).getDate();

  for (let i = startOffset - 1; i >= 0; i--) {
    const d = document.createElement('div');
    d.className = 'hc-cal-mini__day other';
    d.textContent = daysInPrev - i;
    grid.appendChild(d);
  }

  for (let day = 1; day <= daysInMonth; day++) {
    const date = new Date(year, month, day);
    const dateStr = toDateStr(date);
    const isPast = date < today;
    const d = document.createElement('div');
    d.className = 'hc-cal-mini__day' + (isPast ? ' disabled' : '');
    if (dateStr === rsState.date) d.classList.add('selected');
    d.textContent = day;
    if (!isPast) {
      d.addEventListener('click', async () => {
        rsState.date = dateStr;
        rsState.slot = null;
        document.getElementById('btn-confirm-rs').disabled = true;
        document.querySelectorAll('.hc-cal-mini__day').forEach((el) => el.classList.remove('selected'));
        d.classList.add('selected');
        await loadRsSlots();
      });
    }
    grid.appendChild(d);
  }

  const totalCells = startOffset + daysInMonth;
  const remainder = totalCells % 7 === 0 ? 0 : 7 - (totalCells % 7);
  for (let i = 1; i <= remainder; i++) {
    const d = document.createElement('div');
    d.className = 'hc-cal-mini__day other';
    d.textContent = i;
    grid.appendChild(d);
  }
}

async function loadRsSlots() {
  if (!rsState.date || !apptData) return;
  const loading = document.getElementById('rs-slot-loading');
  const grid = document.getElementById('rs-slot-grid');
  grid.innerHTML = '';
  loading.style.display = 'block';

  try {
    const providerId = apptData.provider_id || '';
    const url = `/api/v1/clinics/${apptData.clinic_slug || ''}/branches/${apptData.branch_id || ''}/slots?date=${rsState.date}&appointment_type=${apptData.appointment_type || ''}&provider_id=${providerId}`;
    const res = await window.apiFetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const slots = data.slots || data || [];

    loading.style.display = 'none';
    slots.forEach((slot) => {
      const card = document.createElement('div');
      card.className = 'hc-slot-card';
      card.innerHTML = `<div style="font-weight:700;font-size:var(--font-sm);">${slot.start_time || slot.time}</div>`;
      card.addEventListener('click', () => {
        document.querySelectorAll('.hc-slot-card').forEach((c) => c.classList.remove('selected'));
        card.classList.add('selected');
        rsState.slot = slot;
        document.getElementById('btn-confirm-rs').disabled = false;
      });
      grid.appendChild(card);
    });
  } catch (err) {
    loading.style.display = 'none';
    console.error('reschedule: slots failed', err);
  }
}

async function confirmReschedule() {
  if (!rsState.slot) return;
  const btn = document.getElementById('btn-confirm-rs');
  btn.disabled = true;

  try {
    const res = await window.apiFetch(API_APPT, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ new_slot_id: rsState.slot.id }),
    });

    if (!res.ok) {
      const err = await res.json();
      showAlert('error', err.detail || t('common.error'));
      return;
    }

    closeRescheduleModal();
    clearAlert();
    await loadAppointment();
  } catch (err) {
    showAlert('error', t('common.error') + ': ' + err.message);
  } finally {
    btn.disabled = false;
  }
}

// ── Cancel ────────────────────────────────────────────────────────────────────

function openCancelModal() {
  const policyEl = document.getElementById('cancel-policy');
  policyEl.textContent = apptData?.cancellation_policy || '';
  document.getElementById('cancel-modal').classList.add('open');
}

function closeCancelModal() {
  document.getElementById('cancel-modal').classList.remove('open');
}

async function confirmCancel() {
  const btn = document.getElementById('btn-confirm-cancel');
  btn.disabled = true;

  try {
    const res = await window.apiFetch(API_APPT, { method: 'DELETE' });

    if (res.status === 422) {
      const err = await res.json();
      closeCancelModal();
      showAlert('error', err.detail || t('appointment.cancel_policy_error'));
      return;
    }

    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    closeCancelModal();
    // Optimistic UI: update status badge immediately
    if (apptData) {
      apptData.status = 'cancelled';
      renderCard(apptData);
    }
    document.getElementById('cancelled-notice').style.display = 'block';
    document.getElementById('action-buttons').style.display = 'none';
    showAlert('info', t('appointment.cancelled'));
  } catch (err) {
    closeCancelModal();
    showAlert('error', t('common.error') + ': ' + err.message);
  } finally {
    btn.disabled = false;
  }
}

// ── init ──────────────────────────────────────────────────────────────────────

async function init() {
  const _token = sessionStorage.getItem('access_token');
  if (!_token) { window.location.href = '/patient/login'; }

  await initI18n('id-ID');
  translateDOM(document);

  await loadAppointment();

  document.getElementById('btn-reschedule').addEventListener('click', openRescheduleModal);
  document.getElementById('btn-cancel').addEventListener('click', openCancelModal);

  document.getElementById('btn-cancel-rs').addEventListener('click', closeRescheduleModal);
  document.getElementById('reschedule-modal').addEventListener('click', (e) => {
    if (e.target === e.currentTarget) closeRescheduleModal();
  });
  document.getElementById('btn-confirm-rs').addEventListener('click', confirmReschedule);

  document.getElementById('rs-cal-prev').addEventListener('click', () => {
    rsState.month--;
    if (rsState.month < 0) { rsState.month = 11; rsState.year--; }
    renderRsCal();
  });
  document.getElementById('rs-cal-next').addEventListener('click', () => {
    rsState.month++;
    if (rsState.month > 11) { rsState.month = 0; rsState.year++; }
    renderRsCal();
  });

  document.getElementById('btn-close-cancel').addEventListener('click', closeCancelModal);
  document.getElementById('cancel-modal').addEventListener('click', (e) => {
    if (e.target === e.currentTarget) closeCancelModal();
  });
  document.getElementById('btn-confirm-cancel').addEventListener('click', confirmCancel);
}

document.addEventListener('DOMContentLoaded', init);
