/**
 * Healthcare Dashboard Page
 *
 * Light-DOM page class per docs/modules/MODULE_FRONTEND_CONTRACT.md (§4a).
 * Renders a clinic overview with stat cards and a recent-activity panel.
 * Uses static SAMPLE data (clearly labeled) — no backend wiring required.
 */

export default class HealthcareDashboardPage {
    constructor() {
        this.name = 'healthcare-dashboard';
    }

    async render() {
        const container = document.getElementById('app-content');
        if (!container) return;

        const stats = [
            { label: "Today's Appointments", value: '24', delta: '+3 vs yesterday', icon: 'ph-duotone ph-calendar-check', color: 'text-sky-600', bg: 'bg-sky-50' },
            { label: 'Active Patients', value: '1,287', delta: '+18 this week', icon: 'ph-duotone ph-users-three', color: 'text-emerald-600', bg: 'bg-emerald-50' },
            { label: 'Pending Lab Orders', value: '9', delta: '2 urgent', icon: 'ph-duotone ph-flask', color: 'text-amber-600', bg: 'bg-amber-50' },
            { label: 'Revenue (MTD)', value: '$48.2k', delta: '+12% vs last month', icon: 'ph-duotone ph-currency-circle-dollar', color: 'text-rose-600', bg: 'bg-rose-50' }
        ];

        const activity = [
            { icon: 'ph-duotone ph-calendar-plus', color: 'text-sky-600', text: 'New appointment booked for Sarah Lee', time: '5 min ago' },
            { icon: 'ph-duotone ph-pill', color: 'text-indigo-600', text: 'Prescription issued by Dr. Tan', time: '22 min ago' },
            { icon: 'ph-duotone ph-flask', color: 'text-amber-600', text: 'Lab result ready for Patient #4821', time: '1 hr ago' },
            { icon: 'ph-duotone ph-receipt', color: 'text-emerald-600', text: 'Invoice #INV-2041 marked paid', time: '2 hr ago' },
            { icon: 'ph-duotone ph-user-plus', color: 'text-rose-600', text: 'New patient registered: J. Mendoza', time: '3 hr ago' }
        ];

        const statCards = stats.map(s => `
            <div class="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
                <div class="flex items-center justify-between">
                    <div class="w-11 h-11 rounded-lg ${s.bg} flex items-center justify-center">
                        <i class="${s.icon} ${s.color} text-2xl"></i>
                    </div>
                </div>
                <p class="mt-4 text-2xl font-semibold text-gray-900">${s.value}</p>
                <p class="text-sm text-gray-500">${s.label}</p>
                <p class="mt-1 text-xs ${s.color}">${s.delta}</p>
            </div>
        `).join('');

        const activityRows = activity.map(a => `
            <li class="flex items-start gap-3 py-3 border-b border-gray-100 last:border-0">
                <span class="mt-0.5"><i class="${a.icon} ${a.color} text-lg"></i></span>
                <div class="flex-1 min-w-0">
                    <p class="text-sm text-gray-800">${a.text}</p>
                    <p class="text-xs text-gray-400">${a.time}</p>
                </div>
            </li>
        `).join('');

        container.innerHTML = `
            <div class="p-6 max-w-7xl mx-auto">
                <div class="flex items-center justify-between mb-6">
                    <div class="flex items-center gap-3">
                        <span class="w-10 h-10 rounded-lg bg-rose-50 flex items-center justify-center">
                            <i class="ph-duotone ph-first-aid-kit text-rose-600 text-2xl"></i>
                        </span>
                        <div>
                            <h1 class="text-xl font-semibold text-gray-900">Healthcare Dashboard</h1>
                            <p class="text-sm text-gray-500">Clinic overview at a glance</p>
                        </div>
                    </div>
                    <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-50 text-amber-700 text-xs font-medium">
                        <i class="ph-duotone ph-info"></i> Sample data
                    </span>
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                    ${statCards}
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div class="lg:col-span-2 bg-white rounded-xl border border-gray-200 shadow-sm p-5">
                        <h2 class="text-sm font-semibold text-gray-700 mb-3">Appointments by hour (today)</h2>
                        <div class="flex items-end gap-2 h-40">
                            ${[4,7,9,12,8,11,6,5,3].map((v,i) => `
                                <div class="flex-1 flex flex-col items-center gap-1">
                                    <div class="w-full bg-sky-200 rounded-t" style="height:${v*8}px"></div>
                                    <span class="text-[10px] text-gray-400">${8+i}:00</span>
                                </div>
                            `).join('')}
                        </div>
                        <p class="mt-3 text-xs text-gray-400">Illustrative sample distribution.</p>
                    </div>

                    <div class="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
                        <h2 class="text-sm font-semibold text-gray-700 mb-2">Recent Activity</h2>
                        <ul>${activityRows}</ul>
                    </div>
                </div>
            </div>
        `;
    }

    async destroy() {
        const container = document.getElementById('app-content');
        if (container) container.innerHTML = '';
    }
}
