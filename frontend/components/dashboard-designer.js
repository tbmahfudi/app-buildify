/**
 * Dashboard Designer Component
 *
 * Comprehensive UI for creating and editing dashboards with:
 * - Dashboard metadata configuration
 * - Page management
 * - Widget configuration and layout
 * - Global filters and parameters
 * - Theme customization
 */

import { dashboardService } from '../assets/js/dashboard-service.js';
import { reportService } from '../assets/js/report-service.js';
import { showNotification } from '../assets/js/notifications.js';

export class DashboardDesigner {
    constructor(container, dashboardId = null) {
        this.container = container;
        this.dashboardId = dashboardId;
        this.dashboardData = this._getDefaultDashboardData();
        this.currentStep = 1;
        this.totalSteps = 4;
        this.availableReports = [];
        this.selectedPageIndex = 0;
    }

    _getDefaultDashboardData() {
        return {
            name: '',
            description: '',
            category: '',
            tags: [],
            layout_type: 'grid',
            theme: 'light',
            global_parameters: {},
            global_filters: {},
            refresh_interval: 'none',
            is_public: false,
            allowed_roles: [],
            allowed_users: [],
            pages: [{
                name: 'Main',
                slug: 'main',
                description: '',
                icon: 'ph-duotone ph-square',
                layout_config: {
                    columns: 12,
                    row_height: 50,
                    margin: [10, 10]
                },
                order: 0,
                is_default: true,
                widgets: []
            }]
        };
    }

    async render() {
        if (this.dashboardId) {
            await this.loadDashboard();
        }

        // Load available reports for widgets
        await this.loadAvailableReports();

        this.container.innerHTML = `
            <div class="dashboard-designer">
                <!-- Header -->
                <div class="designer-header bg-white shadow-sm p-4 mb-4 rounded">
                    <h2 class="text-2xl font-bold text-gray-800">
                        ${this.dashboardId ? 'Edit Dashboard' : 'Create New Dashboard'}
                    </h2>
                    <p class="text-gray-600 mt-1">Design your custom dashboard with widgets and visualizations</p>
                </div>

                <!-- Progress Steps -->
                <div class="progress-steps mb-6">
                    ${this._renderProgressSteps()}
                </div>

                <!-- Step Content -->
                <div class="step-content bg-white shadow-sm rounded p-6">
                    <div id="step-container"></div>
                </div>

                <!-- Navigation Buttons -->
                <div class="designer-footer flex justify-between mt-6">
                    <button id="btn-prev" class="btn-secondary ${this.currentStep === 1 ? 'invisible' : ''}">
                        Previous
                    </button>
                    <div class="flex gap-3">
                        <button id="btn-preview" class="btn-outline">
                            Preview Dashboard
                        </button>
                        ${this.currentStep === this.totalSteps ? `
                            <button id="btn-save" class="btn-primary">
                                Save Dashboard
                            </button>
                        ` : `
                            <button id="btn-next" class="btn-primary">
                                Next
                            </button>
                        `}
                    </div>
                </div>
            </div>
        `;

        this._renderCurrentStep();
        this._attachEventListeners();
    }

    _renderProgressSteps() {
        const steps = [
            { num: 1, label: 'Basic Info', icon: 'ℹ️' },
            { num: 2, label: 'Pages', icon: '📄' },
            { num: 3, label: 'Widgets', icon: '📊' },
            { num: 4, label: 'Settings', icon: '⚙️' }
        ];

        return `
            <div class="flex justify-between items-center">
                ${steps.map(step => `
                    <div class="flex-1 ${step.num < this.currentStep ? 'completed' : ''} ${step.num === this.currentStep ? 'active' : ''}">
                        <div class="step-item flex flex-col items-center">
                            <div class="step-circle w-12 h-12 rounded-full flex items-center justify-center font-bold
                                ${step.num < this.currentStep ? 'bg-green-500 text-white' : ''}
                                ${step.num === this.currentStep ? 'bg-blue-600 text-white' : ''}
                                ${step.num > this.currentStep ? 'bg-gray-300 text-gray-600' : ''}">
                                ${step.num <= this.currentStep ? step.icon : step.num}
                            </div>
                            <div class="step-label text-sm mt-2 font-medium
                                ${step.num === this.currentStep ? 'text-blue-600' : 'text-gray-600'}">
                                ${step.label}
                            </div>
                        </div>
                        ${step.num < steps.length ? `
                            <div class="step-line h-1 bg-gray-300 mt-[-20px] ml-6 mr-6
                                ${step.num < this.currentStep ? 'bg-green-500' : ''}"></div>
                        ` : ''}
                    </div>
                `).join('')}
            </div>
        `;
    }

