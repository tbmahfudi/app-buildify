/**
 * Healthcare — Lab Orders page.
 * Light-DOM page class. Resolves the caller's clinic branch, then lists real lab
 * orders from the lab API (GET .../healthcare_lab/branches/{id}/orders) with a
 * status filter. Read-only view — specimen collection / result entry live in the
 * lab-tech workflow; this surfaces ordered panels and their progress. Patient is
 * shown masked (the API never returns raw patient identity to this list).
 */

const STATUS_STYLES = {
    ordered: 'bg-amber-50 text-amber-700',
    collected: 'bg-indigo-50 text-indigo-700',
    in_progress: 'bg-sky-50 text-sky-700',
    resulted: 'bg-violet-50 text-violet-700',
    released: 'bg-emerald-50 text-emerald-700',
    cancelled: 'bg-gray-100 text-gray-500',
};
const STATUSES = ['', 'ordered', 'collected', 'in_progress', 'resulted', 'released', 'cancelled'];
const PRIORITY_STYLES = {
    routine: 'text-gray-500',
    urgent: 'text-orange-600 font-medium',
    stat: 'text-rose-600 font-semibold',
};

function authToken() {
    try { return JSON.parse(localStorage.getItem('tokens') || '{}').access || ''; }
    catch (e) { return ''; }
}

export default class LabOrdersPage {
    constructor() {
        this.name = 'healthcare-lab-orders';
        this.branchId = null;
        this.status = '';
    }

    async _fetch(path, opts = {}) {
        const headers = Object.assign(
            { 'Content-Type': 'application/json', 'Authorization': `Bearer ${authToken()}` },
            this.branchId ? { 'X-Branch-ID': this.branchId } : {}, opts.headers || {});
        const res = await fetch(path, Object.assign({}, opts, { headers }));
        if (!res.ok) {
            let d = res.statusText; try { d = (await res.json()).detail || d; } catch (e) {}
            throw new Error(typeof d === 'string' ? d : 'Request failed');
        }
        return res.status === 204 ? null : res.json();
    }

    get _base() { return `/api/v1/modules/healthcare_lab/branches/${this.branchId}`; }

    async render() {
        const container = document.getElementById('app-content');
        if (!container) return;
        this._container = container;
        container.innerHTML = this._shell('<p class="text-sm text-gray-500 p-6">Loading…</p>');
        try {
            this.branchId = null;
            const branches = await this._fetch('/api/v1/modules/healthcare/branches');
            this.branchId = branches && branches[0] && branches[0].id;
            if (!this.branchId) throw new Error('No clinic branch found for your account.');
            this._renderChrome();
            await this._load();
        } catch (e) {
            container.innerHTML = this._shell(
                `<div class="p-6"><div class="rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3">${e.message}</div></div>`);
        }
    }

    _shell(body) {
        return `<div class="p-6 max-w-7xl mx-auto">
            <div class="bg-white rounded-xl border border-gray-200 shadow-sm px-5 py-4 mb-5 flex items-center gap-3">
                <span class="w-10 h-10 rounded-lg bg-amber-50 flex items-center justify-center"><i class="ph-duotone ph-flask text-amber-600 text-2xl"></i></span>
                <div class="flex-1"><h1 class="text-lg font-semibold text-gray-900">Lab Orders</h1>
                    <p class="text-sm text-gray-500">Laboratory orders &amp; result progress</p></div>
                <div id="hc-lab-controls"></div>
            </div>
            <div id="hc-lab-body">${body}</div></div>`;
    }

    _renderChrome() {
        const opts = STATUSES.map(s =>
            `<option value="${s}" ${s === this.status ? 'selected' : ''}>${s ? s.replace('_', ' ') : 'All statuses'}</option>`).join('');
        this._container.querySelector('#hc-lab-controls').innerHTML = `
            <div class="flex items-center gap-2">
                <select id="hc-lab-status" class="border border-gray-300 rounded-lg px-3 py-1.5 text-sm capitalize">${opts}</select>
                <button id="hc-lab-refresh" class="text-sm text-gray-500 hover:text-gray-700 border border-gray-300 rounded-lg px-3 py-1.5">Refresh</button>
            </div>`;
        this._container.querySelector('#hc-lab-status').addEventListener('change', (e) => {
            this.status = e.target.value; this._load();
        });
        this._container.querySelector('#hc-lab-refresh').addEventListener('click', () => this._load());
    }

    async _load() {
        const body = this._container.querySelector('#hc-lab-body');
        body.innerHTML = '<p class="text-sm text-gray-500 p-6">Loading…</p>';
        try {
            const qs = this.status ? `?status=${encodeURIComponent(this.status)}&page_size=100` : '?page_size=100';
            const data = await this._fetch(this._base + '/orders' + qs);
            this._paint(data.items || []);
        } catch (e) {
            body.innerHTML = `<div class="rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3">${e.message}</div>`;
        }
    }

    _paint(items) {
        if (!items.length) {
            this._container.querySelector('#hc-lab-body').innerHTML =
                '<div class="bg-white rounded-xl border border-gray-200 shadow-sm p-10 text-center text-sm text-gray-400">No lab orders yet.</div>';
            return;
        }
        const rows = items.map(o => {
            const cls = STATUS_STYLES[o.status] || 'bg-gray-100 text-gray-600';
            const pcls = PRIORITY_STYLES[o.priority] || 'text-gray-500';
            return `<tr class="border-b border-gray-100 last:border-0">
                <td class="px-4 py-3 text-sm font-mono text-gray-500">${String(o.id).slice(0, 8)}</td>
                <td class="px-4 py-3 text-sm text-gray-600">${o.patient_display || '—'}</td>
                <td class="px-4 py-3 text-sm text-gray-800">${o.panel_count} panel${o.panel_count === 1 ? '' : 's'}</td>
                <td class="px-4 py-3 text-sm capitalize ${pcls}">${o.priority || '—'}</td>
                <td class="px-4 py-3 text-sm text-gray-500 whitespace-nowrap">${o.created_at ? new Date(o.created_at).toLocaleDateString() : '—'}</td>
                <td class="px-4 py-3"><span class="inline-flex px-2 py-0.5 rounded-full text-xs font-medium capitalize ${cls}">${String(o.status).replace('_', ' ')}</span></td>
            </tr>`;
        }).join('');
        this._container.querySelector('#hc-lab-body').innerHTML = `
            <div class="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                <table class="w-full">
                    <thead class="bg-gray-50"><tr>
                        <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Order</th>
                        <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Patient</th>
                        <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Panels</th>
                        <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Priority</th>
                        <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Date</th>
                        <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Status</th>
                    </tr></thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>
            <p class="text-xs text-gray-400 mt-3">${items.length} order${items.length === 1 ? '' : 's'}${this.status ? ` · filtered by "${this.status.replace('_', ' ')}"` : ''}.</p>`;
    }

    async destroy() {
        const container = document.getElementById('app-content');
        if (container) container.innerHTML = '';
    }
}
