/**
 * Healthcare — Doctors / Providers page (epic-11). Light-DOM page class.
 * Directory of doctors & nurses with create + edit of specialty, STR/SIP
 * license, consultation fee, room assignment, and employment status.
 */
const PTYPES = ['doctor', 'nurse', 'pharmacist', 'lab_tech', 'billing_staff'];
const STATUSES = ['active', 'probation', 'on_leave', 'suspended', 'terminated'];

function authToken() {
    try { return JSON.parse(localStorage.getItem('tokens') || '{}').access || ''; }
    catch (e) { return ''; }
}
function money(v) { return (v == null) ? '—' : new Intl.NumberFormat().format(v); }

export default class DoctorsPage {
    constructor() { this.name = 'healthcare-doctors'; this.branchId = null; this.providers = []; this.rooms = []; this.editing = null; }

    async _fetch(path, opts = {}) {
        const headers = Object.assign(
            { 'Content-Type': 'application/json', 'Authorization': `Bearer ${authToken()}` },
            this.branchId ? { 'X-Branch-ID': this.branchId } : {}, opts.headers || {});
        const res = await fetch(path, Object.assign({}, opts, { headers }));
        if (!res.ok) { let d = res.statusText; try { d = (await res.json()).detail || d; } catch (e) {} throw new Error(d); }
        return res.status === 204 ? null : res.json();
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
            await this._reload();
            this._paint();
        } catch (e) {
            container.innerHTML = this._shell(`<div class="p-6"><div class="rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3">${e.message}</div></div>`);
        }
    }

    async _reload() {
        [this.providers, this.rooms] = await Promise.all([
            this._fetch(this._base + '/hr/providers'),
            this._fetch(this._base + '/rooms?is_active=true'),
        ]);
    }

    _shell(body) {
        return `<div class="p-6 max-w-6xl mx-auto">
            <div class="bg-white rounded-xl border border-gray-200 shadow-sm px-5 py-4 mb-5 flex items-center gap-3">
                <span class="w-10 h-10 rounded-lg bg-sky-50 flex items-center justify-center"><i class="ph-duotone ph-stethoscope text-sky-600 text-2xl"></i></span>
                <div><h1 class="text-lg font-semibold text-gray-900">Doctors &amp; Providers</h1><p class="text-sm text-gray-500">Clinical staff, licenses, fees &amp; room assignment</p></div>
            </div><div id="hc-doc-body">${body}</div></div>`;
    }

    _roomOptions(sel) {
        return `<option value="">— no room —</option>` + this.rooms.map(r =>
            `<option value="${r.id}" ${r.id === sel ? 'selected' : ''}>${r.name}</option>`).join('');
    }

    _paint() {
        const rows = this.providers.map(p => this.editing === p.id ? this._editRow(p) : this._viewRow(p)).join('');
        const typeOpts = PTYPES.map(t => `<option value="${t}">${t.replace('_', ' ')}</option>`).join('');
        this._container.querySelector('#hc-doc-body').innerHTML = `
            <div class="bg-white rounded-xl border border-gray-200 shadow-sm p-4 mb-4">
                <form id="hc-doc-form" class="flex flex-wrap items-end gap-3">
                    <div><label class="block text-xs text-gray-500 mb-1">Name</label><input id="hc-d-name" required class="border border-gray-300 rounded-lg px-3 py-2 text-sm w-56" placeholder="Dr. Sinta Dewi"></div>
                    <div><label class="block text-xs text-gray-500 mb-1">Type</label><select id="hc-d-type" class="border border-gray-300 rounded-lg px-3 py-2 text-sm">${typeOpts}</select></div>
                    <div><label class="block text-xs text-gray-500 mb-1">Specialty</label><input id="hc-d-spec" class="border border-gray-300 rounded-lg px-3 py-2 text-sm w-48" placeholder="Cardiology"></div>
                    <button class="inline-flex items-center gap-1.5 bg-sky-600 text-white text-sm font-medium rounded-lg px-4 py-2 hover:bg-sky-700"><i class="ph ph-plus"></i> Add provider</button>
                    <span id="hc-doc-msg" class="text-sm"></span>
                </form>
            </div>
            <div class="bg-white rounded-xl border border-gray-200 shadow-sm overflow-x-auto">
                <table class="w-full text-sm"><thead class="bg-gray-50"><tr>
                    ${['Name','Type','Specialty','License','Fee','Room','Status',''].map(h => `<th class="px-3 py-3 text-left text-xs font-semibold text-gray-500 uppercase">${h}</th>`).join('')}
                </tr></thead><tbody>${rows || '<tr><td colspan="8" class="px-4 py-6 text-center text-gray-400">No providers yet.</td></tr>'}</tbody></table>
            </div>`;
        this._container.querySelector('#hc-doc-form').addEventListener('submit', (e) => this._create(e));
        this._wireRowEvents();
    }

    _viewRow(p) {
        const lic = [p.str_number && `STR ${p.str_number}`, p.sip_number && `SIP ${p.sip_number}`].filter(Boolean).join(' · ') || '—';
        const stCls = p.employment_status === 'active' ? 'text-emerald-700' : (p.employment_status === 'terminated' ? 'text-rose-600' : 'text-amber-600');
        return `<tr class="border-b border-gray-100">
            <td class="px-3 py-2 font-medium text-gray-800">${p.display_name}${p.is_active ? '' : ' <span class="text-xs text-gray-400">(inactive)</span>'}</td>
            <td class="px-3 py-2 text-gray-600 capitalize">${p.provider_type.replace('_', ' ')}</td>
            <td class="px-3 py-2 text-gray-600">${p.specialty || '—'}${p.sub_specialty ? ` <span class="text-gray-400">/ ${p.sub_specialty}</span>` : ''}</td>
            <td class="px-3 py-2 text-gray-500 text-xs">${lic}</td>
            <td class="px-3 py-2 text-gray-600">${money(p.consultation_fee)}</td>
            <td class="px-3 py-2 text-gray-600">${p.room_name || '—'}</td>
            <td class="px-3 py-2 capitalize ${stCls}">${p.employment_status.replace('_', ' ')}</td>
            <td class="px-3 py-2 text-right"><button data-edit="${p.id}" class="text-sky-600 hover:underline text-xs">Edit</button></td>
        </tr>`;
    }

    _editRow(p) {
        return `<tr class="border-b border-gray-100 bg-sky-50/40"><td colspan="8" class="px-3 py-3">
            <div class="grid md:grid-cols-4 gap-3">
                <div><label class="block text-xs text-gray-500 mb-1">Specialty</label><input id="e-spec" value="${p.specialty || ''}" class="w-full border border-gray-300 rounded px-2 py-1.5 text-sm"></div>
                <div><label class="block text-xs text-gray-500 mb-1">Sub-specialty</label><input id="e-sub" value="${p.sub_specialty || ''}" class="w-full border border-gray-300 rounded px-2 py-1.5 text-sm"></div>
                <div><label class="block text-xs text-gray-500 mb-1">STR number</label><input id="e-str" value="${p.str_number || ''}" class="w-full border border-gray-300 rounded px-2 py-1.5 text-sm"></div>
                <div><label class="block text-xs text-gray-500 mb-1">SIP number</label><input id="e-sip" value="${p.sip_number || ''}" class="w-full border border-gray-300 rounded px-2 py-1.5 text-sm"></div>
                <div><label class="block text-xs text-gray-500 mb-1">Consultation fee</label><input id="e-fee" type="number" min="0" value="${p.consultation_fee ?? ''}" class="w-full border border-gray-300 rounded px-2 py-1.5 text-sm"></div>
                <div><label class="block text-xs text-gray-500 mb-1">Room</label><select id="e-room" class="w-full border border-gray-300 rounded px-2 py-1.5 text-sm">${this._roomOptions(p.room_id)}</select></div>
                <div><label class="block text-xs text-gray-500 mb-1">Status</label><select id="e-status" class="w-full border border-gray-300 rounded px-2 py-1.5 text-sm">${STATUSES.map(s => `<option value="${s}" ${s === p.employment_status ? 'selected' : ''}>${s.replace('_', ' ')}</option>`).join('')}</select></div>
                <div class="flex items-end gap-2">
                    <button data-save="${p.id}" class="bg-sky-600 text-white text-sm rounded-lg px-3 py-1.5 hover:bg-sky-700">Save</button>
                    <button data-cancel="1" class="text-gray-500 text-sm px-2">Cancel</button>
                </div>
            </div><span id="hc-edit-msg" class="text-sm"></span>
        </td></tr>`;
    }

    _wireRowEvents() {
        this._container.querySelectorAll('[data-edit]').forEach(b =>
            b.addEventListener('click', () => { this.editing = b.getAttribute('data-edit'); this._paint(); }));
        this._container.querySelectorAll('[data-cancel]').forEach(b =>
            b.addEventListener('click', () => { this.editing = null; this._paint(); }));
        this._container.querySelectorAll('[data-save]').forEach(b =>
            b.addEventListener('click', () => this._save(b.getAttribute('data-save'))));
    }

    async _create(e) {
        e.preventDefault();
        const msg = this._container.querySelector('#hc-doc-msg');
        try {
            await this._fetch(this._base + '/hr/providers', { method: 'POST', body: JSON.stringify({
                display_name: this._container.querySelector('#hc-d-name').value.trim(),
                provider_type: this._container.querySelector('#hc-d-type').value,
                specialty: this._container.querySelector('#hc-d-spec').value.trim() || null,
            }) });
            await this._reload(); this._paint();
        } catch (err) { msg.textContent = err.message; msg.className = 'text-sm text-red-600'; }
    }

    async _save(id) {
        const g = (i) => this._container.querySelector(i);
        const msg = this._container.querySelector('#hc-edit-msg');
        const fee = g('#e-fee').value;
        try {
            await this._fetch(this._base + `/hr/providers/${id}`, { method: 'PUT', body: JSON.stringify({ specialty: g('#e-spec').value.trim() || null }) });
            await this._fetch(this._base + `/hr/providers/${id}/license`, { method: 'PUT', body: JSON.stringify({
                str_number: g('#e-str').value.trim() || null, sip_number: g('#e-sip').value.trim() || null,
                sub_specialty: g('#e-sub').value.trim() || null }) });
            await this._fetch(this._base + `/hr/providers/${id}/doctor-profile`, { method: 'PUT', body: JSON.stringify({
                consultation_fee: fee === '' ? null : parseInt(fee, 10), room_id: g('#e-room').value || null }) });
            await this._fetch(this._base + `/hr/providers/${id}/status`, { method: 'PUT', body: JSON.stringify({ employment_status: g('#e-status').value }) });
            this.editing = null; await this._reload(); this._paint();
        } catch (err) { msg.textContent = err.message; msg.className = 'text-sm text-red-600'; }
    }

    async destroy() { const c = document.getElementById('app-content'); if (c) c.innerHTML = ''; }
}
