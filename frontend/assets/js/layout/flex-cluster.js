/**
 * FlexCluster Component
 *
 * Horizontal grouping with flexible spacing and wrapping, useful for toolbars,
 * tag lists, button groups, and chip collections.
 *
 * @extends BaseComponent
 *
 * Features:
 * - Auto-wrap items to new lines
 * - Flexible justify and align options
 * - Consistent gap spacing
 * - Responsive sizing and behavior
 * - Priority-based item ordering
 * - Dynamic item management (add, remove, update)
 * - Support for different item types (buttons, tags, chips)
 *
 * @example
 * // Tag cloud
 * const tags = new FlexCluster('#tags', {
 *   gap: 2,
 *   justify: 'start',
 *   wrap: true,
 *   items: [
 *     { id: 'tag1', content: '<span class="tag">JavaScript</span>' },
 *     { id: 'tag2', content: '<span class="tag">React</span>' }
 *   ]
 * });
 *
 * @example
 * // Toolbar with action buttons
 * const toolbar = new FlexCluster('#toolbar', {
 *   gap: 3,
 *   justify: 'between',
 *   align: 'center',
 *   items: [
 *     { content: '<button>New</button>', priority: 1 },
 *     { content: '<button>Save</button>', priority: 1 },
 *     { content: '<button>Delete</button>', priority: 0 }
 *   ]
 * });
 */

import { SPACING_SCALE, EVENTS } from '../core/constants.js';
import BaseComponent from '../core/base-component.js';
import { getResponsive } from '../utilities/flex-responsive.js';

export default class FlexCluster extends BaseComponent {
    /**
     * Default configuration
     */
    static DEFAULTS = {
        gap: 2,
        justify: 'start',      // start | center | end | between | around | evenly
        align: 'center',       // start | center | end | stretch | baseline
        wrap: true,
        responsive: null,
        items: [],
        animated: false,
        tag: 'div',
        classes: []
    };

    constructor(container, options = {}) {
        super(container, { ...FlexCluster.DEFAULTS, ...options });

        this.responsive = getResponsive();
        this.clusterElement = null;
        this.itemElements = new Map();

        this.init();
    }

    /**
     * Initialize the cluster
     */
    init() {
        this.render();
        this.attachEventListeners();
        this.emit(EVENTS.INIT);
    }

    /**
     * Render the cluster
     */
    render() {
        // Get or create cluster element
        if (this.container instanceof HTMLElement) {
            this.clusterElement = this.container;
        } else {
            this.clusterElement = document.querySelector(this.container);
        }

        if (!this.clusterElement) {
            console.error(`FlexCluster: Container not found: ${this.container}`);
            return;
        }

        // Add base classes
        this.clusterElement.classList.add('flex-cluster');

        // Add custom classes
        if (this.options.classes.length > 0) {
            this.clusterElement.classList.add(...this.options.classes);
        }

        // Apply styles
        this.applyStyles();

        // Render items
        this.renderItems();

        this.emit(EVENTS.RENDER);
    }

    /**
     * Apply cluster styles
     */
    applyStyles() {
        // Set display
        this.clusterElement.style.display = 'flex';

        // Apply wrap
        if (this.options.wrap) {
            this.clusterElement.style.flexWrap = 'wrap';
        } else {
            this.clusterElement.style.flexWrap = 'nowrap';
        }

        // Apply justify
        this.applyJustify();

        // Apply align
        this.applyAlign();

        // Apply gap
        this.applyGap();

        // Apply animation
        if (this.options.animated) {
            this.clusterElement.style.transition = 'all 0.3s ease';
        }
    }

    /**
     * Apply justify content
     */
    applyJustify() {
        const { justify } = this.options;

        const justifyMap = {
            'start': 'flex-start',
            'center': 'center',
            'end': 'flex-end',
            'between': 'space-between',
            'around': 'space-around',
            'evenly': 'space-evenly'
        };

        this.clusterElement.style.justifyContent = justifyMap[justify] || 'flex-start';
    }

