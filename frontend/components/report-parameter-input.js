/**
 * Report Parameter Input Component
 *
 * Auto-detects appropriate input components based on parameter types:
 * - String → Text input
 * - Integer/Decimal → Number input
 * - Date/DateTime → Date picker
 * - Boolean → Checkbox
 * - Lookup → Dropdown with search
 * - Multi-select → Multi-select dropdown
 */

import { reportService } from '../assets/js/report-service.js';

export class ReportParameterInput {
    constructor(container, parameters, onValuesChange = null) {
        this.container = container;
        this.parameters = parameters || [];
        this.values = {};
        this.lookupCache = {};
        this.onValuesChange = onValuesChange;

        // Initialize default values
        this.parameters.forEach(param => {
            if (param.default_value !== null && param.default_value !== undefined) {
                this.values[param.name] = param.default_value;
            }
        });
    }

    async render() {
        if (this.parameters.length === 0) {
            this.container.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <p>This report has no parameters</p>
                </div>
            `;
            return;
        }

        // Sort parameters by order
        const sortedParams = [...this.parameters].sort((a, b) => (a.order || 0) - (b.order || 0));

        this.container.innerHTML = `
            <div class="report-parameters space-y-4">
                <h3 class="text-lg font-bold text-gray-800 mb-4">Report Parameters</h3>
                ${sortedParams.map(param => this._renderParameter(param)).join('')}
                <div class="flex justify-end gap-3 pt-4 border-t">
                    <button id="reset-params-btn" class="btn-secondary">
                        Reset to Defaults
                    </button>
                    <button id="apply-params-btn" class="btn-primary">
                        Apply Parameters
                    </button>
                </div>
            </div>
        `;

        await this._loadLookupData();
        this._attachEventListeners();
    }

    _renderParameter(param) {
        const inputId = `param-${param.name}`;
        const required = param.required ? 'required' : '';
        const requiredMark = param.required ? '<span class="text-red-500">*</span>' : '';

        let inputHtml = '';

        switch (param.parameter_type) {
            case 'string':
                inputHtml = `
                    <input type="text" id="${inputId}" name="${param.name}"
                        class="input-field param-input"
                        value="${this.values[param.name] || ''}"
                        placeholder="${param.description || ''}"
                        ${required}>
                `;
                break;

            case 'integer':
                inputHtml = `
                    <input type="number" id="${inputId}" name="${param.name}"
                        class="input-field param-input"
                        value="${this.values[param.name] || ''}"
                        step="1"
                        placeholder="${param.description || ''}"
                        ${required}>
                `;
                break;

            case 'decimal':
                inputHtml = `
                    <input type="number" id="${inputId}" name="${param.name}"
                        class="input-field param-input"
                        value="${this.values[param.name] || ''}"
                        step="0.01"
                        placeholder="${param.description || ''}"
                        ${required}>
                `;
                break;

            case 'date':
                inputHtml = `
                    <input type="date" id="${inputId}" name="${param.name}"
                        class="input-field param-input"
                        value="${this.values[param.name] || ''}"
                        ${required}>
                `;
                break;

            case 'datetime':
                inputHtml = `
                    <input type="datetime-local" id="${inputId}" name="${param.name}"
                        class="input-field param-input"
                        value="${this.values[param.name] || ''}"
                        ${required}>
                `;
                break;

            case 'boolean':
                inputHtml = `
                    <div class="flex items-center">
                        <input type="checkbox" id="${inputId}" name="${param.name}"
                            class="param-input mr-2"
                            ${this.values[param.name] ? 'checked' : ''}>
                        <label for="${inputId}" class="text-sm text-gray-700">
                            ${param.description || 'Enable this option'}
                        </label>
                    </div>
                `;
                break;

            case 'lookup':
                inputHtml = `
                    <select id="${inputId}" name="${param.name}"
                        class="input-field param-input param-lookup"
                        data-entity="${param.lookup_config?.entity || ''}"
                        data-display-field="${param.lookup_config?.display_field || ''}"
                        data-value-field="${param.lookup_config?.value_field || ''}"
                        data-depends-on="${param.lookup_config?.depends_on || ''}"
                        ${required}>
                        <option value="">-- Select ${param.label} --</option>
                        <!-- Options will be loaded dynamically -->
                    </select>
                    ${param.lookup_config?.depends_on ? `
                        <p class="text-xs text-gray-500 mt-1">
                            This field depends on: ${param.lookup_config.depends_on}
                        </p>
                    ` : ''}
                `;
                break;

            case 'multi_select':
                inputHtml = `
                    <select id="${inputId}" name="${param.name}"
                        class="input-field param-input param-lookup"
                        data-entity="${param.lookup_config?.entity || ''}"
                        data-display-field="${param.lookup_config?.display_field || ''}"
                        data-value-field="${param.lookup_config?.value_field || ''}"
                        multiple
                        size="5"
                        ${required}>
                        <!-- Options will be loaded dynamically -->
                    </select>
                    <p class="text-xs text-gray-500 mt-1">Hold Ctrl/Cmd to select multiple</p>
                `;
                break;

            default:
                inputHtml = `
                    <input type="text" id="${inputId}" name="${param.name}"
                        class="input-field param-input"
                        value="${this.values[param.name] || ''}"
                        ${required}>
                `;
        }

        return `
            <div class="parameter-field" data-param-name="${param.name}">
                <label for="${inputId}" class="block text-sm font-medium text-gray-700 mb-1">
                    ${param.label} ${requiredMark}
                </label>
                ${inputHtml}
                ${param.description && param.parameter_type !== 'boolean' ? `
                    <p class="text-xs text-gray-500 mt-1">${param.description}</p>
                ` : ''}
                <div class="param-error text-red-600 text-xs mt-1 hidden"></div>
            </div>
        `;
    }

    async _loadLookupData() {
        // Load data for all lookup and multi-select parameters
        const lookupParams = this.parameters.filter(p =>
            p.parameter_type === 'lookup' || p.parameter_type === 'multi_select'
        );

        for (const param of lookupParams) {
            if (!param.lookup_config) continue;

            try {
                const cacheKey = `${param.lookup_config.entity}_${param.lookup_config.display_field}_${param.lookup_config.value_field}`;

                // Check cache first
                if (!this.lookupCache[cacheKey]) {
                    const result = await reportService.getLookupData(
                        param.lookup_config.entity,
                        param.lookup_config.display_field,
                        param.lookup_config.value_field
                    );
                    this.lookupCache[cacheKey] = result.items;
                }

                // Populate select element
                const selectElement = document.querySelector(`[name="${param.name}"]`);
                if (selectElement) {
                    const items = this.lookupCache[cacheKey];
                    items.forEach(item => {
                        const option = document.createElement('option');
                        option.value = item.value;
                        option.textContent = item.label;
                        if (this.values[param.name] === item.value) {
                            option.selected = true;
                        }
                        selectElement.appendChild(option);
                    });
                }
            } catch (error) {
                console.error(`Failed to load lookup data for ${param.name}:`, error);
            }
        }
    }

    _attachEventListeners() {
        // Attach change listeners to all inputs
        const inputs = this.container.querySelectorAll('.param-input');
        inputs.forEach(input => {
            input.addEventListener('change', (e) => {
                this._handleInputChange(e);
            });
        });

        // Cascading lookups - when a parent parameter changes, reload dependent lookups
        const lookupInputs = this.container.querySelectorAll('.param-lookup');
        lookupInputs.forEach(input => {
            const dependsOn = input.dataset.dependsOn;
            if (dependsOn) {
                const parentInput = this.container.querySelector(`[name="${dependsOn}"]`);
                if (parentInput) {
                    parentInput.addEventListener('change', async () => {
                        await this._reloadDependentLookup(input);
                    });
                }
            }
        });

        // Reset button
        const resetBtn = document.getElementById('reset-params-btn');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => this._resetParameters());
        }

        // Apply button
        const applyBtn = document.getElementById('apply-params-btn');
        if (applyBtn) {
            applyBtn.addEventListener('click', () => this._applyParameters());
        }
    }

    _handleInputChange(event) {
        const input = event.target;
        const paramName = input.name;
        let value;

        if (input.type === 'checkbox') {
            value = input.checked;
        } else if (input.type === 'number') {
            value = input.value ? parseFloat(input.value) : null;
        } else if (input.multiple) {
            // Multi-select
            value = Array.from(input.selectedOptions).map(opt => opt.value);
        } else {
            value = input.value;
        }

        this.values[paramName] = value;

        // Clear any previous errors
        const errorElement = input.closest('.parameter-field').querySelector('.param-error');
        if (errorElement) {
            errorElement.classList.add('hidden');
        }
    }

    async _reloadDependentLookup(selectElement) {
        const paramName = selectElement.name;
        const param = this.parameters.find(p => p.name === paramName);
        if (!param || !param.lookup_config) return;

        const dependsOn = param.lookup_config.depends_on;
        const parentValue = this.values[dependsOn];

        if (!parentValue) {
            // Clear options if parent has no value
            selectElement.innerHTML = `<option value="">-- Select ${param.label} --</option>`;
            return;
        }

        try {
            const result = await reportService.getLookupData(
                param.lookup_config.entity,
                param.lookup_config.display_field,
                param.lookup_config.value_field,
                { parentValue }
            );

            // Repopulate select
            selectElement.innerHTML = `<option value="">-- Select ${param.label} --</option>`;
            result.items.forEach(item => {
                const option = document.createElement('option');
                option.value = item.value;
                option.textContent = item.label;
                selectElement.appendChild(option);
            });
        } catch (error) {
            console.error(`Failed to reload dependent lookup for ${paramName}:`, error);
        }
    }

    _resetParameters() {
        // Reset to default values
        this.values = {};
        this.parameters.forEach(param => {
            if (param.default_value !== null && param.default_value !== undefined) {
                this.values[param.name] = param.default_value;
            }
        });

        // Re-render
        this.render();
    }

    _applyParameters() {
        // Validate all parameters
        const errors = this._validateParameters();

        if (errors.length > 0) {
            // Display errors
            errors.forEach(error => {
                const field = this.container.querySelector(`[data-param-name="${error.paramName}"]`);
                if (field) {
                    const errorElement = field.querySelector('.param-error');
                    if (errorElement) {
                        errorElement.textContent = error.message;
                        errorElement.classList.remove('hidden');
                    }
                }
            });
            return;
        }

        // Call the callback with validated values
        if (this.onValuesChange) {
            this.onValuesChange(this.values);
        }
    }

    _validateParameters() {
        const errors = [];

        this.parameters.forEach(param => {
            const value = this.values[param.name];
            const paramErrors = reportService.validateParameter(param, value);

            paramErrors.forEach(errorMsg => {
                errors.push({
                    paramName: param.name,
                    message: errorMsg
                });
            });
        });

        return errors;
    }

    /**
     * Get current parameter values
     */
    getValues() {
        return { ...this.values };
    }

    /**
     * Set parameter values programmatically
     */
    setValues(values) {
        this.values = { ...this.values, ...values };
        this.render();
    }

    /**
     * Validate without applying
     */
    validate() {
        return this._validateParameters();
    }
}
