/**
 * Permission Matrix Table
 * Renders a grouped role × permission grid.
 * Story B3-P2
 */
import { apiFetch } from './api.js';

function esc(s) { return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

function buildPanel() {
  const el = document.createElement('div');
  el.id = 'perm-matrix-panel';
  el.className = 'hidden bg-white rounded-xl shadow-sm overflow-hidden';
  el.innerHTML = `
    <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200">
      <div>
        <h2 class="text-base font-semibold text-gray-900">Permission Matrix</h2>
        <p class="text-xs text-gray-500">All roles and their assigned permissions by category</p>
      </div>
      <button id="pmatrix-refresh" class="inline-flex items-center gap-2 px-3 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition text-sm">
        <i class="ph ph-arrow-clockwise"></i> Refresh
      </button>
    </div>
    <div id="pmatrix-loading" class="flex items-center justify-center h-40 text-gray-400 text-sm gap-2">
      <i class="ph ph-spinner animate-spin"></i> Loading permissions...
    </div>
    <div id="pmatrix-error" class="hidden px-6 py-4 text-sm text-red-600 bg-red-50"></div>
    <div id="pmatrix-table-wrap" class="hidden overflow-x-auto">
      <table id="pmatrix-table" class="w-full text-xs border-collapse">
        <thead id="pmatrix-head" class="bg-gray-50 sticky top-0 z-10"></thead>
        <tbody id="pmatrix-body" class="divide-y divide-gray-100"></tbody>
      </table>
    </div>`;
  return el;
}

async function loadMatrix() {
  const loading = document.getElementById('pmatrix-loading');
  const error   = document.getElementById('pmatrix-error');
  const wrap    = document.getElementById('pmatrix-table-wrap');
  const head    = document.getElementById('pmatrix-head');
  const body    = document.getElementById('pmatrix-body');

  [error, wrap].forEach(el => el?.classList.add('hidden'));
  loading?.classList.remove('hidden');

  try {
    const [permRes, rolesRes] = await Promise.all([
      apiFetch('/permissions/grouped'),
      apiFetch('/rbac/roles?limit=50'),
    ]);
    loading?.classList.add('hidden');
    if (!permRes.ok) throw new Error(`Permissions: HTTP ${permRes.status}`);
    if (!rolesRes.ok) throw new Error(`Roles: HTTP ${rolesRes.status}`);

    const grouped = await permRes.json(); // { category: [{ id, name, code }] }
    const rolesData = await rolesRes.json();
    const roles = Array.isArray(rolesData) ? rolesData : (rolesData.items ?? rolesData.roles ?? []);

    // Build role → set of permission codes
    const rolePerms = {};
    roles.forEach(r => {
      rolePerms[r.id] = new Set((r.permissions ?? []).map(p => p.code ?? p.id ?? p));
    });

    // Header row
    head.innerHTML = `<tr>
      <th class="px-4 py-3 text-left text-gray-600 font-semibold sticky left-0 bg-gray-50 min-w-[180px]">Permission</th>
      ${roles.map(r => `<th class="px-3 py-3 text-center text-gray-600 font-medium min-w-[90px]">${esc(r.name)}</th>`).join('')}
    </tr>`;

    // Body rows grouped by category
    let rows = '';
    for (const [cat, perms] of Object.entries(grouped)) {
      rows += `<tr class="bg-gray-50"><td colspan="${roles.length+1}" class="px-4 py-2 text-xs font-bold text-gray-500 uppercase tracking-wide">${esc(cat)}</td></tr>`;
      perms.forEach(p => {
        rows += `<tr class="hover:bg-blue-50 transition">
          <td class="px-4 py-2 sticky left-0 bg-white text-gray-800 font-medium">${esc(p.name ?? p.code)}</td>
          ${roles.map(r => {
            const has = rolePerms[r.id]?.has(p.code ?? p.id) ?? false;
            return `<td class="px-3 py-2 text-center">${has
              ? '<i class="ph ph-check-circle text-green-500 text-base"></i>'
              : '<span class="block w-4 h-0.5 bg-gray-200 mx-auto"></span>'}</td>`;
          }).join('')}
        </tr>`;
      });
    }
    body.innerHTML = rows || `<tr><td colspan="${roles.length+1}" class="px-4 py-8 text-center text-gray-400">No permissions found.</td></tr>`;
    wrap?.classList.remove('hidden');
  } catch (e) {
    loading?.classList.add('hidden');
    if (error) { error.textContent = 'Failed to load matrix: ' + e.message; error.classList.remove('hidden'); }
  }
}

export function initPermissionMatrix() {
  // Find a container to inject into — look for an existing "Permissions" tab panel
  const rbacContent = document.querySelector('#content-roles, [id*="rbac"][id*="content"], .rbac-content');
  if (!rbacContent) return;

  // Add a "Permission Matrix" tab if there's a tab strip
  const tabStrip = document.querySelector('[role="tablist"], .rbac-tab-strip, nav.flex.gap-4');
  if (tabStrip && !document.getElementById('tab-perm-matrix')) {
    const btn = document.createElement('button');
    btn.id = 'tab-perm-matrix';
    btn.className = 'rbac-tab px-4 py-3 text-sm font-medium border-b-2 border-transparent text-gray-500 hover:text-gray-700';
    btn.innerHTML = '<i class="ph ph-table mr-2"></i>Permission Matrix';
    tabStrip.appendChild(btn);

    const panel = buildPanel();
    rbacContent.parentNode.appendChild(panel);

    btn.onclick = () => {
      document.querySelectorAll('.rbac-content, .rbac-tab-content').forEach(p => p.classList.add('hidden'));
      document.querySelectorAll('.rbac-tab').forEach(t => {
        t.classList.remove('border-blue-600','text-blue-600');
        t.classList.add('border-transparent','text-gray-500');
      });
      panel.classList.remove('hidden');
      btn.classList.add('border-blue-600','text-blue-600');
      btn.classList.remove('border-transparent','text-gray-500');
      loadMatrix();
    };

    document.getElementById('pmatrix-refresh')?.addEventListener('click', loadMatrix);
  }
}
