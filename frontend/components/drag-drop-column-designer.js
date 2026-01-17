/**
 * Drag-and-Drop Column Designer Component
 *
 * Visual interface for selecting and configuring report columns with:
 * - Drag-and-drop from available fields
 * - Column reordering
 * - Property configuration (alias, aggregate, format)
 * - Live preview
 */

import { apiFetch } from '../assets/js/api.js';
import { showNotification } from '../assets/js/notifications.js';

export class DragDropColumnDesigner {
    constructor(container, options = {}) {
        this.container = container;
        this.options = options;
        this.availableFields = [];
        this.selectedColumns = [];
        this.currentColumn = null;
        this.onColumnsChange = options.onColumnsChange || (() => {});

        this.init();
    }

    async init() {
        await this.loadAvailableFields();
        this.render();
    }

    async loadAvailableFields() {
        // Get available fields from selected entities
        const entities = this.options.entities || [];

        this.availableFields = [];
        for (const entityName of entities) {
            try {
                const response = await apiFetch(`/metadata/entities/${entityName}`);
                if (!response.ok) continue;

                const metadata = await response.json();
                const fields = metadata.fields || [];

                fields.forEach(field => {
                    this.availableFields.push({
                        entity: entityName,
                        name: field.name,
                        label: field.label || field.name,
                        type: field.type || 'string',
                        displayName: `${entityName}.${field.name}`
                    });
                });
            } catch (error) {
                console.error(`Failed to load fields for ${entityName}:`, error);
            }
        }
    }

    render() {
        this.container.innerHTML = `
            <div class="drag-drop-column-designer flex gap-4 h-full">
                <!-- Left Panel: Available Fields -->
                <div class="w-80 border border-gray-200 rounded-lg bg-white">
                    <div class="border-b border-gray-200 p-4">
                        <h3 class="font-semibold text-gray-900 mb-3">Available Fields</h3>
                        <input
                            type="text"
                            id="field-search"
                            class="form-input w-full text-sm"
                            placeholder="Search fields..."
                        />
                    </div>
                    <div class="p-4 overflow-y-auto" style="max-height: 500px;" id="available-fields-list">
                        ${this.renderAvailableFields()}
                    </div>
                </div>

                <!-- Center Panel: Selected Columns -->
                <div class="flex-1 border border-gray-200 rounded-lg bg-white">
                    <div class="border-b border-gray-200 p-4 flex justify-between items-center">
                        <h3 class="font-semibold text-gray-900">Selected Columns</h3>
                        <div class="flex gap-2">
                            <button id="add-all-btn" class="btn btn-xs btn-secondary">
                                <i class="ph ph-plus mr-1"></i>
                                Add All
                            </button>
                            <button id="clear-all-btn" class="btn btn-xs btn-secondary">
                                <i class="ph ph-trash mr-1"></i>
                                Clear All
                            </button>
                        </div>
                    </div>
                    <div class="p-4" id="selected-columns-list">
                        ${this.renderSelectedColumns()}
                    </div>
                </div>

                <!-- Right Panel: Column Properties -->
                <div class="w-96 border border-gray-200 rounded-lg bg-white">
                    <div class="border-b border-gray-200 p-4">
                        <h3 class="font-semibold text-gray-900">Column Properties</h3>
                    </div>
                    <div class="p-4 overflow-y-auto" style="max-height: 500px;" id="column-properties">
                        ${this.renderColumnProperties()}
                    </div>
                </div>
            </div>
        `;

        this.attachEventListeners();
    }

