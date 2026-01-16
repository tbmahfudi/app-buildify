/**
 * Dashboards List Page
 *
 * Manages the dashboard list view with grid and list display modes.
 * Provides search, filtering, and CRUD operations for dashboards.
 */

class DashboardsListPage {
    constructor() {
        this.viewMode = 'grid'; // 'grid' or 'list'
        this.dashboards = [];
        this.filteredDashboards = [];
        this.table = null;
        this.init();
    }

    async init() {
        this.setupEventListeners();
        await this.loadDashboards();
        this.renderDashboards();
    }

    setupEventListeners() {
        // Create Dashboard button
        const createBtn = document.getElementById('create-dashboard-btn');
        if (createBtn) {
            createBtn.addEventListener('click', () => {
                window.location.hash = '#/dashboard-designer';
            });
        }

        // View mode toggle buttons
        const gridBtn = document.getElementById('view-grid-btn');
        const listBtn = document.getElementById('view-list-btn');

        if (gridBtn) {
            gridBtn.addEventListener('click', () => {
                this.switchViewMode('grid');
            });
        }

        if (listBtn) {
            listBtn.addEventListener('click', () => {
                this.switchViewMode('list');
            });
        }

        // Search functionality
        const searchInput = document.getElementById('search-dashboards');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.filterDashboards(e.target.value);
            });
        }
    }

    switchViewMode(mode) {
        this.viewMode = mode;

        // Update button states
        const gridBtn = document.getElementById('view-grid-btn');
        const listBtn = document.getElementById('view-list-btn');

        if (mode === 'grid') {
            gridBtn?.classList.add('active');
            listBtn?.classList.remove('active');
            document.getElementById('dashboards-grid')?.classList.remove('hidden');
            document.getElementById('dashboards-list')?.classList.add('hidden');
        } else {
            listBtn?.classList.add('active');
            gridBtn?.classList.remove('active');
            document.getElementById('dashboards-grid')?.classList.add('hidden');
            document.getElementById('dashboards-list')?.classList.remove('hidden');
        }

        this.renderDashboards();
    }

    async loadDashboards() {
        try {
            const response = await fetch('/api/v1/dashboards', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.dashboards = data.dashboards || data.items || data;
                this.filteredDashboards = [...this.dashboards];
            } else {
                console.error('Failed to load dashboards:', response.statusText);
                // Load sample data for demonstration
                this.dashboards = this.getSampleDashboards();
                this.filteredDashboards = [...this.dashboards];
            }
        } catch (error) {
            console.error('Error loading dashboards:', error);
            // Load sample data for demonstration
            this.dashboards = this.getSampleDashboards();
            this.filteredDashboards = [...this.dashboards];
        }
    }

    getSampleDashboards() {
        return [
            {
                id: 1,
                name: 'Sales Overview',
                description: 'Comprehensive sales metrics and KPIs',
                created_at: '2024-01-15T10:00:00Z',
                updated_at: '2024-01-20T14:30:00Z',
                owner: 'John Doe',
                widget_count: 8,
                is_public: true,
                thumbnail: null
            },
            {
                id: 2,
                name: 'Marketing Analytics',
                description: 'Campaign performance and engagement metrics',
                created_at: '2024-01-18T09:15:00Z',
                updated_at: '2024-01-22T11:45:00Z',
                owner: 'Jane Smith',
                widget_count: 6,
                is_public: false,
                thumbnail: null
            },
            {
                id: 3,
                name: 'Executive Dashboard',
                description: 'High-level business metrics for leadership',
                created_at: '2024-01-10T08:00:00Z',
                updated_at: '2024-01-25T16:20:00Z',
                owner: 'Admin User',
                widget_count: 12,
                is_public: true,
                thumbnail: null
            }
        ];
    }

    filterDashboards(searchTerm) {
        const term = searchTerm.toLowerCase().trim();

        if (!term) {
            this.filteredDashboards = [...this.dashboards];
        } else {
            this.filteredDashboards = this.dashboards.filter(dashboard => {
                return (
                    dashboard.name?.toLowerCase().includes(term) ||
                    dashboard.description?.toLowerCase().includes(term) ||
                    dashboard.owner?.toLowerCase().includes(term)
                );
            });
        }

        this.renderDashboards();
    }

    renderDashboards() {
        if (this.viewMode === 'grid') {
            this.renderGridView();
        } else {
            this.renderListView();
        }
    }

    renderGridView() {
        const container = document.getElementById('dashboards-grid');
        if (!container) return;

        if (this.filteredDashboards.length === 0) {
            container.innerHTML = this.renderEmptyState();
            return;
        }

        container.innerHTML = this.filteredDashboards.map(dashboard => `
            <div class="card hover:shadow-lg transition-shadow cursor-pointer" data-dashboard-id="${dashboard.id}">
                <!-- Thumbnail -->
                <div class="dashboard-thumbnail bg-gradient-to-br from-blue-50 to-indigo-50 h-48 flex items-center justify-center rounded-t-lg">
                    ${dashboard.thumbnail
                        ? `<img src="${dashboard.thumbnail}" alt="${dashboard.name}" class="w-full h-full object-cover rounded-t-lg" />`
                        : `<i class="ph-duotone ph-chart-bar text-6xl text-indigo-400"></i>`
                    }
                </div>

                <!-- Content -->
                <div class="p-4">
                    <div class="flex justify-between items-start mb-2">
                        <h3 class="text-lg font-semibold text-gray-900 truncate flex-1">
                            ${this.escapeHtml(dashboard.name)}
                        </h3>
                        ${dashboard.is_public
                            ? '<span class="badge badge-sm bg-green-100 text-green-800"><i class="ph ph-globe mr-1"></i>Public</span>'
                            : '<span class="badge badge-sm bg-gray-100 text-gray-800"><i class="ph ph-lock mr-1"></i>Private</span>'
                        }
                    </div>

                    <p class="text-sm text-gray-600 mb-3 line-clamp-2">
                        ${this.escapeHtml(dashboard.description || 'No description')}
                    </p>

                    <div class="flex items-center justify-between text-xs text-gray-500 mb-3">
                        <span><i class="ph ph-user mr-1"></i>${this.escapeHtml(dashboard.owner)}</span>
                        <span><i class="ph ph-chart-pie-slice mr-1"></i>${dashboard.widget_count} widgets</span>
                    </div>

                    <div class="text-xs text-gray-400 mb-3">
                        Updated ${this.formatDate(dashboard.updated_at)}
                    </div>

                    <!-- Actions -->
                    <div class="flex gap-2 pt-3 border-t border-gray-200">
                        <button
                            class="btn btn-sm btn-primary flex-1 view-dashboard-btn"
                            data-dashboard-id="${dashboard.id}"
                        >
                            <i class="ph ph-eye mr-1"></i>View
                        </button>
                        <button
                            class="btn btn-sm btn-secondary edit-dashboard-btn"
                            data-dashboard-id="${dashboard.id}"
                        >
                            <i class="ph ph-pencil"></i>
                        </button>
                        <button
                            class="btn btn-sm btn-secondary duplicate-dashboard-btn"
                            data-dashboard-id="${dashboard.id}"
                            title="Duplicate"
                        >
                            <i class="ph ph-copy"></i>
                        </button>
                        <button
                            class="btn btn-sm btn-danger delete-dashboard-btn"
                            data-dashboard-id="${dashboard.id}"
                        >
                            <i class="ph ph-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `).join('');

        this.attachGridEventListeners();
    }

    renderListView() {
        const container = document.getElementById('dashboards-table-container');
        if (!container) return;

        if (this.filteredDashboards.length === 0) {
            container.innerHTML = this.renderEmptyState();
            return;
        }

        // Try to use DynamicTable if available
        if (typeof DynamicTable !== 'undefined') {
            this.initDynamicTable();
        } else {
            // Fallback to simple table rendering
            container.innerHTML = `
                <div class="overflow-x-auto">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Description</th>
                                <th>Owner</th>
                                <th>Widgets</th>
                                <th>Visibility</th>
                                <th>Last Updated</th>
                                <th class="text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${this.filteredDashboards.map(dashboard => `
                                <tr>
                                    <td class="font-medium">${this.escapeHtml(dashboard.name)}</td>
                                    <td class="text-sm text-gray-600">${this.escapeHtml(dashboard.description || 'N/A')}</td>
                                    <td class="text-sm">${this.escapeHtml(dashboard.owner)}</td>
                                    <td class="text-sm text-center">${dashboard.widget_count}</td>
                                    <td>
                                        ${dashboard.is_public
                                            ? '<span class="badge badge-sm bg-green-100 text-green-800">Public</span>'
                                            : '<span class="badge badge-sm bg-gray-100 text-gray-800">Private</span>'
                                        }
                                    </td>
                                    <td class="text-sm text-gray-500">${this.formatDate(dashboard.updated_at)}</td>
                                    <td>
                                        <div class="flex gap-2 justify-end">
                                            <button
                                                class="btn btn-sm btn-primary view-dashboard-btn"
                                                data-dashboard-id="${dashboard.id}"
                                                title="View"
                                            >
                                                <i class="ph ph-eye"></i>
                                            </button>
                                            <button
                                                class="btn btn-sm btn-secondary edit-dashboard-btn"
                                                data-dashboard-id="${dashboard.id}"
                                                title="Edit"
                                            >
                                                <i class="ph ph-pencil"></i>
                                            </button>
                                            <button
                                                class="btn btn-sm btn-secondary duplicate-dashboard-btn"
                                                data-dashboard-id="${dashboard.id}"
                                                title="Duplicate"
                                            >
                                                <i class="ph ph-copy"></i>
                                            </button>
                                            <button
                                                class="btn btn-sm btn-danger delete-dashboard-btn"
                                                data-dashboard-id="${dashboard.id}"
                                                title="Delete"
                                            >
                                                <i class="ph ph-trash"></i>
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;

            this.attachListEventListeners();
        }
    }

    initDynamicTable() {
        const container = document.getElementById('dashboards-table-container');

        this.table = new DynamicTable(container, {
            entity: 'dashboard',
            apiEndpoint: '/api/v1/dashboards',
            columns: [
                { key: 'name', label: 'Name', sortable: true },
                { key: 'description', label: 'Description' },
                { key: 'owner', label: 'Owner', sortable: true },
                {
                    key: 'widget_count',
                    label: 'Widgets',
                    sortable: true,
                    align: 'center'
                },
                {
                    key: 'is_public',
                    label: 'Visibility',
                    render: (value) => value
                        ? '<span class="badge badge-sm bg-green-100 text-green-800">Public</span>'
                        : '<span class="badge badge-sm bg-gray-100 text-gray-800">Private</span>'
                },
                {
                    key: 'updated_at',
                    label: 'Last Updated',
                    sortable: true,
                    render: (value) => this.formatDate(value)
                }
            ],
            actions: [
                {
                    label: 'View',
                    icon: 'ph-eye',
                    class: 'btn-primary',
                    onClick: (dashboard) => this.viewDashboard(dashboard.id)
                },
                {
                    label: 'Edit',
                    icon: 'ph-pencil',
                    class: 'btn-secondary',
                    onClick: (dashboard) => this.editDashboard(dashboard.id)
                },
                {
                    label: 'Duplicate',
                    icon: 'ph-copy',
                    class: 'btn-secondary',
                    onClick: (dashboard) => this.duplicateDashboard(dashboard.id)
                },
                {
                    label: 'Delete',
                    icon: 'ph-trash',
                    class: 'btn-danger',
                    onClick: (dashboard) => this.deleteDashboard(dashboard.id)
                }
            ],
            pagination: true,
            pageSize: 10
        });
    }

    attachGridEventListeners() {
        // View buttons
        document.querySelectorAll('.view-dashboard-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const dashboardId = btn.dataset.dashboardId;
                this.viewDashboard(dashboardId);
            });
        });

        // Edit buttons
        document.querySelectorAll('.edit-dashboard-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const dashboardId = btn.dataset.dashboardId;
                this.editDashboard(dashboardId);
            });
        });

        // Duplicate buttons
        document.querySelectorAll('.duplicate-dashboard-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const dashboardId = btn.dataset.dashboardId;
                this.duplicateDashboard(dashboardId);
            });
        });

        // Delete buttons
        document.querySelectorAll('.delete-dashboard-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const dashboardId = btn.dataset.dashboardId;
                this.deleteDashboard(dashboardId);
            });
        });

        // Card click to view
        document.querySelectorAll('[data-dashboard-id]').forEach(card => {
            if (!card.classList.contains('btn')) {
                card.addEventListener('click', () => {
                    const dashboardId = card.dataset.dashboardId;
                    this.viewDashboard(dashboardId);
                });
            }
        });
    }

    attachListEventListeners() {
        // Similar to grid but for table rows
        document.querySelectorAll('.view-dashboard-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const dashboardId = btn.dataset.dashboardId;
                this.viewDashboard(dashboardId);
            });
        });

        document.querySelectorAll('.edit-dashboard-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const dashboardId = btn.dataset.dashboardId;
                this.editDashboard(dashboardId);
            });
        });

        document.querySelectorAll('.duplicate-dashboard-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const dashboardId = btn.dataset.dashboardId;
                this.duplicateDashboard(dashboardId);
            });
        });

        document.querySelectorAll('.delete-dashboard-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const dashboardId = btn.dataset.dashboardId;
                this.deleteDashboard(dashboardId);
            });
        });
    }

    viewDashboard(dashboardId) {
        // Navigate to dashboard view/runtime
        window.location.hash = `#/dashboard/${dashboardId}`;
    }

    editDashboard(dashboardId) {
        // Navigate to dashboard designer with existing dashboard
        window.location.hash = `#/dashboard-designer?id=${dashboardId}`;
    }

    async duplicateDashboard(dashboardId) {
        if (!confirm('Are you sure you want to duplicate this dashboard?')) {
            return;
        }

        try {
            const response = await fetch(`/api/v1/dashboards/${dashboardId}/duplicate`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const result = await response.json();
                alert('Dashboard duplicated successfully!');
                await this.loadDashboards();
                this.renderDashboards();
            } else {
                throw new Error('Failed to duplicate dashboard');
            }
        } catch (error) {
            console.error('Error duplicating dashboard:', error);
            alert('Failed to duplicate dashboard. Please try again.');
        }
    }

    async deleteDashboard(dashboardId) {
        if (!confirm('Are you sure you want to delete this dashboard? This action cannot be undone.')) {
            return;
        }

        try {
            const response = await fetch(`/api/v1/dashboards/${dashboardId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                alert('Dashboard deleted successfully!');
                await this.loadDashboards();
                this.renderDashboards();
            } else {
                throw new Error('Failed to delete dashboard');
            }
        } catch (error) {
            console.error('Error deleting dashboard:', error);
            alert('Failed to delete dashboard. Please try again.');
        }
    }

    renderEmptyState() {
        return `
            <div class="text-center py-12">
                <i class="ph-duotone ph-chart-bar text-6xl text-gray-300 mb-4"></i>
                <h3 class="text-lg font-semibold text-gray-700 mb-2">No Dashboards Found</h3>
                <p class="text-gray-500 mb-6">
                    ${this.filteredDashboards.length === 0 && this.dashboards.length > 0
                        ? 'No dashboards match your search criteria.'
                        : 'Get started by creating your first dashboard.'
                    }
                </p>
                <button
                    onclick="window.location.hash='#/dashboard-designer'"
                    class="btn btn-primary"
                >
                    <i class="ph-duotone ph-plus mr-2"></i>
                    Create Your First Dashboard
                </button>
            </div>
        `;
    }

    formatDate(dateString) {
        if (!dateString) return 'N/A';

        const date = new Date(dateString);
        const now = new Date();
        const diffTime = Math.abs(now - date);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

        if (diffDays === 0) {
            return 'Today';
        } else if (diffDays === 1) {
            return 'Yesterday';
        } else if (diffDays < 7) {
            return `${diffDays} days ago`;
        } else if (diffDays < 30) {
            const weeks = Math.floor(diffDays / 7);
            return `${weeks} week${weeks > 1 ? 's' : ''} ago`;
        } else {
            return date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
        }
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize the page when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new DashboardsListPage();
    });
} else {
    new DashboardsListPage();
}
