/**
 * Application Configuration
 * Centralized configuration management
 */

// Environment detection
const ENV = {
  development: 'development',
  staging: 'staging',
  production: 'production'
};

// Get current environment (can be set via build tools)
const currentEnv = import.meta.env?.MODE || ENV.development;

// Configuration per environment
const configs = {
  [ENV.development]: {
    apiBase: '/api',
    apiTimeout: 30000,
    apiRetries: 3,
    enableDebug: true,
    logLevel: 'debug'
  },
  
  [ENV.staging]: {
    apiBase: 'https://staging-api.example.com/api',
    apiTimeout: 30000,
    apiRetries: 3,
    enableDebug: true,
    logLevel: 'info'
  },
  
  [ENV.production]: {
    apiBase: 'https://api.example.com/api',
    apiTimeout: 30000,
    apiRetries: 2,
    enableDebug: false,
    logLevel: 'error'
  }
};

// Export config for current environment
export const config = {
  ...configs[currentEnv],
  env: currentEnv,
  isProd: currentEnv === ENV.production,
  isDev: currentEnv === ENV.development
};

// App constants
export const APP_NAME = 'NoCode Platform';
export const APP_VERSION = '1.0.0';
export const TOKEN_REFRESH_BUFFER = 5 * 60 * 1000; // 5 minutes before expiry

// UI Constants
export const TOAST_DURATION = 5000;
export const DEBOUNCE_DELAY = 300;
export const PAGE_SIZE_DEFAULT = 25;
export const PAGE_SIZE_OPTIONS = [10, 25, 50, 100];

// Date formats
export const DATE_FORMATS = {
  short: 'MM/DD/YYYY',
  long: 'MMMM DD, YYYY',
  datetime: 'MM/DD/YYYY HH:mm:ss'
};

// Export all
export default config;