/**
 * Report Viewer Component
 *
 * Displays report with parameter inputs and allows execution and export
 */

import { reportService } from '../assets/js/report-service.js';
import { ReportParameterInput } from './report-parameter-input.js';
import { showNotification } from '../assets/js/notifications.js';

export class ReportViewer {
    constructor(container, reportId) {
        this.container = container;
        this.reportId = reportId;
        this.reportDefinition = null;
        this.parameterInput = null;
        this.currentData = null;
    }

    async render() {
        try {
            // Load report definition
            this.reportDefinition = await reportService.getReportDefinition(this.reportId);

            this.container.innerHTML = `
                <div class="report-viewer">
                    <!-- Header -->
                    <div class="report-header bg-white shadow-sm p-6 mb-4 rounded">
                        <div class="flex justify-between items-start">
                            <div>
                                <h2 class="text-2xl font-bold text-gray-800">${this.reportDefinition.name}</h2>
                                ${this.reportDefinition.description ? `
                                    <p class="text-gray-600 mt-2">${this.reportDefinition.description}</p>
                                ` : ''}
                                ${this.reportDefinition.category ? `
                                    <span class="inline-block mt-2 px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full">
                                        ${this.reportDefinition.category}
                                    </span>
                                ` : ''}
                            </div>
                            <div class="flex gap-2">
                                <button id="edit-report-btn" class="btn-secondary btn-sm">
                                    ✏️ Edit
                                </button>
                            </div>
                        </div>
                    </div>

                    <!-- Parameters Section -->
                    ${this.reportDefinition.parameters && this.reportDefinition.parameters.length > 0 ? `
                        <div class="parameters-section bg-white shadow-sm p-6 mb-4 rounded">
                            <div id="parameters-container"></div>
                        </div>
                    ` : ''}

                    <!-- Actions Bar -->
                    <div class="actions-bar bg-white shadow-sm p-4 mb-4 rounded flex justify-between items-center">
                        <div class="flex gap-2">
                            <button id="run-report-btn" class="btn-primary">
                                ▶️ Run Report
                            </button>
                            <button id="refresh-btn" class="btn-secondary" disabled>
                                🔄 Refresh
                            </button>
                        </div>
                        <div class="flex gap-2">
                            <label class="text-sm font-medium text-gray-700 mr-2">Export as:</label>
                            <button class="btn-sm btn-outline export-btn" data-format="pdf">
                                📄 PDF
                            </button>
                            <button class="btn-sm btn-outline export-btn" data-format="excel_formatted">
                                📊 Excel
                            </button>
                            <button class="btn-sm btn-outline export-btn" data-format="excel_raw">
                                📋 Raw Data
                            </button>
                            <button class="btn-sm btn-outline export-btn" data-format="csv">
                                📝 CSV
                            </button>
                        </div>
                    </div>

                    <!-- Results Section -->
                    <div id="results-container" class="results-section bg-white shadow-sm p-6 rounded">
                        <div class="text-center py-12 text-gray-500">
                            <p>Click "Run Report" to see results</p>
                        </div>
                    </div>
                </div>
            `;

            // Render parameters if any
            if (this.reportDefinition.parameters && this.reportDefinition.parameters.length > 0) {
                const parametersContainer = document.getElementById('parameters-container');
                this.parameterInput = new ReportParameterInput(
                    parametersContainer,
                    this.reportDefinition.parameters,
                    (values) => this._onParametersApplied(values)
                );
                await this.parameterInput.render();
            }

            this._attachEventListeners();

        } catch (error) {
            this.container.innerHTML = `
                <div class="bg-red-50 border border-red-200 text-red-700 p-4 rounded">
                    <p class="font-bold">Error Loading Report</p>
                    <p class="text-sm mt-1">${error.message}</p>
                </div>
            `;
        }
    }

    _attachEventListeners() {
        // Run report button
        const runBtn = document.getElementById('run-report-btn');
        if (runBtn) {
            runBtn.addEventListener('click', () => this._runReport());
        }

        // Refresh button
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this._runReport(false));
        }

        // Export buttons
        const exportBtns = document.querySelectorAll('.export-btn');
        exportBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const format = e.target.closest('.export-btn').dataset.format;
                this._exportReport(format);
            });
        });

        // Edit button
        const editBtn = document.getElementById('edit-report-btn');
        if (editBtn) {
            editBtn.addEventListener('click', () => {
                window.location.hash = `#/reports/designer/${this.reportId}`;
            });
        }
    }

    _onParametersApplied(values) {
        // Parameters have been applied, could auto-run or just store
        console.log('Parameters applied:', values);
    }

    async _runReport(useCache = true) {
        const resultsContainer = document.getElementById('results-container');

        // Get parameter values
        let paramValues = {};
        if (this.parameterInput) {
            const errors = this.parameterInput.validate();
            if (errors.length > 0) {
                showNotification('Please fix parameter errors before running', 'error');
                return;
            }
            paramValues = this.parameterInput.getValues();
        }

        // Show loading
        resultsContainer.innerHTML = `
            <div class="text-center py-12">
                <div class="spinner mb-4"></div>
                <p class="text-gray-600">Running report...</p>
            </div>
        `;

        try {
            const execution = await reportService.executeReport(
                this.reportId,
                paramValues,
                useCache
            );

            if (execution.status === 'completed') {
                // Enable refresh button
                const refreshBtn = document.getElementById('refresh-btn');
                if (refreshBtn) refreshBtn.disabled = false;

                // For now, show a success message and execution stats
                // In production, you'd fetch and display the actual data
                resultsContainer.innerHTML = `
                    <div class="text-center py-12">
                        <div class="text-green-600 text-6xl mb-4">✓</div>
                        <p class="text-xl font-bold text-gray-800 mb-2">Report Executed Successfully</p>
                        <div class="text-sm text-gray-600 space-y-1">
                            <p><strong>Rows:</strong> ${execution.row_count}</p>
                            <p><strong>Execution Time:</strong> ${execution.execution_time_ms}ms</p>
                        </div>
                        <p class="mt-4 text-gray-600">Use the export buttons above to download the report</p>
                    </div>
                `;

                showNotification('Report executed successfully!', 'success');
            } else if (execution.status === 'failed') {
                resultsContainer.innerHTML = `
                    <div class="bg-red-50 border border-red-200 text-red-700 p-4 rounded">
                        <p class="font-bold">Report Execution Failed</p>
                        <p class="text-sm mt-1">${execution.error_message}</p>
                    </div>
                `;
                showNotification('Report execution failed', 'error');
            }
        } catch (error) {
            resultsContainer.innerHTML = `
                <div class="bg-red-50 border border-red-200 text-red-700 p-4 rounded">
                    <p class="font-bold">Error</p>
                    <p class="text-sm mt-1">${error.message}</p>
                </div>
            `;
            showNotification('Failed to run report: ' + error.message, 'error');
        }
    }

    async _exportReport(format) {
        // Get parameter values
        let paramValues = {};
        if (this.parameterInput) {
            const errors = this.parameterInput.validate();
            if (errors.length > 0) {
                showNotification('Please fix parameter errors before exporting', 'error');
                return;
            }
            paramValues = this.parameterInput.getValues();
        }

        try {
            showNotification('Preparing export...', 'info');
            await reportService.executeAndExport(this.reportId, paramValues, format);
            showNotification('Report exported successfully!', 'success');
        } catch (error) {
            showNotification('Failed to export report: ' + error.message, 'error');
        }
    }
}
