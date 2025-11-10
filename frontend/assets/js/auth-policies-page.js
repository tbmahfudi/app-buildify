/**
 * Auth Policies Page Route Handler
 * Initializes the SecurityAdmin component when the auth-policies route is loaded
 */

// Listen for route loaded events
document.addEventListener('route:loaded', async (event) => {
  const { route } = event.detail;

  console.log('Route loaded:', route);

  // Initialize SecurityAdmin when auth-policies route is loaded
  if (route === 'auth-policies') {
    console.log('Initializing Security Administration...');
    try {
      // Load SecurityAdmin component script
      const loadSecurityAdmin = () => {
        return new Promise((resolve, reject) => {
          // Check if script is already loaded
          if (document.querySelector('script[src="/components/security-admin.js"]')) {
            resolve();
            return;
          }

          const script = document.createElement('script');
          script.src = '/components/security-admin.js';
          script.type = 'text/javascript';

          script.onload = () => resolve();
          script.onerror = () => reject(new Error('Failed to load SecurityAdmin script'));

          document.head.appendChild(script);
        });
      };

      // Load the script
      await loadSecurityAdmin();

      // Access the global SecurityAdmin instance
      if (window.securityAdmin) {
        // Re-initialize for this container
        await window.securityAdmin.init('security-admin-container');
        console.log('Security Administration initialized successfully');
      } else {
        throw new Error('SecurityAdmin not found on window object');
      }
    } catch (error) {
      console.error('Failed to initialize Security Administration:', error);

      // Show error message in container
      const container = document.getElementById('security-admin-container');
      if (container) {
        container.innerHTML = `
          <div class="max-w-md mx-auto mt-20">
            <div class="bg-red-50 border-l-4 border-red-500 p-6 rounded-lg shadow-sm">
              <div class="flex items-start gap-3">
                <i class="ph-duotone ph-warning text-red-500 text-3xl"></i>
                <div>
                  <h3 class="text-lg font-semibold text-red-800 mb-2">Failed to Load</h3>
                  <p class="text-red-700 mb-4">The Security Administration component could not be loaded.</p>
                  <p class="text-sm text-red-600">${error.message}</p>
                  <button
                    onclick="window.location.reload()"
                    class="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition flex items-center gap-2">
                    <i class="ph ph-arrow-clockwise"></i> Retry
                  </button>
                </div>
              </div>
            </div>
          </div>
        `;
      }
    }
  }
});
