/**
 * Visual Dashboard Canvas Component
 *
 * Drag-and-drop dashboard layout builder using GridStack.js for widget positioning.
 * Features:
 * - 12-column responsive grid layout
 * - Drag-and-drop widget placement
 * - Visual resize handles
 * - Snap-to-grid alignment
 * - Copy/paste/duplicate widgets
 * - Undo/redo stack
 */

import { showNotification } from '../assets/js/notifications.js';

export class VisualDashboardCanvas {
    constructor(container, options = {}) {
        this.container = container;
        this.options = options;
        this.widgets = [];
        this.selectedWidget = null;
        this.grid = null;
        this.undoStack = [];
        this.redoStack = [];
        this.onWidgetsChange = options.onWidgetsChange || (() => {});
        this.onWidgetSelect = options.onWidgetSelect || (() => {});

        this.init();
    }

    async init() {
        await this.loadGridStack();
        this.render();
    }

    async loadGridStack() {
        // Load GridStack library if not already loaded
        if (typeof GridStack === 'undefined') {
            return new Promise((resolve, reject) => {
                // Load CSS
                const link = document.createElement('link');
                link.rel = 'stylesheet';
                link.href = 'https://cdn.jsdelivr.net/npm/gridstack@8.4.0/dist/gridstack.min.css';
                document.head.appendChild(link);

                // Load JS
                const script = document.createElement('script');
                script.src = 'https://cdn.jsdelivr.net/npm/gridstack@8.4.0/dist/gridstack-all.js';
                script.onload = resolve;
                script.onerror = reject;
                document.head.appendChild(script);
            });
        }
    }

    render() {
        this.container.innerHTML = `
            <div class="visual-dashboard-canvas h-full flex flex-col">
                <!-- Toolbar -->
                <div class="border-b border-gray-200 bg-white p-3 flex justify-between items-center">
                    <div class="flex gap-2">
                        <button id="undo-btn" class="btn btn-sm btn-secondary" ${this.undoStack.length === 0 ? 'disabled' : ''}>
                            <i class="ph ph-arrow-counter-clockwise mr-1"></i>
                            Undo
                        </button>
                        <button id="redo-btn" class="btn btn-sm btn-secondary" ${this.redoStack.length === 0 ? 'disabled' : ''}>
                            <i class="ph ph-arrow-clockwise mr-1"></i>
                            Redo
                        </button>
                    </div>
                    <div class="flex gap-2">
                        <button id="clear-canvas-btn" class="btn btn-sm btn-secondary">
                            <i class="ph ph-trash mr-1"></i>
                            Clear All
                        </button>
                        <button id="preview-btn" class="btn btn-sm btn-primary">
                            <i class="ph ph-eye mr-1"></i>
                            Preview
                        </button>
                    </div>
                </div>

                <!-- Canvas Area -->
                <div class="flex-1 bg-gray-50 p-6 overflow-auto">
                    <div class="grid-stack" id="dashboard-grid-stack">
                        ${this.renderWidgets()}
                    </div>
                </div>

                <!-- Empty State -->
                ${this.widgets.length === 0 ? `
                    <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
                        <div class="text-center">
                            <i class="ph ph-squares-four text-6xl text-gray-300 mb-4"></i>
                            <p class="text-gray-500 text-lg">Drag widgets from the left panel to start</p>
                        </div>
                    </div>
                ` : ''}
            </div>
        `;

        this.initGridStack();
        this.attachEventListeners();
    }

    renderWidgets() {
        return this.widgets.map(widget => `
            <div class="grid-stack-item" gs-id="${widget.id}" gs-x="${widget.x}" gs-y="${widget.y}" gs-w="${widget.w}" gs-h="${widget.h}">
                <div class="grid-stack-item-content bg-white border-2 ${this.selectedWidget?.id === widget.id ? 'border-blue-500' : 'border-gray-300'} rounded-lg shadow-sm overflow-hidden">
                    <!-- Widget Header -->
                    <div class="widget-header p-3 border-b border-gray-200 flex justify-between items-center cursor-move">
                        <div class="flex items-center gap-2">
                            <i class="${widget.icon || 'ph ph-chart-bar'} text-blue-600"></i>
                            <span class="font-medium text-gray-900 text-sm">${this.escapeHtml(widget.title || 'Untitled Widget')}</span>
                        </div>
                        <div class="flex gap-1">
                            <button class="widget-duplicate-btn text-gray-600 hover:text-blue-600" data-widget-id="${widget.id}" title="Duplicate">
                                <i class="ph ph-copy text-sm"></i>
                            </button>
                            <button class="widget-remove-btn text-gray-600 hover:text-red-600" data-widget-id="${widget.id}" title="Remove">
                                <i class="ph ph-x text-sm"></i>
                            </button>
                        </div>
                    </div>
                    <!-- Widget Content -->
                    <div class="widget-content p-4">
                        ${this.renderWidgetContent(widget)}
                    </div>
                </div>
            </div>
        `).join('');
    }