    /**
     * Apply align items
     */
    applyAlign() {
        const { align } = this.options;

        const alignMap = {
            'start': 'flex-start',
            'center': 'center',
            'end': 'flex-end',
            'stretch': 'stretch',
            'baseline': 'baseline'
        };

        this.clusterElement.style.alignItems = alignMap[align] || 'center';
    }

    /**
     * Apply gap spacing
     */
    applyGap() {
        const { gap } = this.options;

        const gapValue = SPACING_SCALE[gap] || gap;
        this.clusterElement.style.gap = gapValue;
    }

    /**
     * Render all items
     */
    renderItems() {
        // Clear existing items
        this.clusterElement.innerHTML = '';
        this.itemElements.clear();

        // Sort items by priority (higher priority first)
        const sortedItems = [...this.options.items].sort((a, b) => {
            const priorityA = a.priority !== undefined ? a.priority : 0;
            const priorityB = b.priority !== undefined ? b.priority : 0;
            return priorityB - priorityA;
        });

        // Render each item
        sortedItems.forEach((item, index) => {
            this.renderItem(item, index);
        });
    }

    /**
     * Render individual item
     */
    renderItem(item, index) {
        const itemWrapper = this.createElement('div', ['flex-cluster__item']);

        // Add item content
        if (typeof item.content === 'string') {
            itemWrapper.innerHTML = item.content;
        } else if (item.content instanceof HTMLElement) {
            itemWrapper.appendChild(item.content);
        } else if (item.content && typeof item.content.getElement === 'function') {
            itemWrapper.appendChild(item.content.getElement());
        }

        // Add custom item classes
        if (item.classes) {
            itemWrapper.classList.add(...item.classes);
        }

        // Store item ID for later reference
        if (item.id) {
            itemWrapper.dataset.itemId = item.id;
            this.itemElements.set(item.id, itemWrapper);
        } else {
            this.itemElements.set(`item-${index}`, itemWrapper);
        }

        // Apply item-specific styles
        if (item.style) {
            Object.assign(itemWrapper.style, item.style);
        }

        // Add to cluster
        this.clusterElement.appendChild(itemWrapper);
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Listen for breakpoint changes if responsive config exists
        if (this.options.responsive) {
            this.responsive.onBreakpointChange(() => {
                this.handleResponsiveChange();
                this.emit(EVENTS.UPDATE, {
                    breakpoint: this.responsive.getCurrentBreakpoint()
                });
            });
        }
    }

    /**
     * Handle responsive changes
     */
    handleResponsiveChange() {
        const currentBreakpoint = this.responsive.getCurrentBreakpoint();
        const responsive = this.options.responsive;

        if (!responsive) return;

        // Update gap if responsive
        if (responsive.gap) {
            const newGap = this.getResponsiveValue(responsive.gap, currentBreakpoint);
            if (newGap !== null && newGap !== undefined) {
                this.options.gap = newGap;
                this.applyGap();
            }
        }

        // Update justify if responsive
        if (responsive.justify) {
            const newJustify = this.getResponsiveValue(responsive.justify, currentBreakpoint);
            if (newJustify) {
                this.options.justify = newJustify;
                this.applyJustify();
            }
        }

        // Update wrap if responsive
        if (responsive.wrap !== undefined) {
            const newWrap = this.getResponsiveValue(responsive.wrap, currentBreakpoint);
            if (newWrap !== null && newWrap !== undefined) {
                this.options.wrap = newWrap;
                this.clusterElement.style.flexWrap = newWrap ? 'wrap' : 'nowrap';
            }
        }
    }

    /**
     * Add item to cluster
     * @param {object} item - Item configuration
     * @param {number} index - Optional index to insert at
     */
    addItem(item, index = null) {
        if (index !== null && index >= 0 && index < this.options.items.length) {
            this.options.items.splice(index, 0, item);
        } else {
            this.options.items.push(item);
        }

        this.renderItems();

        this.emit(EVENTS.ITEM_ADD, { item, index });
    }

