/**
 * GroupByDesigner Component
 *
 * Visual UI for configuring hierarchical GROUP BY clauses on a report.
 * Order matters: the first field is the top-level group, subsequent fields
 * are sub-groups within the level above them.
 *
 * Usage:
 *   const gbd = new GroupByDesigner(container, {
 *     onGroupByChange: (groupBy) => { reportData.query_config.group_by = groupBy; }
 *   });
 *   gbd.setAvailableFields(columns);   // feed from DragDropColumnDesigner
 *   gbd.setGroupBy(['category', 'status']); // restore saved config
 */

export class GroupByDesigner {
    constructor(container, options = {}) {
        this.container = container;
        this.onGroupByChange = options.onGroupByChange || (() => {});

        // Fields the user can group on (populated from the column designer)
        this.availableFields = [];

        // Current ordered group levels — array of { field, label }
        this.groupLevels = [];

        this._dragSrcIndex = null;

        this.render();
    }

    // ── Public API ───────────────────────────────────────────────────────────

    /**
     * Feed available fields from the column / data-source designer.
     * @param {Array<{name, label, entity, displayName}>} fields
     */
    setAvailableFields(fields = []) {
        this.availableFields = fields;
        // Remove any group levels whose field no longer exists
        const valid = new Set(fields.map(f => f.name));
        this.groupLevels = this.groupLevels.filter(g => valid.has(g.field));
        this.render();
    }

    /** Restore a saved group_by config (array of field name strings). */
    setGroupBy(groupBy = []) {
        this.groupLevels = groupBy.map(fieldName => {
            const meta = this.availableFields.find(f => f.name === fieldName);
            return { field: fieldName, label: meta ? (meta.label || meta.displayName || fieldName) : fieldName };
        });
        this.render();
    }

    /** Return the current group_by as an array of field-name strings. */
    getGroupBy() {
        return this.groupLevels.map(g => g.field);
    }

    // ── Rendering ────────────────────────────────────────────────────────────

    render() {
        const grouped   = this._alreadyGrouped();
        const available = this.availableFields.filter(f => !grouped.has(f.name));

        this.container.innerHTML = `
            <div class="group-by-designer bg-white border border-gray-200 rounded-xl overflow-hidden">
                <!-- Header -->
                <div class="flex items-center justify-between px-4 py-3 bg-gray-50 border-b border-gray-200">
                    <div class="flex items-center gap-2">
                        <i class="ph ph-tree-structure text-indigo-600 text-lg"></i>
                        <h3 class="text-sm font-semibold text-gray-900">Group By</h3>
                        <span class="text-xs text-gray-500 ml-1">— hierarchical grouping</span>
                    </div>
                    ${this.groupLevels.length > 0 ? `
                    <button id="gbd-clear-all" class="text-xs text-red-500 hover:text-red-700 flex items-center gap-1">
                        <i class="ph ph-trash"></i> Clear all
                    </button>` : ''}
                </div>

                <div class="flex divide-x divide-gray-200 min-h-[180px]">
                    <!-- Left: available fields -->
                    <div class="w-56 flex-shrink-0 flex flex-col">
                        <div class="px-3 py-2 bg-gray-50 border-b border-gray-200">
                            <input
                                id="gbd-search"
                                type="text"
                                placeholder="Search fields…"
                                class="w-full text-xs px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-indigo-400"
                            />
                        </div>
                        <div id="gbd-available" class="flex-1 overflow-y-auto p-2 space-y-1">
                            ${available.length === 0
                                ? `<p class="text-xs text-gray-400 px-2 py-4 text-center">
                                    ${this.availableFields.length === 0
                                        ? 'Add columns first'
                                        : 'All fields are grouped'}
                                   </p>`
                                : available.map(f => this._renderAvailableField(f)).join('')
                            }
                        </div>
                    </div>

                    <!-- Right: group levels -->
                    <div class="flex-1 flex flex-col">
                        <div class="px-4 py-2 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
                            <span class="text-xs font-medium text-gray-600 uppercase tracking-wide">Group levels</span>
                            <span class="text-xs text-gray-400">drag to reorder</span>
                        </div>

                        <div
                            id="gbd-levels"
                            class="flex-1 p-3 space-y-2 overflow-y-auto"
                            data-droptarget="true"
                        >
                            ${this.groupLevels.length === 0
                                ? `<div id="gbd-empty" class="flex flex-col items-center justify-center h-full text-gray-400 py-8 select-none">
                                        <i class="ph ph-arrow-left text-2xl mb-2"></i>
                                        <p class="text-xs">Click a field to add a group level</p>
                                   </div>`
                                : this.groupLevels.map((g, i) => this._renderLevel(g, i)).join('')
                            }
                        </div>
                    </div>
                </div>

                ${this.groupLevels.length > 0 ? `
                <div class="px-4 py-2 bg-indigo-50 border-t border-indigo-100 flex items-center gap-2">
                    <i class="ph ph-info text-indigo-400 text-sm"></i>
                    <p class="text-xs text-indigo-700">
                        SQL: <code class="font-mono">GROUP BY ${this.groupLevels.map(g => g.field).join(', ')}</code>
                    </p>
                </div>` : ''}
            </div>
        `;

        this._attachListeners();
    }

