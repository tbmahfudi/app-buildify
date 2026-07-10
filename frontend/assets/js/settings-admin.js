/**
 * Admin Settings page (route: settings/admin)
 * -------------------------------------------------------------------------
 * Tenant- and company-level configuration:
 *   - Organization profile & branding (name, logo, colors)
 *   - Business defaults (locale, timezone, currency, date format)
 *   - Email templates (tenant-level)
 *
 * Scope selector: TENANT or a specific COMPANY. Tenant scope reads/writes the
 * real tenant settings store (/settings/tenant). Company scope is a minimal
 * stub: per-company overrides are stored inside the tenant settings JSON blob
 * under settings.companies[companyId] (TODO: dedicated company settings store).
 *
 * Menu access is gated by settings:manage:tenant. The backend endpoints have
 * their own permission checks (settings:read/update:tenant), so this page also
 * degrades gracefully to an "access required" panel on 403.
 */
import { apiFetch } from './api.js';
import FlexSelect from './components/flex-select.js';

const flexSelects = new Map();

const LOCALE_OPTIONS = [
  { value: 'en', label: 'English' },
  { value: 'es', label: 'Español (Spanish)' },
  { value: 'fr', label: 'Français (French)' },
  { value: 'de', label: 'Deutsch (German)' },
  { value: 'id', label: 'Bahasa Indonesia (Indonesian)' },
];

const TIMEZONE_OPTIONS = [
  { value: 'UTC', label: 'UTC' },
  { value: 'America/New_York', label: 'Eastern Time' },
  { value: 'America/Chicago', label: 'Central Time' },
  { value: 'America/Los_Angeles', label: 'Pacific Time' },
  { value: 'Europe/London', label: 'London' },
  { value: 'Asia/Tokyo', label: 'Tokyo' },
];

// Full loaded tenant settings (so we can round-trip the JSON blobs on save).
let tenantSettingsCache = null;
let currentScope = 'tenant';           // 'tenant' | company id
let companyOptions = [];               // [{value,label}]

document.addEventListener('route:loaded', (event) => {
  if (event.detail.route === 'settings/admin') {
    setTimeout(() => initAdminSettings(), 0);
  }
});

function destroyFlexSelects() {
  flexSelects.forEach((fs) => { try { fs.destroy(); } catch (_) {} });
  flexSelects.clear();
}

function mountFlexSelect(id, options, onChange) {
  const container = document.getElementById(`${id}-container`);
  if (!container) return;
  const fs = new FlexSelect(container, {
    options,
    searchable: options.length > 6,
    clearable: false,
    placeholder: 'Select...',
    onChange: onChange || (() => {}),
  });
  flexSelects.set(id, fs);
}

async function initAdminSettings() {
  const body = document.getElementById('admin-settings-body');
  const denied = document.getElementById('admin-settings-denied');
  if (!body) return;

  destroyFlexSelects();

  // Load the scope options (tenant + companies) before wiring the selector.
  await loadCompanyOptions();
  mountScopeSelector();
  mountFlexSelect('admin-default-locale', LOCALE_OPTIONS);
  mountFlexSelect('admin-default-timezone', TIMEZONE_OPTIONS);

  const form = document.getElementById('admin-settings-form');
  if (form && !form.dataset.initialized) {
    form.addEventListener('submit', handleSave);
    form.dataset.initialized = 'true';
  }

  try {
    await loadTenantSettings();     // may throw 403
    body.classList.remove('hidden');
    denied.classList.add('hidden');
    applyScope(currentScope);
    await initEmailTemplates();
  } catch (err) {
    console.warn('Admin settings load failed:', err);
    body.classList.add('hidden');
    denied.classList.remove('hidden');
  }
}

async function loadCompanyOptions() {
  companyOptions = [];
  try {
    const res = await apiFetch('/org/companies');
    if (res.ok) {
      const data = await res.json();
      const list = Array.isArray(data) ? data : (data.items || data.companies || []);
      companyOptions = list.map((c) => ({
        value: String(c.id),
        label: c.name || c.code || String(c.id),
      }));
    }
  } catch (_) { /* companies optional — tenant scope always available */ }
}

function mountScopeSelector() {
  const container = document.getElementById('admin-scope-container');
  if (!container) return;
  const options = [
    { value: 'tenant', label: 'Tenant (organization-wide)' },
    ...companyOptions.map((c) => ({ value: c.value, label: `Company: ${c.label}` })),
  ];
  const fs = new FlexSelect(container, {
    options,
    searchable: options.length > 6,
    clearable: false,
    onChange: (val) => applyScope(val),
  });
  fs.setValue('tenant');
  flexSelects.set('admin-scope', fs);
}