    _renderCurrentStep() {
        const stepContainer = document.getElementById('step-container');
        if (!stepContainer) return;

        switch (this.currentStep) {
            case 1:
                stepContainer.innerHTML = this._renderBasicInfoStep();
                break;
            case 2:
                stepContainer.innerHTML = this._renderPagesStep();
                break;
            case 3:
                stepContainer.innerHTML = this._renderWidgetsStep();
                break;
            case 4:
                stepContainer.innerHTML = this._renderSettingsStep();
                break;
        }

        this._attachStepEventListeners();
    }

    _renderBasicInfoStep() {
        return `
            <h3 class="text-xl font-bold mb-4">Basic Information</h3>
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Dashboard Name *</label>
                    <input type="text" id="dashboard-name" value="${this.dashboardData.name}"
                        class="input-field" placeholder="Enter dashboard name" required>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
                    <textarea id="dashboard-description" rows="3" class="input-field"
                        placeholder="Brief description of the dashboard">${this.dashboardData.description || ''}</textarea>
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Category</label>
                        <input type="text" id="dashboard-category" value="${this.dashboardData.category || ''}"
                            class="input-field" placeholder="e.g., Executive, Operations">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Layout Type</label>
                        <select id="dashboard-layout" class="input-field">
                            <option value="grid" ${this.dashboardData.layout_type === 'grid' ? 'selected' : ''}>Grid Layout</option>
                            <option value="freeform" ${this.dashboardData.layout_type === 'freeform' ? 'selected' : ''}>Freeform</option>
                            <option value="responsive" ${this.dashboardData.layout_type === 'responsive' ? 'selected' : ''}>Responsive Grid</option>
                        </select>
                    </div>
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Theme</label>
                        <select id="dashboard-theme" class="input-field">
                            <option value="light" ${this.dashboardData.theme === 'light' ? 'selected' : ''}>Light</option>
                            <option value="dark" ${this.dashboardData.theme === 'dark' ? 'selected' : ''}>Dark</option>
                            <option value="custom" ${this.dashboardData.theme === 'custom' ? 'selected' : ''}>Custom</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Auto Refresh</label>
                        <select id="dashboard-refresh" class="input-field">
                            <option value="none" ${this.dashboardData.refresh_interval === 'none' ? 'selected' : ''}>None</option>
                            <option value="30s" ${this.dashboardData.refresh_interval === '30s' ? 'selected' : ''}>30 seconds</option>
                            <option value="1m" ${this.dashboardData.refresh_interval === '1m' ? 'selected' : ''}>1 minute</option>
                            <option value="5m" ${this.dashboardData.refresh_interval === '5m' ? 'selected' : ''}>5 minutes</option>
                            <option value="15m" ${this.dashboardData.refresh_interval === '15m' ? 'selected' : ''}>15 minutes</option>
                        </select>
                    </div>
                </div>
                <div class="border-t pt-4 mt-4">
                    <label class="flex items-center">
                        <input type="checkbox" id="dashboard-public" ${this.dashboardData.is_public ? 'checked' : ''}
                            class="mr-2">
                        <span class="text-sm text-gray-700">Make this dashboard publicly accessible</span>
                    </label>
                </div>
            </div>
        `;
    }

    _renderPagesStep() {
        return `
            <h3 class="text-xl font-bold mb-4">Dashboard Pages</h3>
            <div class="mb-4">
                <button id="add-page-btn" class="btn-primary btn-sm">
                    + Add Page
                </button>
            </div>
            <div id="pages-list" class="space-y-3">
                ${this.dashboardData.pages.map((page, idx) => this._renderPageConfig(page, idx)).join('')}
            </div>
            ${this.dashboardData.pages.length === 0 ? `
                <div class="text-center py-8 text-gray-500">
                    <p>No pages configured yet. Add pages to organize your widgets.</p>
                </div>
            ` : ''}
        `;
    }

