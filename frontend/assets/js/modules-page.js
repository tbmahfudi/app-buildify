/**
 * modules-page.js  —  T-23.019 / T-23.021 / T-23.023
 *
 * Route: #/settings/modules
 */

import { apiFetch } from './api.js';
import { showToast } from './ui-utils.js';
import { FlexModal } from './components/flex-modal.js';
import FlexAlert from './components/flex-alert.js';

// ── API helpers ──────────────────────────────────────────────────────────────

async function listModules() {
  const res = await apiFetch('/modules');
  if (!res.ok) throw new Error(`Failed to load modules (HTTP ${res.status})`);
  return res.json();
}

async function getActivationPreview(moduleId) {
  const res = await apiFetch(`/modules/${moduleId}/activation-preview`);
  if (!res.ok) throw new Error(`Preview failed (HTTP ${res.status})`);
  return res.json();
}

async function enableModule(moduleId) {
  const res = await apiFetch(`/modules/${moduleId}/enable`, { method: 'POST' });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw Object.assign(new Error(body.message || 'Enable failed'), { body });
  return body;
}

async function disableModule(moduleId) {
  const res = await apiFetch(`/modules/${moduleId}/disable`, { method: 'POST' });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw Object.assign(new Error(body.message || 'Disable failed'), { body });
  return body;
}

// ── ModuleCard ───────────────────────────────────────────────────────────────

function renderModuleCard(mod) {
  const isActive = mod.activation_status === 'active';
  const isReady  = (mod.install_status ?? 'ready') === 'ready';
  const statusBadge = isActive
    ? `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
         <i class="ph ph-check-circle"></i> Active
       </span>`
    : `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-500">
         <i class="ph ph-circle-dashed"></i> Available
       </span>`;

  const actionBtn = mod.is_core
    ? `<button disabled class="w-full px-3 py-2 text-sm rounded-lg bg-gray-100 text-gray-400 cursor-not-allowed">System module</button>`
    : isActive
      ? `<button
           class="module-deactivate-btn w-full px-3 py-2 text-sm rounded-lg border border-red-200 text-red-600 hover:bg-red-50 transition"
           data-module-id="${mod.id}" data-module="${mod.name}" data-display="${mod.display_name}">
           Deactivate
         </button>`
      : `<button
           class="module-activate-btn w-full px-3 py-2 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition"
           data-module-id="${mod.id}" data-module="${mod.name}" data-display="${mod.display_name}"
           ${isReady ? '' : 'disabled'}>
           ${isReady ? 'Activate' : 'Installing...'}
         </button>`;

  return `
    <div class="module-card bg-white rounded-xl border border-gray-200 p-5 flex flex-col gap-3 shadow-sm hover:shadow-md transition"
         data-module="${mod.name}" data-module-id="${mod.id}">
      <div class="flex items-start justify-between gap-2">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center text-blue-600">
            <i class="ph ph-puzzle-piece text-xl"></i>
          </div>
          <div>
            <h3 class="font-semibold text-gray-900 text-sm leading-tight">${mod.display_name}</h3>
            <p class="text-xs text-gray-400 font-mono">${mod.name} v${mod.version}</p>
          </div>
        </div>
        ${statusBadge}
      </div>
      ${mod.description ? `<p class="text-xs text-gray-600 line-clamp-2">${mod.description}</p>` : ''}
      ${mod.category ? `<span class="inline-block text-xs text-gray-400 px-2 py-0.5 rounded bg-gray-50 border">${mod.category}</span>` : ''}
      <div class="mt-auto pt-2">${actionBtn}</div>
    </div>`;
}

// ── ActivationModal (T-23.021) ───────────────────────────────────────────────

/**
 * ActivationModal
 *
 * Displays the activation-preview for a module, checks dependency status,
 * and calls POST /modules/{id}/enable on confirmation.
 *
 * States:
 *   preview-loading  — skeleton rows; Confirm disabled
 *   preview-loaded   — sections rendered; Confirm enabled (deps met)
 *   deps-unmet       — warning alert in body; Confirm disabled
 *   activating       — both buttons disabled; Confirm shows spinner
 *   activated        — modal closes; module:activated event dispatched
 *   error            — error banner above footer; buttons re-enabled
 */
