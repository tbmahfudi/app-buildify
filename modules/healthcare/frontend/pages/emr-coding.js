/**
 * Healthcare — EMR Clinical Coding workspace (epic-10 / ADR-HC-007).
 * Light-DOM page class. Pick an encounter, then attach ICD-10 diagnoses,
 * ICD-9-CM procedures, and typed clinical notes over the verified coding API.
 */

const NOTE_TYPES = ['progress', 'nursing', 'observation', 'follow_up'];

function authToken() {
    try { return JSON.parse(localStorage.getItem('tokens') || '{}').access || ''; }
    catch (e) { return ''; }
}

export default class EmrCodingPage {
    constructor() {
        this.name = 'healthcare-emr-coding';
        this.branchId = null;
        this.encounters = [];
        this.encId = null;
        this.summary = null;
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

    get _base() { return `/api/v1/modules/healthcare/branches/${this.branchId}`; }
    get _enc() { return `${this._base}/encounters/${this.encId}`; }

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
            this.encounters = await this._fetch(this._base + '/encounters');
            this.encId = this.encounters[0] && this.encounters[0].id;
            this._renderChrome();
            if (this.encId) { await this._loadSummary(); this._paint(); }
            else this._container.querySelector('#hc-emr-body').innerHTML =
                '<p class="text-sm text-gray-400 p-6">No encounters yet. Open one from Registration → hand-off.</p>';
        } catch (e) {
            container.innerHTML = this._shell(
                `<div class="p-6"><div class="rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3">${e.message}</div></div>`);
        }
    }

    _shell(body) {
        return `<div class="p-6 max-w-5xl mx-auto">
            <div class="bg-white rounded-xl border border-gray-200 shadow-sm px-5 py-4 mb-5 flex items-center gap-3">
                <span class="w-10 h-10 rounded-lg bg-violet-50 flex items-center justify-center"><i class="ph-duotone ph-notepad text-violet-600 text-2xl"></i></span>
                <div class="flex-1"><h1 class="text-lg font-semibold text-gray-900">EMR — Clinical Coding</h1>
                    <p class="text-sm text-gray-500">Diagnoses (ICD-10), procedures (ICD-9-CM) &amp; notes</p></div>
                <div id="hc-emr-picker"></div>
            </div>
            <div id="hc-emr-body">${body}</div></div>`;
    }

    _renderChrome() {
        const opts = this.encounters.map(e =>
            `<option value="${e.id}" ${e.id === this.encId ? 'selected' : ''}>${e.patient_name} · ${e.provider_name || ''} · ${e.status}</option>`).join('');
        this._container.querySelector('#hc-emr-picker').innerHTML =
            `<select id="hc-emr-enc" class="border border-gray-300 rounded-lg px-3 py-1.5 text-sm max-w-xs">${opts || '<option>No encounters</option>'}</select>`;
        const sel = this._container.querySelector('#hc-emr-enc');
        if (sel) sel.addEventListener('change', async (e) => {
            this.encId = e.target.value; await this._loadSummary(); this._paint();
        });
    }

    async _loadSummary() { this.summary = await this._fetch(this._enc + '/coding-summary'); }

    _paint() {
        const s = this.summary || { diagnoses: [], procedures: [], notes: [] };
        const diagRows = s.diagnoses.map(d => `
            <div class="flex items-center justify-between border-b border-gray-100 py-2">
                <div class="text-sm"><span class="font-mono font-semibold">${d.icd10_code}</span> <span class="text-gray-600">${d.description || ''}</span>
                    ${d.is_primary ? '<span class="ml-2 text-xs bg-indigo-50 text-indigo-700 border border-indigo-200 rounded-full px-2 py-0.5">primary</span>' : ''}</div>
                ${d.is_primary ? '' : `<button data-primary="${d.id}" class="text-xs text-indigo-600 hover:underline">Make primary</button>`}
            </div>`).join('') || '<p class="text-xs text-gray-300 py-2">No diagnoses.</p>';
        const procRows = s.procedures.map(p => `
            <div class="flex items-center justify-between border-b border-gray-100 py-2">
                <div class="text-sm"><span class="font-mono font-semibold">${p.icd9cm_code}</span> <span class="text-gray-600">${p.description || ''}</span>${p.note ? ` <span class="text-gray-400">(${p.note})</span>` : ''}</div>
                <button data-delproc="${p.id}" class="text-xs text-rose-600 hover:underline">Remove</button>
            </div>`).join('') || '<p class="text-xs text-gray-300 py-2">No procedures.</p>';
        const noteRows = s.notes.map(n =>
            `<div class="text-sm border-b border-gray-100 py-2"><span class="text-xs bg-gray-100 rounded px-1.5 py-0.5 capitalize">${n.note_type.replace('_',' ')}</span>
                <span class="text-gray-400 ml-2">${new Date(n.created_at).toLocaleString()}</span></div>`).join('')
            || '<p class="text-xs text-gray-300 py-2">No notes.</p>';

        this._container.querySelector('#hc-emr-body').innerHTML = `
            <div class="grid md:grid-cols-2 gap-4">
                ${this._section('Diagnoses (ICD-10)', 'icd10', 'Search diagnosis code / name', diagRows,
                    '<label class="text-xs text-gray-500 flex items-center gap-1 mt-2"><input type="checkbox" id="hc-diag-primary"> primary</label>')}
                ${this._section('Procedures (ICD-9-CM)', 'icd9', 'Search procedure code / name', procRows, '')}
            </div>
            <div class="bg-white rounded-xl border border-gray-200 shadow-sm p-4 mt-4">
                <h3 class="text-sm font-semibold text-gray-800 mb-2">Clinical notes</h3>
                <form id="hc-note-form" class="flex flex-wrap items-end gap-2 mb-3">
                    <select id="hc-note-type" class="border border-gray-300 rounded-lg px-2 py-2 text-sm">${NOTE_TYPES.map(t => `<option value="${t}">${t.replace('_',' ')}</option>`).join('')}</select>
                    <input id="hc-note-body" required placeholder="Note text…" class="flex-1 min-w-[200px] border border-gray-300 rounded-lg px-3 py-2 text-sm">
                    <button class="bg-violet-600 text-white text-sm rounded-lg px-3 py-2 hover:bg-violet-700">Add note</button>
                    <span id="hc-note-msg" class="text-sm"></span>
                </form>
                ${noteRows}
            </div>`;

        this._wire('icd10', '/icd10/search', (code) => this._addDiagnosis(code));
        this._wire('icd9', '/icd9cm/search', (code) => this._addProcedure(code));
        this._container.querySelectorAll('[data-primary]').forEach(b =>
            b.addEventListener('click', () => this._setPrimary(b.getAttribute('data-primary'))));
        this._container.querySelectorAll('[data-delproc]').forEach(b =>
            b.addEventListener('click', () => this._delProcedure(b.getAttribute('data-delproc'))));
        this._container.querySelector('#hc-note-form').addEventListener('submit', (e) => this._addNote(e));
    }

    _section(title, key, placeholder, rows, extra) {
        return `<div class="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
            <h3 class="text-sm font-semibold text-gray-800 mb-2">${title}</h3>
            <div class="flex gap-2"><input id="hc-${key}-q" placeholder="${placeholder}" class="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm">
                <button id="hc-${key}-btn" class="bg-gray-100 border border-gray-300 rounded-lg px-3 text-sm hover:bg-gray-200">Search</button></div>
            ${extra}
            <div id="hc-${key}-results" class="mt-2"></div>
            <div class="mt-3">${rows}</div></div>`;
    }

    _wire(key, searchPath, onPick) {
        const btn = this._container.querySelector(`#hc-${key}-btn`);
        const input = this._container.querySelector(`#hc-${key}-q`);
        const run = async () => {
            const q = input.value.trim();
            const results = await this._fetch(`/api/v1/modules/healthcare${searchPath}?q=${encodeURIComponent(q)}`);
            const box = this._container.querySelector(`#hc-${key}-results`);
            box.innerHTML = results.map(r =>
                `<button data-code="${r.code}" class="block w-full text-left text-sm px-2 py-1 hover:bg-gray-50 rounded"><span class="font-mono">${r.code}</span> — ${r.description}</button>`).join('')
                || '<p class="text-xs text-gray-400 px-2">No matches.</p>';
            box.querySelectorAll('[data-code]').forEach(b =>
                b.addEventListener('click', () => onPick(b.getAttribute('data-code'))));
        };
        btn.addEventListener('click', run);
        input.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); run(); } });
    }

    async _refresh() { await this._loadSummary(); this._paint(); }

    async _addDiagnosis(code) {
        const primary = this._container.querySelector('#hc-diag-primary');
        try {
            await this._fetch(this._enc + '/diagnoses', { method: 'POST',
                body: JSON.stringify({ icd10_code: code, is_primary: !!(primary && primary.checked) }) });
            await this._refresh();
        } catch (e) { alert(e.message); }
    }
    async _setPrimary(id) {
        try { await this._fetch(this._enc + `/diagnoses/${id}`, { method: 'PUT', body: JSON.stringify({ is_primary: true }) }); await this._refresh(); }
        catch (e) { alert(e.message); }
    }
    async _addProcedure(code) {
        try { await this._fetch(this._enc + '/procedures', { method: 'POST', body: JSON.stringify({ icd9cm_code: code }) }); await this._refresh(); }
        catch (e) { alert(e.message); }
    }
    async _delProcedure(id) {
        try { await this._fetch(this._enc + `/procedures/${id}`, { method: 'DELETE' }); await this._refresh(); }
        catch (e) { alert(e.message); }
    }
    async _addNote(e) {
        e.preventDefault();
        const msg = this._container.querySelector('#hc-note-msg');
        try {
            await this._fetch(this._enc + '/notes', { method: 'POST', body: JSON.stringify({
                note_type: this._container.querySelector('#hc-note-type').value,
                body: this._container.querySelector('#hc-note-body').value,
            }) });
            await this._refresh();
        } catch (err) { msg.textContent = err.message; msg.className = 'text-sm text-red-600'; }
    }

    async destroy() {
        const container = document.getElementById('app-content');
        if (container) container.innerHTML = '';
    }
}