    _renderPageConfig(page, index) {
        return `
            <div class="page-config border rounded p-4 bg-gray-50" data-index="${index}">
                <div class="grid grid-cols-3 gap-4">
                    <div>
                        <label class="block text-sm font-medium mb-1">Page Name</label>
                        <input type="text" class="input-field page-name" value="${page.name}"
                            placeholder="Page Name">
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-1">Slug</label>
                        <input type="text" class="input-field page-slug" value="${page.slug || ''}"
                            placeholder="page-slug">
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-1">Icon</label>
                        <input type="text" class="input-field page-icon" value="${page.icon || ''}"
                            placeholder="ph-duotone ph-square">
                    </div>
                </div>
                <div class="mt-3">
                    <label class="block text-sm font-medium mb-1">Description</label>
                    <input type="text" class="input-field page-description" value="${page.description || ''}"
                        placeholder="Page description">
                </div>
                <div class="flex justify-between items-center mt-3">
                    <label class="flex items-center text-sm">
                        <input type="checkbox" class="page-default mr-1" ${page.is_default ? 'checked' : ''}>
                        Default Page
                    </label>
                    <button class="text-red-600 hover:text-red-800 text-sm remove-page-btn" ${this.dashboardData.pages.length === 1 ? 'disabled' : ''}>
                        🗑️ Remove
                    </button>
                </div>
            </div>
        `;
    }

    _renderWidgetsStep() {
        const currentPage = this.dashboardData.pages[this.selectedPageIndex] || this.dashboardData.pages[0];

        return `
            <h3 class="text-xl font-bold mb-4">Dashboard Widgets</h3>

            ${this.dashboardData.pages.length > 1 ? `
                <div class="mb-4">
                    <label class="block text-sm font-medium text-gray-700 mb-1">Select Page</label>
                    <select id="page-selector" class="input-field">
                        ${this.dashboardData.pages.map((page, idx) => `
                            <option value="${idx}" ${idx === this.selectedPageIndex ? 'selected' : ''}>
                                ${page.name}
                            </option>
                        `).join('')}
                    </select>
                </div>
            ` : ''}

            <div class="mb-4">
                <button id="add-widget-btn" class="btn-primary btn-sm">
                    + Add Widget
                </button>
            </div>

            <div id="widgets-list" class="space-y-3">
                ${currentPage.widgets.map((widget, idx) => this._renderWidgetConfig(widget, idx)).join('')}
            </div>

            ${currentPage.widgets.length === 0 ? `
                <div class="text-center py-8 text-gray-500">
                    <p>No widgets configured yet. Add widgets to display data and visualizations.</p>
                </div>
            ` : ''}
        `;
    }

    _renderWidgetConfig(widget, index) {
        return `
            <div class="widget-config border rounded p-4 bg-gray-50" data-index="${index}">
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium mb-1">Widget Title</label>
                        <input type="text" class="input-field widget-title" value="${widget.title || ''}"
                            placeholder="Widget Title">
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-1">Widget Type</label>
                        <select class="input-field widget-type">
                            <option value="report_table" ${widget.widget_type === 'report_table' ? 'selected' : ''}>Report Table</option>
                            <option value="chart" ${widget.widget_type === 'chart' ? 'selected' : ''}>Chart</option>
                            <option value="kpi_card" ${widget.widget_type === 'kpi_card' ? 'selected' : ''}>KPI Card</option>
                            <option value="metric" ${widget.widget_type === 'metric' ? 'selected' : ''}>Metric</option>
                            <option value="text" ${widget.widget_type === 'text' ? 'selected' : ''}>Text</option>
                        </select>
                    </div>
                </div>

                ${widget.widget_type === 'report_table' || widget.widget_type === 'chart' || widget.widget_type === 'kpi_card' ? `
                    <div class="mt-3">
                        <label class="block text-sm font-medium mb-1">Data Source (Report)</label>
                        <select class="input-field widget-report">
                            <option value="">Select a report...</option>
                            ${this.availableReports.map(report => `
                                <option value="${report.id}" ${widget.report_definition_id === report.id ? 'selected' : ''}>
                                    ${report.name}
                                </option>
                            `).join('')}
                        </select>
                    </div>
                ` : ''}

                <div class="grid grid-cols-4 gap-3 mt-3">
                    <div>
                        <label class="block text-sm font-medium mb-1">X Position</label>
                        <input type="number" class="input-field widget-x" value="${widget.position?.x || 0}" min="0" max="11">
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-1">Y Position</label>
                        <input type="number" class="input-field widget-y" value="${widget.position?.y || 0}" min="0">
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-1">Width</label>
                        <input type="number" class="input-field widget-w" value="${widget.position?.w || 4}" min="1" max="12">
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-1">Height</label>
                        <input type="number" class="input-field widget-h" value="${widget.position?.h || 3}" min="1" max="20">
                    </div>
                </div>

                <div class="flex justify-between items-center mt-3">
                    <div class="flex gap-4">
                        <label class="flex items-center text-sm">
                            <input type="checkbox" class="widget-show-title mr-1" ${widget.show_title !== false ? 'checked' : ''}>
                            Show Title
                        </label>
                        <label class="flex items-center text-sm">
                            <input type="checkbox" class="widget-show-border mr-1" ${widget.show_border !== false ? 'checked' : ''}>
                            Show Border
                        </label>
                    </div>
                    <button class="text-red-600 hover:text-red-800 text-sm remove-widget-btn">
                        🗑️ Remove
                    </button>
                </div>
            </div>
        `;
    }

