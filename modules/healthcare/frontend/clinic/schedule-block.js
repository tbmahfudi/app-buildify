/**
 * T-HC-036 — Date/Time Block UI
 * Route: /clinic/branches/:branch_id/schedules/:provider_id/block
 */

import { initI18n, t, translateDOM } from '../i18n.js';
import '../locale-switcher.js';

const pathParts = location.pathname.split('/');
const BRANCH_ID = new URLSearchParams(location.search).get('branch_id')
  || pathParts[pathParts.indexOf('branches') + 1] || '';
const PROVIDER_ID = new URLSearchParams(location.search).get('provider_id')
  || pathParts[pathParts.indexOf('schedules') + 1] || '';

const API_BLOCKS = `/api/v1/modules/healthcare_scheduling/branches/${BRANCH_ID}/schedules/${PROVIDER_ID}/blocks`;

// ── state ─────────────────────────────────────────────────────────────────────

let currentYear = new Date().getFullYear();
let currentMonth = new Date().getMonth(); // 0-indexed
let blockedRanges = []; // [{id, start_date, end_date, start_time, end_time, reason, recurrence}]

// ── calendar ──────────────────────────────────────────────────────────────────

const MONTH_NAMES_ID = ['Januari','Februari','Maret','April','Mei','Juni','Juli','Agustus','September','Oktober','November','Desember'];

function isDateBlocked(dateStr) {
  return blockedRanges.find((b) => dateStr >= b.start_date && dateStr <= b.end_date);
}

function renderCalendar() {
  const label = document.getElementById('cal-month-label');
  label.textContent = `${MONTH_NAMES_ID[currentMonth]} ${currentYear}`;

  const grid = document.getElementById('cal-days');
  grid.innerHTML = '';

  // First day of month (0=Sun, convert to Mon-first)
  const firstDay = new Date(currentYear, currentMonth, 1).getDay();
  const startOffset = (firstDay + 6) % 7; // Mon=0
  const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
  const daysInPrev = new Date(currentYear, currentMonth, 0).getDate();

  // Prev month filler
  for (let i = startOffset - 1; i >= 0; i--) {
    const d = document.createElement('div');
    d.className = 'hc-cal__day other-month';
    d.textContent = daysInPrev - i;
    grid.appendChild(d);
  }

  // Current month days
  for (let day = 1; day <= daysInMonth; day++) {
    const dateStr = `${currentYear}-${String(currentMonth + 1).padStart(2,'0')}-${String(day).padStart(2,'0')}`;
    const block = isDateBlocked(dateStr);
    const d = document.createElement('div');
    d.className = 'hc-cal__day' + (block ? ' blocked' : '');
    d.textContent = day;
    d.style.position = 'relative';

    if (block) {
      const tooltip = document.createElement('div');
      tooltip.className = 'hc-cal__tooltip';
      tooltip.innerHTML = `<strong>${block.reason || '—'}</strong><br>${block.start_time || ''} – ${block.end_time || ''}<br>
        <span class="hc-cal__remove" data-block-id="${block.id}" data-i18n="schedule.remove_block">${t('schedule.remove_block')}</span>`;
      tooltip.querySelector('.hc-cal__remove').addEventListener('click', (e) => {
        e.stopPropagation();
        removeBlock(block.id);
      });
      d.appendChild(tooltip);
    }

    grid.appendChild(d);
  }

  // Next month filler
  const totalCells = startOffset + daysInMonth;
  const remainder = totalCells % 7 === 0 ? 0 : 7 - (totalCells % 7);
  for (let i = 1; i <= remainder; i++) {
    const d = document.createElement('div');
    d.className = 'hc-cal__day other-month';
    d.textContent = i;
    grid.appendChild(d);
  }
}

// ── modal ─────────────────────────────────────────────────────────────────────

function openModal() {
  document.getElementById('block-modal').classList.add('open');
}

function closeModal() {
  document.getElementById('block-modal').classList.remove('open');
}

// ── API ───────────────────────────────────────────────────────────────────────

async function loadBlocks() {
  try {
    const res = await window.apiFetch(API_BLOCKS);
    if (!res.ok) return;
    const data = await res.json();
    blockedRanges = data.blocks || data || [];
    renderCalendar();
  } catch (err) {
    console.error('schedule-block: load failed', err);
  }
}

async function submitBlock() {
  const btn = document.getElementById('btn-submit-block');
  btn.disabled = true;

  const payload = {
    start_date: document.getElementById('block-start-date').value,
    end_date: document.getElementById('block-end-date').value,
    start_time: document.getElementById('block-start-time').value,
    end_time: document.getElementById('block-end-time').value,
    reason: document.getElementById('block-reason').value,
    recurrence: document.getElementById('block-recurrence').value,
  };

  try {
    const res = await window.apiFetch(API_BLOCKS, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const data = await res.json();

    if (!res.ok) {
      showAlert('error', data.detail || t('common.error'));
      return;
    }

    // Warning: affected appointments
    if (data.flagged_appointments_count > 0) {
      showAlert('warning',
        t('schedule.affected_appointments', { count: data.flagged_appointments_count }) +
        ` — <a href="/clinic/appointments?branch_id=${BRANCH_ID}&flagged=1">${t('schedule.view_affected')}</a>`
      );
    }

    closeModal();
    await loadBlocks();
  } catch (err) {
    showAlert('error', t('common.error') + ': ' + err.message);
  } finally {
    btn.disabled = false;
  }
}

async function removeBlock(blockId) {
  // Stub — endpoint TBD
  try {
    const res = await window.apiFetch(`${API_BLOCKS}/${blockId}`, { method: 'DELETE' });
    if (res.ok) {
      blockedRanges = blockedRanges.filter((b) => b.id !== blockId);
      renderCalendar();
    }
  } catch (err) {
    console.warn('schedule-block: remove stub failed', err);
  }
}

function showAlert(type, html) {
  const container = document.getElementById('alert-container');
  const el = document.createElement('flex-alert');
  el.setAttribute('type', type);
  el.innerHTML = html;
  container.innerHTML = '';
  container.appendChild(el);
}

// ── init ──────────────────────────────────────────────────────────────────────

async function init() {
  await initI18n('id-ID');
  translateDOM(document);

  renderCalendar();

  document.getElementById('cal-prev').addEventListener('click', () => {
    currentMonth--;
    if (currentMonth < 0) { currentMonth = 11; currentYear--; }
    renderCalendar();
  });

  document.getElementById('cal-next').addEventListener('click', () => {
    currentMonth++;
    if (currentMonth > 11) { currentMonth = 0; currentYear++; }
    renderCalendar();
  });

  document.getElementById('btn-open-block').addEventListener('click', openModal);
  document.getElementById('btn-cancel-block').addEventListener('click', closeModal);
  document.getElementById('btn-submit-block').addEventListener('click', submitBlock);

  document.getElementById('block-modal').addEventListener('click', (e) => {
    if (e.target === e.currentTarget) closeModal();
  });

  await loadBlocks();
}

document.addEventListener('DOMContentLoaded', init);
