/**
 * Healthcare i18n API endpoint constants and fetch helper.
 * T-HC-008 — ADR-HC-004
 */

export const I18N_BASE_URL = '/api/v1/modules/healthcare/i18n';
export const LOCALE_PERSIST_URL = '/api/v1/users/me/locale';

/**
 * Fetch translation JSON for the given locale from the backend.
 * Falls back to id-ID if the locale file is unavailable.
 * @param {string} locale  e.g. 'id-ID', 'en-US'
 * @returns {Promise<object>}  translation key→value map
 */
export async function fetchTranslations(locale) {
  const url = `${I18N_BASE_URL}/${locale}`;
  const res = await fetch(url, {
    headers: { Accept: 'application/json' },
  });
  if (!res.ok) {
    if (locale !== 'id-ID') {
      // fallback to default locale
      return fetchTranslations('id-ID');
    }
    throw new Error(`i18n: failed to fetch translations for ${locale} (${res.status})`);
  }
  return res.json();
}
