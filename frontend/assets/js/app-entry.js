// Import resource loader first to make it available globally
import './resource-loader.js';

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

initApp();
