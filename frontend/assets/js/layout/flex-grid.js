/**
 * FlexGrid - Responsive Grid Layout Component
 *
 * A powerful 2-dimensional grid layout with responsive columns,
 * column/row spanning, and flexible item management.
 *
 * @author Claude Code
 * @version 1.0.0
 */

import { BaseComponent } from '../core/base-component.js';
import { EVENTS } from '../core/constants.js';
import { getResponsive } from '../utilities/flex-responsive.js';

export class FlexGrid extends BaseComponent {
    /**
     * Create a new FlexGrid instance
     * @param {string|HTMLElement} container - Container selector or element
     * @param {Object} options - Configuration options
     */
    constructor(container, options = {}) {
        super(container, options);

        // Default options
        const defaults = {
            // Columns
            columns: {
                xs: 1,
                sm: 2,
                md: 3,
                lg: 4
            },

            // Spacing
            gap: 6,
            columnGap: null, // Use gap if not specified
            rowGap: null,    // Use gap if not specified

            // Behavior
            equalHeight: false,
            dense: false,
            animated: false,

            // Items
            items: [],

            // Classes
            className: '',

            // Callbacks
            onItemAdd: null,
            onItemRemove: null,
            onReorder: null,
            onBreakpointChange: null,
            onChange: null
        };

        this.options = this.mergeOptions(defaults, options);

        // Get responsive instance
        this.responsive = getResponsive();

        // Items storage
        this.items = new Map();

        // Current state
        this.currentColumns = null;

        // Initialize
        this.init();
    }

    /**
     * Initialize component
     */
    init() {
        this.render();
        this.setupResponsive();
        this.addItems(this.options.items);
        this.setState({ initialized: true });
        this.emit(EVENTS.INIT);
    }

    /**
     * Setup responsive behavior
     */
    setupResponsive() {
        this.responsiveUnsubscribe = this.responsive.onBreakpointChange((breakpoint) => {
            this.updateResponsiveStyles();

            if (this.options.onBreakpointChange) {
                this.options.onBreakpointChange(breakpoint);
            }
        });

        // Initial update
        this.updateResponsiveStyles();
    }

    /**
     * Update styles based on current breakpoint
     */
    updateResponsiveStyles() {
        const bp = this.responsive.getCurrentBreakpoint();

        // Get responsive columns
        const newColumns = this.responsive.getResponsiveValue(this.options.columns, bp);
        if (newColumns !== this.currentColumns) {
            this.currentColumns = newColumns;
            this.updateColumns(newColumns);
        }

        // Get responsive gap
        if (typeof this.options.gap === 'object') {
            const newGap = this.responsive.getResponsiveValue(this.options.gap, bp);
            this.updateGap(newGap);
        }
    }

    /**
     * Render component
     */
    render() {
        // Create main grid container
        const grid = this.createElement('div', this.getGridClasses());

        // Store reference
        this.elements.main = grid;

        // Add to container
        this.container.innerHTML = '';
        this.container.appendChild(grid);

        this.emit(EVENTS.RENDER);
    }

    /**
     * Get grid classes
     */
    getGridClasses() {
        const classes = ['flex-grid', 'grid'];

        // Columns - Generate responsive classes
        const bp = this.responsive.getCurrentBreakpoint();
        const columns = this.responsive.getResponsiveValue(this.options.columns, bp);
        this.currentColumns = columns;

        // Add responsive column classes
        if (typeof this.options.columns === 'object') {
            Object.entries(this.options.columns).forEach(([breakpoint, cols]) => {
                if (breakpoint === 'xs') {
                    classes.push(`grid-cols-${cols}`);
                } else {
                    classes.push(`${breakpoint}:grid-cols-${cols}`);
                }
            });
        } else {
            classes.push(`grid-cols-${this.options.columns}`);
        }

        // Gap
        const gap = typeof this.options.gap === 'number'
            ? this.options.gap
            : this.responsive.getResponsiveValue(this.options.gap);

        if (this.options.columnGap !== null || this.options.rowGap !== null) {
            const colGap = this.options.columnGap !== null ? this.options.columnGap : gap;
            const rowGap = this.options.rowGap !== null ? this.options.rowGap : gap;
            classes.push(`gap-x-${colGap}`, `gap-y-${rowGap}`);
        } else {
            classes.push(`gap-${gap}`);
        }

        // Equal height
        if (this.options.equalHeight) {
            classes.push('auto-rows-fr');
        }

        // Dense packing
        if (this.options.dense) {
            classes.push('grid-flow-dense');
        }

        // Custom classes
        if (this.options.className) {
            classes.push(this.options.className);
        }

        return classes;
    }