export class ActivationModal {
  constructor(moduleId, moduleName) {
    this.moduleId     = moduleId;
    this.moduleName   = moduleName;
    this._modal       = null;
    this._confirmBtn  = null;
    this._cancelBtn   = null;
    this._errorZone   = null;
    this._confirmId   = null;
    this._cancelId    = null;
    this._errorZoneId = null;
  }

  async open() {
    this._buildModal();
    this._modal.show();
    try {
      const preview = await getActivationPreview(this.moduleId);
      this._renderPreview(preview);
    } catch (err) {
      this._renderPreviewError(err.message);
    }
  }

  close() {
    if (this._modal) {
      this._modal.hide();
      setTimeout(() => { if (this._modal) { this._modal.destroy(); this._modal = null; } }, 350);
    }
  }

  _buildModal() {
    const ts = Date.now();
    this._confirmId   = `am-confirm-${ts}`;
    this._cancelId    = `am-cancel-${ts}`;
    this._errorZoneId = `am-error-${ts}`;

    const footerHtml = `
      <div id="${this._errorZoneId}" class="hidden mb-3"></div>
      <div class="flex items-center justify-end gap-3">
        <button id="${this._cancelId}"
                class="px-4 py-2 rounded-lg border border-gray-300 text-gray-600 hover:bg-gray-50 transition text-sm font-medium">
          Cancel
        </button>
        <button id="${this._confirmId}" disabled
                class="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2">
          Confirm Activation
        </button>
      </div>`;

    this._modal = new FlexModal({
      title:           `Activate ${this.moduleName}`,
      icon:            'ph ph-puzzle-piece',
      size:            'md',
      backdropDismiss: false,
      showFooter:      true,
      content:         this._skeletonHTML(),
      footer:          footerHtml,
      onShown:         () => this._bindFooterButtons(),
    });
  }

  _bindFooterButtons() {
    this._confirmBtn = document.getElementById(this._confirmId);
    this._cancelBtn  = document.getElementById(this._cancelId);
    this._errorZone  = document.getElementById(this._errorZoneId);
    if (this._cancelBtn) this._cancelBtn.onclick = () => this.close();
  }

  _skeletonHTML() {
    return `
      <div class="space-y-3 animate-pulse" aria-label="Loading preview">
        <div class="h-4 bg-gray-100 rounded w-3/4"></div>
        <div class="h-4 bg-gray-100 rounded w-1/2"></div>
        <div class="h-4 bg-gray-100 rounded w-5/6"></div>
      </div>`;
  }

