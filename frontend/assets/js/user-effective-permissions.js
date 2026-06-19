/**
 * User Effective Permissions Panel
 * Adds a "View permissions" button on each user row in the RBAC Users tab.
 * Opens a slide-in drawer showing effective permissions from GET /users/{id}/permissions.
 * Story B3-P2
 */
import { apiFetch } from './api.js';

function esc(s) { return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

function buildDrawer() {
  const el = document.createElement('div');
  el.id = 'user-perms-drawer';
  el.className = 'fixed inset-y-0 right-0 w-96 bg-white shadow-2xl flex flex-col z-50 transform translate-x-full transition-transform duration-300 border-l border-gray-200';
  el.innerHTML = `
    <div class="flex items-center justify-between px-5 py-4 border-b border-gray-200 flex-shrink-0">
      <div>
        <h2 class="text-base font-semibold text-gray-900">Effective Permissions</h2>
        <p id="uperms-user-name" class="text-xs text-gray-500"></p>
      </div>
      <button id="uperms-close" class="text-gray-400 hover:text-gray-600 p-1"><i class="ph ph-x text-lg"></i></button>
    </div>
    <div class="px-5 py-3 border-b border-gray-100 flex-shrink-0">
      <p class="text-xs text-gray-500">Permissions granted via roles and groups.</p>
    </div>
    <div class="flex-1 overflow-y-auto">
      <div id="uperms-loading" class="flex items-center justify-center h-32 text-gray-400 text-sm gap-2">
        <i class="ph ph-spinner animate-spin"></i> Loading...
      </div>
      <div id="uperms-error" class="hidden px-5 py-3 text-sm text-red-600 bg-red-50 m-4 rounded-lg"></div>
      <div id="uperms-empty" class="hidden flex items-center justify-center h-32 text-gray-400 text-sm">No permissions assigned.</div>
      <div id="uperms-content" class="hidden divide-y divide-gray-100"></div>
    </div>
    <div class="px-5 py-3 border-t border-gray-200 flex-shrink-0">
      <button id="uperms-close-footer" class="w-full px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition text-sm font-medium">Close</button>
    </div>`;
  document.body.appendChild(el);
  return el;
}

export function initUserEffectivePermissions() {
  let drawer = null;

  function getDrawer() {
    if (!drawer) {
      drawer = buildDrawer();
      drawer.querySelector('#uperms-close').onclick = close;
      drawer.querySelector('#uperms-close-footer').onclick = close;
    }
    return drawer;
  }

  function close() { document.getElementById('user-perms-drawer')?.classList.add('translate-x-full'); }

  async function openForUser(userId, userName) {
    const d = getDrawer();
    d.querySelector('#uperms-user-name').textContent = userName ?? userId;
    ['uperms-error','uperms-empty','uperms-content'].forEach(id => d.querySelector('#'+id).classList.add('hidden'));
    d.querySelector('#uperms-loading').classList.remove('hidden');
    d.classList.remove('translate-x-full');

    try {
      const res = await apiFetch(`/users/${userId}/permissions`);
      d.querySelector('#uperms-loading').classList.add('hidden');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      // Support flat list or grouped { category: [perm, ...] }
      const grouped = Array.isArray(data)
        ? { 'Permissions': data }
        : (data.grouped ?? data.by_category ?? { 'Permissions': data.permissions ?? data });

      const content = d.querySelector('#uperms-content');
      content.innerHTML = '';

      let total = 0;
      for (const [cat, perms] of Object.entries(grouped)) {
        const permArr = Array.isArray(perms) ? perms : Object.values(perms);
        if (!permArr.length) continue;
        total += permArr.length;

        const section = document.createElement('div');
        section.innerHTML = `
          <div class="px-5 py-2 bg-gray-50 text-xs font-semibold text-gray-500 uppercase tracking-wide">${esc(cat)}</div>
          <ul class="divide-y divide-gray-50">
            ${permArr.map(p => `
              <li class="flex items-center gap-3 px-5 py-2.5">
                <i class="ph ph-check-circle text-green-500 text-base flex-shrink-0"></i>
                <div>
                  <p class="text-sm font-medium text-gray-800">${esc(p.name ?? p.code ?? p)}</p>
                  ${p.source ? `<p class="text-xs text-gray-400">via ${esc(p.source)}</p>` : ''}
                </div>
              </li>`).join('')}
          </ul>`;
        content.appendChild(section);
      }

      if (!total) { d.querySelector('#uperms-empty').classList.remove('hidden'); return; }
      content.classList.remove('hidden');
    } catch (e) {
      d.querySelector('#uperms-loading').classList.add('hidden');
      const err = d.querySelector('#uperms-error');
      err.textContent = 'Failed to load permissions: ' + e.message;
      err.classList.remove('hidden');
    }
  }

  function attachButtons() {
    document.querySelectorAll('[data-user-id]').forEach(row => {
      if (row.querySelector('.btn-view-user-perms')) return;
      const userId   = row.dataset.userId;
      const userName = row.dataset.userName ?? row.querySelector('[data-user-name]')?.textContent ?? row.querySelector('td:first-child')?.textContent?.trim();
      const btn = document.createElement('button');
      btn.className = 'btn-view-user-perms inline-flex items-center gap-1 px-2 py-1 bg-white border border-gray-200 text-gray-600 rounded hover:bg-gray-50 transition text-xs';
      btn.innerHTML = '<i class="ph ph-key"></i> Permissions';
      btn.onclick = (e) => { e.stopPropagation(); openForUser(userId, userName); };
      (row.querySelector('td:last-child') ?? row).appendChild(btn);
    });
  }

  attachButtons();
  document.addEventListener('users:refreshed', attachButtons);
  document.addEventListener('rbac:users-loaded', attachButtons);
  document.addEventListener('route:loaded', (e) => { if (e.detail.route === 'rbac') setTimeout(attachButtons, 500); });
}
