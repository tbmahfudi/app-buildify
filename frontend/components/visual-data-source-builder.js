/**
 * Visual Data Source Builder Component
 *
 * Interactive entity relationship diagram for building report data sources.
 * Features:
 * - Drag-and-drop entity palette
 * - Visual canvas with Cytoscape.js
 * - Join configuration
 * - Filter builder integration
 * - Live data preview
 */

import { apiFetch } from '../assets/js/api.js';
import { showNotification } from '../assets/js/notifications.js';

export class VisualDataSourceBuilder {
    constructor(container, options = {}) {
        this.container = container;
        this.options = options;
        this.entities = [];
        this.selectedEntities = [];
        this.joins = [];
        this.filters = [];
        this.cy = null; // Cytoscape instance
        this.onDataSourceChange = options.onDataSourceChange || (() => {});

        this.init();
    }

    async init() {
        await this.loadEntities();
        this.render();
        await this.initCytoscape();
    }

    async loadEntities() {
        try {
            // Load both system and nocode entities
            const responses = await Promise.all([
                apiFetch('/metadata/entities').catch(() => ({ ok: false })),
                apiFetch('/data-model/entities?status=published').catch(() => ({ ok: false }))
            ]);

            const allEntities = [];

            // Process system entities
            if (responses[0].ok) {
                const systemEntities = await responses[0].json();
                systemEntities.forEach(e => {
                    allEntities.push({
                        entity_name: e.entity_name || e.name,
                        display_name: e.display_name || e.label || e.name,
                        fields: e.fields || [],
                        type: 'system',
                        icon: e.icon || 'ph-duotone ph-table'
                    });
                });
            }

            // Process nocode entities
            if (responses[1].ok) {
                const nocodeEntities = await responses[1].json();
                nocodeEntities.forEach(e => {
                    allEntities.push({
                        entity_name: e.name,
                        display_name: e.label || e.name,
                        fields: e.fields || [],
                        type: 'nocode',
                        icon: e.icon || 'ph-duotone ph-database'
                    });
                });
            }

            this.entities = allEntities;
        } catch (error) {
            console.error('Failed to load entities:', error);
            this.entities = [];
        }
    }

