/**
 * Dashboard Template Library Component
 *
 * Pre-built dashboard templates for quick start.
 * Provides template gallery with one-click clone and customize.
 *
 * Features:
 * - 5 pre-built templates (Executive, Sales, Operations, Analytics, Financial)
 * - Template gallery with screenshots
 * - One-click clone and customize
 * - Industry-specific templates
 * - Template preview
 *
 * Usage:
 * const library = new DashboardTemplateLibrary(container, {
 *   onTemplateSelect: (template) => console.log('Selected:', template),
 *   onTemplateClone: (template) => console.log('Cloned:', template)
 * });
 */

export class DashboardTemplateLibrary {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        this.options = options;

        // Callbacks
        this.onTemplateSelect = options.onTemplateSelect || (() => {});
        this.onTemplateClone = options.onTemplateClone || (() => {});
        this.onClose = options.onClose || (() => {});

        // State
        this.selectedTemplate = null;
        this.searchQuery = '';
        this.selectedCategory = 'all'; // all, executive, sales, operations, analytics, financial

        // Define templates
        this.templates = this.defineTemplates();

        this.init();
    }

    defineTemplates() {
        return [
            {
                id: 'executive-dashboard',
                name: 'Executive Dashboard',
                category: 'executive',
                description: 'High-level KPIs, trends, and alerts for executives',
                thumbnail: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgdmlld0JveD0iMCAwIDQwMCAzMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjQwMCIgaGVpZ2h0PSIzMDAiIGZpbGw9IiNGM0Y0RjYiLz48cmVjdCB4PSIxMCIgeT0iMTAiIHdpZHRoPSIxMjAiIGhlaWdodD0iODAiIGZpbGw9IndoaXRlIiByeD0iNCIvPjxyZWN0IHg9IjE0MCIgeT0iMTAiIHdpZHRoPSIxMjAiIGhlaWdodD0iODAiIGZpbGw9IndoaXRlIiByeD0iNCIvPjxyZWN0IHg9IjI3MCIgeT0iMTAiIHdpZHRoPSIxMjAiIGhlaWdodD0iODAiIGZpbGw9IndoaXRlIiByeD0iNCIvPjxyZWN0IHg9IjEwIiB5PSIxMDAiIHdpZHRoPSIyNTAiIGhlaWdodD0iMTkwIiBmaWxsPSJ3aGl0ZSIgcng9IjQiLz48cmVjdCB4PSIyNzAiIHk9IjEwMCIgd2lkdGg9IjEyMCIgaGVpZ2h0PSIxOTAiIGZpbGw9IndoaXRlIiByeD0iNCIvPjwvc3ZnPg==',
                widgets: [
                    { id: 'w1', type: 'metric-kpi', title: 'Revenue', x: 0, y: 0, w: 3, h: 2 },
                    { id: 'w2', type: 'metric-kpi', title: 'Profit Margin', x: 3, y: 0, w: 3, h: 2 },
                    { id: 'w3', type: 'metric-kpi', title: 'Customer Growth', x: 6, y: 0, w: 3, h: 2 },
                    { id: 'w4', type: 'metric-kpi', title: 'Active Users', x: 9, y: 0, w: 3, h: 2 },
                    { id: 'w5', type: 'chart-line', title: 'Revenue Trend', x: 0, y: 2, w: 8, h: 4 },
                    { id: 'w6', type: 'chart-donut', title: 'Revenue by Category', x: 8, y: 2, w: 4, h: 4 },
                    { id: 'w7', type: 'table-summary', title: 'Top Products', x: 0, y: 6, w: 6, h: 3 },
                    { id: 'w8', type: 'chart-bar', title: 'Regional Performance', x: 6, y: 6, w: 6, h: 3 }
                ]
            },
            {
                id: 'sales-dashboard',
                name: 'Sales Dashboard',
                category: 'sales',
                description: 'Track revenue, pipeline, conversion rates, and sales performance',
                thumbnail: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgdmlld0JveD0iMCAwIDQwMCAzMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjQwMCIgaGVpZ2h0PSIzMDAiIGZpbGw9IiNGM0Y0RjYiLz48cmVjdCB4PSIxMCIgeT0iMTAiIHdpZHRoPSIxMjAiIGhlaWdodD0iODAiIGZpbGw9IndoaXRlIiByeD0iNCIvPjxyZWN0IHg9IjE0MCIgeT0iMTAiIHdpZHRoPSIxMjAiIGhlaWdodD0iODAiIGZpbGw9IndoaXRlIiByeD0iNCIvPjxyZWN0IHg9IjI3MCIgeT0iMTAiIHdpZHRoPSIxMjAiIGhlaWdodD0iODAiIGZpbGw9IndoaXRlIiByeD0iNCIvPjxyZWN0IHg9IjEwIiB5PSIxMDAiIHdpZHRoPSIxODAiIGhlaWdodD0iMTkwIiBmaWxsPSJ3aGl0ZSIgcng9IjQiLz48cmVjdCB4PSIyMDAiIHk9IjEwMCIgd2lkdGg9IjE5MCIgaGVpZ2h0PSIxOTAiIGZpbGw9IndoaXRlIiByeD0iNCIvPjwvc3ZnPg==',
                widgets: [
                    { id: 'w1', type: 'metric-kpi', title: 'Total Revenue', x: 0, y: 0, w: 3, h: 2 },
                    { id: 'w2', type: 'metric-kpi', title: 'Deals Closed', x: 3, y: 0, w: 3, h: 2 },
                    { id: 'w3', type: 'metric-kpi', title: 'Conversion Rate', x: 6, y: 0, w: 3, h: 2 },
                    { id: 'w4', type: 'metric-gauge', title: 'Quota Achievement', x: 9, y: 0, w: 3, h: 2 },
                    { id: 'w5', type: 'chart-bar', title: 'Sales Pipeline', x: 0, y: 2, w: 6, h: 4 },
                    { id: 'w6', type: 'chart-line', title: 'Monthly Sales Trend', x: 6, y: 2, w: 6, h: 4 },
                    { id: 'w7', type: 'table-grid', title: 'Top Deals', x: 0, y: 6, w: 8, h: 3 },
                    { id: 'w8', type: 'chart-pie', title: 'Sales by Region', x: 8, y: 6, w: 4, h: 3 }
                ]
            },
            {
                id: 'operations-dashboard',
                name: 'Operations Dashboard',
                category: 'operations',
                description: 'Monitor capacity, efficiency, SLA compliance, and operational metrics',
                thumbnail: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgdmlld0JveD0iMCAwIDQwMCAzMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjQwMCIgaGVpZ2h0PSIzMDAiIGZpbGw9IiNGM0Y0RjYiLz48cmVjdCB4PSIxMCIgeT0iMTAiIHdpZHRoPSI5MCIgaGVpZ2h0PSI5MCIgZmlsbD0id2hpdGUiIHJ4PSI0Ii8+PHJlY3QgeD0iMTEwIiB5PSIxMCIgd2lkdGg9IjkwIiBoZWlnaHQ9IjkwIiBmaWxsPSJ3aGl0ZSIgcng9IjQiLz48cmVjdCB4PSIyMTAiIHk9IjEwIiB3aWR0aD0iOTAiIGhlaWdodD0iOTAiIGZpbGw9IndoaXRlIiByeD0iNCIvPjxyZWN0IHg9IjMxMCIgeT0iMTAiIHdpZHRoPSI4MCIgaGVpZ2h0PSI5MCIgZmlsbD0id2hpdGUiIHJ4PSI0Ii8+PHJlY3QgeD0iMTAiIHk9IjExMCIgd2lkdGg9IjM4MCIgaGVpZ2h0PSIxODAiIGZpbGw9IndoaXRlIiByeD0iNCIvPjwvc3ZnPg==',
                widgets: [
                    { id: 'w1', type: 'metric-gauge', title: 'System Capacity', x: 0, y: 0, w: 3, h: 3 },
                    { id: 'w2', type: 'metric-gauge', title: 'CPU Usage', x: 3, y: 0, w: 3, h: 3 },
                    { id: 'w3', type: 'metric-gauge', title: 'Memory Usage', x: 6, y: 0, w: 3, h: 3 },
                    { id: 'w4', type: 'metric-progress', title: 'SLA Compliance', x: 9, y: 0, w: 3, h: 3 },
                    { id: 'w5', type: 'chart-area', title: 'Performance Over Time', x: 0, y: 3, w: 8, h: 4 },
                    { id: 'w6', type: 'table-summary', title: 'Active Tasks', x: 8, y: 3, w: 4, h: 4 },
                    { id: 'w7', type: 'chart-bar', title: 'Resource Utilization', x: 0, y: 7, w: 6, h: 3 },
                    { id: 'w8', type: 'metric-kpi', title: 'Uptime', x: 6, y: 7, w: 3, h: 3 },
                    { id: 'w9', type: 'metric-kpi', title: 'Incidents', x: 9, y: 7, w: 3, h: 3 }
                ]
            },
            {
                id: 'analytics-dashboard',
                name: 'Analytics Dashboard',
                category: 'analytics',
                description: 'Track website traffic, user engagement, and behavior analytics',
                thumbnail: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgdmlld0JveD0iMCAwIDQwMCAzMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjQwMCIgaGVpZ2h0PSIzMDAiIGZpbGw9IiNGM0Y0RjYiLz48cmVjdCB4PSIxMCIgeT0iMTAiIHdpZHRoPSI4MCIgaGVpZ2h0PSI2MCIgZmlsbD0id2hpdGUiIHJ4PSI0Ii8+PHJlY3QgeD0iMTAwIiB5PSIxMCIgd2lkdGg9IjgwIiBoZWlnaHQ9IjYwIiBmaWxsPSJ3aGl0ZSIgcng9IjQiLz48cmVjdCB4PSIxOTAiIHk9IjEwIiB3aWR0aD0iODAiIGhlaWdodD0iNjAiIGZpbGw9IndoaXRlIiByeD0iNCIvPjxyZWN0IHg9IjI4MCIgeT0iMTAiIHdpZHRoPSIxMTAiIGhlaWdodD0iNjAiIGZpbGw9IndoaXRlIiByeD0iNCIvPjxyZWN0IHg9IjEwIiB5PSI4MCIgd2lkdGg9IjI2MCIgaGVpZ2h0PSIxMjAiIGZpbGw9IndoaXRlIiByeD0iNCIvPjxyZWN0IHg9IjI4MCIgeT0iODAiIHdpZHRoPSIxMTAiIGhlaWdodD0iMTIwIiBmaWxsPSJ3aGl0ZSIgcng9IjQiLz48cmVjdCB4PSIxMCIgeT0iMjEwIiB3aWR0aD0iMzgwIiBoZWlnaHQ9IjgwIiBmaWxsPSJ3aGl0ZSIgcng9IjQiLz48L3N2Zz4=',
                widgets: [
                    { id: 'w1', type: 'metric-stat', title: 'Total Visitors', x: 0, y: 0, w: 3, h: 2 },
                    { id: 'w2', type: 'metric-stat', title: 'Page Views', x: 3, y: 0, w: 3, h: 2 },
                    { id: 'w3', type: 'metric-stat', title: 'Bounce Rate', x: 6, y: 0, w: 3, h: 2 },
                    { id: 'w4', type: 'metric-stat', title: 'Avg Session', x: 9, y: 0, w: 3, h: 2 },
                    { id: 'w5', type: 'chart-area', title: 'Traffic Over Time', x: 0, y: 2, w: 8, h: 4 },
                    { id: 'w6', type: 'chart-donut', title: 'Traffic Sources', x: 8, y: 2, w: 4, h: 4 },
                    { id: 'w7', type: 'table-grid', title: 'Top Pages', x: 0, y: 6, w: 6, h: 3 },
                    { id: 'w8', type: 'chart-bar', title: 'Devices', x: 6, y: 6, w: 6, h: 3 }
                ]
            },
            {
                id: 'financial-dashboard',
                name: 'Financial Dashboard',
                category: 'financial',
                description: 'Monitor P&L, cash flow, budget, and financial KPIs',
                thumbnail: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgdmlld0JveD0iMCAwIDQwMCAzMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjQwMCIgaGVpZ2h0PSIzMDAiIGZpbGw9IiNGM0Y0RjYiLz48cmVjdCB4PSIxMCIgeT0iMTAiIHdpZHRoPSIxMjAiIGhlaWdodD0iODAiIGZpbGw9IndoaXRlIiByeD0iNCIvPjxyZWN0IHg9IjE0MCIgeT0iMTAiIHdpZHRoPSIxMjAiIGhlaWdodD0iODAiIGZpbGw9IndoaXRlIiByeD0iNCIvPjxyZWN0IHg9IjI3MCIgeT0iMTAiIHdpZHRoPSIxMjAiIGhlaWdodD0iODAiIGZpbGw9IndoaXRlIiByeD0iNCIvPjxyZWN0IHg9IjEwIiB5PSIxMDAiIHdpZHRoPSIxODAiIGhlaWdodD0iMTkwIiBmaWxsPSJ3aGl0ZSIgcng9IjQiLz48cmVjdCB4PSIyMDAiIHk9IjEwMCIgd2lkdGg9IjE5MCIgaGVpZ2h0PSI5MCIgZmlsbD0id2hpdGUiIHJ4PSI0Ii8+PHJlY3QgeD0iMjAwIiB5PSIyMDAiIHdpZHRoPSIxOTAiIGhlaWdodD0iOTAiIGZpbGw9IndoaXRlIiByeD0iNCIvPjwvc3ZnPg==',
                widgets: [
                    { id: 'w1', type: 'metric-kpi', title: 'Revenue', x: 0, y: 0, w: 3, h: 2 },
                    { id: 'w2', type: 'metric-kpi', title: 'Expenses', x: 3, y: 0, w: 3, h: 2 },
                    { id: 'w3', type: 'metric-kpi', title: 'Net Profit', x: 6, y: 0, w: 3, h: 2 },
                    { id: 'w4', type: 'metric-gauge', title: 'Budget Usage', x: 9, y: 0, w: 3, h: 2 },
                    { id: 'w5', type: 'chart-area', title: 'Cash Flow', x: 0, y: 2, w: 6, h: 4 },
                    { id: 'w6', type: 'chart-pie', title: 'Expense Breakdown', x: 6, y: 2, w: 6, h: 4 },
                    { id: 'w7', type: 'table-summary', title: 'P&L Statement', x: 0, y: 6, w: 8, h: 3 },
                    { id: 'w8', type: 'chart-bar', title: 'Budget vs Actual', x: 8, y: 6, w: 4, h: 3 }
                ]
            }
        ];
    }

    async init() {
        await this.render();
        this.attachEventListeners();
    }

    async render() {
        this.container.innerHTML = `
            <div class="dashboard-template-library bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] flex flex-col">
                <!-- Header -->
                <div class="template-library-header p-6 border-b border-gray-200 flex items-center justify-between">
                    <div>
                        <h2 class="text-xl font-bold text-gray-900">Dashboard Templates</h2>
                        <p class="text-sm text-gray-500 mt-1">Start with a pre-built template and customize to your needs</p>
                    </div>
                    <button id="close-library-btn" class="text-gray-400 hover:text-gray-600">
                        <i class="ph ph-x text-2xl"></i>
                    </button>
                </div>

                <!-- Search & Filter -->
                <div class="template-library-controls p-6 border-b border-gray-200 flex items-center space-x-4">
                    <!-- Search -->
                    <div class="flex-1 relative">
                        <i class="ph ph-magnifying-glass absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"></i>
                        <input type="text" id="template-search"
                            class="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            placeholder="Search templates...">
                    </div>

                    <!-- Category Filter -->
                    <div class="flex items-center space-x-2">
                        <span class="text-sm font-medium text-gray-700">Category:</span>
                        <select id="category-filter" class="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                            <option value="all">All Templates</option>
                            <option value="executive">Executive</option>
                            <option value="sales">Sales</option>
                            <option value="operations">Operations</option>
                            <option value="analytics">Analytics</option>
                            <option value="financial">Financial</option>
                        </select>
                    </div>
                </div>

                <!-- Template Grid -->
                <div class="template-library-content flex-1 overflow-y-auto p-6">
                    <div class="template-grid grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        ${this.renderTemplateCards()}
                    </div>
                </div>
            </div>
        `;
    }

    renderTemplateCards() {
        const filteredTemplates = this.getFilteredTemplates();

        if (filteredTemplates.length === 0) {
            return `
                <div class="col-span-full text-center py-12">
                    <i class="ph ph-magnifying-glass text-6xl text-gray-300 mb-4"></i>
                    <p class="text-gray-500">No templates found</p>
                </div>
            `;
        }

        return filteredTemplates.map(template => `
            <div class="template-card group bg-white border-2 border-gray-200 rounded-lg overflow-hidden hover:border-blue-500 hover:shadow-lg transition-all cursor-pointer ${
                this.selectedTemplate?.id === template.id ? 'border-blue-500 ring-2 ring-blue-200' : ''
            }" data-template-id="${template.id}">
                <!-- Thumbnail -->
                <div class="template-thumbnail aspect-video bg-gray-100 overflow-hidden">
                    <img src="${template.thumbnail}" alt="${template.name}" class="w-full h-full object-cover">
                </div>

                <!-- Info -->
                <div class="template-info p-4">
                    <div class="flex items-start justify-between mb-2">
                        <h3 class="font-semibold text-gray-900 group-hover:text-blue-600">${template.name}</h3>
                        <span class="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-600 rounded">${template.widgets.length} widgets</span>
                    </div>
                    <p class="text-sm text-gray-600 mb-4">${template.description}</p>

                    <!-- Actions -->
                    <div class="flex items-center space-x-2">
                        <button class="preview-template-btn flex-1 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
                            data-template-id="${template.id}">
                            <i class="ph ph-eye mr-1"></i>
                            Preview
                        </button>
                        <button class="use-template-btn flex-1 px-3 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
                            data-template-id="${template.id}">
                            <i class="ph ph-plus mr-1"></i>
                            Use Template
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    getFilteredTemplates() {
        let filtered = this.templates;

        // Filter by category
        if (this.selectedCategory !== 'all') {
            filtered = filtered.filter(t => t.category === this.selectedCategory);
        }

        // Filter by search
        if (this.searchQuery) {
            const query = this.searchQuery.toLowerCase();
            filtered = filtered.filter(t =>
                t.name.toLowerCase().includes(query) ||
                t.description.toLowerCase().includes(query) ||
                t.category.toLowerCase().includes(query)
            );
        }

        return filtered;
    }

    attachEventListeners() {
        const container = this.container;

        // Close button
        const closeBtn = container.querySelector('#close-library-btn');
        closeBtn?.addEventListener('click', () => {
            this.onClose();
        });

        // Search
        const searchInput = container.querySelector('#template-search');
        searchInput?.addEventListener('input', (e) => {
            this.searchQuery = e.target.value;
            this.render();
            this.attachEventListeners();
        });

        // Category filter
        const categoryFilter = container.querySelector('#category-filter');
        categoryFilter?.addEventListener('change', (e) => {
            this.selectedCategory = e.target.value;
            this.render();
            this.attachEventListeners();
        });

        // Template card selection
        container.querySelectorAll('.template-card').forEach(card => {
            card.addEventListener('click', (e) => {
                if (e.target.closest('.preview-template-btn') || e.target.closest('.use-template-btn')) {
                    return;
                }

                const templateId = e.currentTarget.dataset.templateId;
                this.selectTemplate(templateId);
            });
        });

        // Preview buttons
        container.querySelectorAll('.preview-template-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const templateId = e.currentTarget.dataset.templateId;
                this.previewTemplate(templateId);
            });
        });

        // Use template buttons
        container.querySelectorAll('.use-template-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const templateId = e.currentTarget.dataset.templateId;
                this.cloneTemplate(templateId);
            });
        });
    }

    selectTemplate(templateId) {
        const template = this.templates.find(t => t.id === templateId);
        if (template) {
            this.selectedTemplate = template;
            this.onTemplateSelect(template);
            this.render();
            this.attachEventListeners();
        }
    }

    previewTemplate(templateId) {
        const template = this.templates.find(t => t.id === templateId);
        if (template) {
            // Open preview in a modal or new window
            this.showTemplatePreview(template);
        }
    }

    showTemplatePreview(template) {
        // Create preview modal
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4';
        modal.innerHTML = `
            <div class="bg-white rounded-lg shadow-2xl max-w-5xl w-full max-h-[90vh] flex flex-col">
                <div class="p-4 border-b border-gray-200 flex items-center justify-between">
                    <h3 class="text-lg font-semibold text-gray-900">${template.name} - Preview</h3>
                    <button class="close-preview-btn text-gray-400 hover:text-gray-600">
                        <i class="ph ph-x text-xl"></i>
                    </button>
                </div>
                <div class="flex-1 overflow-auto p-6 bg-gray-50">
                    <div class="grid grid-cols-12 gap-4 auto-rows-min">
                        ${template.widgets.map(widget => `
                            <div class="col-span-${widget.w} bg-white rounded-lg shadow p-4" style="grid-row: span ${widget.h};">
                                <div class="font-semibold text-sm mb-2">${widget.title}</div>
                                <div class="bg-gray-100 rounded h-full min-h-[80px] flex items-center justify-center text-xs text-gray-500">
                                    ${widget.type}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                <div class="p-4 border-t border-gray-200 flex justify-end space-x-2">
                    <button class="close-preview-btn px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">
                        Close
                    </button>
                    <button class="use-template-from-preview-btn px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700">
                        Use This Template
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Event listeners
        modal.querySelectorAll('.close-preview-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                modal.remove();
            });
        });

        modal.querySelector('.use-template-from-preview-btn')?.addEventListener('click', () => {
            this.cloneTemplate(template.id);
            modal.remove();
        });

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }

    cloneTemplate(templateId) {
        const template = this.templates.find(t => t.id === templateId);
        if (template) {
            // Clone the template with new IDs
            const clonedTemplate = {
                ...template,
                id: `${template.id}-${Date.now()}`,
                name: `${template.name} (Copy)`,
                widgets: template.widgets.map(w => ({
                    ...w,
                    id: `${w.id}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
                }))
            };

            this.onTemplateClone(clonedTemplate);
        }
    }

    // Public API
    getTemplates() {
        return this.templates;
    }

    getTemplateById(templateId) {
        return this.templates.find(t => t.id === templateId);
    }
}
