class ReportsListPage {
    constructor() {
        this.table = null;
        this.init();
    }

    async init() {
        // Create button handler
        document.getElementById('create-report-btn').addEventListener('click', () => {
            window.location.hash = '#/report-designer';
        });

        // Search handler
        document.getElementById('search-reports').addEventListener('input', (e) => {
            if (this.table && this.table.search) {
                this.table.search(e.target.value);
            }
        });

        // Filter handler
        document.getElementById('filter-category').addEventListener('change', (e) => {
            if (this.table && this.table.filter) {
                if (e.target.value) {
                    this.table.filter({ category: e.target.value });
                } else {
                    this.table.clearFilters();
                }
            }
        });

        // Clear filters handler
        document.getElementById('clear-filters-btn').addEventListener('click', () => {
            document.getElementById('search-reports').value = '';
            document.getElementById('filter-category').value = '';
            if (this.table) {
                if (this.table.clearFilters) this.table.clearFilters();
                if (this.table.search) this.table.search('');
            }
        });

        // Initialize table
        this.initTable();
    }

    async initTable() {
        const container = document.getElementById('reports-table-container');

        // Check if DynamicTable is available
        if (typeof DynamicTable === 'undefined') {
            container.innerHTML = `
                <div class="p-8 text-center">
                    <p class="text-gray-500">Loading reports...</p>
                </div>
            `;

            // Fallback: Load reports directly
            try {
                const response = await apiFetch('/api/v1/reports/definitions');
                this.renderSimpleTable(container, response.items || response || []);
            } catch (error) {
                console.error('Failed to load reports:', error);
                container.innerHTML = `
                    <div class="p-8 text-center">
                        <p class="text-red-500">Failed to load reports: ${error.message}</p>
                    </div>
                `;
            }
            return;
        }

        this.table = new DynamicTable(container, {
            entity: 'report_definitions',
            apiEndpoint: '/api/v1/reports/definitions',
            config: {
                columns: [
                    {
                        name: 'name',
                        label: 'Report Name',
                        sortable: true,
                        render: (value, row) => {
                            return `
                                <div>
                                    <div class="font-medium text-gray-900">${value}</div>
                                    <div class="text-sm text-gray-500">${row.description || ''}</div>
                                </div>
                            `;
                        }
                    },
                    {
                        name: 'category',
                        label: 'Category',
                        sortable: true,
                        render: (value) => {
                            const colors = {
                                'sales': 'bg-blue-100 text-blue-800',
                                'financial': 'bg-green-100 text-green-800',
                                'operational': 'bg-orange-100 text-orange-800',
                                'custom': 'bg-purple-100 text-purple-800'
                            };
                            const color = colors[value] || 'bg-gray-100 text-gray-800';
                            return `<span class="px-2 py-1 text-xs font-medium rounded ${color}">${value || 'Uncategorized'}</span>`;
                        }
                    },
                    {
                        name: 'data_source',
                        label: 'Data Source',
                        sortable: true
                    },
                    {
                        name: 'created_at',
                        label: 'Created',
                        type: 'datetime',
                        sortable: true
                    },
                    {
                        name: 'updated_at',
                        label: 'Modified',
                        type: 'datetime',
                        sortable: true
                    }
                ],
                defaultSort: { column: 'updated_at', direction: 'desc' },
                pageSize: 25
            },
            actions: {
                view: {
                    label: 'Run Report',
                    icon: 'ph-play',
                    handler: (row) => {
                        window.location.hash = `#/report-viewer/${row.id}`;
                    }
                },
                edit: {
                    label: 'Edit',
                    icon: 'ph-pencil',
                    handler: (row) => {
                        window.location.hash = `#/report-designer?id=${row.id}`;
                    }
                },
                delete: {
                    label: 'Delete',
                    icon: 'ph-trash',
                    className: 'text-red-600 hover:text-red-800',
                    handler: async (row) => {
                        if (confirm(`Delete report "${row.name}"? This action cannot be undone.`)) {
                            try {
                                await apiFetch(`/api/v1/reports/definitions/${row.id}`, {
                                    method: 'DELETE'
                                });
                                if (window.showNotification) {
                                    showNotification('Report deleted successfully', 'success');
                                }
                                this.table.refresh();
                            } catch (error) {
                                if (window.showNotification) {
                                    showNotification('Failed to delete report: ' + error.message, 'error');
                                }
                            }
                        }
                    }
                }
            }
        });

        this.table.render();
    }

    renderSimpleTable(container, reports) {
        if (!reports || reports.length === 0) {
            container.innerHTML = `
                <div class="p-8 text-center">
                    <i class="ph-duotone ph-files text-6xl text-gray-300 mb-4"></i>
                    <p class="text-gray-500 mb-4">No reports yet</p>
                    <button onclick="window.location.hash='#/report-designer'" class="btn btn-primary">
                        Create Your First Report
                    </button>
                </div>
            `;
            return;
        }

        const tableHTML = `
            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                        <tr>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Report Name</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Data Source</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                        </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200">
                        ${reports.map(report => `
                            <tr>
                                <td class="px-6 py-4 whitespace-nowrap">
                                    <div class="text-sm font-medium text-gray-900">${report.name}</div>
                                    <div class="text-sm text-gray-500">${report.description || ''}</div>
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap">
                                    <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                                        ${report.category || 'Uncategorized'}
                                    </span>
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${report.data_source || '-'}</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${new Date(report.created_at).toLocaleDateString()}</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                    <button onclick="window.location.hash='#/report-viewer/${report.id}'" class="text-indigo-600 hover:text-indigo-900 mr-3">Run</button>
                                    <button onclick="window.location.hash='#/report-designer?id=${report.id}'" class="text-indigo-600 hover:text-indigo-900 mr-3">Edit</button>
                                    <button onclick="reportsListPage.deleteReport('${report.id}', '${report.name}')" class="text-red-600 hover:text-red-900">Delete</button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;

        container.innerHTML = tableHTML;
    }

    async deleteReport(id, name) {
        if (confirm(`Delete report "${name}"? This action cannot be undone.`)) {
            try {
                await apiFetch(`/api/v1/reports/definitions/${id}`, { method: 'DELETE' });
                if (window.showNotification) {
                    showNotification('Report deleted successfully', 'success');
                }
                // Reload the page
                this.init();
            } catch (error) {
                if (window.showNotification) {
                    showNotification('Failed to delete report: ' + error.message, 'error');
                }
            }
        }
    }
}

// Export to global scope
window.ReportsListPage = ReportsListPage;
window.reportsListPage = null;

// Initialize when route loads
document.addEventListener('DOMContentLoaded', () => {
    if (window.location.hash.includes('reports-list')) {
        window.reportsListPage = new ReportsListPage();
    }
});
