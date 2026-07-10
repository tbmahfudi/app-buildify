import { login, getAuthToken } from './api.js';

/**
 * After a successful platform login, route patient-role users to the healthcare
 * portal instead of the staff SPA. Patients authenticate against the platform
 * (users table) but the portal runs on a separate patient-token auth; the
 * bridge endpoint exchanges the platform JWT for a patient session. Returns
 * true if it redirected to the portal, false to fall through to the staff SPA.
 */
async function routePatientToPortal() {
  try {
    const token = getAuthToken();
    if (!token) return false;

    const meRes = await fetch('/api/v1/auth/me', {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!meRes.ok) return false;
    const me = await meRes.json();
    if (!(me.roles || []).includes('patient')) return false;

    // Exchange the platform token for a patient portal session.
    const brRes = await fetch('/api/v1/patients/auth/from-platform', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!brRes.ok) return false;
    const data = await brRes.json();
    if (!data.access_token) return false;

    localStorage.setItem('hc_patient_token', data.access_token);
    window.location.href = '/portal/healthcare/';
    return true;
  } catch (_e) {
    return false;
  }
}

const form = document.getElementById('login-form');
const errorDiv = document.getElementById('login-error');
const errorMessage = document.getElementById('error-message');

if (form) {
  form.addEventListener('submit', async (event) => {
    event.preventDefault();

    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const tenantValue = document.getElementById('tenant').value.trim();
    const tenant = tenantValue === '' ? null : tenantValue;

    errorDiv.classList.add('hidden');
    errorMessage.textContent = '';

    try {
      await login(email, password, tenant);
      // Patients go to the healthcare portal; everyone else to the staff SPA.
      if (await routePatientToPortal()) return;
      window.location.href = '/index.html';
    } catch (error) {
      errorMessage.textContent = error.message;
      errorDiv.classList.remove('hidden');
    }
  });
}

// ============================================================================
// T-24.006 / T-24.007 -- Forgot-password request & confirm views
// Story 24.1.1 -- appended to login-page.js; exported for use by app.js
// ============================================================================

/**
 * renderRequestReset(container)
 *
 * Request-reset view (T-24.006).
 * Renders an email form; on success replaces with "Check your inbox" state.
 * Calls POST /api/v1/auth/reset-password-request (user-enumeration safe -- always 200).
 */
export function renderRequestReset(container) {
  container.innerHTML = '';
  const wrapper = document.createElement('div');
  wrapper.className = 'min-h-screen flex items-center justify-center bg-gray-50 px-4';
  wrapper.innerHTML = buildRequestResetHTML();
  container.appendChild(wrapper);

  const form    = wrapper.querySelector('#prr-form');
  const emailEl = wrapper.querySelector('#prr-email');
  const errEl   = wrapper.querySelector('#prr-error');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = emailEl.value.trim();
    if (!email) return;

    errEl.classList.add('hidden');
    _setReqLoadingState(wrapper, true);

    try {
      await fetch('/api/v1/auth/reset-password-request', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ email }),
      });
      // Always show success regardless of server response (user-enumeration safe)
      _showEmailSentState(wrapper, email);
    } catch (_err) {
      errEl.textContent = 'Network error -- please try again.';
      errEl.classList.remove('hidden');
      _setReqLoadingState(wrapper, false);
    }
  });
}

function buildRequestResetHTML() {
  return `
    <div class="w-full max-w-md">
      <div class="bg-white rounded-2xl shadow-lg px-8 py-10">
        <h1 class="text-2xl font-semibold text-gray-900 mb-1">Reset your password</h1>
        <p class="text-sm text-gray-500 mb-6">
          Enter the email address for your account and we will send you a reset link.
        </p>
        <div id="prr-error"
             class="hidden mb-4 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-2"
             role="alert"></div>
        <form id="prr-form" novalidate>
          <div class="mb-4">
            <label for="prr-email" class="block text-sm font-medium text-gray-700 mb-1">
              Email address
            </label>
            <input id="prr-email"
                   type="email"
                   autocomplete="email"
                   required
                   placeholder="you@example.com"
                   class="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm
                          focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                          focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none" />
          </div>
          <button id="prr-submit"
                  type="submit"
                  class="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5
                         bg-blue-600 text-white font-medium text-sm rounded-lg
                         hover:bg-blue-700 transition
                         disabled:opacity-60 disabled:cursor-not-allowed
                         focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none">
            <i id="prr-submit-icon" class="ph ph-envelope-simple"></i>
            <span>Send reset link</span>
          </button>
        </form>
        <p class="text-center mt-6 text-sm text-gray-500">
          <a href="#login" class="text-blue-600 hover:underline">Back to sign in</a>
        </p>
      </div>
    </div>`;
}

function _setReqLoadingState(wrapper, isLoading) {
  const btn  = wrapper.querySelector('#prr-submit');
  const icon = wrapper.querySelector('#prr-submit-icon');
  const inp  = wrapper.querySelector('#prr-email');
  if (btn)  btn.disabled   = isLoading;
  if (inp)  inp.disabled   = isLoading;
  if (icon) icon.className = isLoading ? 'ph ph-spinner animate-spin' : 'ph ph-envelope-simple';
}

// Gap A (uildc-24 section 2.1.1) -- email-sent confirmation state.
// Replaces the entire form. Does NOT reveal whether the email is registered.
function _showEmailSentState(wrapper, email) {
  const card = wrapper.querySelector('.bg-white');
  if (!card) return;
  const safeEmail = email.replace(/[&<>"']/g, c =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])
  );
  card.innerHTML = `
    <div class="flex flex-col items-center gap-4 text-center py-4">
      <i class="ph ph-envelope-open text-5xl text-blue-500"></i>
      <h2 class="text-xl font-semibold text-gray-900">Check your inbox</h2>
      <p class="text-sm text-gray-500 text-center max-w-xs">
        If an account exists for <strong class="text-gray-700">${safeEmail}</strong>,
        you will receive a password reset link shortly.
        Check your spam folder if it does not arrive.
      </p>
      <a href="#login" class="text-sm text-blue-600 hover:underline">Back to sign in</a>
    </div>`;
}
