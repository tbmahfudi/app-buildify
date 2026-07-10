/**
 * Healthcare — Family Link Approvals (epic-18 Feature 18.10, Q3). Light-DOM page class.
 * Clinic staff (clinic_owner / branch_manager) approve or reject patient-link
 * requests routed to their branch. Backend enforces the role; branch comes from
 * the caller's clinic.
 */
function authToken() {
    try { return JSON.parse(localStorage.getItem('tokens') || '{}').access || ''; }
    catch (e) { return ''; }
}

export default class FamilyApprovalsPage {
    constructor() { this.name = 'healthcare-family-approvals'; this.branchId = null; this.requests = []; }

    async _fetch(path, opts = {}) {
        const headers = Object.assign(
            { 'Content-Type': 'application/json', 'Authorization': `Bearer ${authToken()}` },
            this.branchId ? { 'X-Branch-ID': this.branchId } : {}, opts.headers || {});
        const res = await fetch(path, Object.assign({}, opts, { headers }));
        if (!res.ok) { let d = res.statusText; try { d = (await res.json()).detail || d; } catch (e) {} throw new Error(d); }
        return res.status === 204 ? null : res.json();
    }

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
            await this._load();
            this._paint();
        } catch (e) {
            container.innerHTML = this._shell(`<div class="p-6"><div class="rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3">${e.message}</div></div>`);
        }
    }

    async _load() {
        const data = await this._fetch(`/api/v1/patients/branches/${this.branchId}/household/link-requests`);
        this.requests = (data && data.link_requests) || [];
    }

    _shell(body) {
        return `<div class="p-6 max-w-4xl mx-auto">
            <div class="bg-white rounded-xl border border-gray-200 shadow-sm px-5 py-4 mb-5 flex items-center gap-3">
                <span class="w-10 h-10 rounded-lg bg-indigo-50 flex items-center justify-center"><i class="ph-duotone ph-users-three text-indigo-600 text-2xl"></i></span>
                <div><h1 class="text-lg font-semibold text-gray-900">Family Link Approvals</h1><p class="text-sm text-gray-500">Approve or reject requests to manage an existing patient</p></div>
            </div><div id="hc-fa-body">${body}</div></div>`;
    }

    _paint() {
        const rows = (this.requests || []).map(r => `
            <tr class="border-b border-gray-100 last:border-0">
                <td class="px-4 py-3 text-sm font-mono text-gray-700">${(r.patient_id || '').slice(0, 8)}…</td>
                <td class="px-4 py-3 text-sm text-gray-800 capitalize">${r.relationship || '—'}</td>
                <td class="px-4 py-3 text-sm text-gray-600">${(r.basis || '').replace(/_/g, ' ')}</td>
                <td class="px-4 py-3 text-sm font-mono text-gray-500">${(r.account_user_id || '').slice(0, 8)}…</td>
                <td class="px-4 py-3 text-sm text-gray-500">${r.requested_at ? new Date(r.requested_at).toLocaleString() : '—'}</td>
                <td class="px-4 py-3 text-right whitespace-nowrap">
                    <button data-approve="${r.id}" class="text-sm text-emerald-600 hover:underline mr-3">Approve</button>
                    <button data-reject="${r.id}" class="text-sm text-red-600 hover:underline">Reject</button>
                </td>
            </tr>`).join('');
        this._container.querySelector('#hc-fa-body').innerHTML = `
            <div class="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                <table class="w-full"><thead class="bg-gray-50"><tr>
                    <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Patient</th>
                    <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Relationship</th>
                    <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Basis</th>
                    <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Requested by</th>
                    <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">When</th><th></th>
                </tr></thead><tbody>${rows || '<tr><td colspan="6" class="px-4 py-6 text-center text-sm text-gray-400">No pending link requests.</td></tr>'}</tbody></table>
            </div>
            <span id="hc-fa-msg" class="text-sm block mt-3"></span>`;
        this._container.querySelectorAll('[data-approve]').forEach(b =>
            b.addEventListener('click', () => this._decide(b.getAttribute('data-approve'), 'approve')));
        this._container.querySelectorAll('[data-reject]').forEach(b =>
            b.addEventListener('click', () => this._decide(b.getAttribute('data-reject'), 'reject')));
    }

    async _decide(relId, action) {
        const msg = this._container.querySelector('#hc-fa-msg');
        try {
            await this._fetch(`/api/v1/patients/branches/${this.branchId}/household/link-requests/${relId}/${action}`, { method: 'POST' });
            await this._load();
            this._paint();
            const m2 = this._container.querySelector('#hc-fa-msg');
            if (m2) { m2.textContent = `Request ${action === 'approve' ? 'approved' : 'rejected'}.`; m2.className = 'text-sm block mt-3 text-emerald-600'; }
        } catch (err) { if (msg) { msg.textContent = err.message; msg.className = 'text-sm block mt-3 text-red-600'; } }
    }

    async destroy() { const c = document.getElementById('app-content'); if (c) c.innerHTML = ''; }
}
