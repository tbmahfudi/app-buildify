/**
 * Visual Chart Builder Component
 *
 * Interactive chart type selector with live preview for report visualizations.
 * Chart types are grouped by category following industry-standard report tools
 * (Metabase, Tableau, Power BI, Jasper).
 */

import { showNotification } from '../assets/js/notifications.js';
import { upgradeAllSelects, setFlexValue } from '../assets/js/utils/upgrade-select.js';

const CHART_CATEGORIES = [
    {
        label: 'Comparison',
        charts: [
            { id: 'bar',            name: 'Bar',            icon: 'ph-chart-bar',             description: 'Compare values across categories' },
            { id: 'bar_horizontal', name: 'Horizontal Bar',  icon: 'ph-chart-bar-horizontal',  description: 'Long category labels, many items' },
            { id: 'bar_stacked',    name: 'Stacked Bar',     icon: 'ph-stack',                 description: 'Part-to-whole across categories' },
            { id: 'bar_grouped',    name: 'Grouped Bar',     icon: 'ph-chart-bar',             description: 'Multiple series side-by-side' },
            { id: 'combo',          name: 'Combo',           icon: 'ph-intersect',             description: 'Bar + line on dual axes' },
        ]
    },
    {
        label: 'Trend',
        charts: [
            { id: 'line',         name: 'Line',         icon: 'ph-chart-line',    description: 'Show trends over time' },
            { id: 'area',         name: 'Area',         icon: 'ph-chart-line-up', description: 'Volume below the trend line' },
            { id: 'area_stacked', name: 'Stacked Area', icon: 'ph-chart-line-up', description: 'Cumulative totals over time' },
        ]
    },
    {
        label: 'Composition',
        charts: [
            { id: 'pie',       name: 'Pie',       icon: 'ph-chart-pie-slice', description: 'Part-to-whole proportions' },
            { id: 'donut',     name: 'Donut',     icon: 'ph-chart-donut',     description: 'Proportions with center space' },
            { id: 'waterfall', name: 'Waterfall', icon: 'ph-steps',           description: 'Incremental changes to a total' },
            { id: 'funnel',    name: 'Funnel',    icon: 'ph-funnel',          description: 'Conversion / pipeline stages' },
        ]
    },
    {
        label: 'Distribution',
        charts: [
            { id: 'scatter', name: 'Scatter',  icon: 'ph-chart-scatter', description: 'Correlation between two measures' },
            { id: 'bubble',  name: 'Bubble',   icon: 'ph-circles-three', description: 'Three-measure scatter (size = 3rd)' },
            { id: 'heatmap', name: 'Heatmap',  icon: 'ph-grid-four',     description: 'Value intensity across a matrix' },
        ]
    },
    {
        label: 'KPI / Metric',
        charts: [
            { id: 'gauge',       name: 'Gauge',       icon: 'ph-gauge',       description: 'Single value vs. a target range' },
            { id: 'metric_card', name: 'Metric Card', icon: 'ph-number-square-one', description: 'Large single-number KPI display' },
        ]
    },
];

export class VisualChartBuilder {
    constructor(container, options = {}) {
        this.container = container;
        this.options = options;
        this.selectedChart = null;
        this.chartConfig = {};
        this.columns = options.columns || [];           // [{name, label}] from DragDropColumnDesigner
        this.onChartChange = options.onChartChange || (() => {});

        this.init();
    }

    init() {
        this.render();
    }

    // Called by the designer when column selection changes
    setColumns(columns) {
        this.columns = columns || [];
        // Re-render only the config panel so axis dropdowns reflect the new columns
        const configEl = this.container.querySelector('#chart-config');
        if (configEl) {
            configEl.innerHTML = this.renderChartConfig();
            upgradeAllSelects(configEl);
            this._attachConfigListeners();
        }
    }

