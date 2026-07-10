/**
 * Healthcare — Organization / Departments page (epic-08).
 * Light-DOM page class per MODULE_FRONTEND_CONTRACT.md §4a.
 *
 * First "real" (API-wired) staff page in this module: resolves the auth token
 * from the platform token store, resolves the clinic branch, and drives the
 * epic-08 endpoints (departments CRUD + org-context) at
 *   /api/v1/modules/healthcare/branches/{branch_id}/...
 * Staff RBAC + branch scope enforced server-side (needs X-Branch-ID).
 */

const KINDS = ['medical', 'pharmacy', 'laboratory', 'radiology', 'administration', 'finance'];

function authToken() {
    try { return JSON.parse(localStorage.getItem('tokens') || '{}').access || ''; }
    catch (e) { return ''; }
}

export default class DepartmentsPage {
    constructor() {
        this.name = 'healthcare-departments';
        this.branchId = null;
        this.departments = [];
        this.context = null;
    }

    async _fetch(path, opts = {}) {
        const headers = Object.assign(
            { 'Content-Type': 'application/json', 'Authorization': `Bearer ${authToken()}` },
            this.branchId ? { 'X-Branch-ID': this.branchId } : {},
            opts.headers || {}
        );
        const res = await fetch(path, Object.assign({}, opts, { headers }));
        if (!res.ok) {
            let detail = res.statusText;
            try { detail = (await res.json()).detail || detail; } catch (e) {}
            throw new Error(detail);
        }
        return res.status === 204 ? null : res.json();
    }

    async _resolveBranch() {
        // Tenant-scoped list (no X-Branch-ID needed); pick the first branch.
        const prev = this.branchId; this.branchId = null;
        const branches = await this._fetch('/api/v1/modules/healthcare/branches');
        this.branchId = (branches && branches[0] && (branches[0].id)) || prev;
    }

    async _load() {
        await this._resolveBranch();
        if (!this.branchId) throw new Error('No clinic branch found for your account.');
        const B = `/api/v1/modules/healthcare/branches/${this.branchId}`;
        [this.departments, this.context] = await Promise.all([
            this._fetch(B + '/departments'),
            this._fetch(B + '/org-context').catch(() => null),
        ]);
    }

    async render() {
        const container = document.getElementById('app-content');
        if (!container) return;
        this._container = container;
        container.innerHTML = this._shell('<p class="text-sm text-gray-500 p-6">Loading…</p>');
        try {
            await this._load();
            this._paint();
        } catch (e) {
            container.innerHTML = this._shell(
                `<div class="p-6"><div class="rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3">${e.message}</div></div>`
            );
        }
    }

    _shell(body) {
        const ctx = this.context;
        const linked = ctx && ctx.linked
            ? `<span class="text-xs text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-full px-2 py-0.5">Linked: ${ctx.company_name || ''}${ctx.platform_branch_name ? ' · ' + ctx.platform_branch_name : ''}</span>`
            : `<span class="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-full px-2 py-0.5">Not linked to platform org</span>`;
        return `
            <div class="p-6 max-w-7xl mx-auto">
                <div class="bg-white rounded-xl border border-gray-200 shadow-sm px-5 py-4 mb-5 flex items-center gap-3">
                    <span class="w-10 h-10 rounded-lg bg-rose-50 flex items-center justify-center">
                        <i class="ph-duotone ph-buildings text-rose-600 text-2xl"></i>
                    </span>
                    <div class="flex-1">
                        <h1 class="text-lg font-semibold text-gray-900">Organization &amp; Departments</h1>
                        <p class="text-sm text-gray-500">Clinical departments for this clinic branch</p>
                    </div>
                    <div>${this.context !== undefined ? linked : ''}</div>
                </div>
                <div id="hc-dept-body">${body}</div>
            </div>`;
    }