function applyScope(scope) {
  currentScope = scope || 'tenant';
  const todo = document.getElementById('admin-company-todo');
  if (todo) todo.classList.toggle('hidden', currentScope === 'tenant');
  populateForm();
}

function currentScopeValues() {
  // Tenant scope → top-level tenant settings.
  if (currentScope === 'tenant') {
    return {
      tenant_name: tenantSettingsCache?.tenant_name || '',
      logo_url: tenantSettingsCache?.logo_url || '',
      primary_color: tenantSettingsCache?.primary_color || '#1976d2',
      secondary_color: tenantSettingsCache?.secondary_color || '#424242',
      defaults: (tenantSettingsCache?.settings && tenantSettingsCache.settings.defaults) || {},
    };
  }
  // Company scope → settings.companies[companyId] blob (stub).
  const companies = (tenantSettingsCache?.settings && tenantSettingsCache.settings.companies) || {};
  const c = companies[currentScope] || {};
  return {
    tenant_name: c.name || '',
    logo_url: c.logo_url || '',
    primary_color: c.primary_color || '#1976d2',
    secondary_color: c.secondary_color || '#424242',
    defaults: c.defaults || {},
  };
}

function populateForm() {
  const v = currentScopeValues();
  setVal('admin-tenant-name', v.tenant_name);
  setVal('admin-logo-url', v.logo_url);
  setVal('admin-primary-color', v.primary_color || '#1976d2');
  setVal('admin-secondary-color', v.secondary_color || '#424242');
  setVal('admin-default-currency', v.defaults.currency || '');
  setVal('admin-date-format', v.defaults.date_format || '');
  setSelect('admin-default-locale', v.defaults.locale || 'en');
  setSelect('admin-default-timezone', v.defaults.timezone || 'UTC');
}

async function loadTenantSettings() {
  const res = await apiFetch('/settings/tenant');
  if (!res.ok) {
    const e = new Error(`settings/tenant ${res.status}`);
    e.status = res.status;
    throw e;
  }
  tenantSettingsCache = await res.json();
  const upd = document.getElementById('admin-settings-last-updated');
  if (upd && tenantSettingsCache.updated_at) {
    upd.textContent = `Last updated: ${new Date(tenantSettingsCache.updated_at).toLocaleString()}`;
  }
}

async function handleSave(event) {
  event.preventDefault();

  const defaults = {
    locale: getSelect('admin-default-locale'),
    timezone: getSelect('admin-default-timezone'),
    currency: (getVal('admin-default-currency') || '').toUpperCase(),
    date_format: getVal('admin-date-format'),
  };

  // Start from the cached settings JSON so we don't clobber other keys.
  const settingsBlob = { ...(tenantSettingsCache?.settings || {}) };

  let payload;
  if (currentScope === 'tenant') {
    settingsBlob.defaults = defaults;
    payload = {
      tenant_name: getVal('admin-tenant-name'),
      logo_url: getVal('admin-logo-url'),
      primary_color: getVal('admin-primary-color'),
      secondary_color: getVal('admin-secondary-color'),
      settings: settingsBlob,
    };
  } else {
    // Company scope stub: write into settings.companies[companyId].
    const companies = { ...(settingsBlob.companies || {}) };
    companies[currentScope] = {
      name: getVal('admin-tenant-name'),
      logo_url: getVal('admin-logo-url'),
      primary_color: getVal('admin-primary-color'),
      secondary_color: getVal('admin-secondary-color'),
      defaults,
    };
    settingsBlob.companies = companies;
    payload = { settings: settingsBlob };
  }

  try {
    const res = await apiFetch('/settings/tenant', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (res.ok) {
      tenantSettingsCache = await res.json();
      if (currentScope === 'tenant') applyBranding(payload);
      showAlert('Settings saved successfully!', 'success');
    } else {
      const err = await res.json().catch(() => ({}));
      showAlert(err.detail || 'Failed to save settings.', 'danger');
    }
  } catch (err) {
    showAlert('Failed to save settings. Please try again.', 'danger');
  }
}

function applyBranding(p) {
  if (p.primary_color) document.documentElement.style.setProperty('--color-primary', p.primary_color);
  if (p.secondary_color) document.documentElement.style.setProperty('--color-secondary', p.secondary_color);
}

// ── helpers ───────────────────────────────────────────────────────────────
function setVal(id, v) { const el = document.getElementById(id); if (el) el.value = v ?? ''; }
function getVal(id) { const el = document.getElementById(id); return el ? el.value.trim() : ''; }
function setSelect(id, v) { const fs = flexSelects.get(id); if (fs) fs.setValue(v); }
function getSelect(id) { const fs = flexSelects.get(id); return fs ? (fs.getValue() ?? '') : ''; }

function showAlert(message, tone = 'info') {
  const toneClasses = {
    success: 'bg-green-50 border-green-200 text-green-700',
    danger: 'bg-red-50 border-red-200 text-red-700',
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-700',
  }[tone] || 'bg-blue-50 border-blue-200 text-blue-700';
  const el = document.createElement('div');
  el.className = `fixed top-4 right-4 max-w-md z-[60] flex items-start gap-3 border rounded-lg shadow-lg p-4 ${toneClasses}`;
  el.innerHTML = `<div class="flex-1">${message}</div><button type="button" data-close class="text-lg">&times;</button>`;
  el.querySelector('[data-close]')?.addEventListener('click', () => el.remove());
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 5000);
}

