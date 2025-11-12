/**
 * Auth Policies Page Route Handler
 * Initializes the SecurityAdmin component when the auth-policies route is loaded
 */

// Listen for route loaded events
document.addEventListener('route:loaded', async (event) => {
  const { route } = event.detail;

  // Initialize SecurityAdmin when auth-policies route is loaded
  if (route === 'auth-policies') {
    console.log('Initializing Security Administration...');

    try {
      // Function to wait for SecurityAdmin to be available
      const waitForSecurityAdmin = () => {
        return new Promise((resolve, reject) => {
          // Check if already loaded
          if (window.securityAdmin) {
            resolve(window.securityAdmin);
            return;
          }

          // Try to load the script if not present
          if (!document.querySelector('script[src="/components/security-admin.js"]')) {
            const script = document.createElement('script');
            script.src = '/components/security-admin.js';
            script.type = 'text/javascript';

            script.onload = () => {
              // Wait a bit for script to execute
              setTimeout(() => {
                if (window.securityAdmin) {
                  resolve(window.securityAdmin);
                } else {
                  reject(new Error('SecurityAdmin script loaded but window.securityAdmin not found'));
                }
              }, 100);
            };

            script.onerror = () => {
              reject(new Error('Failed to load SecurityAdmin script from /components/security-admin.js'));
            };

            document.head.appendChild(script);
          } else {
            // Script tag exists, wait for window.securityAdmin
            let attempts = 0;
            const checkInterval = setInterval(() => {
              attempts++;
              if (window.securityAdmin) {
                clearInterval(checkInterval);
                resolve(window.securityAdmin);
              } else if (attempts > 20) {
                // Waited 2 seconds
                clearInterval(checkInterval);
                reject(new Error('SecurityAdmin script tag exists but window.securityAdmin not initialized'));
              }
            }, 100);
          }
        });
      };

      // Wait for SecurityAdmin to be available
      const securityAdmin = await waitForSecurityAdmin();

      // Initialize for this container
      await securityAdmin.init('security-admin-container');
      console.log('Security Administration initialized successfully');

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
                  <p class="text-sm text-red-600 font-mono bg-red-100 p-2 rounded">${error.message}</p>
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