    /**
     * Add items to grid
     * @param {Array} items - Items to add
     */
    addItems(items) {
        if (!Array.isArray(items)) return;

        items.forEach(item => this.addItem(item));
    }

    /**
     * Add single item to grid
     * @param {Object|HTMLElement} item - Item to add
     */
    addItem(item) {
        // Normalize item
        const normalizedItem = this.normalizeItem(item);

        // Store item
        this.items.set(normalizedItem.id, normalizedItem);

        // Render item
        this.renderItem(normalizedItem);

        this.emit(EVENTS.ITEM_ADD, { item: normalizedItem });

        if (this.options.onItemAdd) {
            this.options.onItemAdd(normalizedItem);
        }
    }

    /**
     * Normalize item data
     */
    normalizeItem(item) {
        if (item instanceof HTMLElement) {
            return {
                id: `item-${this.items.size}`,
                content: item,
                span: 1,
                rowSpan: 1
            };
        }

        return {
            id: item.id || `item-${this.items.size}`,
            content: item.content,
            span: item.span || 1,
            rowSpan: item.rowSpan || 1
        };
    }

    /**
     * Render single item
     */
    renderItem(item) {
        const container = this.elements.main;

        // Create item wrapper
        const itemWrapper = this.createElement('div', 'flex-grid-item', {
            dataset: { id: item.id }
        });

        // Apply span classes
        if (typeof item.span === 'object') {
            // Responsive span
            Object.entries(item.span).forEach(([breakpoint, spanValue]) => {
                if (breakpoint === 'xs') {
                    this.addClass(itemWrapper, `col-span-${spanValue}`);
                } else {
                    this.addClass(itemWrapper, `${breakpoint}:col-span-${spanValue}`);
                }
            });
        } else if (item.span > 1) {
            this.addClass(itemWrapper, `col-span-${item.span}`);
        }

        // Apply row span
        if (item.rowSpan > 1) {
            this.addClass(itemWrapper, `row-span-${item.rowSpan}`);
        }

        // Add content
        if (typeof item.content === 'string') {
            itemWrapper.innerHTML = item.content;
        } else if (item.content instanceof HTMLElement) {
            itemWrapper.appendChild(item.content);
        }

        // Add animation class if enabled
        if (this.options.animated) {
            this.addClass(itemWrapper, 'transition-all duration-300');
        }

        container.appendChild(itemWrapper);
    }

    /**
     * Remove item from grid
     * @param {string} itemId - Item ID to remove
     */
    removeItem(itemId) {
        const item = this.items.get(itemId);
        if (!item) return;

        // Find and remove element
        const element = this.elements.main.querySelector(`[data-id="${itemId}"]`);
        if (element) {
            if (this.options.animated) {
                element.style.opacity = '0';
                element.style.transform = 'scale(0.8)';
                setTimeout(() => element.remove(), 300);
            } else {
                element.remove();
            }
        }

        // Remove from storage
        this.items.delete(itemId);

        this.emit(EVENTS.ITEM_REMOVE, { itemId });

        if (this.options.onItemRemove) {
            this.options.onItemRemove(itemId);
        }
    }

    /**
     * Update item
     * @param {string} itemId - Item ID to update
     * @param {Object} updates - Properties to update
     */
    updateItem(itemId, updates) {
        const item = this.items.get(itemId);
        if (!item) return;

        // Update item data
        Object.assign(item, updates);

        // Find element and update
        const element = this.elements.main.querySelector(`[data-id="${itemId}"]`);
        if (!element) return;

        // Update span if changed
        if (updates.span !== undefined) {
            // Remove old span classes
            for (let i = 1; i <= 12; i++) {
                this.removeClass(element, `col-span-${i}`);
            }

            // Add new span
            if (typeof updates.span === 'object') {
                Object.entries(updates.span).forEach(([breakpoint, spanValue]) => {
                    if (breakpoint === 'xs') {
                        this.addClass(element, `col-span-${spanValue}`);
                    } else {
                        this.addClass(element, `${breakpoint}:col-span-${spanValue}`);
                    }
                });
            } else if (updates.span > 1) {
                this.addClass(element, `col-span-${updates.span}`);
            }
        }

        // Update content if changed
        if (updates.content !== undefined) {
            element.innerHTML = '';
            if (typeof updates.content === 'string') {
                element.innerHTML = updates.content;
            } else if (updates.content instanceof HTMLElement) {
                element.appendChild(updates.content);
            }
        }

        this.emit(EVENTS.ITEM_UPDATE, { itemId, updates });
    }

