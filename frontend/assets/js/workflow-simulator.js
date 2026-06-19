/**
 * Workflow Simulator Panel
 * Story B3-P2
 */
import { apiFetch } from './api.js';

function esc(s) { return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

function buildDrawer() {
  const el = document.createElement('div');
  el.id = 'workflow-sim-drawer';
  el.className = 'fixed inset-y-0 right-0 w-[520px] max-w-full bg-white shadow-2xl flex flex-col z-50 transform translate-x-full transition-transform duration-300 border-l border-gray-200';
  el.innerHTML = `
    <div class="flex items-center justify-between px-5 py-4 border-b border-gray-200 flex-shrink-0">
      <div>
        <h2 class="text-base font-semibold text-gray-900">Workflow Simulator</h2>
        <p id="wfsim-name" class="text-xs text-gray-500"></p>
      </div>
      <button id="wfsim-close" class="text-gray-400 hover:text-gray-600 p-1"><i class="ph ph-x text-lg"></i></button>
    </div>
    <div class="px-5 py-4 border-b border-gray-100 flex-shrink-0">
      <label class="block text-xs text-gray-500 mb-1 uppercase tracking-wide">Context record ID (optional)</label>
      <div class="flex gap-2">
        <input id="wfsim-record-id" type="text" placeholder="e.g. 42 or leave blank"
          class="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-400">
        <button id="wfsim-run" class="inline-flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition text-sm font-medium">
          <i class="ph ph-play"></i> Simulate
        </button>
      </div>
    </div>
    <div class="flex-1 overflow-y-auto px-5 py-4">
      <div id="wfsim-idle" class="flex flex-col items-center justify-center h-40 text-gray-400 text-sm gap-2">
        <i class="ph ph-flow-arrow text-3xl"></i>
        <p>Enter a record ID (or leave blank) and click Simulate.</p>
      </div>
      <div id="wfsim-loading" class="hidden flex items-center justify-center h-32 text-gray-400 text-sm gap-2">
        <i class="ph ph-spinner animate-spin"></i> Running simulation...
      </div>
      <div id="wfsim-error" class="hidden px-4 py-3 text-sm text-red-600 bg-red-50 rounded-lg"></div>
      <div id="wfsim-result" class="hidden space-y-4">
        <div class="flex items-center justify-between">
          <span class="text-xs font-semibold text-gray-500 uppercase tracking-wide">Simulation result</span>
          <span id="wfsim-outcome-badge"></span>
        </div>
        <ol id="wfsim-steps" class="relative border-l border-gray-200 space-y-6 ml-3"></ol>
        <div id="wfsim-actions-section" class="hidden">
          <p class="text-xs text-gray-500 uppercase tracking-wide mb-2">Actions that would fire</p>
          <ul id="wfsim-actions" class="space-y-1 text-sm text-gray-700"></ul>
        </div>
        <div id="wfsim-errors-section" class="hidden mt-3 p-3 bg-red-50 rounded-lg">
          <p class="text-xs text-red-600 font-semibold mb-1">Errors</p>
          <ul id="wfsim-errors" class="text-xs text-red-700 space-y-1"></ul>
        </div>
      </div>
    </div>
    <div class="px-5 py-3 border-t border-gray-200 flex-shrink-0">
      <button id="wfsim-close-footer" class="w-full px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition text-sm font-medium">Close</button>
    </div>`;
  document.body.appendChild(el);
  return el;
}

function renderSimResult(data) {
  const steps   = data.steps ?? data.states ?? data.transitions ?? [];
  const actions = data.actions ?? data.actions_fired ?? [];
  const errors  = data.errors ?? [];
  const outcome = data.outcome ?? data.status ?? 'completed';
  const badgeMap = { completed:'bg-green-100 text-green-700', failed:'bg-red-100 text-red-700', blocked:'bg-amber-100 text-amber-700' };
  const bc = badgeMap[outcome.toLowerCase()] ?? 'bg-gray-100 text-gray-600';
  document.getElementById('wfsim-outcome-badge').className = `px-2 py-1 rounded-full text-xs font-medium ${bc}`;
  document.getElementById('wfsim-outcome-badge').textContent = outcome;

  document.getElementById('wfsim-steps').innerHTML = steps.map((s, i) => `
    <li class="ml-6">
      <span class="absolute -left-3 flex h-6 w-6 items-center justify-center rounded-full ${i === steps.length-1 ? 'bg-purple-100 ring-2 ring-purple-400':'bg-gray-100'} ring-8 ring-white">
        <i class="ph ${i === steps.length-1 ? 'ph-flag-checkered text-purple-600':'ph-arrow-right text-gray-500'} text-xs"></i>
      </span>
      <div class="ml-2">
        <p class="text-sm font-medium text-gray-800">${esc(s.state ?? s.name ?? 'Step '+(i+1))}</p>
        ${s.action ? `<p class="text-xs text-gray-500">Action: ${esc(s.action)}</p>` : ''}
        ${s.condition_met != null ? `<p class="text-xs ${s.condition_met?'text-green-600':'text-red-600'}">${s.condition_met?'Condition met':'Condition not met'}</p>` : ''}
      </div>
    </li>`).join('') || '<li class="text-gray-400 text-sm ml-4">No state transitions recorded.</li>';

  const actSec = document.getElementById('wfsim-actions-section');
  document.getElementById('wfsim-actions').innerHTML = actions.map(a => `<li class="flex items-center gap-2"><i class="ph ph-lightning text-purple-400"></i>${esc(a.name??a.type??JSON.stringify(a))}</li>`).join('');
  actSec.classList.toggle('hidden', !actions.length);

  const errSec = document.getElementById('wfsim-errors-section');
  document.getElementById('wfsim-errors').innerHTML = errors.map(e => `<li>${esc(e.message??e)}</li>`).join('');
  errSec.classList.toggle('hidden', !errors.length);

  document.getElementById('wfsim-result').classList.remove('hidden');
}

export function initWorkflowSimulator() {
  let drawer = null;
  let currentWorkflowId = null;

  function getDrawer() {
    if (!drawer) {
      drawer = buildDrawer();
      drawer.querySelector('#wfsim-close').onclick = close;
      drawer.querySelector('#wfsim-close-footer').onclick = close;
      drawer.querySelector('#wfsim-run').onclick = runSim;
    }
    return drawer;
  }

  function close() { document.getElementById('workflow-sim-drawer')?.classList.add('translate-x-full'); }

  async function runSim() {
    const recordId = document.getElementById('wfsim-record-id')?.value.trim();
    const d = document.getElementById('workflow-sim-drawer');
    ['wfsim-idle','wfsim-error','wfsim-result'].forEach(id => d.querySelector('#'+id).classList.add('hidden'));
    d.querySelector('#wfsim-loading').classList.remove('hidden');
    const btn = d.querySelector('#wfsim-run');
    btn.disabled = true;
    try {
      const body = recordId ? { record_id: recordId } : {};
      const res = await apiFetch(`/workflows/${currentWorkflowId}/simulate`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
      });
      d.querySelector('#wfsim-loading').classList.add('hidden');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      renderSimResult(await res.json());
    } catch (e) {
      d.querySelector('#wfsim-loading').classList.add('hidden');
      const err = d.querySelector('#wfsim-error');
      err.textContent = 'Simulation failed: ' + e.message;
      err.classList.remove('hidden');
    } finally { btn.disabled = false; }
  }

  function openForWorkflow(id, name) {
    currentWorkflowId = id;
    const d = getDrawer();
    d.querySelector('#wfsim-name').textContent = name ?? id;
    d.querySelector('#wfsim-record-id').value = '';
    ['wfsim-loading','wfsim-error','wfsim-result'].forEach(i => d.querySelector('#'+i).classList.add('hidden'));
    d.querySelector('#wfsim-idle').classList.remove('hidden');
    d.classList.remove('translate-x-full');
  }

  function attachButtons() {
    document.querySelectorAll('[data-workflow-id]').forEach(card => {
      if (card.querySelector('.btn-simulate-wf')) return;
      const btn = document.createElement('button');
      btn.className = 'btn-simulate-wf inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-purple-300 text-purple-700 rounded-lg hover:bg-purple-50 transition text-xs font-medium';
      btn.innerHTML = '<i class="ph ph-play-circle"></i> Simulate';
      btn.onclick = (e) => {
        e.stopPropagation();
        openForWorkflow(card.dataset.workflowId, card.dataset.workflowName ?? card.querySelector('h3,h4')?.textContent);
      };
      (card.querySelector('[class*="border-t"]') ?? card).appendChild(btn);
    });
  }

  attachButtons();
  document.addEventListener('workflows:refreshed', attachButtons);
  document.addEventListener('route:loaded', (e) => { if (e.detail.route === 'nocode-workflows') setTimeout(attachButtons, 400); });
}
