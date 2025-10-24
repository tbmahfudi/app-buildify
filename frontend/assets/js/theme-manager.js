/**
 * ThemeManager - Complete theme management system
 * Handles dark/light mode with smooth transitions
 * Uses in-memory state (no localStorage)
 */

class ThemeManager {
  constructor() {
    this.currentTheme = 'light'; // 'light' or 'dark'
    this.listeners = new Set();
    this.initialized = false;
    
    // Theme colors configuration
    this.themes = {
      light: {
        name: 'Light Mode',
        colors: {
          background: '#ffffff',
          surface: '#f9fafb',
          surfaceHover: '#f3f4f6',
          primary: '#3b82f6',
          primaryHover: '#2563eb',
          text: '#111827',
          textSecondary: '#6b7280',
          border: '#e5e7eb',
          success: '#10b981',
          warning: '#f59e0b',
          error: '#ef4444',
          info: '#3b82f6'
        }
      },
      dark: {
        name: 'Dark Mode',
        colors: {
          background: '#0f172a',
          surface: '#1e293b',
          surfaceHover: '#334155',
          primary: '#60a5fa',
          primaryHover: '#3b82f6',
          text: '#f1f5f9',
          textSecondary: '#94a3b8',
          border: '#334155',
          success: '#34d399',
          warning: '#fbbf24',
          error: '#f87171',
          info: '#60a5fa'
        }
      }
    };
  }

  /**
   * Initialize the theme system
   */
  init() {
    if (this.initialized) return;
    
    // Check system preference
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    this.currentTheme = prefersDark ? 'dark' : 'light';
    
    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)')
      .addEventListener('change', (e) => {
        if (!this.userOverride) {
          this.setTheme(e.matches ? 'dark' : 'light', false);
        }
      });
    
    this.applyTheme();
    this.initialized = true;
    