    _paint() {
        const rows = (this.departments || []).map(d => `
            <tr class="border-b border-gray-100 last:border-0">
                <td class="px-4 py-3 text-sm font-mono text-gray-700">${d.code}</td>
                <td class="px-4 py-3 text-sm font-medium text-gray-800">${d.name}</td>
                <td class="px-4 py-3 text-sm text-gray-600 capitalize">${d.kind}</td>
                <td class="px-4 py-3 text-sm">
                    <span class="text-xs rounded-full px-2 py-0.5 ${d.is_active ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-gray-100 text-gray-500 border border-gray-200'}">${d.is_active ? 'Active' : 'Disabled'}</span>
                </td>
                <td class="px-4 py-3 text-right">
                    <button data-toggle="${d.id}" data-active="${d.is_active}" class="text-sm text-indigo-600 hover:text-indigo-800">${d.is_active ? 'Disable' : 'Enable'}</button>
                </td>
            </tr>`).join('');

        const kindOpts = KINDS.map(k => `<option value="${k}">${k.charAt(0).toUpperCase() + k.slice(1)}</option>`).join('');

        this._container.querySelector('#hc-dept-body').innerHTML = `
            <div class="bg-white rounded-xl border border-gray-200 shadow-sm p-4 mb-4">
                <form id="hc-dept-form" class="flex flex-wrap items-end gap-3">
                    <div><label class="block text-xs text-gray-500 mb-1">Code</label><input id="hc-d-code" maxlength="50" required class="border border-gray-300 rounded-lg px-3 py-2 text-sm w-28" placeholder="MED"></div>
                    <div><label class="block text-xs text-gray-500 mb-1">Name</label><input id="hc-d-name" maxlength="255" required class="border border-gray-300 rounded-lg px-3 py-2 text-sm w-56" placeholder="Medical"></div>
                    <div><label class="block text-xs text-gray-500 mb-1">Kind</label><select id="hc-d-kind" class="border border-gray-300 rounded-lg px-3 py-2 text-sm">${kindOpts}</select></div>
                    <button type="submit" class="inline-flex items-center gap-1.5 bg-indigo-600 text-white text-sm font-medium rounded-lg px-4 py-2 hover:bg-indigo-700"><i class="ph ph-plus"></i> Add department</button>
                    <span id="hc-dept-msg" class="text-sm"></span>
                </form>
            </div>
            <div class="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                <table class="w-full">
                    <thead class="bg-gray-50"><tr>
                        <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Code</th>
                        <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Name</th>
                        <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Kind</th>
                        <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Status</th>
                        <th class="px-4 py-3"></th>
                    </tr></thead>
                    <tbody>${rows || '<tr><td colspan="5" class="px-4 py-6 text-center text-sm text-gray-400">No departments yet.</td></tr>'}</tbody>
                </table>
            </div>`;

        this._container.querySelector('#hc-dept-form').addEventListener('submit', (e) => this._create(e));
        this._container.querySelectorAll('[data-toggle]').forEach(btn =>
            btn.addEventListener('click', () => this._toggle(btn.getAttribute('data-toggle'), btn.getAttribute('data-active') === 'true')));
    }

    async _create(e) {
        e.preventDefault();
        const msg = this._container.querySelector('#hc-dept-msg');
        const body = {
            code: this._container.querySelector('#hc-d-code').value.trim(),
            name: this._container.querySelector('#hc-d-name').value.trim(),
            kind: this._container.querySelector('#hc-d-kind').value,
        };
        try {
            await this._fetch(`/api/v1/modules/healthcare/branches/${this.branchId}/departments`,
                { method: 'POST', body: JSON.stringify(body) });
            await this._load(); this._paint();
        } catch (err) {
            msg.textContent = err.message; msg.className = 'text-sm text-red-600';
        }
    }

    async _toggle(id, isActive) {
        try {
            await this._fetch(`/api/v1/modules/healthcare/branches/${this.branchId}/departments/${id}`,
                { method: 'PUT', body: JSON.stringify({ is_active: !isActive }) });
            await this._load(); this._paint();
        } catch (err) {
            const msg = this._container.querySelector('#hc-dept-msg');
            if (msg) { msg.textContent = err.message; msg.className = 'text-sm text-red-600'; }
        }
    }

    async destroy() {
        const container = document.getElementById('app-content');
        if (container) container.innerHTML = '';
    }
}
