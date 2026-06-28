/**
 * T-HC-038 — Patient Appointment Booking Wizard (4 steps)
 * Route: /book/:clinic_slug/:branch_id
 */

import { initI18n, t, translateDOM } from '../i18n.js';

// ── URL params ────────────────────────────────────────────────────────────────

const pathParts = location.pathname.split('/').filter(Boolean);
const bookIdx = pathParts.indexOf('book');
const CLINIC_SLUG = bookIdx >= 0 ? (pathParts[bookIdx + 1] || '') : '';
const BRANCH_ID = bookIdx >= 0 ? (pathParts[bookIdx + 2] || '') : '';
const qp = new URLSearchParams(location.search);

// ── state ─────────────────────────────────────────────────────────────────────

const state = {
  step: 1,
  appointmentType: null,
  selectedDate: null,
  selectedSlot: null,
  clinicName: qp.get('clinic_name') || CLINIC_SLUG,
  branchName: qp.get('branch_name') || '',
  calYear: new Date().getFullYear(),
  calMonth: new Date().getMonth(),
};

const APPOINTMENT_TYPES = [
  { value: 'general',    i18nName: 'booking.type_general',    desc: 'Pemeriksaan umum oleh dokter umum' },
  { value: 'specialist', i18nName: 'booking.type_specialist', desc: 'Konsultasi dengan dokter spesialis' },
  { value: 'procedure',  i18nName: 'booking.type_procedure',  desc: 'Tindakan medis atau prosedur' },
  { value: 'follow_up',  i18nName: 'booking.type_follow_up',  desc: 'Kunjungan lanjutan' },
];

const MONTH_NAMES = ['Januari','Februari','Maret','April','Mei','Juni','Juli','Agustus','September','Oktober','November','Desember'];

// ── step navigation ───────────────────────────────────────────────────────────

function goStep(n) {
  document.querySelectorAll('.hc-step').forEach((el) => el.classList.remove('active'));
  document.getElementById(`step-${n}`).classList.add('active');
  for (let i = 1; i <= 4; i++) {
    document.getElementById(`prog-${i}`).classList.toggle('done', i <= n);
  }
  state.step = n;
  clearAlert();
}

function clearAlert() {
  document.getElementById('alert-container').innerHTML = '';
}

function showAlert(type, msg) {
  const container = document.getElementById('alert-container');
  container.innerHTML = '';
  const el = document.createElement('flex-alert');
  el.setAttribute('type', type);
  el.textContent = msg;
  container.appendChild(el);
}

// ── Step 1: Type ──────────────────────────────────────────────────────────────

function buildTypeGrid() {
  const grid = document.getElementById('type-grid');
  grid.innerHTML = '';
  APPOINTMENT_TYPES.forEach((appt) => {
    const card = document.createElement('div');
    card.className = 'hc-type-card';
    card.dataset.value = appt.value;
    card.innerHTML = `<div class="hc-type-card__name">${t(appt.i18nName)}</div><div class="hc-type-card__desc">${appt.desc}</div>`;
    card.addEventListener('click', () => {
      document.querySelectorAll('.hc-type-card').forEach((c) => c.classList.remove('selected'));
      card.classList.add('selected');
      state.appointmentType = appt.value;
      document.getElementById('btn-next-1').disabled = false;
    });
    grid.appendChild(card);
  });
}

// ── Step 2: Calendar ──────────────────────────────────────────────────────────

