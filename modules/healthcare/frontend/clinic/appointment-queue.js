/**
 * T-HC-040 — Appointment Queue UI
 * Route: /clinic/appointments/queue
 */

import { initI18n, t, translateDOM } from '../i18n.js';
import '../locale-switcher.js';

// ── branch context ────────────────────────────────────────────────────────────

function getBranchId() {
  // Try cookie first
  const match = document.cookie.match(/(?:^|;\s*)branch_id=([^;]+)/);
  if (match) return match[1];
  return sessionStorage.getItem('branch_id') || '';
}

const BRANCH_ID = getBranchId();
const API_QUEUE = `/api/v1/modules/healthcare_scheduling/branches/${BRANCH_ID}/appointments/queue`;
const API_STATUS = (apptId) =>
  `/api/v1/modules/healthcare_scheduling/branches/${BRANCH_ID}/appointments/${apptId}/status`;
const WS_URL = BRANCH_ID
  ? `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws/branches/${BRANCH_ID}/queue`
  : null;

// ── state ─────────────────────────────────────────────────────────────────────

let phiMask = false;
let appointments = [];
let ws = null;
let pollInterval = null;

// ── helpers ───────────────────────────────────────────────────────────────────

const STATUS_ORDER = ['confirmed', 'checked_in', 'in_progress'];
const STATUS_LABELS = {
  confirmed:   { cls: 'hc-badge--confirmed',   key: 'appointment.status_confirmed' },
  checked_in:  { cls: 'hc-badge--checked_in',  key: 'appointment.status_checked_in' },
  in_progress: { cls: 'hc-badge--in_progress', key: 'appointment.status_in_progress' },
  completed:   { cls: 'hc-badge--completed',   key: 'appointment.status_completed' },
  no_show:     { cls: 'hc-badge--no_show',     key: 'appointment.status_no_show' },
};

function patientDisplay(appt) {
  if (phiMask) return 'Pasien ●●●●';
  return appt.patient_name || appt.patient_id || '—';
}

function badgeHTML(status) {
  const info = STATUS_LABELS[status] || { cls: '', key: status };
  return `<span class="hc-badge ${info.cls}">${t(info.key)}</span>`;
}

// ── render ────────────────────────────────────────────────────────────────────

function renderSkeleton() {
  const container = document.getElementById('queue-container');
  container.innerHTML = Array(4).fill(0).map(() =>
    `<div class="hc-skeleton hc-skeleton-card"></div>`
  ).join('');
}

function renderQueue() {
  const container = document.getElementById('queue-container');
  container.innerHTML = '';

  const grouped = {};
  STATUS_ORDER.forEach((s) => { grouped[s] = []; });
  appointments.forEach((a) => {
    if (STATUS_ORDER.includes(a.status)) grouped[a.status].push(a);
  });

  let anyShown = false;
  STATUS_ORDER.forEach((status) => {
    const group = grouped[status];
    if (!group.length) return;
    anyShown = true;

    const section = document.createElement('div');
    section.className = 'hc-group';
    section.innerHTML = `<div class="hc-group__label">${t(STATUS_LABELS[status]?.key || status)}</div>`;

    group.forEach((appt) => {
      section.appendChild(buildCard(appt));
    });

    container.appendChild(section);
  });

  if (!anyShown) {
    container.innerHTML = `<div class="hc-empty">${t('queue.empty')}</div>`;
  }
}

function buildCard(appt) {
  const card = document.createElement('div');
  card.className = 'hc-queue-card';
  card.dataset.id = appt.id;

  const timeStr = appt.scheduled_at
    ? new Date(appt.scheduled_at).toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' })
    : appt.time || '—';

  card.innerHTML = `
    <div class="hc-queue-card__top">
      <span class="hc-queue-card__name" data-patient="${appt.id}">${patientDisplay(appt)}</span>
      <span class="hc-queue-card__time">${timeStr}</span>
      ${badgeHTML(appt.status)}
    </div>
    <div class="hc-queue-card__actions" id="actions-${appt.id}"></div>
  `;

  const actionsEl = card.querySelector(`#actions-${appt.id}`);
  buildActions(actionsEl, appt);

  return card;
}