    /**
     * Reorder items
     * @param {Array} order - Array of item IDs in new order
     */
    reorder(order) {
        if (!Array.isArray(order)) return;

        const container = this.elements.main;
        const fragment = document.createDocumentFragment();

        // Move elements in specified order
        order.forEach(itemId => {
            const element = container.querySelector(`[data-id="${itemId}"]`);
            if (element) {
                fragment.appendChild(element);
            }
        });

        // Append remaining elements (not in order array)
        const allElements = Array.from(container.children);
        allElements.forEach(element => {
            const id = element.dataset.id;
            if (!order.includes(id)) {
                fragment.appendChild(element);
            }
        });

        container.appendChild(fragment);

        this.emit(EVENTS.REORDER, { order });

        if (this.options.onReorder) {
            this.options.onReorder(order);
        }
    }

    /**
     * Update columns
     * @param {number} columns - Number of columns
     */
    updateColumns(columns) {
        const grid = this.elements.main;

        // Remove old column classes
        for (let i = 1; i <= 12; i++) {
            this.removeClass(grid, `grid-cols-${i}`);
        }

        // Add new column class
        this.addClass(grid, `grid-cols-${columns}`);
    }

    /**
     * Update gap
     * @param {number} gap - Gap value
     */
    updateGap(gap) {
        const grid = this.elements.main;

        // Remove old gap classes
        for (let i = 0; i <= 12; i++) {
            this.removeClass(grid, `gap-${i}`);
            this.removeClass(grid, `gap-x-${i}`);
            this.removeClass(grid, `gap-y-${i}`);
        }

        // Add new gap classes
        if (this.options.columnGap !== null || this.options.rowGap !== null) {
            const colGap = this.options.columnGap !== null ? this.options.columnGap : gap;
            const rowGap = this.options.rowGap !== null ? this.options.rowGap : gap;
            this.addClass(grid, `gap-x-${colGap}`);
            this.addClass(grid, `gap-y-${rowGap}`);
        } else {
            this.addClass(grid, `gap-${gap}`);
        }
    }

    /**
     * Set columns
     * @param {number|Object} columns - Columns configuration
     */
    setColumns(columns) {
        this.options.columns = columns;

        // Re-render grid classes
        const newClasses = this.getGridClasses();
        this.elements.main.className = newClasses.join(' ');

        this.updateResponsiveStyles();
    }

    /**
     * Set gap
     * @param {number} gap - Gap value
     */
    setGap(gap) {
        this.options.gap = gap;
        this.updateGap(gap);
    }

    /**
     * Get current layout
     * @returns {Object} Current grid state
     */
    getLayout() {
        return {
            breakpoint: this.responsive.getCurrentBreakpoint(),
            columns: this.currentColumns,
            itemCount: this.items.size,
            items: this.getItems()
        };
    }

    /**
     * Get all items
     * @returns {Array} Array of items
     */
    getItems() {
        return Array.from(this.items.values());
    }

    /**
     * Clear all items
     */
    clear() {
        if (this.options.animated) {
            const elements = Array.from(this.elements.main.children);
            elements.forEach((el, index) => {
                setTimeout(() => {
                    el.style.opacity = '0';
                    el.style.transform = 'scale(0.8)';
                }, index * 50);
            });

            setTimeout(() => {
                this.items.clear();
                this.elements.main.innerHTML = '';
            }, elements.length * 50 + 300);
        } else {
            this.items.clear();
            this.elements.main.innerHTML = '';
        }
    }

    /**
     * Destroy component
     */
    destroy() {
        if (this.responsiveUnsubscribe) {
            this.responsiveUnsubscribe();
        }

        super.destroy();
    }
}

export default FlexGrid;