    _renderAvailableField(f) {
        return `
            <button
                class="gbd-add-field w-full text-left text-xs px-2 py-1.5 rounded hover:bg-indigo-50 hover:text-indigo-700 flex items-center gap-2 group transition-colors"
                data-field="${f.name}"
                data-label="${this._esc(f.label || f.displayName || f.name)}"
                title="Add to group"
            >
                <i class="ph ph-plus-circle text-gray-300 group-hover:text-indigo-500 transition-colors flex-shrink-0"></i>
                <span class="truncate">${this._esc(f.label || f.displayName || f.name)}</span>
            </button>
        `;
    }

    _renderLevel(g, index) {
        const ordinals = ['1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th'];
        const badge = ordinals[index] || `${index + 1}th`;
        const badgeColor = index === 0
            ? 'bg-indigo-100 text-indigo-700'
            : index === 1
            ? 'bg-purple-100 text-purple-700'
            : 'bg-gray-100 text-gray-600';

        return `
            <div
                class="gbd-level flex items-center gap-2 px-3 py-2 bg-white border border-gray-200 rounded-lg shadow-sm cursor-grab select-none hover:border-indigo-300 transition-colors"
                draggable="true"
                data-index="${index}"
            >
                <!-- Drag handle -->
                <i class="ph ph-dots-six-vertical text-gray-300 flex-shrink-0 text-base"></i>

                <!-- Ordinal badge -->
                <span class="text-xs font-semibold px-1.5 py-0.5 rounded ${badgeColor} flex-shrink-0">${badge}</span>

                <!-- Field name -->
                <span class="flex-1 text-sm font-medium text-gray-800 truncate">${this._esc(g.label)}</span>
                <code class="text-xs text-gray-400 font-mono truncate max-w-[100px]">${this._esc(g.field)}</code>

                <!-- Move buttons -->
                <div class="flex items-center gap-0.5 flex-shrink-0">
                    <button class="gbd-move-up p-0.5 rounded text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 transition-colors disabled:opacity-30"
                        data-index="${index}" ${index === 0 ? 'disabled' : ''} title="Move up">
                        <i class="ph ph-caret-up text-sm"></i>
                    </button>
                    <button class="gbd-move-down p-0.5 rounded text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 transition-colors disabled:opacity-30"
                        data-index="${index}" ${index === this.groupLevels.length - 1 ? 'disabled' : ''} title="Move down">
                        <i class="ph ph-caret-down text-sm"></i>
                    </button>
                    <button class="gbd-remove p-0.5 rounded text-gray-400 hover:text-red-600 hover:bg-red-50 transition-colors ml-1"
                        data-index="${index}" title="Remove">
                        <i class="ph ph-x text-sm"></i>
                    </button>
                </div>
            </div>
        `;
    }