  _renderPreview(data) {
    const deps      = data.dependencies || [];
    const perms     = data.permissions  || [];
    const items     = data.menu_items   || [];
    const depsUnmet = deps.filter(d => d.status !== 'active');

    let html = `
      <div class="mb-4 flex items-start gap-2 p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
        <i class="ph ph-info text-blue-500 mt-0.5 flex-shrink-0"></i>
        <span>The following will be added to your account:</span>
      </div>`;

    if (perms.length) {
      html += `
        <div class="mb-4">
          <p class="text-xs font-semibold text-gray-700 uppercase tracking-wide mb-2">Permissions</p>
          <ul class="space-y-1">
            ${perms.map(p => `
              <li class="flex items-center gap-2 text-xs text-gray-600">
                <i class="ph ph-lock-simple text-gray-400 flex-shrink-0"></i>
                <span>${p.description || p.code || p.name || ''}</span>
              </li>`).join('')}
          </ul>
        </div>`;
    }

    if (items.length) {
      html += `
        <div class="mb-4">
          <p class="text-xs font-semibold text-gray-700 uppercase tracking-wide mb-2">Menu items</p>
          <ul class="space-y-1">
            ${items.map(m => `
              <li class="flex items-center gap-2 text-xs text-gray-600">
                <i class="ph ph-list text-gray-400 flex-shrink-0"></i>
                <span>${m.label}</span>
                ${m.route ? `<span class="ml-auto font-mono text-gray-400 bg-gray-50 border px-1.5 py-0.5 rounded">${m.route}</span>` : ''}
              </li>`).join('')}
          </ul>
        </div>`;
    }

    if (deps.length) {
      html += `
        <div class="mb-4">
          <p class="text-xs font-semibold text-gray-700 uppercase tracking-wide mb-2">Requires</p>
          <ul class="space-y-1">
            ${deps.map(d => {
              const ok    = d.status === 'active';
              const dot   = ok ? '<span class="w-2 h-2 rounded-full bg-green-500 flex-shrink-0 inline-block"></span>'
                               : '<span class="w-2 h-2 rounded-full bg-red-500 flex-shrink-0 inline-block"></span>';
              const badge = ok ? '<span class="ml-auto text-xs px-1.5 py-0.5 rounded bg-green-100 text-green-700">Active</span>'
                               : '<span class="ml-auto text-xs px-1.5 py-0.5 rounded bg-red-100 text-red-700">Not activated</span>';
              return `<li class="flex items-center gap-2 text-xs text-gray-600">${dot}<span>${d.name}</span>${badge}</li>`;
            }).join('')}
          </ul>
        </div>`;

      if (depsUnmet.length) {
        html += `
          <div class="mb-2 flex items-start gap-2 p-3 bg-amber-50 border border-amber-300 rounded-lg text-sm text-amber-800">
            <i class="ph ph-warning text-amber-500 mt-0.5 flex-shrink-0"></i>
            <span>Activate required modules first.</span>
          </div>`;
      }
    }

    if (!perms.length && !items.length) {
      html += '<p class="text-sm text-gray-500">No permissions or menu items will be added.</p>';
    }

    const body = this._modal.getBodyElement();
    if (body) body.innerHTML = html;

    if (depsUnmet.length) {
      this._setConfirmDisabled(true);
    } else {
      this._setConfirmDisabled(false);
      if (this._confirmBtn) this._confirmBtn.onclick = () => this._handleConfirm();
    }
  }

  _renderPreviewError(message) {
    const body = this._modal.getBodyElement();
    if (body) {
      body.innerHTML = `
        <div class="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          <i class="ph ph-warning-circle text-red-500 mt-0.5 flex-shrink-0"></i>
          <span>Failed to load preview: ${message}</span>
        </div>`;
    }
    this._setConfirmDisabled(true);
  }

  async _handleConfirm() {
    this._setBothButtonsDisabled(true);
    if (this._confirmBtn) {
      this._confirmBtn.innerHTML = `
        <svg class="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path>
        </svg>
        Activating...`;
    }
    this._clearErrorZone();

    try {
      await enableModule(this.moduleId);
      this.close();
      document.dispatchEvent(new CustomEvent('module:activated', { detail: { moduleId: this.moduleId } }));
      document.dispatchEvent(new CustomEvent('modules:refresh'));
    } catch (err) {
      this._showErrorInZone(err.message || 'Activation failed');
      this._setBothButtonsDisabled(false);
      if (this._confirmBtn) this._confirmBtn.innerHTML = 'Confirm Activation';
    }
  }

  _setConfirmDisabled(disabled) {
    if (this._confirmBtn) this._confirmBtn.disabled = disabled;
  }

  _setBothButtonsDisabled(disabled) {
    if (this._confirmBtn) this._confirmBtn.disabled = disabled;
    if (this._cancelBtn)  this._cancelBtn.disabled  = disabled;
  }

  _clearErrorZone() {
    if (this._errorZone) { this._errorZone.innerHTML = ''; this._errorZone.classList.add('hidden'); }
  }

  _showErrorInZone(message) {
    if (!this._errorZone) return;
    this._errorZone.classList.remove('hidden');
    this._errorZone.innerHTML = `
      <div class="flex items-start gap-2 p-3 bg-red-50 border border-red-300 rounded-lg text-sm text-red-800">
        <i class="ph ph-x-circle text-red-500 mt-0.5 flex-shrink-0"></i>
        <span>Activation failed: ${message}</span>
      </div>`;
  }
}

// ── DeactivateModal (T-23.023) ───────────────────────────────────────────────