function renderCalendar() {
  const { calYear: year, calMonth: month } = state;
  document.getElementById('cal-month').textContent = `${MONTH_NAMES[month]} ${year}`;

  const grid = document.getElementById('cal-days');
  grid.innerHTML = '';

  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const firstDay = new Date(year, month, 1).getDay();
  const startOffset = (firstDay + 6) % 7;
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const daysInPrev = new Date(year, month, 0).getDate();

  for (let i = startOffset - 1; i >= 0; i--) {
    const d = document.createElement('div');
    d.className = 'hc-cal__day other';
    d.textContent = daysInPrev - i;
    grid.appendChild(d);
  }

  for (let day = 1; day <= daysInMonth; day++) {
    const date = new Date(year, month, day);
    const dateStr = toDateStr(date);
    const isPast = date < today;
    const d = document.createElement('div');
    d.className = 'hc-cal__day' + (isPast ? ' disabled' : '');
    if (dateStr === state.selectedDate) d.classList.add('selected');
    d.textContent = day;
    if (!isPast) {
      d.addEventListener('click', () => {
        state.selectedDate = dateStr;
        document.querySelectorAll('.hc-cal__day').forEach((el) => el.classList.remove('selected'));
        d.classList.add('selected');
        document.getElementById('btn-next-2').disabled = false;
      });
    }
    grid.appendChild(d);
  }

  const totalCells = startOffset + daysInMonth;
  const remainder = totalCells % 7 === 0 ? 0 : 7 - (totalCells % 7);
  for (let i = 1; i <= remainder; i++) {
    const d = document.createElement('div');
    d.className = 'hc-cal__day other';
    d.textContent = i;
    grid.appendChild(d);
  }
}

function toDateStr(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
}

function updateTzNote() {
  const userTz = Intl.DateTimeFormat().resolvedOptions().timeZone;
  const note = document.getElementById('tz-note');
  note.textContent = `${t('booking.your_time')}: ${userTz} / ${t('booking.clinic_time')}: WIB (Asia/Jakarta)`;
}

// ── Step 3: Slots ─────────────────────────────────────────────────────────────

async function loadSlots() {
  const slotGrid = document.getElementById('slot-grid');
  const slotLoading = document.getElementById('slot-loading');
  const slotEmpty = document.getElementById('slot-empty');
  const slotBtnWrap = document.getElementById('slot-btn-wrap');

  slotGrid.style.display = 'none';
  slotEmpty.style.display = 'none';
  slotBtnWrap.style.display = 'none';
  slotLoading.style.display = 'block';
  slotGrid.innerHTML = '';
  state.selectedSlot = null;
  document.getElementById('btn-next-3').disabled = true;

  try {
    const url = `/api/v1/clinics/${CLINIC_SLUG}/branches/${BRANCH_ID}/slots?date=${state.selectedDate}&appointment_type=${state.appointmentType}`;
    const res = await window.apiFetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const slots = data.slots || data || [];

    slotLoading.style.display = 'none';

    if (!slots.length) {
      slotEmpty.style.display = 'block';
      return;
    }

    slotGrid.style.display = 'grid';
    slotBtnWrap.style.display = 'block';

    slots.forEach((slot) => {
      const card = document.createElement('div');
      card.className = 'hc-slot-card';
      card.dataset.slotId = slot.id;
      card.innerHTML = `
        <div class="hc-slot-card__time">${slot.start_time || slot.time}</div>
        <div class="hc-slot-card__provider">${slot.provider_name || ''}</div>
        <div class="hc-slot-card__provider" style="font-style:italic;">${slot.specialty || ''}</div>
      `;
      card.addEventListener('click', () => {
        document.querySelectorAll('.hc-slot-card').forEach((c) => c.classList.remove('selected'));
        card.classList.add('selected');
        state.selectedSlot = slot;
        document.getElementById('btn-next-3').disabled = false;
      });
      slotGrid.appendChild(card);
    });
  } catch (err) {
    slotLoading.style.display = 'none';
    slotEmpty.style.display = 'block';
    console.error('book: slots load failed', err);
  }
}

// ── Step 4: Confirmation ──────────────────────────────────────────────────────

