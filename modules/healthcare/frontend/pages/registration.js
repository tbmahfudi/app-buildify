/**
 * Healthcare — Visit Registration page (epic-09).
 * Light-DOM page class. Front-desk walk-in registration: pick a patient +
 * department + payer, register the visit, and issue a queue ticket in one step.
 */

const PAYERS = [
    ['self_pay', 'Self-pay'], ['bpjs', 'BPJS'],
    ['private_insurance', 'Private insurance'], ['corporate', 'Corporate'],
];

function authToken() {
    try { return JSON.parse(localStorage.getItem('tokens') || '{}').access || ''; }
    catch (e) { return ''; }
}

export default class RegistrationPage {
    constructor() {
        this.name = 'healthcare-registration';
        this.branchId = null;
        this.departments = [];
        this.patients = [];
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
            const base = `/api/v1/modules/healthcare/branches/${this.branchId}`;
            [this.departments, this.patients] = await Promise.all([
                this._fetch(base + '/departments'),
                this._fetch('/api/v1/modules/healthcare/patients'),
            ]);
            this.departments = this.departments.filter(d => d.is_active);
            this._paint();
        } catch (e) {
            container.innerHTML = this._shell(
                `<div class="p-6"><div class="rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3">${e.message}</div></div>`);
        }
    }

    _shell(body) {
        return `<div class="p-6 max-w-3xl mx-auto">
            <div class="bg-white rounded-xl border border-gray-200 shadow-sm px-5 py-4 mb-5 flex items-center gap-3">
                <span class="w-10 h-10 rounded-lg bg-teal-50 flex items-center justify-center"><i class="ph-duotone ph-user-plus text-teal-600 text-2xl"></i></span>
                <div><h1 class="text-lg font-semibold text-gray-900">Visit Registration</h1>
                    <p class="text-sm text-gray-500">Register a walk-in patient and issue a queue ticket</p></div>
            </div>
            <div id="hc-reg-body">${body}</div></div>`;
    }

    _paint() {
        const patientOpts = this.patients.map(p =>
            `<option value="${p.id}">${p.full_name}${p.masked_phone ? ' · ' + p.masked_phone : ''}</option>`).join('');
        const deptOpts = this.departments.map(d => `<option value="${d.id}">${d.name}</option>`).join('');
        const payerOpts = PAYERS.map(([v, l]) => `<option value="${v}">${l}</option>`).join('');

        this._container.querySelector('#hc-reg-body').innerHTML = `
            <div class="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
                <form id="hc-reg-form" class="space-y-4">
                    <div><label class="block text-sm text-gray-600 mb-1">Patient</label>
                        <select id="hc-r-patient" required class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm">${patientOpts || '<option value="">No patients</option>'}</select></div>
                    <div class="grid grid-cols-2 gap-4">
                        <div><label class="block text-sm text-gray-600 mb-1">Department</label>
                            <select id="hc-r-dept" required class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm">${deptOpts}</select></div>
                        <div><label class="block text-sm text-gray-600 mb-1">Payer</label>
                            <select id="hc-r-payer" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm">${payerOpts}</select></div>
                    </div>
                    <div class="flex items-center gap-3">
                        <button type="submit" class="inline-flex items-center gap-1.5 bg-teal-600 text-white text-sm font-medium rounded-lg px-4 py-2 hover:bg-teal-700"><i class="ph ph-ticket"></i> Register &amp; issue ticket</button>
                        <span id="hc-reg-msg" class="text-sm"></span>
                    </div>
                </form>
            </div>
            <div id="hc-reg-result" class="mt-4"></div>`;

        this._container.querySelector('#hc-reg-form').addEventListener('submit', (e) => this._submit(e));
    }

    async _submit(e) {
        e.preventDefault();
        const msg = this._container.querySelector('#hc-reg-msg');
        msg.textContent = 'Registering…'; msg.className = 'text-sm text-gray-400';
        const base = `/api/v1/modules/healthcare/branches/${this.branchId}`;
        try {
            const visit = await this._fetch(base + '/visits/walk-in', {
                method: 'POST', body: JSON.stringify({
                    patient_id: this._container.querySelector('#hc-r-patient').value,
                    department_id: this._container.querySelector('#hc-r-dept').value,
                    payment_category: this._container.querySelector('#hc-r-payer').value,
                }),
            });
            const ticket = await this._fetch(base + `/visits/${visit.id}/queue-ticket`, { method: 'POST', body: '{}' });
            msg.textContent = '';
            this._container.querySelector('#hc-reg-result').innerHTML = `
                <div class="rounded-xl border border-teal-200 bg-teal-50 px-5 py-4 flex items-center gap-4">
                    <div class="text-3xl font-extrabold text-teal-700">${ticket.ticket_number}</div>
                    <div class="text-sm text-teal-800">Ticket issued · status <b>${ticket.status}</b><br>
                        <a href="#/healthcare/queue-board" class="text-teal-700 underline">Open the queue board →</a></div>
                </div>`;
        } catch (err) {
            msg.textContent = err.message; msg.className = 'text-sm text-red-600';
        }
    }

    async destroy() {
        const container = document.getElementById('app-content');
        if (container) container.innerHTML = '';
    }
}
