/**
 * Dashboard Interactive Features Component
 *
 * Provides interactive features for dashboards including drill-down,
 * filtering, linking, real-time updates, and export capabilities.
 *
 * Features:
 * - Widget drill-down (click chart → details)
 * - Cross-widget filtering
 * - Widget linking and communication
 * - Real-time data refresh
 * - Export dashboard (PDF, PNG, HTML)
 * - Dashboard sharing and embedding
 *
 * Usage:
 * const interactive = new DashboardInteractiveFeatures(dashboard, {
 *   onDrillDown: (widget, data) => console.log('Drill down:', widget, data),
 *   onFilterApply: (filters) => console.log('Filters:', filters),
 *   onExport: (format) => console.log('Export:', format)
 * });
 */

import { apiFetch } from '../utils/api.js';

export class DashboardInteractiveFeatures {
    constructor(dashboardElement, options = {}) {
        this.dashboardElement = dashboardElement;
        this.options = options;

        // State
        this.widgets = [];
        this.activeFilters = {};
        this.widgetLinks = {}; // widget linking configuration
        this.refreshIntervals = {};
        this.drillDownStack = [];

        // Callbacks
        this.onDrillDown = options.onDrillDown || (() => {});
        this.onFilterApply = options.onFilterApply || (() => {});
        this.onWidgetLink = options.onWidgetLink || (() => {});
        this.onExport = options.onExport || (() => {});
        this.onShare = options.onShare || (() => {});

        this.init();
    }

    init() {
        this.attachGlobalListeners();
    }

    attachGlobalListeners() {
        // Listen for widget clicks for drill-down
        this.dashboardElement.addEventListener('click', (e) => {
            const widgetElement = e.target.closest('[data-widget-id]');
            if (widgetElement) {
                this.handleWidgetClick(widgetElement, e);
            }
        });
    }

    // ========================================
    // Drill-Down Features
    // ========================================

    enableDrillDown(widgetId, config = {}) {
        const widget = this.getWidget(widgetId);
        if (!widget) return;

        widget.drillDown = {
            enabled: true,
            target: config.target || null, // target report/dashboard
            parameterMapping: config.parameterMapping || {},
            breadcrumb: config.breadcrumb !== false
        };

        this.updateWidget(widget);
    }

    handleWidgetClick(widgetElement, event) {
        const widgetId = widgetElement.dataset.widgetId;
        const widget = this.getWidget(widgetId);

        if (!widget || !widget.drillDown?.enabled) return;

        // Check if click is on a data point
        const dataPoint = event.target.closest('[data-value]');
        if (!dataPoint) return;

        const value = dataPoint.dataset.value;
        const label = dataPoint.dataset.label;

        this.executeDrillDown(widget, { value, label });
    }

    executeDrillDown(widget, data) {
        // Add to drill-down stack
        this.drillDownStack.push({
            widgetId: widget.id,
            data: data,
            timestamp: Date.now()
        });

        // Show breadcrumb if enabled
        if (widget.drillDown.breadcrumb) {
            this.showDrillDownBreadcrumb();
        }

        // Execute callback
        this.onDrillDown(widget, data);

        // Apply filters based on drill-down
        const filters = this.mapDrillDownToFilters(widget, data);
        this.applyFilters(filters);
    }

    mapDrillDownToFilters(widget, data) {
        const filters = {};

        if (widget.drillDown.parameterMapping) {
            for (const [param, value] of Object.entries(widget.drillDown.parameterMapping)) {
                filters[param] = data.value;
            }
        }

        return filters;
    }

    showDrillDownBreadcrumb() {
        const breadcrumbContainer = document.createElement('div');
        breadcrumbContainer.className = 'drill-down-breadcrumb fixed top-16 left-0 right-0 bg-blue-50 border-b border-blue-200 px-4 py-2 flex items-center space-x-2 z-40';
        breadcrumbContainer.innerHTML = `
            <i class="ph ph-arrow-left cursor-pointer hover:text-blue-700" id="breadcrumb-back"></i>
            <div class="flex items-center space-x-2 text-sm">
                ${this.drillDownStack.map((item, index) => `
                    <span class="text-gray-600">${index > 0 ? '>' : ''}</span>
                    <span class="text-blue-600">${item.data.label || item.data.value}</span>
                `).join('')}
            </div>
            <button class="ml-auto text-gray-400 hover:text-gray-600" id="breadcrumb-close">
                <i class="ph ph-x"></i>
            </button>
        `;

        // Remove existing breadcrumb
        const existing = document.querySelector('.drill-down-breadcrumb');
        if (existing) existing.remove();

        document.body.appendChild(breadcrumbContainer);

        // Event listeners
        breadcrumbContainer.querySelector('#breadcrumb-back')?.addEventListener('click', () => {
            this.drillDownBack();
        });

        breadcrumbContainer.querySelector('#breadcrumb-close')?.addEventListener('click', () => {
            this.clearDrillDown();
        });
    }