    // ── Event handling ───────────────────────────────────────────────────────

    _attachListeners() {
        // Add field buttons
        this.container.querySelectorAll('.gbd-add-field').forEach(btn => {
            btn.addEventListener('click', () => {
                this._addLevel(btn.dataset.field, btn.dataset.label);
            });
        });

        // Remove buttons
        this.container.querySelectorAll('.gbd-remove').forEach(btn => {
            btn.addEventListener('click', () => {
                this._removeLevel(parseInt(btn.dataset.index));
            });
        });

        // Move up/down
        this.container.querySelectorAll('.gbd-move-up').forEach(btn => {
            btn.addEventListener('click', () => {
                const i = parseInt(btn.dataset.index);
                if (i > 0) this._moveLevel(i, i - 1);
            });
        });
        this.container.querySelectorAll('.gbd-move-down').forEach(btn => {
            btn.addEventListener('click', () => {
                const i = parseInt(btn.dataset.index);
                if (i < this.groupLevels.length - 1) this._moveLevel(i, i + 1);
            });
        });

        // Clear all
        this.container.querySelector('#gbd-clear-all')?.addEventListener('click', () => {
            this.groupLevels = [];
            this.render();
            this.onGroupByChange([]);
        });

        // Search filter
        this.container.querySelector('#gbd-search')?.addEventListener('input', e => {
            const q = e.target.value.toLowerCase();
            this.container.querySelectorAll('.gbd-add-field').forEach(btn => {
                const text = (btn.dataset.label + btn.dataset.field).toLowerCase();
                btn.closest('button').classList.toggle('hidden', q !== '' && !text.includes(q));
            });
        });

        // Drag-and-drop reordering of levels
        this._attachDragListeners();
    }

    _attachDragListeners() {
        const levels = this.container.querySelectorAll('.gbd-level');
        const dropZone = this.container.querySelector('#gbd-levels');

        levels.forEach(el => {
            el.addEventListener('dragstart', e => {
                this._dragSrcIndex = parseInt(el.dataset.index);
                e.dataTransfer.effectAllowed = 'move';
                el.classList.add('opacity-50');
            });
            el.addEventListener('dragend', () => {
                el.classList.remove('opacity-50');
                dropZone?.querySelectorAll('.gbd-level').forEach(l => l.classList.remove('border-indigo-400'));
            });
            el.addEventListener('dragover', e => {
                e.preventDefault();
                e.dataTransfer.dropEffect = 'move';
                levels.forEach(l => l.classList.remove('border-indigo-400', 'border-dashed'));
                el.classList.add('border-indigo-400', 'border-dashed');
            });
            el.addEventListener('drop', e => {
                e.preventDefault();
                const toIndex = parseInt(el.dataset.index);
                if (this._dragSrcIndex !== null && this._dragSrcIndex !== toIndex) {
                    this._moveLevel(this._dragSrcIndex, toIndex);
                }
                this._dragSrcIndex = null;
            });
        });
    }

    // ── Mutations ────────────────────────────────────────────────────────────

    _addLevel(field, label) {
        if (this.groupLevels.some(g => g.field === field)) return; // already there
        this.groupLevels.push({ field, label });
        this.render();
        this.onGroupByChange(this.getGroupBy());
    }

    _removeLevel(index) {
        this.groupLevels.splice(index, 1);
        this.render();
        this.onGroupByChange(this.getGroupBy());
    }

    _moveLevel(from, to) {
        const [item] = this.groupLevels.splice(from, 1);
        this.groupLevels.splice(to, 0, item);
        this.render();
        this.onGroupByChange(this.getGroupBy());
    }

    // ── Helpers ──────────────────────────────────────────────────────────────

    _alreadyGrouped() {
        return new Set(this.groupLevels.map(g => g.field));
    }

    _esc(str = '') {
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }
}
