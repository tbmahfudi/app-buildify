/**
 * Live Dashboard Preview Component
 *
 * Multi-device preview with live/mock data toggle and theme switching.
 * Provides real-time dashboard preview with performance metrics.
 *
 * Features:
 * - Multi-device preview modes (Desktop, Tablet, Mobile)
 * - Theme switcher (Light, Dark, Custom)
 * - Live data vs Mock data toggle
 * - Performance metrics overlay
 * - Refresh rate configuration
 * - Auto-save with version history
 *
 * Usage:
 * const preview = new LiveDashboardPreview(container, {
 *   dashboardConfig: {},
 *   autoRefresh: true,
 *   refreshInterval: 30000,
 *   onThemeChange: (theme) => console.log('Theme:', theme),
 *   onDeviceChange: (device) => console.log('Device:', device)
 * });
 */

import { apiFetch } from '../assets/js/api.js';

export class LiveDashboardPreview {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        this.options = options;

        // State
        this.dashboardConfig = options.dashboardConfig || {};
        this.currentDevice = options.defaultDevice || 'desktop';
        this.currentTheme = options.defaultTheme || 'light';
        this.dataMode = options.dataMode || 'mock'; // 'live' or 'mock'
        this.isVisible = options.isVisible !== false;
        this.autoRefresh = options.autoRefresh || false;
        this.refreshInterval = options.refreshInterval || 30000; // 30 seconds
        this.showPerformance = options.showPerformance || false;

        // Callbacks
        this.onThemeChange = options.onThemeChange || (() => {});
        this.onDeviceChange = options.onDeviceChange || (() => {});
        this.onDataModeChange = options.onDataModeChange || (() => {});
        this.onRefresh = options.onRefresh || (() => {});

        // Preview data
        this.previewData = null;
        this.performanceMetrics = {
            loadTime: 0,
            widgetCount: 0,
            dataSize: 0,
            renderTime: 0
        };

        // Auto-refresh timer
        this.refreshTimer = null;

        // Version history
        this.versionHistory = [];
        this.currentVersion = 0;

        // Device presets
        this.devicePresets = {
            desktop: { width: '100%', height: '100%', label: 'Desktop', icon: 'ph-desktop' },
            tablet: { width: '768px', height: '1024px', label: 'Tablet', icon: 'ph-device-tablet' },
            mobile: { width: '375px', height: '667px', label: 'Mobile', icon: 'ph-device-mobile' }
        };

        // Theme presets
        this.themePresets = {
            light: { label: 'Light', bgColor: '#ffffff', textColor: '#1f2937' },
            dark: { label: 'Dark', bgColor: '#1f2937', textColor: '#f3f4f6' },
            custom: { label: 'Custom', bgColor: '#f8fafc', textColor: '#0f172a' }
        };

