/**
 * RBAC Page Route Handler
 * Initializes the RBAC management interface when the rbac route is loaded
 */

import { initRBACManager } from './rbac-manager.js';

// Listen for route loaded events
document.addEventListener('route:loaded', async (event) => {
  const { route } = event.detail;

  // Initialize RBAC Manager when rbac route is loaded
  if (route === 'rbac') {
    try {
      await initRBACManager();
    } catch (error) {
      console.error('Failed to initialize RBAC Manager:', error);
    }
  }
});
