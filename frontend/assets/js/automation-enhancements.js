/**
 * Automation Enhancements — Execution History tab + Rule Test panel
 *
 * Adds:
 *   - "Execution History" tab to nocode-automations.html
 *   - Inline "Test" accordion panel on each rule card
 *
 * Story 24.4.1 + 24.4.2
 */
import { apiFetch } from './api.js';

function esc(s) { return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function badge(s, map) {
  const cls = map[s?.toLowerCase()] ?? 'bg-gray-100 text-gray-600';
  return `<span class="px-2 py-0.5 rounded-full text-xs font-medium ${cls}">${esc(s)}</span>`;
}
function relTime(iso) {
  if (!iso) return '—';
  const d = (Date.now() - new Date(iso)) / 1000;
  if (d < 60) return `${Math.round(d)}s ago`;
  if (d < 3600) return `${Math.round(d/60)}m ago`;
  return new Date(iso).toLocaleString();
}

// ── Execution History Tab ──────────────────────────────────────────────────

const STATUS_MAP = { success:'bg-green-100 text-green-700', failed:'bg-red-100 text-red-700', partial:'bg-amber-100 text-amber-700' };

function buildHistoryTab() {
  const panel = document.createElement('div');
  panel.id = 'exec-history-panel';
  panel.className = 'hidden space-y-4';
  panel.innerHTML = `
    <!-- Filter bar -->
    <div class="bg-white rounded-lg shadow-sm p-4 flex flex-wrap gap-3 items-end">
      <div>
        <label class="block text-xs text-gray-500 mb-1">Rule</label>
        <select id="eh-rule-filter" class="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-400">
          <option value="">All rules</option>
        </select>
      </div>
      <div>
        <label class="block text-xs text-gray-500 mb-1">Status</label>
        <select id="eh-status-filter" class="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-400">
          <option value="">All</option>
          <option value="success">Success</option>
          <option value="failed">Failed</option>
          <option value="partial">Partial</option>
        </select>
      </div>
      <button id="eh-refresh" class="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium transition">
        <i class="ph ph-arrow-clockwise"></i> Refresh
      </button>
    </div>

    <!-- Table -->
    <div class="bg-white rounded-lg shadow-sm overflow-hidden">
      <div id="eh-loading" class="flex items-center justify-center h-32 text-gray-400 text-sm gap-2">
        <i class="ph ph-spinner animate-spin"></i> Loading…
      </div>
      <table id="eh-table" class="hidden w-full text-sm">
        <thead class="bg-gray-50 text-xs text-gray-500 uppercase border-b border-gray-200">
          <tr>
            <th class="px-4 py-3 text-left">Triggered</th>
            <th class="px-4 py-3 text-left">Rule</th>
            <th class="px-4 py-3 text-left">Status</th>
            <th class="px-4 py-3 text-left">Duration</th>
            <th class="px-4 py-3 text-left">Records</th>
          </tr>
        </thead>
        <tbody id="eh-rows" class="divide-y divide-gray-100"></tbody>
      </table>
      <div id="eh-empty" class="hidden flex items-center justify-center h-32 text-gray-400 text-sm">
        No executions recorded yet. Rules will appear here after they fire.
      </div>
      <div id="eh-error" class="hidden px-4 py-3 text-sm text-red-600 bg-red-50"></div>
    </div>

    <!-- Detail drawer -->
    <div id="eh-detail-drawer" class="hidden fixed inset-y-0 right-0 w-96 bg-white shadow-2xl flex flex-col z-50 border-l border-gray-200">
      <div class="flex items-center justify-between px-5 py-4 border-b border-gray-200">
        <h3 class="font-semibold text-gray-900" id="eh-drawer-title">Execution detail</h3>
        <button id="eh-drawer-close" class="text-gray-400 hover:text-gray-600"><i class="ph ph-x text-xl"></i></button>
      </div>
      <div id="eh-drawer-body" class="flex-1 overflow-y-auto p-5 text-sm text-gray-700 space-y-4"></div>
    </div>`;
  return panel;
}

async function loadHistory(ruleId, status) {
  const loading = document.getElementById('eh-loading');
  const table   = document.getElementById('eh-table');
  const empty   = document.getElementById('eh-empty');
  const error   = document.getElementById('eh-error');
  const rows    = document.getElementById('eh-rows');

  [table, empty, error].forEach(el => el?.classList.add('hidden'));
  loading?.classList.remove('hidden');

  try {
    const params = new URLSearchParams();
    if (ruleId)  params.set('rule_id', ruleId);
    if (status)  params.set('status', status);
    const res = await apiFetch(`/automations/executions?${params}`);
    loading?.classList.add('hidden');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const items = Array.isArray(data) ? data : (data.items ?? data.executions ?? []);
    if (!items.length) { empty?.classList.remove('hidden'); return; }

    rows.innerHTML = items.map(r => `
      <tr class="eh-row hover:bg-blue-50 cursor-pointer transition" data-exec-id="${esc(r.id)}">
        <td class="px-4 py-3 text-gray-700">${relTime(r.triggered_at ?? r.created_at)}</td>
        <td class="px-4 py-3 text-gray-800 font-medium">${esc(r.rule_name ?? r.rule_id)}</td>
        <td class="px-4 py-3">${badge(r.status, STATUS_MAP)}</td>
        <td class="px-4 py-3 text-gray-600">${r.duration_ms != null ? (r.duration_ms < 1000 ? r.duration_ms+'ms' : (r.duration_ms/1000).toFixed(1)+'s') : '—'}</td>
        <td class="px-4 py-3 text-gray-600">${r.records_affected ?? '—'}</td>
      </tr>`).join('');
    table?.classList.remove('hidden');

    rows.querySelectorAll('.eh-row').forEach(row => {
      row.onclick = () => openDetail(row.dataset.execId, row.querySelector('td:nth-child(2)')?.textContent);
    });
  } catch (e) {
    loading?.classList.add('hidden');
    if (error) { error.textContent = 'Failed to load executions: ' + e.message; error.classList.remove('hidden'); }
  }
}

async function openDetail(execId, ruleName) {
  const drawer = document.getElementById('eh-detail-drawer');
  const body   = document.getElementById('eh-drawer-body');
  document.getElementById('eh-drawer-title').textContent = ruleName ?? 'Execution detail';
  body.innerHTML = '<div class="flex items-center gap-2 text-gray-400"><i class="ph ph-spinner animate-spin"></i> Loading…</div>';
  drawer?.classList.remove('hidden');

  try {
    const res = await apiFetch(`/automations/executions/${execId}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const d = await res.json();
    body.innerHTML = `
      <div class="space-y-3">
        <div><span class="text-xs text-gray-500 uppercase tracking-wide">Status</span><div class="mt-1">${badge(d.status, STATUS_MAP)}</div></div>
        <div><span class="text-xs text-gray-500 uppercase tracking-wide">Triggered</span><p class="mt-1">${relTime(d.triggered_at)}</p></div>
        <div><span class="text-xs text-gray-500 uppercase tracking-wide">Records affected</span><p class="mt-1">${d.records_affected ?? '—'}</p></div>
        <div><span class="text-xs text-gray-500 uppercase tracking-wide">Actions taken</span>
          <ul class="mt-1 space-y-1 list-disc list-inside text-gray-700">
            ${(d.actions_taken ?? d.actions ?? []).map(a => `<li>${esc(a.name ?? JSON.stringify(a))}</li>`).join('') || '<li class="text-gray-400 list-none">None recorded</li>'}
          </ul>
        </div>
        ${d.error_message ? `<div><span class="text-xs text-gray-500 uppercase tracking-wide text-red-500">Error</span><pre class="mt-1 text-xs bg-red-50 text-red-700 p-3 rounded overflow-auto">${esc(d.error_message)}</pre></div>` : ''}
      </div>`;
  } catch (e) {
    body.innerHTML = `<div class="text-red-600 text-sm">Failed to load detail: ${esc(e.message)}</div>`;
  }
}

function injectHistoryTab(tabStrip, mainContent) {
  // Add tab button
  const tabBtn = document.createElement('button');
  tabBtn.id = 'tab-exec-history';
  tabBtn.className = 'px-4 py-2 text-sm font-medium text-gray-600 border-b-2 border-transparent hover:text-gray-900 transition';
  tabBtn.textContent = 'Execution History';
  tabStrip.appendChild(tabBtn);

  // Add tab panel after main content
  const panel = buildHistoryTab();
  mainContent.parentNode.insertBefore(panel, mainContent.nextSibling);

  // Tab switching
  tabBtn.onclick = () => {
    // Hide other tab panels
    document.querySelectorAll('.automations-tab-panel').forEach(p => p.classList.add('hidden'));
    mainContent.classList.add('hidden');
    panel.classList.remove('hidden');
    tabBtn.classList.add('border-blue-600', 'text-blue-600');
    tabBtn.classList.remove('border-transparent', 'text-gray-600');
    // Populate rule filter
    populateRuleFilter();
    loadHistory('', '');
  };

  document.getElementById('eh-refresh')?.addEventListener('click', () => {
    loadHistory(document.getElementById('eh-rule-filter')?.value, document.getElementById('eh-status-filter')?.value);
  });
  document.getElementById('eh-drawer-close')?.addEventListener('click', () => {
    document.getElementById('eh-detail-drawer')?.classList.add('hidden');
  });

  async function populateRuleFilter() {
    try {
      const res = await apiFetch('/automations/rules?limit=200');
      if (!res.ok) return;
      const data = await res.json();
      const rules = Array.isArray(data) ? data : (data.items ?? []);
      const sel = document.getElementById('eh-rule-filter');
      rules.forEach(r => {
        const opt = document.createElement('option');
        opt.value = r.id; opt.textContent = r.name ?? r.id;
        sel.appendChild(opt);
      });
    } catch { /* non-fatal */ }
  }
}

// ── Rule Test Panel ────────────────────────────────────────────────────────

function attachTestPanels() {
  document.querySelectorAll('[data-rule-id]').forEach(card => {
    if (card.querySelector('.rule-test-panel')) return;
    const ruleId = card.dataset.ruleId;

    const panel = document.createElement('div');
    panel.className = 'rule-test-panel mt-3 border border-gray-200 rounded-lg overflow-hidden';
    panel.innerHTML = `
      <button class="test-toggle w-full flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100 transition text-sm font-medium text-gray-700">
        <span class="flex items-center gap-2"><i class="ph ph-flask"></i> Test this rule</span>
        <span class="flex items-center gap-3">
          <span class="last-run text-xs text-gray-400"></span>
          <button class="run-test-btn inline-flex items-center gap-1 px-3 py-1 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 text-xs font-medium transition">
            <i class="ph ph-play"></i> Run test
          </button>
          <i class="ph ph-caret-right toggle-icon transition-transform"></i>
        </span>
      </button>
      <div class="test-body hidden px-4 py-3 bg-white text-sm text-gray-500">
        Run the test to see which records match and which actions would fire.
      </div>`;

    const toggle = panel.querySelector('.test-toggle');
    const body   = panel.querySelector('.test-body');
    const icon   = panel.querySelector('.toggle-icon');
    const runBtn = panel.querySelector('.run-test-btn');

    toggle.onclick = (e) => {
      if (e.target.closest('.run-test-btn')) return; // let run btn handle
      body.classList.toggle('hidden');
      icon.classList.toggle('rotate-90');
    };

    runBtn.onclick = async (e) => {
      e.stopPropagation();
      body.classList.remove('hidden');
      icon.classList.add('rotate-90');
      runBtn.disabled = true;
      runBtn.innerHTML = '<i class="ph ph-spinner animate-spin"></i> Running…';
      body.innerHTML = '<div class="flex items-center gap-2 text-gray-400"><i class="ph ph-spinner animate-spin"></i> Running test…</div>';

      try {
        const res = await apiFetch(`/automations/rules/${ruleId}/test`, { method: 'POST' });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const d = await res.json();
        const matched = d.matched_records ?? d.records ?? [];
        const actions  = d.actions_that_would_fire ?? d.actions ?? [];

        body.innerHTML = matched.length === 0
          ? '<div class="flex items-center gap-2 text-blue-600 bg-blue-50 px-3 py-2 rounded-lg"><i class="ph ph-funnel"></i> No records matched this rule\'s conditions.</div>'
          : `<div class="grid grid-cols-2 gap-4">
              <div>
                <p class="text-xs text-gray-500 uppercase tracking-wide mb-2">Records matched <span class="ml-1 px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full text-xs font-medium">${matched.length}</span></p>
                <ul class="space-y-1">${matched.slice(0,10).map(r => `<li class="text-gray-700">${esc(r.name ?? r.id ?? JSON.stringify(r))}</li>`).join('')}
                  ${matched.length > 10 ? `<li class="text-gray-400 text-xs">+ ${matched.length - 10} more</li>` : ''}</ul>
              </div>
              <div>
                <p class="text-xs text-gray-500 uppercase tracking-wide mb-2">Actions that would fire</p>
                <ul class="space-y-1">${actions.map(a => `<li class="text-gray-700">${esc(a.name ?? a.type ?? JSON.stringify(a))}</li>`).join('') || '<li class="text-gray-400">None</li>'}</ul>
              </div>
            </div>`;
        panel.querySelector('.last-run').textContent = 'Just now';
      } catch (e) {
        body.innerHTML = `<div class="text-red-600 bg-red-50 px-3 py-2 rounded-lg text-sm">Test failed: ${esc(e.message)}</div>`;
      } finally {
        runBtn.disabled = false;
        runBtn.innerHTML = '<i class="ph ph-play"></i> Run test';
      }
    };

    // Attach after the existing card content
    const footer = card.querySelector('[class*="border-t"]') ?? card;
    card.appendChild(panel);
  });
}

export function initAutomationEnhancements() {
  // Find the tab strip and main list — try common selectors
  const tabStrip   = document.querySelector('#automations-tabs, .tab-strip, [role="tablist"]');
  const mainList   = document.querySelector('#automations-list, [id*="automation"][id*="list"]');

  if (tabStrip && mainList) {
    injectHistoryTab(tabStrip, mainList);
  }

  attachTestPanels();
  // Re-attach after the automation list refreshes
  document.addEventListener('automations:refreshed', attachTestPanels);
}
