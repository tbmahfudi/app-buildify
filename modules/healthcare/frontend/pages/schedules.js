/**
 * Healthcare — Schedules page (epic-11 extension). Light-DOM page class.
 * Manage doctors' WEEKLY practice schedules per room, and per-date overrides:
 * on a specific future date a doctor can be marked unavailable, or a substitute
 * doctor assigned for that day. day_of_week: 0=Sunday .. 6=Saturday.
 */
const DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
const DEFAULT_APPT_TYPES = ['general_consultation'];

function authToken() {
    try { return JSON.parse(localStorage.getItem('tokens') || '{}').access || ''; }
    catch (e) { return ''; }
}
function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c])); }
function todayStr() { return new Date().toISOString().slice(0, 10); }

export default class SchedulesPage {
    constructor() {
        this.name = 'healthcare-schedules';
        this.branchId = null;
        this.providers = [];
        this.rooms = [];
        this.schedules = [];
        this.overrides = {};      // { scheduleId: [override, ...] }
        this.expanded = null;     // scheduleId whose overrides panel is open
    }

    // Two backends: healthcare (providers/rooms) and healthcare_scheduling (schedules).
    async _fetch(path, opts = {}) {
        const headers = Object.assign(
            { 'Content-Type': 'application/json', 'Authorization': `Bearer ${authToken()}` },
            this.branchId ? { 'X-Branch-ID': this.branchId } : {}, opts.headers || {});
        const res = await fetch(path, Object.assign({}, opts, { headers }));
        if (!res.ok) { let d = res.statusText; try { d = (await res.json()).detail || d; } catch (e) {} throw new Error(d); }
        return res.status === 204 ? null : res.json();
    }
    get _hc() { return `/api/v1/modules/healthcare/branches/${this.branchId}`; }
    get _sch() { return `/api/v1/modules/healthcare_scheduling/branches/${this.branchId}`; }

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
            container.innerHTML = this._shell(`<div class="p-6"><div class="rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3">${esc(e.message)}</div></div>`);
        }
    }

    async _reload() {
        const [providers, rooms, sched] = await Promise.all([
            this._fetch(this._hc + '/hr/providers'),
            this._fetch(this._hc + '/rooms?is_active=true'),
            this._fetch(this._sch + '/schedules'),
        ]);
        this.providers = providers || [];
        this.rooms = rooms || [];
        this.schedules = (sched && sched.schedules) || [];
    }

    _providerName(id) {
        const p = this.providers.find(x => x.id === id);
        return p ? p.display_name : '(unknown)';
    }
    _doctorOptions(sel, placeholder) {
        const opts = this.providers.map(p =>
            `<option value="${p.id}" ${p.id === sel ? 'selected' : ''}>${esc(p.display_name)}</option>`).join('');
        return (placeholder ? `<option value="">${esc(placeholder)}</option>` : '') + opts;
    }
    _roomOptions(sel) {
        return `<option value="">— no room —</option>` + this.rooms.map(r =>
            `<option value="${r.id}" ${r.id === sel ? 'selected' : ''}>${esc(r.name)}</option>`).join('');
    }
    _dayOptions(sel) {
        return DAYS.map((d, i) => `<option value="${i}" ${i === sel ? 'selected' : ''}>${d}</option>`).join('');
    }

    _shell(body) {
        return `<div class="p-6 max-w-7xl mx-auto">
            <div class="bg-white rounded-xl border border-gray-200 shadow-sm px-5 py-4 mb-5 flex items-center gap-3">
                <span class="w-10 h-10 rounded-lg bg-indigo-50 flex items-center justify-center"><i class="ph-duotone ph-calendar text-indigo-600 text-2xl"></i></span>
                <div><h1 class="text-lg font-semibold text-gray-900">Doctor Schedules</h1><p class="text-sm text-gray-500">Weekly practice schedules per room, with per-date substitutions</p></div>
            </div><div id="hc-sch-body">${body}</div></div>`;
    }

    _paint() {
        const dayGrp = {};
        this.schedules.forEach(s => { (dayGrp[s.day_of_week] = dayGrp[s.day_of_week] || []).push(s); });

        let rows = '';
        Object.keys(dayGrp).map(Number).sort((a, b) => a - b).forEach(dow => {
            dayGrp[dow].sort((a, b) => a.start_time.localeCompare(b.start_time)).forEach(s => {
                rows += this._scheduleRow(s);
                if (this.expanded === String(s.id)) rows += this._overridePanel(s);
            });
        });

        this._container.querySelector('#hc-sch-body').innerHTML = `
            <div class="bg-white rounded-xl border border-gray-200 shadow-sm p-4 mb-4">
                <form id="hc-sch-form" class="flex flex-wrap items-end gap-3">
                    <div><label class="block text-xs text-gray-500 mb-1">Doctor</label><select id="hc-s-prov" required class="border border-gray-300 rounded-lg px-3 py-2 text-sm w-52">${this._doctorOptions(null, 'Select doctor…')}</select></div>
                    <div><label class="block text-xs text-gray-500 mb-1">Day</label><select id="hc-s-day" class="border border-gray-300 rounded-lg px-3 py-2 text-sm">${this._dayOptions(1)}</select></div>
                    <div><label class="block text-xs text-gray-500 mb-1">Start</label><input id="hc-s-start" type="time" value="09:00" class="border border-gray-300 rounded-lg px-3 py-2 text-sm"></div>
                    <div><label class="block text-xs text-gray-500 mb-1">End</label><input id="hc-s-end" type="time" value="17:00" class="border border-gray-300 rounded-lg px-3 py-2 text-sm"></div>
                    <div><label class="block text-xs text-gray-500 mb-1">Room</label><select id="hc-s-room" class="border border-gray-300 rounded-lg px-3 py-2 text-sm w-44">${this._roomOptions(null)}</select></div>
                    <div><label class="block text-xs text-gray-500 mb-1">Slot (min)</label><input id="hc-s-slot" type="number" min="5" step="5" value="30" class="border border-gray-300 rounded-lg px-3 py-2 text-sm w-24"></div>
                    <button class="inline-flex items-center gap-1.5 bg-indigo-600 text-white text-sm font-medium rounded-lg px-4 py-2 hover:bg-indigo-700"><i class="ph ph-plus"></i> Add schedule</button>
                    <span id="hc-sch-msg" class="text-sm"></span>
                </form>
            </div>
            <div class="bg-white rounded-xl border border-gray-200 shadow-sm overflow-x-auto">
                <table class="w-full text-sm"><thead class="bg-gray-50"><tr>
                    ${['Doctor', 'Day', 'Hours', 'Room', 'Slot', 'Overrides', ''].map(h => `<th class="px-3 py-3 text-left text-xs font-semibold text-gray-500 uppercase">${h}</th>`).join('')}
                </tr></thead><tbody>${rows || '<tr><td colspan="7" class="px-4 py-6 text-center text-gray-400">No schedules yet — add a weekly schedule for a doctor above.</td></tr>'}</tbody></table>
            </div>`;

        this._container.querySelector('#hc-sch-form').addEventListener('submit', (e) => this._create(e));
        this._wire();
    }

    _scheduleRow(s) {
        const nOvr = (this.overrides[s.id] || []).length;
        const ovrBadge = nOvr
            ? `<span class="text-xs rounded-full px-2 py-0.5 bg-amber-50 text-amber-700 border border-amber-200">${nOvr}</span>`
            : `<span class="text-xs text-gray-400">none</span>`;
        return `<tr class="border-b border-gray-100">
            <td class="px-3 py-2 font-medium text-gray-800">${esc(this._providerName(s.provider_id))}</td>
            <td class="px-3 py-2 text-gray-600">${DAYS[s.day_of_week]}</td>
            <td class="px-3 py-2 text-gray-600">${esc(s.start_time)}–${esc(s.end_time)}</td>
            <td class="px-3 py-2"><select data-roomsel="${s.id}" class="border border-gray-200 rounded px-2 py-1 text-sm text-gray-700 bg-white">${this._roomOptions(s.room_id)}</select></td>
            <td class="px-3 py-2 text-gray-500">${s.slot_duration_minutes}m</td>
            <td class="px-3 py-2">${ovrBadge}</td>
            <td class="px-3 py-2 text-right whitespace-nowrap">
                <button data-ovr="${s.id}" class="text-indigo-600 hover:underline text-xs mr-3">${this.expanded === String(s.id) ? 'Close' : 'Overrides'}</button>
                <button data-del="${s.id}" class="text-rose-600 hover:underline text-xs">Deactivate</button>
            </td>
        </tr>`;
    }

    _overridePanel(s) {
        const list = (this.overrides[s.id] || []).map(o => {
            const who = o.status === 'substituted'
                ? `<span class="text-emerald-700">Substitute: ${esc(o.substitute_provider_name || this._providerName(o.substitute_provider_id))}</span>`
                : `<span class="text-rose-600">Unavailable</span>`;
            return `<div class="flex items-center gap-3 py-1.5 border-b border-gray-100 last:border-0">
                <span class="font-mono text-xs text-gray-700 w-24">${esc(o.override_date)}</span>
                <span class="text-sm flex-1">${who}${o.reason ? ` <span class="text-gray-400">· ${esc(o.reason)}</span>` : ''}</span>
                <button data-rmovr="${o.id}" class="text-rose-600 hover:underline text-xs">Remove</button>
            </div>`;
        }).join('') || '<p class="text-xs text-gray-400 py-2">No overrides for this schedule.</p>';

        return `<tr class="bg-indigo-50/40"><td colspan="7" class="px-4 py-3">
            <div class="mb-2 text-xs font-semibold text-gray-500 uppercase">Per-date overrides · ${esc(this._providerName(s.provider_id))} · ${DAYS[s.day_of_week]}s</div>
            <div class="bg-white rounded-lg border border-gray-200 px-3 py-2 mb-3">${list}</div>
            <form data-ovrform="${s.id}" class="flex flex-wrap items-end gap-3">
                <div><label class="block text-xs text-gray-500 mb-1">Date (a ${DAYS[s.day_of_week]})</label><input data-of="date" type="date" min="${todayStr()}" required class="border border-gray-300 rounded-lg px-3 py-2 text-sm"></div>
                <div><label class="block text-xs text-gray-500 mb-1">Action</label><select data-of="status" class="border border-gray-300 rounded-lg px-3 py-2 text-sm"><option value="unavailable">Mark unavailable</option><option value="substituted">Assign substitute</option></select></div>
                <div data-of="subwrap" class="hidden"><label class="block text-xs text-gray-500 mb-1">Substitute doctor</label><select data-of="sub" class="border border-gray-300 rounded-lg px-3 py-2 text-sm w-52">${this._doctorOptions(null, 'Select…')}</select></div>
                <div><label class="block text-xs text-gray-500 mb-1">Reason (optional)</label><input data-of="reason" class="border border-gray-300 rounded-lg px-3 py-2 text-sm w-48" placeholder="Leave, training…"></div>
                <button class="inline-flex items-center gap-1.5 bg-amber-600 text-white text-sm font-medium rounded-lg px-4 py-2 hover:bg-amber-700"><i class="ph ph-plus"></i> Add override</button>
                <span data-of="msg" class="text-sm"></span>
            </form>
        </td></tr>`;
    }

    _wire() {
        const q = (s) => this._container.querySelectorAll(s);
        q('[data-del]').forEach(b => b.addEventListener('click', () => this._deactivate(b.getAttribute('data-del'))));
        q('[data-roomsel]').forEach(sel => sel.addEventListener('change', () => this._changeRoom(sel.getAttribute('data-roomsel'), sel.value)));
        q('[data-ovr]').forEach(b => b.addEventListener('click', () => this._toggleOverrides(b.getAttribute('data-ovr'))));
        q('[data-rmovr]').forEach(b => b.addEventListener('click', () => this._removeOverride(b.getAttribute('data-rmovr'))));
        q('form[data-ovrform]').forEach(f => {
            const statusSel = f.querySelector('[data-of="status"]');
            const subwrap = f.querySelector('[data-of="subwrap"]');
            statusSel.addEventListener('change', () => subwrap.classList.toggle('hidden', statusSel.value !== 'substituted'));
            f.addEventListener('submit', (e) => this._addOverride(e, f.getAttribute('data-ovrform')));
        });
    }

    async _create(e) {
        e.preventDefault();
        const msg = this._container.querySelector('#hc-sch-msg');
        const g = (i) => this._container.querySelector(i);
        const provId = g('#hc-s-prov').value;
        if (!provId) { msg.textContent = 'Select a doctor'; msg.className = 'text-sm text-red-600'; return; }
        try {
            await this._fetch(this._sch + '/schedules', { method: 'POST', body: JSON.stringify({
                provider_id: provId,
                day_of_week: parseInt(g('#hc-s-day').value, 10),
                start_time: g('#hc-s-start').value,
                end_time: g('#hc-s-end').value,
                slot_duration_minutes: parseInt(g('#hc-s-slot').value, 10),
                appointment_types: DEFAULT_APPT_TYPES,
                room_id: g('#hc-s-room').value || null,
            }) });
            await this._reload(); this._paint();
        } catch (err) { msg.textContent = err.message; msg.className = 'text-sm text-red-600'; }
    }

    async _changeRoom(id, roomId) {
        const msg = this._container.querySelector('#hc-sch-msg');
        const body = roomId ? { room_id: roomId } : { clear_room: true };
        try {
            await this._fetch(this._sch + `/schedules/${id}`, { method: 'PUT', body: JSON.stringify(body) });
            await this._reload(); this._paint();
            msg.textContent = 'Room updated'; msg.className = 'text-sm text-emerald-600';
        } catch (err) {
            msg.textContent = err.message; msg.className = 'text-sm text-red-600';
            await this._reload(); this._paint();  // revert the select to the server state
        }
    }

    async _deactivate(id) {
        const s = this.schedules.find(x => x.id === id);
        if (!confirm(`Deactivate the ${s ? DAYS[s.day_of_week] : ''} schedule for ${s ? this._providerName(s.provider_id) : 'this doctor'}?`)) return;
        const msg = this._container.querySelector('#hc-sch-msg');
        try {
            await this._fetch(this._sch + `/schedules/${id}`, { method: 'DELETE' });
            if (this.expanded === String(id)) this.expanded = null;
            await this._reload(); this._paint();
        } catch (err) { msg.textContent = err.message; msg.className = 'text-sm text-red-600'; }
    }

    async _toggleOverrides(id) {
        if (this.expanded === String(id)) { this.expanded = null; this._paint(); return; }
        this.expanded = String(id);
        try { this.overrides[id] = (await this._fetch(this._sch + `/schedules/${id}/overrides`)).overrides || []; }
        catch (e) { this.overrides[id] = []; }
        this._paint();
    }

    async _addOverride(e, scheduleId) {
        e.preventDefault();
        const f = e.target;
        const val = (k) => { const el = f.querySelector(`[data-of="${k}"]`); return el ? el.value : ''; };
        const msg = f.querySelector('[data-of="msg"]');
        const s = this.schedules.find(x => x.id === scheduleId);
        const dateStr = val('date');
        // Client-side weekday guard (backend also enforces).
        if (s && new Date(dateStr + 'T00:00:00').getDay() !== s.day_of_week) {
            msg.textContent = `Date must be a ${DAYS[s.day_of_week]}`; msg.className = 'text-sm text-red-600'; return;
        }
        const status = val('status');
        const body = { override_date: dateStr, status, reason: val('reason').trim() || null };
        if (status === 'substituted') {
            if (!val('sub')) { msg.textContent = 'Choose a substitute doctor'; msg.className = 'text-sm text-red-600'; return; }
            body.substitute_provider_id = val('sub');
        }
        try {
            await this._fetch(this._sch + `/schedules/${scheduleId}/overrides`, { method: 'POST', body: JSON.stringify(body) });
            this.overrides[scheduleId] = (await this._fetch(this._sch + `/schedules/${scheduleId}/overrides`)).overrides || [];
            this._paint();
        } catch (err) { msg.textContent = err.message; msg.className = 'text-sm text-red-600'; }
    }

    async _removeOverride(overrideId) {
        const schedId = this.expanded;
        try {
            await this._fetch(this._sch + `/schedule-overrides/${overrideId}`, { method: 'DELETE' });
            if (schedId) this.overrides[schedId] = (await this._fetch(this._sch + `/schedules/${schedId}/overrides`)).overrides || [];
            this._paint();
        } catch (err) {
            const msg = this._container.querySelector('#hc-sch-msg');
            if (msg) { msg.textContent = err.message; msg.className = 'text-sm text-red-600'; }
        }
    }

    async destroy() { const c = document.getElementById('app-content'); if (c) c.innerHTML = ''; }
}