function showDeactivateModal(moduleId, moduleName, displayName) {
  const modalId = 'deactivate-modal';
  let el = document.getElementById(modalId);
  if (!el) { el = document.createElement('div'); el.id = modalId; document.body.appendChild(el); }

  el.innerHTML = `
    <div class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md">
        <div class="px-6 py-4 border-b flex items-center justify-between">
          <h2 class="text-lg font-semibold text-gray-900">Deactivate ${displayName}?</h2>
          <button id="dm-close" class="text-gray-400 hover:text-gray-600"><i class="ph ph-x text-xl"></i></button>
        </div>
        <div class="px-6 py-5">
          <div class="flex items-start gap-3 p-3 bg-amber-50 border border-amber-200 rounded-lg mb-4">
            <i class="ph ph-shield-warning text-amber-500 text-xl mt-0.5"></i>
            <p class="text-sm text-amber-800">Your data will not be deleted. Menu items and permissions added by this module will be hidden for all users in your account. You can reactivate at any time.</p>
          </div>
          <div id="dm-deps" class="hidden mb-4">
            <div class="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-800">
              <i class="ph ph-link-break text-red-500 mt-0.5"></i>
              <div>
                <p class="font-medium">The following active modules depend on this one and must be deactivated first:</p>
                <ul id="dm-deps-list" class="mt-1 list-disc list-inside space-y-0.5"></ul>
              </div>
            </div>
          </div>
        </div>
        <div class="px-6 py-4 border-t flex gap-3 justify-end items-center">
          <div id="dm-error" class="hidden flex-1 text-xs text-red-600"></div>
          <button id="dm-cancel" class="px-4 py-2 rounded-lg border border-gray-300 text-gray-600 hover:bg-gray-50 transition text-sm font-medium">Cancel</button>
          <button id="dm-confirm" class="px-4 py-2 rounded-lg bg-red-600 text-white hover:bg-red-700 transition text-sm font-medium">Deactivate</button>
        </div>
      </div>
    </div>`;

  el.querySelector('#dm-close').onclick  = () => el.remove();
  el.querySelector('#dm-cancel').onclick = () => el.remove();
  el.querySelector('#dm-confirm').onclick = async () => {
    const btn = el.querySelector('#dm-confirm');
    const cancelBtn = el.querySelector('#dm-cancel');
    btn.disabled = true; cancelBtn.disabled = true;
    btn.innerHTML = '<svg class="animate-spin inline h-4 w-4 mr-1" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path></svg> Deactivating...';
    try {
      await disableModule(moduleId || moduleName);
      el.remove();
      document.dispatchEvent(new CustomEvent('module:deactivated', { detail: { moduleId: moduleId || moduleName } }));
      document.dispatchEvent(new CustomEvent('modules:refresh'));
    } catch (err) {
      const body = err.body || {};
      const code = body.code || '';
      if ((code === 'DEPENDENTS_ACTIVE' || code === 'dependents_active') &&
          body.detail && body.detail.dependents && body.detail.dependents.length) {
        const list = el.querySelector('#dm-deps-list');
        list.innerHTML = body.detail.dependents.map(d => `<li>${d.name || d}</li>`).join('');
        el.querySelector('#dm-deps').classList.remove('hidden');
        btn.disabled = true; btn.textContent = 'Cannot deactivate';
        cancelBtn.disabled = false;
      } else {
        const errZone = el.querySelector('#dm-error');
        errZone.classList.remove('hidden');
        errZone.textContent = err.message || 'Deactivation failed';
        btn.disabled = false; cancelBtn.disabled = false;
        btn.textContent = 'Deactivate';
      }
    }
  };
}

// ── Page init ────────────────────────────────────────────────────────────────

