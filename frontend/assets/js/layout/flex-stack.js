/**
 * FlexStack - Flexible Stack Layout Component
 *
 * A simple yet powerful 1-dimensional layout component (row or column)
 * with consistent spacing, alignment, and responsive behavior.
 *
 * @author Claude Code
 * @version 1.0.0
 */

import { BaseComponent } from '../core/base-component.js';
import { EVENTS, SPACING_SCALE } from '../core/constants.js';
import { getResponsive } from '../utilities/flex-responsive.js';

export class FlexStack extends BaseComponent {
    /**
     * Create a new FlexStack instance
     * @param {string|HTMLElement} container - Container selector or element
     * @param {Object} options - Configuration options
     */
    constructor(container, options = {}) {
        super(container, options);

        // Default options
        const defaults = {
            // Layout
            direction: 'horizontal', // horizontal | vertical | responsive object
            gap: 4,
            wrap: false,

            // Alignment
            align: 'stretch', // start | center | end | stretch | baseline
            justify: 'start', // start | center | end | between | around | evenly

            // Divider
            divider: {
                enabled: false,
                variant: 'line', // line | dashed | dotted
                color: 'gray-300',
                thickness: '1px'
            },

            // Items
            items: [],

            // Behavior
            animated: false,
            responsive: null, // { xs: {...}, md: {...} }

            // Classes
            className: '',

            // Callbacks
            onItemAdd: null,
            onItemRemove: null,
            onChange: null
        };

        this.options = this.mergeOptions(defaults, options);

        // Get responsive instance
        this.responsive = getResponsive();

        // Items storage
        this.items = new Map();

        // Current direction (resolved from responsive config)
        this.currentDirection = null;

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
        if (!this.options.responsive) return;

        this.responsiveUnsubscribe = this.responsive.onBreakpointChange(() => {
            this.updateResponsiveStyles();
        });

        // Initial update
        this.updateResponsiveStyles();
    }

    /**
     * Update styles based on current breakpoint
     */
    updateResponsiveStyles() {
        const bp = this.responsive.getCurrentBreakpoint();

        // Get responsive direction
        if (typeof this.options.direction === 'object') {
            const newDirection = this.responsive.getResponsiveValue(this.options.direction, bp);
            if (newDirection !== this.currentDirection) {
                this.currentDirection = newDirection;
                this.updateDirection(newDirection);
            }
        }

        // Get responsive gap
        if (typeof this.options.gap === 'object') {
            const newGap = this.responsive.getResponsiveValue(this.options.gap, bp);
            this.updateGap(newGap);
        }

        // Apply responsive options if configured
        if (this.options.responsive && this.options.responsive[bp]) {
            const responsiveOpts = this.options.responsive[bp];

            if (responsiveOpts.direction !== undefined) {
                this.updateDirection(responsiveOpts.direction);
            }
            if (responsiveOpts.gap !== undefined) {
                this.updateGap(responsiveOpts.gap);
            }
            if (responsiveOpts.align !== undefined) {
                this.updateAlign(responsiveOpts.align);
            }
            if (responsiveOpts.justify !== undefined) {
                this.updateJustify(responsiveOpts.justify);
            }
        }
    }

    /**
     * Render component
     */
    render() {
        // Create main stack container
        const stack = this.createElement('div', this.getStackClasses());

        // Store reference
        this.elements.main = stack;

        // Add to container
        this.container.innerHTML = '';
        this.container.appendChild(stack);

        this.emit(EVENTS.RENDER);
    }

    /**
     * Get stack classes
     */
    getStackClasses() {
        const classes = ['flex-stack', 'flex'];

        // Direction
        const direction = typeof this.options.direction === 'string'
            ? this.options.direction
            : this.responsive.getResponsiveValue(this.options.direction);

        this.currentDirection = direction;

        if (direction === 'vertical') {
            classes.push('flex-col');
        } else {
            classes.push('flex-row');
        }

        // Wrap
        if (this.options.wrap) {
            classes.push('flex-wrap');
        }

        // Alignment
        const alignMap = {
            start: 'items-start',
            center: 'items-center',
            end: 'items-end',
            stretch: 'items-stretch',
            baseline: 'items-baseline'
        };
        classes.push(alignMap[this.options.align] || 'items-stretch');

        // Justify
        const justifyMap = {
            start: 'justify-start',
            center: 'justify-center',
            end: 'justify-end',
            between: 'justify-between',
            around: 'justify-around',
            evenly: 'justify-evenly'
        };
        classes.push(justifyMap[this.options.justify] || 'justify-start');

        // Gap
        const gap = typeof this.options.gap === 'number'
            ? this.options.gap
            : this.responsive.getResponsiveValue(this.options.gap);
        classes.push(`gap-${gap}`);

        // Custom classes
        if (this.options.className) {
            classes.push(this.options.className);
        }

        return classes;
    }

    /**
     * Add items to stack
     * @param {Array} items - Items to add
     */
    addItems(items) {
        if (!Array.isArray(items)) return;

        items.forEach(item => this.addItem(item));
    }