function buildConfirmCard() {
  const card = document.getElementById('confirm-card');
  const slot = state.selectedSlot || {};
  const apptTypeLabel = APPOINTMENT_TYPES.find((a) => a.value === state.appointmentType);

  card.innerHTML = `
    <div class="hc-confirm-card__row"><span class="hc-confirm-card__label">Klinik</span><span class="hc-confirm-card__value">${state.clinicName}</span></div>
    <div class="hc-confirm-card__row"><span class="hc-confirm-card__label">Cabang</span><span class="hc-confirm-card__value">${state.branchName}</span></div>
    <div class="hc-confirm-card__row"><span class="hc-confirm-card__label">Tanggal</span><span class="hc-confirm-card__value">${state.selectedDate}</span></div>
    <div class="hc-confirm-card__row"><span class="hc-confirm-card__label">Waktu</span><span class="hc-confirm-card__value">${slot.start_time || slot.time || '—'}</span></div>
    <div class="hc-confirm-card__row"><span class="hc-confirm-card__label">Dokter</span><span class="hc-confirm-card__value">${slot.provider_name || '—'}</span></div>
    <div class="hc-confirm-card__row"><span class="hc-confirm-card__label">Jenis</span><span class="hc-confirm-card__value">${apptTypeLabel ? t(apptTypeLabel.i18nName) : '—'}</span></div>
  `;

  // ICS download
  buildICSLink();
}

function buildICSLink() {
  const slot = state.selectedSlot || {};
  const date = (state.selectedDate || '').replace(/-/g, '');
  const startTime = ((slot.start_time || '09:00')).replace(':', '') + '00';
  const endHour = String(parseInt((slot.start_time || '09:00').split(':')[0]) + 1).padStart(2,'0');
  const endTime = endHour + ((slot.start_time || '09:00').split(':')[1] || '00') + '00';

  const ics = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//Healthcare//Appointment//EN',
    'BEGIN:VEVENT',
    `DTSTART:${date}T${startTime}`,
    `DTEND:${date}T${endTime}`,
    'SUMMARY:Appointment',
    `LOCATION:${state.clinicName} - ${state.branchName}`,
    'END:VEVENT',
    'END:VCALENDAR',
  ].join('\r\n');

  const blob = new Blob([ics], { type: 'text/calendar;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.getElementById('ics-link');
  link.href = url;
  link.download = 'appointment.ics';
}

// ── Confirm booking ───────────────────────────────────────────────────────────

async function confirmBooking() {
  const btn = document.getElementById('btn-confirm');
  btn.disabled = true;
  clearAlert();

  try {
    const res = await window.apiFetch('/api/v1/patients/me/appointments', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        slot_id: state.selectedSlot?.id,
        appointment_type: state.appointmentType,
        branch_id: BRANCH_ID,
      }),
    });

    if (res.status === 409 || res.status === 422) {
      const err = await res.json();
      showAlert('error', err.detail || t('booking.slot_taken'));
      goStep(3);
      await loadSlots();
      return;
    }

    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const data = await res.json();
    const newId = data.id || data.appointment_id;
    location.href = `/patient/appointments/${newId}`;
  } catch (err) {
    showAlert('error', t('common.error') + ': ' + err.message);
  } finally {
    btn.disabled = false;
  }
}

// ── event wiring ──────────────────────────────────────────────────────────────

function wireEvents() {
  document.getElementById('btn-next-1').addEventListener('click', () => goStep(2));
  document.getElementById('back-2').addEventListener('click', () => goStep(1));
  document.getElementById('btn-next-2').addEventListener('click', async () => {
    goStep(3);
    await loadSlots();
  });
  document.getElementById('back-3').addEventListener('click', () => goStep(2));
  document.getElementById('btn-try-another').addEventListener('click', () => goStep(2));
  document.getElementById('btn-next-3').addEventListener('click', () => {
    buildConfirmCard();
    goStep(4);
  });
  document.getElementById('back-4').addEventListener('click', () => goStep(3));
  document.getElementById('btn-confirm').addEventListener('click', confirmBooking);

  document.getElementById('cal-prev').addEventListener('click', () => {
    state.calMonth--;
    if (state.calMonth < 0) { state.calMonth = 11; state.calYear--; }
    renderCalendar();
  });
  document.getElementById('cal-next').addEventListener('click', () => {
    state.calMonth++;
    if (state.calMonth > 11) { state.calMonth = 0; state.calYear++; }
    renderCalendar();
  });
}

// ── init ──────────────────────────────────────────────────────────────────────

async function init() {
  await initI18n('id-ID');
  translateDOM(document);
  buildTypeGrid();
  renderCalendar();
  updateTzNote();
  wireEvents();
}

document.addEventListener('DOMContentLoaded', init);
