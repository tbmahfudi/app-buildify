/**
 * T-HC-035 — Provider Schedule Editor
 * Route: /clinic/branches/:branch_id/schedules/:provider_id
 */

import { initI18n, t, translateDOM } from '../i18n.js';
import '../locale-switcher.js';

// ── URL params ────────────────────────────────────────────────────────────────

const params = new URLSearchParams(location.search);
const pathParts = location.pathname.split('/');
const BRANCH_ID = params.get('branch_id') || pathParts[pathParts.indexOf('branches') + 1] || '';
const PROVIDER_ID = params.get('provider_id') || pathParts[pathParts.indexOf('schedules') + 1] || '';
const TZ = params.get('tz') || 'WIB';

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const DAY_KEYS = ['schedule.mon', 'schedule.tue', 'schedule.wed', 'schedule.thu', 'schedule.fri', 'schedule.sat', 'schedule.sun'];
const DAY_LABELS_ID = ['Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab', 'Min'];
const START_HOUR = 7;
const END_HOUR = 20;

// state: Set of "dayIndex-HH:MM" strings for active cells
const activeSlots = new Set();
let slotDuration = 30;
let isDragging = false;
let dragValue = null; // true = activating, false = deactivating

// ── helpers ───────────────────────────────────────────────────────────────────

function timeSlots() {
  const slots = [];
  for (let h = START_HOUR; h < END_HOUR; h++) {
    slots.push(`${String(h).padStart(2, '0')}:00`);
    slots.push(`${String(h).padStart(2, '0')}:30`);
  }
  return slots;
}

function cellKey(dayIdx, time) {
  return `${dayIdx}-${time}`;
}

function showAlert(type, msg) {
  const container = document.getElementById('alert-container');
  container.innerHTML = '';
  const el = document.createElement('flex-alert');
  el.setAttribute('type', type);
  el.textContent = msg;
  container.appendChild(el);
}

function clearAlert() {
  document.getElementById('alert-container').innerHTML = '';
}

// ── grid build ────────────────────────────────────────────────────────────────

function buildGrid() {
  const grid = document.getElementById('weekly-grid');
  grid.innerHTML = '';
  const times = timeSlots();

  // Corner
  const corner = document.createElement('div');
  corner.className = 'hc-grid__corner';
  corner.textContent = TZ;
  grid.appendChild(corner);

  // Column headers
  DAYS.forEach((day, i) => {
    const th = document.createElement('div');
    th.className = 'hc-grid__col-head';
    th.textContent = DAY_LABELS_ID[i];
    grid.appendChild(th);
  });

  // Time rows
  times.forEach((time) => {
    const timeCell = document.createElement('div');
    timeCell.className = 'hc-grid__time';
    timeCell.textContent = time;
    grid.appendChild(timeCell);

    DAYS.forEach((_, dayIdx) => {
      const cell = document.createElement('div');
      cell.className = 'hc-grid__cell';
      cell.dataset.key = cellKey(dayIdx, time);
      cell.setAttribute('role', 'gridcell');
      cell.setAttribute('aria-label', `${DAY_LABELS_ID[dayIdx]} ${time}`);
      cell.setAttribute('tabindex', '0');

      if (activeSlots.has(cellKey(dayIdx, time))) cell.classList.add('active');

      // Mouse events for click+drag
      cell.addEventListener('mousedown', (e) => {
        e.preventDefault();
        isDragging = true;
        const key = cell.dataset.key;
        dragValue = !activeSlots.has(key);
        toggleCell(cell, key, dragValue);
      });

      cell.addEventListener('mouseover', () => {
        if (isDragging) toggleCell(cell, cell.dataset.key, dragValue);
      });

      cell.addEventListener('keydown', (e) => {
        if (e.key === ' ' || e.key === 'Enter') {
          e.preventDefault();
          const key = cell.dataset.key;
          toggleCell(cell, key, !activeSlots.has(key));
        }
      });

      grid.appendChild(cell);
    });
  });

  document.addEventListener('mouseup', () => { isDragging = false; dragValue = null; });
}

function toggleCell(el, key, activate) {
  if (activate) {
    activeSlots.add(key);
    el.classList.add('active');
  } else {
    activeSlots.delete(key);
    el.classList.remove('active');
  }
}

// ── mobile accordion ──────────────────────────────────────────────────────────