    renderWidgetContent(widget) {
        switch (widget.type) {
            case 'chart':
                return `
                    <div class="text-center text-gray-400">
                        <i class="ph ph-chart-line text-4xl mb-2"></i>
                        <p class="text-sm">${widget.chartType || 'Chart'} Preview</p>
                    </div>
                `;
            case 'metric':
                return `
                    <div class="text-center">
                        <div class="text-3xl font-bold text-blue-600">1,234</div>
                        <div class="text-sm text-gray-500 mt-1">Sample Metric</div>
                    </div>
                `;
            case 'table':
                return `
                    <div class="text-gray-400 text-sm">
                        <div class="border-b border-gray-200 py-2">Header | Header | Header</div>
                        <div class="py-2">Data | Data | Data</div>
                        <div class="py-2">Data | Data | Data</div>
                    </div>
                `;
            case 'text':
                return `
                    <div class="text-gray-700">
                        ${this.escapeHtml(widget.content || 'Text content')}
                    </div>
                `;
            default:
                return `
                    <div class="text-center text-gray-400">
                        <i class="ph ph-placeholder text-4xl mb-2"></i>
                        <p class="text-sm">Widget Content</p>
                    </div>
                `;
        }
    }

    initGridStack() {
        if (typeof GridStack === 'undefined') {
            console.warn('GridStack not loaded');
            return;
        }

        const gridElement = document.getElementById('dashboard-grid-stack');
        if (!gridElement) return;

        this.grid = GridStack.init({
            column: 12,
            cellHeight: 60,
            acceptWidgets: true,
            removable: false,
            float: false,
            animate: true,
            resizable: {
                handles: 'e, se, s, sw, w'
            }
        }, gridElement);

        // Listen for changes
        this.grid.on('change', (event, items) => {
            if (items) {
                items.forEach(item => {
                    const widgetId = item.el.getAttribute('gs-id');
                    const widget = this.widgets.find(w => w.id === widgetId);
                    if (widget) {
                        widget.x = item.x;
                        widget.y = item.y;
                        widget.w = item.w;
                        widget.h = item.h;
                    }
                });
                this.pushUndo();
                this.notifyChange();
            }
        });

        // Listen for item clicks
        this.grid.on('click', (event) => {
            const item = event.target.closest('.grid-stack-item');
            if (item) {
                const widgetId = item.getAttribute('gs-id');
                this.selectWidget(widgetId);
            }
        });
    }

    attachEventListeners() {
        // Undo/Redo
        document.getElementById('undo-btn')?.addEventListener('click', () => {
            this.undo();
        });

        document.getElementById('redo-btn')?.addEventListener('click', () => {
            this.redo();
        });

        // Clear canvas
        document.getElementById('clear-canvas-btn')?.addEventListener('click', () => {
            this.clearCanvas();
        });

        // Preview
        document.getElementById('preview-btn')?.addEventListener('click', () => {
            this.preview();
        });

        // Widget actions
        this.container.addEventListener('click', (e) => {
            const duplicateBtn = e.target.closest('.widget-duplicate-btn');
            if (duplicateBtn) {
                const widgetId = duplicateBtn.dataset.widgetId;
                this.duplicateWidget(widgetId);
                return;
            }

            const removeBtn = e.target.closest('.widget-remove-btn');
            if (removeBtn) {
                const widgetId = removeBtn.dataset.widgetId;
                this.removeWidget(widgetId);
                return;
            }
        });
    }

