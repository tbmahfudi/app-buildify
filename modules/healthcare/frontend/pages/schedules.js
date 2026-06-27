/**
 * Healthcare Schedules Page (stub)
 * Light-DOM page class per MODULE_FRONTEND_CONTRACT.md §4a.
 */

export default class SchedulesPage {
    constructor() { this.name = 'healthcare-schedules'; }

    async render() {
        const container = document.getElementById('app-content');
        if (!container) return;

        const rows = [
            { provider: 'Dr. Tan', days: 'Mon - Fri', hours: '09:00 - 17:00', room: 'Room 1', status: 'Active' },
            { provider: 'Dr. Patel', days: 'Tue, Thu', hours: '10:00 - 15:00', room: 'Room 2', status: 'Active' },
            { provider: 'Dr. Lim', days: 'Mon, Wed, Fri', hours: '08:00 - 13:00', room: 'Room 3', status: 'Active' },
            { provider: 'Dr. Okafor', days: 'Sat', hours: '09:00 - 12:00', room: 'Room 1', status: 'Limited' }
        ];

        const tbody = rows.map(r => `
            <tr class="border-b border-gray-100 last:border-0">
                <td class="px-4 py-3 text-sm font-medium text-gray-800">${r.provider}</td>
                <td class="px-4 py-3 text-sm text-gray-600">${r.days}</td>
                <td class="px-4 py-3 text-sm text-gray-600">${r.hours}</td>
                <td class="px-4 py-3 text-sm text-gray-600">${r.room}</td>
                <td class="px-4 py-3 text-sm text-gray-600">${r.status}</td>
            </tr>
        `).join('');

        container.innerHTML = `
            <div class="p-6 max-w-7xl mx-auto">
                <div class="bg-white rounded-xl border border-gray-200 shadow-sm px-5 py-4 mb-5 flex items-center gap-3">
                    <span class="w-10 h-10 rounded-lg bg-indigo-50 flex items-center justify-center">
                        <i class="ph-duotone ph-calendar text-indigo-600 text-2xl"></i>
                    </span>
                    <div>
                        <h1 class="text-lg font-semibold text-gray-900">Schedules</h1>
                        <p class="text-sm text-gray-500">Provider availability and clinic schedules (sample data)</p>
                    </div>
                </div>
                <div class="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                    <table class="w-full">
                        <thead class="bg-gray-50">
                            <tr>
                                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Provider</th>
                                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Days</th>
                                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Hours</th>
                                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Room</th>
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
