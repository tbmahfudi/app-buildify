/**
 * Enhanced Parameter UI Component
 *
 * Visual interface for creating and configuring report parameters with smart defaults.
 */

import { showNotification } from '../assets/js/notifications.js';

export class EnhancedParameterUI {
    constructor(container, options = {}) {
        this.container = container;
        this.options = options;
        this.parameters = [];
        this.onParametersChange = options.onParametersChange || (() => {});

        this.init();
    }

    init() {
        this.render();
    }

    render() {
        this.container.innerHTML = `
            <div class="enhanced-parameter-ui">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-lg font-semibold text-gray-900">Parameters</h3>
                    <button id="add-parameter-btn" class="btn btn-sm btn-primary">
                        <i class="ph ph-plus mr-1"></i>
                        Add Parameter
                    </button>
                </div>

                <div id="parameters-list" class="space-y-3">
                    ${this.renderParameters()}
                </div>
            </div>
        `;

        this.attachEventListeners();
    }

    renderParameters() {
        if (this.parameters.length === 0) {
            return `
                <div class="text-center py-12 border-2 border-dashed border-gray-300 rounded-lg">
                    <i class="ph ph-funnel text-4xl text-gray-300 mb-2"></i>
                    <p class="text-gray-500">No parameters defined</p>
                    <p class="text-sm text-gray-400 mt-1">Click "Add Parameter" to create one</p>
                </div>
            `;
        }

        return this.parameters.map((param, index) => `
            <div class="parameter-item bg-white border border-gray-200 rounded-lg p-4">
                <div class="flex justify-between items-start mb-3">
                    <div class="flex-1">
                        <input
                            type="text"
                            class="font-medium text-gray-900 bg-transparent border-0 p-0 focus:ring-0 w-full"
                            value="${this.escapeHtml(param.name || '')}"
                            placeholder="Parameter name"
                            data-index="${index}"
                            data-field="name"
                        />
                    </div>
                    <button class="remove-parameter-btn text-red-600 hover:text-red-800 ml-2" data-index="${index}">
                        <i class="ph ph-trash"></i>
                    </button>
                </div>

                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="block text-xs font-medium text-gray-700 mb-1">Type</label>
                        <select class="form-select w-full text-sm" data-index="${index}" data-field="type">
                            <option value="string" ${param.type === 'string' ? 'selected' : ''}>Text</option>
                            <option value="number" ${param.type === 'number' ? 'selected' : ''}>Number</option>
                            <option value="date" ${param.type === 'date' ? 'selected' : ''}>Date</option>
                            <option value="boolean" ${param.type === 'boolean' ? 'selected' : ''}>Boolean</option>
                            <option value="list" ${param.type === 'list' ? 'selected' : ''}>Dropdown</option>
                        </select>
                    </div>

                    <div>
                        <label class="block text-xs font-medium text-gray-700 mb-1">Default Value</label>
                        <input
                            type="text"
                            class="form-input w-full text-sm"
                            value="${this.escapeHtml(param.defaultValue || '')}"
                            placeholder="Default value"
                            data-index="${index}"
                            data-field="defaultValue"
                        />
                    </div>
                </div>

                <div class="mt-3 flex items-center gap-4">
                    <label class="flex items-center text-sm">
                        <input
                            type="checkbox"
                            class="checkbox mr-2"
                            ${param.required ? 'checked' : ''}
                            data-index="${index}"
                            data-field="required"
                        />
                        Required
                    </label>
                    <label class="flex items-center text-sm">
                        <input
                            type="checkbox"
                            class="checkbox mr-2"
                            ${param.multiSelect ? 'checked' : ''}
                            data-index="${index}"
                            data-field="multiSelect"
                        />
                        Multi-select
                    </label>
                </div>
            </div>
        `).join('');
    }

    attachEventListeners() {
        document.getElementById('add-parameter-btn')?.addEventListener('click', () => {
            this.addParameter();
        });

        // Delegated event listeners for parameter inputs
        this.container.addEventListener('input', (e) => {
            const target = e.target;
            if (target.dataset.index !== undefined && target.dataset.field) {
                const index = parseInt(target.dataset.index);
                const field = target.dataset.field;
                const value = target.type === 'checkbox' ? target.checked : target.value;

                if (this.parameters[index]) {
                    this.parameters[index][field] = value;
                    this.notifyChange();
                }
            }
        });

        // Remove parameter
        this.container.addEventListener('click', (e) => {
            const removeBtn = e.target.closest('.remove-parameter-btn');
            if (removeBtn) {
                const index = parseInt(removeBtn.dataset.index);
                this.removeParameter(index);
            }
        });
    }

    addParameter() {
        this.parameters.push({
            name: `param${this.parameters.length + 1}`,
            type: 'string',
            required: false,
            multiSelect: false,
            defaultValue: ''
        });

        this.render();
        this.notifyChange();
    }

    removeParameter(index) {
        this.parameters.splice(index, 1);
        this.render();
        this.notifyChange();
    }

    getParameters() {
        return this.parameters;
    }

    setParameters(parameters) {
        this.parameters = parameters || [];
        this.render();
    }

    notifyChange() {
        this.onParametersChange(this.parameters);
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}
