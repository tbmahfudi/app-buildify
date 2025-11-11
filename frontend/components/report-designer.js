/**
 * Report Designer Component
 *
 * Comprehensive UI for creating and editing report definitions with:
 * - Report metadata configuration
 * - Data source selection
 * - Column configuration
 * - Parameter definition
 * - Conditional formatting
 * - Preview and testing
 */

import { reportService } from '../assets/js/report-service.js';
import { dataService } from '../assets/js/data-service.js';
import { showNotification } from '../assets/js/notifications.js';

export class ReportDesigner {
    constructor(container, reportId = null) {
        this.container = container;
        this.reportId = reportId;
        this.reportData = this._getDefaultReportData();
        this.currentStep = 1;
        this.totalSteps = 5;
    }

    _getDefaultReportData() {
        return {
            name: '',
            description: '',
            category: '',
            report_type: 'tabular',
            base_entity: '',
            query_config: {
                joins: [],
                filters: { logic: 'AND', conditions: [], groups: [] },
                group_by: [],
                order_by: [],
                limit: null
            },
            columns_config: [],
            parameters: [],
            visualization_config: null,
            formatting_rules: [],
            is_public: false,
            allowed_roles: [],
            allowed_users: []
        };
    }

    async render() {
        if (this.reportId) {
            await this.loadReport();
        }

        this.container.innerHTML = `
            <div class="report-designer">
                <!-- Header -->
                <div class="designer-header bg-white shadow-sm p-4 mb-4 rounded">
                    <h2 class="text-2xl font-bold text-gray-800">
                        ${this.reportId ? 'Edit Report' : 'Create New Report'}
                    </h2>
                    <p class="text-gray-600 mt-1">Design your custom report with parameters and formatting</p>
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
                            Preview Report
                        </button>
                        ${this.currentStep === this.totalSteps ? `
                            <button id="btn-save" class="btn-primary">
                                Save Report
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
            { num: 2, label: 'Data Source', icon: '📊' },
            { num: 3, label: 'Columns', icon: '📋' },
            { num: 4, label: 'Parameters', icon: '⚙️' },
            { num: 5, label: 'Formatting', icon: '🎨' }
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
                stepContainer.innerHTML = this._renderDataSourceStep();
                break;
            case 3:
                stepContainer.innerHTML = this._renderColumnsStep();
                break;
            case 4:
                stepContainer.innerHTML = this._renderParametersStep();
                break;
            case 5:
                stepContainer.innerHTML = this._renderFormattingStep();
                break;
        }

