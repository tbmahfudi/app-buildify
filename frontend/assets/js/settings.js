import { apiFetch } from './api.js';

document.addEventListener('route:loaded', async (e) => {
  if (e.detail.route === 'settings') {
    await initSettings();
  }
});

async function initSettings() {
  // Load user settings
  await loadUserSettings();
  
  // Setup user settings form
  const userForm = document.getElementById('user-settings-form');
  userForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    await saveUserSettings();
  });

  // Setup live preview
  setupLivePreview();

  // Check if user is admin and load tenant settings
  const userStr = localStorage.getItem('user');
  if (userStr) {
    const user = JSON.parse(userStr);
    if (user.roles && (user.roles.includes('admin') || user.is_superuser)) {
      document.getElementById('tenant-settings-card').style.display = 'block';
      await loadTenantSettings();
      
      const tenantForm = document.getElementById('tenant-settings-form');
      tenantForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        await saveTenantSettings();
      });
    }
  }
}

/**
 * Load user settings
 */
async function loadUserSettings() {
  try {
    const response = await apiFetch('/settings/user');
    const settings = await response.json();

    document.getElementById('setting-theme').value = settings.theme || 'light';
    document.getElementById('setting-density').value = settings.density || 'normal';
    document.getElementById('setting-language').value = settings.language || 'en';
    document.getElementById('setting-timezone').value = settings.timezone || 'UTC';

    updatePreview();

    if (settings.updated_at) {
      document.getElementById('settings-last-updated').textContent = 
        `Last updated: ${new Date(settings.updated_at).toLocaleString()}`;
    }
  } catch (error) {
    console.error('Failed to load user settings:', error);
  }
}

/**
 * Save user settings
 */
async function saveUserSettings() {
  const settings = {
    theme: document.getElementById('setting-theme').value,
    density: document.getElementById('setting-density').value,
    language: document.getElementById('setting-language').value,
    timezone: document.getElementById('setting-timezone').value
  };

  try {
    const response = await apiFetch('/settings/user', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings)
    });

    if (response.ok) {
      showAlert('Settings saved successfully!', 'success');
      
      // Apply theme immediately
      applyTheme(settings.theme);
    } else {
      const error = await response.json();
      showAlert(error.detail || 'Failed to save settings', 'danger');
    }
  } catch (error) {
    showAlert('Failed to save settings: ' + error.message, 'danger');
  }
}

/**
 * Load tenant settings
 */
async function loadTenantSettings() {
  try {
    const response = await apiFetch('/settings/tenant');
    const settings = await response.json();

    document.getElementById('tenant-name').value = settings.tenant_name || '';
    document.getElementById('tenant-primary-color').value = settings.primary_color || '#0066cc';
    document.getElementById('tenant-secondary-color').value = settings.secondary_color || '#6c757d';
    document.getElementById('tenant-logo-url').value = settings.logo_url || '';
  } catch (error) {
    console.error('Failed to load tenant settings:', error);
  }
}

/**
 * Save tenant settings
 */
async function saveTenantSettings() {
  const settings = {
    tenant_name: document.getElementById('tenant-name').value,
    primary_color: document.getElementById('tenant-primary-color').value,
    secondary_color: document.getElementById('tenant-secondary-color').value,
    logo_url: document.getElementById('tenant-logo-url').value
  };

  try {
    const response = await apiFetch('/settings/tenant', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings)
    });

    if (response.ok) {
      showAlert('Tenant settings saved successfully!', 'success');
      
      // Apply branding immediately
      applyBranding(settings);
    } else {
      const error = await response.json();
      showAlert(error.detail || 'Failed to save tenant settings', 'danger');
    }
  } catch (error) {
    showAlert('Failed to save tenant settings: ' + error.message, 'danger');
  }
}

/**
 * Setup live preview
 */
function setupLivePreview() {
  const fields = ['setting-theme', 'setting-density', 'setting-language', 'setting-timezone'];
  
  fields.forEach(fieldId => {
    const field = document.getElementById(fieldId);
    field.addEventListener('change', updatePreview);
  });
}

/**
 * Update preview
 */
function updatePreview() {
  document.getElementById('preview-theme').textContent = 
    document.getElementById('setting-theme').value;
  document.getElementById('preview-density').textContent = 
    document.getElementById('setting-density').value;
  document.getElementById('preview-language').textContent = 
    document.getElementById('setting-language').selectedOptions[0].text;
  document.getElementById('preview-timezone').textContent = 
    document.getElementById('setting-timezone').value;
}

/**
 * Apply theme
 */
function applyTheme(theme) {
  if (theme === 'dark') {
    document.documentElement.setAttribute('data-bs-theme', 'dark');
    document.body.classList.add('bg-dark', 'text-light');
  } else {
    document.documentElement.removeAttribute('data-bs-theme');
    document.body.classList.remove('bg-dark', 'text-light');
  }
}

/**
 * Apply branding
 */
function applyBranding(settings) {
  if (settings.primary_color) {
    document.documentElement.style.setProperty('--bs-primary', settings.primary_color);
  }
  if (settings.secondary_color) {
    document.documentElement.style.setProperty('--bs-secondary', settings.secondary_color);
  }
}

/**
 * Show alert message
 */
function showAlert(message, type) {
  const alert = document.createElement('div');
  alert.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
  alert.style.zIndex = '9999';
  alert.innerHTML = `
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  `;
  
  document.body.appendChild(alert);
  
  setTimeout(() => {
    alert.remove();
  }, 5000);
}