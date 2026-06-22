/**
 * admin-modules.js
 *
 * Route: #/admin/modules  (superuser only)
 *
 * Tab 1 – Installed Modules  : table of all is_installed=true modules
 * Tab 2 – Install New Module : drag-and-drop .tar.gz upload + async polling
 */

import { apiFetch } from './api.js';
import { showToast } from './ui-utils.js';

// ── helpers ──────────────────────────────────────────────────────────────────

/** Extract module name from a tarball filename.
 *  "healthcare_1.0.0.tar.gz" → "healthcare"
 *  "my-module-2.3.tar.gz"   → "my-module"
 */
function moduleNameFromFilename(filename) {
  // Strip extensions
  const base = filename.replace(/\.tar\.gz$/i, '').replace(/\.tgz$/i, '');
  // Strip trailing _semver or -semver
  return base.replace(/[_-]\d+(\.\d+)*$/, '');
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// ── API ───────────────────────────────────────────────────────────────────────

async function fetchAllModules() {
  const res = await apiFetch('/admin/modules/');
  if (res.status === 401 || res.status === 403) {
    throw Object.assign(new Error('Superuser access required'), { accessDenied: true });
  }
  if (!res.ok) throw new Error(`Failed to load modules (HTTP ${res.status})`);
  return res.json();
}

async function syncRegistry() {
  const res = await apiFetch('/module-registry/sync', { method: 'POST' });
  if (!res.ok) throw new Error(`Sync failed (HTTP ${res.status})`);
  return res.json().catch(() => ({}));
}

async function pollInstallStatus(moduleName) {
  const res = await apiFetch(`/admin/modules/${encodeURIComponent(moduleName)}/install-status`);
  if (!res.ok) throw new Error(`Status check failed (HTTP ${res.status})`);
  return res.json();
}

// ── Status badge ──────────────────────────────────────────────────────────────

function statusBadge(status) {
  const map = {
    ready:       ['bg-green-100 text-green-700',  'ph-check-circle',   'Ready'],
    in_progress: ['bg-yellow-100 text-yellow-700','ph-spinner',        'In Progress'],
    failed:      ['bg-red-100 text-red-700',      'ph-x-circle',       'Failed'],
  };
  const [cls, icon, label] = map[status] || ['bg-gray-100 text-gray-500', 'ph-circle-dashed', status || 'Unknown'];
  return `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${cls}">
    <i class="ph ${icon}"></i>${label}
  </span>`;
}

// ── Installed modules table ───────────────────────────────────────────────────

function renderInstalledTable(modules) {
  const installed = modules.filter(m => m.is_installed);

  if (!installed.length) {
    return `<div class="flex flex-col items-center justify-center py-16 text-gray-400">
      <i class="ph ph-package text-5xl mb-3"></i>
      <p class="font-medium">No modules installed yet</p>
      <p class="text-sm mt-1">Use the "Install New Module" tab to add one.</p>
    </div>`;
  }

  const rows = installed.map(m => `
    <tr class="hover:bg-gray-50 transition">
      <td class="px-4 py-3">
        <div class="font-medium text-gray-900 text-sm">${m.display_name || m.name}</div>
        <div class="text-xs text-gray-400 font-mono">${m.name}</div>
      </td>
      <td class="px-4 py-3 text-sm text-gray-600">${m.version || '—'}</td>
      <td class="px-4 py-3">${statusBadge(m.install_status)}</td>
      <td class="px-4 py-3 text-sm text-gray-500">${m.category || '—'}</td>
      <td class="px-4 py-3 text-sm text-gray-400">${m.module_type || '—'}</td>
      <td class="px-4 py-3">
        <button disabled
                title="Uninstall via CLI"
                class="px-3 py-1.5 rounded-lg border border-gray-200 text-xs text-gray-400 cursor-not-allowed bg-gray-50">
          Uninstall
        </button>
      </td>
    </tr>`).join('');

  return `
    <div class="overflow-x-auto rounded-xl border border-gray-200 shadow-sm">
      <table class="w-full text-left">
        <thead class="bg-gray-50 border-b border-gray-200">
          <tr>
            <th class="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Module</th>
            <th class="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Version</th>
            <th class="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Status</th>
            <th class="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Category</th>
            <th class="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Type</th>
            <th class="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100 bg-white">
          ${rows}
        </tbody>
      </table>
    </div>
    <p class="mt-2 text-xs text-gray-400">
      <i class="ph ph-info mr-1"></i>Uninstall is only available via the CLI.
    </p>`;
}

// ── Page render ───────────────────────────────────────────────────────────────

export async function render(container) {
  // Load HTML template
  const html = await fetch('/assets/templates/admin-modules.html').then(r => r.text());
  container.innerHTML = html;

  const page = container.querySelector('#admin-modules-page');

  // ── State ────────────────────────────────────────────────────────────────
  let selectedFile     = null;
  let selectedChecksum = null;
  let pollTimer        = null;

  // ── Element refs ─────────────────────────────────────────────────────────
  const accessDeniedBanner = page.querySelector('#admin-modules-access-denied');
  const syncBtn            = page.querySelector('#admin-modules-sync-btn');
  const tabs               = page.querySelectorAll('.admin-modules-tab');
  const panels             = page.querySelectorAll('.admin-modules-panel');
  const tableWrap          = page.querySelector('#admin-modules-table-wrap');

  const dropzone           = page.querySelector('#admin-modules-dropzone');
  const fileInput          = page.querySelector('#admin-modules-file-input');
  const dropIdle           = page.querySelector('#admin-modules-drop-idle');
  const dropSelected       = page.querySelector('#admin-modules-drop-selected');
  const selectedName       = page.querySelector('#admin-modules-selected-name');
  const selectedSize       = page.querySelector('#admin-modules-selected-size');

  const checksumInput      = page.querySelector('#admin-modules-checksum-input');
  const checksumLabel      = page.querySelector('#admin-modules-checksum-label');
  const checksumClear      = page.querySelector('#admin-modules-checksum-clear');

  const installBtn         = page.querySelector('#admin-modules-install-btn');
  const deployModeSelect    = page.querySelector('#admin-modules-deploy-mode');

  const progressPanel      = page.querySelector('#admin-modules-progress');
  const progressSpinner    = page.querySelector('#admin-modules-progress-spinner');
  const progressMsg        = page.querySelector('#admin-modules-progress-msg');
  const progressSuccess    = page.querySelector('#admin-modules-progress-success');
  const successMsg         = page.querySelector('#admin-modules-success-msg');
  const successDetail      = page.querySelector('#admin-modules-success-detail');
  const progressError      = page.querySelector('#admin-modules-progress-error');
  const errorMsg           = page.querySelector('#admin-modules-error-msg');

  // ── Tab switching ────────────────────────────────────────────────────────
  function switchTab(name) {
    tabs.forEach(t => {
      const active = t.dataset.tab === name;
      t.classList.toggle('border-blue-600', active);
      t.classList.toggle('text-blue-600', active);
      t.classList.toggle('border-transparent', !active);
      t.classList.toggle('text-gray-500', !active);
    });
    panels.forEach(p => {
      p.classList.toggle('hidden', p.id !== `admin-modules-tab-${name}`);
    });
  }

  tabs.forEach(t => t.addEventListener('click', () => switchTab(t.dataset.tab)));

  // ── Sync button ──────────────────────────────────────────────────────────
  syncBtn.addEventListener('click', async () => {
    syncBtn.disabled = true;
    const icon = syncBtn.querySelector('i');
    icon.classList.add('animate-spin');
    try {
      await syncRegistry();
      showToast('Registry synced', 'success');
      await loadInstalledModules();
    } catch (err) {
      showToast(err.message || 'Sync failed', 'error');
    } finally {
      syncBtn.disabled = false;
      icon.classList.remove('animate-spin');
    }
  });

  // ── Load installed modules ───────────────────────────────────────────────
  async function loadInstalledModules() {
    tableWrap.innerHTML = `
      <div class="animate-pulse space-y-3">
        <div class="h-10 bg-gray-100 rounded-lg w-full"></div>
        <div class="h-10 bg-gray-100 rounded-lg w-full"></div>
        <div class="h-10 bg-gray-100 rounded-lg w-full"></div>
      </div>`;
    try {
      const data = await fetchAllModules();
      const modules = Array.isArray(data) ? data : (data.modules || data.items || []);
      tableWrap.innerHTML = renderInstalledTable(modules);
    } catch (err) {
      if (err.accessDenied) {
        accessDeniedBanner.classList.remove('hidden');
        tableWrap.innerHTML = '';
      } else {
        tableWrap.innerHTML = `
          <div class="p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            <i class="ph ph-warning-circle mr-2"></i>${err.message}
          </div>`;
      }
    }
  }

  // ── File selection helpers ────────────────────────────────────────────────
  function setSelectedFile(file) {
    selectedFile = file;
    if (file) {
      dropIdle.classList.add('hidden');
      dropSelected.classList.remove('hidden');
      selectedName.textContent = file.name;
      selectedSize.textContent = formatBytes(file.size);
      installBtn.disabled = false;
    } else {
      dropIdle.classList.remove('hidden');
      dropSelected.classList.add('hidden');
      selectedName.textContent = '-';
      selectedSize.textContent = '-';
      installBtn.disabled = true;
    }
  }

  fileInput.addEventListener('change', () => {
    if (fileInput.files.length) setSelectedFile(fileInput.files[0]);
  });

  // Drag-and-drop
  dropzone.addEventListener('dragover', e => {
    e.preventDefault();
    dropzone.classList.add('border-blue-400', 'bg-blue-50');
  });
  dropzone.addEventListener('dragleave', () => {
    dropzone.classList.remove('border-blue-400', 'bg-blue-50');
  });
  dropzone.addEventListener('drop', e => {
    e.preventDefault();
    dropzone.classList.remove('border-blue-400', 'bg-blue-50');
    const file = e.dataTransfer.files[0];
    if (file && (file.name.endsWith('.tar.gz') || file.name.endsWith('.tgz'))) {
      setSelectedFile(file);
    } else {
      showToast('Please drop a .tar.gz file', 'error');
    }
  });

  // Checksum file
  checksumInput.addEventListener('change', () => {
    if (checksumInput.files.length) {
      selectedChecksum = checksumInput.files[0];
      checksumLabel.textContent = selectedChecksum.name;
      checksumClear.classList.remove('hidden');
    }
  });
  checksumClear.addEventListener('click', () => {
    selectedChecksum = null;
    checksumInput.value = '';
    checksumLabel.textContent = 'Choose file...';
    checksumClear.classList.add('hidden');
  });

  // ── Progress helpers ──────────────────────────────────────────────────────
  function showProgress(msg) {
    progressPanel.classList.remove('hidden');
    progressSpinner.classList.remove('hidden');
    progressMsg.textContent = msg;
    progressSuccess.classList.add('hidden');
    progressError.classList.add('hidden');
  }

  function showSuccess(msg, detail) {
    progressSpinner.classList.add('hidden');
    progressSuccess.classList.remove('hidden');
    progressError.classList.add('hidden');
    successMsg.textContent = msg;
    successDetail.textContent = detail || '';
  }

  function showError(msg) {
    progressSpinner.classList.add('hidden');
    progressSuccess.classList.add('hidden');
    progressError.classList.remove('hidden');
    errorMsg.textContent = msg;
  }

  // ── Install flow ──────────────────────────────────────────────────────────
  installBtn.addEventListener('click', async () => {
    if (!selectedFile) return;

    installBtn.disabled = true;
    const moduleName = moduleNameFromFilename(selectedFile.name);

    showProgress(`Uploading ${selectedFile.name}...`);

    // Build FormData
    const formData = new FormData();
    formData.append('file', selectedFile);
    const deployMode = deployModeSelect ? deployModeSelect.value : 'auto';
    formData.append('deploy_mode', deployMode);
    if (selectedChecksum) formData.append('checksum_file', selectedChecksum);

    try {
      // Use fetch directly for multipart — pass auth header manually
      const token = localStorage.getItem('accessToken') ||
                    (() => { try { return JSON.parse(localStorage.getItem('tokens'))?.access; } catch { return null; } })();

      const headers = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;

      // Optionally include tenant header
      const tenantId = localStorage.getItem('tenantId');
      if (tenantId) headers['X-Tenant-Id'] = tenantId;

      const uploadRes = await fetch('/api/v1/admin/modules/upload-install', {
        method: 'POST',
        headers,
        body: formData,
      });

      if (uploadRes.status === 401 || uploadRes.status === 403) {
        showError('Superuser access required');
        accessDeniedBanner.classList.remove('hidden');
        return;
      }
      if (!uploadRes.ok) {
        const body = await uploadRes.json().catch(() => ({}));
        throw new Error(body.detail || body.message || `Upload failed (HTTP ${uploadRes.status})`);
      }

      // Upload accepted — start polling
      showProgress(`Installing ${selectedFile.name}...`);
      startPolling(moduleName);

    } catch (err) {
      showError(err.message || 'Upload failed');
      installBtn.disabled = false;
    }
  });

  // ── Status polling ────────────────────────────────────────────────────────
  function startPolling(moduleName) {
    let attempts = 0;
    const MAX_ATTEMPTS = 60; // 2 min at 2s intervals

    function tick() {
      pollTimer = setTimeout(async () => {
        attempts++;
        try {
          const status = await pollInstallStatus(moduleName);

          if (status.install_status === 'ready' && status.is_installed) {
            showSuccess(
              `${status.name || moduleName} installed successfully`,
              status.version ? `Version ${status.version}` : ''
            );
            showToast(`Module "${status.name || moduleName}" installed`, 'success');
            // Switch to installed tab and refresh list after short delay
            setTimeout(async () => {
              switchTab('installed');
              await loadInstalledModules();
            }, 1500);
            return; // stop polling
          }

          if (status.install_status === 'failed') {
            showError(status.install_error_message || 'Installation failed');
            installBtn.disabled = false;
            return; // stop polling
          }

          // Still in_progress
          if (attempts < MAX_ATTEMPTS) {
            tick();
          } else {
            showError('Timed out waiting for install to complete. Check server logs.');
            installBtn.disabled = false;
          }
        } catch (err) {
          if (attempts < MAX_ATTEMPTS) {
            tick(); // transient error — keep polling
          } else {
            showError(`Status check failed: ${err.message}`);
            installBtn.disabled = false;
          }
        }
      }, 2000);
    }

    tick();
  }

  // ── Initial load ──────────────────────────────────────────────────────────
  await loadInstalledModules();

  // Cleanup poller if user navigates away
  return () => {
    if (pollTimer) clearTimeout(pollTimer);
  };
}

// Auto-init when loaded into SPA content area
(async () => {
  const content = document.getElementById('content');
  if (content) await render(content);
})();
