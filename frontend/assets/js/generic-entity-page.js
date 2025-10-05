import { EntityManager } from './entity-manager.js';

/**
 * Initialize generic entity pages
 * Usage: Call initGenericEntity('companies') for any entity
 */
document.addEventListener('route:loaded', async (e) => {
  const route = e.detail.route;
  
  // Check if this is an entity route
  const entityRoutes = ['companies', 'branches', 'departments'];
  
  if (entityRoutes.includes(route)) {
    await initGenericEntity(route);
  }
});

async function initGenericEntity(entity) {
  const container = document.getElementById('content');
  
  // Clear and show loading
  const loadingDiv = document.createElement('div');
  loadingDiv.innerHTML = '<div class="text-center"><div class="spinner-border"></div><p class="mt-2">Loading...</p></div>';
  container.innerHTML = '';
  container.appendChild(loadingDiv);
  
  // Create entity manager
  const manager = new EntityManager(container, entity);
  await manager.init();
}

// Export for use in other modules
export { initGenericEntity };