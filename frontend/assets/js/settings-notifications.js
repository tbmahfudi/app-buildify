/**
 * Settings Notifications Page Route Handler
 * T-24.008: Prepends a persistent honesty banner to the page content.
 * The banner informs users that email notifications are not yet active.
 */

document.addEventListener('route:loaded', (event) => {
  const { route } = event.detail;

  if (route === 'settings-notifications') {
    console.log('Notification settings page loaded');
    _prependHonestyBanner();
  }
});

/**
 * _prependHonestyBanner
 *
 * Inserts a persistent FlexAlert-style warning banner at the top of the
 * settings-notifications content area (Story 24.1.2 / T-24.008).
 * The banner uses the ph-envelope-simple-slash icon and warns users that
 * email notifications are not yet active.
 */
function _prependHonestyBanner() {
  const content = document.getElementById('content');
  if (!content) return;

  // Avoid double-insertion on hot reloads
  if (content.querySelector('#notif-honesty-banner')) return;

  const banner = document.createElement('div');
  banner.id = 'notif-honesty-banner';
  banner.setAttribute('role', 'alert');
  banner.className = [
    'flex items-start gap-3 px-4 py-3 mb-6',
    'bg-amber-50 border border-amber-200 rounded-lg text-amber-800',
  ].join(' ');

  banner.innerHTML = `
    <i class="ph ph-envelope-simple-slash text-amber-600 text-xl flex-shrink-0 mt-0.5"></i>
    <p class="text-sm">
      <strong class="font-semibold">Email notifications are not yet active</strong>
      &mdash; configuration in progress. Settings saved here will take effect once
      the email service is enabled.
    </p>`;

  content.prepend(banner);
}
