/**
 * Healthcare Invoices Page (stub)
 * Light-DOM page class per MODULE_FRONTEND_CONTRACT.md §4a.
 */

export default class InvoicesPage {
    constructor() { this.name = 'healthcare-invoices'; }

    async render() {
        const container = document.getElementById('app-content');
        if (!container) return;

        const rows = [
            { no: 'INV-2041', patient: 'Sarah Lee', date: '2026-06-27', amount: '$120.00', status: 'Paid', color: 'bg-emerald-50 text-emerald-700' },
            { no: 'INV-2042', patient: 'James Wong', date: '2026-06-27', amount: '$85.50', status: 'Pending', color: 'bg-amber-50 text-amber-700' },
            { no: 'INV-2043', patient: 'Maria Garcia', date: '2026-06-26', amount: '$240.00', status: 'Overdue', color: 'bg-rose-50 text-rose-700' },
            { no: 'INV-2044', patient: 'David Chen', date: '2026-06-26', amount: '$60.00', status: 'Paid', color: 'bg-emerald-50 text-emerald-700' }
        ];

        const tbody = rows.map(r => `
            <tr class="border-b border-gray-100 last:border-0">
                <td class="px-4 py-3 text-sm font-medium text-gray-700">${r.no}</td>
                <td class="px-4 py-3 text-sm text-gray-800">${r.patient}</td>
                <td class="px-4 py-3 text-sm text-gray-600">${r.date}</td>
                <td class="px-4 py-3 text-sm text-gray-800">${r.amount}</td>
                <td class="px-4 py-3"><span class="inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${r.color}">${r.status}</span></td>
            </tr>
        `).join('');

        container.innerHTML = `
            <div class="p-6 max-w-7xl mx-auto">
                <div class="bg-white rounded-xl border border-gray-200 shadow-sm px-5 py-4 mb-5 flex items-center gap-3">
                    <span class="w-10 h-10 rounded-lg bg-orange-50 flex items-center justify-center">
                        <i class="ph-duotone ph-receipt text-orange-600 text-2xl"></i>
                    </span>
                    <div>
                        <h1 class="text-lg font-semibold text-gray-900">Invoices</h1>
                        <p class="text-sm text-gray-500">Billing and patient invoices (sample data)</p>
                    </div>
                </div>
                <div class="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                    <table class="w-full">
                        <thead class="bg-gray-50">
                            <tr>
                                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Invoice</th>
                                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Patient</th>
                                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Date</th>
                                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Amount</th>
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
