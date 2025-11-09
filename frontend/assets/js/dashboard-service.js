/**
 * Dashboard Service - Singleton service for dashboard operations
 *
 * Provides comprehensive API for:
 * - Dashboard CRUD operations
 * - Dashboard page management
 * - Widget management
 * - Widget data fetching (reuses report infrastructure)
 * - Dashboard sharing and snapshots
 */

import { authService } from './auth-service.js';

class DashboardService {
    constructor() {
        if (DashboardService.instance) {
            return DashboardService.instance;
        }
        this.baseUrl = '/api/v1/dashboards';
        DashboardService.instance = this;
    }

    /**
     * Helper method to make authenticated API calls
     */
    async _fetchWithAuth(endpoint, options = {}) {
        const token = authService.getToken();
        if (!token) {
            throw new Error('Not authenticated');
        }

        const headers = {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
            ...options.headers
        };

        const response = await fetch(endpoint, {
            ...options,
            headers
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Request failed' }));
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        // Handle 204 No Content
        if (response.status === 204) {
            return null;
        }

        return response.json();
    }

    // ==================== Dashboard Methods ====================

    /**
     * Create a new dashboard
     */
    async createDashboard(dashboardData) {
        return this._fetchWithAuth(`${this.baseUrl}`, {
            method: 'POST',
            body: JSON.stringify(dashboardData)
        });
    }

    /**
     * List all dashboards
     */
    async listDashboards(filters = {}) {
        const params = new URLSearchParams();
        if (filters.category) params.append('category', filters.category);
        if (filters.favorites_only) params.append('favorites_only', 'true');
        if (filters.skip) params.append('skip', filters.skip);
        if (filters.limit) params.append('limit', filters.limit);

        const url = `${this.baseUrl}${params.toString() ? '?' + params.toString() : ''}`;
        return this._fetchWithAuth(url);
    }

    /**
     * Get a specific dashboard
     */
    async getDashboard(dashboardId) {
        return this._fetchWithAuth(`${this.baseUrl}/${dashboardId}`);
    }

    /**
     * Update a dashboard
     */
    async updateDashboard(dashboardId, dashboardData) {
        return this._fetchWithAuth(`${this.baseUrl}/${dashboardId}`, {
            method: 'PUT',
            body: JSON.stringify(dashboardData)
        });
    }

    /**
     * Delete a dashboard
     */
    async deleteDashboard(dashboardId) {
        return this._fetchWithAuth(`${this.baseUrl}/${dashboardId}`, {
            method: 'DELETE'
        });
    }

    /**
     * Clone a dashboard
     */
    async cloneDashboard(dashboardId, newName) {
        return this._fetchWithAuth(`${this.baseUrl}/${dashboardId}/clone`, {
            method: 'POST',
            body: JSON.stringify({ name: newName })
        });
    }

    // ==================== Dashboard Page Methods ====================

    /**
     * Create a new page
     */
    async createPage(pageData) {
        return this._fetchWithAuth(`${this.baseUrl}/pages`, {
            method: 'POST',
            body: JSON.stringify(pageData)
        });
    }

    /**
     * Update a page
     */
    async updatePage(pageId, pageData) {
        return this._fetchWithAuth(`${this.baseUrl}/pages/${pageId}`, {
            method: 'PUT',
            body: JSON.stringify(pageData)
        });
    }

    /**
     * Delete a page
     */
    async deletePage(pageId) {
        return this._fetchWithAuth(`${this.baseUrl}/pages/${pageId}`, {
            method: 'DELETE'
        });
    }

    // ==================== Dashboard Widget Methods ====================

    /**
     * Create a new widget
     */
    async createWidget(widgetData) {
        return this._fetchWithAuth(`${this.baseUrl}/widgets`, {
            method: 'POST',
            body: JSON.stringify(widgetData)
        });
    }

    /**
     * Update a widget
     */
    async updateWidget(widgetId, widgetData) {
        return this._fetchWithAuth(`${this.baseUrl}/widgets/${widgetId}`, {
            method: 'PUT',
            body: JSON.stringify(widgetData)
        });
    }

    /**
     * Delete a widget
     */
    async deleteWidget(widgetId) {
        return this._fetchWithAuth(`${this.baseUrl}/widgets/${widgetId}`, {
            method: 'DELETE'
        });
    }

    /**
     * Bulk update widgets (for repositioning)
     */
    async bulkUpdateWidgets(updates) {
        return this._fetchWithAuth(`${this.baseUrl}/widgets/bulk-update`, {
            method: 'POST',
            body: JSON.stringify({ updates })
        });
    }

    // ==================== Widget Data Methods (Reuses Report Infrastructure) ====================

    /**
     * Get data for a widget
     * This reuses the report execution infrastructure on the backend
     */
    async getWidgetData(widgetId, parameters = {}, useCache = true) {
        return this._fetchWithAuth(`${this.baseUrl}/widgets/data`, {
            method: 'POST',
            body: JSON.stringify({
                widget_id: widgetId,
                parameters,
                use_cache: useCache
            })
        });
    }

    // ==================== Dashboard Sharing Methods ====================

    /**
     * Share a dashboard
     */
    async shareDashboard(shareData) {
        return this._fetchWithAuth(`${this.baseUrl}/shares`, {
            method: 'POST',
            body: JSON.stringify(shareData)
        });
    }

    // ==================== Dashboard Snapshot Methods ====================

    /**
     * Create a dashboard snapshot
     */
    async createSnapshot(snapshotData) {
        return this._fetchWithAuth(`${this.baseUrl}/snapshots`, {
            method: 'POST',
            body: JSON.stringify(snapshotData)
        });
    }

    // ==================== Helper Methods ====================

    /**
     * Get widget type icon
     */
    getWidgetTypeIcon(widgetType) {
        const icons = {
            'report_table': '📊',
            'chart': '📈',
            'kpi_card': '📌',
            'metric': '🔢',
            'text': '📝',
            'iframe': '🌐',
            'image': '🖼️',
            'filter_panel': '🔍'
        };
        return icons[widgetType] || '📦';
    }

    /**
     * Get widget type name
     */
    getWidgetTypeName(widgetType) {
        const names = {
            'report_table': 'Report Table',
            'chart': 'Chart',
            'kpi_card': 'KPI Card',
            'metric': 'Metric',
            'text': 'Text',
            'iframe': 'Embedded Page',
            'image': 'Image',
            'filter_panel': 'Filter Panel'
        };
        return names[widgetType] || 'Unknown';
    }

    /**
     * Validate widget position
     */
    validatePosition(position, layoutConfig = {}) {
        const columns = layoutConfig.columns || 12;
        const errors = [];

        if (position.x < 0 || position.x >= columns) {
            errors.push(`X position must be between 0 and ${columns - 1}`);
        }

        if (position.y < 0) {
            errors.push('Y position must be non-negative');
        }

        if (position.w <= 0 || position.w > columns) {
            errors.push(`Width must be between 1 and ${columns}`);
        }

        if (position.h <= 0) {
            errors.push('Height must be positive');
        }

        if (position.x + position.w > columns) {
            errors.push(`Widget extends beyond grid boundary (${columns} columns)`);
        }

        return errors;
    }

    /**
     * Calculate optimal widget position for new widget
     */
    calculateOptimalPosition(existingWidgets, defaultSize = { w: 4, h: 4 }, columns = 12) {
        // Create a grid to track occupied spaces
        const maxY = Math.max(0, ...existingWidgets.map(w => w.position.y + w.position.h));
        const grid = Array(maxY + 10).fill(null).map(() => Array(columns).fill(false));

        // Mark occupied spaces
        existingWidgets.forEach(widget => {
            const { x, y, w, h } = widget.position;
            for (let row = y; row < y + h; row++) {
                for (let col = x; col < x + w; col++) {
                    if (grid[row] && grid[row][col] !== undefined) {
                        grid[row][col] = true;
                    }
                }
            }
        });

        // Find first available spot
        for (let y = 0; y < grid.length; y++) {
            for (let x = 0; x <= columns - defaultSize.w; x++) {
                // Check if this spot can fit the widget
                let canFit = true;
                for (let row = y; row < y + defaultSize.h && row < grid.length; row++) {
                    for (let col = x; col < x + defaultSize.w; col++) {
                        if (grid[row][col]) {
                            canFit = false;
                            break;
                        }
                    }
                    if (!canFit) break;
                }

                if (canFit) {
                    return { x, y, ...defaultSize };
                }
            }
        }

        // If no spot found, add to bottom
        return { x: 0, y: maxY + 1, ...defaultSize };
    }

    /**
     * Get chart type options
     */
    getChartTypes() {
        return [
            { value: 'bar', label: 'Bar Chart', icon: '📊' },
            { value: 'line', label: 'Line Chart', icon: '📈' },
            { value: 'pie', label: 'Pie Chart', icon: '🥧' },
            { value: 'donut', label: 'Donut Chart', icon: '🍩' },
            { value: 'area', label: 'Area Chart', icon: '📉' },
            { value: 'scatter', label: 'Scatter Plot', icon: '⚫' },
            { value: 'gauge', label: 'Gauge', icon: '🎯' },
            { value: 'funnel', label: 'Funnel Chart', icon: '🔻' },
            { value: 'heatmap', label: 'Heatmap', icon: '🔥' }
        ];
    }

    /**
     * Get refresh interval options
     */
    getRefreshIntervals() {
        return [
            { value: 'none', label: 'No Auto-Refresh' },
            { value: '30s', label: 'Every 30 seconds' },
            { value: '1m', label: 'Every minute' },
            { value: '5m', label: 'Every 5 minutes' },
            { value: '15m', label: 'Every 15 minutes' },
            { value: '30m', label: 'Every 30 minutes' },
            { value: '1h', label: 'Every hour' }
        ];
    }

    /**
     * Parse refresh interval to milliseconds
     */
    parseRefreshInterval(interval) {
        const map = {
            'none': 0,
            '30s': 30 * 1000,
            '1m': 60 * 1000,
            '5m': 5 * 60 * 1000,
            '15m': 15 * 60 * 1000,
            '30m': 30 * 60 * 1000,
            '1h': 60 * 60 * 1000
        };
        return map[interval] || 0;
    }
}

// Create singleton instance
export const dashboardService = new DashboardService();