function buildMobileAccordion() {
  const container = document.getElementById('mobile-accordion');
  container.innerHTML = '';

  DAYS.forEach((day, i) => {
    const wrap = document.createElement('div');
    wrap.className = 'hc-accordion-day';

    const header = document.createElement('div');
    header.className = 'hc-accordion-day__header';
    header.innerHTML = `<span>${DAY_LABELS_ID[i]}</span><span>+</span>`;

    const body = document.createElement('div');
    body.className = 'hc-accordion-day__body';
    body.id = `accordion-body-${i}`;
    body.innerHTML = `
      <div class="hc-time-range">
        <label>Mulai</label>
        <input type="time" id="mobile-start-${i}" min="07:00" max="20:00" value="08:00" />
        <label>Selesai</label>
        <input type="time" id="mobile-end-${i}" min="07:00" max="20:00" value="17:00" />
      </div>
      <button class="hc-btn hc-btn--primary" data-day="${i}" id="mobile-add-${i}" style="font-size:var(--font-sm);padding:var(--spacing-xs) var(--spacing-md);">+ Tambah Blok</button>
    `;

    header.addEventListener('click', () => {
      body.classList.toggle('open');
    });

    body.querySelector(`#mobile-add-${i}`).addEventListener('click', () => {
      const start = document.getElementById(`mobile-start-${i}`).value;
      const end = document.getElementById(`mobile-end-${i}`).value;
      applyMobileBlock(i, start, end);
    });

    wrap.appendChild(header);
    wrap.appendChild(body);
    container.appendChild(wrap);
  });
}

function applyMobileBlock(dayIdx, startTime, endTime) {
  const times = timeSlots();
  times.forEach((t) => {
    if (t >= startTime && t < endTime) {
      activeSlots.add(cellKey(dayIdx, t));
    }
  });
}

// ── serialize schedule blocks ─────────────────────────────────────────────────

function serializeBlocks() {
  // Group consecutive active slots per day into blocks
  const blocks = [];
  const times = timeSlots();

  for (let dayIdx = 0; dayIdx < 7; dayIdx++) {
    let blockStart = null;
    let prevTime = null;

    times.forEach((time, i) => {
      const active = activeSlots.has(cellKey(dayIdx, time));
      if (active && blockStart === null) {
        blockStart = time;
      } else if (!active && blockStart !== null) {
        blocks.push({
          day_of_week: dayIdx + 1,
          start_time: blockStart,
          end_time: prevTime,
          slot_duration_minutes: slotDuration,
          appointment_types: getSelectedApptTypes(),
        });
        blockStart = null;
      }
      prevTime = time;

      // End of day
      if (i === times.length - 1 && active && blockStart !== null) {
        blocks.push({
          day_of_week: dayIdx + 1,
          start_time: blockStart,
          end_time: '20:00',
          slot_duration_minutes: slotDuration,
          appointment_types: getSelectedApptTypes(),
        });
        blockStart = null;
      }
    });
  }
  return blocks;
}

function getSelectedApptTypes() {
  return Array.from(document.querySelectorAll('[name=appt_type]:checked')).map((el) => el.value);
}

// ── API ───────────────────────────────────────────────────────────────────────

const API_BASE = `/api/v1/modules/healthcare_scheduling/branches/${BRANCH_ID}/schedules/${PROVIDER_ID}`;

async function loadSchedule() {
  try {
    const res = await window.apiFetch(API_BASE);
    if (!res.ok) return;
    const data = await res.json();
    const scheduleBlocks = data.blocks || [];
    const times = timeSlots();

    activeSlots.clear();
    scheduleBlocks.forEach((block) => {
      const dayIdx = (block.day_of_week || 1) - 1;
      times.forEach((time) => {
        if (time >= block.start_time && time < block.end_time) {
          activeSlots.add(cellKey(dayIdx, time));
        }
      });
    });

    renderActiveCells();
  } catch (err) {
    console.error('schedule-editor: load failed', err);
  }
}

function renderActiveCells() {
  document.querySelectorAll('.hc-grid__cell').forEach((cell) => {
    cell.classList.toggle('active', activeSlots.has(cell.dataset.key));
  });
}

async function saveSchedule() {
  clearAlert();
  const btn = document.getElementById('btn-save');
  btn.disabled = true;

  const blocks = serializeBlocks();

  try {
    const res = await window.apiFetch(API_BASE, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ blocks }),
    });

    if (res.status === 409) {
      const err = await res.json();
      showAlert('error', t('schedule.conflict_error') + (err.detail ? ': ' + err.detail : ''));
      return;
    }

    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const now = new Date();
    const timeStr = `${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}`;
    document.getElementById('save-status').textContent = `${t('schedule.last_saved')}: ${timeStr}`;
  } catch (err) {
    showAlert('error', t('common.error') + ': ' + err.message);
  } finally {
    btn.disabled = false;
  }
}

// ── init ──────────────────────────────────────────────────────────────────────

async function init() {
  await initI18n('id-ID');

  document.getElementById('tz-label').textContent = TZ;

  buildGrid();
  buildMobileAccordion();
  translateDOM(document);

  await loadSchedule();

  document.getElementById('slot-duration').addEventListener('change', (e) => {
    slotDuration = parseInt(e.target.value, 10);
  });

  document.getElementById('btn-save').addEventListener('click', saveSchedule);
}

document.addEventListener('DOMContentLoaded', init);
