/**
 * Healthcare Prescriptions Page (stub)
 * Light-DOM page class per MODULE_FRONTEND_CONTRACT.md §4a.
 */

export default class PrescriptionsPage {
    constructor() { this.name = 'healthcare-prescriptions'; }

    async render() {
        const container = document.getElementById('app-content');
        if (!container) return;

        const rows = [
            { rx: 'RX-7781', patient: 'Sarah Lee', drug: 'Amoxicillin 500mg', provider: 'Dr. Tan', status: 'Dispensed', color: 'bg-emerald-50 text-emerald-700' },
            { rx: 'RX-7782', patient: 'James Wong', drug: 'Lisinopril 10mg', provider: 'Dr. Patel', status: 'Ready', color: 'bg-sky-50 text-sky-700' },
            { rx: 'RX-7783', patient: 'Maria Garcia', drug: 'Metformin 850mg', provider: 'Dr. Tan', status: 'Pending', color: 'bg-amber-50 text-amber-700' },
            { rx: 'RX-7784', patient: 'David Chen', drug: 'Ibuprofen 400mg', provider: 'Dr. Lim', status: 'Dispensed', color: 'bg-emerald-50 text-emerald-700' }
        ];

        const tbody = rows.map(r => `
            <tr class="border-b border-gray-100 last:border-0">
                <td class="px-4 py-3 text-sm font-medium text-gray-700">${r.rx}</td>
                <td class="px-4 py-3 text-sm text-gray-800">${r.patient}</td>
                <td class="px-4 py-3 text-sm text-gray-600">${r.drug}</td>
                <td class="px-4 py-3 text-sm text-gray-600">${r.provider}</td>
                <td class="px-4 py-3"><span class="inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${r.color}">${r.status}</span></td>
            </tr>
        `).join('');

        container.innerHTML = `
            <div class="p-6 max-w-7xl mx-auto">
                <div class="bg-white rounded-xl border border-gray-200 shadow-sm px-5 py-4 mb-5 flex items-center gap-3">
                    <span class="w-10 h-10 rounded-lg bg-violet-50 flex items-center justify-center">
                        <i class="ph-duotone ph-pill text-violet-600 text-2xl"></i>
                    </span>
                    <div>
                        <h1 class="text-lg font-semibold text-gray-900">Prescriptions</h1>
                        <p class="text-sm text-gray-500">Pharmacy prescriptions and dispensing (sample data)</p>
                    </div>
                </div>
                <div class="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                    <table class="w-full">
                        <thead class="bg-gray-50">
                            <tr>
                                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Rx</th>
                                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Patient</th>
                                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Medication</th>
                                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Provider</th>
                                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Status</th>
                            </tr>
                        </thead>
                        <tbody>${tbody}</tbody>
                    </table>
                </div>
            </div>
        `;
    }

    async destroy() {
        const container = document.getElementById('app-content');
        if (container) container.innerHTML = '';
    }
}
