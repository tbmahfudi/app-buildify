/**
 * T-HC-037 — Availability Heatmap UI
 * Route: /clinic/branches/:branch_id/availability
 */

import { initI18n, t, translateDOM } from '../i18n.js';
import '../locale-switcher.js';

const params = new URLSearchParams(location.search);
const pathParts = location.pathname.split('/');
const BRANCH_ID = params.get('branch_id') || pathParts[pathParts.indexOf('branches') + 1] || '';

const API_SCHEDULES = `/api/v1/modules/healthcare_scheduling/branches/${BRANCH_ID}/schedules`;

// ── date helpers ──────────────────────────────────────────────────────────────

function toDateStr(d) {
  return d.toISOString().slice(0, 10);
}

function addDays(dateStr, n) {
  const d = new Date(dateStr);
  d.setDate(d.getDate() + n);
  return toDateStr(d);
}

function defaultRange() {
  const today = toDateStr(new Date());
  return { start: today, end: addDays(today, 6) };
}

function dateRange(start, end) {
  const dates = [];
  let cur = start;
  while (cur <= end) {
    dates.push(cur);
    cur = addDays(cur, 1);
  }
  return dates;
}

function shortDate(dateStr) {
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('id-ID', { weekday: 'short', day: 'numeric', month: 'short' });
}

// ── availability calculation ──────────────────────────────────────────────────

/**
 * Given a provider's schedule blocks, calculate available slot count for a date.
 * Returns { available, total } where available = slots not yet booked.
 * The API gives us total slots per block; booked_count per slot date is in bookings array if present.
 */
function calcAvailability(provider, dateStr) {
  const dayOfWeek = ((new Date(dateStr + 'T00:00:00').getDay() + 6) % 7) + 1; // 1=Mon
  let total = 0;
  let booked = 0;

  const blocks = provider.schedule_blocks || [];
  blocks.forEach((block) => {
    if (block.day_of_week !== dayOfWeek) return;
    const startMins = timeToMins(block.start_time);
    const endMins = timeToMins(block.end_time);
    const dur = block.slot_duration_minutes || 30;
    const blockSlots = Math.floor((endMins - startMins) / dur);
    total += blockSlots;
  });

  // Booked slots from bookings array if provided
  const bookings = provider.bookings || [];
  bookings.forEach((b) => {
    if (b.date === dateStr) booked += 1;
  });

  return { available: Math.max(0, total - booked), total };
}

function timeToMins(timeStr) {
  const [h, m] = (timeStr || '00:00').split(':').map(Number);
  return h * 60 + m;
}

function availabilityClass(available, total) {
  if (total === 0) return 'hc-cell--none';
  const pct = available / total;
  if (pct > 0.3) return 'hc-cell--high';
  if (pct > 0) return 'hc-cell--mid';
  return 'hc-cell--low';
}

// ── render ────────────────────────────────────────────────────────────────────

function renderSkeleton(dates) {
  const head = document.getElementById('heatmap-head');
  const body = document.getElementById('heatmap-body');

  head.innerHTML = `<tr><th>Dokter</th>${dates.map((d) => `<th>${shortDate(d)}</th>`).join('')}</tr>`;
  body.innerHTML = '';

  for (let i = 0; i < 5; i++) {
    const tr = document.createElement('tr');
    tr.className = 'hc-skeleton-row';
    tr.innerHTML = `<td><div class="hc-skeleton" style="height:16px;width:120px;"></div></td>` +
      dates.map(() => `<td><div class="hc-skeleton" style="height:16px;width:48px;margin:auto;"></div></td>`).join('');
    body.appendChild(tr);
  }
}

function renderHeatmap(providers, dates) {
  const head = document.getElementById('heatmap-head');
  const body = document.getElementById('heatmap-body');

  head.innerHTML = `<tr><th>Dokter</th>${dates.map((d) => `<th>${shortDate(d)}</th>`).join('')}</tr>`;
  body.innerHTML = '';

  if (!providers.length) {
    body.innerHTML = `<tr><td colspan="${dates.length + 1}" style="padding:var(--spacing-xl);color:var(--color-text-tertiary);">${t('queue.empty')}</td></tr>`;
    return;
  }

  providers.forEach((provider) => {
    const tr = document.createElement('tr');
    const nameTd = document.createElement('td');
    nameTd.className = 'hc-cell--provider';
    nameTd.textContent = provider.provider_name || provider.name || provider.id;
    tr.appendChild(nameTd);

    dates.forEach((dateStr) => {
      const { available, total } = calcAvailability(provider, dateStr);
      const pct = total > 0 ? Math.round((available / total) * 100) : null;
      const td = document.createElement('td');
      td.className = 'hc-cell--data ' + availabilityClass(available, total);
      td.textContent = pct !== null ? `${pct}%` : '—';
      td.title = `${provider.provider_name || provider.id}: ${available}/${total} slots`;
      td.addEventListener('click', () => {
        const url = `schedule-editor.html?branch_id=${BRANCH_ID}&provider_id=${provider.id}&date=${dateStr}`;
        location.href = url;
      });
      tr.appendChild(td);
    });

    body.appendChild(tr);
  });
}

// ── CSV export ────────────────────────────────────────────────────────────────

function exportCSV(providers, dates) {
  const header = ['Dokter', ...dates].join(',');
  const rows = providers.map((p) => {
    const cells = dates.map((d) => {
      const { available, total } = calcAvailability(p, d);
      return total > 0 ? `${Math.round((available / total) * 100)}%` : '—';
    });
    return [(p.provider_name || p.id), ...cells].join(',');
  });
  const csv = [header, ...rows].join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `availability-${dates[0]}-to-${dates[dates.length - 1]}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

// ── load ──────────────────────────────────────────────────────────────────────

let currentProviders = [];
let currentDates = [];

async function load(start, end) {
  currentDates = dateRange(start, end);
  renderSkeleton(currentDates);

  try {
    const res = await window.apiFetch(`${API_SCHEDULES}?start=${start}&end=${end}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    currentProviders = data.providers || data || [];
    renderHeatmap(currentProviders, currentDates);
  } catch (err) {
    const container = document.getElementById('alert-container');
    const alert = document.createElement('flex-alert');
    alert.setAttribute('type', 'error');
    alert.textContent = t('common.error') + ': ' + err.message;
    container.innerHTML = '';
    container.appendChild(alert);
  }
}

// ── init ──────────────────────────────────────────────────────────────────────

async function init() {
  await initI18n('id-ID');
  translateDOM(document);

  const { start, end } = defaultRange();
  document.getElementById('range-start').value = start;
  document.getElementById('range-end').value = end;

  document.getElementById('btn-apply-range').addEventListener('click', () => {
    const s = document.getElementById('range-start').value;
    const e = document.getElementById('range-end').value;
    if (s && e && s <= e) load(s, e);
  });

  document.getElementById('btn-export-csv').addEventListener('click', () => {
    exportCSV(currentProviders, currentDates);
  });

  await load(start, end);
}

document.addEventListener('DOMContentLoaded', init);
