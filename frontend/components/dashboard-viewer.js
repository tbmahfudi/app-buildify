/**
 * Dashboard Viewer Component
 *
 * Displays dashboards with multiple pages and widgets
 * Supports grid layout, global parameters, and auto-refresh
 */

import { dashboardService } from '../assets/js/dashboard-service.js';
import { DashboardWidget } from './dashboard-widget.js';
import { ReportParameterInput } from './report-parameter-input.js';
import { showNotification } from '../assets/js/notifications.js';

export class DashboardViewer {
    constructor(container, dashboardId) {
        this.container = container;
        this.dashboardId = dashboardId;
        this.dashboard = null;
        this.currentPageIndex = 0;
        this.widgets = [];
        this.globalParameters = {};
        this.parameterInput = null;
    }

    async render() {
        try {
            // Load dashboard
            this.dashboard = await dashboardService.getDashboard(this.dashboardId);

            this.container.innerHTML = `
                <div class="dashboard-viewer">
                    <!-- Header -->
                    ${this.dashboard.show_header ? `
                        <div class="dashboard-header bg-white shadow-sm p-4 mb-4 rounded">
                            <div class="flex justify-between items-start">
                                <div>
                                    <h2 class="text-2xl font-bold text-gray-800">${this.dashboard.name}</h2>
                                    ${this.dashboard.description ? `
                                        <p class="text-gray-600 mt-1">${this.dashboard.description}</p>
                                    ` : ''}
                                </div>
                                <div class="flex gap-2">
                                    <button id="refresh-all-btn" class="px-3 py-1.5 text-sm bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-medium transition" title="Refresh All Widgets">
                                        🔄 Refresh All
                                    </button>
                                    <button id="fullscreen-btn" class="px-3 py-1.5 text-sm bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-medium transition" title="Toggle Fullscreen">
                                        ⛶ Fullscreen
                                    </button>
                                    <button id="edit-dashboard-btn" class="px-3 py-1.5 text-sm bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-medium transition">
                                        ✏️ Edit
                                    </button>
                                </div>
                            </div>
                        </div>
                    ` : ''}

                    <!-- Global Parameters -->
                    ${this.dashboard.show_filters && this.dashboard.global_parameters?.length > 0 ? `
                        <div class="global-parameters bg-white shadow-sm p-4 mb-4 rounded">
                            <div id="global-parameters-container"></div>
                        </div>
                    ` : ''}

                    <!-- Page Tabs -->
                    ${this.dashboard.pages.length > 1 ? `
                        <div class="page-tabs bg-white shadow-sm mb-4 rounded">
                            <div class="flex border-b">
                                ${this.dashboard.pages.map((page, index) => `
                                    <button class="page-tab px-6 py-3 font-medium transition-colors
                                        ${index === this.currentPageIndex ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-600 hover:text-gray-800'}"
                                        data-page-index="${index}">
                                        ${page.icon || ''} ${page.name}
                                    </button>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}

                    <!-- Page Content -->
                    <div id="page-container"></div>
                </div>
            `;

            // Render global parameters if any
            if (this.dashboard.show_filters && this.dashboard.global_parameters?.length > 0) {
                await this._renderGlobalParameters();
            }

            // Attach event listeners
            this._attachEventListeners();

            // Render current page
            await this._renderCurrentPage();

        } catch (error) {
            this.container.innerHTML = `
                <div class="bg-red-50 border border-red-200 text-red-700 p-4 rounded">
                    <p class="font-bold">Error Loading Dashboard</p>
                    <p class="text-sm mt-1">${error.message}</p>
                </div>
            `;
        }
    }

    async _renderGlobalParameters() {
        const container = document.getElementById('global-parameters-container');
        if (!container) return;

        this.parameterInput = new ReportParameterInput(
            container,
            this.dashboard.global_parameters,
            (values) => this._onGlobalParametersApplied(values)
        );
        await this.parameterInput.render();
    }

    _onGlobalParametersApplied(values) {
        this.globalParameters = values;
        // Refresh all widgets with new parameters
        this._refreshAllWidgets();
    }

    async _renderCurrentPage() {
        const page = this.dashboard.pages[this.currentPageIndex];
        if (!page) return;

        const pageContainer = document.getElementById('page-container');
        if (!pageContainer) return;

        // Get layout config
        const layoutConfig = page.layout_config || {
            columns: 12,
            row_height: 50,
            margin: [10, 10]
        };

        // Create grid container
        pageContainer.innerHTML = `
            <div class="dashboard-grid bg-gray-50 p-4 rounded" style="
                display: grid;
                grid-template-columns: repeat(${layoutConfig.columns}, 1fr);
                gap: ${layoutConfig.margin[0]}px;
                min-height: 500px;
            ">
                ${page.widgets.map(widget => this._renderWidgetContainer(widget, layoutConfig)).join('')}
            </div>
        `;

        // Render each widget
        this.widgets = [];
        for (const widgetConfig of page.widgets) {
            const widgetContainer = document.getElementById(`widget-container-${widgetConfig.id}`);
            if (widgetContainer) {
                const widget = new DashboardWidget(widgetContainer, widgetConfig, this.globalParameters);
                await widget.render();
                this.widgets.push(widget);
            }
        }
    }

    _renderWidgetContainer(widgetConfig, layoutConfig) {
        const { position } = widgetConfig;
        const rowHeight = layoutConfig.row_height || 50;

        return `
            <div class="widget-container"
                 id="widget-container-${widgetConfig.id}"
                 style="
                    grid-column: ${position.x + 1} / span ${position.w};
                    grid-row: ${position.y + 1} / span ${position.h};
                    min-height: ${position.h * rowHeight}px;
                 ">
            </div>
        `;
    }

    _attachEventListeners() {
        // Page tabs
        const pageTabs = this.container.querySelectorAll('.page-tab');
        pageTabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                const pageIndex = parseInt(e.target.dataset.pageIndex);
                this._switchPage(pageIndex);
            });
        });

        // Refresh all button
        const refreshAllBtn = document.getElementById('refresh-all-btn');
        if (refreshAllBtn) {
            refreshAllBtn.addEventListener('click', () => this._refreshAllWidgets());
        }

        // Fullscreen button
        const fullscreenBtn = document.getElementById('fullscreen-btn');
        if (fullscreenBtn) {
            fullscreenBtn.addEventListener('click', () => this._toggleFullscreen());
        }

        // Edit button
        const editBtn = document.getElementById('edit-dashboard-btn');
        if (editBtn) {
            editBtn.addEventListener('click', () => {
                window.location.hash = `#/dashboards/builder/${this.dashboardId}`;
            });
        }
    }

    async _switchPage(pageIndex) {
        if (pageIndex === this.currentPageIndex) return;

        // Cleanup current widgets
        this.widgets.forEach(widget => widget.destroy());
        this.widgets = [];

        // Update current page
        this.currentPageIndex = pageIndex;

        // Update tab styles
        const tabs = this.container.querySelectorAll('.page-tab');
        tabs.forEach((tab, index) => {
            if (index === pageIndex) {
                tab.classList.add('text-blue-600', 'border-b-2', 'border-blue-600');
                tab.classList.remove('text-gray-600');
            } else {
                tab.classList.remove('text-blue-600', 'border-b-2', 'border-blue-600');
                tab.classList.add('text-gray-600');
            }
        });

        // Render new page
        await this._renderCurrentPage();
    }

    async _refreshAllWidgets() {
        showNotification('Refreshing all widgets...', 'info');
        for (const widget of this.widgets) {
            await widget.loadData(false); // Don't use cache
        }
        showNotification('All widgets refreshed!', 'success');
    }

    _toggleFullscreen() {
        if (!document.fullscreenElement) {
            this.container.requestFullscreen().catch(err => {
                console.error('Failed to enter fullscreen:', err);
            });
        } else {
            document.exitFullscreen();
        }
    }

    destroy() {
        // Cleanup all widgets
        this.widgets.forEach(widget => widget.destroy());
        this.widgets = [];
    }
}
