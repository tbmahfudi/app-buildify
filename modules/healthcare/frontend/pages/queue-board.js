/**
 * Healthcare — Queue Board page (epic-09 / ADR-HC-006).
 * Light-DOM page class. Short-polls the branch-scoped queue endpoint using the
 * queue_version contract (re-renders only when the version changes), and drives
 * the ticket lifecycle (call / skip / recall / serve / transfer).
 */

const POLL_MS = 2500;
const COLUMNS = [
    { key: 'waiting', label: 'Waiting', cls: 'bg-slate-50 text-slate-700 border-slate-200' },
    { key: 'called', label: 'Called', cls: 'bg-indigo-50 text-indigo-700 border-indigo-200' },
    { key: 'recalled', label: 'Recalled', cls: 'bg-amber-50 text-amber-700 border-amber-200' },
    { key: 'skipped', label: 'Skipped', cls: 'bg-rose-50 text-rose-700 border-rose-200' },
    { key: 'served', label: 'Served', cls: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
];

function authToken() {
    try { return JSON.parse(localStorage.getItem('tokens') || '{}').access || ''; }
    catch (e) { return ''; }
}

export default class QueueBoardPage {
    constructor() {
        this.name = 'healthcare-queue-board';
        this.branchId = null;
        this.departments = [];
        this.deptId = null;
        this.version = null;
        this.timer = null;
        this.fresh = false;
    }

    async _fetch(path, opts = {}) {
        const headers = Object.assign(
            { 'Content-Type': 'application/json', 'Authorization': `Bearer ${authToken()}` },
            this.branchId ? { 'X-Branch-ID': this.branchId } : {}, opts.headers || {});
        const res = await fetch(path, Object.assign({}, opts, { headers }));
        if (!res.ok) {
            let d = res.statusText; try { d = (await res.json()).detail || d; } catch (e) {}
            throw new Error(d);
        }
        return res.status === 204 ? null : res.json();
    }

    async _resolveBranch() {
        this.branchId = null;
        const branches = await this._fetch('/api/v1/modules/healthcare/branches');
        this.branchId = branches && branches[0] && branches[0].id;
    }

    async render() {
        const container = document.getElementById('app-content');
        if (!container) return;
        this._container = container;
        container.innerHTML = this._shell('<p class="text-sm text-gray-500 p-6">Loading…</p>');
        try {
            await this._resolveBranch();
            if (!this.branchId) throw new Error('No clinic branch found for your account.');
            this.departments = (await this._fetch(`/api/v1/modules/healthcare/branches/${this.branchId}/departments`))
                .filter(d => d.is_active);
            this.deptId = this.departments[0] && this.departments[0].id;
            this._renderChrome();
            await this._poll(true);
            this.timer = setInterval(() => this._poll(false), POLL_MS);
        } catch (e) {
            container.innerHTML = this._shell(
                `<div class="p-6"><div class="rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3">${e.message}</div></div>`);
        }
    }

    _shell(body) {
        return `<div class="p-6 max-w-7xl mx-auto">
            <div class="bg-white rounded-xl border border-gray-200 shadow-sm px-5 py-4 mb-5 flex items-center gap-3">
                <span class="w-10 h-10 rounded-lg bg-indigo-50 flex items-center justify-center"><i class="ph-duotone ph-users-three text-indigo-600 text-2xl"></i></span>
                <div class="flex-1"><h1 class="text-lg font-semibold text-gray-900">Queue Board</h1>
                    <p class="text-sm text-gray-500">Live patient queue by department</p></div>
                <div id="hc-queue-controls"></div>
            </div>
            <div id="hc-queue-body">${body}</div></div>`;
    }

    _renderChrome() {
        const opts = this.departments.map(d =>
            `<option value="${d.id}" ${d.id === this.deptId ? 'selected' : ''}>${d.name}</option>`).join('');
        this._container.querySelector('#hc-queue-controls').innerHTML = `
            <div class="flex items-center gap-3">
                <span id="hc-queue-fresh" class="text-xs text-gray-400"></span>
                <select id="hc-queue-dept" class="border border-gray-300 rounded-lg px-3 py-1.5 text-sm">${opts}</select>
            </div>`;
        this._container.querySelector('#hc-queue-dept').addEventListener('change', (e) => {
            this.deptId = e.target.value; this.version = null; this._poll(true);
        });
    }

    async _poll(force) {
        if (!this.deptId) { this._container.querySelector('#hc-queue-body').innerHTML =
            '<p class="text-sm text-gray-400 p-6">No active departments.</p>'; return; }
        try {
            const data = await this._fetch(
                `/api/v1/modules/healthcare/branches/${this.branchId}/queue?department_id=${this.deptId}`);
            this.fresh = true;
            const v = data.queue_version || '';
            if (!force && v === this.version) { this._setFresh(); return; }
            this.version = v;
            this._paint(data.tickets || []);
        } catch (e) {
            this.fresh = false; this._setFresh(e.message);
        }
    }

    _setFresh(err) {
        const el = this._container && this._container.querySelector('#hc-queue-fresh');
        if (el) el.textContent = err ? `⚠ ${err}` : (this.fresh ? `● live · ${new Date().toLocaleTimeString()}` : '○ reconnecting…');
        if (el) el.className = `text-xs ${this.fresh ? 'text-emerald-500' : 'text-amber-500'}`;
    }

    _paint(tickets) {
        const byStatus = {};
        COLUMNS.forEach(c => byStatus[c.key] = []);
        tickets.forEach(t => (byStatus[t.status] = byStatus[t.status] || []).push(t));

        const col = (c) => {
            const cards = (byStatus[c.key] || []).map(t => this._card(t, c.key)).join('') ||
                '<p class="text-xs text-gray-300 py-4 text-center">—</p>';
            return `<div class="flex-1 min-w-[150px]">
                <div class="text-xs font-semibold uppercase tracking-wide px-2 py-1 rounded border ${c.cls} mb-2 text-center">${c.label} (${(byStatus[c.key]||[]).length})</div>
                <div class="space-y-2">${cards}</div></div>`;
        };
        this._container.querySelector('#hc-queue-body').innerHTML =
            `<div class="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
                <div class="flex gap-3 overflow-x-auto">${COLUMNS.map(col).join('')}</div></div>`;
        this._setFresh();
        this._container.querySelectorAll('[data-act]').forEach(b =>
            b.addEventListener('click', () => this._action(b.getAttribute('data-act'), b.getAttribute('data-id'))));
    }

    _card(t, statusKey) {
        const actions = [];
        if (statusKey === 'waiting' || statusKey === 'recalled') actions.push(['call', 'Call', 'text-indigo-600']);
        if (statusKey === 'called') { actions.push(['serve', 'Serve', 'text-emerald-600']); actions.push(['skip', 'Skip', 'text-rose-600']); }
        if (statusKey === 'skipped') actions.push(['recall', 'Recall', 'text-amber-600']);
        const btns = actions.map(([a, l, c]) =>
            `<button data-act="${a}" data-id="${t.id}" class="text-xs font-medium ${c} hover:underline">${l}</button>`).join('<span class="text-gray-200">·</span>');
        return `<div class="rounded-lg border border-gray-200 px-3 py-2">
            <div class="font-bold text-gray-800">${t.ticket_number}</div>
            ${t.station ? `<div class="text-xs text-gray-400">${t.station}</div>` : ''}
            <div class="mt-1 flex gap-2 items-center">${btns}</div></div>`;
    }

    async _action(act, id) {
        try {
            await this._fetch(`/api/v1/modules/healthcare/branches/${this.branchId}/queue-tickets/${id}/${act}`,
                { method: 'POST', body: '{}' });
            this.version = null;         // force re-render
            await this._poll(true);
        } catch (e) { this._setFresh(e.message); }
    }

    async destroy() {
        if (this.timer) clearInterval(this.timer);
        this.timer = null;
        const container = document.getElementById('app-content');
        if (container) container.innerHTML = '';
    }
}
