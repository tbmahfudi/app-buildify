/**
 * RBAC Page Route Handler
 * Initializes the RBAC management interface when the rbac route is loaded
 */

import { initRBACManager } from './rbac-manager.js';

// Listen for route loaded events
document.addEventListener('route:loaded', async (event) => {
  const { route } = event.detail;

  console.log('Route loaded:', route);

  // Initialize RBAC Manager when rbac route is loaded
  if (route === 'rbac') {
    console.log('Initializing RBAC Manager...');
    try {
      await initRBACManager();
      console.log('RBAC Manager initialized successfully');
    } catch (error) {
      console.error('Failed to initialize RBAC Manager:', error);
    }
  }
});