        this._attachStepEventListeners();
    }

    _renderBasicInfoStep() {
        return `
            <h3 class="text-xl font-bold mb-4">Basic Information</h3>
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Report Name *</label>
                    <input type="text" id="report-name" value="${this.reportData.name}"
                        class="input-field" placeholder="Enter report name" required>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
                    <textarea id="report-description" rows="3" class="input-field"
                        placeholder="Brief description of the report">${this.reportData.description || ''}</textarea>
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Category</label>
                        <input type="text" id="report-category" value="${this.reportData.category || ''}"
                            class="input-field" placeholder="e.g., Financial, Operations">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Report Type</label>
                        <select id="report-type" class="input-field">
                            <option value="tabular" ${this.reportData.report_type === 'tabular' ? 'selected' : ''}>Tabular</option>
                            <option value="summary" ${this.reportData.report_type === 'summary' ? 'selected' : ''}>Summary</option>
                            <option value="chart" ${this.reportData.report_type === 'chart' ? 'selected' : ''}>Chart</option>
                            <option value="dashboard" ${this.reportData.report_type === 'dashboard' ? 'selected' : ''}>Dashboard</option>
                        </select>
                    </div>
                </div>
                <div class="border-t pt-4 mt-4">
                    <label class="flex items-center">
                        <input type="checkbox" id="report-public" ${this.reportData.is_public ? 'checked' : ''}
                            class="mr-2">
                        <span class="text-sm text-gray-700">Make this report publicly accessible</span>
                    </label>
                </div>
            </div>
        `;
    }

    _renderDataSourceStep() {
        return `
            <h3 class="text-xl font-bold mb-4">Data Source Configuration</h3>
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Base Entity/Table *</label>
                    <select id="base-entity" class="input-field">
                        <option value="">Select an entity...</option>
                        <option value="companies" ${this.reportData.base_entity === 'companies' ? 'selected' : ''}>Companies</option>
                        <option value="branches" ${this.reportData.base_entity === 'branches' ? 'selected' : ''}>Branches</option>
                        <option value="departments" ${this.reportData.base_entity === 'departments' ? 'selected' : ''}>Departments</option>
                        <option value="users" ${this.reportData.base_entity === 'users' ? 'selected' : ''}>Users</option>
                    </select>
                    <p class="text-xs text-gray-500 mt-1">Select the primary data source for your report</p>
                </div>

                <div class="border-t pt-4">
                    <h4 class="font-medium mb-3">Filters</h4>
                    <div id="filter-builder">
                        <p class="text-sm text-gray-500 mb-2">Add filters to refine your data</p>
                        <button id="add-filter-btn" class="btn-sm btn-outline">
                            + Add Filter Condition
                        </button>
                        <div id="filter-conditions-list" class="mt-3 space-y-2">
                            <!-- Filter conditions will be rendered here -->
                        </div>
                    </div>
                </div>

                <div class="border-t pt-4">
                    <h4 class="font-medium mb-3">Sorting</h4>
                    <button id="add-sort-btn" class="btn-sm btn-outline">
                        + Add Sort Field
                    </button>
                    <div id="sort-fields-list" class="mt-3 space-y-2">
                        <!-- Sort fields will be rendered here -->
                    </div>
                </div>

                <div class="border-t pt-4">
                    <label class="block text-sm font-medium text-gray-700 mb-1">Result Limit (optional)</label>
                    <input type="number" id="query-limit" value="${this.reportData.query_config?.limit || ''}"
                        class="input-field" placeholder="Leave empty for no limit" min="1">
                </div>
            </div>
        `;
    }

    _renderColumnsStep() {
        return `
            <h3 class="text-xl font-bold mb-4">Column Configuration</h3>
            <div class="mb-4">
                <button id="add-column-btn" class="btn-primary btn-sm">
                    + Add Column
                </button>
            </div>
            <div id="columns-list" class="space-y-3">
                ${this.reportData.columns_config.map((col, idx) => this._renderColumnConfig(col, idx)).join('')}
            </div>
            ${this.reportData.columns_config.length === 0 ? `
                <div class="text-center py-8 text-gray-500">
                    <p>No columns configured yet. Add columns to display in your report.</p>
                </div>
            ` : ''}
        `;
    }

    _renderColumnConfig(column, index) {
        return `
            <div class="column-config border rounded p-4 bg-gray-50" data-index="${index}">
                <div class="grid grid-cols-3 gap-4">
                    <div>
                        <label class="block text-sm font-medium mb-1">Field Name</label>
                        <input type="text" class="input-field column-name" value="${column.name}"
                            placeholder="field_name">
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-1">Display Label</label>
                        <input type="text" class="input-field column-label" value="${column.label}"
                            placeholder="Display Label">
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-1">Aggregation</label>
                        <select class="input-field column-aggregation">
                            <option value="none" ${column.aggregation === 'none' ? 'selected' : ''}>None</option>
                            <option value="sum" ${column.aggregation === 'sum' ? 'selected' : ''}>SUM</option>
                            <option value="avg" ${column.aggregation === 'avg' ? 'selected' : ''}>AVG</option>
                            <option value="count" ${column.aggregation === 'count' ? 'selected' : ''}>COUNT</option>
                            <option value="min" ${column.aggregation === 'min' ? 'selected' : ''}>MIN</option>
                            <option value="max" ${column.aggregation === 'max' ? 'selected' : ''}>MAX</option>
                        </select>
                    </div>
                </div>
                <div class="flex justify-between items-center mt-3">
                    <div class="flex gap-4">
                        <label class="flex items-center text-sm">
                            <input type="checkbox" class="column-visible mr-1" ${column.visible ? 'checked' : ''}>
                            Visible
                        </label>
                        <label class="flex items-center text-sm">
                            <input type="checkbox" class="column-sortable mr-1" ${column.sortable ? 'checked' : ''}>
                            Sortable
                        </label>
                    </div>
                    <button class="text-red-600 hover:text-red-800 text-sm remove-column-btn">
                        🗑️ Remove
                    </button>
                </div>
            </div>
        `;
    }

    _renderParametersStep() {
        return `
            <h3 class="text-xl font-bold mb-4">Report Parameters</h3>
            <p class="text-gray-600 mb-4">Define parameters that users can provide when running the report</p>
            <div class="mb-4">
                <button id="add-parameter-btn" class="btn-primary btn-sm">
                    + Add Parameter
                </button>
            </div>
            <div id="parameters-list" class="space-y-4">
                ${this.reportData.parameters.map((param, idx) => this._renderParameterConfig(param, idx)).join('')}
            </div>
            ${this.reportData.parameters.length === 0 ? `
                <div class="text-center py-8 text-gray-500">
                    <p>No parameters defined. Parameters allow users to customize report output.</p>
                </div>
            ` : ''}
        `;
    }

    _renderParameterConfig(parameter, index) {
        return `
            <div class="parameter-config border rounded p-4 bg-gray-50" data-index="${index}">
                <div class="grid grid-cols-2 gap-4 mb-3">
                    <div>
                        <label class="block text-sm font-medium mb-1">Parameter Name</label>
                        <input type="text" class="input-field param-name" value="${parameter.name}"
                            placeholder="param_name">
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-1">Display Label</label>
                        <input type="text" class="input-field param-label" value="${parameter.label}"
                            placeholder="Display Label">
                    </div>
                </div>
                <div class="grid grid-cols-2 gap-4 mb-3">
                    <div>
                        <label class="block text-sm font-medium mb-1">Parameter Type</label>
                        <select class="input-field param-type">
                            <option value="string" ${parameter.parameter_type === 'string' ? 'selected' : ''}>String</option>
                            <option value="integer" ${parameter.parameter_type === 'integer' ? 'selected' : ''}>Integer</option>
                            <option value="decimal" ${parameter.parameter_type === 'decimal' ? 'selected' : ''}>Decimal</option>
                            <option value="date" ${parameter.parameter_type === 'date' ? 'selected' : ''}>Date</option>
                            <option value="datetime" ${parameter.parameter_type === 'datetime' ? 'selected' : ''}>Date Time</option>
                            <option value="boolean" ${parameter.parameter_type === 'boolean' ? 'selected' : ''}>Boolean</option>
                            <option value="lookup" ${parameter.parameter_type === 'lookup' ? 'selected' : ''}>Lookup (from table)</option>
                            <option value="multi_select" ${parameter.parameter_type === 'multi_select' ? 'selected' : ''}>Multi-Select</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-1">Default Value</label>
                        <input type="text" class="input-field param-default" value="${parameter.default_value || ''}"
                            placeholder="Optional default">
                    </div>
                </div>
                ${parameter.parameter_type === 'lookup' || parameter.parameter_type === 'multi_select' ? `
                    <div class="lookup-config border-t pt-3 mt-3">
                        <h5 class="font-medium mb-2">Lookup Configuration</h5>
                        <div class="grid grid-cols-3 gap-3">
                            <div>
                                <label class="block text-xs mb-1">Entity/Table</label>
                                <input type="text" class="input-field text-sm param-lookup-entity"
                                    value="${parameter.lookup_config?.entity || ''}" placeholder="companies">
                            </div>
                            <div>
                                <label class="block text-xs mb-1">Display Field</label>
                                <input type="text" class="input-field text-sm param-lookup-display"
                                    value="${parameter.lookup_config?.display_field || ''}" placeholder="name">
                            </div>
                            <div>
                                <label class="block text-xs mb-1">Value Field</label>
                                <input type="text" class="input-field text-sm param-lookup-value"
                                    value="${parameter.lookup_config?.value_field || ''}" placeholder="id">
                            </div>
                        </div>
                    </div>
                ` : ''}
                <div class="flex justify-between items-center mt-3">
                    <label class="flex items-center text-sm">
                        <input type="checkbox" class="param-required mr-1" ${parameter.required ? 'checked' : ''}>
                        Required Parameter
                    </label>
                    <button class="text-red-600 hover:text-red-800 text-sm remove-parameter-btn">
                        🗑️ Remove
                    </button>
                </div>
            </div>
        `;
    }

    _renderFormattingStep() {
        return `
            <h3 class="text-xl font-bold mb-4">Formatting & Appearance</h3>
            <p class="text-gray-600 mb-4">Configure conditional formatting and visual styling</p>

            <div class="space-y-6">
                <div class="border-t pt-4">
                    <h4 class="font-medium mb-3">Conditional Formatting Rules</h4>
                    <button id="add-formatting-rule-btn" class="btn-sm btn-outline">
                        + Add Formatting Rule
                    </button>
                    <div id="formatting-rules-list" class="mt-3 space-y-3">
                        ${this.reportData.formatting_rules.map((rule, idx) => this._renderFormattingRule(rule, idx)).join('')}
                    </div>
                    ${this.reportData.formatting_rules.length === 0 ? `
                        <div class="text-center py-6 text-gray-500 text-sm">
                            <p>No formatting rules defined yet</p>
                        </div>
                    ` : ''}
                </div>

                <div class="border-t pt-4">
                    <h4 class="font-medium mb-3">Export Formats</h4>
                    <p class="text-sm text-gray-600 mb-2">This report can be exported to the following formats:</p>
                    <div class="grid grid-cols-3 gap-3">
                        <div class="flex items-center p-3 border rounded bg-green-50">
                            <span class="mr-2">📄</span>
                            <span class="text-sm">PDF</span>
                        </div>
                        <div class="flex items-center p-3 border rounded bg-green-50">
                            <span class="mr-2">📊</span>
                            <span class="text-sm">Excel (Formatted)</span>
                        </div>
                        <div class="flex items-center p-3 border rounded bg-green-50">
                            <span class="mr-2">📋</span>
                            <span class="text-sm">Excel (Raw Data)</span>
                        </div>
                        <div class="flex items-center p-3 border rounded bg-green-50">
                            <span class="mr-2">📝</span>
                            <span class="text-sm">CSV</span>
                        </div>
                        <div class="flex items-center p-3 border rounded bg-green-50">
                            <span class="mr-2">🌐</span>
                            <span class="text-sm">HTML</span>
                        </div>
                        <div class="flex items-center p-3 border rounded bg-green-50">
                            <span class="mr-2">{ }</span>
                            <span class="text-sm">JSON</span>
                        </div>
                    </div>
                </div>

                <div class="border-t pt-4 mt-4">
                    <h4 class="font-medium mb-3">Report Summary</h4>
                    <div class="bg-blue-50 p-4 rounded">
                        <p class="text-sm"><strong>Report Name:</strong> ${this.reportData.name || 'Not set'}</p>
                        <p class="text-sm mt-1"><strong>Base Entity:</strong> ${this.reportData.base_entity || 'Not set'}</p>
                        <p class="text-sm mt-1"><strong>Columns:</strong> ${this.reportData.columns_config.length}</p>
                        <p class="text-sm mt-1"><strong>Parameters:</strong> ${this.reportData.parameters.length}</p>
                        <p class="text-sm mt-1"><strong>Visibility:</strong> ${this.reportData.is_public ? 'Public' : 'Private'}</p>
                    </div>
                </div>
            </div>
        `;
    }

    _renderFormattingRule(rule, index) {
        return `
            <div class="formatting-rule border rounded p-3 bg-white" data-index="${index}">
                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="block text-xs font-medium mb-1">Condition</label>
                        <input type="text" class="input-field text-sm rule-condition" value="${rule.condition}"
                            placeholder="e.g., value > 100">
                    </div>
                    <div>
                        <label class="block text-xs font-medium mb-1">Applies To Columns</label>
                        <input type="text" class="input-field text-sm rule-applies-to"
                            value="${rule.applies_to.join(', ')}"
                            placeholder="column1, column2">
                    </div>
                </div>
                <div class="flex justify-between items-center mt-2">
                    <div class="text-xs text-gray-600">
                        Style: <code class="bg-gray-100 px-2 py-1 rounded">${JSON.stringify(rule.style)}</code>
                    </div>
                    <button class="text-red-600 hover:text-red-800 text-sm remove-rule-btn">
                        🗑️ Remove
                    </button>
                </div>
            </div>
        `;
    }

    async loadReport() {
        try {
            const loadedData = await reportService.getReportDefinition(this.reportId);

            // Merge with defaults to ensure all required properties exist
            this.reportData = {
                ...this._getDefaultReportData(),
                ...loadedData,
                // Ensure nested objects are properly merged
                query_config: {
                    ...this._getDefaultReportData().query_config,
                    ...(loadedData.query_config || {})
                },
                columns_config: loadedData.columns_config || [],
                parameters: loadedData.parameters || [],
                formatting_rules: loadedData.formatting_rules || [],
                allowed_roles: loadedData.allowed_roles || [],
                allowed_users: loadedData.allowed_users || []
            };
        } catch (error) {
            showNotification('Failed to load report: ' + error.message, 'error');
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
            btnSave.addEventListener('click', () => this._saveReport());
        }
        if (btnPreview) {
            btnPreview.addEventListener('click', () => this._previewReport());
        }
    }

    _attachStepEventListeners() {
        // Step 1: Basic Info
        const reportName = document.getElementById('report-name');
        if (reportName) {
            reportName.addEventListener('change', (e) => {
                this.reportData.name = e.target.value;
            });
        }

        // Step 3: Columns
        const addColumnBtn = document.getElementById('add-column-btn');
        if (addColumnBtn) {
            addColumnBtn.addEventListener('click', () => this._addColumn());
        }

        // Step 4: Parameters
        const addParameterBtn = document.getElementById('add-parameter-btn');
        if (addParameterBtn) {
            addParameterBtn.addEventListener('click', () => this._addParameter());
        }

        // Step 5: Formatting
        const addFormattingRuleBtn = document.getElementById('add-formatting-rule-btn');
        if (addFormattingRuleBtn) {
            addFormattingRuleBtn.addEventListener('click', () => this._addFormattingRule());
        }
    }

    _addColumn() {
        const newColumn = {
            name: '',
            label: '',
            data_type: 'string',
            visible: true,
            sortable: true,
            filterable: true,
            aggregation: 'none',
            order: this.reportData.columns_config.length
        };
        this.reportData.columns_config.push(newColumn);
        this._renderCurrentStep();
    }

    _addParameter() {
        const newParameter = {
            name: '',
            label: '',
            parameter_type: 'string',
            required: false,
            default_value: null,
            order: this.reportData.parameters.length
        };
        this.reportData.parameters.push(newParameter);
        this._renderCurrentStep();
    }

    _addFormattingRule() {
        const newRule = {
            condition: '',
            style: { 'font-weight': 'bold' },
            applies_to: []
        };
        this.reportData.formatting_rules.push(newRule);
        this._renderCurrentStep();
    }

    _collectStepData() {
        // Collect data from current step before moving to next
        switch (this.currentStep) {
            case 1:
                this.reportData.name = document.getElementById('report-name')?.value || '';
                this.reportData.description = document.getElementById('report-description')?.value || '';
                this.reportData.category = document.getElementById('report-category')?.value || '';
                this.reportData.report_type = document.getElementById('report-type')?.value || 'tabular';
                this.reportData.is_public = document.getElementById('report-public')?.checked || false;
                break;
            case 2:
                this.reportData.base_entity = document.getElementById('base-entity')?.value || '';
                this.reportData.query_config.limit = parseInt(document.getElementById('query-limit')?.value) || null;
                break;
            // Add more cases as needed
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
        // Add validation logic for each step
        if (this.currentStep === 1) {
            if (!this.reportData.name) {
                showNotification('Report name is required', 'error');
                return false;
            }
        }
        if (this.currentStep === 2) {
            if (!this.reportData.base_entity) {
                showNotification('Base entity is required', 'error');
                return false;
            }
        }
        return true;
    }

    async _saveReport() {
        this._collectStepData();

        try {
            if (this.reportId) {
                await reportService.updateReportDefinition(this.reportId, this.reportData);
                showNotification('Report updated successfully!', 'success');
            } else {
                const result = await reportService.createReportDefinition(this.reportData);
                this.reportId = result.id;
                showNotification('Report created successfully!', 'success');
            }
            // Redirect to reports list or viewer
            setTimeout(() => {
                window.location.hash = '#/reports';
            }, 1500);
        } catch (error) {
            showNotification('Failed to save report: ' + error.message, 'error');
        }
    }

    async _previewReport() {
        showNotification('Preview functionality coming soon', 'info');
    }
}
