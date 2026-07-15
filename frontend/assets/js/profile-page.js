import { apiFetch } from './api.js';
import PasswordStrengthIndicator from './password-strength-indicator.js';

// Listen for route changes to profile page
document.addEventListener('route:loaded', (event) => {
  if (event.detail.route === 'profile') {
    // Use setTimeout to ensure DOM is fully ready after innerHTML update
    setTimeout(() => initProfilePage(), 50);
  }
});

/**
 * Initialize profile page
 */
async function initProfilePage() {
  const profileForm = document.getElementById('profile-form');
  const passwordForm = document.getElementById('password-form');

  if (!profileForm || !passwordForm) {
    console.error('Profile: Form elements not found, retrying...');
    // Retry after a short delay
    setTimeout(() => {
      const retryProfileForm = document.getElementById('profile-form');
      const retryPasswordForm = document.getElementById('password-form');
      if (!retryProfileForm || !retryPasswordForm) {
        console.error('Profile: Form elements still not found after retry');
        return;
      }
      initProfilePageWithForms(retryProfileForm, retryPasswordForm);
    }, 100);
    return;
  }

  initProfilePageWithForms(profileForm, passwordForm);
}

/**
 * Initialize profile page with the found forms
 */
async function initProfilePageWithForms(profileForm, passwordForm) {
  const firstInit = !profileForm.dataset.initialized;

  // Load user profile data
  await loadUserProfile();

  if (firstInit) {
    // Setup event listeners
    profileForm.addEventListener('submit', handleProfileFormSubmit);
    passwordForm.addEventListener('submit', handlePasswordFormSubmit);
    profileForm.dataset.initialized = 'true';
    passwordForm.dataset.initialized = 'true';
    console.log('Profile: Forms initialized and event listeners attached');

    // T-24.010: Attach PasswordStrengthIndicator to the new-password field.
    // The submit button for the password form is the last button inside #password-form.
    const newPwdEl  = passwordForm.querySelector('#new-password');
    const submitBtn = passwordForm.querySelector('button[type="submit"]');
    if (newPwdEl && submitBtn) {
      PasswordStrengthIndicator.attach(newPwdEl, submitBtn);
    }
  } else {
    console.log('Profile: Forms already initialized, data refreshed');
  }

  // Two-Factor Authentication panel (ADR-011 S5)
  initMfaPanel(firstInit);
}

/**
 * Load user profile data from the server
 */
async function loadUserProfile() {
  try {
    const response = await apiFetch('/auth/me');
    if (!response.ok) {
      throw new Error('Failed to load profile data');
    }

    const user = await response.json();
    console.log('Profile: User data loaded', user);

    // Populate form fields
    setInputValue('profile-full-name', user.full_name || '');
    setInputValue('profile-display-name', user.display_name || '');
    setInputValue('profile-email', user.email || '');
    setInputValue('profile-phone', user.phone || '');

    // Set avatar initials
    const initials = getInitials(user.display_name || user.full_name || user.email);
    setTextContent('profile-avatar-initials', initials);

    // Populate overview section
    const displayName = user.display_name || user.full_name || user.email.split('@')[0];
    setTextContent('profile-overview-name', displayName);

    const overviewEmailEl = document.getElementById('profile-overview-email');
    if (overviewEmailEl) {
      const emailSpan = overviewEmailEl.querySelector('span');
      if (emailSpan) {
        emailSpan.textContent = user.email;
      }
    }

    // Update status
    const statusElements = [
      document.getElementById('profile-overview-status'),
      document.getElementById('profile-status')
    ];

    statusElements.forEach(statusElement => {
      if (statusElement && user.is_active !== undefined) {
        if (user.is_active) {
          statusElement.innerHTML = '<i class="ph ph-check-circle-fill"></i> Active';
          statusElement.className = 'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-700 border border-green-200';
        } else {
          statusElement.innerHTML = '<i class="ph ph-x-circle-fill"></i> Inactive';
          statusElement.className = 'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-red-100 text-red-700 border border-red-200';
        }
      }
    });

    // Display organization information
    setTextContent('profile-tenant', user.tenant_id || 'Not assigned');
    setTextContent('profile-company', user.default_company_id || 'Not assigned');
    setTextContent('profile-branch', user.branch_id || 'Not assigned');
    setTextContent('profile-department', user.department_id || 'Not assigned');

    // Display account stats
    setTextContent('profile-user-id', user.id ? user.id.substring(0, 8) + '...' : '-');

    // Format and display dates
    if (user.created_at) {
      const createdDate = new Date(user.created_at);
      setTextContent('profile-created', formatDate(createdDate));
      setTextContent('profile-overview-joined', formatDate(createdDate));
    }

    if (user.last_login) {
      const lastLoginDate = new Date(user.last_login);
      setTextContent('profile-last-login', formatRelativeTime(lastLoginDate));
      setTextContent('profile-overview-last-active', formatRelativeTime(lastLoginDate));
    }

    if (user.updated_at) {
      const updatedDate = new Date(user.updated_at);
      setTextContent('profile-updated', formatRelativeTime(updatedDate));
    }

    // Display role
    let roleText = 'User';
    if (user.is_superuser) {
      roleText = 'Super Admin';
    } else if (Array.isArray(user.roles) && user.roles.length > 0) {
      roleText = user.roles.slice(0, 2).join(', ');
      if (user.roles.length > 2) {
        roleText += ` +${user.roles.length - 2} more`;
      }
    }
    setTextContent('profile-role', roleText);
    setTextContent('profile-overview-role', roleText);

  } catch (error) {
    console.error('Profile: Failed to load user profile', error);
    showAlert('Unable to load profile data. Please try refreshing the page.', 'danger');
  }
}

