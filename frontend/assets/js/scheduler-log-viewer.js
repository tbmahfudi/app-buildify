/**
 * Scheduler Job Log Viewer
 *
 * Adds a "View history" button to each job row in scheduler.html.
 * Clicking opens a drawer with execution history + log output.
 *
 * Story 24.5.1
 */
import { apiFetch } from './api.js';

const LOG_COLOURS = { ERROR: 'text-red-400', CRITICAL: 'text-red-400', WARN: 'text-yellow-400', WARNING: 'text-yellow-400' };

function colourLine(line) {
  for (const [key, cls] of Object.entries(LOG_COLOURS)) {
    if (line.toUpperCase().includes(key)) return `<span class="${cls}">${escHtml(line)}</span>`;
  }
  return `<span class="text-green-400">${escHtml(line)}</span>`;
}
function escHtml(s) { return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function relTime(iso) {
  if (!iso) return '—';
  const d = (Date.now() - new Date(iso)) / 1000;
  if (d < 60) return `${Math.round(d)}s ago`;
  if (d < 3600) return `${Math.round(d/60)}m ago`;
  return new Date(iso).toLocaleString();
}

function statusBadge(s) {
  const map = { success:'bg-green-100 text-green-700', failed:'bg-red-100 text-red-700', running:'bg-amber-100 text-amber-700' };
  const cls = map[s?.toLowerCase()] ?? 'bg-gray-100 text-gray-600';
  return `<span class="px-2 py-0.5 rounded-full text-xs font-medium ${cls}" aria-label="Status: ${escHtml(s ?? 'unknown')}">${escHtml(s ?? 'unknown')}</span>`;
}

function buildDrawer() {
  const el = document.createElement('div');
  el.id = 'job-history-drawer';
  el.className = 'fixed inset-y-0 right-0 w-[680px] max-w-full bg-white shadow-2xl flex flex-col z-50 transform translate-x-full transition-transform duration-300';
  el.innerHTML = `
    <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200 flex-shrink-0">
      <div>
        <h2 class="text-lg font-semibold text-gray-900">Run history</h2>
        <p id="drawer-job-name" class="text-sm text-gray-500"></p>
      </div>
      <button id="drawer-close" class="text-gray-400 hover:text-gray-600 p-1 rounded"><i class="ph ph-x text-xl"></i></button>
    </div>

    <!-- Executions table -->
    <div class="flex-1 overflow-y-auto flex flex-col">
      <div id="exec-table-zone" class="border-b border-gray-200" style="min-height:180px;max-height:40%">
        <div id="exec-loading" class="flex items-center justify-center h-32 text-gray-400 text-sm gap-2">
          <i class="ph ph-spinner animate-spin"></i> Loading…
        </div>
        <table id="exec-table" class="hidden w-full text-sm">
          <thead class="bg-gray-50 text-xs text-gray-500 uppercase">
            <tr>
              <th class="px-4 py-2 text-left">Started</th>
              <th class="px-4 py-2 text-left">Status</th>
              <th class="px-4 py-2 text-left">Duration</th>
              <th class="px-4 py-2 text-left">Trigger</th>
            </tr>
          </thead>
          <tbody id="exec-rows" class="divide-y divide-gray-100"></tbody>
        </table>
        <div id="exec-empty" class="hidden text-center py-8">
          <i class="ph ph-clock text-3xl text-gray-300 block mb-2"></i>
          <p class="text-sm text-gray-400">No runs yet</p>
        </div>
        <div id="exec-error" class="hidden px-4 py-3 text-sm text-red-600 bg-red-50 border-b border-red-200"></div>
      </div>

      <!-- Log pane -->
      <div class="flex-1 bg-gray-950 flex flex-col overflow-hidden">
        <div id="log-prompt" class="flex items-center justify-center flex-1 text-gray-500 text-xs">Select a run above to view its log output.</div>
        <div id="log-loading" class="hidden flex items-center justify-center flex-1 text-gray-400 text-xs gap-2"><i class="ph ph-spinner animate-spin"></i> Loading log…</div>
        <pre id="log-output"
             class="hidden text-xs font-mono p-4 overflow-auto leading-relaxed"
             style="flex: 1 1 0; min-height: 120px; resize: vertical;"
             role="log"
             aria-label="Job execution log"
             aria-live="polite"></pre>
        <div id="log-empty" class="hidden flex items-center justify-center flex-1 text-gray-500 text-xs">No log output captured for this run.</div>
        <div id="log-error" class="hidden px-4 py-2 text-xs text-red-400 bg-red-900/30"></div>
      </div>
    </div>

    <div class="px-6 py-3 border-t border-gray-200 flex-shrink-0">
      <button id="drawer-close-footer" class="w-full px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition text-sm font-medium">Close</button>
    </div>`;
  document.body.appendChild(el);
  return el;
}

export function initSchedulerLogViewer() {
  let drawer = null;
  let currentJobId = null;

  function getDrawer() {
    if (!drawer) {
      drawer = buildDrawer();
      drawer.querySelector('#drawer-close').onclick = close;
      drawer.querySelector('#drawer-close-footer').onclick = close;
    }
    return drawer;
  }

  function close() {
    const d = document.getElementById('job-history-drawer');
    if (d) { d.classList.add('translate-x-full'); currentJobId = null; }
    document.removeEventListener('keydown', _escHandler);
    // Return focus to the triggering History button
    _lastFocusTrigger?.focus();
  }

  let _escHandler = null;
  let _lastFocusTrigger = null;

  function _setupEscapeAndFocus(triggerBtn) {
    _lastFocusTrigger = triggerBtn;
    document.removeEventListener('keydown', _escHandler);
    _escHandler = (e) => { if (e.key === 'Escape') close(); };
    document.addEventListener('keydown', _escHandler);
    // Focus close button when drawer opens
    setTimeout(() => document.getElementById('drawer-close')?.focus(), 80);
  }

  async function openForJob(jobId, jobName) {
    currentJobId = jobId;
    const d = getDrawer();
    d.querySelector('#drawer-job-name').textContent = jobName || `Job ${jobId}`;

    // Reset state
    ['exec-table','exec-empty','exec-error'].forEach(id => d.querySelector(`#${id}`).classList.add('hidden'));
    d.querySelector('#exec-loading').classList.remove('hidden');
    ['log-prompt','log-loading','log-output','log-empty','log-error'].forEach(id => {
      const el = d.querySelector(`#${id}`);
      el.classList.add('hidden');
    });
    d.querySelector('#log-prompt').classList.remove('hidden');
    d.classList.remove('translate-x-full');
    _setupEscapeAndFocus(null);

    try {
      const res = await apiFetch(`/scheduler/jobs/${jobId}/executions`);
      d.querySelector('#exec-loading').classList.add('hidden');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const rows = Array.isArray(data) ? data : (data.items ?? data.executions ?? []);
      if (!rows.length) { d.querySelector('#exec-empty').classList.remove('hidden'); return; }

      const tbody = d.querySelector('#exec-rows');
      tbody.innerHTML = rows.map(r => `
        <tr class="exec-row hover:bg-blue-50 cursor-pointer transition" data-exec-id="${escHtml(r.id)}">
          <td class="px-4 py-2 text-gray-700">${relTime(r.started_at ?? r.created_at)}</td>
          <td class="px-4 py-2">${statusBadge(r.status)}</td>
          <td class="px-4 py-2 text-gray-600">${r.duration_ms != null ? (r.duration_ms < 1000 ? r.duration_ms+'ms' : (r.duration_ms/1000).toFixed(1)+'s') : '—'}</td>
          <td class="px-4 py-2 text-gray-600">${escHtml(r.trigger ?? r.trigger_type ?? 'manual')}</td>
        </tr>`).join('');
      d.querySelector('#exec-table').classList.remove('hidden');

      tbody.querySelectorAll('.exec-row').forEach(row => {
        row.setAttribute('tabindex', '0');
        row.onclick = () => loadLog(row.dataset.execId, tbody);
        row.onkeydown = (e) => {
          if (e.key === 'Enter') loadLog(row.dataset.execId, tbody);
          if (e.key === 'ArrowDown') { e.preventDefault(); row.nextElementSibling?.focus(); }
          if (e.key === 'ArrowUp')   { e.preventDefault(); row.previousElementSibling?.focus(); }
        };
      });
    } catch (e) {
      d.querySelector('#exec-loading').classList.add('hidden');
      const err = d.querySelector('#exec-error');
      err.textContent = 'Failed to load executions: ' + e.message;
      err.classList.remove('hidden');
    }
  }

  async function loadLog(execId, tbody) {
    tbody.querySelectorAll('.exec-row').forEach(r => r.classList.remove('bg-blue-50'));
    tbody.querySelector(`[data-exec-id="${execId}"]`)?.classList.add('bg-blue-50');

    const d = document.getElementById('job-history-drawer');
    ['log-prompt','log-output','log-empty','log-error'].forEach(id => d.querySelector(`#${id}`).classList.add('hidden'));
    d.querySelector('#log-loading').classList.remove('hidden');

    try {
      const res = await apiFetch(`/scheduler/executions/${execId}/logs`);
      d.querySelector('#log-loading').classList.add('hidden');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const lines = Array.isArray(data) ? data : (data.lines ?? data.logs ?? []);
      if (!lines.length) { d.querySelector('#log-empty').classList.remove('hidden'); return; }
      const pre = d.querySelector('#log-output');
      pre.innerHTML = lines.map(l => colourLine(typeof l === 'string' ? l : l.message ?? JSON.stringify(l))).join('\n');
      pre.classList.remove('hidden');
    } catch (e) {
      d.querySelector('#log-loading').classList.add('hidden');
      const err = d.querySelector('#log-error');
      err.textContent = 'Failed to load log: ' + e.message;
      err.classList.remove('hidden');
    }
  }

  // Inject "View history" buttons into existing job rows
  function attachButtons() {
    document.querySelectorAll('[data-job-id]').forEach(row => {
      if (row.querySelector('.btn-view-history')) return;
      const jobId = row.dataset.jobId;
      const jobName = row.dataset.jobName ?? row.querySelector('[data-job-name]')?.textContent ?? `Job ${jobId}`;
      const btn = document.createElement('button');
      btn.className = 'btn-view-history inline-flex items-center gap-1 px-3 py-1.5 bg-white border border-gray-300 text-gray-600 rounded-lg hover:bg-gray-50 transition text-xs font-medium ml-2';
      btn.innerHTML = '<i class="ph ph-clock-clockwise"></i> History';
      btn.onclick = (e) => { e.stopPropagation(); _lastFocusTrigger = btn; openForJob(jobId, jobName); };
      const actionsCell = row.querySelector('td:last-child') ?? row;
      actionsCell.appendChild(btn);
    });
  }

  // Run once immediately and also after table refresh events
  attachButtons();
  document.addEventListener('scheduler:refreshed', attachButtons);
}
