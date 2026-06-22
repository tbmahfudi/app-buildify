/**
 * modules-page.js  —  T-23.019 / T-23.021 / T-23.023
 *
 * Route: #/settings/modules
 */

import { apiFetch } from './api.js';
import { showToast } from './ui-utils.js';

// ── API helpers ──────────────────────────────────────────────────────────────

async function listModules() {
  const res = await apiFetch('/modules');
  if (!res.ok) throw new Error(`Failed to load modules (HTTP ${res.status})`);
  return res.json();
}

async function getActivationPreview(moduleName) {
  const res = await apiFetch(`/modules/${moduleName}/activation-preview`);
  if (!res.ok) throw new Error(`Preview failed (HTTP ${res.status})`);
  return res.json();
}

async function enableModule(moduleName) {
  const res = await apiFetch(`/modules/${moduleName}/enable`, { method: 'POST' });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw Object.assign(new Error(body.message || 'Enable failed'), { body });
  return body;
}

async function disableModule(moduleName) {
  const res = await apiFetch(`/modules/${moduleName}/disable`, { method: 'POST' });
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
         <i class="ph ph-circle-dashed"></i> Inactive
       </span>`;

  const actionBtn = mod.is_core
    ? `<button disabled class="w-full px-3 py-2 text-sm rounded-lg bg-gray-100 text-gray-400 cursor-not-allowed">System module</button>`
    : isActive
      ? `<button
           class="module-deactivate-btn w-full px-3 py-2 text-sm rounded-lg border border-red-200 text-red-600 hover:bg-red-50 transition"
           data-module="${mod.name}" data-display="${mod.display_name}">
           Deactivate
         </button>`
      : `<button
           class="module-activate-btn w-full px-3 py-2 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition"
           data-module="${mod.name}" data-display="${mod.display_name}"
           ${isReady ? '' : 'disabled'}>
           ${isReady ? 'Activate' : 'Installing…'}
         </button>`;

  return `
    <div class="module-card bg-white rounded-xl border border-gray-200 p-5 flex flex-col gap-3 shadow-sm hover:shadow-md transition"
         data-module="${mod.name}">
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
      ${mod.category ? `<p class="text-xs text-gray-400">${mod.category}</p>` : ''}
      <div class="mt-auto pt-2">${actionBtn}</div>
    </div>`;
}

// ── ActivationModal (T-23.021) ───────────────────────────────────────────────

function showActivationModal(moduleName, displayName) {
  const modalId = 'activation-modal';
  let el = document.getElementById(modalId);
  if (!el) { el = document.createElement('div'); el.id = modalId; document.body.appendChild(el); }

  el.innerHTML = `
    <div class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] flex flex-col">
        <div class="flex items-center justify-between px-6 py-4 border-b">
          <div>
            <h2 class="text-lg font-semibold text-gray-900">Activate Module</h2>
            <p class="text-sm text-gray-500">${displayName}</p>
          </div>
          <button id="am-close" class="text-gray-400 hover:text-gray-600">
            <i class="ph ph-x text-xl"></i>
          </button>
        </div>
        <div id="am-body" class="flex-1 overflow-y-auto px-6 py-4">
          <div class="space-y-3 animate-pulse">
            <div class="h-4 bg-gray-100 rounded w-3/4"></div>
            <div class="h-4 bg-gray-100 rounded w-1/2"></div>
            <div class="h-4 bg-gray-100 rounded w-5/6"></div>
          </div>
        </div>
        <div class="px-6 py-4 border-t flex gap-3 justify-end">
          <button id="am-cancel" class="px-4 py-2 rounded-lg border text-gray-600 hover:bg-gray-50 transition">Cancel</button>
          <button id="am-confirm" class="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition" disabled>
            Confirm Activation
          </button>
        </div>
      </div>
    </div>`;

  el.querySelector('#am-close').onclick  = () => el.remove();
  el.querySelector('#am-cancel').onclick = () => el.remove();

  getActivationPreview(moduleName).then(data => {
    const depsUnmet  = (data.dependencies || []).filter(d => d.status !== 'active');
    const confirmBtn = el.querySelector('#am-confirm');

    el.querySelector('#am-body').innerHTML = `
      ${depsUnmet.length ? `
        <div class="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800">
          <strong>Dependencies not active:</strong>
          <ul class="mt-1 list-disc list-inside">
            ${depsUnmet.map(d => `<li>${d.display_name || d.name} — ${d.status}</li>`).join('')}
          </ul>
        </div>` : ''}
      ${(data.permissions || []).length ? `
        <div class="mb-4">
          <h4 class="text-sm font-medium text-gray-700 mb-2 flex items-center gap-1">
            <i class="ph ph-shield-check text-blue-500"></i> Permissions granted
          </h4>
          <ul class="space-y-1">
            ${(data.permissions || []).map(p =>
              `<li class="text-xs text-gray-600 flex items-center gap-2">
                 <i class="ph ph-dot text-blue-400"></i>${p.name}
                 ${p.description ? `<span class="text-gray-400">— ${p.description}</span>` : ''}
               </li>`).join('')}
          </ul>
        </div>` : ''}
      ${(data.menu_items || []).length ? `
        <div class="mb-4">
          <h4 class="text-sm font-medium text-gray-700 mb-2 flex items-center gap-1">
            <i class="ph ph-list text-blue-500"></i> Menu items added
          </h4>
          <ul class="space-y-1">
            ${(data.menu_items || []).map(m =>
              `<li class="text-xs text-gray-600 flex items-center gap-2">
                 <i class="ph ph-arrow-right text-blue-400"></i>${m.label}
                 ${m.route ? `<span class="text-gray-400">(${m.route})</span>` : ''}
               </li>`).join('')}
          </ul>
        </div>` : ''}
      ${!(data.permissions || []).length && !(data.menu_items || []).length
        ? '<p class="text-sm text-gray-500">No permissions or menu items will be added.</p>'
        : ''}`;

    if (depsUnmet.length === 0) {
      confirmBtn.disabled = false;
      confirmBtn.onclick = async () => {
        confirmBtn.disabled = true;
        confirmBtn.textContent = 'Activating…';
        try {
          await enableModule(moduleName);
          showToast(`${displayName} activated`, 'success');
          el.remove();
          document.dispatchEvent(new CustomEvent('module:activated', { detail: { name: moduleName } }));
          document.dispatchEvent(new CustomEvent('modules:refresh'));
        } catch (err) {
          showToast(err.message || 'Activation failed', 'error');
          confirmBtn.disabled = false;
          confirmBtn.textContent = 'Confirm Activation';
        }
      };
    } else {
      confirmBtn.title = 'Resolve dependencies first';
    }
  }).catch(err => {
    el.querySelector('#am-body').innerHTML =
      `<p class="text-sm text-red-500">Failed to load preview: ${err.message}</p>`;
  });
}

// ── DeactivateModal (T-23.023) ───────────────────────────────────────────────

function showDeactivateModal(moduleName, displayName) {
  const modalId = 'deactivate-modal';
  let el = document.getElementById(modalId);
  if (!el) { el = document.createElement('div'); el.id = modalId; document.body.appendChild(el); }

  el.innerHTML = `
    <div class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md">
        <div class="px-6 py-4 border-b flex items-center justify-between">
          <h2 class="text-lg font-semibold text-gray-900">Deactivate Module</h2>
          <button id="dm-close" class="text-gray-400 hover:text-gray-600">
            <i class="ph ph-x text-xl"></i>
          </button>
        </div>
        <div class="px-6 py-5">
          <div class="flex items-start gap-3 p-3 bg-red-50 border border-red-200 rounded-lg mb-4">
            <i class="ph ph-warning text-red-500 text-xl mt-0.5"></i>
            <div>
              <p class="text-sm font-medium text-red-800">Deactivate <strong>${displayName}</strong>?</p>
              <p class="text-xs text-red-600 mt-1">
                This will remove the module's menu items and permissions from your tenant.
                Your data will be preserved.
              </p>
            </div>
          </div>
          <div id="dm-deps" class="hidden mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800">
            <strong>Dependent modules must be deactivated first.</strong>
            <ul id="dm-deps-list" class="mt-1 list-disc list-inside"></ul>
          </div>
        </div>
        <div class="px-6 py-4 border-t flex gap-3 justify-end">
          <button id="dm-cancel" class="px-4 py-2 rounded-lg border text-gray-600 hover:bg-gray-50 transition">Cancel</button>
          <button id="dm-confirm" class="px-4 py-2 rounded-lg bg-red-600 text-white hover:bg-red-700 transition">
            Deactivate
          </button>
        </div>
      </div>
    </div>`;

  el.querySelector('#dm-close').onclick  = () => el.remove();
  el.querySelector('#dm-cancel').onclick = () => el.remove();
  el.querySelector('#dm-confirm').onclick = async () => {
    const btn = el.querySelector('#dm-confirm');
    btn.disabled = true;
    btn.textContent = 'Deactivating…';
    try {
      await disableModule(moduleName);
      showToast(`${displayName} deactivated`, 'success');
      el.remove();
      document.dispatchEvent(new CustomEvent('module:deactivated', { detail: { name: moduleName } }));
      document.dispatchEvent(new CustomEvent('modules:refresh'));
    } catch (err) {
      const body = err.body || {};
      if (body.code === 'DEPENDENTS_ACTIVE' && body.detail?.dependents?.length) {
        const list = el.querySelector('#dm-deps-list');
        list.innerHTML = body.detail.dependents.map(d => `<li>${d}</li>`).join('');
        el.querySelector('#dm-deps').classList.remove('hidden');
        btn.disabled = true;
        btn.textContent = 'Cannot deactivate';
      } else {
        showToast(err.message || 'Deactivation failed', 'error');
        btn.disabled = false;
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
        <p class="text-gray-500 mt-1 text-sm">
          Activate or deactivate modules for your organisation.
        </p>
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
            <i class="ph ph-puzzle-piece text-5xl mb-3"></i>
            <p class="font-medium">No modules installed</p>
            <p class="text-sm mt-1">Ask your platform administrator to install modules.</p>
          </div>`;
        return;
      }
      grid.innerHTML = modules.map(renderModuleCard).join('');
    } catch (err) {
      grid.innerHTML = `
        <div class="col-span-full p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          <i class="ph ph-warning-circle mr-2"></i>Failed to load modules: ${err.message}
        </div>`;
    }
  }

  // Delegate click events for Activate / Deactivate buttons
  container.addEventListener('click', e => {
    const activateBtn   = e.target.closest('.module-activate-btn');
    const deactivateBtn = e.target.closest('.module-deactivate-btn');
    if (activateBtn) {
      showActivationModal(activateBtn.dataset.module, activateBtn.dataset.display);
    } else if (deactivateBtn) {
      showDeactivateModal(deactivateBtn.dataset.module, deactivateBtn.dataset.display);
    }
  });

  // Refresh the grid when a modal action completes
  document.addEventListener('modules:refresh', loadModules);

  await loadModules();
}

// Auto-init when loaded into the SPA content area
(async () => {
  const content = document.getElementById('content');
  if (content) await render(content);
})();

export { render };