// ── Email templates (moved from the old General settings page) ──────────────
const EMAIL_TEMPLATES = [
  { name: 'welcome_user', label: 'Welcome User' },
  { name: 'password_reset', label: 'Password Reset' },
  { name: 'account_locked', label: 'Account Locked' },
  { name: 'password_expiring', label: 'Password Expiring' },
  { name: 'workflow_approval_request', label: 'Workflow Approval Request' },
];

async function initEmailTemplates() {
  const loading = document.getElementById('email-templates-loading');
  const list = document.getElementById('email-templates-list');
  if (!loading || !list) return;

  let templates = {};
  try {
    const res = await apiFetch('/settings/email-templates');
    if (res.ok) {
      const data = await res.json();
      const arr = Array.isArray(data) ? data : (data.templates || []);
      arr.forEach((t) => { templates[t.name] = t.override || t; });
    }
  } catch (_) { /* show rows with empty values */ }

  list.innerHTML = EMAIL_TEMPLATES.map((tmpl) => `
    <div class="flex items-center justify-between px-4 py-3 hover:bg-gray-50 transition">
      <div>
        <p class="text-sm font-medium text-gray-900">${tmpl.label}</p>
        <p class="text-xs text-gray-400 font-mono">${tmpl.name}</p>
      </div>
      <button class="email-template-edit-btn px-3 py-1.5 text-sm rounded-lg border border-gray-200 text-gray-600 hover:border-orange-300 hover:text-orange-600 transition"
              data-template-name="${tmpl.name}"
              data-template-label="${tmpl.label}"
              data-subject="${encodeURIComponent((templates[tmpl.name] || {}).subject || '')}"
              data-body="${encodeURIComponent((templates[tmpl.name] || {}).body || (templates[tmpl.name] || {}).html_body || '')}">
        <i class="ph ph-pencil-simple mr-1"></i>Edit
      </button>
    </div>`).join('');

  loading.classList.add('hidden');
  list.classList.remove('hidden');

  list.addEventListener('click', (e) => {
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
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <div>
            <h2 class="text-base font-semibold text-gray-900">Edit Email Template</h2>
            <p class="text-sm text-gray-500">${label}</p>
          </div>
          <button id="ete-close" class="w-8 h-8 rounded-lg hover:bg-gray-100 flex items-center justify-center text-gray-500 transition"><i class="ph ph-x text-lg"></i></button>
        </div>
        <div class="flex-1 overflow-y-auto px-6 py-4 space-y-4">
          <div>
            <label class="block text-xs font-medium text-gray-500 mb-2">Subject line</label>
            <input id="ete-subject" type="text" value="${subject.replace(/"/g, '&quot;')}"
                   class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500">
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-500 mb-2">HTML Body</label>
            <textarea id="ete-body" rows="12" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-orange-500">${body.replace(/</g, '&lt;')}</textarea>
          </div>
        </div>
        <div class="px-6 py-4 border-t border-gray-200 flex gap-3 justify-end">
          <button id="ete-cancel" class="px-4 py-2 rounded-lg border text-gray-600 hover:bg-gray-50 text-sm transition">Cancel</button>
          <button id="ete-save" class="px-4 py-2 rounded-lg bg-orange-600 text-white hover:bg-orange-700 text-sm transition">Save Template</button>
        </div>
      </div>
    </div>`;

  host.querySelector('#ete-close').onclick = () => host.innerHTML = '';
  host.querySelector('#ete-cancel').onclick = () => host.innerHTML = '';
  host.querySelector('#ete-save').addEventListener('click', async () => {
    const saveBtn = host.querySelector('#ete-save');
    saveBtn.disabled = true;
    saveBtn.textContent = 'Saving…';
    try {
      const payload = {
        subject: host.querySelector('#ete-subject').value,
        html_body: host.querySelector('#ete-body').value,
        body: host.querySelector('#ete-body').value,
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
      showAlert(`"${label}" saved`, 'success');
    } catch (err) {
      saveBtn.disabled = false;
      saveBtn.textContent = 'Save Template';
      showAlert(`Save failed: ${err.message}`, 'danger');
    }
  });
}
