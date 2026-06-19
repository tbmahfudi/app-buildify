/**
 * Dashboard Share + Snapshot Buttons
 * Adds Share and Snapshot actions to the dashboard header.
 * Story B3-P2
 */
import { apiFetch } from './api.js';

function esc(s) { return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

function showToast(msg, type = 'success') {
  const el = document.createElement('div');
  const colour = type === 'error' ? 'bg-red-600' : 'bg-green-600';
  el.className = `fixed top-4 right-4 z-50 flex items-center gap-3 ${colour} text-white px-5 py-3 rounded-xl shadow-lg text-sm`;
  el.innerHTML = `<i class="ph ${type === 'error' ? 'ph-warning-circle' : 'ph-check-circle'} text-xl"></i><span>${esc(msg)}</span>`;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 5000);
}

async function shareDashboard(dashboardId) {
  try {
    const res = await apiFetch(`/dashboards/${dashboardId}/share`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ expires_in_days: 7 }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const shareUrl = data.share_url ?? data.url ?? window.location.href;

    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 z-50 flex items-center justify-center bg-black/60';
    modal.innerHTML = `
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-2">Share Dashboard</h3>
        <p class="text-sm text-gray-500 mb-4">Anyone with this link can view this dashboard (read-only) for 7 days.</p>
        <div class="flex gap-2">
          <input id="share-url-input" type="text" value="${esc(shareUrl)}" readonly
            class="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm bg-gray-50 focus:outline-none">
          <button id="copy-share-url" class="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition text-sm font-medium">
            <i class="ph ph-copy"></i> Copy
          </button>
        </div>
        <div class="flex justify-end mt-4">
          <button class="close-modal px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition text-sm font-medium">Close</button>
        </div>
      </div>`;
    document.body.appendChild(modal);
    modal.querySelector('.close-modal').onclick = () => modal.remove();
    modal.querySelector('#copy-share-url').onclick = () => {
      navigator.clipboard.writeText(shareUrl).then(() => {
        modal.querySelector('#copy-share-url').innerHTML = '<i class="ph ph-check"></i> Copied!';
        setTimeout(() => { modal.querySelector('#copy-share-url').innerHTML = '<i class="ph ph-copy"></i> Copy'; }, 2000);
      });
    };
  } catch (e) {
    showToast('Could not generate share link: ' + e.message, 'error');
  }
}

async function snapshotDashboard(dashboardId) {
  const btn = document.getElementById('btn-snapshot-dashboard');
  if (btn) { btn.disabled = true; btn.innerHTML = '<i class="ph ph-spinner animate-spin"></i> Saving...'; }
  try {
    const res = await apiFetch(`/dashboards/${dashboardId}/snapshot`, { method: 'POST' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    showToast(`Snapshot saved: ${data.name ?? data.snapshot_id ?? 'done'}`);
  } catch (e) {
    showToast('Snapshot failed: ' + e.message, 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.innerHTML = '<i class="ph ph-camera"></i> Snapshot'; }
  }
}

export function initDashboardShareSnapshot() {
  function inject() {
    const header = document.querySelector('#dashboard-header-actions, .dashboard-actions, [id*="dashboard"] .flex.gap-3');
    if (!header || document.getElementById('btn-share-dashboard')) return;

    const dashboardId = window.currentDashboardId
      ?? document.getElementById('current-dashboard-id')?.value
      ?? new URLSearchParams(window.location.hash.split('?')[1] ?? '').get('id');
    if (!dashboardId) return;

    const shareBtn = document.createElement('button');
    shareBtn.id = 'btn-share-dashboard';
    shareBtn.className = 'inline-flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition text-sm font-medium';
    shareBtn.innerHTML = '<i class="ph ph-share-network"></i> Share';
    shareBtn.onclick = () => shareDashboard(dashboardId);

    const snapBtn = document.createElement('button');
    snapBtn.id = 'btn-snapshot-dashboard';
    snapBtn.className = 'inline-flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition text-sm font-medium';
    snapBtn.innerHTML = '<i class="ph ph-camera"></i> Snapshot';
    snapBtn.onclick = () => snapshotDashboard(dashboardId);

    header.prepend(snapBtn);
    header.prepend(shareBtn);
  }

  inject();
  document.addEventListener('route:loaded', (e) => {
    if (e.detail.route === 'dashboard' || e.detail.route?.startsWith('dashboards-list')) setTimeout(inject, 300);
  });
  document.addEventListener('dashboard:loaded', inject);
}
