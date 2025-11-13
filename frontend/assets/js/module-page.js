/**
 * Module Management Initialization
 * Handles loading and initialization of the module manager page
 */

import { moduleManager } from './module-manager-enhanced.js';

// Initialize on route load
document.addEventListener('route:loaded', async (e) => {
  if (e.detail.route === 'modules') {
    await initModuleManager();
  }
});

async function initModuleManager() {
  console.log('Initializing module manager...');

  // Render the module manager UI
  await moduleManager.render();
}