async function render(container) {
  container.innerHTML = `
    <div class="px-6 py-8 max-w-7xl mx-auto">
      <div class="mb-8">
        <h1 class="text-2xl font-bold text-gray-900 flex items-center gap-3">
          <i class="ph-duotone ph-puzzle-piece text-blue-600"></i>
          Modules
        </h1>
        <p class="text-gray-500 mt-1 text-sm">Activate or deactivate modules for your organisation.</p>
      </div>
      <div id="modules-grid" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        ${Array.from({length: 4}).map(() => `
          <div class="bg-white rounded-xl border border-gray-200 p-5 animate-pulse">
            <div class="flex items-center gap-3 mb-3">
              <div class="w-10 h-10 rounded-lg bg-gray-100"></div>
              <div class="flex-1 space-y-2">
                <div class="h-3 bg-gray-100 rounded w-3/4"></div>
                <div class="h-2 bg-gray-100 rounded w-1/2"></div>
              </div>
            </div>
            <div class="h-2 bg-gray-100 rounded w-full mb-1"></div>
            <div class="h-2 bg-gray-100 rounded w-5/6 mb-4"></div>
            <div class="h-8 bg-gray-100 rounded w-full"></div>
          </div>`).join('')}
      </div>
    </div>`;

  async function loadModules() {
    const grid = container.querySelector('#modules-grid');
    try {
      const data = await listModules();
      const modules = data.modules || data;
      if (!modules.length) {
        grid.innerHTML = `
          <div class="col-span-full flex flex-col items-center justify-center py-16 text-gray-400">
            <i class="ph ph-package text-5xl mb-3"></i>
            <p class="font-medium">No modules are installed on this platform yet.</p>
            <p class="text-sm mt-1">Ask your platform administrator to install modules.</p>
          </div>`;
        return;
      }
      grid.innerHTML = modules.map(renderModuleCard).join('');
    } catch (err) {
      grid.innerHTML = `
        <div class="col-span-full p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          <i class="ph ph-warning-circle mr-2"></i>Could not load modules.
          <a href="#" class="underline" id="retry-modules-link">Retry?</a>
          <span class="ml-2 text-xs opacity-70">${err.message}</span>
        </div>`;
      const retryLink = container.querySelector('#retry-modules-link');
      if (retryLink) retryLink.onclick = (e) => { e.preventDefault(); loadModules(); };
    }
  }

  container.addEventListener('click', e => {
    const activateBtn   = e.target.closest('.module-activate-btn');
    const deactivateBtn = e.target.closest('.module-deactivate-btn');
    if (activateBtn) {
      const moduleId    = activateBtn.dataset.moduleId || activateBtn.dataset.module;
      const displayName = activateBtn.dataset.display;
      new ActivationModal(moduleId, displayName).open();
    } else if (deactivateBtn) {
      showDeactivateModal(
        deactivateBtn.dataset.moduleId || deactivateBtn.dataset.module,
        deactivateBtn.dataset.module,
        deactivateBtn.dataset.display
      );
    }
  });

  document.addEventListener('module:activated', (e) => {
    const moduleId = e.detail && e.detail.moduleId;
    if (!moduleId) return;
    const card = container.querySelector(`[data-module-id="${moduleId}"]`);
    if (!card) return;
    const badge = card.querySelector('.inline-flex');
    if (badge) {
      badge.className = 'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700';
      badge.innerHTML = '<i class="ph ph-check-circle"></i> Active';
    }
    const btn = card.querySelector('.module-activate-btn');
    if (btn) {
      btn.className = 'module-deactivate-btn w-full px-3 py-2 text-sm rounded-lg border border-red-200 text-red-600 hover:bg-red-50 transition';
      btn.textContent = 'Deactivate'; btn.disabled = false;
    }
  });

  document.addEventListener('module:deactivated', (e) => {
    const moduleId = e.detail && e.detail.moduleId;
    if (!moduleId) return;
    const card = container.querySelector(`[data-module-id="${moduleId}"]`);
    if (!card) return;
    const badge = card.querySelector('.inline-flex');
    if (badge) {
      badge.className = 'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-500';
      badge.innerHTML = '<i class="ph ph-circle-dashed"></i> Available';
    }
    const btn = card.querySelector('.module-deactivate-btn');
    if (btn) {
      btn.className = 'module-activate-btn w-full px-3 py-2 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition';
      btn.textContent = 'Activate'; btn.disabled = false;
    }
  });

  document.addEventListener('modules:refresh', loadModules);
  await loadModules();
}

(async () => {
  const content = document.getElementById('content');
  if (content) await render(content);
})();

export { render };