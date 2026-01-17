/**
 * Enhanced Widget Configuration Component
 *
 * Visual configuration panels for widget properties.
 * Provides intuitive UI for configuring widget appearance and behavior.
 *
 * Features:
 * - Report selector with search/filter/preview
 * - Chart type visual picker
 * - Color scheme designer
 * - Spacing editor (padding, margin visual)
 * - Border and shadow designer
 * - Conditional formatting rules
 *
 * Usage:
 * const config = new EnhancedWidgetConfig(container, {
 *   widget: widgetData,
 *   onConfigChange: (config) => console.log('Config:', config)
 * });
 */

import { apiFetch } from '../assets/js/api.js';

export class EnhancedWidgetConfig {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        this.options = options;

        // State
        this.widget = options.widget || {};
        this.config = this.widget.config || {};
        this.reports = [];
        this.activePanel = 'general'; // general, data, appearance, advanced

        // Callbacks
        this.onConfigChange = options.onConfigChange || (() => {});

        // Color presets
        this.colorSchemes = [
            { name: 'Blue', colors: ['#3B82F6', '#60A5FA', '#93C5FD', '#BFDBFE'] },
            { name: 'Green', colors: ['#10B981', '#34D399', '#6EE7B7', '#A7F3D0'] },
            { name: 'Purple', colors: ['#8B5CF6', '#A78BFA', '#C4B5FD', '#DDD6FE'] },
            { name: 'Orange', colors: ['#F59E0B', '#FBBF24', '#FCD34D', '#FDE68A'] },
            { name: 'Red', colors: ['#EF4444', '#F87171', '#FCA5A5', '#FECACA'] },
            { name: 'Custom', colors: [] }
        ];

