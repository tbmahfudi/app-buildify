/**
 * FormBuilder Component
 *
 * Dynamic form builder for create/edit modals
 */

export class FormBuilder {
    constructor(config) {
        this.formId = config.formId;
        this.fields = config.fields || [];
        this.submitLabel = config.submitLabel || 'Submit';
        this.cancelLabel = config.cancelLabel || 'Cancel';
        this.onSubmit = config.onSubmit || null;
        this.onCancel = config.onCancel || null;
        this.values = config.values || {};
        this.mode = config.mode || 'create'; // 'create' or 'edit'
    }

    /**
     * Render the form
     */
    render(containerId) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container ${containerId} not found`);
            return;
        }

        let formHtml = `
            <form id="${this.formId}" class="space-y-4">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        `;

        this.fields.forEach(field => {
            const fieldHtml = this.renderField(field);
            const fullWidth = field.fullWidth || field.type === 'textarea' || field.type === 'editor';

            if (fullWidth) {
                formHtml += `<div class="md:col-span-2">${fieldHtml}</div>`;
            } else {
                formHtml += `<div>${fieldHtml}</div>`;
            }
        });

        formHtml += `
                </div>
                <div class="flex justify-end gap-3 mt-6 pt-4 border-t border-gray-200">
                    <button
                        type="button"
                        id="${this.formId}-cancel"
                        class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
                    >
                        ${this.cancelLabel}
                    </button>
                    <button
                        type="submit"
                        id="${this.formId}-submit"
                        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center gap-2"
                    >
                        <i class="ph ph-check"></i>
                        ${this.submitLabel}
                    </button>
                </div>
            </form>
        `;

        container.innerHTML = formHtml;
        this.attachEventListeners();
        this.populateValues();
    }

    /**
     * Render a single field
     */
    renderField(field) {
        const required = field.required ? 'required' : '';
        const disabled = field.disabled ? 'disabled' : '';
        const value = this.values[field.name] || field.defaultValue || '';
        const placeholder = field.placeholder || '';
        const helpText = field.helpText || '';

        let fieldHtml = `
            <div class="form-field">
                <label for="${this.formId}-${field.name}" class="block text-sm font-medium text-gray-700 mb-1">
                    ${field.label}
                    ${field.required ? '<span class="text-red-500">*</span>' : ''}
                </label>
        `;

        switch (field.type) {
            case 'text':
            case 'email':
            case 'number':
            case 'date':
            case 'datetime-local':
            case 'time':
                fieldHtml += `
                    <input
                        type="${field.type}"
                        id="${this.formId}-${field.name}"
                        name="${field.name}"
                        value="${value}"
                        placeholder="${placeholder}"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        ${required}
                        ${disabled}
                        ${field.min !== undefined ? `min="${field.min}"` : ''}
                        ${field.max !== undefined ? `max="${field.max}"` : ''}
                        ${field.step !== undefined ? `step="${field.step}"` : ''}
                    />
                `;
                break;

            case 'textarea':
                fieldHtml += `
                    <textarea
                        id="${this.formId}-${field.name}"
                        name="${field.name}"
                        placeholder="${placeholder}"
                        rows="${field.rows || 3}"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        ${required}
                        ${disabled}
                    >${value}</textarea>
                `;
                break;

            case 'select':
                fieldHtml += `
                    <select
                        id="${this.formId}-${field.name}"
                        name="${field.name}"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        ${required}
                        ${disabled}
                    >
                        ${field.placeholder ? `<option value="">${field.placeholder}</option>` : ''}
                        ${(field.options || []).map(option => {
                            const optionValue = typeof option === 'object' ? option.value : option;
                            const optionLabel = typeof option === 'object' ? option.label : option;
                            const selected = value == optionValue ? 'selected' : '';
                            return `<option value="${optionValue}" ${selected}>${optionLabel}</option>`;
                        }).join('')}
                    </select>
                `;
                break;

            case 'checkbox':
                const checked = value ? 'checked' : '';
                fieldHtml += `
                    <div class="flex items-center">
                        <input
                            type="checkbox"
                            id="${this.formId}-${field.name}"
                            name="${field.name}"
                            value="1"
                            class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                            ${checked}
                            ${disabled}
                        />
                        <label for="${this.formId}-${field.name}" class="ml-2 text-sm text-gray-700">
                            ${field.checkboxLabel || field.label}
                        </label>
                    </div>
                `;
                break;

            case 'radio':
                fieldHtml += `
                    <div class="space-y-2">
                        ${(field.options || []).map(option => {
                            const optionValue = typeof option === 'object' ? option.value : option;
                            const optionLabel = typeof option === 'object' ? option.label : option;
                            const checked = value == optionValue ? 'checked' : '';
                            return `
                                <div class="flex items-center">
                                    <input
                                        type="radio"
                                        id="${this.formId}-${field.name}-${optionValue}"
                                        name="${field.name}"
                                        value="${optionValue}"
                                        class="border-gray-300 text-blue-600 focus:ring-blue-500"
                                        ${checked}
                                        ${disabled}
                                    />
                                    <label for="${this.formId}-${field.name}-${optionValue}" class="ml-2 text-sm text-gray-700">
                                        ${optionLabel}
                                    </label>
                                </div>
                            `;
                        }).join('')}
                    </div>
                `;
                break;

            case 'file':
                fieldHtml += `
                    <input
                        type="file"
                        id="${this.formId}-${field.name}"
                        name="${field.name}"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        ${field.accept ? `accept="${field.accept}"` : ''}
                        ${field.multiple ? 'multiple' : ''}
                        ${disabled}
                    />
                `;
                break;

            case 'hidden':
                return `<input type="hidden" id="${this.formId}-${field.name}" name="${field.name}" value="${value}" />`;

            default:
                fieldHtml += `
                    <input
                        type="text"
                        id="${this.formId}-${field.name}"
                        name="${field.name}"
                        value="${value}"
                        placeholder="${placeholder}"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        ${required}
                        ${disabled}
                    />
                `;
        }

        if (helpText) {
            fieldHtml += `<p class="mt-1 text-sm text-gray-500">${helpText}</p>`;
        }

        fieldHtml += '</div>';
        return fieldHtml;
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        const form = document.getElementById(this.formId);
        if (!form) return;

        // Submit
        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            if (this.onSubmit) {
                const formData = this.getFormData();
                const submitBtn = document.getElementById(`${this.formId}-submit`);

                // Disable button and show loading state
                if (submitBtn) {
                    submitBtn.disabled = true;
                    submitBtn.innerHTML = `
                        <div class="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                        <span>Saving...</span>
                    `;
                }

                try {
                    await this.onSubmit(formData);
                } catch (error) {
                    console.error('Form submission error:', error);
                    this.showError(error.message || 'An error occurred');
                } finally {
                    // Restore button state
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = `
                            <i class="ph ph-check"></i>
                            ${this.submitLabel}
                        `;
                    }
                }
            }
        });

        // Cancel
        const cancelBtn = document.getElementById(`${this.formId}-cancel`);
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                if (this.onCancel) {
                    this.onCancel();
                }
            });
        }

        // Field-specific listeners
        this.fields.forEach(field => {
            if (field.onChange) {
                const element = document.getElementById(`${this.formId}-${field.name}`);
                if (element) {
                    element.addEventListener('change', (e) => {
                        field.onChange(e.target.value, this.getFormData());
                    });
                }
            }
        });
    }

    /**
     * Populate form values
     */
    populateValues() {
        if (!this.values || Object.keys(this.values).length === 0) {
            return;
        }

        this.fields.forEach(field => {
            const element = document.getElementById(`${this.formId}-${field.name}`);
            if (!element) return;

            const value = this.values[field.name];
            if (value === undefined || value === null) return;

            if (field.type === 'checkbox') {
                element.checked = !!value;
            } else if (field.type === 'radio') {
                const radioBtn = document.querySelector(`input[name="${field.name}"][value="${value}"]`);
                if (radioBtn) {
                    radioBtn.checked = true;
                }
            } else {
                element.value = value;
            }
        });
    }

    /**
     * Get form data
     */
    getFormData() {
        const formData = {};

        this.fields.forEach(field => {
            const element = document.getElementById(`${this.formId}-${field.name}`);
            if (!element) return;

            if (field.type === 'checkbox') {
                formData[field.name] = element.checked;
            } else if (field.type === 'number') {
                formData[field.name] = element.value ? parseFloat(element.value) : null;
            } else if (field.type === 'file') {
                formData[field.name] = element.files;
            } else {
                formData[field.name] = element.value;
            }
        });

        return formData;
    }

    /**
     * Set form values
     */
    setValues(values) {
        this.values = values;
        this.populateValues();
    }

    /**
     * Reset form
     */
    reset() {
        const form = document.getElementById(this.formId);
        if (form) {
            form.reset();
        }
        this.values = {};
    }

    /**
     * Validate form
     */
    validate() {
        const form = document.getElementById(this.formId);
        if (!form) return false;

        // Use HTML5 validation
        if (!form.checkValidity()) {
            form.reportValidity();
            return false;
        }

        // Custom validation
        for (const field of this.fields) {
            if (field.validate) {
                const element = document.getElementById(`${this.formId}-${field.name}`);
                const value = element ? element.value : null;
                const error = field.validate(value, this.getFormData());

                if (error) {
                    this.showFieldError(field.name, error);
                    return false;
                }
            }
        }

        return true;
    }

    /**
     * Show field error
     */
    showFieldError(fieldName, message) {
        const element = document.getElementById(`${this.formId}-${fieldName}`);
        if (!element) return;

        // Add error styling
        element.classList.add('border-red-500', 'focus:ring-red-500', 'focus:border-red-500');

        // Show error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'field-error text-red-500 text-sm mt-1';
        errorDiv.textContent = message;

        const existingError = element.parentElement.querySelector('.field-error');
        if (existingError) {
            existingError.remove();
        }

        element.parentElement.appendChild(errorDiv);

        // Remove error on input
        element.addEventListener('input', () => {
            element.classList.remove('border-red-500', 'focus:ring-red-500', 'focus:border-red-500');
            errorDiv.remove();
        }, { once: true });
    }

    /**
     * Show general error
     */
    showError(message) {
        const form = document.getElementById(this.formId);
        if (!form) return;

        const errorDiv = document.createElement('div');
        errorDiv.className = 'bg-red-50 border-l-4 border-red-500 p-4 mb-4';
        errorDiv.innerHTML = `
            <div class="flex items-start">
                <i class="ph-duotone ph-warning-circle text-red-500 text-xl mr-3"></i>
                <div>
                    <p class="text-red-700 font-medium">Error</p>
                    <p class="text-red-600 text-sm">${message}</p>
                </div>
            </div>
        `;

        const existingError = form.querySelector('.bg-red-50');
        if (existingError) {
            existingError.remove();
        }

        form.insertBefore(errorDiv, form.firstChild);

        // Auto-remove after 5 seconds
        setTimeout(() => errorDiv.remove(), 5000);
    }

    /**
     * Show success message
     */
    showSuccess(message) {
        const form = document.getElementById(this.formId);
        if (!form) return;

        const successDiv = document.createElement('div');
        successDiv.className = 'bg-green-50 border-l-4 border-green-500 p-4 mb-4';
        successDiv.innerHTML = `
            <div class="flex items-start">
                <i class="ph-duotone ph-check-circle text-green-500 text-xl mr-3"></i>
                <div>
                    <p class="text-green-700 font-medium">Success</p>
                    <p class="text-green-600 text-sm">${message}</p>
                </div>
            </div>
        `;

        const existingSuccess = form.querySelector('.bg-green-50');
        if (existingSuccess) {
            existingSuccess.remove();
        }

        form.insertBefore(successDiv, form.firstChild);

        // Auto-remove after 3 seconds
        setTimeout(() => successDiv.remove(), 3000);
    }
}
