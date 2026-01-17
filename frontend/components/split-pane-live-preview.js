/**
 * Split-Pane Live Preview Component
 *
 * Real-time preview of report as it's being designed with split-pane layout.
 */

import { apiFetch } from '../assets/js/api.js';
import { showNotification } from '../assets/js/notifications.js';

export class SplitPaneLivePreview {
    constructor(container, options = {}) {
        this.container = container;
        this.options = options;
        this.isVisible = false;
        this.previewData = null;
        this.reportConfig = {};

        this.init();
    }

    init() {
        this.render();
    }

    render() {
        this.container.innerHTML = `
            <div class="split-pane-live-preview">
                <!-- Toggle Button -->
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-lg font-semibold text-gray-900">Live Preview</h3>
                    <button id="toggle-preview" class="btn btn-sm btn-secondary">
                        <i class="ph ${this.isVisible ? 'ph-eye-slash' : 'ph-eye'} mr-1"></i>
                        ${this.isVisible ? 'Hide' : 'Show'} Preview
                    </button>
                </div>

                <!-- Preview Container -->
                <div id="preview-container" class="${this.isVisible ? '' : 'hidden'}">
                    <div class="border border-gray-200 rounded-lg bg-white p-6 min-h-[400px]">
                        <div id="preview-content">
                            ${this.renderPreview()}
                        </div>
                    </div>

                    <!-- Refresh Controls -->
                    <div class="mt-4 flex justify-between items-center">
                        <div class="flex items-center gap-2">
                            <input type="checkbox" id="auto-refresh" class="checkbox" ${this.options.autoRefresh ? 'checked' : ''} />
                            <label for="auto-refresh" class="text-sm text-gray-700">Auto-refresh on changes</label>
                        </div>
                        <button id="refresh-preview" class="btn btn-sm btn-secondary">
                            <i class="ph ph-arrow-clockwise mr-1"></i>
                            Refresh
                        </button>
                    </div>
                </div>
            </div>
        `;

        this.attachEventListeners();
    }

    renderPreview() {
        if (!this.previewData) {
            return `
                <div class="text-center py-12">
                    <i class="ph ph-chart-bar text-6xl text-gray-300 mb-4"></i>
                    <p class="text-gray-500">Configure your report to see a preview</p>
                    <button onclick="splitPaneLivePreview.loadPreview()" class="btn btn-primary mt-4">
                        <i class="ph ph-eye mr-2"></i>
                        Load Preview
                    </button>
                </div>
            `;
        }

        return `
            <div class="preview-report">
                <h2 class="text-xl font-bold text-gray-900 mb-4">${this.escapeHtml(this.reportConfig.name || 'Report Preview')}</h2>
                ${this.renderPreviewTable()}
            </div>
        `;
    }

    renderPreviewTable() {
        if (!this.previewData || !this.previewData.data || this.previewData.data.length === 0) {
            return '<p class="text-gray-500">No data to preview</p>';
        }

        const columns = this.previewData.columns || Object.keys(this.previewData.data[0] || {});

        return `
            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                        <tr>
                            ${columns.map(col => `
                                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    ${this.escapeHtml(col)}
                                </th>
                            `).join('')}
                        </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200">
                        ${this.previewData.data.slice(0, 10).map(row => `
                            <tr>
                                ${columns.map(col => `
                                    <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                                        ${this.escapeHtml(row[col] || '-')}
                                    </td>
                                `).join('')}
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
            ${this.previewData.data.length > 10 ? `
                <p class="text-sm text-gray-500 mt-4">Showing 10 of ${this.previewData.data.length} rows</p>
            ` : ''}
        `;
    }

    attachEventListeners() {
        document.getElementById('toggle-preview')?.addEventListener('click', () => {
            this.togglePreview();
        });

        document.getElementById('refresh-preview')?.addEventListener('click', () => {
            this.loadPreview();
        });

        document.getElementById('auto-refresh')?.addEventListener('change', (e) => {
            this.options.autoRefresh = e.target.checked;
        });
    }

    togglePreview() {
        this.isVisible = !this.isVisible;
        this.render();
    }

    async loadPreview() {
        const content = document.getElementById('preview-content');
        if (!content) return;

        content.innerHTML = '<p class="text-center py-12 text-gray-500">Loading preview...</p>';

        try {
            // Build preview request from current report config
            const response = await apiFetch('/api/v1/reports/preview', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    ...this.reportConfig,
                    limit: 10
                })
            });

            if (!response.ok) {
                throw new Error('Failed to load preview');
            }

            this.previewData = await response.json();
            content.innerHTML = this.renderPreviewTable();
        } catch (error) {
            console.error('Failed to load preview:', error);
            content.innerHTML = `
                <div class="text-center py-12">
                    <i class="ph ph-warning text-4xl text-red-500 mb-4"></i>
                    <p class="text-red-600">Failed to load preview</p>
                    <p class="text-sm text-gray-500 mt-2">${error.message}</p>
                </div>
            `;
        }
    }

    updateReportConfig(config) {
        this.reportConfig = config;

        if (this.options.autoRefresh && this.isVisible) {
            this.loadPreview();
        }
    }

    show() {
        this.isVisible = true;
        this.render();
    }

    hide() {
        this.isVisible = false;
        this.render();
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}