    renderAvailableFields() {
        if (this.availableFields.length === 0) {
            return '<p class="text-sm text-gray-500">No fields available. Select a data source first.</p>';
        }

        // Group by entity
        const groupedFields = {};
        this.availableFields.forEach(field => {
            if (!groupedFields[field.entity]) {
                groupedFields[field.entity] = [];
            }
            groupedFields[field.entity].push(field);
        });

        return Object.entries(groupedFields).map(([entity, fields]) => `
            <div class="mb-4">
                <h4 class="text-xs font-semibold text-gray-700 uppercase mb-2">${this.escapeHtml(entity)}</h4>
                <div class="space-y-1">
                    ${fields.map(field => `
                        <div
                            class="field-item p-2 bg-gray-50 border border-gray-200 rounded cursor-move hover:border-blue-500 hover:bg-blue-50 transition-all"
                            draggable="true"
                            data-field='${JSON.stringify(field)}'
                        >
                            <div class="flex items-center justify-between">
                                <div class="flex items-center">
                                    <i class="ph ph-database text-gray-400 mr-2 text-sm"></i>
                                    <span class="text-sm text-gray-900">${this.escapeHtml(field.label)}</span>
                                </div>
                                <button
                                    class="add-field-btn text-blue-600 hover:text-blue-800"
                                    data-field='${JSON.stringify(field)}'
                                >
                                    <i class="ph ph-plus text-sm"></i>
                                </button>
                            </div>
                            <div class="text-xs text-gray-500 mt-1">${field.type}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `).join('');
    }

    renderSelectedColumns() {
        if (this.selectedColumns.length === 0) {
            return `
                <div class="text-center py-12">
                    <i class="ph ph-arrow-left text-4xl text-gray-300 mb-2"></i>
                    <p class="text-sm text-gray-500">Drag fields here or click + to add</p>
                </div>
            `;
        }

        return `
            <div class="space-y-2" id="sortable-columns">
                ${this.selectedColumns.map((column, index) => `
                    <div
                        class="column-item p-3 bg-gray-50 border border-gray-200 rounded cursor-move hover:border-blue-500 transition-all ${this.currentColumn === index ? 'border-blue-500 bg-blue-50' : ''}"
                        draggable="true"
                        data-index="${index}"
                    >
                        <div class="flex items-center justify-between">
                            <div class="flex items-center flex-1">
                                <i class="ph ph-dots-six-vertical text-gray-400 mr-2 cursor-move"></i>
                                <div class="flex-1">
                                    <div class="text-sm font-medium text-gray-900">${this.escapeHtml(column.alias || column.label)}</div>
                                    <div class="text-xs text-gray-500">${this.escapeHtml(column.displayName)}</div>
                                </div>
                            </div>
                            <div class="flex items-center gap-2">
                                ${column.aggregate ? `<span class="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">${column.aggregate}</span>` : ''}
                                ${column.format ? `<span class="px-2 py-1 text-xs bg-green-100 text-green-800 rounded">${column.format}</span>` : ''}
                                <button
                                    class="remove-column-btn text-red-600 hover:text-red-800"
                                    data-index="${index}"
                                >
                                    <i class="ph ph-x"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    renderColumnProperties() {
        if (this.currentColumn === null || !this.selectedColumns[this.currentColumn]) {
            return '<p class="text-sm text-gray-500">Select a column to edit properties</p>';
        }

        const column = this.selectedColumns[this.currentColumn];

        return `
            <div class="space-y-4">
                <!-- Column Name -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Column Name</label>
                    <input
                        type="text"
                        id="column-alias"
                        class="form-input w-full"
                        value="${this.escapeHtml(column.alias || column.label)}"
                        placeholder="Column display name"
                    />
                </div>

                <!-- Original Field -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Original Field</label>
                    <input
                        type="text"
                        class="form-input w-full bg-gray-50"
                        value="${this.escapeHtml(column.displayName)}"
                        readonly
                    />
                </div>

                <!-- Data Type -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Data Type</label>
                    <input
                        type="text"
                        class="form-input w-full bg-gray-50"
                        value="${column.type}"
                        readonly
                    />
                </div>

                <!-- Aggregate Function -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Aggregate</label>
                    <select id="column-aggregate" class="form-select w-full">
                        <option value="">None</option>
                        <option value="SUM" ${column.aggregate === 'SUM' ? 'selected' : ''}>SUM</option>
                        <option value="AVG" ${column.aggregate === 'AVG' ? 'selected' : ''}>AVG</option>
                        <option value="COUNT" ${column.aggregate === 'COUNT' ? 'selected' : ''}>COUNT</option>
                        <option value="MIN" ${column.aggregate === 'MIN' ? 'selected' : ''}>MIN</option>
                        <option value="MAX" ${column.aggregate === 'MAX' ? 'selected' : ''}>MAX</option>
                    </select>
                </div>

                <!-- Format -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Format</label>
                    <select id="column-format" class="form-select w-full">
                        <option value="">Default</option>
                        <option value="currency" ${column.format === 'currency' ? 'selected' : ''}>Currency</option>
                        <option value="percent" ${column.format === 'percent' ? 'selected' : ''}>Percent</option>
                        <option value="number" ${column.format === 'number' ? 'selected' : ''}>Number (1,000)</option>
                        <option value="date" ${column.format === 'date' ? 'selected' : ''}>Date (MM/DD/YYYY)</option>
                        <option value="datetime" ${column.format === 'datetime' ? 'selected' : ''}>Date Time</option>
                        <option value="boolean" ${column.format === 'boolean' ? 'selected' : ''}>Boolean (Yes/No)</option>
                    </select>
                </div>

                <!-- Sortable -->
                <div class="flex items-center">
                    <input
                        type="checkbox"
                        id="column-sortable"
                        class="checkbox mr-2"
                        ${column.sortable !== false ? 'checked' : ''}
                    />
                    <label for="column-sortable" class="text-sm text-gray-700">Allow sorting</label>
                </div>

                <!-- Width -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Column Width (optional)</label>
                    <input
                        type="text"
                        id="column-width"
                        class="form-input w-full"
                        value="${column.width || ''}"
                        placeholder="e.g., 150px or 20%"
                    />
                </div>

                <!-- Alignment -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Alignment</label>
                    <select id="column-align" class="form-select w-full">
                        <option value="left" ${column.align === 'left' || !column.align ? 'selected' : ''}>Left</option>
                        <option value="center" ${column.align === 'center' ? 'selected' : ''}>Center</option>
                        <option value="right" ${column.align === 'right' ? 'selected' : ''}>Right</option>
                    </select>
                </div>
            </div>
        `;
    }

    attachEventListeners() {
        // Field search
        document.getElementById('field-search')?.addEventListener('input', (e) => {
            this.filterFields(e.target.value);
        });

        // Add all / Clear all buttons
        document.getElementById('add-all-btn')?.addEventListener('click', () => {
            this.addAllFields();
        });

        document.getElementById('clear-all-btn')?.addEventListener('click', () => {
            this.clearAllColumns();
        });

        // Drag and drop for available fields
        document.querySelectorAll('.field-item').forEach(item => {
            item.addEventListener('dragstart', (e) => {
                e.dataTransfer.setData('field', item.dataset.field);
            });
        });

        // Add field buttons
        this.container.addEventListener('click', (e) => {
            const addBtn = e.target.closest('.add-field-btn');
            if (addBtn) {
                const field = JSON.parse(addBtn.dataset.field);
                this.addColumn(field);
            }

            const removeBtn = e.target.closest('.remove-column-btn');
            if (removeBtn) {
                const index = parseInt(removeBtn.dataset.index);
                this.removeColumn(index);
            }

            const columnItem = e.target.closest('.column-item');
            if (columnItem && !e.target.closest('.remove-column-btn')) {
                const index = parseInt(columnItem.dataset.index);
                this.selectColumn(index);
            }
        });

        // Drop zone for columns
        const columnsList = document.getElementById('selected-columns-list');
        if (columnsList) {
            columnsList.addEventListener('dragover', (e) => {
                e.preventDefault();
            });

            columnsList.addEventListener('drop', (e) => {
                e.preventDefault();
                const fieldData = e.dataTransfer.getData('field');
                if (fieldData) {
                    const field = JSON.parse(fieldData);
                    this.addColumn(field);
                }
            });
        }

        // Drag and drop for reordering columns
        document.querySelectorAll('.column-item').forEach(item => {
            item.addEventListener('dragstart', (e) => {
                e.dataTransfer.setData('columnIndex', item.dataset.index);
            });

            item.addEventListener('dragover', (e) => {
                e.preventDefault();
            });

            item.addEventListener('drop', (e) => {
                e.preventDefault();
                const fromIndex = parseInt(e.dataTransfer.getData('columnIndex'));
                const toIndex = parseInt(item.dataset.index);
                this.reorderColumn(fromIndex, toIndex);
            });
        });

        // Property change listeners
        document.getElementById('column-alias')?.addEventListener('change', (e) => {
            if (this.currentColumn !== null) {
                this.selectedColumns[this.currentColumn].alias = e.target.value;
                this.refreshSelectedColumns();
                this.notifyChange();
            }
        });

        document.getElementById('column-aggregate')?.addEventListener('change', (e) => {
            if (this.currentColumn !== null) {
                this.selectedColumns[this.currentColumn].aggregate = e.target.value;
                this.refreshSelectedColumns();
                this.notifyChange();
            }
        });

        document.getElementById('column-format')?.addEventListener('change', (e) => {
            if (this.currentColumn !== null) {
                this.selectedColumns[this.currentColumn].format = e.target.value;
                this.refreshSelectedColumns();
                this.notifyChange();
            }
        });

        document.getElementById('column-sortable')?.addEventListener('change', (e) => {
            if (this.currentColumn !== null) {
                this.selectedColumns[this.currentColumn].sortable = e.target.checked;
                this.notifyChange();
            }
        });

        document.getElementById('column-width')?.addEventListener('change', (e) => {
            if (this.currentColumn !== null) {
                this.selectedColumns[this.currentColumn].width = e.target.value;
                this.notifyChange();
            }
        });

        document.getElementById('column-align')?.addEventListener('change', (e) => {
            if (this.currentColumn !== null) {
                this.selectedColumns[this.currentColumn].align = e.target.value;
                this.notifyChange();
            }
        });
    }

    filterFields(searchTerm) {
        const term = searchTerm.toLowerCase().trim();
        const items = document.querySelectorAll('.field-item');

        items.forEach(item => {
            const field = JSON.parse(item.dataset.field);
            const matches =
                field.label.toLowerCase().includes(term) ||
                field.name.toLowerCase().includes(term) ||
                field.displayName.toLowerCase().includes(term);

            item.style.display = matches ? 'block' : 'none';
        });
    }

    addColumn(field) {
        // Check if already added
        if (this.selectedColumns.find(c => c.displayName === field.displayName)) {
            showNotification('Column already added', 'warning');
            return;
        }

        // Add column
        this.selectedColumns.push({
            ...field,
            alias: field.label,
            sortable: true,
            visible: true
        });

        this.refreshSelectedColumns();
        this.selectColumn(this.selectedColumns.length - 1);
        this.notifyChange();
    }

    removeColumn(index) {
        this.selectedColumns.splice(index, 1);

        if (this.currentColumn === index) {
            this.currentColumn = null;
        } else if (this.currentColumn > index) {
            this.currentColumn--;
        }

        this.refreshSelectedColumns();
        this.refreshProperties();
        this.notifyChange();
    }

    selectColumn(index) {
        this.currentColumn = index;
        this.refreshSelectedColumns();
        this.refreshProperties();
    }

    reorderColumn(fromIndex, toIndex) {
        if (fromIndex === toIndex) return;

        const column = this.selectedColumns.splice(fromIndex, 1)[0];
        this.selectedColumns.splice(toIndex, 0, column);

        // Update current column index
        if (this.currentColumn === fromIndex) {
            this.currentColumn = toIndex;
        } else if (fromIndex < this.currentColumn && toIndex >= this.currentColumn) {
            this.currentColumn--;
        } else if (fromIndex > this.currentColumn && toIndex <= this.currentColumn) {
            this.currentColumn++;
        }

        this.refreshSelectedColumns();
        this.notifyChange();
    }

    addAllFields() {
        this.availableFields.forEach(field => {
            if (!this.selectedColumns.find(c => c.displayName === field.displayName)) {
                this.selectedColumns.push({
                    ...field,
                    alias: field.label,
                    sortable: true,
                    visible: true
                });
            }
        });

        this.refreshSelectedColumns();
        this.notifyChange();
    }

    clearAllColumns() {
        if (!confirm('Remove all columns?')) return;

        this.selectedColumns = [];
        this.currentColumn = null;
        this.refreshSelectedColumns();
        this.refreshProperties();
        this.notifyChange();
    }

    refreshSelectedColumns() {
        document.getElementById('selected-columns-list').innerHTML = this.renderSelectedColumns();
        this.attachEventListeners(); // Re-attach after render
    }

    refreshProperties() {
        document.getElementById('column-properties').innerHTML = this.renderColumnProperties();
        this.attachEventListeners(); // Re-attach after render
    }

    getColumns() {
        return this.selectedColumns;
    }

    setColumns(columns) {
        this.selectedColumns = columns || [];
        this.currentColumn = null;
        this.refreshSelectedColumns();
        this.refreshProperties();
    }

    setAvailableFields(fields) {
        this.availableFields = fields || [];
        document.getElementById('available-fields-list').innerHTML = this.renderAvailableFields();
        this.attachEventListeners();
    }

    notifyChange() {
        this.onColumnsChange(this.selectedColumns);
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}