    addWidget(widgetConfig) {
        const widget = {
            id: `widget-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            x: 0,
            y: 0,
            w: widgetConfig.defaultWidth || 4,
            h: widgetConfig.defaultHeight || 3,
            type: widgetConfig.type,
            title: widgetConfig.title || 'New Widget',
            icon: widgetConfig.icon,
            chartType: widgetConfig.chartType,
            content: widgetConfig.content,
            config: widgetConfig.config || {}
        };

        this.widgets.push(widget);
        this.pushUndo();

        if (this.grid) {
            this.grid.addWidget({
                id: widget.id,
                x: widget.x,
                y: widget.y,
                w: widget.w,
                h: widget.h,
                content: this.createWidgetElement(widget)
            });
        } else {
            this.render();
        }

        this.selectWidget(widget.id);
        this.notifyChange();
        showNotification('Widget added', 'success');
    }

    createWidgetElement(widget) {
        const div = document.createElement('div');
        div.className = 'grid-stack-item-content bg-white border-2 border-gray-300 rounded-lg shadow-sm overflow-hidden';
        div.innerHTML = `
            <div class="widget-header p-3 border-b border-gray-200 flex justify-between items-center cursor-move">
                <div class="flex items-center gap-2">
                    <i class="${widget.icon || 'ph ph-chart-bar'} text-blue-600"></i>
                    <span class="font-medium text-gray-900 text-sm">${this.escapeHtml(widget.title)}</span>
                </div>
                <div class="flex gap-1">
                    <button class="widget-duplicate-btn text-gray-600 hover:text-blue-600" data-widget-id="${widget.id}">
                        <i class="ph ph-copy text-sm"></i>
                    </button>
                    <button class="widget-remove-btn text-gray-600 hover:text-red-600" data-widget-id="${widget.id}">
                        <i class="ph ph-x text-sm"></i>
                    </button>
                </div>
            </div>
            <div class="widget-content p-4">
                ${this.renderWidgetContent(widget)}
            </div>
        `;
        return div;
    }

    removeWidget(widgetId) {
        if (!confirm('Remove this widget?')) return;

        this.widgets = this.widgets.filter(w => w.id !== widgetId);
        this.pushUndo();

        if (this.grid) {
            const element = document.querySelector(`[gs-id="${widgetId}"]`);
            if (element) {
                this.grid.removeWidget(element);
            }
        }

        if (this.selectedWidget?.id === widgetId) {
            this.selectedWidget = null;
        }

        this.notifyChange();
        showNotification('Widget removed', 'success');
    }

    duplicateWidget(widgetId) {
        const widget = this.widgets.find(w => w.id === widgetId);
        if (!widget) return;

        const duplicate = {
            ...widget,
            id: `widget-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            x: widget.x + 1,
            y: widget.y + 1,
            title: `${widget.title} (Copy)`
        };

        this.widgets.push(duplicate);
        this.pushUndo();

        if (this.grid) {
            this.grid.addWidget({
                id: duplicate.id,
                x: duplicate.x,
                y: duplicate.y,
                w: duplicate.w,
                h: duplicate.h,
                content: this.createWidgetElement(duplicate)
            });
        }

        this.notifyChange();
        showNotification('Widget duplicated', 'success');
    }

    selectWidget(widgetId) {
        this.selectedWidget = this.widgets.find(w => w.id === widgetId);
        this.render();
        this.onWidgetSelect(this.selectedWidget);
    }

    clearCanvas() {
        if (!confirm('Clear all widgets from the canvas?')) return;

        this.widgets = [];
        this.selectedWidget = null;
        this.pushUndo();

        if (this.grid) {
            this.grid.removeAll();
        }

        this.render();
        this.notifyChange();
    }

    preview() {
        showNotification('Opening preview...', 'info');
        // This would open a preview modal or new window
    }

    pushUndo() {
        this.undoStack.push(JSON.stringify(this.widgets));
        this.redoStack = [];

        // Limit undo stack size
        if (this.undoStack.length > 50) {
            this.undoStack.shift();
        }
    }

    undo() {
        if (this.undoStack.length === 0) return;

        this.redoStack.push(JSON.stringify(this.widgets));
        const previousState = this.undoStack.pop();
        this.widgets = JSON.parse(previousState);
        this.render();
        this.notifyChange();
    }

    redo() {
        if (this.redoStack.length === 0) return;

        this.undoStack.push(JSON.stringify(this.widgets));
        const nextState = this.redoStack.pop();
        this.widgets = JSON.parse(nextState);
        this.render();
        this.notifyChange();
    }

    getWidgets() {
        return this.widgets;
    }

    setWidgets(widgets) {
        this.widgets = widgets || [];
        this.render();
    }

    notifyChange() {
        this.onWidgetsChange(this.widgets);
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}
