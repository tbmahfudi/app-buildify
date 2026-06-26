/**
 * PasswordResetPage
 *
 * Handles the #/reset-password route. On init it extracts a reset token from
 * the URL hash (e.g. #/reset-password?token=xxx or #reset?token=xxx), clears
 * the token from browser history immediately via history.replaceState (security
 * requirement -- arch-24 section 3.1), then renders the confirm-reset form with
 * a live PasswordStrengthIndicator strength bar, and POSTs to
 * /api/v1/auth/reset-password.
 *
 * States
 *   idle     — new-password + confirm-password fields + strength bar + submit
 *   loading  — submit button shows spinner, fields disabled
 *   success  — form replaced with success message + link to login
 *   error    — invalid/expired token shown inline above form; fields hidden
 *
 * Story 24.1.1 / T-24.003
 */

import PasswordStrengthIndicator, { getStrength, renderStrengthBar } from './password-strength-indicator.js';

// ---------------------------------------------------------------------------
// Token extraction
// ---------------------------------------------------------------------------

/**
 * Extract the reset token from the current URL hash.
 * Supports:
 *   #reset?token=xxx
 *   #/reset-password?token=xxx
 *
 * @returns {string|null}
 */
function extractToken() {
  const hash = window.location.hash;
  const qIndex = hash.indexOf('?');
  if (qIndex === -1) return null;
  const qs = hash.slice(qIndex + 1);
  return new URLSearchParams(qs).get('token') || null;
}

// ---------------------------------------------------------------------------
// Public render entry-point (called by app.js route handler)
// ---------------------------------------------------------------------------

export function render(container) {
  // Extract token FIRST, then immediately clear it from the URL so it never
  // appears in server logs or browser history (arch-24 § 3.1).
  const token = extractToken();
  history.replaceState(null, '', window.location.pathname);

  const wrapper = document.createElement('div');
  wrapper.className = 'min-h-screen flex items-center justify-center bg-gray-50 px-4';
  wrapper.innerHTML = buildCardHTML();
  container.innerHTML = '';
  container.appendChild(wrapper);

  if (!token) {
    // No token in URL — show expired/invalid state immediately.
    showExpiredState(wrapper);
    return;
  }

  // Wire up the live strength bar and form submit.
  const form         = wrapper.querySelector('#prp-form');
  const newPwdEl     = wrapper.querySelector('#prp-new-password');
  const confirmEl    = wrapper.querySelector('#prp-confirm-password');
  const barContainer = wrapper.querySelector('#prp-strength-bar');

  newPwdEl.addEventListener('input', () => {
    renderStrengthBar(barContainer, newPwdEl.value);
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const newPassword = newPwdEl.value;
    const confirm     = confirmEl.value;

    // Client-side checks
    if (newPassword !== confirm) {
      showInlineError(wrapper, 'Passwords do not match.');
      return;
    }
    if (getStrength(newPassword).score < 2) {
      showInlineError(wrapper, 'Password is too weak. Please choose a stronger password.');
      return;
    }

    setLoadingState(wrapper, true);
    hideErrorBanner(wrapper);

    try {
      const res = await fetch('/api/v1/auth/reset-password', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ token, new_password: newPassword }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        const msg  = data.detail || data.message || 'Invalid or expired reset link.';
        if (res.status === 400 || res.status === 422) {
          showExpiredState(wrapper, msg);
        } else {
          showInlineError(wrapper, msg);
          setLoadingState(wrapper, false);
        }
        return;
      }

      showSuccessState(wrapper);
    } catch (_err) {
      showInlineError(wrapper, 'Network error — please try again.');
      setLoadingState(wrapper, false);
    }
  });
}

// ---------------------------------------------------------------------------
// HTML builder
// ---------------------------------------------------------------------------