    console.log(`ThemeManager initialized: ${this.currentTheme} mode`);
  }

  /**
   * Set the current theme
   * @param {string} theme - 'light' or 'dark'
   * @param {boolean} userInitiated - Whether this was a user action
   */
  setTheme(theme, userInitiated = true) {
    if (!['light', 'dark'].includes(theme)) {
      console.warn(`Invalid theme: ${theme}. Using 'light' instead.`);
      theme = 'light';
    }

    if (this.currentTheme === theme) return;

    const previousTheme = this.currentTheme;
    this.currentTheme = theme;
    this.userOverride = userInitiated;

    this.applyTheme();
    this.notifyListeners(previousTheme, theme);

    console.log(`Theme changed: ${previousTheme} → ${theme}`);
  }

  /**
   * Toggle between light and dark themes
   */
  toggle() {
    const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
    this.setTheme(newTheme, true);
    return newTheme;
  }

  /**
   * Apply the current theme to the document
   */
  applyTheme() {
    const theme = this.themes[this.currentTheme];
    const root = document.documentElement;

    // Apply Tailwind's dark class
    if (this.currentTheme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }

    // Apply CSS custom properties for fine-grained control
    Object.entries(theme.colors).forEach(([key, value]) => {
      root.style.setProperty(`--color-${key}`, value);
    });

    // Update meta theme-color for mobile browsers
    let metaTheme = document.querySelector('meta[name="theme-color"]');
    if (!metaTheme) {
      metaTheme = document.createElement('meta');
      metaTheme.name = 'theme-color';
      document.head.appendChild(metaTheme);
    }
    metaTheme.content = theme.colors.background;
  }

  /**
   * Get the current theme name
   * @returns {string}
   */
  getTheme() {
    return this.currentTheme;
  }

  /**
   * Get theme colors
   * @param {string} theme - Optional theme name, defaults to current
   * @returns {object}
   */
  getColors(theme = null) {
    const targetTheme = theme || this.currentTheme;
    return { ...this.themes[targetTheme].colors };
  }

  /**
   * Check if dark mode is active
   * @returns {boolean}
   */
  isDark() {
    return this.currentTheme === 'dark';
  }

  /**
   * Check if light mode is active
   * @returns {boolean}
   */
  isLight() {
    return this.currentTheme === 'light';
  }

  /**
   * Subscribe to theme changes
   * @param {Function} callback - Called with (previousTheme, newTheme)
   * @returns {Function} Unsubscribe function
   */
  subscribe(callback) {
    if (typeof callback !== 'function') {
      throw new Error('Callback must be a function');
    }
    
    this.listeners.add(callback);
    
    // Return unsubscribe function
    return () => {
      this.listeners.delete(callback);
    };
  }

  /**
   * Notify all listeners of theme change
   * @private
   */
  notifyListeners(previousTheme, newTheme) {
    this.listeners.forEach(callback => {
      try {
        callback(previousTheme, newTheme);
      } catch (error) {
        console.error('Error in theme listener:', error);
      }
    });
  }

  /**
   * Get system color scheme preference
   * @returns {string} 'light' or 'dark'
   */
  getSystemPreference() {
    return window.matchMedia('(prefers-color-scheme: dark)').matches 
      ? 'dark' 
      : 'light';
  }

  /**
   * Reset to system preference
   */
  resetToSystem() {
    this.userOverride = false;
    const systemTheme = this.getSystemPreference();
    this.setTheme(systemTheme, false);
  }

  /**
   * Create a theme toggle button
   * @param {object} options - Configuration options
   * @returns {HTMLElement}
   */
  createToggleButton(options = {}) {
    const {
      className = '',
      showLabel = true,
      size = 'md'
    } = options;

    const sizeClasses = {
      sm: 'text-sm px-2 py-1',
      md: 'text-base px-3 py-2',
      lg: 'text-lg px-4 py-3'
    };

    const button = document.createElement('button');
    button.className = `
      inline-flex items-center gap-2 rounded-lg
      bg-white dark:bg-slate-800
      border border-gray-300 dark:border-slate-600
      text-gray-700 dark:text-gray-200
      hover:bg-gray-50 dark:hover:bg-slate-700
      transition-all duration-200
      ${sizeClasses[size]}
      ${className}
    `.trim().replace(/\s+/g, ' ');

    const updateButton = () => {
      const isDark = this.isDark();
      const icon = isDark ? '☀️' : '🌙';
      const label = isDark ? 'Light Mode' : 'Dark Mode';
      
      button.innerHTML = `
        <span class="text-xl">${icon}</span>
        ${showLabel ? `<span class="font-medium">${label}</span>` : ''}
      `;
      button.setAttribute('aria-label', `Switch to ${label}`);
      button.setAttribute('title', `Switch to ${label}`);
    };

    button.addEventListener('click', () => {
      this.toggle();
    });

    // Update on theme change
    this.subscribe(() => {
      updateButton();
    });

    updateButton();
    return button;
  }

  /**
   * Apply theme to a specific element
   * @param {HTMLElement} element
   * @param {object} options - Styling options
   */
  applyToElement(element, options = {}) {
    const {
      background = true,
      border = true,
      text = true
    } = options;

    const updateElement = () => {
      const isDark = this.isDark();
      
      if (background) {
        element.classList.toggle('bg-white', !isDark);
        element.classList.toggle('dark:bg-slate-800', isDark);
      }
      
      if (border) {
        element.classList.toggle('border-gray-300', !isDark);
        element.classList.toggle('dark:border-slate-600', isDark);
      }
      
      if (text) {
        element.classList.toggle('text-gray-900', !isDark);
        element.classList.toggle('dark:text-gray-100', isDark);
      }
    };

    this.subscribe(updateElement);
    updateElement();
  }

  /**
   * Destroy the theme manager
   */
  destroy() {
    this.listeners.clear();
    this.initialized = false;
    document.documentElement.classList.remove('dark');
  }
}

// Export singleton instance
export const themeManager = new ThemeManager();
export default themeManager;