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
import { upgradeAllSelects, upgradeSelect, setFlexOptions, setFlexValue } from '../assets/js/utils/upgrade-select.js';

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
        this._entityFieldsCache = {}; // cache: entityName → [{value, label}]

        this.init();
    }

    async init() {
        await this.loadEntities();
        this.render();
        await this.initCytoscape();
    }

    async loadEntities() {
        try {
            // Load system entities, nocode entities, and modules in parallel
            const [sysRes, nocodeRes, modulesRes] = await Promise.all([
                apiFetch('/metadata/entities').catch(() => ({ ok: false })),
                apiFetch('/data-model/entities?status=published').catch(() => ({ ok: false })),
                apiFetch('/modules').catch(() => ({ ok: false }))
            ]);

            const allEntities = [];

            // Build module id → display_name lookup
            this.moduleMap = {};
            if (modulesRes.ok) {
                const modulesData = await modulesRes.json();
                const moduleList = modulesData.modules || modulesData;
                if (Array.isArray(moduleList)) {
                    moduleList.forEach(m => {
                        this.moduleMap[m.id] = m.display_name || m.name;
                    });
                }
            }

            // Process system entities
            // /metadata/entities returns { entities: ["name1","name2",...], total: N }
            // — each item is a plain string (entity name), not a full object.
            if (sysRes.ok) {
                const sysData = await sysRes.json();
                const systemEntities = Array.isArray(sysData) ? sysData : (sysData.entities || []);
                systemEntities.forEach(e => {
                    const entityName = typeof e === 'string' ? e : (e.entity_name || e.name);
                    const displayName = typeof e === 'string' ? e : (e.display_name || e.label || entityName);
                    allEntities.push({
                        entity_name: entityName,
                        display_name: displayName,
                        fields: e.fields || [],
                        type: 'system',
                        module: null,
                        icon: (typeof e === 'object' && e.icon) || 'ph-duotone ph-table'
                    });
                });
            }

            // Process nocode entities — resolve module_id to a display name
            if (nocodeRes.ok) {
                const nocodeData = await nocodeRes.json();
                const nocodeEntities = Array.isArray(nocodeData) ? nocodeData : (nocodeData.entities || nocodeData.items || []);
                nocodeEntities.forEach(e => {
                    const moduleLabel = e.module_id
                        ? (this.moduleMap[e.module_id] || e.module_id)
                        : (e.category || 'General');
                    allEntities.push({
                        entity_name: e.name,
                        display_name: e.label || e.name,
                        fields: e.fields || [],
                        type: 'nocode',
                        module: moduleLabel,
                        icon: e.icon || 'ph-duotone ph-database'
                    });
                });
            }

            // Deduplicate by entity_name — nocode wins over system if names clash
            const seen = new Map();
            for (const e of allEntities) {
                if (!seen.has(e.entity_name) || e.type === 'nocode') {
                    seen.set(e.entity_name, e);
                }
            }
            this.entities = Array.from(seen.values());
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
                    <div class="mb-3">
                        <input
                            type="text"
                            id="entity-search"
                            class="form-input w-full text-sm"
                            placeholder="Search entities..."
                        />
                    </div>
                    <div class="mb-3">
                        <select id="module-filter" class="form-select w-full text-sm">
                            <option value="">All Modules</option>
                            ${[...new Set(this.entities.filter(e => e.module).map(e => e.module))].sort().map(m =>
                                `<option value="${this.escapeHtml(m)}">${this.escapeHtml(m)}</option>`
                            ).join('')}
                        </select>
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
                        <div id="join-suggestions-panel" class="mt-2 space-y-1"></div>
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

        const leftPanel = this.container.querySelector('.w-64');
        if (leftPanel) upgradeAllSelects(leftPanel);
        this.attachEventListeners();
    }

    renderEntityPalette() {
        if (this.entities.length === 0) {
            return '<p class="text-sm text-gray-500">Loading entities...</p>';
        }

        const renderCard = (entity) => `
            <div
                class="entity-palette-item p-2.5 bg-white border border-gray-200 rounded cursor-move hover:border-blue-500 hover:shadow-sm transition-all mb-1.5"
                draggable="true"
                data-entity="${entity.entity_name}"
            >
                <div class="flex items-center gap-2">
                    <i class="${entity.icon} text-blue-600 text-base"></i>
                    <div class="flex-1 min-w-0">
                        <div class="text-sm font-medium text-gray-900 truncate">${this.escapeHtml(entity.display_name)}</div>
                        <div class="text-xs text-gray-400 truncate">${entity.entity_name}</div>
                    </div>
                </div>
            </div>
        `;

        const renderSection = (label, entities, badgeClass, icon) => `
            <div class="mb-1 mt-3 flex items-center gap-1.5">
                <i class="${icon} text-xs text-gray-400"></i>
                <span class="text-xs font-semibold text-gray-500 uppercase tracking-wide">${label}</span>
                <span class="ml-auto text-xs px-1.5 py-0.5 rounded ${badgeClass}">${entities.length}</span>
            </div>
            ${entities.map(renderCard).join('')}
        `;

        // System group (flat)
        const systemEntities = this.entities.filter(e => e.type === 'system');

        // Custom entities grouped by module
        const nocodeEntities = this.entities.filter(e => e.type === 'nocode');
        const moduleGroups = new Map();
        nocodeEntities.forEach(e => {
            const key = e.module || 'General';
            if (!moduleGroups.has(key)) moduleGroups.set(key, []);
            moduleGroups.get(key).push(e);
        });

        // Sort module groups alphabetically, keeping General last
        const sortedGroups = Array.from(moduleGroups.entries()).sort(([a], [b]) => {
            if (a === 'General') return 1;
            if (b === 'General') return -1;
            return a.localeCompare(b);
        });

        const systemHtml = systemEntities.length
            ? renderSection('System', systemEntities, 'bg-blue-50 text-blue-600', 'ph ph-gear')
            : '';

        const customHtml = sortedGroups.map(([moduleName, entities]) =>
            renderSection(moduleName, entities, 'bg-emerald-50 text-emerald-600', 'ph ph-cube')
        ).join('');

        return systemHtml + customHtml;
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

        // Restore saved state if provided via options
        if (this.options.initialDataSource) {
            this._restoreDataSource(this.options.initialDataSource);
        }
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

        // Handle node clicks — show a floating remove button
        this.cy.on('tap', 'node', (evt) => {
            const node = evt.target;
            this._showNodePopup(node);
        });

        // Dismiss popup when tapping the background
        this.cy.on('tap', (evt) => {
            if (evt.target === this.cy) this._hideNodePopup();
        });
    }

    _showNodePopup(node) {
        this._hideNodePopup(); // remove any existing popup

        const entityName = node.data('id');
        const entity = this.selectedEntities.find(e => e.entity_name === entityName);
        if (!entity) return;

        const popup = document.createElement('div');
        popup.id = 'cy-node-popup';
        popup.style.cssText = 'position:absolute;z-index:200;background:#fff;border:1px solid #e2e8f0;border-radius:8px;box-shadow:0 4px 12px rgba(0,0,0,.15);padding:10px 12px;min-width:160px;pointer-events:auto;';

        popup.innerHTML = `
            <div class="flex items-center justify-between gap-3">
                <span style="font-size:13px;font-weight:600;color:#1e293b;white-space:nowrap;">${this.escapeHtml(entity.display_name)}</span>
                <button id="cy-popup-remove" style="display:flex;align-items:center;gap:4px;padding:3px 8px;background:#fee2e2;color:#dc2626;border:1px solid #fecaca;border-radius:5px;font-size:12px;cursor:pointer;white-space:nowrap;">
                    <i class="ph ph-trash"></i> Remove
                </button>
            </div>
        `;

        // Position near the node using its rendered bounding box
        const canvas = document.getElementById('cytoscape-canvas');
        if (!canvas) return;
        const canvasRect = canvas.getBoundingClientRect();
        const nodePos = node.renderedPosition();

        popup.style.left = `${nodePos.x + 10}px`;
        popup.style.top  = `${nodePos.y - 44}px`;

        canvas.style.position = 'relative';
        canvas.appendChild(popup);

        document.getElementById('cy-popup-remove')?.addEventListener('click', () => {
            this._hideNodePopup();
            this.removeEntity(entityName);
        });
    }

    _hideNodePopup() {
        document.getElementById('cy-node-popup')?.remove();
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

        // Entity search and module filter
        document.getElementById('entity-search')?.addEventListener('input', () => {
            this.filterEntityPalette();
        });
        document.getElementById('module-filter')?.addEventListener('change', () => {
            this.filterEntityPalette();
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

    async addEntityToCanvas(entityName) {
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

        // When we have 2+ entities, auto-fetch join suggestions
        if (this.selectedEntities.length >= 2) {
            await this._refreshJoinSuggestions();
        }
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

    /** Alias used by the report designer's clearReport() */
    clear() { this.clearCanvas(); }

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
        this._renderJoinSuggestionsPanel();
    }

    filterEntityPalette() {
        const term   = (document.getElementById('entity-search')?.value || '').toLowerCase().trim();
        const module = document.getElementById('module-filter')?.value || '';

        document.querySelectorAll('.entity-palette-item').forEach(item => {
            const entity = this.entities.find(e => e.entity_name === item.dataset.entity);
            if (!entity) { item.style.display = 'none'; return; }

            const matchesSearch = !term ||
                entity.display_name.toLowerCase().includes(term) ||
                entity.entity_name.toLowerCase().includes(term);

            const matchesModule = !module ||
                (entity.module || '') === module ||
                (module === 'System' && entity.type === 'system');

            item.style.display = matchesSearch && matchesModule ? '' : 'none';
        });
    }

    async showAddJoinDialog() {
        if (this.selectedEntities.length < 2) {
            showNotification('Add at least 2 entities first', 'warning');
            return;
        }
        // Fetch suggestions then show modal
        await this._refreshJoinSuggestions();
        this._openJoinModal();
    }

    // ── Join Suggestion Logic ─────────────────────────────────────────────────

    async _refreshJoinSuggestions() {
        const names = this.selectedEntities.map(e => e.entity_name).join(',');
        try {
            const res = await apiFetch(`/reports/entities/join-suggestions?entities=${encodeURIComponent(names)}`);
            if (res.ok) {
                const data = await res.json();
                this._joinSuggestions = Array.isArray(data) ? data : [];
            } else {
                this._joinSuggestions = [];
            }
        } catch {
            this._joinSuggestions = [];
        }
        this._renderJoinSuggestionsPanel();
    }

    _renderJoinSuggestionsPanel() {
        const panel = document.getElementById('join-suggestions-panel');
        if (!panel) return;

        const suggestions = (this._joinSuggestions || []).filter(s =>
            // Hide suggestions already added as joins
            !this.joins.some(j =>
                j.from_entity === s.from_entity && j.from_field === s.from_field &&
                j.to_entity   === s.to_entity   && j.to_field   === s.to_field
            )
        );

        if (suggestions.length === 0) {
            panel.innerHTML = this.selectedEntities.length >= 2
                ? '<p class="text-xs text-gray-400 italic">No automatic joins found — use manual form below.</p>'
                : '';
            return;
        }

        panel.innerHTML = `
            <div class="mb-1 text-xs font-semibold text-gray-500 uppercase tracking-wide">Suggested Joins</div>
            ${suggestions.map((s, i) => `
                <div class="flex items-center justify-between gap-2 p-2 bg-blue-50 border border-blue-100 rounded mb-1">
                    <div class="text-xs text-gray-700 truncate flex-1" title="${this.escapeHtml(s.label)}">
                        <i class="ph ph-link text-blue-400 mr-1"></i>
                        <span class="font-medium">${this.escapeHtml(s.from_entity)}</span>.<span class="text-blue-600">${this.escapeHtml(s.from_field)}</span>
                        <span class="text-gray-400 mx-1">=</span>
                        <span class="font-medium">${this.escapeHtml(s.to_entity)}</span>.<span class="text-blue-600">${this.escapeHtml(s.to_field)}</span>
                        <span class="ml-1 text-gray-400">(${this.escapeHtml(s.join_type)})</span>
                    </div>
                    <button class="add-suggested-join-btn flex-shrink-0 px-2 py-0.5 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition"
                        data-suggestion-index="${i}">
                        Add
                    </button>
                </div>
            `).join('')}
        `;

        // Wire add buttons
        panel.querySelectorAll('.add-suggested-join-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const idx = parseInt(btn.dataset.suggestionIndex);
                const s = suggestions[idx];
                if (s) this._addSuggestedJoin(s);
            });
        });
    }

    _addSuggestedJoin(suggestion) {
        this.joins.push({
            type:        suggestion.join_type || 'LEFT',
            from_entity: suggestion.from_entity,
            from_field:  suggestion.from_field,
            to_entity:   suggestion.to_entity,
            to_field:    suggestion.to_field,
        });

        this._addJoinEdge(suggestion.from_entity, suggestion.to_entity, suggestion.join_type || 'LEFT');
        this.refreshUI();
        this._renderJoinSuggestionsPanel(); // re-render to hide the added suggestion
        this.notifyChange();
    }

    _openJoinModal() {
        const entityOptions = this.selectedEntities.map(e =>
            `<option value="${this.escapeHtml(e.entity_name)}">${this.escapeHtml(e.display_name)}</option>`
        ).join('');

        const defaultFrom = this.selectedEntities[0]?.entity_name || '';
        const defaultTo   = this.selectedEntities[1]?.entity_name || this.selectedEntities[0]?.entity_name || '';

        // Reuse existing modal element or create one
        let modal = document.getElementById('join-manual-modal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'join-manual-modal';
            modal.className = 'fixed inset-0 z-50 flex items-center justify-center bg-black/40';
            document.body.appendChild(modal);
        }

        modal.innerHTML = `
            <div class="bg-white rounded-xl shadow-2xl w-full max-w-md mx-4 p-6">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-base font-semibold text-gray-900">Add Join</h3>
                    <button id="close-join-modal" class="text-gray-400 hover:text-gray-600"><i class="ph ph-x text-lg"></i></button>
                </div>

                <div id="modal-join-suggestions-panel" class="mb-4 space-y-1"></div>

                <details class="group" open>
                    <summary class="text-xs font-medium text-gray-500 cursor-pointer hover:text-gray-700 mb-3 select-none">
                        <i class="ph ph-pencil mr-1"></i>Manual join
                    </summary>
                    <div class="space-y-3 mt-2">
                        <div class="grid grid-cols-2 gap-3">
                            <div>
                                <label class="block text-xs font-medium text-gray-600 mb-1">From Entity</label>
                                <select id="join-from-entity" class="form-select w-full">${entityOptions}</select>
                            </div>
                            <div>
                                <label class="block text-xs font-medium text-gray-600 mb-1">From Field</label>
                                <select id="join-from-field" class="form-select w-full">
                                    <option value="">— loading —</option>
                                </select>
                            </div>
                            <div>
                                <label class="block text-xs font-medium text-gray-600 mb-1">To Entity</label>
                                <select id="join-to-entity" class="form-select w-full">${entityOptions}</select>
                            </div>
                            <div>
                                <label class="block text-xs font-medium text-gray-600 mb-1">To Field</label>
                                <select id="join-to-field" class="form-select w-full">
                                    <option value="">— loading —</option>
                                </select>
                            </div>
                        </div>
                        <div>
                            <label class="block text-xs font-medium text-gray-600 mb-1">Join Type</label>
                            <select id="join-type" class="form-select w-full">
                                <option value="LEFT">LEFT — keep all rows from left table</option>
                                <option value="INNER">INNER — only matching rows</option>
                                <option value="RIGHT">RIGHT — keep all rows from right table</option>
                            </select>
                        </div>
                        <button id="confirm-manual-join" class="w-full py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition">
                            Add Join
                        </button>
                    </div>
                </details>
            </div>
        `;

        modal.classList.remove('hidden');

        // Load fields for a given entity name, then update the field dropdown
        const loadFromFields = async (entityName) => {
            const name = typeof entityName === 'string' ? entityName : String(entityName?.value ?? entityName ?? '');
            if (!name) return;
            const fields = await this._loadEntityFields(name);
            setFlexOptions('join-from-field', fields, '— select field —');
        };
        const loadToFields = async (entityName) => {
            const name = typeof entityName === 'string' ? entityName : String(entityName?.value ?? entityName ?? '');
            if (!name) return;
            const fields = await this._loadEntityFields(name);
            setFlexOptions('join-to-field', fields, '— select field —');
        };

        // Upgrade entity selects first, wiring onChange so we receive the value
        // string directly from FlexSelect (avoids any hidden-input / e.target ambiguity)
        const fromEntitySel = modal.querySelector('#join-from-entity');
        const toEntitySel   = modal.querySelector('#join-to-entity');

        upgradeSelect(fromEntitySel, { onChange: (val) => loadFromFields(val) });
        upgradeSelect(toEntitySel,   { onChange: (val) => loadToFields(val) });

        // Upgrade remaining selects (join-from-field, join-to-field, join-type)
        upgradeAllSelects(modal);

        // Set initial entity values and load their fields
        setFlexValue('join-from-entity', defaultFrom);
        setFlexValue('join-to-entity',   defaultTo);
        loadFromFields(defaultFrom);
        loadToFields(defaultTo);

        // Populate suggestion panel inside modal
        const innerPanel = modal.querySelector('#modal-join-suggestions-panel');
        if (innerPanel) {
            const suggestions = (this._joinSuggestions || []).filter(s =>
                !this.joins.some(j =>
                    j.from_entity === s.from_entity && j.from_field === s.from_field &&
                    j.to_entity   === s.to_entity   && j.to_field   === s.to_field
                )
            );
            if (suggestions.length > 0) {
                innerPanel.innerHTML = `
                    <p class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Suggested</p>
                    ${suggestions.map((s, i) => `
                        <div class="flex items-center justify-between gap-2 p-2 bg-blue-50 border border-blue-100 rounded mb-1">
                            <span class="text-xs text-gray-700 truncate flex-1">
                                <span class="font-medium">${this.escapeHtml(s.from_entity)}</span>.<span class="text-blue-600">${this.escapeHtml(s.from_field)}</span>
                                = <span class="font-medium">${this.escapeHtml(s.to_entity)}</span>.<span class="text-blue-600">${this.escapeHtml(s.to_field)}</span>
                            </span>
                            <button class="modal-add-suggestion flex-shrink-0 px-2 py-0.5 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
                                data-idx="${i}">Add</button>
                        </div>
                    `).join('')}
                `;
                innerPanel.querySelectorAll('.modal-add-suggestion').forEach(btn => {
                    btn.addEventListener('click', () => {
                        const s = suggestions[parseInt(btn.dataset.idx)];
                        if (s) {
                            this._addSuggestedJoin(s);
                            btn.closest('div.flex')?.remove();
                        }
                    });
                });
            }
        }

        // Close handlers
        const close = () => modal.classList.add('hidden');
        modal.querySelector('#close-join-modal').addEventListener('click', close);
        modal.addEventListener('click', e => { if (e.target === modal) close(); });

        // Manual add handler — read from hidden inputs (flex-select keeps id on hidden input)
        modal.querySelector('#confirm-manual-join').addEventListener('click', () => {
            const fromEntity = document.getElementById('join-from-entity')?.value || '';
            const fromField  = document.getElementById('join-from-field')?.value  || '';
            const toEntity   = document.getElementById('join-to-entity')?.value   || '';
            const toField    = document.getElementById('join-to-field')?.value    || '';
            const joinType   = document.getElementById('join-type')?.value        || 'LEFT';

            if (!fromField || !toField) {
                showNotification('Please select both field names', 'warning');
                return;
            }
            if (fromEntity === toEntity) {
                showNotification('From and To entity must be different', 'warning');
                return;
            }

            this.joins.push({ type: joinType, from_entity: fromEntity, from_field: fromField, to_entity: toEntity, to_field: toField });
            this._addJoinEdge(fromEntity, toEntity, joinType);
            this.refreshUI();
            this.notifyChange();
            close();
        });
    }

    /**
     * Fetch the field list for an entity.
     * Priority:
     *  1. Already-loaded entity.fields (nocode entities from /data-model/entities)
     *     → fields have {name, label} properties
     *  2. Metadata API /metadata/entities/{name}
     *     → table.columns have {field, title} properties (ColumnMetadata schema)
     * Results are cached per entity name for the lifetime of the component.
     * Returns [{value: fieldName, label: displayLabel}]
     */
    async _loadEntityFields(entityName) {
        if (!entityName) return [];
        if (this._entityFieldsCache[entityName]) return this._entityFieldsCache[entityName];

        // 1. Try pre-loaded entity fields (populated for nocode entities)
        const entity = this.entities.find(e => e.entity_name === entityName);
        if (entity?.fields?.length) {
            const fields = entity.fields.map(f => ({ value: f.name, label: f.label || f.name }));
            this._entityFieldsCache[entityName] = fields;
            return fields;
        }

        // 2. Fall back to metadata API (system entities / entities without inline fields)
        try {
            const res = await apiFetch(`/metadata/entities/${encodeURIComponent(entityName)}`);
            if (!res.ok) return [];
            const data = await res.json();
            // ColumnMetadata schema: {field, title}  (NOT {field, label})
            const tableFields = (data?.table?.columns || []).map(c => ({ value: c.field, label: c.title || c.field }));
            // FormConfig schema: fields with {field, title}
            const formFields  = (data?.form?.fields  || []).map(f => ({ value: f.field, label: f.title || f.field }));
            // Prefer form fields (more complete); merge unique by value
            const merged = new Map();
            [...tableFields, ...formFields].forEach(f => { if (!merged.has(f.value)) merged.set(f.value, f); });
            const fields = [...merged.values()];
            this._entityFieldsCache[entityName] = fields;
            return fields;
        } catch {
            return [];
        }
    }

    _addJoinEdge(fromEntity, toEntity, joinType) {
        if (!this.cy) return;
        if (!this.cy.getElementById(fromEntity).length || !this.cy.getElementById(toEntity).length) return;
        const edgeId = `${fromEntity}__${toEntity}`;
        if (this.cy.getElementById(edgeId).length) return; // already exists
        this.cy.add({
            group: 'edges',
            data: { id: edgeId, source: fromEntity, target: toEntity, label: joinType }
        });
    }

    async showAddFilterDialog() {
        if (this.selectedEntities.length === 0) {
            showNotification('Add at least 1 entity first', 'warning');
            return;
        }

        // Build combined field list from all selected entities
        const allFieldsMap = new Map(); // "entity.field" → {value, label}
        await Promise.all(this.selectedEntities.map(async e => {
            const fields = await this._loadEntityFields(e.entity_name);
            fields.forEach(f => {
                const key = `${e.entity_name}.${f.value}`;
                allFieldsMap.set(key, { value: key, label: `${e.display_name} › ${f.label}` });
            });
        }));
        const fieldOptions = [...allFieldsMap.values()];

        let modal = document.getElementById('filter-manual-modal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'filter-manual-modal';
            modal.className = 'fixed inset-0 z-50 flex items-center justify-center bg-black/40';
            document.body.appendChild(modal);
        }

        modal.innerHTML = `
            <div class="bg-white rounded-xl shadow-2xl w-full max-w-sm mx-4 p-6">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-base font-semibold text-gray-900">Add Filter</h3>
                    <button id="close-filter-modal" class="text-gray-400 hover:text-gray-600"><i class="ph ph-x text-lg"></i></button>
                </div>
                <div class="space-y-3">
                    <div>
                        <label class="block text-xs font-medium text-gray-600 mb-1">Field</label>
                        <select id="filter-field" class="form-select w-full">
                            <option value="">— select field —</option>
                            ${fieldOptions.map(f => `<option value="${this.escapeHtml(f.value)}">${this.escapeHtml(f.label)}</option>`).join('')}
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-gray-600 mb-1">Operator</label>
                        <select id="filter-operator" class="form-select w-full">
                            <option value="=">=&nbsp; equals</option>
                            <option value="!=">≠&nbsp; not equals</option>
                            <option value=">">&gt;&nbsp; greater than</option>
                            <option value=">=">&gt;=&nbsp; greater or equal</option>
                            <option value="<">&lt;&nbsp; less than</option>
                            <option value="<=">&lt;=&nbsp; less or equal</option>
                            <option value="LIKE">LIKE&nbsp; contains</option>
                            <option value="NOT LIKE">NOT LIKE&nbsp; not contains</option>
                            <option value="IN">IN&nbsp; in list</option>
                            <option value="IS NULL">IS NULL</option>
                            <option value="IS NOT NULL">IS NOT NULL</option>
                        </select>
                    </div>
                    <div id="filter-value-row">
                        <label class="block text-xs font-medium text-gray-600 mb-1">Value</label>
                        <input id="filter-value" type="text" class="form-input w-full text-sm" placeholder="Filter value" />
                    </div>
                    <button id="confirm-filter" class="w-full py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition">
                        Add Filter
                    </button>
                </div>
            </div>
        `;

        modal.classList.remove('hidden');
        upgradeAllSelects(modal);

        // Hide value input for null operators
        document.getElementById('filter-operator')?.addEventListener('change', e => {
            const noValue = ['IS NULL', 'IS NOT NULL'].includes(e.target.value);
            const row = document.getElementById('filter-value-row');
            if (row) row.classList.toggle('hidden', noValue);
        });

        const close = () => modal.classList.add('hidden');
        modal.querySelector('#close-filter-modal').addEventListener('click', close);
        modal.addEventListener('click', e => { if (e.target === modal) close(); });

        modal.querySelector('#confirm-filter').addEventListener('click', () => {
            const field    = document.getElementById('filter-field')?.value    || '';
            const operator = document.getElementById('filter-operator')?.value || '=';
            const value    = document.getElementById('filter-value')?.value    || '';

            if (!field) {
                showNotification('Please select a field', 'warning');
                return;
            }
            const noValue = ['IS NULL', 'IS NOT NULL'].includes(operator);
            if (!noValue && !value) {
                showNotification('Please enter a value', 'warning');
                return;
            }

            this.filters.push({ field, operator, value: noValue ? null : value });
            this.refreshUI();
            this.notifyChange();
            close();
        });
    }

    async loadPreviewData() {
        const container = document.getElementById('preview-data-container');
        if (!container) return;

        container.innerHTML = '<p class="text-sm text-gray-500">Loading preview data...</p>';

        try {
            // Build query from selected entities, joins, filters
            const query = this.buildQuery();

            // Execute query and get preview data
            const response = await apiFetch('/reports/preview', {
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

    /**
     * Restore previously saved data source state (entities, joins, filters).
     * Called automatically when options.initialDataSource is provided, or
     * can be called manually after initialization.
     */
    setDataSource(dataSource) {
        if (!dataSource) return;
        this._restoreDataSource(dataSource);
    }

    _restoreDataSource(dataSource) {
        if (!dataSource) return;

        // Clear existing canvas state
        this.selectedEntities = [];
        this.joins = [];
        this.filters = dataSource.filters || [];
        if (this.cy) this.cy.elements().remove();

        // Restore entities
        const entityList = dataSource.entities || [];
        entityList.forEach(saved => {
            const entityName = typeof saved === 'string' ? saved
                : (saved.entity_name || saved.name || '');
            if (!entityName) return;

            // Find the matching loaded entity object, or reconstruct a minimal one
            const found = this.entities.find(e => e.entity_name === entityName);
            const entity = found || { entity_name: entityName, display_name: entityName };

            this.selectedEntities.push(entity);

            if (this.cy) {
                this.cy.add({
                    group: 'nodes',
                    data: { id: entityName, label: entity.display_name || entityName }
                });
            }
        });

        // Restore joins
        const joinList = dataSource.joins || [];
        joinList.forEach((join, idx) => {
            this.joins.push(join);
            if (this.cy) {
                const from = join.from_entity || join.left_entity;
                const to   = join.to_entity   || join.right_entity;
                if (from && to) {
                    this.cy.add({
                        group: 'edges',
                        data: {
                            id: `join-${idx}`,
                            source: from,
                            target: to,
                            label: join.join_type || 'INNER JOIN'
                        }
                    });
                }
            }
        });

        if (this.cy && this.selectedEntities.length) this.autoLayout();
        this.refreshUI();

        // Auto-load suggestions for the restored entity set
        if (this.selectedEntities.length >= 2) {
            this._refreshJoinSuggestions();
        }
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
