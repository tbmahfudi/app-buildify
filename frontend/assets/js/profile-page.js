import { apiFetch } from './api.js';

// Listen for route changes to profile page
document.addEventListener('route:loaded', (event) => {
  if (event.detail.route === 'profile') {
    // Use setTimeout to ensure DOM is fully ready after innerHTML update
    setTimeout(() => initProfilePage(), 0);
  }
});

/**
 * Initialize profile page
 */
async function initProfilePage() {
  const profileForm = document.getElementById('profile-form');
  const passwordForm = document.getElementById('password-form');

  if (!profileForm || !passwordForm) {
    console.error('Profile: Form elements not found');
    return;
  }

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
  } else {
    console.log('Profile: Forms already initialized, data refreshed');
  }
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
    setInputValue('profile-email', user.email || '');
    setInputValue('profile-phone', user.phone || '');

    // Display organization information
    setTextContent('profile-tenant', user.tenant_id || 'Not assigned');
    setTextContent('profile-company', user.default_company_id || 'Not assigned');
    setTextContent('profile-branch', user.branch_id || 'Not assigned');
    setTextContent('profile-department', user.department_id || 'Not assigned');

    // Display account information
    const statusElement = document.getElementById('profile-status');
    if (statusElement && user.is_active !== undefined) {
      if (user.is_active) {
        statusElement.innerHTML = '<i class="bi bi-check-circle-fill"></i> Active';
        statusElement.className = 'inline-flex items-center gap-1.5 text-green-400';
      } else {
        statusElement.innerHTML = '<i class="bi bi-x-circle-fill"></i> Inactive';
        statusElement.className = 'inline-flex items-center gap-1.5 text-red-400';
      }
    }

    // Format and display dates
    if (user.created_at) {
      const createdDate = new Date(user.created_at);
      setTextContent('profile-created', formatDate(createdDate));
    }

    if (user.last_login) {
      const lastLoginDate = new Date(user.last_login);
      setTextContent('profile-last-login', formatDate(lastLoginDate));
    }

    // Display role
    if (user.is_superuser) {
      setTextContent('profile-role', 'Super Admin');
    } else if (Array.isArray(user.roles) && user.roles.length > 0) {
      setTextContent('profile-role', user.roles.join(', '));
    } else {
      setTextContent('profile-role', 'User');
    }

  } catch (error) {
    console.error('Profile: Failed to load user profile', error);
    showAlert('Unable to load profile data. Please try refreshing the page.', 'danger');
  }
}

/**
 * Handle profile form submission
 */
async function handleProfileFormSubmit(event) {
  event.preventDefault();
  console.log('Profile: Profile form submit triggered');

  const payload = {
    full_name: getInputValue('profile-full-name'),
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
 * Format date for display
 */
function formatDate(date) {
  const now = new Date();
  const diff = now - date;
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));

  if (days === 0) {
    return 'Today';
  } else if (days === 1) {
    return 'Yesterday';
  } else if (days < 7) {
    return `${days} days ago`;
  } else {
    return date.toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
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
    <i class="bi ${getToneIcon(tone)} flex-shrink-0 mt-0.5"></i>
    <div class="flex-1">${message}</div>
    <button type="button" class="text-lg hover:opacity-70" data-alert-close>
      <i class="bi bi-x"></i>
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
      return 'bi-check-circle';
    case 'danger':
      return 'bi-exclamation-circle';
    case 'warning':
      return 'bi-exclamation-triangle';
    default:
      return 'bi-info-circle';
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
