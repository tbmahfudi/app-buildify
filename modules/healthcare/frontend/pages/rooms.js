/**
 * Healthcare — Rooms page (epic-11). Light-DOM page class.
 * Manage consultation/procedure rooms per branch (create / enable / disable).
 */
const ROOM_TYPES = ['consultation', 'procedure', 'observation', 'other'];

function authToken() {
    try { return JSON.parse(localStorage.getItem('tokens') || '{}').access || ''; }
    catch (e) { return ''; }
}

export default class RoomsPage {
    constructor() { this.name = 'healthcare-rooms'; this.branchId = null; this.rooms = []; }

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
            this.rooms = await this._fetch(`/api/v1/modules/healthcare/branches/${this.branchId}/rooms`);
            this._paint();
        } catch (e) {
            container.innerHTML = this._shell(`<div class="p-6"><div class="rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3">${e.message}</div></div>`);
        }
    }

    _shell(body) {
        return `<div class="p-6 max-w-4xl mx-auto">
            <div class="bg-white rounded-xl border border-gray-200 shadow-sm px-5 py-4 mb-5 flex items-center gap-3">
                <span class="w-10 h-10 rounded-lg bg-amber-50 flex items-center justify-center"><i class="ph-duotone ph-door-open text-amber-600 text-2xl"></i></span>
                <div><h1 class="text-lg font-semibold text-gray-900">Rooms</h1><p class="text-sm text-gray-500">Consultation &amp; procedure rooms for this clinic</p></div>
            </div><div id="hc-rooms-body">${body}</div></div>`;
    }

    _paint() {
        const rows = (this.rooms || []).map(r => `
            <tr class="border-b border-gray-100 last:border-0">
                <td class="px-4 py-3 text-sm font-mono text-gray-700">${r.code}</td>
                <td class="px-4 py-3 text-sm font-medium text-gray-800">${r.name}</td>
                <td class="px-4 py-3 text-sm text-gray-600 capitalize">${r.room_type || '—'}</td>
                <td class="px-4 py-3"><span class="text-xs rounded-full px-2 py-0.5 ${r.is_active ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-gray-100 text-gray-500 border border-gray-200'}">${r.is_active ? 'Active' : 'Disabled'}</span></td>
                <td class="px-4 py-3 text-right"><button data-toggle="${r.id}" data-active="${r.is_active}" class="text-sm text-indigo-600 hover:underline">${r.is_active ? 'Disable' : 'Enable'}</button></td>
            </tr>`).join('');
        const typeOpts = ROOM_TYPES.map(t => `<option value="${t}">${t[0].toUpperCase() + t.slice(1)}</option>`).join('');
        this._container.querySelector('#hc-rooms-body').innerHTML = `
            <div class="bg-white rounded-xl border border-gray-200 shadow-sm p-4 mb-4">
                <form id="hc-room-form" class="flex flex-wrap items-end gap-3">
                    <div><label class="block text-xs text-gray-500 mb-1">Code</label><input id="hc-rm-code" required maxlength="50" class="border border-gray-300 rounded-lg px-3 py-2 text-sm w-32" placeholder="RM-103"></div>
                    <div><label class="block text-xs text-gray-500 mb-1">Name</label><input id="hc-rm-name" required maxlength="255" class="border border-gray-300 rounded-lg px-3 py-2 text-sm w-64" placeholder="Consultation Room 103"></div>
                    <div><label class="block text-xs text-gray-500 mb-1">Type</label><select id="hc-rm-type" class="border border-gray-300 rounded-lg px-3 py-2 text-sm">${typeOpts}</select></div>
                    <button class="inline-flex items-center gap-1.5 bg-amber-600 text-white text-sm font-medium rounded-lg px-4 py-2 hover:bg-amber-700"><i class="ph ph-plus"></i> Add room</button>
                    <span id="hc-room-msg" class="text-sm"></span>
                </form>
            </div>
            <div class="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                <table class="w-full"><thead class="bg-gray-50"><tr>
                    <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Code</th>
                    <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Name</th>
                    <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Type</th>
                    <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Status</th><th></th>
                </tr></thead><tbody>${rows || '<tr><td colspan="5" class="px-4 py-6 text-center text-sm text-gray-400">No rooms yet.</td></tr>'}</tbody></table>
            </div>`;
        this._container.querySelector('#hc-room-form').addEventListener('submit', (e) => this._create(e));
        this._container.querySelectorAll('[data-toggle]').forEach(b =>
            b.addEventListener('click', () => this._toggle(b.getAttribute('data-toggle'), b.getAttribute('data-active') === 'true')));
    }

    async _create(e) {
        e.preventDefault();
        const msg = this._container.querySelector('#hc-room-msg');
        try {
            await this._fetch(`/api/v1/modules/healthcare/branches/${this.branchId}/rooms`, { method: 'POST', body: JSON.stringify({
                code: this._container.querySelector('#hc-rm-code').value.trim(),
                name: this._container.querySelector('#hc-rm-name').value.trim(),
                room_type: this._container.querySelector('#hc-rm-type').value,
            }) });
            this.rooms = await this._fetch(`/api/v1/modules/healthcare/branches/${this.branchId}/rooms`);
            this._paint();
        } catch (err) { msg.textContent = err.message; msg.className = 'text-sm text-red-600'; }
    }

    async _toggle(id, active) {
        try {
            await this._fetch(`/api/v1/modules/healthcare/branches/${this.branchId}/rooms/${id}`, { method: 'PUT', body: JSON.stringify({ is_active: !active }) });
            this.rooms = await this._fetch(`/api/v1/modules/healthcare/branches/${this.branchId}/rooms`);
            this._paint();
        } catch (err) { const m = this._container.querySelector('#hc-room-msg'); if (m) { m.textContent = err.message; m.className = 'text-sm text-red-600'; } }
    }

    async destroy() { const c = document.getElementById('app-content'); if (c) c.innerHTML = ''; }
}