    render() {
        this.container.innerHTML = `
            <div class="visual-chart-builder">
                <div class="mb-4">
                    <h3 class="text-lg font-semibold text-gray-900 mb-1">Select Chart Type</h3>
                    <p class="text-sm text-gray-500">Choose how you want to visualize your data</p>
                </div>

                ${CHART_CATEGORIES.map(cat => `
                    <div class="mb-5">
                        <h4 class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">${cat.label}</h4>
                        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2">
                            ${cat.charts.map(chart => `
                                <div
                                    class="chart-type-card p-3 border-2 rounded-lg cursor-pointer transition-all hover:border-blue-500 hover:shadow-sm ${this.selectedChart === chart.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200'}"
                                    data-chart="${chart.id}"
                                    title="${chart.description}"
                                >
                                    <div class="text-center">
                                        <i class="ph-duotone ${chart.icon} text-3xl ${this.selectedChart === chart.id ? 'text-blue-600' : 'text-gray-400'} mb-1"></i>
                                        <div class="font-medium text-gray-800 text-xs leading-tight">${chart.name}</div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `).join('')}

                <!-- Chart Configuration -->
                <div id="chart-config" class="mt-4">
                    ${this.renderChartConfig()}
                </div>
            </div>
        `;

        upgradeAllSelects(this.container);
        this._attachCardListeners();
        this._attachConfigListeners();
    }

    renderChartConfig() {
        if (!this.selectedChart) {
            return '<p class="text-sm text-gray-400 italic">Select a chart type above to configure axes and options.</p>';
        }

        const colOptions = this._columnOptions();
        const needsXY   = !['gauge', 'metric_card'].includes(this.selectedChart);
        const needsSize = this.selectedChart === 'bubble';

        return `
            <div class="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-4">
                <h4 class="font-semibold text-gray-900 text-sm">Chart Configuration
                    <span class="ml-2 text-xs font-normal text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full">${this.selectedChart}</span>
                </h4>

                ${needsXY ? `
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label class="block text-xs font-medium text-gray-600 mb-1">X-Axis / Category</label>
                        <select id="chart-x-axis" class="form-select w-full text-sm">
                            <option value="">— select field —</option>
                            ${colOptions}
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-gray-600 mb-1">Y-Axis / Measure(s)</label>
                        <select id="chart-y-axis" class="form-select w-full text-sm" ${this.selectedChart === 'combo' ? 'multiple' : ''}>
                            <option value="">— select field —</option>
                            ${colOptions}
                        </select>
                    </div>
                    ${this.selectedChart === 'combo' ? `
                    <div>
                        <label class="block text-xs font-medium text-gray-600 mb-1">Secondary Y-Axis (Line)</label>
                        <select id="chart-y-secondary" class="form-select w-full text-sm">
                            <option value="">— select field —</option>
                            ${colOptions}
                        </select>
                    </div>` : ''}
                    <div>
                        <label class="block text-xs font-medium text-gray-600 mb-1">Group By / Series</label>
                        <select id="chart-group-by" class="form-select w-full text-sm">
                            <option value="">— none —</option>
                            ${colOptions}
                        </select>
                    </div>
                    ${needsSize ? `
                    <div>
                        <label class="block text-xs font-medium text-gray-600 mb-1">Bubble Size Field</label>
                        <select id="chart-bubble-size" class="form-select w-full text-sm">
                            <option value="">— select field —</option>
                            ${colOptions}
                        </select>
                    </div>` : ''}
                </div>` : ''}

                <hr class="border-gray-200" />

                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label class="block text-xs font-medium text-gray-600 mb-1">Chart Title</label>
                        <input type="text" id="chart-title" class="form-input w-full text-sm"
                            value="${this._escape(this.chartConfig.title || '')}"
                            placeholder="Leave blank to use report title" />
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-gray-600 mb-1">Color Scheme</label>
                        <select id="chart-colors" class="form-select w-full text-sm">
                            <option value="default"  ${this._sel('default')}>Default</option>
                            <option value="blue"     ${this._sel('blue')}>Blue</option>
                            <option value="green"    ${this._sel('green')}>Green</option>
                            <option value="purple"   ${this._sel('purple')}>Purple</option>
                            <option value="rainbow"  ${this._sel('rainbow')}>Rainbow</option>
                            <option value="monochrome" ${this._sel('monochrome')}>Monochrome</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-gray-600 mb-1">Sort Order</label>
                        <select id="chart-sort" class="form-select w-full text-sm">
                            <option value=""    ${this._sel2('sort_order', '')}>None</option>
                            <option value="asc" ${this._sel2('sort_order', 'asc')}>Ascending</option>
                            <option value="desc" ${this._sel2('sort_order', 'desc')}>Descending</option>
                        </select>
                    </div>
                    <div class="flex items-center gap-4 pt-4">
                        <label class="flex items-center gap-2 text-xs text-gray-600 cursor-pointer">
                            <input type="checkbox" id="chart-legend" class="checkbox"
                                ${this.chartConfig.show_legend !== false ? 'checked' : ''} />
                            Show Legend
                        </label>
                        <label class="flex items-center gap-2 text-xs text-gray-600 cursor-pointer">
                            <input type="checkbox" id="chart-data-labels" class="checkbox"
                                ${this.chartConfig.show_data_labels ? 'checked' : ''} />
                            Data Labels
                        </label>
                    </div>
                </div>
            </div>
        `;
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    _columnOptions() {
        return this.columns.map(c => {
            const val   = c.name  || c.field || '';
            const label = c.label || c.alias || c.name || val;
            return `<option value="${this._escape(val)}">${this._escape(label)}</option>`;
        }).join('');
    }

    _sel(val) {
        return (this.chartConfig.color_scheme || 'default') === val ? 'selected' : '';
    }

    _sel2(key, val) {
        return (this.chartConfig[key] || '') === val ? 'selected' : '';
    }

    _escape(str) {
        return String(str || '').replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    }

    _setSelectValue(id, value) {
        if (value == null) return;
        // After upgradeAllSelects the <select> is replaced by a hidden input;
        // use setFlexValue so the FlexSelect display updates correctly too.
        setFlexValue(id, value);
    }

    // ── Event wiring ──────────────────────────────────────────────────────────

    _attachCardListeners() {
        this.container.querySelectorAll('.chart-type-card').forEach(card => {
            card.addEventListener('click', () => this.selectChart(card.dataset.chart));
        });
    }

    _attachConfigListeners() {
        const on = (id, event, fn) => {
            this.container.querySelector(`#${id}`)?.addEventListener(event, fn);
        };

