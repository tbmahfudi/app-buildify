/**
 * Builder Version History Sidebar
 *
 * Adds a "History" button to the builder toolbar and a slide-in drawer
 * listing page versions with preview and restore actions.
 *
 * Story 24.6.1
 */
import { apiFetch } from './api.js';

function esc(s) { return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function relTime(iso) {
  if (!iso) return '—';
  const d = (Date.now() - new Date(iso)) / 1000;
  if (d < 60) return `${Math.round(d)}s ago`;
  if (d < 3600) return `${Math.round(d/60)}m ago`;
  if (d < 86400) return `${Math.round(d/3600)}h ago`;
  return new Date(iso).toLocaleDateString();
}

function buildDrawer() {
  const el = document.createElement('div');
  el.id = 'version-history-drawer';
  el.className = 'fixed inset-y-0 right-0 w-80 bg-white shadow-2xl flex flex-col z-50 transform translate-x-full transition-transform duration-300 border-l border-gray-200';
  el.innerHTML = `
    <div class="flex items-center justify-between px-5 py-4 border-b border-gray-200 flex-shrink-0">
      <div>
        <h2 class="text-base font-semibold text-gray-900">Version history</h2>
        <p id="vh-page-name" class="text-xs text-gray-500"></p>
      </div>
      <button id="vh-close" class="text-gray-400 hover:text-gray-600 p-1"><i class="ph ph-x text-lg"></i></button>
    </div>

    <div class="flex-1 overflow-y-auto" id="vh-list">
      <div id="vh-loading" class="flex items-center justify-center h-32 text-gray-400 text-sm gap-2">
        <i class="ph ph-spinner animate-spin"></i> Loading versions…
      </div>
      <div id="vh-empty" class="hidden text-center py-10">
        <i class="ph ph-files text-3xl text-gray-300 block mb-2"></i>
        <p class="text-sm text-gray-400">No versions saved yet</p>
        <p class="text-xs text-gray-300 mt-1">Save the page to create the first version.</p>
      </div>
      <div id="vh-error" class="hidden px-4 py-3 text-sm text-red-600 bg-red-50 m-4 rounded-lg"></div>
      <ul id="vh-items" class="divide-y divide-gray-100" role="list"></ul>
    </div>

    <div class="px-5 py-3 border-t border-gray-200 flex-shrink-0">
      <button id="vh-close-footer" class="w-full px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition text-sm font-medium">Close</button>
    </div>`;
  document.body.appendChild(el);
  return el;
}

function versionItem(v, isLive, onPreview, onRestore) {
  const li = document.createElement('li');
  const vNum = v.version_number ?? v.version ?? "?"
  const vAuthor = v.created_by_email ?? v.author ?? "unknown"
  const vTime = relTime(v.created_at)
  li.className = "px-4 py-3 hover:bg-gray-50 transition"
  li.setAttribute("role", "listitem")
  li.setAttribute("aria-label", `Version ${vNum}, saved ${vTime} by ${vAuthor}`)
  li.innerHTML = `
    <div class="flex items-center gap-2 mb-1">
      ${isLive ? '<span class="px-2 py-0.5 bg-green-100 text-green-700 rounded-full text-xs font-medium">Live</span>' : ''}
      <span class="text-xs font-mono text-gray-500">#${esc(v.version_number ?? v.version ?? '?')}</span>
      <span class="px-2 py-0.5 bg-gray-100 text-gray-500 rounded-full text-xs">${esc(v.save_type ?? (v.is_autosave ? 'Autosave' : 'Manual'))}</span>
    </div>
    <div class="flex items-center justify-between">
      <div>
        <p class="text-xs text-gray-500">${relTime(v.created_at)}</p>
        <p class="text-xs text-gray-400">${esc(v.created_by_email ?? v.author ?? '')}</p>
      </div>
      <div class="flex gap-1 action-row">
        <button class="preview-btn inline-flex items-center gap-1 px-2 py-1 bg-white border border-gray-200 text-gray-600 rounded hover:bg-gray-50 text-xs transition">
          <i class="ph ph-eye"></i> Preview
        </button>
        <button class="restore-btn inline-flex items-center gap-1 px-2 py-1 bg-white border border-gray-200 text-gray-600 rounded hover:bg-gray-50 text-xs transition">
          <i class="ph ph-arrow-counter-clockwise"></i> Restore
        </button>
      </div>
      <div class="confirm-row hidden flex items-center gap-2">
        <span class="text-xs text-amber-700">Unsaved changes will be lost.</span>
        <button class="confirm-yes px-2 py-1 bg-red-600 text-white rounded text-xs hover:bg-red-700 transition">Restore</button>
        <button class="confirm-no px-2 py-1 bg-white border border-gray-200 text-gray-600 rounded text-xs hover:bg-gray-50 transition">Cancel</button>
      </div>
    </div>`;

  li.querySelector('.preview-btn').onclick = () => onPreview(v);
  const restoreBtn = li.querySelector('.restore-btn');
  restoreBtn.onclick = () => {
    document.querySelectorAll('#vh-items .restore-btn').forEach(b => { if (b !== restoreBtn) { b.disabled = true; b.classList.add('opacity-50'); } });
    li.querySelector('.action-row').classList.add('hidden');
    li.querySelector('.confirm-row').classList.remove('hidden');
    setTimeout(() => li.querySelector('.confirm-yes')?.focus(), 30);
  };
  li.querySelector('.confirm-no').onclick = () => {
    li.querySelector('.confirm-row').classList.add('hidden');
    li.querySelector('.action-row').classList.remove('hidden');
    document.querySelectorAll('#vh-items .restore-btn').forEach(b => { b.disabled = false; b.classList.remove('opacity-50'); });
    restoreBtn.focus();
  };
  li.querySelector('.confirm-yes').onclick = () => onRestore(v, li);
  return li;
}

export function initBuilderVersionHistory() {
  let drawer = null;
  let currentPageId = null;
  let notification = null;

  function showNotification(msg) {
    if (notification) notification.remove();
    notification = document.createElement('div');
    notification.className = 'fixed top-4 right-4 z-50 flex items-center gap-3 bg-green-600 text-white px-5 py-3 rounded-xl shadow-lg';
    notification.innerHTML = `<i class="ph ph-check-circle text-xl"></i><span>${esc(msg)}</span>`;
    document.body.appendChild(notification);
    setTimeout(() => notification?.remove(), 5000);
  }

  function getDrawer() {
    if (!drawer) {
      drawer = buildDrawer();
      drawer.querySelector('#vh-close').onclick = close;
      drawer.querySelector('#vh-close-footer').onclick = close;
    }
    return drawer;
  }

  let _escDrawer = null; let _lastFocus = null;
  function close() {
    document.getElementById('version-history-drawer')?.classList.add('translate-x-full');
    document.removeEventListener('keydown', _escDrawer);
    _lastFocus?.focus();
  }
  function _openEsc(btn) {
    _lastFocus = btn;
    document.removeEventListener('keydown', _escDrawer);
    _escDrawer = (e) => { if (e.key === 'Escape') close(); };
    document.addEventListener('keydown', _escDrawer);
    setTimeout(() => document.getElementById('vh-close')?.focus(), 80);
  }

  async function open(pageId, pageName) {
    currentPageId = pageId;
    const d = getDrawer();
    d.querySelector('#vh-page-name').textContent = pageName ?? '';
    ['vh-empty','vh-error'].forEach(id => d.querySelector(`#${id}`).classList.add('hidden'));
    d.querySelector('#vh-loading').classList.remove('hidden');
    d.querySelector('#vh-items').innerHTML = '';
    d.classList.remove('translate-x-full');
    _openEsc(null);

    try {
      const res = await apiFetch(`/builder-pages/${pageId}/versions`);
      d.querySelector('#vh-loading').classList.add('hidden');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const versions = Array.isArray(data) ? data : (data.versions ?? data.items ?? []);
      if (!versions.length) { d.querySelector('#vh-empty').classList.remove('hidden'); return; }

      const ul = d.querySelector('#vh-items');
      versions.forEach((v, i) => {
        ul.appendChild(versionItem(v, i === 0, previewVersion, restoreVersion));
      });
    } catch (e) {
      d.querySelector('#vh-loading').classList.add('hidden');
      const err = d.querySelector('#vh-error');
      err.textContent = 'Could not load versions: ' + e.message;
      err.classList.remove('hidden');
    }
  }

  async function previewVersion(v) {
    const modal = document.createElement('div');
    modal.setAttribute('role','dialog'); modal.setAttribute('aria-modal','true'); modal.setAttribute('aria-labelledby','vh-preview-title');
    modal.className = 'fixed inset-0 z-50 flex items-center justify-center bg-black/60';
    modal.innerHTML = `
      <div class="bg-white rounded-2xl shadow-2xl w-4/5 max-w-5xl flex flex-col max-h-[90vh]">
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <div>
            <h2 id="vh-preview-title" class="font-semibold text-gray-900">Version #${esc(v.version_number ?? v.version)} — preview</h2>
            <p class="text-xs text-gray-500">${relTime(v.created_at)}</p>
          </div>
          <button class="close-modal text-gray-400 hover:text-gray-600"><i class="ph ph-x text-xl"></i></button>
        </div>
        <div class="bg-blue-50 border-b border-blue-100 px-5 py-2 flex items-center gap-2 text-sm text-blue-700">
          <i class="ph ph-info"></i> This is a read-only preview. No changes have been made.
        </div>
        <div class="flex-1 overflow-auto p-6 bg-gray-50 rounded-b-2xl">
          <div style="pointer-events:none" class="bg-white rounded-lg border border-gray-200 overflow-auto max-h-[55vh] p-4">
            <pre class="text-xs overflow-auto">${esc(JSON.stringify(v.page_data ?? v.content ?? v, null, 2))}</pre>
          </div>
        </div>
        <div class="flex justify-end gap-3 px-6 py-4 border-t border-gray-200">
          <button class="close-modal inline-flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition text-sm font-medium">Close</button>
          <button class="restore-from-modal inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition text-sm font-medium">
            <i class="ph ph-arrow-counter-clockwise"></i> Restore this version
          </button>
        </div>
      </div>`;
    document.body.appendChild(modal);
    let _escM = null;
    const closeM = () => { modal.remove(); document.removeEventListener('keydown', _escM); };
    _escM = (e) => { if (e.key === 'Escape') closeM(); };
    document.addEventListener('keydown', _escM);
    setTimeout(() => modal.querySelector('.close-modal')?.focus(), 50);
    modal.querySelectorAll('.close-modal').forEach(b => b.onclick = closeM);
    modal.querySelector('.restore-from-modal').onclick = async () => {
      if (!confirm('Unsaved changes will be lost. Restore this version?')) return;
      closeM();
      await doRestore(v.id ?? v.version_id);
    };
  }

  async function restoreVersion(v, li) {
    await doRestore(v.id ?? v.version_id, li);
  }

  async function doRestore(versionId, li) {
    const confirmYes = li?.querySelector('.confirm-yes');
    if (confirmYes) { confirmYes.disabled = true; confirmYes.textContent = 'Restoring…'; }
    try {
      const res = await apiFetch(`/builder-pages/${currentPageId}/restore/${versionId}`, { method: 'POST' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      document.querySelectorAll('#vh-items .restore-btn').forEach(b => { b.disabled = false; b.classList.remove('opacity-50'); });
      close();
      showNotification(`Restored to version #${versionId}.`);
      // Signal the builder to reload its canvas
      document.dispatchEvent(new CustomEvent('builder:version-restored', { detail: { versionId } }));
    } catch (e) {
      if (li) {
        const err = document.createElement('p');
        err.className = 'text-xs text-red-600 mt-1';
        err.textContent = 'Restore failed: ' + e.message;
        li.querySelector('.confirm-row').after(err);
      }
    } finally {
      if (confirmYes) { confirmYes.disabled = false; confirmYes.textContent = 'Restore'; }
    }
  }

  // Inject "History" button into the builder toolbar
  function injectButton() {
    const toolbar = document.querySelector('#builder-container > div, .builder-toolbar, [id*="builder"] .flex.items-center');
    const existing = document.getElementById('btn-version-history');
    if (existing || !toolbar) return;

    const btn = document.createElement('button');
    btn.id = 'btn-version-history';
    btn.className = 'flex-shrink-0 inline-flex items-center gap-1 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition';
    btn.innerHTML = '<i class="ph-duotone ph-clock-clockwise"></i> History';
    btn.onclick = () => {
      const pageId   = window.currentBuilderPageId ?? document.getElementById('current-page-id')?.value;
      const pageName = document.getElementById('current-page-name')?.textContent ?? 'This page';
      if (!pageId) { alert('Save the page first to enable version history.'); return; }
      open(pageId, pageName);
    };

    // Insert before the last button group in the toolbar header
    const lastBtnGroup = toolbar.querySelector('.flex.items-center.gap-2:last-child, .flex.gap-2:last-child');
    if (lastBtnGroup) {
      lastBtnGroup.insertBefore(btn, lastBtnGroup.firstChild);
    } else {
      toolbar.appendChild(btn);
    }
  }

  // Try immediately, then after route loads (builder JS may not have run yet)
  injectButton();
  document.addEventListener('route:loaded', (e) => { if (e.detail.route === 'builder') setTimeout(injectButton, 200); });
}