    render() {
        this.container.innerHTML = `
            <div class="visual-data-source-builder h-full flex">
                <!-- Left Panel: Entity Palette -->
                <div class="w-64 border-r border-gray-200 bg-gray-50 p-4 overflow-y-auto">
                    <div class="mb-4">
                        <input
                            type="text"
                            id="entity-search"
                            class="form-input w-full text-sm"
                            placeholder="Search entities..."
                        />
                    </div>

                    <div class="space-y-2" id="entity-palette">
                        ${this.renderEntityPalette()}
                    </div>
                </div>

                <!-- Center: Canvas -->
                <div class="flex-1 flex flex-col">
                    <!-- Toolbar -->
                    <div class="border-b border-gray-200 p-3 flex justify-between items-center bg-white">
                        <div class="flex gap-2">
                            <button id="clear-canvas-btn" class="btn btn-sm btn-secondary">
                                <i class="ph ph-trash mr-1"></i>
                                Clear
                            </button>
                            <button id="auto-layout-btn" class="btn btn-sm btn-secondary">
                                <i class="ph ph-arrows-out-cardinal mr-1"></i>
                                Auto Layout
                            </button>
                        </div>
                        <div class="flex gap-2">
                            <button id="zoom-in-btn" class="btn btn-sm btn-secondary">
                                <i class="ph ph-magnifying-glass-plus"></i>
                            </button>
                            <button id="zoom-out-btn" class="btn btn-sm btn-secondary">
                                <i class="ph ph-magnifying-glass-minus"></i>
                            </button>
                            <button id="fit-btn" class="btn btn-sm btn-secondary">
                                <i class="ph ph-arrows-out"></i>
                            </button>
                        </div>
                    </div>

                    <!-- Cytoscape Canvas -->
                    <div id="cytoscape-canvas" class="flex-1 bg-white"></div>

                    <!-- Bottom Panel: Preview Data -->
                    <div class="border-t border-gray-200 bg-white">
                        <button
                            id="toggle-preview-btn"
                            class="w-full p-3 text-left font-medium text-gray-700 hover:bg-gray-50 flex justify-between items-center"
                        >
                            <span>
                                <i class="ph ph-table mr-2"></i>
                                Preview Data (10 rows)
                            </span>
                            <i class="ph ph-caret-up" id="preview-caret"></i>
                        </button>
                        <div id="preview-data-container" class="p-4 max-h-64 overflow-auto hidden">
                            <!-- Data preview table will be rendered here -->
                        </div>
                    </div>
                </div>

                <!-- Right Panel: Properties -->
                <div class="w-80 border-l border-gray-200 bg-gray-50 p-4 overflow-y-auto">
                    <h3 class="font-semibold text-gray-900 mb-4">Properties</h3>

                    <!-- Selected Entities -->
                    <div class="mb-6">
                        <h4 class="text-sm font-medium text-gray-700 mb-2">Selected Entities</h4>
                        <div id="selected-entities-list" class="space-y-2">
                            ${this.renderSelectedEntities()}
                        </div>
                    </div>

                    <!-- Joins -->
                    <div class="mb-6">
                        <div class="flex justify-between items-center mb-2">
                            <h4 class="text-sm font-medium text-gray-700">Joins</h4>
                            <button id="add-join-btn" class="btn btn-xs btn-secondary">
                                <i class="ph ph-plus"></i>
                            </button>
                        </div>
                        <div id="joins-list" class="space-y-2">
                            ${this.renderJoins()}
                        </div>
                    </div>

                    <!-- Filters -->
                    <div>
                        <div class="flex justify-between items-center mb-2">
                            <h4 class="text-sm font-medium text-gray-700">Filters</h4>
                            <button id="add-filter-btn" class="btn btn-xs btn-secondary">
                                <i class="ph ph-plus"></i>
                            </button>
                        </div>
                        <div id="filters-list" class="space-y-2">
                            ${this.renderFilters()}
                        </div>
                    </div>
                </div>
            </div>
        `;

        this.attachEventListeners();
    }

    renderEntityPalette() {
        if (this.entities.length === 0) {
            return '<p class="text-sm text-gray-500">Loading entities...</p>';
        }

        return this.entities.map(entity => `
            <div
                class="entity-palette-item p-3 bg-white border border-gray-200 rounded cursor-move hover:border-blue-500 hover:shadow transition-all"
                draggable="true"
                data-entity="${entity.entity_name}"
            >
                <div class="flex items-center">
                    <i class="${entity.icon} text-blue-600 mr-2"></i>
                    <div class="flex-1">
                        <div class="text-sm font-medium text-gray-900">${this.escapeHtml(entity.display_name)}</div>
                        <div class="text-xs text-gray-500">${entity.type}</div>
                    </div>
                </div>
            </div>
        `).join('');
    }

    renderSelectedEntities() {
        if (this.selectedEntities.length === 0) {
            return '<p class="text-xs text-gray-500">Drag entities from left</p>';
        }

        return this.selectedEntities.map(entity => `
            <div class="p-2 bg-white border border-gray-200 rounded flex justify-between items-center">
                <span class="text-sm text-gray-900">${this.escapeHtml(entity.display_name)}</span>
                <button
                    class="remove-entity-btn text-red-600 hover:text-red-800"
                    data-entity="${entity.entity_name}"
                >
                    <i class="ph ph-x"></i>
                </button>
            </div>
        `).join('');
    }

    renderJoins() {
        if (this.joins.length === 0) {
            return '<p class="text-xs text-gray-500">No joins defined</p>';
        }

        return this.joins.map((join, index) => `
            <div class="p-2 bg-white border border-gray-200 rounded">
                <div class="flex justify-between items-start mb-2">
                    <span class="text-xs font-medium text-gray-700">${join.type}</span>
                    <button
                        class="remove-join-btn text-red-600 hover:text-red-800"
                        data-index="${index}"
                    >
                        <i class="ph ph-x text-xs"></i>
                    </button>
                </div>
                <div class="text-xs text-gray-600">
                    ${join.from_entity}.${join.from_field} = ${join.to_entity}.${join.to_field}
                </div>
            </div>
        `).join('');
    }