/**
 * Get initials from name
 */
function getInitials(name) {
  if (!name) return 'U';

  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) {
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  }
  return name.substring(0, 2).toUpperCase();
}

/**
 * Handle profile form submission
 */
async function handleProfileFormSubmit(event) {
  event.preventDefault();
  console.log('Profile: Profile form submit triggered');

  const payload = {
    full_name: getInputValue('profile-full-name'),
    display_name: getInputValue('profile-display-name'),
    email: getInputValue('profile-email'),
    phone: getInputValue('profile-phone')
  };

  // Remove empty values
  Object.keys(payload).forEach(key => {
    if (payload[key] === '') {
      payload[key] = null;
    }
  });

  console.log('Profile: Updating profile with payload:', payload);

  try {
    const response = await apiFetch('/auth/me', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (response.ok) {
      const updatedUser = await response.json();
      console.log('Profile: Profile updated successfully', updatedUser);
      showAlert('Profile updated successfully!', 'success');

      // Update localStorage user data
      const storedUser = localStorage.getItem('user');
      if (storedUser) {
        try {
          const userData = JSON.parse(storedUser);
          Object.assign(userData, payload);
          localStorage.setItem('user', JSON.stringify(userData));
        } catch (e) {
          console.warn('Profile: Could not update stored user data', e);
        }
      }

      // Reload profile to show updated data
      await loadUserProfile();

      // Update navbar display name
      const userNameEl = document.getElementById('user-name');
      if (userNameEl) {
        const displayName = updatedUser.display_name || updatedUser.full_name || updatedUser.email.split('@')[0];
        userNameEl.textContent = displayName;
      }
    } else {
      const error = await safeJson(response);
      console.error('Profile: Failed to update profile. Response:', response.status, error);
      showAlert((error && error.detail) || 'Failed to update profile.', 'danger');
    }
  } catch (error) {
    console.error('Profile: Exception while updating profile:', error);
    showAlert('Failed to update profile. Please try again.', 'danger');
  }
}

/**
 * Handle password form submission
 */
async function handlePasswordFormSubmit(event) {
  event.preventDefault();
  console.log('Profile: Password form submit triggered');

  const currentPassword = getInputValue('current-password');
  const newPassword = getInputValue('new-password');
  const confirmPassword = getInputValue('confirm-password');

  // Validation
  if (!currentPassword || !newPassword || !confirmPassword) {
    showAlert('All password fields are required.', 'warning');
    return;
  }

  if (newPassword !== confirmPassword) {
    showAlert('New password and confirmation do not match.', 'warning');
    return;
  }

  if (newPassword.length < 8) {
    showAlert('New password must be at least 8 characters long.', 'warning');
    return;
  }

  if (newPassword === currentPassword) {
    showAlert('New password must be different from current password.', 'warning');
    return;
  }

  const payload = {
    current_password: currentPassword,
    new_password: newPassword,
    confirm_password: confirmPassword
  };

  console.log('Profile: Changing password...');

  try {
    const response = await apiFetch('/auth/change-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (response.ok) {
      console.log('Profile: Password changed successfully');
      showAlert('Password changed successfully!', 'success');

      // Clear password form
      document.getElementById('current-password').value = '';
      document.getElementById('new-password').value = '';
      document.getElementById('confirm-password').value = '';
    } else {
      const error = await safeJson(response);
      console.error('Profile: Failed to change password. Response:', response.status, error);
      showAlert((error && error.detail) || 'Failed to change password.', 'danger');
    }
  } catch (error) {
    console.error('Profile: Exception while changing password:', error);
    showAlert('Failed to change password. Please try again.', 'danger');
  }
}

/**
 * Format date for display (e.g., "Jan 15, 2024")
 */
function formatDate(date) {
  return date.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}

/**
 * Format relative time (e.g., "2 days ago", "Just now")
 */
function formatRelativeTime(date) {
  const now = new Date();
  const diff = now - date;
  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (seconds < 60) {
    return 'Just now';
  } else if (minutes < 60) {
    return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`;
  } else if (hours < 24) {
    return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
  } else if (days < 7) {
    return `${days} day${days !== 1 ? 's' : ''} ago`;
  } else {
    return formatDate(date);
  }
}

/**
 * Show alert notification
 */
function showAlert(message, tone = 'info') {
  const container = document.createElement('div');
  const toneClasses = getToneClasses(tone);

  container.className = `fixed top-4 right-4 max-w-md z-[60] flex items-start gap-3 border rounded-lg shadow-lg p-4 ${toneClasses}`;
  container.innerHTML = `
    <i class="ph ${getToneIcon(tone)} flex-shrink-0 mt-0.5"></i>
    <div class="flex-1">${message}</div>
    <button type="button" class="text-lg hover:opacity-70" data-alert-close>
      <i class="ph ph-x"></i>
    </button>
  `;

  container.querySelector('[data-alert-close]')?.addEventListener('click', () => container.remove());

  document.body.appendChild(container);

  window.setTimeout(() => {
    container.remove();
  }, 5000);
}

/**
 * Get tone-specific CSS classes
 */
function getToneClasses(tone) {
  switch (tone) {
    case 'success':
      return 'bg-green-50 border-green-200 text-green-700';
    case 'danger':
      return 'bg-red-50 border-red-200 text-red-700';
    case 'warning':
      return 'bg-yellow-50 border-yellow-200 text-yellow-700';
    default:
      return 'bg-blue-50 border-blue-200 text-blue-700';
  }
}

/**
 * Get tone-specific icon
 */
function getToneIcon(tone) {
  switch (tone) {
    case 'success':
      return 'ph-check-circle';
    case 'danger':
      return 'ph-warning-circle';
    case 'warning':
      return 'ph-warning';
    default:
      return 'ph-info';
  }
}

/**
 * Utility: Set input value
 */
function setInputValue(id, value) {
  const element = document.getElementById(id);
  if (element) {
    element.value = value;
  }
}

/**
 * Utility: Get input value
 */
function getInputValue(id) {
  const element = document.getElementById(id);
  return element ? element.value.trim() : '';
}

/**
 * Utility: Set text content
 */
function setTextContent(id, value) {
  const element = document.getElementById(id);
  if (element) {
    element.textContent = value || '—';
  }
}

/**
 * Utility: Safely parse JSON response
 */
async function safeJson(response) {
  try {
    return await response.json();
  } catch (_) {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Two-Factor Authentication (ADR-011 S5) — enroll / verify / remove MFA factors.
// Talks to the platform /api/v1/mfa/* endpoints (S4).
// ---------------------------------------------------------------------------

let mfaPending = null; // { factorId, target } while a code is awaiting verification

function initMfaPanel(firstInit) {
  const list = document.getElementById('mfa-list');
  if (!list) return; // template without the MFA card — nothing to do

  if (firstInit) {
    document.getElementById('mfa-send-btn')?.addEventListener('click', mfaSendCode);
    document.getElementById('mfa-verify-btn')?.addEventListener('click', mfaVerifyCode);
    document.getElementById('mfa-resend-btn')?.addEventListener('click', mfaResendCode);
    document.getElementById('mfa-cancel-btn')?.addEventListener('click', mfaCancel);
    const typeSel = document.getElementById('mfa-type');
    typeSel?.addEventListener('change', () => {
      const t = document.getElementById('mfa-target');
      if (t) t.placeholder = typeSel.value === 'phone_otp' ? '+15551234567' : 'you@example.com';
    });
  }
  loadMfaFactors();
  loadTrustedDevices();
}

async function loadTrustedDevices() {
  const section = document.getElementById('trusted-devices-section');
  const list = document.getElementById('trusted-devices-list');
  if (!section || !list) return;

  try {
    const res = await apiFetch('/mfa/devices');
    if (!res.ok) {
      section.classList.add('hidden');
      return;
    }
    renderTrustedDevices((await res.json()) || []);
  } catch (_) {
    section.classList.add('hidden');
  }
}

function renderTrustedDevices(devices) {
  const section = document.getElementById('trusted-devices-section');
  const list = document.getElementById('trusted-devices-list');
  if (!section || !list) return;

  // Nothing remembered — keep the card focused on enrollment.
  if (!devices.length) {
    section.classList.add('hidden');
    list.innerHTML = '';
    return;
  }
  section.classList.remove('hidden');

  list.innerHTML = devices.map((d) => `
      <div class="flex items-center justify-between gap-3 border border-gray-200 rounded-lg px-4 py-3">
        <div class="flex items-center gap-3 min-w-0">
          <i class="ph ph-desktop text-purple-600 text-xl"></i>
          <div class="min-w-0">
            <p class="text-sm font-medium text-gray-900 truncate">${escapeHtml(d.label || 'Unknown device')}</p>
            <p class="text-xs text-gray-500">
              Last used ${formatDeviceDate(d.last_used_at)} · Expires ${formatDeviceDate(d.expires_at)}
            </p>
          </div>
        </div>
        <button type="button" data-device-remove="${escapeHtml(d.id)}"
          class="px-3 py-1.5 text-red-600 hover:bg-red-50 rounded-lg transition text-sm font-medium flex items-center gap-1 whitespace-nowrap">
          <i class="ph ph-trash"></i> Remove
        </button>
      </div>`).join('');

  list.querySelectorAll('[data-device-remove]').forEach((btn) => {
    btn.addEventListener('click', () => trustedDeviceRemove(btn.getAttribute('data-device-remove')));
  });
}

function formatDeviceDate(value) {
  if (!value) return 'never';
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? 'unknown' : d.toLocaleDateString();
}

async function trustedDeviceRemove(deviceId) {
  if (!deviceId) return;
  try {
    const res = await apiFetch(`/mfa/devices/${deviceId}`, { method: 'DELETE' });
    if (res.ok) {
      showAlert('Device removed. It will be asked for a code next time.', 'success');
      loadTrustedDevices();
    } else {
      const body = await safeJson(res);
      showAlert((body && body.detail) || 'Could not remove that device.', 'danger');
    }
  } catch (_) {
    showAlert('Could not remove that device.', 'danger');
  }
}

async function loadMfaFactors() {
  const list = document.getElementById('mfa-list');
  if (!list) return;
  try {
    const res = await apiFetch('/mfa/factors');
    if (!res.ok) {
      list.innerHTML = '<p class="text-sm text-gray-400">Could not load methods.</p>';
      return;
    }
    renderMfaFactors((await res.json()) || []);
  } catch (_) {
    list.innerHTML = '<p class="text-sm text-gray-400">Could not load methods.</p>';
  }
}

function renderMfaFactors(factors) {
  const list = document.getElementById('mfa-list');
  if (!list) return;
  if (!factors.length) {
    list.innerHTML = '<p class="text-sm text-gray-400">No methods enrolled yet.</p>';
    return;
  }
  list.innerHTML = factors.map((f) => {
    const isEmail = f.factor_type === 'email_otp';
    const icon = isEmail ? 'ph-envelope-simple' : 'ph-device-mobile';
    const label = isEmail ? 'Email' : 'Phone';
    const badge = f.is_active
      ? '<span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-green-100 text-green-700">Active</span>'
      : '<span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-700">Pending</span>';
    return `
      <div class="flex items-center justify-between gap-3 border border-gray-200 rounded-lg px-4 py-3">
        <div class="flex items-center gap-3 min-w-0">
          <i class="ph ${icon} text-purple-600 text-xl"></i>
          <div class="min-w-0">
            <p class="text-sm font-medium text-gray-900 truncate">${label} · ${escapeHtml(f.target)}</p>
            <div class="mt-0.5">${badge}</div>
          </div>
        </div>
        <button type="button" data-mfa-remove="${escapeHtml(f.id)}"
          class="px-3 py-1.5 text-red-600 hover:bg-red-50 rounded-lg transition text-sm font-medium flex items-center gap-1 whitespace-nowrap">
          <i class="ph ph-trash"></i> Remove
        </button>
      </div>`;
  }).join('');
  list.querySelectorAll('[data-mfa-remove]').forEach((btn) => {
    btn.addEventListener('click', () => mfaRemove(btn.getAttribute('data-mfa-remove')));
  });
}

async function mfaSendCode() {
  const factorType = document.getElementById('mfa-type')?.value || 'email_otp';
  const target = getInputValue('mfa-target');
  if (!target) { showAlert('Enter an email or phone number.', 'warning'); return; }

  const btn = document.getElementById('mfa-send-btn');
  setBusy(btn, true);
  try {
    const res = await apiFetch('/mfa/factors', {
      method: 'POST',
      body: JSON.stringify({ factor_type: factorType, target }),
    });
    const body = await safeJson(res);
    if (res.ok) {
      mfaPending = { factorId: body.factor_id, target };
      showMfaVerify(target);
      showAlert('Verification code sent.', 'success');
      loadMfaFactors(); // surface the new Pending factor immediately
    } else if (res.status === 409) {
      showAlert('That method is already enrolled and active.', 'warning');
      loadMfaFactors();
    } else {
      showAlert((body && body.detail) || 'Could not send the code.', 'danger');
    }
  } catch (_) {
    showAlert('Could not send the code.', 'danger');
  } finally {
    setBusy(btn, false);
  }
}

async function mfaVerifyCode() {
  if (!mfaPending) return;
  const code = getInputValue('mfa-code');
  if (!code) { showAlert('Enter the code.', 'warning'); return; }

  const btn = document.getElementById('mfa-verify-btn');
  setBusy(btn, true);
  try {
    const res = await apiFetch(`/mfa/factors/${mfaPending.factorId}/verify`, {
      method: 'POST',
      body: JSON.stringify({ code }),
    });
    const body = await safeJson(res);
    if (res.ok) {
      showAlert('Two-factor method activated.', 'success');
      mfaCancel();
      setInputValue('mfa-target', '');
      loadMfaFactors();
    } else {
      showAlert((body && body.detail) || 'Incorrect or expired code.', 'danger');
    }
  } catch (_) {
    showAlert('Could not verify the code.', 'danger');
  } finally {
    setBusy(btn, false);
  }
}

async function mfaResendCode() {
  if (!mfaPending) return;
  const btn = document.getElementById('mfa-resend-btn');
  setBusy(btn, true);
  try {
    const res = await apiFetch(`/mfa/factors/${mfaPending.factorId}/resend`, { method: 'POST' });
    const body = await safeJson(res);
    showAlert(res.ok ? 'A new code is on its way.' : ((body && body.detail) || 'Could not resend the code.'),
      res.ok ? 'success' : 'danger');
  } catch (_) {
    showAlert('Could not resend the code.', 'danger');
  } finally {
    setBusy(btn, false);
  }
}

async function mfaRemove(factorId) {
  if (!factorId) return;
  try {
    const res = await apiFetch(`/mfa/factors/${factorId}`, { method: 'DELETE' });
    if (res.ok) {
      showAlert('Method removed.', 'success');
      if (mfaPending && mfaPending.factorId === factorId) mfaCancel();
      loadMfaFactors();
      // Removing a factor also revokes trusted devices server-side (D4), so the
      // list on screen would otherwise still show devices that no longer exist.
      loadTrustedDevices();
    } else {
      const body = await safeJson(res);
      showAlert((body && body.detail) || 'Could not remove the method.', 'danger');
    }
  } catch (_) {
    showAlert('Could not remove the method.', 'danger');
  }
}

function showMfaVerify(target) {
  const box = document.getElementById('mfa-verify');
  setTextContent('mfa-verify-target', target);
  if (box) box.classList.remove('hidden');
  const codeEl = document.getElementById('mfa-code');
  if (codeEl) { codeEl.value = ''; codeEl.focus(); }
}

function mfaCancel() {
  mfaPending = null;
  document.getElementById('mfa-verify')?.classList.add('hidden');
  setInputValue('mfa-code', '');
}

function setBusy(btn, busy) {
  if (!btn) return;
  btn.disabled = busy;
  btn.classList.toggle('opacity-60', busy);
  btn.classList.toggle('cursor-not-allowed', busy);
}

function escapeHtml(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ));
}