function buildActions(container, appt) {
  container.innerHTML = '';

  if (appt.status === 'confirmed') {
    container.appendChild(actionBtn(t('queue.check_in'), 'hc-btn--teal', () => updateStatus(appt.id, 'checked_in')));
    container.appendChild(actionBtn(t('queue.no_show'), 'hc-btn--grey', () => updateStatus(appt.id, 'no_show')));
  } else if (appt.status === 'checked_in') {
    container.appendChild(actionBtn(t('queue.start'), 'hc-btn--orange', () => updateStatus(appt.id, 'in_progress')));
  } else if (appt.status === 'in_progress') {
    container.appendChild(actionBtn(t('queue.complete'), 'hc-btn--green', () => updateStatus(appt.id, 'completed')));
  }
}

function actionBtn(label, cls, onClick) {
  const btn = document.createElement('button');
  btn.className = `hc-btn ${cls}`;
  btn.textContent = label;
  btn.addEventListener('click', onClick);
  return btn;
}

// ── API ───────────────────────────────────────────────────────────────────────

async function loadQueue() {
  try {
    const res = await window.apiFetch(API_QUEUE);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    appointments = data.appointments || data || [];
    renderQueue();
  } catch (err) {
    console.error('queue: load failed', err);
  }
}

async function updateStatus(apptId, newStatus) {
  // Optimistic update
  const appt = appointments.find((a) => a.id === apptId);
  const prevStatus = appt?.status;
  if (appt) appt.status = newStatus;
  renderQueue();

  try {
    const res = await window.apiFetch(API_STATUS(apptId), {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
  } catch (err) {
    // Revert on error
    if (appt) appt.status = prevStatus;
    renderQueue();
    const el = document.createElement('flex-alert');
    el.setAttribute('type', 'error');
    el.textContent = t('common.error') + ': ' + err.message;
    const container = document.getElementById('alert-container');
    container.innerHTML = '';
    container.appendChild(el);
  }
}

// ── WebSocket / polling ───────────────────────────────────────────────────────

function startRealtime() {
  if (!WS_URL) {
    startPolling();
    return;
  }

  try {
    ws = new WebSocket(WS_URL);

    ws.addEventListener('message', (e) => {
      try {
        const msg = JSON.parse(e.data);
        if (msg.appointments) {
          appointments = msg.appointments;
          renderQueue();
        } else {
          // Incremental update
          loadQueue();
        }
      } catch (_) {
        loadQueue();
      }
    });

    ws.addEventListener('error', () => {
      ws = null;
      startPolling();
    });

    ws.addEventListener('close', () => {
      if (!pollInterval) startPolling();
    });
  } catch (_) {
    startPolling();
  }
}

function startPolling() {
  if (pollInterval) return;
  pollInterval = setInterval(loadQueue, 30000);
}

// ── PHI mask toggle ───────────────────────────────────────────────────────────

function applyPhiMask() {
  document.querySelectorAll('[data-patient]').forEach((el) => {
    const apptId = el.dataset.patient;
    const appt = appointments.find((a) => String(a.id) === apptId);
    if (appt) el.textContent = patientDisplay(appt);
  });
}

// ── init ──────────────────────────────────────────────────────────────────────

async function init() {
  await initI18n('id-ID');
  translateDOM(document);

  // Branch name
  const branchName = sessionStorage.getItem('branch_name') || BRANCH_ID || '—';
  document.getElementById('branch-name').textContent = branchName;

  // PHI toggle
  document.getElementById('phi-toggle').addEventListener('change', (e) => {
    phiMask = e.target.checked;
    applyPhiMask();
  });

  // Initial load
  renderSkeleton();
  await loadQueue();

  // Realtime
  startRealtime();
}

document.addEventListener('DOMContentLoaded', init);

// Cleanup on unload
window.addEventListener('beforeunload', () => {
  if (ws) ws.close();
  if (pollInterval) clearInterval(pollInterval);
});
