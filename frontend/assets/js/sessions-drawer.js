/**
 * sessions-drawer.js  —  Wave 2 / Screen 1
 *
 * "My Sessions" right-side FlexDrawer (480 px).
 * Lists active JWT sessions for the current user.
 * Wires: GET  /api/v1/auth/me/sessions
 *        DELETE /api/v1/auth/me/sessions/{jti}
 *        DELETE /api/v1/auth/me/sessions   (revoke-all-others)
 */

import { apiFetch } from './api.js';

// ── helpers ──────────────────────────────────────────────────────────────────

function fmtDate(iso) {
  if (!iso) return '—';
  try {
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: 'medium', timeStyle: 'short'
    }).format(new Date(iso));
  } catch { return iso; }
}

function deviceIcon(hint) {
  if (!hint) return 'ph-duotone ph-desktop';
  const h = hint.toLowerCase();
  if (h.includes('mobile') || h.includes('android') || h.includes('iphone')) return 'ph-duotone ph-device-mobile';
  if (h.includes('tablet') || h.includes('ipad')) return 'ph-duotone ph-device-tablet';
  return 'ph-duotone ph-desktop';
}

function renderSessionCard(session, isCurrent) {
  return `
    <div class="flex items-start gap-3 p-4 bg-white border border-gray-200 rounded-xl shadow-sm
                ${isCurrent ? 'border-blue-300 bg-blue-50/40' : ''}"
         data-jti="${session.jti}">
      <div class="w-9 h-9 flex-shrink-0 rounded-lg bg-gray-100 flex items-center justify-center text-gray-500">
        <i class="${deviceIcon(session.device_hint)} text-lg"></i>
      </div>
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 flex-wrap">
          <span class="text-sm font-medium text-gray-900 truncate">
            ${session.device_hint || 'Unknown device'}
          </span>
          ${isCurrent ? `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-700 border border-blue-200">
            <i class="ph ph-check-circle-fill text-xs"></i> Current
          </span>` : ''}
        </div>
        <p class="text-xs text-gray-500 mt-0.5">IP: ${session.ip || '—'}</p>
        <p class="text-xs text-gray-400">Last seen: ${fmtDate(session.last_seen)}</p>
      </div>
      ${!isCurrent ? `
      <button class="session-revoke-btn flex-shrink-0 text-xs px-3 py-1.5 rounded-lg border border-red-200
                     text-red-600 hover:bg-red-50 transition"
              data-jti="${session.jti}" aria-label="Revoke this session">
        Revoke
      </button>` : ''}
    </div>`;
}

// ── Drawer ────────────────────────────────────────────────────────────────────

let drawerEl = null;

function getOrCreateDrawer() {
  if (!drawerEl) {
    drawerEl = document.createElement('div');
    drawerEl.id = 'sessions-drawer-host';
    document.body.appendChild(drawerEl);
  }
  return drawerEl;
}

