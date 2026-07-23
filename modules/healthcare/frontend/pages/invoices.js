/**
 * Healthcare — Invoices page (billing).
 * Light-DOM page class. Resolves the caller's clinic branch, then lists real
 * invoices from the billing API (GET .../healthcare_billing/branches/{id}/invoices)
 * with a status filter. Read-only view — invoice creation / finalize / payment
 * live in the billing workflow; this surfaces raised invoices and their state.
 */

const STATUS_STYLES = {
    draft: 'bg-amber-50 text-amber-700',
    finalized: 'bg-emerald-50 text-emerald-700',
    void: 'bg-gray-100 text-gray-500',
};
const STATUSES = ['', 'draft', 'finalized', 'void'];

function authToken() {
    try { return JSON.parse(localStorage.getItem('tokens') || '{}').access || ''; }
    catch (e) { return ''; }
}

function money(amount, currency) {
    if (amount == null) return '—';
    const n = Number(amount);
    const formatted = isNaN(n) ? amount : n.toLocaleString(undefined, { maximumFractionDigits: 2 });
    return `${currency || ''} ${formatted}`.trim();
}

export default class InvoicesPage {
    constructor() {
        this.name = 'healthcare-invoices';
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

    get _base() { return `/api/v1/modules/healthcare_billing/branches/${this.branchId}`; }

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
                <span class="w-10 h-10 rounded-lg bg-orange-50 flex items-center justify-center"><i class="ph-duotone ph-receipt text-orange-600 text-2xl"></i></span>
                <div class="flex-1"><h1 class="text-lg font-semibold text-gray-900">Invoices</h1>
                    <p class="text-sm text-gray-500">Billing &amp; patient invoices</p></div>
                <div id="hc-inv-controls"></div>
            </div>
            <div id="hc-inv-body">${body}</div></div>`;
    }

    _renderChrome() {
        const opts = STATUSES.map(s =>
            `<option value="${s}" ${s === this.status ? 'selected' : ''}>${s ? s : 'All statuses'}</option>`).join('');
        this._container.querySelector('#hc-inv-controls').innerHTML = `
            <div class="flex items-center gap-2">
                <select id="hc-inv-status" class="border border-gray-300 rounded-lg px-3 py-1.5 text-sm capitalize">${opts}</select>
                <button id="hc-inv-refresh" class="text-sm text-gray-500 hover:text-gray-700 border border-gray-300 rounded-lg px-3 py-1.5">Refresh</button>
            </div>`;
        this._container.querySelector('#hc-inv-status').addEventListener('change', (e) => {
            this.status = e.target.value; this._load();
        });
        this._container.querySelector('#hc-inv-refresh').addEventListener('click', () => this._load());
    }

    async _load() {
        const body = this._container.querySelector('#hc-inv-body');
        body.innerHTML = '<p class="text-sm text-gray-500 p-6">Loading…</p>';
        try {
            const qs = this.status ? `?status=${encodeURIComponent(this.status)}&page_size=100` : '?page_size=100';
            const data = await this._fetch(this._base + '/invoices' + qs);
            this._paint(data.items || []);
        } catch (e) {
            body.innerHTML = `<div class="rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3">${e.message}</div>`;
        }
    }

    _paint(items) {
        if (!items.length) {
            this._container.querySelector('#hc-inv-body').innerHTML =
                '<div class="bg-white rounded-xl border border-gray-200 shadow-sm p-10 text-center text-sm text-gray-400">No invoices yet.</div>';
            return;
        }
        const rows = items.map(inv => {
            const cls = STATUS_STYLES[inv.status] || 'bg-gray-100 text-gray-600';
            return `<tr class="border-b border-gray-100 last:border-0">
                <td class="px-4 py-3 text-sm font-medium text-gray-700">${inv.invoice_number}</td>
                <td class="px-4 py-3 text-sm font-mono text-gray-500">${String(inv.patient_id).slice(0, 8)}</td>
                <td class="px-4 py-3 text-sm text-gray-500 whitespace-nowrap">${inv.created_at ? new Date(inv.created_at).toLocaleDateString() : '—'}</td>
                <td class="px-4 py-3 text-sm text-gray-800 whitespace-nowrap">${money(inv.total_amount, inv.currency)}</td>
                <td class="px-4 py-3"><span class="inline-flex px-2 py-0.5 rounded-full text-xs font-medium capitalize ${cls}">${inv.status}</span></td>
            </tr>`;
        }).join('');
        this._container.querySelector('#hc-inv-body').innerHTML = `
            <div class="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                <table class="w-full">
                    <thead class="bg-gray-50"><tr>
                        <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Invoice</th>
                        <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Patient</th>
                        <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Date</th>
                        <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Amount</th>
                        <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Status</th>
                    </tr></thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>
            <p class="text-xs text-gray-400 mt-3">${items.length} invoice${items.length === 1 ? '' : 's'}${this.status ? ` · filtered by "${this.status}"` : ''}.</p>`;
    }

    async destroy() {
        const container = document.getElementById('app-content');
        if (container) container.innerHTML = '';
    }
}
