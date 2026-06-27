/**
 * Healthcare Appointments Page (stub)
 * Light-DOM page class per MODULE_FRONTEND_CONTRACT.md §4a.
 */

export default class AppointmentsPage {
    constructor() { this.name = 'healthcare-appointments'; }

    async render() {
        const container = document.getElementById('app-content');
        if (!container) return;

        const rows = [
            { time: '09:00', patient: 'Sarah Lee', provider: 'Dr. Tan', type: 'Consultation', status: 'Confirmed', color: 'bg-emerald-50 text-emerald-700' },
            { time: '09:30', patient: 'James Wong', provider: 'Dr. Patel', type: 'Follow-up', status: 'Checked in', color: 'bg-sky-50 text-sky-700' },
            { time: '10:15', patient: 'Maria Garcia', provider: 'Dr. Tan', type: 'Vaccination', status: 'Pending', color: 'bg-amber-50 text-amber-700' },
            { time: '11:00', patient: 'David Chen', provider: 'Dr. Lim', type: 'Consultation', status: 'Confirmed', color: 'bg-emerald-50 text-emerald-700' }
        ];

        const tbody = rows.map(r => `
            <tr class="border-b border-gray-100 last:border-0">
                <td class="px-4 py-3 text-sm font-medium text-gray-700">${r.time}</td>
                <td class="px-4 py-3 text-sm text-gray-800">${r.patient}</td>
                <td class="px-4 py-3 text-sm text-gray-600">${r.provider}</td>
                <td class="px-4 py-3 text-sm text-gray-600">${r.type}</td>
                <td class="px-4 py-3"><span class="inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${r.color}">${r.status}</span></td>
            </tr>
        `).join('');

        container.innerHTML = `
            <div class="p-6 max-w-7xl mx-auto">
                <div class="bg-white rounded-xl border border-gray-200 shadow-sm px-5 py-4 mb-5 flex items-center gap-3">
                    <span class="w-10 h-10 rounded-lg bg-sky-50 flex items-center justify-center">
                        <i class="ph-duotone ph-calendar-check text-sky-600 text-2xl"></i>
                    </span>
                    <div>
                        <h1 class="text-lg font-semibold text-gray-900">Appointments</h1>
                        <p class="text-sm text-gray-500">Today's clinic appointment queue (sample data)</p>
                    </div>
                </div>
                <div class="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                    <table class="w-full">
                        <thead class="bg-gray-50">
                            <tr>
                                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Time</th>
                                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Patient</th>
                                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Provider</th>
                                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Type</th>
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
