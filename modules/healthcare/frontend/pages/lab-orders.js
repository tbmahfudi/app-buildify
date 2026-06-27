/**
 * Healthcare Lab Orders Page (stub)
 * Light-DOM page class per MODULE_FRONTEND_CONTRACT.md §4a.
 */

export default class LabOrdersPage {
    constructor() { this.name = 'healthcare-lab-orders'; }

    async render() {
        const container = document.getElementById('app-content');
        if (!container) return;

        const rows = [
            { id: 'LAB-3310', patient: 'Sarah Lee', panel: 'Complete Blood Count', priority: 'Routine', status: 'Resulted', color: 'bg-emerald-50 text-emerald-700' },
            { id: 'LAB-3311', patient: 'James Wong', panel: 'Lipid Panel', priority: 'Routine', status: 'In progress', color: 'bg-sky-50 text-sky-700' },
            { id: 'LAB-3312', patient: 'Maria Garcia', panel: 'HbA1c', priority: 'Urgent', status: 'Pending', color: 'bg-amber-50 text-amber-700' },
            { id: 'LAB-3313', patient: 'David Chen', panel: 'Thyroid Function', priority: 'Urgent', status: 'Collected', color: 'bg-indigo-50 text-indigo-700' }
        ];

        const tbody = rows.map(r => `
            <tr class="border-b border-gray-100 last:border-0">
                <td class="px-4 py-3 text-sm font-medium text-gray-700">${r.id}</td>
                <td class="px-4 py-3 text-sm text-gray-800">${r.patient}</td>
                <td class="px-4 py-3 text-sm text-gray-600">${r.panel}</td>
                <td class="px-4 py-3 text-sm text-gray-600">${r.priority}</td>
                <td class="px-4 py-3"><span class="inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${r.color}">${r.status}</span></td>
            </tr>
        `).join('');

        container.innerHTML = `
            <div class="p-6 max-w-7xl mx-auto">
                <div class="bg-white rounded-xl border border-gray-200 shadow-sm px-5 py-4 mb-5 flex items-center gap-3">
                    <span class="w-10 h-10 rounded-lg bg-amber-50 flex items-center justify-center">
                        <i class="ph-duotone ph-flask text-amber-600 text-2xl"></i>
                    </span>
                    <div>
                        <h1 class="text-lg font-semibold text-gray-900">Lab Orders</h1>
                        <p class="text-sm text-gray-500">Laboratory orders and results (sample data)</p>
                    </div>
                </div>
                <div class="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                    <table class="w-full">
                        <thead class="bg-gray-50">
                            <tr>
                                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Order</th>
                                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Patient</th>
                                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Panel</th>
                                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Priority</th>
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
