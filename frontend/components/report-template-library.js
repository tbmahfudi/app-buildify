/**
 * Report Template Library Component
 *
 * Pre-built report templates for quick start.
 */

import { showNotification } from '../assets/js/notifications.js';

export class ReportTemplateLibrary {
    constructor(container, options = {}) {
        this.container = container;
        this.options = options;
        this.onTemplateSelect = options.onTemplateSelect || (() => {});

        this.templates = [
            {
                id: 'sales-summary',
                name: 'Sales Summary',
                description: 'Monthly sales performance report with totals and trends',
                category: 'Sales',
                icon: 'ph-chart-line-up',
                previewImage: null,
                config: {
                    report_type: 'tabular',
                    columns: [
                        { name: 'date', label: 'Date', format: 'date' },
                        { name: 'product', label: 'Product' },
                        { name: 'quantity', label: 'Quantity', aggregate: 'SUM' },
                        { name: 'revenue', label: 'Revenue', format: 'currency', aggregate: 'SUM' }
                    ]
                }
            },
            {
                id: 'customer-list',
                name: 'Customer List',
                description: 'Complete customer directory with contact information',
                category: 'CRM',
                icon: 'ph-users',
                previewImage: null,
                config: {
                    report_type: 'tabular',
                    columns: [
                        { name: 'name', label: 'Customer Name' },
                        { name: 'email', label: 'Email' },
                        { name: 'phone', label: 'Phone' },
                        { name: 'created_at', label: 'Joined Date', format: 'date' }
                    ]
                }
            },
            {
                id: 'inventory-status',
                name: 'Inventory Status',
                description: 'Current stock levels and reorder points',
                category: 'Inventory',
                icon: 'ph-package',
                previewImage: null,
                config: {
                    report_type: 'tabular',
                    columns: [
                        { name: 'product', label: 'Product' },
                        { name: 'sku', label: 'SKU' },
                        { name: 'quantity', label: 'In Stock' },
                        { name: 'reorder_point', label: 'Reorder Point' }
                    ]
                }
            },
            {
                id: 'monthly-revenue',
                name: 'Monthly Revenue',
                description: 'Revenue trends by month with year-over-year comparison',
                category: 'Financial',
                icon: 'ph-currency-dollar',
                previewImage: null,
                config: {
                    report_type: 'chart',
                    visualization_config: { type: 'bar' },
                    columns: [
                        { name: 'month', label: 'Month' },
                        { name: 'revenue', label: 'Revenue', aggregate: 'SUM', format: 'currency' }
                    ]
                }
            },
            {
                id: 'blank',
                name: 'Blank Report',
                description: 'Start from scratch with no pre-configured columns',
                category: 'Custom',
                icon: 'ph-file-plus',
                previewImage: null,
                config: {
                    report_type: 'tabular',
                    columns: []
                }
            }
        ];

        this.init();
    }

    init() {
        this.render();
    }

    render() {
        this.container.innerHTML = `
            <div class="report-template-library">
                <div class="mb-6">
                    <h2 class="text-2xl font-bold text-gray-900 mb-2">Choose a Template</h2>
                    <p class="text-gray-600">Select a pre-built template to get started quickly, or create a blank report</p>
                </div>

                <!-- Category Filters -->
                <div class="flex gap-2 mb-6 overflow-x-auto pb-2">
                    <button class="category-filter-btn px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium" data-category="all">
                        All Templates
                    </button>
                    ${[...new Set(this.templates.map(t => t.category))].map(category => `
                        <button class="category-filter-btn px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200" data-category="${category}">
                            ${category}
                        </button>
                    `).join('')}
                </div>

                <!-- Templates Grid -->
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" id="templates-grid">
                    ${this.renderTemplates()}
                </div>
            </div>
        `;

        this.attachEventListeners();
    }

    renderTemplates(filterCategory = 'all') {
        const filteredTemplates = filterCategory === 'all'
            ? this.templates
            : this.templates.filter(t => t.category === filterCategory);

        return filteredTemplates.map(template => `
            <div class="template-card bg-white border-2 border-gray-200 rounded-lg p-6 cursor-pointer hover:border-blue-500 hover:shadow-lg transition-all" data-template="${template.id}">
                <div class="flex items-start justify-between mb-4">
                    <div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                        <i class="ph-duotone ${template.icon} text-2xl text-blue-600"></i>
                    </div>
                    <span class="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">${template.category}</span>
                </div>

                <h3 class="text-lg font-semibold text-gray-900 mb-2">${this.escapeHtml(template.name)}</h3>
                <p class="text-sm text-gray-600 mb-4">${this.escapeHtml(template.description)}</p>

                <button class="w-full btn btn-primary btn-sm use-template-btn" data-template="${template.id}">
                    <i class="ph ph-arrow-right mr-1"></i>
                    Use Template
                </button>
            </div>
        `).join('');
    }

    attachEventListeners() {
        // Category filters
        document.querySelectorAll('.category-filter-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const category = btn.dataset.category;

                // Update active state
                document.querySelectorAll('.category-filter-btn').forEach(b => {
                    b.classList.remove('bg-blue-600', 'text-white');
                    b.classList.add('bg-gray-100', 'text-gray-700');
                });
                btn.classList.remove('bg-gray-100', 'text-gray-700');
                btn.classList.add('bg-blue-600', 'text-white');

                // Filter templates
                document.getElementById('templates-grid').innerHTML = this.renderTemplates(category);
                this.attachTemplateListeners();
            });
        });

        this.attachTemplateListeners();
    }

    attachTemplateListeners() {
        // Template cards
        document.querySelectorAll('.template-card').forEach(card => {
            card.addEventListener('click', (e) => {
                if (!e.target.closest('.use-template-btn')) {
                    // Preview template (could show modal)
                    const templateId = card.dataset.template;
                    this.previewTemplate(templateId);
                }
            });
        });

        // Use template buttons
        document.querySelectorAll('.use-template-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const templateId = btn.dataset.template;
                this.selectTemplate(templateId);
            });
        });
    }

    previewTemplate(templateId) {
        const template = this.templates.find(t => t.id === templateId);
        if (!template) return;

        // Could show a modal with template preview
        console.log('Preview template:', template);
    }

    selectTemplate(templateId) {
        const template = this.templates.find(t => t.id === templateId);
        if (!template) return;

        showNotification(`Using template: ${template.name}`, 'success');
        this.onTemplateSelect(template);
    }

    getTemplates() {
        return this.templates;
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}