    renderFilters() {
        if (this.filters.length === 0) {
            return '<p class="text-xs text-gray-500">No filters defined</p>';
        }

        return this.filters.map((filter, index) => `
            <div class="p-2 bg-white border border-gray-200 rounded">
                <div class="flex justify-between items-start mb-2">
                    <span class="text-xs font-medium text-gray-700">${filter.field}</span>
                    <button
                        class="remove-filter-btn text-red-600 hover:text-red-800"
                        data-index="${index}"
                    >
                        <i class="ph ph-x text-xs"></i>
                    </button>
                </div>
                <div class="text-xs text-gray-600">
                    ${filter.operator} ${filter.value}
                </div>
            </div>
        `).join('');
    }

    async initCytoscape() {
        // Load Cytoscape.js library dynamically if not loaded
        if (typeof cytoscape === 'undefined') {
            try {
                await this.loadCytoscapeLibrary();
            } catch (error) {
                console.error('Failed to load Cytoscape:', error);
                showNotification('Failed to load visualization library', 'error');
                return;
            }
        }

        this.createCytoscapeInstance();
    }

    async loadCytoscapeLibrary() {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.26.0/cytoscape.min.js';
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    createCytoscapeInstance() {
        const container = document.getElementById('cytoscape-canvas');
        if (!container) return;

        this.cy = cytoscape({
            container: container,
            elements: [],
            style: [
                {
                    selector: 'node',
                    style: {
                        'label': 'data(label)',
                        'text-valign': 'center',
                        'text-halign': 'center',
                        'background-color': '#3B82F6',
                        'color': '#fff',
                        'font-size': '12px',
                        'width': '120px',
                        'height': '60px',
                        'shape': 'roundrectangle',
                        'text-wrap': 'wrap',
                        'text-max-width': '110px'
                    }
                },
                {
                    selector: 'edge',
                    style: {
                        'width': 2,
                        'line-color': '#9CA3AF',
                        'target-arrow-color': '#9CA3AF',
                        'target-arrow-shape': 'triangle',
                        'curve-style': 'bezier',
                        'label': 'data(label)',
                        'font-size': '10px',
                        'text-rotation': 'autorotate',
                        'text-margin-y': -10
                    }
                }
            ],
            layout: {
                name: 'grid',
                padding: 50
            }
        });

        // Enable panning and zooming
        this.cy.userPanningEnabled(true);
        this.cy.userZoomingEnabled(true);

        // Handle node clicks
        this.cy.on('tap', 'node', (evt) => {
            const node = evt.target;
            console.log('Node clicked:', node.data('id'));
        });
    }

    attachEventListeners() {
        // Entity palette drag
        document.querySelectorAll('.entity-palette-item').forEach(item => {
            item.addEventListener('dragstart', (e) => {
                e.dataTransfer.setData('entity', e.target.dataset.entity);
            });
        });

        // Canvas drop
        const canvas = document.getElementById('cytoscape-canvas');
        if (canvas) {
            canvas.addEventListener('dragover', (e) => {
                e.preventDefault();
            });

            canvas.addEventListener('drop', (e) => {
                e.preventDefault();
                const entityName = e.dataTransfer.getData('entity');
                this.addEntityToCanvas(entityName);
            });
        }

        // Toolbar buttons
        document.getElementById('clear-canvas-btn')?.addEventListener('click', () => {
            this.clearCanvas();
        });

        document.getElementById('auto-layout-btn')?.addEventListener('click', () => {
            this.autoLayout();
        });

        document.getElementById('zoom-in-btn')?.addEventListener('click', () => {
            if (this.cy) this.cy.zoom(this.cy.zoom() * 1.2);
        });

        document.getElementById('zoom-out-btn')?.addEventListener('click', () => {
            if (this.cy) this.cy.zoom(this.cy.zoom() * 0.8);
        });

        document.getElementById('fit-btn')?.addEventListener('click', () => {
            if (this.cy) this.cy.fit(50);
        });

        // Preview toggle
        document.getElementById('toggle-preview-btn')?.addEventListener('click', () => {
            const container = document.getElementById('preview-data-container');
            const caret = document.getElementById('preview-caret');
            container?.classList.toggle('hidden');
            caret?.classList.toggle('ph-caret-up');
            caret?.classList.toggle('ph-caret-down');

            if (!container?.classList.contains('hidden')) {
                this.loadPreviewData();
            }
        });

        // Add join/filter buttons
        document.getElementById('add-join-btn')?.addEventListener('click', () => {
            this.showAddJoinDialog();
        });

        document.getElementById('add-filter-btn')?.addEventListener('click', () => {
            this.showAddFilterDialog();
        });

        // Entity search
        document.getElementById('entity-search')?.addEventListener('input', (e) => {
            this.filterEntityPalette(e.target.value);
        });

        // Remove entity buttons (delegated)
        this.container.addEventListener('click', (e) => {
            const removeEntityBtn = e.target.closest('.remove-entity-btn');
            if (removeEntityBtn) {
                const entityName = removeEntityBtn.dataset.entity;
                this.removeEntity(entityName);
            }

            const removeJoinBtn = e.target.closest('.remove-join-btn');
            if (removeJoinBtn) {
                const index = parseInt(removeJoinBtn.dataset.index);
                this.removeJoin(index);
            }

            const removeFilterBtn = e.target.closest('.remove-filter-btn');
            if (removeFilterBtn) {
                const index = parseInt(removeFilterBtn.dataset.index);
                this.removeFilter(index);
            }
        });
    }

    addEntityToCanvas(entityName) {
        const entity = this.entities.find(e => e.entity_name === entityName);
        if (!entity) return;

        // Check if already added
        if (this.selectedEntities.find(e => e.entity_name === entityName)) {
            showNotification('Entity already added', 'warning');
            return;
        }

        // Add to selected entities
        this.selectedEntities.push(entity);

        // Add node to Cytoscape
        if (this.cy) {
            this.cy.add({
                group: 'nodes',
                data: {
                    id: entityName,
                    label: entity.display_name
                }
            });

            // Auto layout
            this.autoLayout();
        }

        // Refresh UI
        this.refreshUI();
        this.notifyChange();
    }

    removeEntity(entityName) {
        // Remove from selected entities
        this.selectedEntities = this.selectedEntities.filter(e => e.entity_name !== entityName);

        // Remove node from Cytoscape
        if (this.cy) {
            this.cy.getElementById(entityName).remove();
        }

        // Remove related joins
        this.joins = this.joins.filter(j => j.from_entity !== entityName && j.to_entity !== entityName);

        // Refresh UI
        this.refreshUI();
        this.notifyChange();
    }

    removeJoin(index) {
        this.joins.splice(index, 1);
        this.refreshUI();
        this.notifyChange();
    }

    removeFilter(index) {
        this.filters.splice(index, 1);
        this.refreshUI();
        this.notifyChange();
    }

    clearCanvas() {
        this.selectedEntities = [];
        this.joins = [];
        this.filters = [];

        if (this.cy) {
            this.cy.elements().remove();
        }

        this.refreshUI();
        this.notifyChange();
    }

    autoLayout() {
        if (!this.cy) return;

        this.cy.layout({
            name: 'breadthfirst',
            directed: true,
            padding: 50,
            spacingFactor: 1.5
        }).run();
    }

    refreshUI() {
        document.getElementById('selected-entities-list').innerHTML = this.renderSelectedEntities();
        document.getElementById('joins-list').innerHTML = this.renderJoins();
        document.getElementById('filters-list').innerHTML = this.renderFilters();
    }

    filterEntityPalette(searchTerm) {
        const term = searchTerm.toLowerCase().trim();
        const items = document.querySelectorAll('.entity-palette-item');

        items.forEach(item => {
            const entityName = item.dataset.entity;
            const entity = this.entities.find(e => e.entity_name === entityName);

            if (!entity) {
                item.style.display = 'none';
                return;
            }

            const matches =
                entity.display_name.toLowerCase().includes(term) ||
                entity.entity_name.toLowerCase().includes(term) ||
                entity.type.toLowerCase().includes(term);

            item.style.display = matches ? 'block' : 'none';
        });
    }

    showAddJoinDialog() {
        if (this.selectedEntities.length < 2) {
            showNotification('Add at least 2 entities first', 'warning');
            return;
        }

        // Simple prompt-based join for now
        // TODO: Create proper modal dialog
        const fromEntity = prompt('From entity:', this.selectedEntities[0].entity_name);
        if (!fromEntity) return;

        const fromField = prompt('From field:');
        if (!fromField) return;

        const toEntity = prompt('To entity:', this.selectedEntities[1]?.entity_name || '');
        if (!toEntity) return;

        const toField = prompt('To field:');
        if (!toField) return;

        const joinType = prompt('Join type (INNER, LEFT, RIGHT):', 'INNER');

        this.joins.push({
            type: joinType || 'INNER',
            from_entity: fromEntity,
            from_field: fromField,
            to_entity: toEntity,
            to_field: toField
        });

        // Add edge to graph if both entities exist
        if (this.cy && this.cy.getElementById(fromEntity).length && this.cy.getElementById(toEntity).length) {
            this.cy.add({
                group: 'edges',
                data: {
                    id: `${fromEntity}_${toEntity}`,
                    source: fromEntity,
                    target: toEntity,
                    label: joinType
                }
            });
        }

        this.refreshUI();
        this.notifyChange();
    }

    showAddFilterDialog() {
        if (this.selectedEntities.length === 0) {
            showNotification('Add at least 1 entity first', 'warning');
            return;
        }

        // Simple prompt-based filter for now
        const field = prompt('Field name:');
        if (!field) return;

        const operator = prompt('Operator (=, !=, >, <, LIKE):', '=');
        if (!operator) return;

        const value = prompt('Value:');
        if (!value) return;

        this.filters.push({
            field: field,
            operator: operator || '=',
            value: value
        });

        this.refreshUI();
        this.notifyChange();
    }

    async loadPreviewData() {
        const container = document.getElementById('preview-data-container');
        if (!container) return;

        container.innerHTML = '<p class="text-sm text-gray-500">Loading preview data...</p>';

        try {
            // Build query from selected entities, joins, filters
            const query = this.buildQuery();

            // Execute query and get preview data
            const response = await apiFetch('/api/v1/reports/preview', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: query,
                    limit: 10
                })
            });

