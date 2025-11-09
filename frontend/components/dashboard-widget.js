/**
 * Dashboard Widget Component
 *
 * Reusable widget renderer that displays different types of widgets:
 * - Report Table (reuses report infrastructure)
 * - Charts (bar, line, pie, etc.)
 * - KPI Cards
 * - Text widgets
 * - Iframe embeds
 */

import { dashboardService } from '../assets/js/dashboard-service.js';
import { showNotification } from '../assets/js/notifications.js';

export class DashboardWidget {
    constructor(container, widgetConfig, globalParameters = {}) {
        this.container = container;
        this.widgetConfig = widgetConfig;
        this.globalParameters = globalParameters;
        this.data = null;
        this.refreshInterval = null;
    }

    async render() {
        const { widget_type, title, show_title, show_border, background_color } = this.widgetConfig;

        this.container.innerHTML = `
            <div class="dashboard-widget ${show_border ? 'border rounded shadow-sm' : ''}"
                 style="height: 100%; ${background_color ? `background-color: ${background_color};` : 'background: white;'}">
                ${show_title ? `
                    <div class="widget-header p-3 border-b flex justify-between items-center">
                        <h3 class="text-sm font-bold text-gray-800">${title}</h3>
                        <div class="widget-actions flex gap-2">
                            <button class="refresh-widget-btn text-gray-600 hover:text-gray-800" title="Refresh">
                                🔄
                            </button>
                        </div>
                    </div>
                ` : ''}
                <div class="widget-body p-4" id="widget-body-${this.widgetConfig.id}">
                    <div class="text-center py-8">
                        <div class="spinner mb-2"></div>
                        <p class="text-sm text-gray-500">Loading...</p>
                    </div>
                </div>
            </div>
        `;

        // Attach refresh event
        const refreshBtn = this.container.querySelector('.refresh-widget-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadData(false));
        }

        // Load data
        await this.loadData();

        // Setup auto-refresh if configured
        this._setupAutoRefresh();
    }

    async loadData(useCache = true) {
        const bodyContainer = document.getElementById(`widget-body-${this.widgetConfig.id}`);
        if (!bodyContainer) return;

        try {
            // Merge global parameters with widget-specific parameters
            const parameters = { ...this.globalParameters };

            // Fetch widget data (reuses report infrastructure on backend)
            const result = await dashboardService.getWidgetData(
                this.widgetConfig.id,
                parameters,
                useCache
            );

            this.data = result.data;

            // Render based on widget type
            await this._renderWidgetContent(bodyContainer);

        } catch (error) {
            bodyContainer.innerHTML = `
                <div class="bg-red-50 border border-red-200 text-red-700 p-4 rounded">
                    <p class="font-bold text-sm">Error Loading Widget</p>
                    <p class="text-xs mt-1">${error.message}</p>
                </div>
            `;
        }
    }

    async _renderWidgetContent(container) {
        const { widget_type } = this.widgetConfig;

        switch (widget_type) {
            case 'report_table':
                this._renderReportTable(container);
                break;
            case 'chart':
                this._renderChart(container);
                break;
            case 'kpi_card':
                this._renderKpiCard(container);
                break;
            case 'metric':
                this._renderMetric(container);
                break;
            case 'text':
                this._renderText(container);
                break;
            case 'iframe':
                this._renderIframe(container);
                break;
            default:
                container.innerHTML = '<p class="text-gray-500">Unknown widget type</p>';
        }
    }

    _renderReportTable(container) {
        if (!this.data || this.data.length === 0) {
            container.innerHTML = '<p class="text-gray-500 text-center py-8">No data available</p>';
            return;
        }

        // Get column headers from first row
        const columns = Object.keys(this.data[0]);

        let html = `
            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                        <tr>
                            ${columns.map(col => `
                                <th class="px-3 py-2 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                                    ${col}
                                </th>
                            `).join('')}
                        </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200">
        `;

        this.data.forEach(row => {
            html += '<tr class="hover:bg-gray-50">';
            columns.forEach(col => {
                html += `<td class="px-3 py-2 whitespace-nowrap text-sm text-gray-900">${row[col] ?? ''}</td>`;
            });
            html += '</tr>';
        });

        html += `
                    </tbody>
                </table>
            </div>
            <div class="mt-2 text-xs text-gray-500 text-right">
                ${this.data.length} row(s)
            </div>
        `;

        container.innerHTML = html;
    }

    _renderChart(container) {
        const chartConfig = this.widgetConfig.chart_config;

        if (!chartConfig || !this.data) {
            container.innerHTML = '<p class="text-gray-500 text-center py-8">No chart configuration</p>';
            return;
        }

        // For now, render a placeholder with chart info
        // In production, you'd integrate with Chart.js or similar
        container.innerHTML = `
            <div class="text-center py-12">
                <div class="text-6xl mb-4">📊</div>
                <p class="font-bold text-gray-800">${chartConfig.chart_type.toUpperCase()} Chart</p>
                <p class="text-sm text-gray-600 mt-2">X-Axis: ${chartConfig.x_axis}</p>
                <p class="text-sm text-gray-600">Y-Axis: ${chartConfig.y_axis.join(', ')}</p>
                <p class="text-xs text-gray-500 mt-4">${this.data.labels?.length || 0} data points</p>
                <p class="text-xs text-gray-400 mt-2">Chart integration with Chart.js ready</p>
            </div>
        `;
    }

    _renderKpiCard(container) {
        if (!this.data) {
            container.innerHTML = '<p class="text-gray-500 text-center py-8">No data</p>';
            return;
        }

        const { value, label, format } = this.data;
        let formattedValue = value;

        // Format value based on format type
        if (format === 'currency') {
            formattedValue = new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD'
            }).format(value);
        } else if (format === 'percentage') {
            formattedValue = `${value.toFixed(2)}%`;
        } else if (format === 'number') {
            formattedValue = new Intl.NumberFormat('en-US').format(value);
        }

        container.innerHTML = `
            <div class="text-center py-8">
                <div class="text-5xl font-bold text-blue-600 mb-2">${formattedValue}</div>
                <div class="text-gray-600 text-sm">${label || 'KPI'}</div>
            </div>
        `;
    }

    _renderMetric(container) {
        container.innerHTML = `
            <div class="text-center py-6">
                <div class="text-4xl font-bold text-gray-800">1,234</div>
                <div class="text-gray-600 text-sm mt-1">Sample Metric</div>
            </div>
        `;
    }

    _renderText(container) {
        const content = this.widgetConfig.widget_config?.content || 'No content';
        container.innerHTML = `<div class="prose max-w-none">${content}</div>`;
    }

    _renderIframe(container) {
        const url = this.widgetConfig.widget_config?.url || '';
        container.innerHTML = `
            <iframe src="${url}"
                    class="w-full h-full border-0"
                    style="min-height: 400px;"
                    sandbox="allow-scripts allow-same-origin"></iframe>
        `;
    }

    _setupAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }

        const interval = this.widgetConfig.refresh_interval || 'none';
        const ms = dashboardService.parseRefreshInterval(interval);

        if (ms > 0) {
            this.refreshInterval = setInterval(() => {
                this.loadData(false); // Don't use cache on auto-refresh
            }, ms);
        }
    }

    destroy() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
    }
}
