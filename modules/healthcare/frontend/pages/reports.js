/**
 * Healthcare — Executive Dashboard & Reports (epic-12 / ADR-HC-008).
 * Light-DOM page class. Renders KPI cards + revenue/disease panels from the
 * reporting dashboard endpoint, and a report viewer over the v_hc_* datasets.
 */
const DATASETS = [
    ['daily-patients', 'Daily patients'],
    ['doctor-productivity', 'Doctor productivity'],
    ['queue', 'Queue metrics'],
    ['appointments', 'Appointments'],
    ['revenue', 'Revenue'],
    ['disease-stats', 'Disease statistics'],
];

function authToken() {
    try { return JSON.parse(localStorage.getItem('tokens') || '{}').access || ''; }
    catch (e) { return ''; }
}
function num(v) { return new Intl.NumberFormat().format(v || 0); }

export default class ReportsPage {
    constructor() { this.name = 'healthcare-reports'; this.branchId = null; this.dash = null; this.dataset = 'daily-patients'; }

    async _fetch(path) {
        const headers = { 'Content-Type': 'application/json', 'Authorization': `Bearer ${authToken()}` };
        if (this.branchId) headers['X-Branch-ID'] = this.branchId;
        const res = await fetch(path, { headers });
        if (!res.ok) { let d = res.statusText; try { d = (await res.json()).detail || d; } catch (e) {} throw new Error(d); }
        return res.json();
    }
    get _base() { return `/api/v1/modules/healthcare/branches/${this.branchId}`; }

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
            this.dash = await this._fetch(this._base + '/reports/dashboard');
            this._paint();
            await this._loadDataset();
        } catch (e) {
            container.innerHTML = this._shell(`<div class="p-6"><div class="rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3">${e.message}</div></div>`);
        }
    }

    _shell(body) {
        return `<div class="p-6 max-w-6xl mx-auto">
            <div class="bg-white rounded-xl border border-gray-200 shadow-sm px-5 py-4 mb-5 flex items-center gap-3">
                <span class="w-10 h-10 rounded-lg bg-fuchsia-50 flex items-center justify-center"><i class="ph-duotone ph-chart-line-up text-fuchsia-600 text-2xl"></i></span>
                <div><h1 class="text-lg font-semibold text-gray-900">Executive Dashboard &amp; Reports</h1><p class="text-sm text-gray-500">Operational, financial &amp; medical metrics</p></div>
            </div><div id="hc-rep-body">${body}</div></div>`;
    }

    _kpi(label, value, icon, cls) {
        return `<div class="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
            <div class="flex items-center gap-2 text-gray-400 text-xs uppercase tracking-wide"><i class="${icon} ${cls}"></i> ${label}</div>
            <div class="text-2xl font-bold text-gray-900 mt-1">${value}</div></div>`;
    }

    _paint() {
        const k = this.dash.kpis;
        const cards = [
            this._kpi("Today's patients", num(k.todays_patients), 'ph-duotone ph-users', 'text-indigo-500'),
            this._kpi('Waiting', num(k.waiting_patients), 'ph-duotone ph-hourglass-medium', 'text-amber-500'),
            this._kpi('Walk-ins', num(k.walk_ins), 'ph-duotone ph-person-simple-walk', 'text-teal-500'),
            this._kpi('Encounters', num(k.encounters_today), 'ph-duotone ph-stethoscope', 'text-sky-500'),
            this._kpi('Appointments', num(k.appointments_today), 'ph-duotone ph-calendar-check', 'text-violet-500'),
            this._kpi('Revenue today', num(k.revenue_today), 'ph-duotone ph-money', 'text-emerald-500'),
            this._kpi('Active doctors', num(k.active_doctors), 'ph-duotone ph-user-circle', 'text-rose-500'),
        ].join('');

        const payer = this.dash.revenue_by_payer || [];
        const maxInv = Math.max(1, ...payer.map(r => Number(r.invoiced) || 0));
        const payerRows = payer.map(r => `
            <div class="mb-2"><div class="flex justify-between text-sm"><span class="capitalize text-gray-600">${r.payer}</span><span class="text-gray-800 font-medium">${num(r.invoiced)}</span></div>
            <div class="h-2 bg-gray-100 rounded"><div class="h-2 bg-emerald-400 rounded" style="width:${(Number(r.invoiced) / maxInv * 100).toFixed(0)}%"></div></div></div>`).join('')
            || '<p class="text-xs text-gray-400">No revenue yet.</p>';

        const dx = this.dash.top_diagnoses || [];
        const dxRows = dx.map(d => `<div class="flex justify-between text-sm py-1 border-b border-gray-100 last:border-0"><span class="font-mono">${d.icd10_code}</span><span class="text-gray-600">${num(d.n)}</span></div>`).join('')
            || '<p class="text-xs text-gray-400">No diagnoses yet.</p>';

        const tabs = DATASETS.map(([k2, l]) =>
            `<button data-ds="${k2}" class="px-3 py-1.5 text-sm rounded-lg ${k2 === this.dataset ? 'bg-fuchsia-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}">${l}</button>`).join('');

        this._container.querySelector('#hc-rep-body').innerHTML = `
            <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3 mb-5">${cards}</div>
            <div class="grid md:grid-cols-2 gap-4 mb-5">
                <div class="bg-white rounded-xl border border-gray-200 shadow-sm p-4"><h3 class="text-sm font-semibold text-gray-800 mb-3">Revenue by payer</h3>${payerRows}</div>
                <div class="bg-white rounded-xl border border-gray-200 shadow-sm p-4"><h3 class="text-sm font-semibold text-gray-800 mb-3">Top diagnoses (this month)</h3>${dxRows}</div>
            </div>
            <div class="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
                <div class="flex flex-wrap gap-2 mb-3">${tabs}</div>
                <div id="hc-rep-table" class="overflow-x-auto"><p class="text-sm text-gray-400">Loading…</p></div>
            </div>`;
        this._container.querySelectorAll('[data-ds]').forEach(b =>
            b.addEventListener('click', () => { this.dataset = b.getAttribute('data-ds'); this._paint(); this._loadDataset(); }));
    }

    async _loadDataset() {
        const box = this._container.querySelector('#hc-rep-table');
        if (!box) return;
        try {
            const data = await this._fetch(this._base + `/reports/datasets/${this.dataset}`);
            const rows = data.rows || [];
            if (!rows.length) { box.innerHTML = '<p class="text-sm text-gray-400">No data for this report yet.</p>'; return; }
            const cols = Object.keys(rows[0]).filter(c => c !== 'tenant_id' && c !== 'branch_id');
            box.innerHTML = `<table class="w-full text-sm"><thead class="bg-gray-50"><tr>${cols.map(c => `<th class="px-3 py-2 text-left text-xs font-semibold text-gray-500 uppercase">${c.replace(/_/g, ' ')}</th>`).join('')}</tr></thead>
                <tbody>${rows.map(r => `<tr class="border-b border-gray-100 last:border-0">${cols.map(c => `<td class="px-3 py-2 text-gray-700">${this._fmt(r[c])}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
        } catch (e) { box.innerHTML = `<p class="text-sm text-red-600">${e.message}</p>`; }
    }

    _fmt(v) {
        if (v == null) return '—';
        if (typeof v === 'number') return num(v);
        return String(v);
    }

    async destroy() { const c = document.getElementById('app-content'); if (c) c.innerHTML = ''; }
}