        // Restore current values into dropdowns (after re-render)
        this._setSelectValue('chart-x-axis',     this.chartConfig.x_axis);
        this._setSelectValue('chart-y-axis',     Array.isArray(this.chartConfig.y_axis) ? this.chartConfig.y_axis[0] : this.chartConfig.y_axis);
        this._setSelectValue('chart-y-secondary',this.chartConfig.y_axis_secondary);
        this._setSelectValue('chart-group-by',   this.chartConfig.group_by);
        this._setSelectValue('chart-bubble-size',this.chartConfig.bubble_size_field);
        this._setSelectValue('chart-colors',     this.chartConfig.color_scheme || 'default');
        this._setSelectValue('chart-sort',       this.chartConfig.sort_order || '');

        on('chart-x-axis',      'change', e => { this.chartConfig.x_axis      = e.target.value || null; this._notify(); });
        on('chart-y-axis',      'change', e => { this.chartConfig.y_axis      = e.target.value ? [e.target.value] : null; this._notify(); });
        on('chart-y-secondary', 'change', e => { this.chartConfig.y_axis_secondary = e.target.value || null; this._notify(); });
        on('chart-group-by',    'change', e => { this.chartConfig.group_by    = e.target.value || null; this._notify(); });
        on('chart-bubble-size', 'change', e => { this.chartConfig.bubble_size_field = e.target.value || null; this._notify(); });
        on('chart-title',       'input',  e => { this.chartConfig.title       = e.target.value; this._notify(); });
        on('chart-colors',      'change', e => { this.chartConfig.color_scheme= e.target.value; this._notify(); });
        on('chart-sort',        'change', e => { this.chartConfig.sort_order  = e.target.value || null; this._notify(); });
        on('chart-legend',      'change', e => { this.chartConfig.show_legend = e.target.checked; this._notify(); });
        on('chart-data-labels', 'change', e => { this.chartConfig.show_data_labels = e.target.checked; this._notify(); });
    }

    // ── Public API ────────────────────────────────────────────────────────────

    selectChart(chartId) {
        this.selectedChart = chartId;
        this.chartConfig.chart_type = chartId;
        this.render();
        this._notify();
    }

    getChartConfig() {
        return {
            chart_type: this.selectedChart,
            ...this.chartConfig,
        };
    }

    setChartConfig(config) {
        this.selectedChart = config?.chart_type || config?.type || null;
        this.chartConfig   = config ? { ...config } : {};
        // Normalise legacy 'type' key
        if (this.chartConfig.type && !this.chartConfig.chart_type) {
            this.chartConfig.chart_type = this.chartConfig.type;
        }
        this.render();
    }

    clear() {
        this.setChartConfig({});
    }

    _notify() {
        this.onChartChange(this.getChartConfig());
    }
}
