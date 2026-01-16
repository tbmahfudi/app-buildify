/**
 * Visual Chart Builder Component
 *
 * Interactive chart type selector with live preview for report visualizations.
 */

import { showNotification } from '../assets/js/notifications.js';

export class VisualChartBuilder {
    constructor(container, options = {}) {
        this.container = container;
        this.options = options;
        this.selectedChart = null;
        this.chartConfig = {};
        this.onChartChange = options.onChartChange || (() => {});

        this.chartTypes = [
            { id: 'table', name: 'Table', icon: 'ph-table', description: 'Tabular data display' },
            { id: 'bar', name: 'Bar Chart', icon: 'ph-chart-bar', description: 'Compare values across categories' },
            { id: 'line', name: 'Line Chart', icon: 'ph-chart-line', description: 'Show trends over time' },
            { id: 'pie', name: 'Pie Chart', icon: 'ph-chart-pie-slice', description: 'Show proportions' },
            { id: 'donut', name: 'Donut Chart', icon: 'ph-chart-donut', description: 'Show proportions with center' },
            { id: 'area', name: 'Area Chart', icon: 'ph-chart-line-up', description: 'Show cumulative values' },
            { id: 'scatter', name: 'Scatter Plot', icon: 'ph-chart-scatter', description: 'Show correlations' },
            { id: 'heatmap', name: 'Heatmap', icon: 'ph-grid-four', description: 'Show data density' }
        ];

        this.init();
    }

    init() {
        this.render();
    }

    render() {
        this.container.innerHTML = `
            <div class="visual-chart-builder">
                <div class="mb-6">
                    <h3 class="text-lg font-semibold text-gray-900 mb-2">Select Chart Type</h3>
                    <p class="text-sm text-gray-600">Choose how you want to visualize your data</p>
                </div>

                <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    ${this.chartTypes.map(chart => `
                        <div
                            class="chart-type-card p-4 border-2 rounded-lg cursor-pointer transition-all hover:border-blue-500 hover:shadow-md ${this.selectedChart === chart.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200'}"
                            data-chart="${chart.id}"
                        >
                            <div class="text-center">
                                <i class="ph-duotone ${chart.icon} text-4xl text-blue-600 mb-2"></i>
                                <div class="font-medium text-gray-900 text-sm">${chart.name}</div>
                                <div class="text-xs text-gray-500 mt-1">${chart.description}</div>
                            </div>
                        </div>
                    `).join('')}
                </div>

                <!-- Chart Configuration -->
                <div id="chart-config" class="mt-6">
                    ${this.renderChartConfig()}
                </div>
            </div>
        `;

        this.attachEventListeners();
    }

    renderChartConfig() {
        if (!this.selectedChart) {
            return '<p class="text-sm text-gray-500">Select a chart type to configure</p>';
        }

        const commonConfig = `
            <div class="bg-white border border-gray-200 rounded-lg p-4 space-y-4">
                <h4 class="font-semibold text-gray-900">Chart Configuration</h4>

                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Title</label>
                    <input type="text" id="chart-title" class="form-input w-full" value="${this.chartConfig.title || ''}" placeholder="Chart title" />
                </div>

                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Show Legend</label>
                    <input type="checkbox" id="chart-legend" class="checkbox" ${this.chartConfig.showLegend !== false ? 'checked' : ''} />
                </div>

                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Color Scheme</label>
                    <select id="chart-colors" class="form-select w-full">
                        <option value="default">Default</option>
                        <option value="blue">Blue</option>
                        <option value="green">Green</option>
                        <option value="purple">Purple</option>
                        <option value="rainbow">Rainbow</option>
                    </select>
                </div>
            </div>
        `;

        return commonConfig;
    }

    attachEventListeners() {
        // Chart type selection
        document.querySelectorAll('.chart-type-card').forEach(card => {
            card.addEventListener('click', () => {
                const chartId = card.dataset.chart;
                this.selectChart(chartId);
            });
        });

        // Config changes
        document.getElementById('chart-title')?.addEventListener('change', (e) => {
            this.chartConfig.title = e.target.value;
            this.notifyChange();
        });

        document.getElementById('chart-legend')?.addEventListener('change', (e) => {
            this.chartConfig.showLegend = e.target.checked;
            this.notifyChange();
        });

        document.getElementById('chart-colors')?.addEventListener('change', (e) => {
            this.chartConfig.colorScheme = e.target.value;
            this.notifyChange();
        });
    }

    selectChart(chartId) {
        this.selectedChart = chartId;
        this.chartConfig.type = chartId;
        this.render();
        this.notifyChange();
    }

    getChartConfig() {
        return {
            type: this.selectedChart,
            ...this.chartConfig
        };
    }

    setChartConfig(config) {
        this.selectedChart = config?.type || null;
        this.chartConfig = config || {};
        this.render();
    }

    notifyChange() {
        this.onChartChange(this.getChartConfig());
    }
}
