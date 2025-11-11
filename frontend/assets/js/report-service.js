/**
 * Report Service - Singleton service for report operations
 *
 * Provides comprehensive API for:
 * - Report definition management (CRUD)
 * - Report execution and export
 * - Parameter lookup data
 * - Report scheduling
 * - Report templates
 */

import { apiFetch } from './api.js';

class ReportService {
    constructor() {
        if (ReportService.instance) {
            return ReportService.instance;
        }
        this.baseUrl = '/reports';
        ReportService.instance = this;
    }

    /**
     * Helper method to make authenticated API calls
     */
    async _fetchWithAuth(endpoint, options = {}) {
        const response = await apiFetch(endpoint, options);

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

    /**
     * Helper method for file downloads
     */
    async _downloadFile(endpoint, options = {}) {
        const response = await apiFetch(endpoint, options);

        if (!response.ok) {
            throw new Error(`Download failed: HTTP ${response.status}`);
        }

        return response;
    }

    // ==================== Report Definition Methods ====================

    /**
     * Create a new report definition
     */
    async createReportDefinition(reportData) {
        return this._fetchWithAuth(`${this.baseUrl}/definitions`, {
            method: 'POST',
            body: JSON.stringify(reportData)
        });
    }

    /**
     * List all report definitions
     */
    async listReportDefinitions(filters = {}) {
        const params = new URLSearchParams();
        if (filters.category) params.append('category', filters.category);
        if (filters.skip) params.append('skip', filters.skip);
        if (filters.limit) params.append('limit', filters.limit);

        const url = `${this.baseUrl}/definitions${params.toString() ? '?' + params.toString() : ''}`;
        return this._fetchWithAuth(url);
    }

    /**
     * Get a specific report definition
     */
    async getReportDefinition(reportId) {
        return this._fetchWithAuth(`${this.baseUrl}/definitions/${reportId}`);
    }

    /**
     * Update a report definition
     */
    async updateReportDefinition(reportId, reportData) {
        return this._fetchWithAuth(`${this.baseUrl}/definitions/${reportId}`, {
            method: 'PUT',
            body: JSON.stringify(reportData)
        });
    }

    /**
     * Delete a report definition
     */
    async deleteReportDefinition(reportId) {
        return this._fetchWithAuth(`${this.baseUrl}/definitions/${reportId}`, {
            method: 'DELETE'
        });
    }

    // ==================== Report Execution Methods ====================

    /**
     * Execute a report and get results
     */
    async executeReport(reportId, parameters = {}, useCache = true) {
        return this._fetchWithAuth(`${this.baseUrl}/execute`, {
            method: 'POST',
            body: JSON.stringify({
                report_definition_id: reportId,
                parameters,
                use_cache: useCache
            })
        });
    }

    /**
     * Execute a report and export to file
     */
    async executeAndExport(reportId, parameters = {}, exportFormat = 'pdf') {
        const response = await this._downloadFile(`${this.baseUrl}/execute/export`, {
            method: 'POST',
            body: JSON.stringify({
                report_definition_id: reportId,
                parameters,
                export_format: exportFormat
            })
        });

        // Get filename from Content-Disposition header
        const contentDisposition = response.headers.get('Content-Disposition');
        const filenameMatch = contentDisposition?.match(/filename="(.+)"/);
        const filename = filenameMatch ? filenameMatch[1] : `report.${exportFormat}`;

        // Convert to blob and trigger download
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        return { success: true, filename };
    }

    /**
     * Get execution history
     */
    async getExecutionHistory(reportId = null, skip = 0, limit = 50) {
        const params = new URLSearchParams();
        if (reportId) params.append('report_id', reportId);
        params.append('skip', skip);
        params.append('limit', limit);

        return this._fetchWithAuth(`${this.baseUrl}/executions/history?${params.toString()}`);
    }

    // ==================== Lookup Data Methods ====================

    /**
     * Get lookup data for a parameter
     */
    async getLookupData(entity, displayField, valueField, options = {}) {
        return this._fetchWithAuth(`${this.baseUrl}/lookup`, {
            method: 'POST',
            body: JSON.stringify({
                entity,
                display_field: displayField,
                value_field: valueField,
                filter_conditions: options.filterConditions,
                parent_value: options.parentValue,
                search: options.search,
                limit: options.limit || 100
            })
        });
    }

    // ==================== Report Schedule Methods ====================

    /**
     * Create a report schedule
     */
    async createReportSchedule(scheduleData) {
        return this._fetchWithAuth(`${this.baseUrl}/schedules`, {
            method: 'POST',
            body: JSON.stringify(scheduleData)
        });
    }

    /**
     * List report schedules
     */
    async listReportSchedules(reportId = null, skip = 0, limit = 100) {
        const params = new URLSearchParams();
        if (reportId) params.append('report_id', reportId);
        params.append('skip', skip);
        params.append('limit', limit);

        return this._fetchWithAuth(`${this.baseUrl}/schedules?${params.toString()}`);
    }

    /**
     * Update a report schedule
     */
    async updateReportSchedule(scheduleId, scheduleData) {
        return this._fetchWithAuth(`${this.baseUrl}/schedules/${scheduleId}`, {
            method: 'PUT',
            body: JSON.stringify(scheduleData)
        });
    }

    /**
     * Delete a report schedule
     */
    async deleteReportSchedule(scheduleId) {
        return this._fetchWithAuth(`${this.baseUrl}/schedules/${scheduleId}`, {
            method: 'DELETE'
        });
    }

    // ==================== Report Template Methods ====================

    /**
     * List available report templates
     */
    async listReportTemplates(category = null, skip = 0, limit = 100) {
        const params = new URLSearchParams();
        if (category) params.append('category', category);
        params.append('skip', skip);
        params.append('limit', limit);

        return this._fetchWithAuth(`${this.baseUrl}/templates?${params.toString()}`);
    }

    /**
     * Create a report from a template
     */
    async createFromTemplate(templateId, reportName) {
        const params = new URLSearchParams();
        params.append('name', reportName);

        return this._fetchWithAuth(`${this.baseUrl}/templates/${templateId}/use?${params.toString()}`, {
            method: 'POST'
        });
    }

    // ==================== Helper Methods ====================

    /**
     * Get parameter type for auto-detection
     */
    getParameterInputType(parameterType) {
        const typeMap = {
            'string': 'text',
            'integer': 'number',
            'decimal': 'number',
            'date': 'date',
            'datetime': 'datetime-local',
            'boolean': 'checkbox',
            'lookup': 'select',
            'multi_select': 'multi-select'
        };
        return typeMap[parameterType] || 'text';
    }

    /**
     * Validate parameter value based on validation rules
     */
    validateParameter(parameter, value) {
        const errors = [];

        // Check required
        if (parameter.required && (value === null || value === undefined || value === '')) {
            errors.push(`${parameter.label} is required`);
            return errors;
        }

        // Skip validation if value is empty and not required
        if (!value && !parameter.required) {
            return errors;
        }

        // Apply validation rules
        if (parameter.validation_rules) {
            for (const rule of parameter.validation_rules) {
                switch (rule.rule_type) {
                    case 'min':
                        if (parseFloat(value) < parseFloat(rule.value)) {
                            errors.push(rule.error_message || `${parameter.label} must be at least ${rule.value}`);
                        }
                        break;
                    case 'max':
                        if (parseFloat(value) > parseFloat(rule.value)) {
                            errors.push(rule.error_message || `${parameter.label} must be at most ${rule.value}`);
                        }
                        break;
                    case 'regex':
                        const regex = new RegExp(rule.value);
                        if (!regex.test(value)) {
                            errors.push(rule.error_message || `${parameter.label} format is invalid`);
                        }
                        break;
                    case 'minLength':
                        if (value.length < rule.value) {
                            errors.push(rule.error_message || `${parameter.label} must be at least ${rule.value} characters`);
                        }
                        break;
                    case 'maxLength':
                        if (value.length > rule.value) {
                            errors.push(rule.error_message || `${parameter.label} must be at most ${rule.value} characters`);
                        }
                        break;
                }
            }
        }

        return errors;
    }

    /**
     * Build query filter from parameters
     */
    buildFilterFromParameters(reportDefinition, parameterValues) {
        if (!reportDefinition.query_config || !reportDefinition.query_config.filters) {
            return null;
        }

        // This is a helper to work with filter conditions that reference parameters
        const processCondition = (condition) => {
            if (condition.parameter && parameterValues[condition.parameter] !== undefined) {
                return {
                    ...condition,
                    value: parameterValues[condition.parameter]
                };
            }
            return condition;
        };

        return reportDefinition.query_config.filters;
    }
}

// Create singleton instance
export const reportService = new ReportService();