    drillDownBack() {
        if (this.drillDownStack.length > 0) {
            this.drillDownStack.pop();

            if (this.drillDownStack.length === 0) {
                this.clearDrillDown();
            } else {
                this.showDrillDownBreadcrumb();
                // Reapply filters from current stack
                const lastItem = this.drillDownStack[this.drillDownStack.length - 1];
                const widget = this.getWidget(lastItem.widgetId);
                const filters = this.mapDrillDownToFilters(widget, lastItem.data);
                this.applyFilters(filters);
            }
        }
    }

    clearDrillDown() {
        this.drillDownStack = [];
        this.clearFilters();

        const breadcrumb = document.querySelector('.drill-down-breadcrumb');
        if (breadcrumb) breadcrumb.remove();
    }

    // ========================================
    // Cross-Widget Filtering
    // ========================================

    applyFilters(filters) {
        this.activeFilters = { ...this.activeFilters, ...filters };

        // Refresh all widgets with new filters
        this.refreshAllWidgets();

        // Show active filters bar
        this.showActiveFilters();

        this.onFilterApply(this.activeFilters);
    }

    clearFilters() {
        this.activeFilters = {};
        this.refreshAllWidgets();
        this.hideActiveFilters();
    }

    showActiveFilters() {
        const filterBar = document.createElement('div');
        filterBar.className = 'active-filters-bar fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 px-4 py-3 flex items-center space-x-2 z-40 shadow-lg';
        filterBar.innerHTML = `
            <span class="text-sm font-medium text-gray-700">Active Filters:</span>
            <div class="flex items-center space-x-2 flex-1">
                ${Object.entries(this.activeFilters).map(([key, value]) => `
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800">
                        <span class="font-medium">${key}:</span>
                        <span class="ml-1">${value}</span>
                        <button class="ml-2 hover:text-blue-900" data-filter-key="${key}">
                            <i class="ph ph-x text-xs"></i>
                        </button>
                    </span>
                `).join('')}
            </div>
            <button class="text-sm text-gray-600 hover:text-gray-900" id="clear-all-filters">
                Clear All
            </button>
        `;

        // Remove existing filter bar
        const existing = document.querySelector('.active-filters-bar');
        if (existing) existing.remove();

        document.body.appendChild(filterBar);

        // Event listeners
        filterBar.querySelectorAll('[data-filter-key]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const key = e.currentTarget.dataset.filterKey;
                this.removeFilter(key);
            });
        });

        filterBar.querySelector('#clear-all-filters')?.addEventListener('click', () => {
            this.clearFilters();
        });
    }

    hideActiveFilters() {
        const filterBar = document.querySelector('.active-filters-bar');
        if (filterBar) filterBar.remove();
    }

    removeFilter(key) {
        delete this.activeFilters[key];

        if (Object.keys(this.activeFilters).length === 0) {
            this.clearFilters();
        } else {
            this.refreshAllWidgets();
            this.showActiveFilters();
        }
    }

    // ========================================
    // Widget Linking
    // ========================================

    linkWidgets(sourceWidgetId, targetWidgetId, config = {}) {
        if (!this.widgetLinks[sourceWidgetId]) {
            this.widgetLinks[sourceWidgetId] = [];
        }

        this.widgetLinks[sourceWidgetId].push({
            target: targetWidgetId,
            event: config.event || 'click', // click, hover, change
            parameterMapping: config.parameterMapping || {},
            action: config.action || 'filter' // filter, highlight, update
        });

        this.onWidgetLink(sourceWidgetId, targetWidgetId, config);
    }

    unlinkWidgets(sourceWidgetId, targetWidgetId) {
        if (this.widgetLinks[sourceWidgetId]) {
            this.widgetLinks[sourceWidgetId] = this.widgetLinks[sourceWidgetId].filter(
                link => link.target !== targetWidgetId
            );
        }
    }

    // ========================================
    // Real-Time Refresh
    // ========================================

    enableAutoRefresh(widgetId, interval = 30000) {
        this.disableAutoRefresh(widgetId); // Clear existing

        this.refreshIntervals[widgetId] = setInterval(() => {
            this.refreshWidget(widgetId);
        }, interval);
    }

    disableAutoRefresh(widgetId) {
        if (this.refreshIntervals[widgetId]) {
            clearInterval(this.refreshIntervals[widgetId]);
            delete this.refreshIntervals[widgetId];
        }
    }

    async refreshWidget(widgetId) {
        const widget = this.getWidget(widgetId);
        if (!widget) return;

        try {
            const response = await apiFetch(`/api/v1/widgets/${widgetId}/data`, {
                method: 'POST',
                body: JSON.stringify({
                    filters: this.activeFilters
                })
            });

            const data = await response.json();
            widget.data = data;

            // Update widget UI
            this.updateWidgetUI(widget);
        } catch (error) {
            console.error(`Failed to refresh widget ${widgetId}:`, error);
        }
    }

    async refreshAllWidgets() {
        const refreshPromises = this.widgets.map(widget => this.refreshWidget(widget.id));
        await Promise.all(refreshPromises);
    }

    // ========================================
    // Export Features
    // ========================================

    async exportDashboard(format = 'pdf', options = {}) {
        const exportOptions = {
            format: format, // pdf, png, html, excel
            filename: options.filename || `dashboard-${Date.now()}`,
            includeFilters: options.includeFilters !== false,
            ...options
        };

        this.onExport(format);

        switch (format) {
            case 'pdf':
                await this.exportToPDF(exportOptions);
                break;
            case 'png':
                await this.exportToPNG(exportOptions);
                break;
            case 'html':
                await this.exportToHTML(exportOptions);
                break;
            case 'excel':
                await this.exportToExcel(exportOptions);
                break;
            default:
                console.error('Unsupported export format:', format);
        }
    }

    async exportToPDF(options) {
        // Show loading
        this.showExportLoading('Generating PDF...');

        try {
            const response = await apiFetch('/api/v1/dashboards/export/pdf', {
                method: 'POST',
                body: JSON.stringify({
                    widgets: this.widgets,
                    filters: options.includeFilters ? this.activeFilters : {},
                    filename: options.filename
                })
            });

            const blob = await response.blob();
            this.downloadBlob(blob, `${options.filename}.pdf`);
        } catch (error) {
            console.error('PDF export failed:', error);
            alert('Failed to export dashboard to PDF');
        } finally {
            this.hideExportLoading();
        }
    }

    async exportToPNG(options) {
        this.showExportLoading('Generating PNG...');

        try {
            // Use html2canvas to capture dashboard
            const html2canvas = await this.loadHtml2Canvas();
            const canvas = await html2canvas(this.dashboardElement, {
                backgroundColor: '#ffffff',
                scale: 2
            });

            canvas.toBlob((blob) => {
                this.downloadBlob(blob, `${options.filename}.png`);
                this.hideExportLoading();
            });
        } catch (error) {
            console.error('PNG export failed:', error);
            alert('Failed to export dashboard to PNG');
            this.hideExportLoading();
        }
    }

    async exportToHTML(options) {
        this.showExportLoading('Generating HTML...');

        try {
            const html = this.generateStandaloneHTML();
            const blob = new Blob([html], { type: 'text/html' });
            this.downloadBlob(blob, `${options.filename}.html`);
        } catch (error) {
            console.error('HTML export failed:', error);
            alert('Failed to export dashboard to HTML');
        } finally {
            this.hideExportLoading();
        }
    }

    async exportToExcel(options) {
        this.showExportLoading('Generating Excel...');

        try {
            const response = await apiFetch('/api/v1/dashboards/export/excel', {
                method: 'POST',
                body: JSON.stringify({
                    widgets: this.widgets,
                    filters: this.activeFilters
                })
            });

            const blob = await response.blob();
            this.downloadBlob(blob, `${options.filename}.xlsx`);
        } catch (error) {
            console.error('Excel export failed:', error);
            alert('Failed to export dashboard to Excel');
        } finally {
            this.hideExportLoading();
        }
    }

    generateStandaloneHTML() {
        const dashboardHTML = this.dashboardElement.innerHTML;
        return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Export</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/@phosphor-icons/web"></script>
    <style>
        body { margin: 0; padding: 20px; background: #f3f4f6; }
        .dashboard-container { max-width: 1400px; margin: 0 auto; }
    </style>
</head>
<body>
    <div class="dashboard-container">
        <div class="bg-white rounded-lg shadow-lg p-6 mb-4">
            <h1 class="text-2xl font-bold text-gray-900">Dashboard Export</h1>
            <p class="text-sm text-gray-500">Exported on ${new Date().toLocaleString()}</p>
        </div>
        ${dashboardHTML}
    </div>
</body>
</html>
        `;
    }

    downloadBlob(blob, filename) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    async loadHtml2Canvas() {
        if (typeof html2canvas !== 'undefined') {
            return html2canvas;
        }

        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js';
            script.onload = () => resolve(window.html2canvas);
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    showExportLoading(message) {
        const loader = document.createElement('div');
        loader.id = 'export-loader';
        loader.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center';
        loader.innerHTML = `
            <div class="bg-white rounded-lg p-6 flex flex-col items-center">
                <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
                <p class="text-gray-900 font-medium">${message}</p>
            </div>
        `;
        document.body.appendChild(loader);
    }

    hideExportLoading() {
        const loader = document.getElementById('export-loader');
        if (loader) loader.remove();
    }

    // ========================================
    // Sharing & Embedding
    // ========================================

    async shareDashboard(options = {}) {
        const shareConfig = {
            accessLevel: options.accessLevel || 'view', // view, edit
            expiresAt: options.expiresAt || null,
            password: options.password || null,
            allowDownload: options.allowDownload !== false
        };

        try {
            const response = await apiFetch('/api/v1/dashboards/share', {
                method: 'POST',
                body: JSON.stringify({
                    dashboardId: options.dashboardId,
                    ...shareConfig
                })
            });

            const data = await response.json();
            const shareUrl = data.shareUrl;

            this.showShareDialog(shareUrl, shareConfig);
            this.onShare(shareUrl, shareConfig);
        } catch (error) {
            console.error('Failed to share dashboard:', error);
            alert('Failed to generate share link');
        }
    }

    showShareDialog(shareUrl, config) {
        const dialog = document.createElement('div');
        dialog.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4';
        dialog.innerHTML = `
            <div class="bg-white rounded-lg shadow-2xl max-w-md w-full p-6">
                <h3 class="text-lg font-semibold text-gray-900 mb-4">Share Dashboard</h3>

                <div class="mb-4">
                    <label class="block text-sm font-medium text-gray-700 mb-2">Share Link</label>
                    <div class="flex items-center space-x-2">
                        <input type="text" value="${shareUrl}" readonly
                            class="flex-1 px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-sm">
                        <button id="copy-share-link" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                            <i class="ph ph-copy"></i>
                        </button>
                    </div>
                </div>

                <div class="mb-4">
                    <label class="block text-sm font-medium text-gray-700 mb-2">Embed Code</label>
                    <textarea readonly rows="3"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-xs font-mono">&lt;iframe src="${shareUrl}" width="100%" height="600"&gt;&lt;/iframe&gt;</textarea>
                </div>

                <div class="flex justify-end space-x-2">
                    <button id="close-share-dialog" class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">
                        Close
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(dialog);

        // Event listeners
        dialog.querySelector('#copy-share-link')?.addEventListener('click', () => {
            navigator.clipboard.writeText(shareUrl);
            alert('Link copied to clipboard!');
        });

        dialog.querySelector('#close-share-dialog')?.addEventListener('click', () => {
            dialog.remove();
        });

        dialog.addEventListener('click', (e) => {
            if (e.target === dialog) {
                dialog.remove();
            }
        });
    }

    // ========================================
    // Utility Methods
    // ========================================

    getWidget(widgetId) {
        return this.widgets.find(w => w.id === widgetId);
    }

    updateWidget(widget) {
        const index = this.widgets.findIndex(w => w.id === widget.id);
        if (index !== -1) {
            this.widgets[index] = widget;
        }
    }

    updateWidgetUI(widget) {
        const widgetElement = this.dashboardElement.querySelector(`[data-widget-id="${widget.id}"]`);
        if (widgetElement) {
            // Update widget content based on new data
            // This would typically re-render the widget
            widgetElement.dispatchEvent(new CustomEvent('widget-update', { detail: widget }));
        }
    }

    // Public API
    setWidgets(widgets) {
        this.widgets = widgets;
    }

    getActiveFilters() {
        return this.activeFilters;
    }

    getDrillDownStack() {
        return this.drillDownStack;
    }

    destroy() {
        // Clean up all intervals
        Object.keys(this.refreshIntervals).forEach(widgetId => {
            this.disableAutoRefresh(widgetId);
        });

        // Clear UI elements
        this.clearDrillDown();
        this.hideActiveFilters();
    }
}
