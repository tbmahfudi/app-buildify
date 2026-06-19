import { apiFetch } from './api.js';
import { positionSidebarToggle } from './app.js';
import FlexSelect from './components/flex-select.js';

// ---------------------------------------------------------------------------
// FlexSelect instances — keyed by field id (without the "-container" suffix)
// ---------------------------------------------------------------------------
const flexSelects = new Map();

// Options for every settings select field
const SELECT_OPTIONS = {
  'setting-theme': [
    { value: 'light',  label: 'Light' },
    { value: 'dark',   label: 'Dark'  },
  ],
  'setting-density': [
    { value: 'comfortable', label: 'Comfortable' },
    { value: 'normal',      label: 'Normal'      },
    { value: 'compact',     label: 'Compact'     },
  ],
  'setting-sidebar-state': [
    { value: 'expanded',  label: 'Expanded (Full menu)'   },
    { value: 'collapsed', label: 'Collapsed (Icons only)' },
  ],
  'setting-toggle-position': [
    { value: 'sidebar-header', label: 'Sidebar Header'         },
    { value: 'before-logo',    label: 'Before Logo'            },
    { value: 'between',        label: 'Between Logo & Title'   },
    { value: 'after-title',    label: 'After Platform Title'   },
  ],
  'setting-language': [
    { value: 'en', label: 'English'                        },
    { value: 'es', label: 'Español (Spanish)'              },
    { value: 'fr', label: 'Français (French)'              },
    { value: 'de', label: 'Deutsch (German)'               },
    { value: 'id', label: 'Bahasa Indonesia (Indonesian)'  },
  ],
  'setting-timezone': [
    { value: 'UTC',                 label: 'UTC'           },
    { value: 'America/New_York',    label: 'Eastern Time'  },
    { value: 'America/Chicago',     label: 'Central Time'  },
    { value: 'America/Los_Angeles', label: 'Pacific Time'  },
    { value: 'Europe/London',       label: 'London'        },
    { value: 'Asia/Tokyo',          label: 'Tokyo'         },
  ],
};

// Initialize settings on app load
document.addEventListener('DOMContentLoaded', () => {
  initGlobalSettings();
});

// Also listen for route changes to settings page
document.addEventListener('route:loaded', (event) => {
  if (event.detail.route === 'settings') {
    // Use setTimeout to ensure DOM is fully ready after innerHTML update
    setTimeout(() => initSettingsPage(), 0);
  }
});

/**
 * Create FlexSelect instances for every settings field.
 * Called on each route load — destroys any stale instances first since
 * the DOM is re-rendered on each navigation.
 */
function initFlexSelects() {
  flexSelects.forEach((fs) => { try { fs.destroy(); } catch (_) {} });
  flexSelects.clear();

  Object.entries(SELECT_OPTIONS).forEach(([id, options]) => {
    const container = document.getElementById(`${id}-container`);
    if (!container) return;

    const fs = new FlexSelect(container, {
      options,
      searchable: false,
      clearable: false,
      placeholder: 'Select...',
      onChange: () => updatePreview(),
    });
    flexSelects.set(id, fs);
  });
}

/**
 * Load and apply user settings globally on app initialization
 */
async function initGlobalSettings() {
  try {
    const response = await apiFetch('/settings/user');
    if (response.ok) {
      const settings = await response.json();

      // Apply settings to the entire site
      applyAllSettings({
        theme: settings.theme,
        density: settings.density,
        language: settings.language,
        timezone: settings.timezone
      });

      console.log('Settings: Global settings initialized');
    }
  } catch (error) {
    console.warn('Settings: Could not load global settings, using defaults', error);

    // Apply default settings if loading fails
    applyAllSettings({
      theme: 'light',
      density: 'normal',
      language: 'en',
      timezone: 'UTC'
    });
  }
}