    /**
     * Add single item to stack
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
                align: null,
                order: null,
                shrink: null,
                grow: null
            };
        }

        return {
            id: item.id || `item-${this.items.size}`,
            content: item.content,
            align: item.align || null,
            order: item.order || null,
            shrink: item.shrink !== undefined ? item.shrink : null,
            grow: item.grow !== undefined ? item.grow : null
        };
    }

    /**
     * Render single item
     */
    renderItem(item) {
        const container = this.elements.main;

        // Check if we need divider before this item
        if (this.options.divider.enabled && this.items.size > 1) {
            const divider = this.renderDivider();
            container.appendChild(divider);
        }

        // Create item wrapper
        const itemWrapper = this.createElement('div', 'flex-stack-item', {
            dataset: { id: item.id }
        });

        // Apply item-specific styles
        if (item.align) {
            const alignMap = {
                start: 'self-start',
                center: 'self-center',
                end: 'self-end',
                stretch: 'self-stretch',
                baseline: 'self-baseline'
            };
            this.addClass(itemWrapper, alignMap[item.align]);
        }

        if (item.order !== null) {
            itemWrapper.style.order = item.order;
        }

        if (item.shrink !== null) {
            itemWrapper.style.flexShrink = item.shrink;
        }

        if (item.grow !== null) {
            itemWrapper.style.flexGrow = item.grow;
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
     * Render divider
     */
    renderDivider() {
        const divider = this.createElement('div', 'flex-stack-divider');

        const isVertical = this.currentDirection === 'vertical';
        const { variant, color, thickness } = this.options.divider;

        // Base styles
        if (isVertical) {
            divider.classList.add('border-t', `border-${color}`);
            divider.style.height = thickness;
        } else {
            divider.classList.add('border-l', `border-${color}`);
            divider.style.width = thickness;
        }

        // Variant styles
        if (variant === 'dashed') {
            divider.style.borderStyle = 'dashed';
        } else if (variant === 'dotted') {
            divider.style.borderStyle = 'dotted';
        }

        return divider;
    }

    /**
     * Remove item from stack
     * @param {string} itemId - Item ID to remove
     */
    removeItem(itemId) {
        const item = this.items.get(itemId);
        if (!item) return;

        // Find and remove element
        const element = this.elements.main.querySelector(`[data-id="${itemId}"]`);
        if (element) {
            // Also remove adjacent divider if exists
            const prevSibling = element.previousElementSibling;
            if (prevSibling && prevSibling.classList.contains('flex-stack-divider')) {
                prevSibling.remove();
            }

            element.remove();
        }

        // Remove from storage
        this.items.delete(itemId);

        this.emit(EVENTS.ITEM_REMOVE, { itemId });

        if (this.options.onItemRemove) {
            this.options.onItemRemove(itemId);
        }
    }

    /**
     * Insert item at specific position
     * @param {Object} item - Item to insert
     * @param {number} index - Position to insert at
     */
    insertItem(item, index) {
        const normalizedItem = this.normalizeItem(item);
        this.items.set(normalizedItem.id, normalizedItem);

        // Get all item elements
        const itemElements = Array.from(this.elements.main.querySelectorAll('.flex-stack-item'));

        // Create new item wrapper
        const itemWrapper = this.createElement('div', 'flex-stack-item', {
            dataset: { id: normalizedItem.id }
        });

        if (typeof normalizedItem.content === 'string') {
            itemWrapper.innerHTML = normalizedItem.content;
        } else if (normalizedItem.content instanceof HTMLElement) {
            itemWrapper.appendChild(normalizedItem.content);
        }

        // Insert at position
        if (index >= itemElements.length) {
            this.elements.main.appendChild(itemWrapper);
        } else {
            const refElement = itemElements[index];
            this.elements.main.insertBefore(itemWrapper, refElement);
        }

        this.emit(EVENTS.ITEM_ADD, { item: normalizedItem });
    }

    /**
     * Update direction
     * @param {string} direction - New direction
     */
    updateDirection(direction) {
        this.currentDirection = direction;
        this.removeClass(this.elements.main, ['flex-row', 'flex-col']);

        if (direction === 'vertical') {
            this.addClass(this.elements.main, 'flex-col');
        } else {
            this.addClass(this.elements.main, 'flex-row');
        }
    }

    /**
     * Update gap
     * @param {number} gap - New gap value
     */
    updateGap(gap) {
        // Remove old gap classes
        for (let i = 0; i <= 12; i++) {
            this.removeClass(this.elements.main, `gap-${i}`);
        }

        // Add new gap class
        this.addClass(this.elements.main, `gap-${gap}`);
    }

    /**
     * Update alignment
     * @param {string} align - New alignment
     */
    updateAlign(align) {
        const alignMap = {
            start: 'items-start',
            center: 'items-center',
            end: 'items-end',
            stretch: 'items-stretch',
            baseline: 'items-baseline'
        };

        // Remove old alignment
        Object.values(alignMap).forEach(cls => this.removeClass(this.elements.main, cls));

        // Add new alignment
        this.addClass(this.elements.main, alignMap[align]);
    }

    /**
     * Update justify
     * @param {string} justify - New justify value
     */
    updateJustify(justify) {
        const justifyMap = {
            start: 'justify-start',
            center: 'justify-center',
            end: 'justify-end',
            between: 'justify-between',
            around: 'justify-around',
            evenly: 'justify-evenly'
        };

        // Remove old justify
        Object.values(justifyMap).forEach(cls => this.removeClass(this.elements.main, cls));

        // Add new justify
        this.addClass(this.elements.main, justifyMap[justify]);
    }

    /**
     * Set direction
     * @param {string} direction - Direction to set
     */
    setDirection(direction) {
        this.options.direction = direction;
        this.updateDirection(direction);
    }

    /**
     * Set gap
     * @param {number} gap - Gap to set
     */
    setGap(gap) {
        this.options.gap = gap;
        this.updateGap(gap);
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
        this.items.clear();
        this.elements.main.innerHTML = '';
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

export default FlexStack;