    /**
     * Remove item from cluster
     * @param {string} itemId - Item ID to remove
     */
    removeItem(itemId) {
        const index = this.options.items.findIndex(item => item.id === itemId);

        if (index === -1) {
            console.warn(`FlexCluster: Item not found: ${itemId}`);
            return;
        }

        const removedItem = this.options.items.splice(index, 1)[0];
        this.renderItems();

        this.emit(EVENTS.ITEM_REMOVE, { item: removedItem, index });
    }

    /**
     * Update item in cluster
     * @param {string} itemId - Item ID to update
     * @param {object} updates - Updates to apply
     */
    updateItem(itemId, updates) {
        const item = this.options.items.find(item => item.id === itemId);

        if (!item) {
            console.warn(`FlexCluster: Item not found: ${itemId}`);
            return;
        }

        Object.assign(item, updates);
        this.renderItems();

        this.emit(EVENTS.ITEM_UPDATE, { itemId, updates });
    }

    /**
     * Clear all items
     */
    clearItems() {
        this.options.items = [];
        this.renderItems();

        this.emit('clear');
    }

    /**
     * Set gap spacing
     * @param {number|string} gap - Gap value
     */
    setGap(gap) {
        this.options.gap = gap;
        this.applyGap();

        this.emit(EVENTS.UPDATE, { gap });
    }

    /**
     * Set justify content
     * @param {string} justify - Justify value
     */
    setJustify(justify) {
        if (!['start', 'center', 'end', 'between', 'around', 'evenly'].includes(justify)) {
            console.warn(`FlexCluster: Invalid justify value "${justify}"`);
            return;
        }

        this.options.justify = justify;
        this.applyJustify();

        this.emit(EVENTS.UPDATE, { justify });
    }

    /**
     * Set align items
     * @param {string} align - Align value
     */
    setAlign(align) {
        if (!['start', 'center', 'end', 'stretch', 'baseline'].includes(align)) {
            console.warn(`FlexCluster: Invalid align value "${align}"`);
            return;
        }

        this.options.align = align;
        this.applyAlign();

        this.emit(EVENTS.UPDATE, { align });
    }

    /**
     * Set wrap behavior
     * @param {boolean} wrap - Whether items should wrap
     */
    setWrap(wrap) {
        this.options.wrap = wrap;
        this.clusterElement.style.flexWrap = wrap ? 'wrap' : 'nowrap';

        this.emit(EVENTS.UPDATE, { wrap });
    }

    /**
     * Get all items
     * @returns {array} Array of items
     */
    getItems() {
        return [...this.options.items];
    }

    /**
     * Get item by ID
     * @param {string} itemId - Item ID
     * @returns {object|null} Item object or null
     */
    getItem(itemId) {
        return this.options.items.find(item => item.id === itemId) || null;
    }

    /**
     * Get item element
     * @param {string} itemId - Item ID
     * @returns {HTMLElement|null} Item element or null
     */
    getItemElement(itemId) {
        return this.itemElements.get(itemId) || null;
    }

    /**
     * Get cluster element
     * @returns {HTMLElement}
     */
    getElement() {
        return this.clusterElement;
    }

    /**
     * Destroy the cluster
     */
    destroy() {
        // Remove classes
        this.clusterElement.classList.remove('flex-cluster');

        if (this.options.classes.length > 0) {
            this.clusterElement.classList.remove(...this.options.classes);
        }

        // Remove inline styles
        this.clusterElement.style.display = '';
        this.clusterElement.style.flexWrap = '';
        this.clusterElement.style.justifyContent = '';
        this.clusterElement.style.alignItems = '';
        this.clusterElement.style.gap = '';
        this.clusterElement.style.transition = '';

        // Clear items
        this.itemElements.clear();

        this.emit(EVENTS.DESTROY);

        super.destroy();
    }
}
