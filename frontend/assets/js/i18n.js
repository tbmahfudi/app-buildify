/**
 * i18next Internationalization Module
 * Provides multi-language support for the application
 *
 * Supported languages: en, es, fr, de, id
 */

class I18nManager {
  constructor() {
    this.i18next = null;
    this.currentLanguage = 'en';
    this.isInitialized = false;
  }

  /**
   * Initialize i18next with configuration
   * @returns {Promise<void>}
   */
  async init() {
    if (this.isInitialized) {
      console.log('i18n already initialized');
      return this.i18next;
    }

    try {
      // Wait for i18next to be available (CDN)
      await this.waitForI18next();

      const { i18next, i18nextHttpBackend, i18nextBrowserLanguageDetector } = window;

      // Get stored language preference
      const storedLanguage = localStorage.getItem('preferredLanguage') || 'en';

      await i18next
        .use(i18nextHttpBackend)
        .use(i18nextBrowserLanguageDetector)
        .init({
          fallbackLng: 'en',
          debug: false, // Set to true for debugging

          // Supported languages
          supportedLngs: ['en', 'es', 'fr', 'de', 'id'],

          // Namespace configuration
          ns: ['common', 'menu', 'pages'],
          defaultNS: 'common',

          // Backend configuration
          backend: {
            loadPath: '/assets/i18n/{{lng}}/{{ns}}.json',
            crossDomain: false,
            requestOptions: {
              cache: 'default'
            }
          },

          // Language detection
          detection: {
            order: ['localStorage', 'navigator', 'htmlTag'],
            caches: ['localStorage'],
            lookupLocalStorage: 'preferredLanguage'
          },

          // Interpolation
          interpolation: {
            escapeValue: false, // Not needed for vanilla JS
            prefix: '{{',
            suffix: '}}'
          },

          // React to missing keys
          saveMissing: false,
          missingKeyHandler: (lng, ns, key) => {
            console.warn(`Missing translation: ${lng}:${ns}:${key}`);
          }
        });

      // Set to stored language if different from detected
      if (storedLanguage && i18next.language !== storedLanguage) {
        await i18next.changeLanguage(storedLanguage);
      }

      this.i18next = i18next;
      this.currentLanguage = i18next.language;
      this.isInitialized = true;

      console.log(`i18n initialized with language: ${this.currentLanguage}`);

      return i18next;
    } catch (error) {
      console.error('Failed to initialize i18n:', error);
      throw error;
    }
  }

  /**
   * Wait for i18next CDN to load
   * @returns {Promise<void>}
   */
  waitForI18next() {
    return new Promise((resolve, reject) => {
      const maxAttempts = 50;
      let attempts = 0;

      const checkI18next = () => {
        if (window.i18next && window.i18nextHttpBackend && window.i18nextBrowserLanguageDetector) {
          resolve();
        } else if (attempts < maxAttempts) {
          attempts++;
          setTimeout(checkI18next, 100);
        } else {
          reject(new Error('i18next CDN failed to load'));
        }
      };

      checkI18next();
    });
  }

  /**
   * Translate a key
   * @param {string} key - Translation key (e.g., 'menu.dashboard')
   * @param {object} options - Interpolation options
   * @returns {string} - Translated text
   */
  t(key, options = {}) {
    if (!this.isInitialized || !this.i18next) {
      console.warn('i18n not initialized, returning key');
      return key;
    }
    return this.i18next.t(key, options);
  }

  /**
   * Change language
   * @param {string} lng - Language code
   * @returns {Promise<void>}
   */
  async changeLanguage(lng) {
    if (!this.isInitialized || !this.i18next) {
      console.warn('i18n not initialized');
      return;
    }

    try {
      await this.i18next.changeLanguage(lng);
      this.currentLanguage = lng;

      // Update HTML lang attribute
      document.documentElement.lang = lng;

      // Store preference
      localStorage.setItem('preferredLanguage', lng);

      // Translate all elements on the page
      this.translatePage();

      // Dispatch custom event for other components to react
      window.dispatchEvent(new CustomEvent('languageChanged', {
        detail: { language: lng }
      }));

      console.log(`Language changed to: ${lng}`);
    } catch (error) {
      console.error('Failed to change language:', error);
    }
  }

  /**
   * Get current language
   * @returns {string} - Current language code
   */
  getCurrentLanguage() {
    return this.currentLanguage;
  }

  /**
   * Translate all elements with data-i18n attribute
   */
  translatePage() {
    const elements = document.querySelectorAll('[data-i18n]');

    elements.forEach(element => {
      const key = element.getAttribute('data-i18n');
      const optionsAttr = element.getAttribute('data-i18n-options');

      try {
        const options = optionsAttr ? JSON.parse(optionsAttr) : {};
        const translation = this.t(key, options);

        // Check if we should update text content or placeholder
        if (element.hasAttribute('placeholder')) {
          element.placeholder = translation;
        } else {
          element.textContent = translation;
        }
      } catch (error) {
        console.warn(`Failed to translate element with key: ${key}`, error);
      }
    });
  }

  /**
   * Translate a single element
   * @param {string} selector - CSS selector
   * @param {string} key - Translation key
   * @param {object} options - Interpolation options
   */
  translateElement(selector, key, options = {}) {
    const element = document.querySelector(selector);
    if (element) {
      element.textContent = this.t(key, options);
    }
  }

  /**
   * Get all available languages
   * @returns {Array} - Array of language objects
   */
  getAvailableLanguages() {
    return [
      { code: 'en', name: 'English', nativeName: 'English' },
      { code: 'es', name: 'Spanish', nativeName: 'Español' },
      { code: 'fr', name: 'French', nativeName: 'Français' },
      { code: 'de', name: 'German', nativeName: 'Deutsch' },
      { code: 'id', name: 'Indonesian', nativeName: 'Bahasa Indonesia' }
    ];
  }

  /**
   * Get language name by code
   * @param {string} code - Language code
   * @returns {string} - Language name
   */
  getLanguageName(code) {
    const languages = this.getAvailableLanguages();
    const lang = languages.find(l => l.code === code);
    return lang ? lang.nativeName : code;
  }
}

// Create singleton instance
const i18nManager = new I18nManager();

// Export for use in other modules
window.i18n = i18nManager;

// Also export as module for ES6 imports
if (typeof module !== 'undefined' && module.exports) {
  module.exports = i18nManager;
}