export async function openSessionsDrawer() {
  const host = getOrCreateDrawer();

  // Build drawer shell
  host.innerHTML = `
    <!-- backdrop -->
    <div id="sd-backdrop"
         class="fixed inset-0 bg-gray-900/50 z-40 transition-opacity duration-300 opacity-0"></div>

    <!-- panel -->
    <div id="sd-panel"
         class="fixed top-0 right-0 bottom-0 z-50 w-[480px] max-w-full bg-white shadow-2xl
                flex flex-col translate-x-full transition-transform duration-300">

      <!-- header -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200">
        <div>
          <h2 class="text-base font-semibold text-gray-900 flex items-center gap-2">
            <i class="ph-duotone ph-devices text-blue-600 text-xl"></i>
            My Sessions
          </h2>
          <p class="text-xs text-gray-500 mt-0.5">Manage devices signed in to your account</p>
        </div>
        <button id="sd-close" aria-label="Close sessions panel"
                class="w-8 h-8 rounded-lg hover:bg-gray-100 flex items-center justify-center text-gray-500 hover:text-gray-900 transition">
          <i class="ph ph-x text-lg"></i>
        </button>
      </div>

      <!-- body -->
      <div id="sd-body" class="flex-1 overflow-y-auto px-6 py-4 space-y-3">
        <!-- skeleton -->
        ${Array.from({length: 3}).map(() => `
          <div class="animate-pulse flex gap-3 p-4 bg-gray-50 rounded-xl border border-gray-100">
            <div class="w-9 h-9 rounded-lg bg-gray-200 flex-shrink-0"></div>
            <div class="flex-1 space-y-2">
              <div class="h-3 bg-gray-200 rounded w-3/5"></div>
              <div class="h-2 bg-gray-200 rounded w-2/5"></div>
              <div class="h-2 bg-gray-200 rounded w-1/3"></div>
            </div>
          </div>`).join('')}
      </div>

      <!-- footer -->
      <div class="px-6 py-4 border-t border-gray-200">
        <button id="sd-revoke-all"
                class="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg border border-red-200
                       text-red-600 text-sm font-medium hover:bg-red-50 transition">
          <i class="ph-duotone ph-prohibit text-lg"></i>
          Revoke all other sessions
        </button>
      </div>
    </div>`;

  // Animate in
  requestAnimationFrame(() => {
    host.querySelector('#sd-backdrop').classList.replace('opacity-0', 'opacity-100');
    host.querySelector('#sd-panel').classList.replace('translate-x-full', 'translate-x-0');
  });

  function close() {
    host.querySelector('#sd-backdrop').classList.replace('opacity-100', 'opacity-0');
    host.querySelector('#sd-panel').classList.replace('translate-x-0', 'translate-x-full');
    setTimeout(() => { host.innerHTML = ''; }, 320);
  }

  host.querySelector('#sd-close').addEventListener('click', close);
  host.querySelector('#sd-backdrop').addEventListener('click', close);
  document.addEventListener('keydown', function esc(e) {
    if (e.key === 'Escape') { close(); document.removeEventListener('keydown', esc); }
  });

  // Load sessions
  async function loadSessions() {
    const body = host.querySelector('#sd-body');
    try {
      const res = await apiFetch('/auth/me/sessions');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const sessions = Array.isArray(data) ? data : (data.sessions || []);

      if (!sessions.length) {
        body.innerHTML = `
          <div class="flex flex-col items-center justify-center py-12 text-gray-400">
            <i class="ph ph-devices text-4xl mb-3"></i>
            <p class="text-sm font-medium">No other sessions found</p>
          </div>`;
        return;
      }

      body.innerHTML = sessions.map(s => renderSessionCard(s, !!s.is_current)).join('');

      // Revoke individual
      body.addEventListener('click', async e => {
        const btn = e.target.closest('.session-revoke-btn');
        if (!btn) return;
        const jti = btn.dataset.jti;
        btn.disabled = true;
        btn.textContent = 'Revoking…';
        try {
          const r = await apiFetch(`/auth/me/sessions/${jti}`, { method: 'DELETE' });
          if (!r.ok) throw new Error(`HTTP ${r.status}`);
          btn.closest('[data-jti]').remove();
        } catch (err) {
          btn.textContent = 'Error';
          setTimeout(() => { btn.disabled = false; btn.textContent = 'Revoke'; }, 2000);
        }
      });

    } catch (err) {
      body.innerHTML = `
        <div class="p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          <i class="ph ph-warning-circle mr-2"></i>Failed to load sessions: ${err.message}
        </div>`;
    }
  }

  await loadSessions();

  // Revoke all others
  host.querySelector('#sd-revoke-all').addEventListener('click', () => {
    // Confirmation modal
    const confirmHost = document.createElement('div');
    document.body.appendChild(confirmHost);
    confirmHost.innerHTML = `
      <div class="fixed inset-0 bg-black/50 z-[60] flex items-center justify-center p-4">
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-sm p-6">
          <h3 class="text-base font-semibold text-gray-900 mb-2">Revoke all other sessions?</h3>
          <p class="text-sm text-gray-600 mb-5">
            All devices other than this one will be signed out immediately.
          </p>
          <div class="flex gap-3 justify-end">
            <button id="ra-cancel" class="px-4 py-2 rounded-lg border text-gray-600 hover:bg-gray-50 text-sm transition">Cancel</button>
            <button id="ra-confirm" class="px-4 py-2 rounded-lg bg-red-600 text-white hover:bg-red-700 text-sm transition">Revoke all</button>
          </div>
        </div>
      </div>`;

    confirmHost.querySelector('#ra-cancel').onclick = () => confirmHost.remove();
    confirmHost.querySelector('#ra-confirm').onclick = async () => {
      const btn = confirmHost.querySelector('#ra-confirm');
      btn.disabled = true;
      btn.textContent = 'Revoking…';
      try {
        const r = await apiFetch('/auth/me/sessions', { method: 'DELETE' });
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        confirmHost.remove();
        await loadSessions();
      } catch (err) {
        btn.textContent = 'Error — try again';
        btn.disabled = false;
      }
    };
  });
}