function buildCardHTML() {
  return `
    <div class="w-full max-w-md">
      <div class="bg-white rounded-2xl shadow-lg px-8 py-10">

        <!-- Inline error / expired banner (initially hidden) -->
        <div id="prp-error-banner"
             class="hidden mb-4 flex items-start gap-3 bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3"
             role="alert">
          <i class="ph ph-warning text-lg mt-0.5 flex-shrink-0"></i>
          <div>
            <p class="font-medium" id="prp-error-title">Reset link has expired</p>
            <p class="text-sm mt-0.5" id="prp-error-body">
              Password reset links are valid for 1 hour. Request a new one.
            </p>
          </div>
        </div>

        <h1 class="text-2xl font-semibold text-gray-900 mb-1">Set new password</h1>
        <p class="text-sm text-gray-500 mb-6">Choose a strong password for your account.</p>

        <form id="prp-form" novalidate>

          <!-- New password -->
          <div class="mb-4">
            <label for="prp-new-password"
                   class="block text-sm font-medium text-gray-700 mb-1">New password</label>
            <input id="prp-new-password"
                   type="password"
                   autocomplete="new-password"
                   required
                   class="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm
                          focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
            <!-- 4-segment strength bar injected here by renderStrengthBar() -->
            <div id="prp-strength-bar" class="mt-2"></div>
          </div>

          <!-- Confirm password -->
          <div class="mb-6">
            <label for="prp-confirm-password"
                   class="block text-sm font-medium text-gray-700 mb-1">Confirm password</label>
            <input id="prp-confirm-password"
                   type="password"
                   autocomplete="new-password"
                   required
                   class="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm
                          focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
          </div>

          <button id="prp-submit"
                  type="submit"
                  class="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5
                         bg-blue-600 text-white font-medium text-sm rounded-lg
                         hover:bg-blue-700 transition
                         disabled:opacity-60 disabled:cursor-not-allowed">
            <i id="prp-submit-icon" class="ph ph-lock-key"></i>
            <span>Set new password</span>
          </button>
        </form>

        <p class="text-center mt-6 text-sm text-gray-500">
          <a href="#login" class="text-blue-600 hover:underline">Back to sign in</a>
        </p>

      </div>
    </div>`;
}

// ---------------------------------------------------------------------------
// State helpers
// ---------------------------------------------------------------------------

function setLoadingState(wrapper, isLoading) {
  const btn    = wrapper.querySelector('#prp-submit');
  const icon   = wrapper.querySelector('#prp-submit-icon');
  const inputs = wrapper.querySelectorAll('#prp-form input');

  btn.disabled = isLoading;
  inputs.forEach(i => { i.disabled = isLoading; });
  if (icon) {
    icon.className = isLoading ? 'ph ph-spinner animate-spin' : 'ph ph-lock-key';
  }
}

function showInlineError(wrapper, message) {
  const banner = wrapper.querySelector('#prp-error-banner');
  const title  = wrapper.querySelector('#prp-error-title');
  const body   = wrapper.querySelector('#prp-error-body');
  if (!banner) return;
  title.textContent = 'Error';
  body.textContent  = message;
  banner.classList.remove('hidden');
  banner.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function hideErrorBanner(wrapper) {
  wrapper.querySelector('#prp-error-banner')?.classList.add('hidden');
}

function showExpiredState(wrapper, message) {
  const banner = wrapper.querySelector('#prp-error-banner');
  const title  = wrapper.querySelector('#prp-error-title');
  const body   = wrapper.querySelector('#prp-error-body');
  const form   = wrapper.querySelector('#prp-form');

  if (title) title.textContent = 'Reset link has expired';
  if (body)  body.textContent  = message || 'Password reset links are valid for 1 hour. Request a new one.';

  // Append "Request new link" button if not already there
  if (banner && !banner.querySelector('.prp-request-new')) {
    const link = document.createElement('a');
    link.href = '#reset-password';
    link.className = 'prp-request-new inline-block mt-2 text-sm font-medium text-red-700 underline';
    link.textContent = 'Request new link';
    banner.appendChild(link);
  }

  banner?.classList.remove('hidden');
  // Hide the password fields per uildc-24 § 2.1.1 Gap B
  if (form) form.classList.add('hidden');
}

function showSuccessState(wrapper) {
  const card = wrapper.querySelector('.bg-white');
  if (!card) return;
  card.innerHTML = `
    <div class="flex flex-col items-center text-center py-4">
      <i class="ph ph-check-circle text-5xl text-green-500 mb-4"></i>
      <h2 class="text-xl font-semibold text-gray-900 mb-2">Password updated</h2>
      <p class="text-sm text-gray-500 mb-6">
        Your password has been changed successfully.
        You can now sign in with your new password.
      </p>
      <a href="#login"
         class="inline-flex items-center gap-2 px-5 py-2.5
                bg-blue-600 text-white font-medium text-sm rounded-lg
                hover:bg-blue-700 transition">
        <i class="ph ph-sign-in"></i> Sign in
      </a>
    </div>`;
}