        this.init();
    }

    async init() {
        await this.render();
        this.attachEventListeners();

        if (this.autoRefresh) {
            this.startAutoRefresh();
        }
    }

    async render() {
        const devicePreset = this.devicePresets[this.currentDevice];
        const themePreset = this.themePresets[this.currentTheme];

        this.container.innerHTML = `
            <div class="live-dashboard-preview ${this.isVisible ? '' : 'hidden'} h-full flex flex-col bg-gray-50">
                <!-- Toolbar -->
                <div class="preview-toolbar bg-white border-b border-gray-200 p-3 flex items-center justify-between">
                    <!-- Left: Device Switcher -->
                    <div class="flex items-center space-x-2">
                        <span class="text-xs font-medium text-gray-700 mr-2">Device:</span>
                        ${Object.entries(this.devicePresets).map(([key, preset]) => `
                            <button class="device-btn px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                                this.currentDevice === key
                                    ? 'bg-blue-100 text-blue-700'
                                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                            }" data-device="${key}">
                                <i class="${preset.icon} mr-1"></i>
                                ${preset.label}
                            </button>
                        `).join('')}
                    </div>

                    <!-- Center: Theme Switcher -->
                    <div class="flex items-center space-x-2">
                        <span class="text-xs font-medium text-gray-700 mr-2">Theme:</span>
                        ${Object.entries(this.themePresets).map(([key, preset]) => `
                            <button class="theme-btn px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                                this.currentTheme === key
                                    ? 'bg-blue-100 text-blue-700'
                                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                            }" data-theme="${key}">
                                ${preset.label}
                            </button>
                        `).join('')}
                    </div>

                    <!-- Right: Controls -->
                    <div class="flex items-center space-x-2">
                        <!-- Data Mode Toggle -->
                        <div class="flex items-center bg-gray-100 rounded-lg p-1">
                            <button class="data-mode-btn px-3 py-1 rounded text-xs font-medium transition-colors ${
                                this.dataMode === 'mock' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600'
                            }" data-mode="mock">
                                <i class="ph ph-database mr-1"></i>
                                Mock
                            </button>
                            <button class="data-mode-btn px-3 py-1 rounded text-xs font-medium transition-colors ${
                                this.dataMode === 'live' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600'
                            }" data-mode="live">
                                <i class="ph ph-broadcast mr-1"></i>
                                Live
                            </button>
                        </div>

                        <!-- Refresh Controls -->
                        <button id="refresh-btn" class="px-3 py-1.5 bg-white border border-gray-300 rounded-lg text-xs font-medium text-gray-700 hover:bg-gray-50">
                            <i class="ph ph-arrows-clockwise mr-1"></i>
                            Refresh
                        </button>

                        <button id="auto-refresh-btn" class="px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                            this.autoRefresh
                                ? 'bg-green-100 text-green-700'
                                : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                        }">
                            <i class="ph ${this.autoRefresh ? 'ph-pause' : 'ph-play'} mr-1"></i>
                            ${this.autoRefresh ? 'Auto' : 'Manual'}
                        </button>

                        <!-- Performance Toggle -->
                        <button id="performance-btn" class="px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                            this.showPerformance
                                ? 'bg-purple-100 text-purple-700'
                                : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                        }">
                            <i class="ph ph-gauge mr-1"></i>
                            Metrics
                        </button>
                    </div>
                </div>

                <!-- Preview Frame -->
                <div class="preview-frame-container flex-1 flex items-center justify-center p-4 overflow-auto">
                    <div class="preview-frame-wrapper relative" style="width: ${devicePreset.width}; height: ${devicePreset.height};">
                        <!-- Performance Overlay -->
                        ${this.showPerformance ? `
                            <div class="performance-overlay absolute top-0 right-0 m-4 bg-black bg-opacity-80 text-white rounded-lg p-3 text-xs space-y-1 z-50">
                                <div class="font-semibold mb-2">Performance Metrics</div>
                                <div class="flex justify-between">
                                    <span class="text-gray-300">Load Time:</span>
                                    <span class="font-mono">${this.performanceMetrics.loadTime}ms</span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-gray-300">Widgets:</span>
                                    <span class="font-mono">${this.performanceMetrics.widgetCount}</span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-gray-300">Data Size:</span>
                                    <span class="font-mono">${this.formatBytes(this.performanceMetrics.dataSize)}</span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-gray-300">Render:</span>
                                    <span class="font-mono">${this.performanceMetrics.renderTime}ms</span>
                                </div>
                            </div>
                        ` : ''}

                        <!-- Preview Content -->
                        <div class="preview-content w-full h-full rounded-lg shadow-xl overflow-auto"
                            style="background-color: ${themePreset.bgColor}; color: ${themePreset.textColor};">
                            ${this.renderDashboardPreview()}
                        </div>
                    </div>
                </div>

                <!-- Status Bar -->
                <div class="preview-status-bar bg-white border-t border-gray-200 px-4 py-2 flex items-center justify-between text-xs text-gray-600">
                    <div class="flex items-center space-x-4">
                        <span>
                            <i class="ph ph-monitor mr-1"></i>
                            ${devicePreset.label} (${devicePreset.width})
                        </span>
                        <span>
                            <i class="ph ph-palette mr-1"></i>
                            ${themePreset.label} Theme
                        </span>
                        <span class="${this.dataMode === 'live' ? 'text-green-600' : 'text-blue-600'}">
                            <i class="ph ${this.dataMode === 'live' ? 'ph-broadcast' : 'ph-database'} mr-1"></i>
                            ${this.dataMode === 'live' ? 'Live Data' : 'Mock Data'}
                        </span>
                    </div>
                    <div class="flex items-center space-x-4">
                        ${this.autoRefresh ? `
                            <span class="text-green-600">
                                <i class="ph ph-arrows-clockwise mr-1"></i>
                                Auto-refresh: ${this.refreshInterval / 1000}s
                            </span>
                        ` : ''}
                        <span>
                            Last updated: ${new Date().toLocaleTimeString()}
                        </span>
                    </div>
                </div>
            </div>
        `;
    }

    renderDashboardPreview() {
        if (!this.dashboardConfig || !this.dashboardConfig.widgets || this.dashboardConfig.widgets.length === 0) {
            return `
                <div class="flex items-center justify-center h-full">
                    <div class="text-center">
                        <i class="ph ph-grid-four text-6xl text-gray-300 mb-4"></i>
                        <p class="text-gray-500">No widgets added yet</p>
                        <p class="text-sm text-gray-400 mt-2">Drag widgets from the library to start building</p>
                    </div>
                </div>
            `;
        }

        // Render dashboard grid with widgets
        return `
            <div class="dashboard-preview-grid p-4">
                <div class="grid grid-cols-12 gap-4 auto-rows-min">
                    ${this.dashboardConfig.widgets.map(widget => this.renderWidget(widget)).join('')}
                </div>
            </div>
        `;
    }

    renderWidget(widget) {
        const colSpan = widget.w || 4;
        const rowSpan = widget.h || 3;

        return `
            <div class="widget-preview col-span-${Math.min(colSpan, 12)} bg-white dark:bg-gray-800 rounded-lg shadow p-4"
                style="grid-row: span ${rowSpan};">
                <div class="widget-header mb-3 flex items-center justify-between">
                    <h4 class="font-semibold text-sm">${widget.title || 'Widget'}</h4>
                    <i class="ph ph-dots-three text-gray-400"></i>
                </div>
                <div class="widget-body">
                    ${this.renderWidgetContent(widget)}
                </div>
            </div>
        `;
    }

    renderWidgetContent(widget) {
        const type = widget.type || 'chart';

        // Render based on widget type
        if (type.startsWith('chart-')) {
            return this.renderChartWidget(widget);
        } else if (type.startsWith('metric-')) {
            return this.renderMetricWidget(widget);
        } else if (type.startsWith('table-')) {
            return this.renderTableWidget(widget);
        } else if (type.startsWith('text-')) {
            return this.renderTextWidget(widget);
        } else if (type.startsWith('media-')) {
            return this.renderMediaWidget(widget);
        } else if (type.startsWith('action-')) {
            return this.renderActionWidget(widget);
        }

        return '<div class="text-gray-400 text-sm">Widget content</div>';
    }

    renderChartWidget(widget) {
        return `
            <div class="chart-placeholder bg-gray-50 dark:bg-gray-700 rounded h-full min-h-[150px] flex items-center justify-center">
                <div class="text-center">
                    <i class="ph ph-chart-bar text-4xl text-gray-300 mb-2"></i>
                    <div class="text-xs text-gray-500">${this.dataMode === 'live' ? 'Loading data...' : 'Mock chart data'}</div>
                </div>
            </div>
        `;
    }

    renderMetricWidget(widget) {
        const mockValue = this.dataMode === 'live' ? '...' : Math.floor(Math.random() * 10000);
        const mockTrend = this.dataMode === 'live' ? '...' : '+' + (Math.random() * 20).toFixed(1) + '%';

        return `
            <div class="metric-content">
                <div class="text-3xl font-bold text-gray-900 dark:text-white mb-2">${mockValue}</div>
                <div class="text-sm text-green-600 flex items-center">
                    <i class="ph ph-trend-up mr-1"></i>
                    ${mockTrend}
                </div>
            </div>
        `;
    }

    renderTableWidget(widget) {
        return `
            <div class="table-placeholder">
                <table class="w-full text-sm">
                    <thead class="bg-gray-50 dark:bg-gray-700">
                        <tr>
                            <th class="px-2 py-1 text-left">Column 1</th>
                            <th class="px-2 py-1 text-left">Column 2</th>
                            <th class="px-2 py-1 text-left">Column 3</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${[1, 2, 3].map(i => `
                            <tr class="border-t border-gray-200 dark:border-gray-600">
                                <td class="px-2 py-1">${this.dataMode === 'live' ? '...' : 'Data ' + i}</td>
                                <td class="px-2 py-1">${this.dataMode === 'live' ? '...' : 'Value ' + i}</td>
                                <td class="px-2 py-1">${this.dataMode === 'live' ? '...' : Math.floor(Math.random() * 100)}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }

    renderTextWidget(widget) {
        return `
            <div class="text-content">
                <p class="text-gray-600 dark:text-gray-300">${widget.content || 'Text widget content'}</p>
            </div>
        `;
    }

    renderMediaWidget(widget) {
        return `
            <div class="media-placeholder bg-gray-100 dark:bg-gray-700 rounded h-full min-h-[150px] flex items-center justify-center">
                <i class="ph ph-image text-4xl text-gray-300"></i>
            </div>
        `;
    }

    renderActionWidget(widget) {
        return `
            <div class="action-content flex items-center justify-center">
                <button class="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700">
                    ${widget.label || 'Action Button'}
                </button>
            </div>
        `;
    }

    attachEventListeners() {
        const container = this.container;

        // Device switcher
        container.querySelectorAll('.device-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const device = e.currentTarget.dataset.device;
                this.switchDevice(device);
            });
        });

        // Theme switcher
        container.querySelectorAll('.theme-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const theme = e.currentTarget.dataset.theme;
                this.switchTheme(theme);
            });
        });

        // Data mode toggle
        container.querySelectorAll('.data-mode-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const mode = e.currentTarget.dataset.mode;
                this.switchDataMode(mode);
            });
        });

        // Refresh button
        const refreshBtn = container.querySelector('#refresh-btn');
        refreshBtn?.addEventListener('click', () => {
            this.refreshPreview();
        });

        // Auto-refresh toggle
        const autoRefreshBtn = container.querySelector('#auto-refresh-btn');
        autoRefreshBtn?.addEventListener('click', () => {
            this.toggleAutoRefresh();
        });

        // Performance toggle
        const performanceBtn = container.querySelector('#performance-btn');
        performanceBtn?.addEventListener('click', () => {
            this.togglePerformance();
        });
    }

    switchDevice(device) {
        if (this.devicePresets[device]) {
            this.currentDevice = device;
            this.render();
            this.attachEventListeners();
            this.onDeviceChange(device);
        }
    }

    switchTheme(theme) {
        if (this.themePresets[theme]) {
            this.currentTheme = theme;
            this.render();
            this.attachEventListeners();
            this.onThemeChange(theme);
        }
    }

    switchDataMode(mode) {
        this.dataMode = mode;
        this.render();
        this.attachEventListeners();
        this.onDataModeChange(mode);

        if (mode === 'live') {
            this.loadLiveData();
        }
    }

    async refreshPreview() {
        const startTime = performance.now();

        if (this.dataMode === 'live') {
            await this.loadLiveData();
        }

        this.performanceMetrics.loadTime = Math.round(performance.now() - startTime);

        await this.render();
        this.attachEventListeners();
        this.onRefresh();
    }

    async loadLiveData() {
        if (!this.dashboardConfig || !this.dashboardConfig.id) {
            return;
        }

        try {
            const response = await apiFetch(`/api/v1/dashboards/${this.dashboardConfig.id}/data`);
            this.previewData = await response.json();
            this.performanceMetrics.dataSize = JSON.stringify(this.previewData).length;
        } catch (error) {
            console.error('Failed to load live data:', error);
        }
    }

    toggleAutoRefresh() {
        this.autoRefresh = !this.autoRefresh;

        if (this.autoRefresh) {
            this.startAutoRefresh();
        } else {
            this.stopAutoRefresh();
        }

        this.render();
        this.attachEventListeners();
    }

    startAutoRefresh() {
        this.stopAutoRefresh(); // Clear any existing timer

        this.refreshTimer = setInterval(() => {
            this.refreshPreview();
        }, this.refreshInterval);
    }

    stopAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
        }
    }

    togglePerformance() {
        this.showPerformance = !this.showPerformance;
        this.render();
        this.attachEventListeners();
    }

    formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }

    // Public API
    updateDashboardConfig(config) {
        this.dashboardConfig = config;
        this.performanceMetrics.widgetCount = config.widgets?.length || 0;

        // Save version
        this.saveVersion();

        this.render();
        this.attachEventListeners();

        if (this.autoRefresh && this.dataMode === 'live') {
            this.loadLiveData();
        }
    }

    saveVersion() {
        const version = {
            timestamp: Date.now(),
            config: JSON.parse(JSON.stringify(this.dashboardConfig))
        };

        this.versionHistory.push(version);

        // Keep only last 20 versions
        if (this.versionHistory.length > 20) {
            this.versionHistory.shift();
        }

        this.currentVersion = this.versionHistory.length - 1;

        // Auto-save to localStorage
        this.autoSave();
    }

    autoSave() {
        try {
            const key = `dashboard_autosave_${this.dashboardConfig.id || 'new'}`;
            localStorage.setItem(key, JSON.stringify({
                config: this.dashboardConfig,
                timestamp: Date.now()
            }));
        } catch (e) {
            console.error('Auto-save failed:', e);
        }
    }

    loadAutoSave(dashboardId) {
        try {
            const key = `dashboard_autosave_${dashboardId || 'new'}`;
            const saved = localStorage.getItem(key);
            if (saved) {
                const data = JSON.parse(saved);
                return data.config;
            }
        } catch (e) {
            console.error('Failed to load auto-save:', e);
        }
        return null;
    }

    getVersionHistory() {
        return this.versionHistory;
    }

    restoreVersion(versionIndex) {
        if (versionIndex >= 0 && versionIndex < this.versionHistory.length) {
            this.dashboardConfig = JSON.parse(JSON.stringify(this.versionHistory[versionIndex].config));
            this.currentVersion = versionIndex;
            this.render();
            this.attachEventListeners();
        }
    }

    toggle() {
        this.isVisible = !this.isVisible;
        this.container.querySelector('.live-dashboard-preview')?.classList.toggle('hidden', !this.isVisible);
    }

    show() {
        this.isVisible = true;
        this.container.querySelector('.live-dashboard-preview')?.classList.remove('hidden');
    }

    hide() {
        this.isVisible = false;
        this.container.querySelector('.live-dashboard-preview')?.classList.add('hidden');
    }

    destroy() {
        this.stopAutoRefresh();
    }
}