    _renderSettingsStep() {
        return `
            <h3 class="text-xl font-bold mb-4">Dashboard Settings</h3>
            <div class="space-y-6">
                <div class="border rounded p-4">
                    <h4 class="font-medium mb-3">Global Filters</h4>
                    <p class="text-sm text-gray-500 mb-3">Configure global filters that apply to all widgets</p>
                    <button id="add-global-filter-btn" class="btn-sm btn-outline">
                        + Add Global Filter
                    </button>
                    <div id="global-filters-list" class="mt-3 space-y-2">
                        <!-- Global filters will be added here -->
                        <p class="text-sm text-gray-400">No global filters configured</p>
                    </div>
                </div>

                <div class="border rounded p-4">
                    <h4 class="font-medium mb-3">Permissions</h4>
                    <div class="space-y-3">
                        <div>
                            <label class="flex items-center">
                                <input type="checkbox" id="dashboard-public-final" ${this.dashboardData.is_public ? 'checked' : ''}
                                    class="mr-2">
                                <span class="text-sm">Public Dashboard (accessible to all users)</span>
                            </label>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Allowed Roles</label>
                            <input type="text" id="dashboard-allowed-roles" class="input-field"
                                placeholder="Enter role IDs separated by commas"
                                value="${(this.dashboardData.allowed_roles || []).join(', ')}">
                            <p class="text-xs text-gray-500 mt-1">Leave empty to allow all roles</p>
                        </div>
                    </div>
                </div>

                <div class="border rounded p-4">
                    <h4 class="font-medium mb-3">Summary</h4>
                    <dl class="grid grid-cols-2 gap-3 text-sm">
                        <div>
                            <dt class="font-medium text-gray-700">Dashboard Name:</dt>
                            <dd class="text-gray-600">${this.dashboardData.name || 'Not set'}</dd>
                        </div>
                        <div>
                            <dt class="font-medium text-gray-700">Layout Type:</dt>
                            <dd class="text-gray-600">${this.dashboardData.layout_type}</dd>
                        </div>
                        <div>
                            <dt class="font-medium text-gray-700">Pages:</dt>
                            <dd class="text-gray-600">${this.dashboardData.pages.length}</dd>
                        </div>
                        <div>
                            <dt class="font-medium text-gray-700">Total Widgets:</dt>
                            <dd class="text-gray-600">${this.dashboardData.pages.reduce((sum, p) => sum + p.widgets.length, 0)}</dd>
                        </div>
                        <div>
                            <dt class="font-medium text-gray-700">Theme:</dt>
                            <dd class="text-gray-600">${this.dashboardData.theme}</dd>
                        </div>
                        <div>
                            <dt class="font-medium text-gray-700">Auto Refresh:</dt>
                            <dd class="text-gray-600">${this.dashboardData.refresh_interval}</dd>
                        </div>
                    </dl>
                </div>
            </div>
        `;
    }