async function initSettingsPage() {
  const userForm = document.getElementById('user-settings-form');
  if (!userForm) {
    console.error('Settings: user-settings-form element not found');
    return;
  }

  const firstInit = !userForm.dataset.initialized;

  // Always (re-)create FlexSelect instances — the DOM is re-rendered on each
  // route load so existing element references are stale.
  initFlexSelects();

  await loadUserSettings();

  if (firstInit) {
    setupLivePreview();
    userForm.addEventListener('submit', handleUserFormSubmit);
    userForm.dataset.initialized = 'true';
    console.log('Settings: Form initialized and event listener attached');
  } else {
    updatePreview();
    console.log('Settings: Form already initialized, updated preview only');
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

    // Load sidebar state from localStorage (not from server)
    const sidebarState = localStorage.getItem('sidebarDefaultState') || 'expanded';
    setSelectValue('setting-sidebar-state', sidebarState, 'expanded');

    // Load sidebar toggle position from localStorage
    const togglePosition = localStorage.getItem('sidebarTogglePosition') || 'after-title';
    setSelectValue('setting-toggle-position', togglePosition, 'after-title');

    updatePreview();

    // Apply loaded settings to the site
    applyAllSettings({
      theme: settings.theme,
      density: settings.density,
      language: settings.language,
      timezone: settings.timezone
    });

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
  console.log('Settings: Form submit event triggered');

  const payload = {
    theme: getSelectValue('setting-theme'),
    density: getSelectValue('setting-density'),
    language: getSelectValue('setting-language'),
    timezone: getSelectValue('setting-timezone'),
  };

  // Save sidebar state to localStorage (not sent to server)
  const sidebarState = getSelectValue('setting-sidebar-state');
  localStorage.setItem('sidebarDefaultState', sidebarState);

  // Save sidebar toggle position to localStorage (not sent to server)
  const togglePosition = getSelectValue('setting-toggle-position');
  localStorage.setItem('sidebarTogglePosition', togglePosition);

  // Apply toggle position immediately
  positionSidebarToggle();

  console.log('Settings: Saving user settings with payload:', payload);
  console.log('Settings: Sidebar default state saved to localStorage:', sidebarState);
  console.log('Settings: Sidebar toggle position saved to localStorage:', togglePosition);

  try {
    const response = await apiFetch('/settings/user', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (response.ok) {
      console.log('Settings: User settings saved successfully');
      showAlert('Settings saved successfully!', 'success');

      // Apply all settings to the site immediately
      applyAllSettings(payload);

      // Store settings in localStorage for persistence
      localStorage.setItem('userSettings', JSON.stringify(payload));
    } else {
      const error = await safeJson(response);
      console.error('Settings: Failed to save user settings. Response:', response.status, error);
      showAlert((error && error.detail) || 'Failed to save settings.', 'danger');
    }
  } catch (error) {
    console.error('Settings: Exception while saving user settings:', error);
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
  console.log('Settings: Tenant form submit event triggered');

  const payload = {
    tenant_name: getInputValue('tenant-name'),
    primary_color: getInputValue('tenant-primary-color'),
    secondary_color: getInputValue('tenant-secondary-color'),
    logo_url: getInputValue('tenant-logo-url'),
  };

  console.log('Settings: Saving tenant settings with payload:', payload);

  try {
    const response = await apiFetch('/settings/tenant', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (response.ok) {
      console.log('Settings: Tenant settings saved successfully');
      showAlert('Tenant settings saved successfully!', 'success');
      applyBranding(payload);
    } else {
      const error = await safeJson(response);
      console.error('Settings: Failed to save tenant settings. Response:', response.status, error);
      showAlert((error && error.detail) || 'Failed to save tenant settings.', 'danger');
    }
  } catch (error) {
    console.error('Settings: Exception while saving tenant settings:', error);
    showAlert('Failed to save tenant settings. Please try again.', 'danger');
  }
}

/**
 * Wire up live-preview.  The FlexSelect onChange callbacks already call
 * updatePreview() — this function just triggers an initial render.
 */
function setupLivePreview() {
  updatePreview();
}

function updatePreview() {
  setTextContent('preview-theme',           getSelectLabel('setting-theme'));
  setTextContent('preview-density',         getSelectLabel('setting-density'));
  setTextContent('preview-sidebar-state',   getSelectLabel('setting-sidebar-state'));
  setTextContent('preview-toggle-position', getSelectLabel('setting-toggle-position'));
  setTextContent('preview-language',        getSelectLabel('setting-language'));
  setTextContent('preview-timezone',        getSelectLabel('setting-timezone'));
}

function applyTheme(theme) {
  if (theme === 'dark') {
    document.documentElement.setAttribute('data-theme', 'dark');
    document.documentElement.classList.add('dark'); // For Tailwind dark mode
    document.body.classList.add('bg-gray-900', 'text-white');
  } else {
    document.documentElement.removeAttribute('data-theme');
    document.documentElement.classList.remove('dark'); // For Tailwind dark mode
    document.body.classList.remove('bg-gray-900', 'text-white');
  }
}

function applyDensity(density) {
  // Remove existing density classes
  document.body.classList.remove('density-comfortable', 'density-normal', 'density-compact');

  // Apply new density class
  if (density === 'comfortable') {
    document.body.classList.add('density-comfortable');
    document.documentElement.style.setProperty('--spacing-scale', '1.25');
  } else if (density === 'compact') {
    document.body.classList.add('density-compact');
    document.documentElement.style.setProperty('--spacing-scale', '0.75');
  } else {
    document.body.classList.add('density-normal');
    document.documentElement.style.setProperty('--spacing-scale', '1');
  }
}

function applyLanguage(language) {
  // Set HTML lang attribute
  document.documentElement.lang = language;

  // Store for persistence
  localStorage.setItem('preferredLanguage', language);

  // Change i18next language if initialized
  if (window.i18n && window.i18n.isInitialized) {
    window.i18n.changeLanguage(language);
  }

  console.log(`Settings: Language set to ${language}`);
}

function applyTimezone(timezone) {
  // Store timezone for date formatting throughout the app
  localStorage.setItem('userTimezone', timezone);

  console.log(`Settings: Timezone set to ${timezone}`);
}

function applyAllSettings(settings) {
  console.log('Settings: Applying all settings to the site', settings);

  if (settings.theme) {
    applyTheme(settings.theme);
  }

  if (settings.density) {
    applyDensity(settings.density);
  }

  if (settings.language) {
    applyLanguage(settings.language);
  }

  if (settings.timezone) {
    applyTimezone(settings.timezone);
  }

  console.log('Settings: All settings applied successfully');
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
      return 'ph-check-circle';
    case 'danger':
      return 'ph-warning-circle';
    case 'warning':
      return 'ph-warning';
    default:
      return 'ph-info';
  }
}

// ---------------------------------------------------------------------------
// FlexSelect helpers
// ---------------------------------------------------------------------------

/**
 * Set the selected value on a FlexSelect field.
 */
function setSelectValue(id, value, fallback) {
  const component = flexSelects.get(id);
  if (component) {
    component.setValue(value || fallback);
  }
}

/**
 * Get the current value from a FlexSelect field.
 */
function getSelectValue(id) {
  const component = flexSelects.get(id);
  return component ? (component.getValue() ?? '') : '';
}

/**
 * Get the display label for the currently selected option.
 * Used by updatePreview() to show human-readable text.
 */
function getSelectLabel(id) {
  const value = getSelectValue(id);
  const option = SELECT_OPTIONS[id]?.find((o) => o.value === value);
  return option ? option.label : value;
}

// ---------------------------------------------------------------------------
// Input / text helpers (unchanged from original)
// ---------------------------------------------------------------------------

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


// ── Email Templates  (Wave 2 / Screen 2) ─────────────────────────────────────

const EMAIL_TEMPLATES = [
  { name: 'welcome_user',              label: 'Welcome User'              },
  { name: 'password_reset',            label: 'Password Reset'            },
  { name: 'account_locked',            label: 'Account Locked'            },
  { name: 'password_expiring',         label: 'Password Expiring'         },
  { name: 'workflow_approval_request', label: 'Workflow Approval Request' },
];

async function initEmailTemplates() {
  const loading = document.getElementById('email-templates-loading');
  const list    = document.getElementById('email-templates-list');
  const errEl   = document.getElementById('email-templates-error');
  if (!loading || !list) return;

  // Load all templates
  let templates = {};
  try {
    const res = await apiFetch('/settings/email-templates');
    if (res.ok) {
      const data = await res.json();
      // data may be an array or object keyed by name
      if (Array.isArray(data)) {
        data.forEach(t => { templates[t.name] = t; });
      } else {
        templates = data;
      }
    }
  } catch (_) { /* will show rows with empty values */ }

  list.innerHTML = EMAIL_TEMPLATES.map(tmpl => `
    <div class="flex items-center justify-between px-4 py-3 hover:bg-gray-50 transition">
      <div>
        <p class="text-sm font-medium text-gray-900">${tmpl.label}</p>
        <p class="text-xs text-gray-400 font-mono">${tmpl.name}</p>
      </div>
      <button class="email-template-edit-btn px-3 py-1.5 text-sm rounded-lg border border-gray-200
                     text-gray-600 hover:border-blue-300 hover:text-blue-600 transition"
              data-template-name="${tmpl.name}"
              data-template-label="${tmpl.label}"
              data-subject="${encodeURIComponent((templates[tmpl.name] || {}).subject || '')}"
              data-body="${encodeURIComponent((templates[tmpl.name] || {}).html_body || '')}">
        <i class="ph ph-pencil-simple mr-1"></i>Edit
      </button>
    </div>`).join('');

  loading.classList.add('hidden');
  list.classList.remove('hidden');

  // Delegate clicks
  list.addEventListener('click', e => {
    const btn = e.target.closest('.email-template-edit-btn');
    if (!btn) return;
    openTemplateEditor(
      btn.dataset.templateName,
      btn.dataset.templateLabel,
      decodeURIComponent(btn.dataset.subject),
      decodeURIComponent(btn.dataset.body)
    );
  });
}

function openTemplateEditor(name, label, subject, body) {
  const host = document.getElementById('email-template-editor-host') || (() => {
    const el = document.createElement('div');
    el.id = 'email-template-editor-host';
    document.body.appendChild(el);
    return el;
  })();

  host.innerHTML = `
    <div class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        <!-- header -->
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <div>
            <h2 class="text-base font-semibold text-gray-900">Edit Email Template</h2>
            <p class="text-sm text-gray-500">${label}</p>
          </div>
          <button id="ete-close" class="w-8 h-8 rounded-lg hover:bg-gray-100 flex items-center justify-center text-gray-500 transition">
            <i class="ph ph-x text-lg"></i>
          </button>
        </div>

        <!-- tabs -->
        <div class="flex border-b border-gray-200 px-6">
          <button class="ete-tab ete-tab-active py-3 px-1 mr-6 text-sm font-medium border-b-2 border-blue-600 text-blue-600"
                  data-tab="subject">Subject</button>
          <button class="ete-tab py-3 px-1 mr-6 text-sm font-medium border-b-2 border-transparent text-gray-500 hover:text-gray-700"
                  data-tab="html-body">HTML Body</button>
        </div>

        <!-- tab panels -->
        <div class="flex-1 overflow-y-auto px-6 py-4">
          <div id="ete-panel-subject">
            <label class="block text-xs font-medium text-gray-500 mb-2">Subject line</label>
            <input id="ete-subject" type="text" value="${subject.replace(/"/g, '&quot;')}"
                   class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
            <p class="text-xs text-gray-400 mt-2">You may use template variables like <code class="bg-gray-100 px-1 rounded">{{user_name}}</code></p>
          </div>
          <div id="ete-panel-html-body" class="hidden">
            <label class="block text-xs font-medium text-gray-500 mb-2">HTML Body</label>
            <textarea id="ete-body" rows="14"
                      class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500">${body.replace(/</g, '&lt;')}</textarea>
          </div>
        </div>

        <!-- footer -->
        <div class="px-6 py-4 border-t border-gray-200 flex gap-3 justify-end">
          <button id="ete-cancel" class="px-4 py-2 rounded-lg border text-gray-600 hover:bg-gray-50 text-sm transition">Cancel</button>
          <button id="ete-save" class="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 text-sm transition">Save Template</button>
        </div>
      </div>
    </div>`;

  host.querySelector('#ete-close').onclick  = () => host.innerHTML = '';
  host.querySelector('#ete-cancel').onclick = () => host.innerHTML = '';

  // Tab switching
  host.querySelectorAll('.ete-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      host.querySelectorAll('.ete-tab').forEach(t => {
        t.classList.remove('ete-tab-active', 'border-blue-600', 'text-blue-600');
        t.classList.add('border-transparent', 'text-gray-500');
      });
      tab.classList.add('ete-tab-active', 'border-blue-600', 'text-blue-600');
      tab.classList.remove('border-transparent', 'text-gray-500');
      host.querySelectorAll('[id^="ete-panel-"]').forEach(p => p.classList.add('hidden'));
      host.querySelector(`#ete-panel-${tab.dataset.tab}`).classList.remove('hidden');
    });
  });

  // Save
  host.querySelector('#ete-save').addEventListener('click', async () => {
    const saveBtn = host.querySelector('#ete-save');
    saveBtn.disabled = true;
    saveBtn.textContent = 'Saving…';
    try {
      const payload = {
        subject:   host.querySelector('#ete-subject').value,
        html_body: host.querySelector('#ete-body').value,
      };
      const res = await apiFetch(`/settings/email-templates/${name}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      host.innerHTML = '';
      // simple toast
      const t = document.createElement('div');
      t.className = 'fixed top-4 right-4 z-[70] bg-green-600 text-white text-sm px-4 py-2 rounded-lg shadow-lg';
      t.textContent = `"${label}" saved`;
      document.body.appendChild(t);
      setTimeout(() => t.remove(), 3000);
    } catch (err) {
      saveBtn.disabled = false;
      saveBtn.textContent = 'Save Template';
      alert(`Save failed: ${err.message}`);
    }
  });
}

// Hook into settings route load
document.addEventListener('route:loaded', (event) => {
  if (event.detail.route === 'settings') {
    setTimeout(initEmailTemplates, 100);
  }
});