            if (!response.ok) {
                throw new Error('Failed to load preview');
            }

            const result = await response.json();

            // Render data table
            container.innerHTML = this.renderDataTable(result.data || [], result.columns || []);
        } catch (error) {
            console.error('Failed to load preview data:', error);
            container.innerHTML = '<p class="text-sm text-red-500">Preview not available yet</p>';
        }
    }

    renderDataTable(data, columns) {
        if (!data || data.length === 0) {
            return '<p class="text-sm text-gray-500">No data available</p>';
        }

        return `
            <table class="min-w-full divide-y divide-gray-200 text-sm">
                <thead class="bg-gray-50">
                    <tr>
                        ${columns.map(col => `
                            <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">${this.escapeHtml(col)}</th>
                        `).join('')}
                    </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                    ${data.map(row => `
                        <tr>
                            ${columns.map(col => `
                                <td class="px-3 py-2 whitespace-nowrap text-gray-900">${this.escapeHtml(row[col] || '-')}</td>
                            `).join('')}
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    }

    buildQuery() {
        return {
            entities: this.selectedEntities.map(e => e.entity_name),
            joins: this.joins,
            filters: this.filters
        };
    }

    getDataSource() {
        return {
            base_entity: this.selectedEntities[0]?.entity_name || '',
            entities: this.selectedEntities,
            joins: this.joins,
            filters: this.filters
        };
    }

    notifyChange() {
        this.onDataSourceChange(this.getDataSource());
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}