    async loadDashboard() {
        try {
            const loadedData = await dashboardService.getDashboard(this.dashboardId);

            // Merge with defaults
            this.dashboardData = {
                ...this._getDefaultDashboardData(),
                ...loadedData,
                pages: loadedData.pages || this._getDefaultDashboardData().pages
            };
        } catch (error) {
            showNotification('Failed to load dashboard: ' + error.message, 'error');
        }
    }

    async loadAvailableReports() {
        try {
            const reports = await reportService.listReportDefinitions({ limit: 100 });
            this.availableReports = reports;
        } catch (error) {
            console.error('Failed to load reports:', error);
            this.availableReports = [];
        }
    }

    _attachEventListeners() {
        // Navigation
        const btnPrev = document.getElementById('btn-prev');
        const btnNext = document.getElementById('btn-next');
        const btnSave = document.getElementById('btn-save');
        const btnPreview = document.getElementById('btn-preview');

        if (btnPrev) {
            btnPrev.addEventListener('click', () => this._previousStep());
        }
        if (btnNext) {
            btnNext.addEventListener('click', () => this._nextStep());
        }
        if (btnSave) {
            btnSave.addEventListener('click', () => this._saveDashboard());
        }
        if (btnPreview) {
            btnPreview.addEventListener('click', () => this._previewDashboard());
        }
    }

    _attachStepEventListeners() {
        // Step 1: Basic Info
        const dashboardName = document.getElementById('dashboard-name');
        if (dashboardName) {
            dashboardName.addEventListener('change', (e) => {
                this.dashboardData.name = e.target.value;
            });
        }

        // Step 2: Pages
        const addPageBtn = document.getElementById('add-page-btn');
        if (addPageBtn) {
            addPageBtn.addEventListener('click', () => this._addPage());
        }

        const removePageBtns = document.querySelectorAll('.remove-page-btn');
        removePageBtns.forEach((btn, index) => {
            btn.addEventListener('click', () => this._removePage(index));
        });

        // Step 3: Widgets
        const addWidgetBtn = document.getElementById('add-widget-btn');
        if (addWidgetBtn) {
            addWidgetBtn.addEventListener('click', () => this._addWidget());
        }

        const pageSelector = document.getElementById('page-selector');
        if (pageSelector) {
            pageSelector.addEventListener('change', (e) => {
                this.selectedPageIndex = parseInt(e.target.value);
                this._renderCurrentStep();
            });
        }

        const removeWidgetBtns = document.querySelectorAll('.remove-widget-btn');
        removeWidgetBtns.forEach((btn, index) => {
            btn.addEventListener('click', () => this._removeWidget(index));
        });
    }

    _addPage() {
        const newPage = {
            name: `Page ${this.dashboardData.pages.length + 1}`,
            slug: `page-${this.dashboardData.pages.length + 1}`,
            description: '',
            icon: 'ph-duotone ph-square',
            layout_config: {
                columns: 12,
                row_height: 50,
                margin: [10, 10]
            },
            order: this.dashboardData.pages.length,
            is_default: false,
            widgets: []
        };
        this.dashboardData.pages.push(newPage);
        this._renderCurrentStep();
    }

    _removePage(index) {
        if (this.dashboardData.pages.length <= 1) {
            showNotification('Cannot remove the last page', 'error');
            return;
        }
        this.dashboardData.pages.splice(index, 1);
        this._renderCurrentStep();
    }

    _addWidget() {
        const currentPage = this.dashboardData.pages[this.selectedPageIndex];
        const newWidget = {
            title: `Widget ${currentPage.widgets.length + 1}`,
            description: '',
            widget_type: 'kpi_card',
            report_definition_id: null,
            position: {
                x: 0,
                y: currentPage.widgets.length * 3,
                w: 4,
                h: 3
            },
            show_title: true,
            show_border: true,
            order: currentPage.widgets.length
        };
        currentPage.widgets.push(newWidget);
        this._renderCurrentStep();
    }

    _removeWidget(index) {
        const currentPage = this.dashboardData.pages[this.selectedPageIndex];
        currentPage.widgets.splice(index, 1);
        this._renderCurrentStep();
    }