        this.init();
    }

    async init() {
        await this.loadReports();
        await this.render();
        this.attachEventListeners();
    }

    async loadReports() {
        try {
            const response = await apiFetch('/api/v1/reports');
            const data = await response.json();
            this.reports = data.reports || [];
        } catch (error) {
            console.error('Failed to load reports:', error);
            this.reports = [];
        }
    }

    async render() {
        this.container.innerHTML = `
            <div class="enhanced-widget-config bg-white h-full flex flex-col">
                <!-- Header -->
                <div class="config-header p-4 border-b border-gray-200">
                    <h3 class="text-sm font-semibold text-gray-900 mb-1">Widget Configuration</h3>
                    <p class="text-xs text-gray-500">${this.widget.title || 'Untitled Widget'}</p>
                </div>

                <!-- Panel Tabs -->
                <div class="config-tabs flex border-b border-gray-200 bg-gray-50">
                    ${this.renderPanelTabs()}
                </div>

                <!-- Panel Content -->
                <div class="config-content flex-1 overflow-y-auto p-4">
                    ${this.renderActivePanel()}
                </div>

                <!-- Footer -->
                <div class="config-footer p-4 border-t border-gray-200 flex justify-end space-x-2">
                    <button id="reset-config-btn" class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">
                        Reset
                    </button>
                    <button id="apply-config-btn" class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700">
                        Apply
                    </button>
                </div>
            </div>
        `;
    }

    renderPanelTabs() {
        const tabs = [
            { key: 'general', icon: 'ph-gear', label: 'General' },
            { key: 'data', icon: 'ph-database', label: 'Data' },
            { key: 'appearance', icon: 'ph-palette', label: 'Appearance' },
            { key: 'advanced', icon: 'ph-sliders', label: 'Advanced' }
        ];

        return tabs.map(tab => `
            <button class="panel-tab flex-1 px-4 py-3 text-xs font-medium transition-colors ${
                this.activePanel === tab.key
                    ? 'text-blue-600 border-b-2 border-blue-600 bg-white'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }" data-panel="${tab.key}">
                <i class="${tab.icon} mr-1"></i>
                ${tab.label}
            </button>
        `).join('');
    }

    renderActivePanel() {
        switch (this.activePanel) {
            case 'general':
                return this.renderGeneralPanel();
            case 'data':
                return this.renderDataPanel();
            case 'appearance':
                return this.renderAppearancePanel();
            case 'advanced':
                return this.renderAdvancedPanel();
            default:
                return '';
        }
    }

    renderGeneralPanel() {
        return `
            <div class="general-panel space-y-4">
                <!-- Widget Title -->
                <div class="form-group">
                    <label class="block text-sm font-medium text-gray-700 mb-2">Widget Title</label>
                    <input type="text" id="widget-title" value="${this.widget.title || ''}"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="Enter widget title">
                </div>

                <!-- Widget Type -->
                <div class="form-group">
                    <label class="block text-sm font-medium text-gray-700 mb-2">Widget Type</label>
                    <select id="widget-type" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                        ${this.renderWidgetTypeOptions()}
                    </select>
                </div>

                <!-- Description -->
                <div class="form-group">
                    <label class="block text-sm font-medium text-gray-700 mb-2">Description</label>
                    <textarea id="widget-description" rows="3"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="Optional description">${this.config.description || ''}</textarea>
                </div>

                <!-- Visibility -->
                <div class="form-group">
                    <label class="flex items-center">
                        <input type="checkbox" id="widget-visible" ${this.config.visible !== false ? 'checked' : ''}
                            class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500">
                        <span class="ml-2 text-sm text-gray-700">Show widget</span>
                    </label>
                </div>
            </div>
        `;
    }

    renderWidgetTypeOptions() {
        const types = [
            { group: 'Charts', options: ['Bar Chart', 'Line Chart', 'Pie Chart', 'Donut Chart', 'Area Chart'] },
            { group: 'Metrics', options: ['KPI Card', 'Gauge', 'Progress Bar', 'Stat Card'] },
            { group: 'Tables', options: ['Data Grid', 'Summary Table'] },
            { group: 'Other', options: ['Text', 'Image', 'Button'] }
        ];

        return types.map(group => `
            <optgroup label="${group.group}">
                ${group.options.map(opt => `
                    <option value="${opt.toLowerCase().replace(/\s+/g, '-')}" ${this.widget.type === opt.toLowerCase().replace(/\s+/g, '-') ? 'selected' : ''}>
                        ${opt}
                    </option>
                `).join('')}
            </optgroup>
        `).join('');
    }

    renderDataPanel() {
        return `
            <div class="data-panel space-y-4">
                <!-- Report Selector -->
                <div class="form-group">
                    <label class="block text-sm font-medium text-gray-700 mb-2">Data Source</label>

                    <!-- Report Search -->
                    <div class="relative mb-2">
                        <i class="ph ph-magnifying-glass absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"></i>
                        <input type="text" id="report-search"
                            class="w-full pl-10 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                            placeholder="Search reports...">
                    </div>

                    <!-- Report List -->
                    <div class="report-list max-h-64 overflow-y-auto border border-gray-300 rounded-lg">
                        ${this.reports.length > 0 ? this.reports.map(report => `
                            <div class="report-item flex items-center justify-between p-3 hover:bg-gray-50 cursor-pointer border-b last:border-b-0 ${
                                this.config.reportId === report.id ? 'bg-blue-50' : ''
                            }" data-report-id="${report.id}">
                                <div class="flex-1">
                                    <div class="text-sm font-medium text-gray-900">${report.name}</div>
                                    <div class="text-xs text-gray-500">${report.report_type || 'Unknown type'}</div>
                                </div>
                                <button class="preview-report-btn text-blue-600 hover:text-blue-700" data-report-id="${report.id}">
                                    <i class="ph ph-eye"></i>
                                </button>
                            </div>
                        `).join('') : '<div class="p-4 text-sm text-gray-500 text-center">No reports found</div>'}
                    </div>
                </div>

                <!-- Refresh Rate -->
                <div class="form-group">
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        Refresh Rate
                        <span class="text-xs text-gray-500 ml-1">(seconds)</span>
                    </label>
                    <div class="flex items-center space-x-2">
                        <input type="range" id="refresh-rate" min="0" max="300" step="10" value="${this.config.refreshRate || 30}"
                            class="flex-1">
                        <span class="refresh-rate-value text-sm font-medium text-gray-900 min-w-[40px]">${this.config.refreshRate || 30}s</span>
                    </div>
                    <div class="flex justify-between text-xs text-gray-500 mt-1">
                        <span>Off</span>
                        <span>5 min</span>
                    </div>
                </div>

                <!-- Auto-refresh Toggle -->
                <div class="form-group">
                    <label class="flex items-center">
                        <input type="checkbox" id="auto-refresh" ${this.config.autoRefresh ? 'checked' : ''}
                            class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500">
                        <span class="ml-2 text-sm text-gray-700">Enable auto-refresh</span>
                    </label>
                </div>
            </div>
        `;
    }

    renderAppearancePanel() {
        return `
            <div class="appearance-panel space-y-6">
                <!-- Color Scheme -->
                <div class="form-group">
                    <label class="block text-sm font-medium text-gray-700 mb-3">Color Scheme</label>
                    <div class="color-schemes grid grid-cols-2 gap-2">
                        ${this.colorSchemes.map(scheme => `
                            <div class="color-scheme-card border-2 ${
                                this.config.colorScheme === scheme.name ? 'border-blue-500' : 'border-gray-200'
                            } rounded-lg p-3 cursor-pointer hover:border-blue-300 transition-colors" data-scheme="${scheme.name}">
                                <div class="text-xs font-medium text-gray-700 mb-2">${scheme.name}</div>
                                ${scheme.colors.length > 0 ? `
                                    <div class="flex space-x-1">
                                        ${scheme.colors.map(color => `
                                            <div class="w-8 h-8 rounded" style="background-color: ${color};"></div>
                                        `).join('')}
                                    </div>
                                ` : `
                                    <div class="flex items-center justify-center h-8 bg-gray-100 rounded">
                                        <i class="ph ph-palette text-gray-400"></i>
                                    </div>
                                `}
                            </div>
                        `).join('')}
                    </div>
                </div>

                <!-- Spacing Editor -->
                <div class="form-group">
                    <label class="block text-sm font-medium text-gray-700 mb-3">Spacing</label>

                    <!-- Visual Spacing Editor -->
                    <div class="spacing-editor border border-gray-300 rounded-lg p-4 bg-gray-50">
                        <div class="spacing-preview relative bg-blue-100 rounded p-4">
                            <!-- Margin -->
                            <div class="margin-box absolute inset-0 border-2 border-dashed border-orange-400 rounded">
                                <div class="absolute -top-5 left-1/2 -translate-x-1/2 text-xs text-orange-600">
                                    Margin: <span id="margin-display">${this.config.margin || 0}px</span>
                                </div>
                            </div>

                            <!-- Padding -->
                            <div class="padding-box bg-green-100 rounded p-4 relative">
                                <div class="absolute -top-5 left-1/2 -translate-x-1/2 text-xs text-green-600">
                                    Padding: <span id="padding-display">${this.config.padding || 16}px</span>
                                </div>

                                <!-- Content -->
                                <div class="content-box bg-white rounded p-3 text-center text-xs text-gray-500">
                                    Widget Content
                                </div>
                            </div>
                        </div>

                        <!-- Controls -->
                        <div class="spacing-controls mt-4 space-y-2">
                            <div class="flex items-center space-x-2">
                                <label class="text-xs text-gray-600 w-16">Margin:</label>
                                <input type="range" id="margin-slider" min="0" max="32" step="4" value="${this.config.margin || 0}"
                                    class="flex-1">
                            </div>
                            <div class="flex items-center space-x-2">
                                <label class="text-xs text-gray-600 w-16">Padding:</label>
                                <input type="range" id="padding-slider" min="0" max="48" step="4" value="${this.config.padding || 16}"
                                    class="flex-1">
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Border & Shadow -->
                <div class="form-group">
                    <label class="block text-sm font-medium text-gray-700 mb-3">Border & Shadow</label>

                    <div class="space-y-3">
                        <!-- Border Width -->
                        <div class="flex items-center space-x-2">
                            <label class="text-xs text-gray-600 w-24">Border:</label>
                            <input type="range" id="border-width" min="0" max="8" step="1" value="${this.config.borderWidth || 1}"
                                class="flex-1">
                            <span class="text-xs font-medium text-gray-900 min-w-[40px]">${this.config.borderWidth || 1}px</span>
                        </div>

                        <!-- Border Color -->
                        <div class="flex items-center space-x-2">
                            <label class="text-xs text-gray-600 w-24">Border Color:</label>
                            <input type="color" id="border-color" value="${this.config.borderColor || '#e5e7eb'}"
                                class="h-8 w-12 rounded cursor-pointer">
                            <input type="text" id="border-color-text" value="${this.config.borderColor || '#e5e7eb'}"
                                class="flex-1 px-2 py-1 text-xs border border-gray-300 rounded">
                        </div>

                        <!-- Border Radius -->
                        <div class="flex items-center space-x-2">
                            <label class="text-xs text-gray-600 w-24">Radius:</label>
                            <input type="range" id="border-radius" min="0" max="24" step="2" value="${this.config.borderRadius || 8}"
                                class="flex-1">
                            <span class="text-xs font-medium text-gray-900 min-w-[40px]">${this.config.borderRadius || 8}px</span>
                        </div>

                        <!-- Shadow -->
                        <div class="flex items-center space-x-2">
                            <label class="text-xs text-gray-600 w-24">Shadow:</label>
                            <select id="shadow-size" class="flex-1 px-2 py-1 text-xs border border-gray-300 rounded">
                                <option value="none" ${!this.config.shadow || this.config.shadow === 'none' ? 'selected' : ''}>None</option>
                                <option value="sm" ${this.config.shadow === 'sm' ? 'selected' : ''}>Small</option>
                                <option value="md" ${this.config.shadow === 'md' ? 'selected' : ''}>Medium</option>
                                <option value="lg" ${this.config.shadow === 'lg' ? 'selected' : ''}>Large</option>
                                <option value="xl" ${this.config.shadow === 'xl' ? 'selected' : ''}>Extra Large</option>
                            </select>
                        </div>

                        <!-- Preview Box -->
                        <div class="mt-4 p-4 bg-gray-50 rounded">
                            <div id="border-shadow-preview" class="bg-white p-4 text-center text-sm text-gray-600"
                                style="border: ${this.config.borderWidth || 1}px solid ${this.config.borderColor || '#e5e7eb'};
                                       border-radius: ${this.config.borderRadius || 8}px;
                                       box-shadow: ${this.getShadowValue(this.config.shadow)};">
                                Preview
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderAdvancedPanel() {
        return `
            <div class="advanced-panel space-y-4">
                <!-- Conditional Formatting -->
                <div class="form-group">
                    <label class="block text-sm font-medium text-gray-700 mb-3">Conditional Formatting</label>

                    <div class="conditional-rules space-y-2">
                        ${(this.config.conditionalRules || []).map((rule, index) => this.renderConditionalRule(rule, index)).join('')}
                    </div>

                    <button id="add-rule-btn" class="mt-2 px-3 py-1.5 text-xs font-medium text-blue-600 bg-blue-50 rounded-lg hover:bg-blue-100">
                        <i class="ph ph-plus mr-1"></i>
                        Add Rule
                    </button>
                </div>

                <!-- Custom CSS -->
                <div class="form-group">
                    <label class="block text-sm font-medium text-gray-700 mb-2">Custom CSS Class</label>
                    <input type="text" id="custom-css-class" value="${this.config.customClass || ''}"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        placeholder="custom-widget-class">
                    <p class="text-xs text-gray-500 mt-1">Add custom CSS classes for styling</p>
                </div>

                <!-- Animation -->
                <div class="form-group">
                    <label class="block text-sm font-medium text-gray-700 mb-2">Entrance Animation</label>
                    <select id="animation" class="w-full px-3 py-2 border border-gray-300 rounded-lg">
                        <option value="none" ${!this.config.animation || this.config.animation === 'none' ? 'selected' : ''}>None</option>
                        <option value="fade" ${this.config.animation === 'fade' ? 'selected' : ''}>Fade In</option>
                        <option value="slide-up" ${this.config.animation === 'slide-up' ? 'selected' : ''}>Slide Up</option>
                        <option value="slide-down" ${this.config.animation === 'slide-down' ? 'selected' : ''}>Slide Down</option>
                        <option value="zoom" ${this.config.animation === 'zoom' ? 'selected' : ''}>Zoom</option>
                    </select>
                </div>

                <!-- Click Action -->
                <div class="form-group">
                    <label class="block text-sm font-medium text-gray-700 mb-2">Click Action</label>
                    <select id="click-action" class="w-full px-3 py-2 border border-gray-300 rounded-lg">
                        <option value="none" ${!this.config.clickAction || this.config.clickAction === 'none' ? 'selected' : ''}>None</option>
                        <option value="drill-down" ${this.config.clickAction === 'drill-down' ? 'selected' : ''}>Drill Down</option>
                        <option value="filter" ${this.config.clickAction === 'filter' ? 'selected' : ''}>Apply Filter</option>
                        <option value="navigate" ${this.config.clickAction === 'navigate' ? 'selected' : ''}>Navigate to URL</option>
                        <option value="modal" ${this.config.clickAction === 'modal' ? 'selected' : ''}>Open Modal</option>
                    </select>
                </div>

                <!-- Permissions -->
                <div class="form-group">
                    <label class="block text-sm font-medium text-gray-700 mb-2">Visibility Permissions</label>
                    <div class="space-y-2">
                        <label class="flex items-center">
                            <input type="checkbox" ${this.config.permissions?.admin !== false ? 'checked' : ''}
                                class="w-4 h-4 text-blue-600 border-gray-300 rounded">
                            <span class="ml-2 text-sm text-gray-700">Admin</span>
                        </label>
                        <label class="flex items-center">
                            <input type="checkbox" ${this.config.permissions?.manager !== false ? 'checked' : ''}
                                class="w-4 h-4 text-blue-600 border-gray-300 rounded">
                            <span class="ml-2 text-sm text-gray-700">Manager</span>
                        </label>
                        <label class="flex items-center">
                            <input type="checkbox" ${this.config.permissions?.user !== false ? 'checked' : ''}
                                class="w-4 h-4 text-blue-600 border-gray-300 rounded">
                            <span class="ml-2 text-sm text-gray-700">User</span>
                        </label>
                    </div>
                </div>
            </div>
        `;
    }

    renderConditionalRule(rule, index) {
        return `
            <div class="conditional-rule flex items-center space-x-2 p-2 bg-gray-50 rounded border border-gray-200" data-index="${index}">
                <select class="rule-field flex-1 px-2 py-1 text-xs border border-gray-300 rounded">
                    <option value="value">Value</option>
                    <option value="percentage">Percentage</option>
                    <option value="count">Count</option>
                </select>

                <select class="rule-operator px-2 py-1 text-xs border border-gray-300 rounded">
                    <option value=">">&gt;</option>
                    <option value="<">&lt;</option>
                    <option value="=">equals</option>
                    <option value="!=">not equals</option>
                </select>

                <input type="text" class="rule-value flex-1 px-2 py-1 text-xs border border-gray-300 rounded" placeholder="Value" value="${rule?.value || ''}">

                <input type="color" class="rule-color w-8 h-6 rounded cursor-pointer" value="${rule?.color || '#3B82F6'}">

                <button class="remove-rule-btn text-red-600 hover:text-red-700">
                    <i class="ph ph-trash text-sm"></i>
                </button>
            </div>
        `;
    }

    attachEventListeners() {
        const container = this.container;

        // Panel tabs
        container.querySelectorAll('.panel-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                this.activePanel = e.currentTarget.dataset.panel;
                this.render();
                this.attachEventListeners();
            });
        });

        // General panel
        this.attachGeneralListeners();

        // Data panel
        this.attachDataListeners();

        // Appearance panel
        this.attachAppearanceListeners();

        // Advanced panel
        this.attachAdvancedListeners();

        // Footer buttons
        const resetBtn = container.querySelector('#reset-config-btn');
        resetBtn?.addEventListener('click', () => this.resetConfig());

        const applyBtn = container.querySelector('#apply-config-btn');
        applyBtn?.addEventListener('click', () => this.applyConfig());
    }

    attachGeneralListeners() {
        const container = this.container;

        const titleInput = container.querySelector('#widget-title');
        titleInput?.addEventListener('input', (e) => {
            this.widget.title = e.target.value;
        });

        const typeSelect = container.querySelector('#widget-type');
        typeSelect?.addEventListener('change', (e) => {
            this.widget.type = e.target.value;
        });

        const descInput = container.querySelector('#widget-description');
        descInput?.addEventListener('input', (e) => {
            this.config.description = e.target.value;
        });

        const visibleCheck = container.querySelector('#widget-visible');
        visibleCheck?.addEventListener('change', (e) => {
            this.config.visible = e.target.checked;
        });
    }

    attachDataListeners() {
        const container = this.container;

        // Report search
        const searchInput = container.querySelector('#report-search');
        searchInput?.addEventListener('input', (e) => {
            this.filterReports(e.target.value);
        });

        // Report selection
        container.querySelectorAll('.report-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (e.target.closest('.preview-report-btn')) return;

                const reportId = parseInt(e.currentTarget.dataset.reportId);
                this.selectReport(reportId);
            });
        });

        // Report preview
        container.querySelectorAll('.preview-report-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const reportId = parseInt(e.currentTarget.dataset.reportId);
                this.previewReport(reportId);
            });
        });

        // Refresh rate
        const refreshSlider = container.querySelector('#refresh-rate');
        const refreshValue = container.querySelector('.refresh-rate-value');
        refreshSlider?.addEventListener('input', (e) => {
            this.config.refreshRate = parseInt(e.target.value);
            if (refreshValue) {
                refreshValue.textContent = `${this.config.refreshRate}s`;
            }
        });

        // Auto-refresh
        const autoRefreshCheck = container.querySelector('#auto-refresh');
        autoRefreshCheck?.addEventListener('change', (e) => {
            this.config.autoRefresh = e.target.checked;
        });
    }

    attachAppearanceListeners() {
        const container = this.container;

        // Color schemes
        container.querySelectorAll('.color-scheme-card').forEach(card => {
            card.addEventListener('click', (e) => {
                const scheme = e.currentTarget.dataset.scheme;
                this.config.colorScheme = scheme;
                this.render();
                this.attachEventListeners();
            });
        });

        // Spacing
        const marginSlider = container.querySelector('#margin-slider');
        const marginDisplay = container.querySelector('#margin-display');
        marginSlider?.addEventListener('input', (e) => {
            this.config.margin = parseInt(e.target.value);
            if (marginDisplay) {
                marginDisplay.textContent = `${this.config.margin}px`;
            }
        });

        const paddingSlider = container.querySelector('#padding-slider');
        const paddingDisplay = container.querySelector('#padding-display');
        paddingSlider?.addEventListener('input', (e) => {
            this.config.padding = parseInt(e.target.value);
            if (paddingDisplay) {
                paddingDisplay.textContent = `${this.config.padding}px`;
            }
        });

        // Border & Shadow
        const borderWidth = container.querySelector('#border-width');
        borderWidth?.addEventListener('input', (e) => {
            this.config.borderWidth = parseInt(e.target.value);
            this.updateBorderPreview();
        });

        const borderColor = container.querySelector('#border-color');
        const borderColorText = container.querySelector('#border-color-text');
        borderColor?.addEventListener('input', (e) => {
            this.config.borderColor = e.target.value;
            if (borderColorText) borderColorText.value = e.target.value;
            this.updateBorderPreview();
        });
        borderColorText?.addEventListener('input', (e) => {
            this.config.borderColor = e.target.value;
            if (borderColor) borderColor.value = e.target.value;
            this.updateBorderPreview();
        });

        const borderRadius = container.querySelector('#border-radius');
        borderRadius?.addEventListener('input', (e) => {
            this.config.borderRadius = parseInt(e.target.value);
            this.updateBorderPreview();
        });

        const shadowSize = container.querySelector('#shadow-size');
        shadowSize?.addEventListener('change', (e) => {
            this.config.shadow = e.target.value;
            this.updateBorderPreview();
        });
    }

    attachAdvancedListeners() {
        const container = this.container;

        // Add rule button
        const addRuleBtn = container.querySelector('#add-rule-btn');
        addRuleBtn?.addEventListener('click', () => {
            if (!this.config.conditionalRules) {
                this.config.conditionalRules = [];
            }
            this.config.conditionalRules.push({ field: 'value', operator: '>', value: '', color: '#3B82F6' });
            this.render();
            this.attachEventListeners();
        });

        // Remove rule buttons
        container.querySelectorAll('.remove-rule-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const ruleDiv = e.currentTarget.closest('.conditional-rule');
                const index = parseInt(ruleDiv.dataset.index);
                this.config.conditionalRules.splice(index, 1);
                this.render();
                this.attachEventListeners();
            });
        });

        // Custom CSS
        const customClass = container.querySelector('#custom-css-class');
        customClass?.addEventListener('input', (e) => {
            this.config.customClass = e.target.value;
        });

        // Animation
        const animation = container.querySelector('#animation');
        animation?.addEventListener('change', (e) => {
            this.config.animation = e.target.value;
        });

        // Click action
        const clickAction = container.querySelector('#click-action');
        clickAction?.addEventListener('change', (e) => {
            this.config.clickAction = e.target.value;
        });
    }

    updateBorderPreview() {
        const preview = this.container.querySelector('#border-shadow-preview');
        if (preview) {
            preview.style.border = `${this.config.borderWidth || 1}px solid ${this.config.borderColor || '#e5e7eb'}`;
            preview.style.borderRadius = `${this.config.borderRadius || 8}px`;
            preview.style.boxShadow = this.getShadowValue(this.config.shadow);
        }
    }

    getShadowValue(size) {
        const shadows = {
            none: 'none',
            sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
            md: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
            lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
            xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1)'
        };
        return shadows[size] || shadows.none;
    }

    filterReports(query) {
        const lowerQuery = query.toLowerCase();
        this.container.querySelectorAll('.report-item').forEach(item => {
            const name = item.querySelector('.text-sm').textContent.toLowerCase();
            const shouldShow = name.includes(lowerQuery);
            item.classList.toggle('hidden', !shouldShow);
        });
    }

    selectReport(reportId) {
        this.config.reportId = reportId;
        this.render();
        this.attachEventListeners();
    }

    previewReport(reportId) {
        // TODO: Open report preview modal
        console.log('Preview report:', reportId);
    }

    resetConfig() {
        this.config = {};
        this.widget.title = '';
        this.render();
        this.attachEventListeners();
    }

    applyConfig() {
        this.widget.config = this.config;
        this.onConfigChange(this.config);
    }

    // Public API
    updateWidget(widget) {
        this.widget = widget;
        this.config = widget.config || {};
        this.render();
        this.attachEventListeners();
    }

    getConfig() {
        return this.config;
    }

    getWidget() {
        return {
            ...this.widget,
            config: this.config
        };
    }
}
