/**
 * T-HC-042 — Notification Settings UI (Clinic)
 * Route: /clinic/settings/notifications
 */

import { initI18n, t, translateDOM } from '../i18n.js';
import '../locale-switcher.js';

const API_TEST = '/api/v1/modules/healthcare_scheduling/notifications/test';

// ── template definitions ──────────────────────────────────────────────────────

const TEMPLATES = [
  {
    id: 'appointment_confirmed',
    channel: 'whatsapp',
    previews: {
      'id-ID': 'Halo [Nama Pasien], janji Anda di [Nama Klinik] - [Nama Cabang] telah dikonfirmasi untuk [Tanggal] pukul [Waktu]. Terima kasih.',
      'en-US': 'Hello [Patient Name], your appointment at [Clinic Name] - [Branch Name] is confirmed for [Date] at [Time]. Thank you.',
    },
  },
  {
    id: 'appointment_reminder_24h',
    channel: 'whatsapp',
    previews: {
      'id-ID': 'Pengingat: Anda memiliki janji di [Nama Klinik] besok [Tanggal] pukul [Waktu]. Harap hadir 15 menit lebih awal.',
      'en-US': 'Reminder: You have an appointment at [Clinic Name] tomorrow [Date] at [Time]. Please arrive 15 minutes early.',
    },
  },
  {
    id: 'appointment_reminder_2h',
    channel: 'sms',
    previews: {
      'id-ID': 'Pengingat: Janji Anda di [Nama Klinik] dalam 2 jam ([Waktu]). Hubungi kami jika perlu reschedule.',
      'en-US': 'Reminder: Your appointment at [Clinic Name] is in 2 hours ([Time]). Contact us if you need to reschedule.',
    },
  },
  {
    id: 'appointment_cancelled',
    channel: 'whatsapp',
    previews: {
      'id-ID': 'Janji Anda di [Nama Klinik] pada [Tanggal] pukul [Waktu] telah dibatalkan. Silakan buat janji baru jika diperlukan.',
      'en-US': 'Your appointment at [Clinic Name] on [Date] at [Time] has been cancelled. Please book a new appointment if needed.',
    },
  },
  {
    id: 'appointment_rescheduled',
    channel: 'whatsapp',
    previews: {
      'id-ID': 'Janji Anda di [Nama Klinik] telah dijadwalkan ulang ke [Tanggal Baru] pukul [Waktu Baru]. Konfirmasi: [Link].',
      'en-US': 'Your appointment at [Clinic Name] has been rescheduled to [New Date] at [New Time]. Confirm: [Link].',
    },
  },
  {
    id: 'waitlist_offer',
    channel: 'whatsapp',
    previews: {
      'id-ID': 'Slot tersedia untuk Anda di [Nama Klinik] pada [Tanggal] pukul [Waktu]. Konfirmasi dalam 15 menit: [Link]. Penawaran berakhir [Waktu Kedaluwarsa].',
      'en-US': 'A slot is available for you at [Clinic Name] on [Date] at [Time]. Confirm within 15 minutes: [Link]. Offer expires [Expiry Time].',
    },
  },
];

// ── state ─────────────────────────────────────────────────────────────────────

let testTemplateId = null;
const cardLocales = {}; // templateId -> current preview locale

// ── render ────────────────────────────────────────────────────────────────────

function channelLabel(channel) {
  return channel === 'whatsapp'
    ? t('notification.channel_whatsapp')
    : t('notification.channel_sms');
}

function buildTemplateCard(tmpl) {
  const locale = cardLocales[tmpl.id] || 'id-ID';

  const card = document.createElement('div');
  card.className = 'hc-template-card';
  card.id = `tmpl-${tmpl.id}`;

  card.innerHTML = `
    <div class="hc-template-card__header">
      <span class="hc-template-card__name">${tmpl.id}</span>
      <span class="hc-template-card__channel">${channelLabel(tmpl.channel)}</span>
      <span class="hc-locked-badge">
        🔒 ${t('notification.template_locked')}
        <span class="hc-tooltip">${t('notification.template_locked')}: Templates are system-locked to prevent PHI leakage</span>
      </span>
    </div>
    <div class="hc-locale-toggle" data-tmpl="${tmpl.id}">
      <button class="hc-locale-btn ${locale === 'id-ID' ? 'active' : ''}" data-locale="id-ID">id-ID</button>
      <button class="hc-locale-btn ${locale === 'en-US' ? 'active' : ''}" data-locale="en-US">en-US</button>
    </div>
    <div class="hc-template-preview" id="preview-${tmpl.id}">${tmpl.previews[locale] || ''}</div>
    <div class="hc-template-card__footer">
      <button class="hc-btn hc-btn--outline" data-test-tmpl="${tmpl.id}">${t('notification.send_test')}</button>
    </div>
  `;

  // Locale toggle
  card.querySelectorAll('.hc-locale-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      const newLocale = btn.dataset.locale;
      cardLocales[tmpl.id] = newLocale;
      card.querySelectorAll('.hc-locale-btn').forEach((b) => {
        b.classList.toggle('active', b.dataset.locale === newLocale);
      });
      document.getElementById(`preview-${tmpl.id}`).textContent = tmpl.previews[newLocale] || '';
    });
  });

  // Send test button
  card.querySelector(`[data-test-tmpl="${tmpl.id}"]`).addEventListener('click', () => {
    testTemplateId = tmpl.id;
    document.getElementById('test-phone').value = '';
    document.getElementById('test-result').textContent = '';
    document.getElementById('test-modal').classList.add('open');
  });

  return card;
}

function renderTemplates() {
  const container = document.getElementById('templates-container');
  container.innerHTML = '';
  TEMPLATES.forEach((tmpl) => {
    cardLocales[tmpl.id] = cardLocales[tmpl.id] || 'id-ID';
    container.appendChild(buildTemplateCard(tmpl));
  });
}

// ── send test ─────────────────────────────────────────────────────────────────

async function sendTest() {
  const phone = document.getElementById('test-phone').value.trim();
  const resultEl = document.getElementById('test-result');
  const btn = document.getElementById('btn-submit-test');

  if (!phone) {
    resultEl.textContent = t('validation.required');
    return;
  }

  btn.disabled = true;
  resultEl.textContent = t('common.loading');

  try {
    const res = await window.apiFetch(API_TEST, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ template_id: testTemplateId, phone }),
    });

    if (res.status === 404) {
      resultEl.textContent = t('notification.coming_soon');
      return;
    }

    if (!res.ok) {
      const err = await res.json();
      resultEl.textContent = err.detail || t('common.error');
      return;
    }

    resultEl.textContent = '✓ Test message sent.';
    setTimeout(() => closeTestModal(), 2000);
  } catch (err) {
    if (err.message.includes('404') || err.message.includes('Not Found')) {
      resultEl.textContent = t('notification.coming_soon');
    } else {
      resultEl.textContent = t('common.error') + ': ' + err.message;
    }
  } finally {
    btn.disabled = false;
  }
}

function closeTestModal() {
  document.getElementById('test-modal').classList.remove('open');
  testTemplateId = null;
}

// ── init ──────────────────────────────────────────────────────────────────────

async function init() {
  await initI18n('id-ID');
  translateDOM(document);
  renderTemplates();

  document.getElementById('btn-close-test').addEventListener('click', closeTestModal);
  document.getElementById('test-modal').addEventListener('click', (e) => {
    if (e.target === e.currentTarget) closeTestModal();
  });
  document.getElementById('btn-submit-test').addEventListener('click', sendTest);
}

document.addEventListener('DOMContentLoaded', init);
