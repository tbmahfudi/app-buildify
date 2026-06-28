/**
 * Locale switcher component — T-HC-008 / ADR-HC-004
 *
 * Auto-mounts on any element with [data-locale-switcher] on DOMContentLoaded.
 * Works in both clinic portal and patient portal.
 *
 * Usage in HTML:
 *   <div data-locale-switcher></div>
 */

import { changeLocale, getCurrentLocale } from './i18n.js';

const LOCALES = [
  { code: 'id-ID', label: '🇮🇩 Bahasa Indonesia' },
  { code: 'en-US', label: '🇬🇧 English' },
];

/**
 * Build and attach the switcher <select> into the given container element.
 * @param {HTMLElement} container
 */
function mountLocaleSwitcher(container) {
  const current = getCurrentLocale();

  const select = document.createElement('select');
  select.setAttribute('aria-label', 'Select language');
  select.className = 'hc-locale-switcher';

  LOCALES.forEach(({ code, label }) => {
    const option = document.createElement('option');
    option.value = code;
    option.textContent = label;
    if (code === current) option.selected = true;
    select.appendChild(option);
  });

  select.addEventListener('change', async (e) => {
    const selected = e.target.value;
    select.disabled = true;
    try {
      await changeLocale(selected);
    } finally {
      select.disabled = false;
    }
  });

  // Keep select in sync if locale changes from elsewhere
  document.addEventListener('hc:localeChanged', (e) => {
    select.value = e.detail.locale;
  });

  container.innerHTML = '';
  container.appendChild(select);
}

/**
 * Initialise all [data-locale-switcher] elements on the page.
 */
function initLocaleSwitchers() {
  document.querySelectorAll('[data-locale-switcher]').forEach(mountLocaleSwitcher);
}

// Auto-init
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initLocaleSwitchers);
} else {
  initLocaleSwitchers();
}

export { initLocaleSwitchers, mountLocaleSwitcher };
