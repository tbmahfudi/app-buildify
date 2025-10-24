import { apiFetch } from './api.js';

document.addEventListener('route:loaded', (event) => {
  if (event.detail.route === 'settings') {
    initSettingsPage();
  }
});

async function initSettingsPage() {
  const userForm = document.getElementById('user-settings-form');
  if (!userForm) {
    return;
  }

  const firstInit = !userForm.dataset.initialized;

  await loadUserSettings();

  if (firstInit) {
    setupLivePreview();
    userForm.addEventListener('submit', handleUserFormSubmit);
    userForm.dataset.initialized = 'true';
  } else {
    updatePreview();
  }

  const currentUser = parseUser(localStorage.getItem('user'));
  const tenantCard = document.getElementById('tenant-settings-card');

  if (tenantCard && userHasAdminAccess(currentUser)) {
    tenantCard.classList.remove('hidden');
    const tenantForm = document.getElementById('tenant-settings-form');
    const tenantFirstInit = tenantForm && !tenantForm.dataset.initialized;

    await loadTenantSettings();

    if (tenantForm && tenantFirstInit) {
      tenantForm.addEventListener('submit', handleTenantFormSubmit);
      tenantForm.dataset.initialized = 'true';
    }
  } else if (tenantCard) {
    tenantCard.classList.add('hidden');
  }
}

async function loadUserSettings() {
  try {
    const response = await apiFetch('/settings/user');
    const settings = await response.json();

    setSelectValue('setting-theme', settings.theme, 'light');
    setSelectValue('setting-density', settings.density, 'normal');
    setSelectValue('setting-language', settings.language, 'en');
    setSelectValue('setting-timezone', settings.timezone, 'UTC');

    updatePreview();

    if (settings.updated_at) {
      const lastUpdated = document.getElementById('settings-last-updated');
      if (lastUpdated) {
        lastUpdated.textContent = `Last updated: ${new Date(settings.updated_at).toLocaleString()}`;
      }
    }
  } catch (error) {
    console.error('Failed to load user settings:', error);
    showAlert('Unable to load user settings. Please try again.', 'danger');
  }
}

async function handleUserFormSubmit(event) {
  event.preventDefault();

  const payload = {
    theme: getSelectValue('setting-theme'),
    density: getSelectValue('setting-density'),
    language: getSelectValue('setting-language'),
    timezone: getSelectValue('setting-timezone'),
  };

  try {
    const response = await apiFetch('/settings/user', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (response.ok) {
      showAlert('Settings saved successfully!', 'success');
      applyTheme(payload.theme);
    } else {
      const error = await safeJson(response);
      showAlert((error && error.detail) || 'Failed to save settings.', 'danger');
    }
  } catch (error) {
    console.error('Failed to save user settings:', error);
    showAlert('Failed to save settings. Please try again.', 'danger');
  }
}

async function loadTenantSettings() {
  try {
    const response = await apiFetch('/settings/tenant');
    const settings = await response.json();

    setInputValue('tenant-name', settings.tenant_name || '');
    setInputValue('tenant-primary-color', settings.primary_color || '#0066cc');
    setInputValue('tenant-secondary-color', settings.secondary_color || '#6c757d');
    setInputValue('tenant-logo-url', settings.logo_url || '');
  } catch (error) {
    console.error('Failed to load tenant settings:', error);
    showAlert('Unable to load tenant settings. Please try again.', 'warning');
  }
}

async function handleTenantFormSubmit(event) {
  event.preventDefault();

  const payload = {
    tenant_name: getInputValue('tenant-name'),
    primary_color: getInputValue('tenant-primary-color'),
    secondary_color: getInputValue('tenant-secondary-color'),
    logo_url: getInputValue('tenant-logo-url'),
  };

  try {
    const response = await apiFetch('/settings/tenant', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (response.ok) {
      showAlert('Tenant settings saved successfully!', 'success');
      applyBranding(payload);
    } else {
      const error = await safeJson(response);
      showAlert((error && error.detail) || 'Failed to save tenant settings.', 'danger');
    }
  } catch (error) {
    console.error('Failed to save tenant settings:', error);
    showAlert('Failed to save tenant settings. Please try again.', 'danger');
  }
}

function setupLivePreview() {
  const fields = ['setting-theme', 'setting-density', 'setting-language', 'setting-timezone'];
  fields.forEach((id) => {
    const element = document.getElementById(id);
    if (element) {
      element.addEventListener('change', updatePreview);
    }
  });

  updatePreview();
}

function updatePreview() {
  setTextContent('preview-theme', getSelectValue('setting-theme'));
  setTextContent('preview-density', getSelectValue('setting-density'));

  const languageSelect = document.getElementById('setting-language');
  setTextContent('preview-language', languageSelect?.selectedOptions[0]?.text || '');
  setTextContent('preview-timezone', getSelectValue('setting-timezone'));
}

function applyTheme(theme) {
  if (theme === 'dark') {
    document.documentElement.setAttribute('data-theme', 'dark');
    document.body.classList.add('bg-gray-900', 'text-white');
  } else {
    document.documentElement.removeAttribute('data-theme');
    document.body.classList.remove('bg-gray-900', 'text-white');
  }
}

function applyBranding(settings) {
  if (settings.primary_color) {
    document.documentElement.style.setProperty('--color-primary', settings.primary_color);
  }
  if (settings.secondary_color) {
    document.documentElement.style.setProperty('--color-secondary', settings.secondary_color);
  }
}

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

function setSelectValue(id, value, fallback) {
  const element = document.getElementById(id);
  if (element) {
    element.value = value || fallback;
  }
}

function getSelectValue(id) {
  const element = document.getElementById(id);
  return element ? element.value : '';
}

function setInputValue(id, value) {
  const element = document.getElementById(id);
  if (element) {
    element.value = value;
  }
}

function getInputValue(id) {
  const element = document.getElementById(id);
  return element ? element.value.trim() : '';
}

function setTextContent(id, value) {
  const element = document.getElementById(id);
  if (element) {
    element.textContent = value || '—';
  }
}

function parseUser(raw) {
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw);
  } catch (error) {
    console.warn('Unable to parse stored user', error);
    return null;
  }
}

function userHasAdminAccess(user) {
  if (!user) {
    return false;
  }

  if (user.is_superuser) {
    return true;
  }

  if (Array.isArray(user.roles)) {
    return user.roles.some((role) => role && role.toLowerCase() === 'admin');
  }

  return false;
}

async function safeJson(response) {
  try {
    return await response.json();
  } catch (_) {
    return null;
  }
}
