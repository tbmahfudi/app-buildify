// Import resource loader first to make it available globally
import './resource-loader.js';

// Import i18n module
import './i18n.js';

import { initApp } from './app.js';
import './tenants.js';
import './organization-hierarchy.js';
import './companies.js';
import './generic-entity-page.js';
import './users.js';
import './settings.js';
import './profile-page.js';
import './audit-enhanced.js';
import './showcase.js';
import './module-page.js';
import './rbac-page.js';
import './auth-policies-page.js';
import './sample-reports-dashboards-page.js';
import './report-designer-page.js';
import './dashboard-designer-page.js';

// Resource loader is automatically available at window.resourceLoader
// Error handling classes are available at window.ErrorDisplay and window.ResourceLoadError
// i18n is available at window.i18n

// Initialize i18n and then start the app
(async () => {
  try {
    // Initialize i18n
    await window.i18n.init();
    console.log('i18n initialized successfully');

    // Initialize the app
    initApp();

    // Translate the initial page
    setTimeout(() => {
      window.i18n.translatePage();
    }, 100);
  } catch (error) {
    console.error('Failed to initialize i18n:', error);
    // Still init the app even if i18n fails
    initApp();
  }
})();
