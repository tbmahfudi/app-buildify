/**
 * T-HC-041 — Waitlist offer banner (shared component)
 * Include on any patient page to show offer notification.
 * Usage: <script type="module" src="/modules/healthcare/frontend/patient/waitlist-banner.js"></script>
 */

import { initI18n, t } from '../i18n.js';

const API_WAITLIST = '/api/v1/patients/me/waitlist';
const BANNER_ID = 'hc-waitlist-banner';

function injectStyles() {
  if (document.getElementById('hc-waitlist-banner-styles')) return;
  const style = document.createElement('style');
  style.id = 'hc-waitlist-banner-styles';
  style.textContent = `
    #${BANNER_ID} {
      position: fixed;
      top: 0; left: 0; right: 0;
      z-index: 999;
      background: var(--color-warning, var(--color-warning));
      color: #fff;
      padding: var(--spacing-sm, 8px) var(--spacing-xl, 24px);
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-size: var(--font-sm, 14px);
      font-weight: 600;
      font-family: system-ui, sans-serif;
      box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }
    #${BANNER_ID} a { color: #fff; text-decoration: underline; margin-left: 8px; }
    #${BANNER_ID}__close { background: none; border: none; color: #fff; cursor: pointer; font-size: 18px; padding: 0 4px; line-height: 1; }
  `;
  document.head.appendChild(style);
}

function showBanner() {
  if (document.getElementById(BANNER_ID)) return; // already shown
  injectStyles();

  const banner = document.createElement('div');
  banner.id = BANNER_ID;
  banner.setAttribute('role', 'alert');
  banner.innerHTML = `
    <span>${t('waitlist.banner_msg')} <a href="/patient/waitlist">→</a></span>
    <button id="${BANNER_ID}__close" aria-label="Tutup">✕</button>
  `;

  banner.querySelector(`#${BANNER_ID}__close`).addEventListener('click', () => {
    banner.remove();
  });

  document.body.insertBefore(banner, document.body.firstChild);
}

async function checkWaitlistOffer() {
  // Only run if patient appears authenticated
  const token = sessionStorage.getItem('access_token');
  if (!token) return;

  try {
    const res = await window.apiFetch(API_WAITLIST);
    if (!res.ok) return;
    const data = await res.json();
    const entries = data.entries || data || [];
    const hasOffer = entries.some((e) => e.status === 'offered');
    if (hasOffer) showBanner();
  } catch (_) {
    // Silently ignore — banner is non-critical
  }
}

// Auto-run after i18n is ready
(async () => {
  await initI18n('id-ID');
  // Wait for DOM ready before inserting banner
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', checkWaitlistOffer);
  } else {
    await checkWaitlistOffer();
  }
})();