    _collectStepData() {
        switch (this.currentStep) {
            case 1:
                this.dashboardData.name = document.getElementById('dashboard-name')?.value || '';
                this.dashboardData.description = document.getElementById('dashboard-description')?.value || '';
                this.dashboardData.category = document.getElementById('dashboard-category')?.value || '';
                this.dashboardData.layout_type = document.getElementById('dashboard-layout')?.value || 'grid';
                this.dashboardData.theme = document.getElementById('dashboard-theme')?.value || 'light';
                this.dashboardData.refresh_interval = document.getElementById('dashboard-refresh')?.value || 'none';
                this.dashboardData.is_public = document.getElementById('dashboard-public')?.checked || false;
                break;
            case 2:
                // Collect page data from inputs
                document.querySelectorAll('.page-config').forEach((pageEl, idx) => {
                    if (this.dashboardData.pages[idx]) {
                        this.dashboardData.pages[idx].name = pageEl.querySelector('.page-name').value;
                        this.dashboardData.pages[idx].slug = pageEl.querySelector('.page-slug').value;
                        this.dashboardData.pages[idx].icon = pageEl.querySelector('.page-icon').value;
                        this.dashboardData.pages[idx].description = pageEl.querySelector('.page-description').value;
                        this.dashboardData.pages[idx].is_default = pageEl.querySelector('.page-default').checked;
                    }
                });
                break;
            case 3:
                // Collect widget data from inputs
                const currentPage = this.dashboardData.pages[this.selectedPageIndex];
                document.querySelectorAll('.widget-config').forEach((widgetEl, idx) => {
                    if (currentPage.widgets[idx]) {
                        currentPage.widgets[idx].title = widgetEl.querySelector('.widget-title').value;
                        currentPage.widgets[idx].widget_type = widgetEl.querySelector('.widget-type').value;
                        currentPage.widgets[idx].report_definition_id = widgetEl.querySelector('.widget-report')?.value || null;
                        currentPage.widgets[idx].position = {
                            x: parseInt(widgetEl.querySelector('.widget-x').value) || 0,
                            y: parseInt(widgetEl.querySelector('.widget-y').value) || 0,
                            w: parseInt(widgetEl.querySelector('.widget-w').value) || 4,
                            h: parseInt(widgetEl.querySelector('.widget-h').value) || 3
                        };
                        currentPage.widgets[idx].show_title = widgetEl.querySelector('.widget-show-title').checked;
                        currentPage.widgets[idx].show_border = widgetEl.querySelector('.widget-show-border').checked;
                    }
                });
                break;
            case 4:
                this.dashboardData.is_public = document.getElementById('dashboard-public-final')?.checked || false;
                const allowedRoles = document.getElementById('dashboard-allowed-roles')?.value || '';
                this.dashboardData.allowed_roles = allowedRoles ? allowedRoles.split(',').map(r => r.trim()).filter(r => r) : [];
                break;
        }
    }

    _previousStep() {
        if (this.currentStep > 1) {
            this._collectStepData();
            this.currentStep--;
            this.render();
        }
    }

    _nextStep() {
        this._collectStepData();
        if (this._validateCurrentStep()) {
            if (this.currentStep < this.totalSteps) {
                this.currentStep++;
                this.render();
            }
        }
    }

    _validateCurrentStep() {
        if (this.currentStep === 1) {
            if (!this.dashboardData.name) {
                showNotification('Dashboard name is required', 'error');
                return false;
            }
        }
        return true;
    }

    async _saveDashboard() {
        this._collectStepData();

        try {
            let result;
            if (this.dashboardId) {
                result = await dashboardService.updateDashboard(this.dashboardId, this.dashboardData);
                showNotification('Dashboard updated successfully', 'success');
            } else {
                result = await dashboardService.createDashboard(this.dashboardData);
                showNotification('Dashboard created successfully', 'success');
            }

            // Redirect to dashboard list or viewer
            setTimeout(() => {
                window.location.hash = '#/sample-reports-dashboards';
            }, 1500);
        } catch (error) {
            showNotification('Failed to save dashboard: ' + error.message, 'error');
        }
    }

    _previewDashboard() {
        showNotification('Preview functionality coming soon', 'info');
    }
}
