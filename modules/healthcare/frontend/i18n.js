/**
 * Healthcare i18n core module — T-HC-008 / ADR-HC-004
 *
 * i18next-compatible API surface (t, changeLocale) built on vanilla JS /
 * fetch so it works without a bundler (arch-00-platform §4).
 *
 * Usage:
 *   import { initI18n, t, changeLocale, getCurrentLocale } from './i18n.js';
 *   await initI18n();
 *   document.title = t('nav.dashboard');
 */

import { fetchTranslations, LOCALE_PERSIST_URL } from './api-endpoint.js';

const STORAGE_KEY = 'hc_locale';
const SUPPORTED_LOCALES = ['id-ID', 'en-US'];

// Module-level state — never exposed as globals
let _translations = {};
let _locale = 'id-ID';
let _observer = null;

// ── locale resolution ────────────────────────────────────────────────────────

/**
 * Resolve starting locale from: localStorage → <html lang> → 'id-ID'
 * @returns {string}
 */
export function getCurrentLocale() {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored && SUPPORTED_LOCALES.includes(stored)) return stored;

  const htmlLang = document.documentElement.lang;
  if (htmlLang && SUPPORTED_LOCALES.includes(htmlLang)) return htmlLang;

  return 'id-ID';
}

// ── translation lookup ───────────────────────────────────────────────────────

/**
 * i18next-compatible translation function.
 * Replaces {{param}} and {param} placeholders.
 * Returns the key itself on miss — never throws.
 * @param {string} key
 * @param {object} [params]
 * @returns {string}
 */
export function t(key, params = {}) {
  const raw = _translations[key];
  if (raw === undefined) {
    console.warn(`i18n: missing key "${key}" for locale "${_locale}"`);
    return key;
  }
  return raw.replace(/\{\{?(\w+)\}?\}/g, (_, name) =>
    Object.prototype.hasOwnProperty.call(params, name) ? params[name] : `{${name}}`
  );
}

// ── DOM translation ──────────────────────────────────────────────────────────

/**
 * Find all [data-i18n] elements under root and set their textContent.
 * @param {Element|Document} [root=document]
 */
export function translateDOM(root = document) {
  const elements = (root === document ? document : root).querySelectorAll
    ? (root === document ? document.querySelectorAll('[data-i18n]') : root.querySelectorAll('[data-i18n]'))
    : [];
  elements.forEach((el) => {
    const key = el.dataset.i18n;
    if (key) el.textContent = t(key);
  });
}

// ── MutationObserver ─────────────────────────────────────────────────────────

function _startObserver() {
  if (_observer) _observer.disconnect();

  _observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      for (const node of mutation.addedNodes) {
        if (node.nodeType !== Node.ELEMENT_NODE) continue;
        // Translate the node itself if it carries data-i18n
        if (node.dataset && node.dataset.i18n) {
          node.textContent = t(node.dataset.i18n);
        }
        // Translate descendants
        translateDOM(node);
      }
    }
  });

  _observer.observe(document.body, { childList: true, subtree: true });
}

// ── locale switching ─────────────────────────────────────────────────────────

/**
 * Switch to a new locale:
 *  1. Fetch translations (cached by fetchTranslations if already loaded)
 *  2. Update module state
 *  3. Persist to localStorage
 *  4. Re-render all [data-i18n] elements
 *  5. Update <html lang>
 *  6. Fire-and-forget PUT /api/v1/users/me/locale (if session cookie present)
 * @param {string} locale
 * @returns {Promise<void>}
 */
export async function changeLocale(locale) {
  if (!SUPPORTED_LOCALES.includes(locale)) {
    console.warn(`i18n: unsupported locale "${locale}", ignoring`);
    return;
  }

  try {
    _translations = await fetchTranslations(locale);
  } catch (err) {
    console.error('i18n: changeLocale fetch failed, keeping current locale', err);
    return;
  }

  _locale = locale;
  localStorage.setItem(STORAGE_KEY, locale);
  document.documentElement.lang = locale;
  translateDOM(document);

  // Fire-and-forget persistence — do not block or await
  _persistLocaleToServer(locale);

  // Dispatch custom event so other modules can react
  document.dispatchEvent(new CustomEvent('hc:localeChanged', { detail: { locale } }));
}

/**
 * Attempt to persist locale to authenticated user's profile.
 * Silently swallows errors — unauthenticated users simply have no session.
 * @param {string} locale
 */
async function _persistLocaleToServer(locale) {
  window.apiFetch(LOCALE_PERSIST_URL, {
    method: 'PUT',
    body: JSON.stringify({ locale }),
  }).catch(() => {});
}

// ── initialisation ───────────────────────────────────────────────────────────

/**
 * Initialise i18n. Call once on DOMContentLoaded.
 * @param {string} [defaultLocale='id-ID']  overridden by localStorage / <html lang>
 * @returns {Promise<void>}
 */
export async function initI18n(defaultLocale = 'id-ID') {
  const locale = getCurrentLocale() || defaultLocale;
  try {
    _translations = await fetchTranslations(locale);
    _locale = locale;
  } catch (err) {
    console.error('i18n: initI18n failed, falling back to id-ID', err);
    try {
      _translations = await fetchTranslations('id-ID');
      _locale = 'id-ID';
    } catch (fallbackErr) {
      console.error('i18n: fallback also failed — no translations loaded', fallbackErr);
      _translations = {};
      _locale = 'id-ID';
    }
  }

  document.documentElement.lang = _locale;
  translateDOM(document);
  _startObserver();
}
