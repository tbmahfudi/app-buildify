/**
 * FlexMasonry Component
 *
 * Pinterest-style masonry grid layout where items of varying heights
 * flow naturally into columns with minimal gaps.
 *
 * @extends BaseComponent
 *
 * Features:
 * - Responsive column count
 * - Variable item heights
 * - Minimal gap spacing
 * - Lazy loading support
 * - Reflow on window resize
 * - Dynamic item management
 * - Animation support
 * - Column balancing algorithm
 *
 * @example
 * // Image gallery with masonry layout
 * const gallery = new FlexMasonry('#gallery', {
 *   columns: { xs: 1, sm: 2, md: 3, lg: 4 },
 *   gap: 4,
 *   items: [
 *     { id: 'img1', content: '<img src="1.jpg" />' },
 *     { id: 'img2', content: '<img src="2.jpg" />' }
 *   ]
 * });
 *
 * @example
 * // Card masonry with variable heights
 * const cards = new FlexMasonry('#cards', {
 *   columns: { xs: 1, md: 2, lg: 3 },
 *   gap: 6,
 *   animated: true,
 *   items: cardData.map(card => ({
 *     id: card.id,
 *     content: createCardElement(card)
 *   }))
 * });
 */

import { SPACING_SCALE, EVENTS } from '../core/constants.js';
import BaseComponent from '../core/base-component.js';
import { getResponsive } from '../utilities/flex-responsive.js';

export default class FlexMasonry extends BaseComponent {
    /**
     * Default configuration
     */
    static DEFAULTS = {
        columns: { xs: 1, sm: 2, md: 3, lg: 4 },
        gap: 4,
        columnGap: null,
        rowGap: null,
        items: [],
        animated: false,
        lazyLoad: false,
        reflow: true,           // Reflow on resize
        tag: 'div',
        classes: []
    };

    constructor(container, options = {}) {
        super(container, { ...FlexMasonry.DEFAULTS, ...options });

        this.responsive = getResponsive();
        this.masonryElement = null;
        this.columnElements = [];
        this.itemElements = new Map();
        this.resizeObserver = null;
        this.reflowDebounced = null;

        this.init();
    }

    /**
     * Initialize the masonry layout
     */
    init() {
        this.reflowDebounced = this.debounce(() => this.reflow(), 150);
        this.render();
        this.attachEventListeners();
        this.emit(EVENTS.INIT);
    }

    /**
     * Render the masonry layout
     */
    render() {
        // Get or create masonry element
        if (this.container instanceof HTMLElement) {
            this.masonryElement = this.container;
        } else {
            this.masonryElement = document.querySelector(this.container);
        }

        if (!this.masonryElement) {
            console.error(`FlexMasonry: Container not found: ${this.container}`);
            return;
        }

        // Add base classes
        this.masonryElement.classList.add('flex-masonry');

        // Add custom classes
        if (this.options.classes.length > 0) {
            this.masonryElement.classList.add(...this.options.classes);
        }

        // Apply base styles
        this.applyBaseStyles();

        // Create column structure
        this.createColumns();

        // Distribute items to columns
        this.distributeItems();

        this.emit(EVENTS.RENDER);
    }

    /**
     * Apply base styles to masonry container
     */
    applyBaseStyles() {
        this.masonryElement.style.display = 'flex';
        this.masonryElement.style.alignItems = 'flex-start';

        // Apply column gap
        const columnGap = this.options.columnGap !== null ? this.options.columnGap : this.options.gap;
        const columnGapValue = SPACING_SCALE[columnGap] || columnGap;
        this.masonryElement.style.gap = columnGapValue;
    }

    /**
     * Create column elements based on current breakpoint
     */
    createColumns() {
        // Get current column count
        const currentBreakpoint = this.responsive.getCurrentBreakpoint();
        const columnCount = this.getResponsiveValue(this.options.columns, currentBreakpoint);

        // Clear existing columns
        this.masonryElement.innerHTML = '';
        this.columnElements = [];

        // Create columns
        for (let i = 0; i < columnCount; i++) {
            const column = this.createElement('div', ['flex-masonry__column']);
            column.style.flex = '1';
            column.style.display = 'flex';
            column.style.flexDirection = 'column';

            // Apply row gap
            const rowGap = this.options.rowGap !== null ? this.options.rowGap : this.options.gap;
            const rowGapValue = SPACING_SCALE[rowGap] || rowGap;
            column.style.gap = rowGapValue;

            this.columnElements.push(column);
            this.masonryElement.appendChild(column);
        }
    }

    /**
     * Distribute items to columns using balanced algorithm
     */
    distributeItems() {
        if (this.columnElements.length === 0) return;

        // Track column heights for balancing
        const columnHeights = new Array(this.columnElements.length).fill(0);

        // Clear all columns
        this.columnElements.forEach(column => {
            column.innerHTML = '';
        });

        this.itemElements.clear();

        // Distribute each item to shortest column
        this.options.items.forEach((item, index) => {
            const itemElement = this.createItemElement(item, index);

            // Find shortest column
            const shortestColumnIndex = columnHeights.indexOf(Math.min(...columnHeights));

            // Add item to shortest column
            this.columnElements[shortestColumnIndex].appendChild(itemElement);

            // Update column height (estimate based on current content)
            // In real usage, you'd measure actual heights after render
            columnHeights[shortestColumnIndex] += this.estimateItemHeight(item);

            // Store item element
            const itemId = item.id || `item-${index}`;
            this.itemElements.set(itemId, {
                element: itemElement,
                column: shortestColumnIndex
            });
        });

        // Apply animations if enabled
        if (this.options.animated) {
            this.applyAnimations();
        }
    }

    /**
     * Create item element
     */
    createItemElement(item, index) {
        const itemWrapper = this.createElement('div', ['flex-masonry__item']);

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

        // Store item ID
        if (item.id) {
            itemWrapper.dataset.itemId = item.id;
        }

        // Apply item-specific styles
        if (item.style) {
            Object.assign(itemWrapper.style, item.style);
        }

        // Lazy loading
        if (this.options.lazyLoad) {
            const images = itemWrapper.querySelectorAll('img[data-src]');
            images.forEach(img => {
                this.observeLazyImage(img);
            });
        }

        return itemWrapper;
    }

    /**
     * Estimate item height (rough approximation)
     * In real usage, you'd measure after render or use provided height
     */
    estimateItemHeight(item) {
        // If item has explicit height, use it
        if (item.height) {
            return typeof item.height === 'number' ? item.height : parseInt(item.height);
        }

        // Otherwise use rough estimate
        return 200; // Default estimate
    }

    /**
     * Apply animations to items
     */
    applyAnimations() {
        const items = this.masonryElement.querySelectorAll('.flex-masonry__item');

        items.forEach((item, index) => {
            item.style.opacity = '0';
            item.style.transform = 'translateY(20px)';
            item.style.transition = 'opacity 0.3s ease, transform 0.3s ease';

            setTimeout(() => {
                item.style.opacity = '1';
                item.style.transform = 'translateY(0)';
            }, index * 50); // Stagger animation
        });
    }

    /**
     * Observe lazy loading images
     */
    observeLazyImage(img) {
        if (!('IntersectionObserver' in window)) {
            // Fallback: load immediately
            if (img.dataset.src) {
                img.src = img.dataset.src;
                delete img.dataset.src;
            }
            return;
        }

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const image = entry.target;
                    if (image.dataset.src) {
                        image.src = image.dataset.src;
                        delete image.dataset.src;
                        observer.unobserve(image);
                    }
                }
            });
        }, {
            rootMargin: '50px'
        });

        observer.observe(img);
    }

    /**
     * Reflow masonry layout
     */
    reflow() {
        this.createColumns();
        this.distributeItems();

        this.emit('reflow');
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Listen for breakpoint changes
        this.responsive.onBreakpointChange(() => {
            this.reflow();
            this.emit(EVENTS.UPDATE, {
                breakpoint: this.responsive.getCurrentBreakpoint()
            });
        });

        // Listen for window resize
        if (this.options.reflow) {
            window.addEventListener('resize', this.reflowDebounced);
        }

        // Observe item size changes for reflow
        if ('ResizeObserver' in window && this.options.reflow) {
            this.resizeObserver = new ResizeObserver(() => {
                this.reflowDebounced();
            });

            // Observe all items
            this.options.items.forEach((item, index) => {
                const itemId = item.id || `item-${index}`;
                const itemData = this.itemElements.get(itemId);
                if (itemData && itemData.element) {
                    this.resizeObserver.observe(itemData.element);
                }
            });
        }
    }

    /**
     * Add item to masonry
     * @param {object} item - Item configuration
     */
    addItem(item) {
        this.options.items.push(item);
        this.reflow();

        this.emit(EVENTS.ITEM_ADD, { item });
    }

    /**
     * Add multiple items
     * @param {array} items - Array of item configurations
     */
    addItems(items) {
        this.options.items.push(...items);
        this.reflow();

        this.emit(EVENTS.ITEM_ADD, { items });
    }

    /**
     * Remove item from masonry
     * @param {string} itemId - Item ID to remove
     */
    removeItem(itemId) {
        const index = this.options.items.findIndex(item => item.id === itemId);

        if (index === -1) {
            console.warn(`FlexMasonry: Item not found: ${itemId}`);
            return;
        }

        const removedItem = this.options.items.splice(index, 1)[0];

        // Unobserve if using ResizeObserver
        const itemData = this.itemElements.get(itemId);
        if (this.resizeObserver && itemData && itemData.element) {
            this.resizeObserver.unobserve(itemData.element);
        }

        this.reflow();

        this.emit(EVENTS.ITEM_REMOVE, { item: removedItem });
    }

    /**
     * Update item in masonry
     * @param {string} itemId - Item ID to update
     * @param {object} updates - Updates to apply
     */
    updateItem(itemId, updates) {
        const item = this.options.items.find(item => item.id === itemId);

        if (!item) {
            console.warn(`FlexMasonry: Item not found: ${itemId}`);
            return;
        }

        Object.assign(item, updates);
        this.reflow();

        this.emit(EVENTS.ITEM_UPDATE, { itemId, updates });
    }

    /**
     * Clear all items
     */
    clearItems() {
        // Unobserve all items
        if (this.resizeObserver) {
            this.resizeObserver.disconnect();
        }

        this.options.items = [];
        this.reflow();

        this.emit('clear');
    }

    /**
     * Set column count
     * @param {number|object} columns - Column count or responsive config
     */
    setColumns(columns) {
        this.options.columns = typeof columns === 'object' ? columns : { xs: columns };
        this.reflow();

        this.emit(EVENTS.UPDATE, { columns });
    }

    /**
     * Set gap spacing
     * @param {number|string} gap - Gap value
     */
    setGap(gap) {
        this.options.gap = gap;
        this.applyBaseStyles();
        this.reflow();

        this.emit(EVENTS.UPDATE, { gap });
    }

    /**
     * Get all items
     * @returns {array} Array of items
     */
    getItems() {
        return [...this.options.items];
    }

    /**
     * Get item element
     * @param {string} itemId - Item ID
     * @returns {HTMLElement|null} Item element or null
     */
    getItemElement(itemId) {
        const itemData = this.itemElements.get(itemId);
        return itemData ? itemData.element : null;
    }

    /**
     * Get masonry element
     * @returns {HTMLElement}
     */
    getElement() {
        return this.masonryElement;
    }

    /**
     * Destroy the masonry layout
     */
    destroy() {
        // Remove event listeners
        if (this.reflowDebounced) {
            window.removeEventListener('resize', this.reflowDebounced);
        }

        // Disconnect ResizeObserver
        if (this.resizeObserver) {
            this.resizeObserver.disconnect();
        }

        // Remove classes
        this.masonryElement.classList.remove('flex-masonry');

        if (this.options.classes.length > 0) {
            this.masonryElement.classList.remove(...this.options.classes);
        }

        // Remove inline styles
        this.masonryElement.style.display = '';
        this.masonryElement.style.alignItems = '';
        this.masonryElement.style.gap = '';

        // Clear items
        this.itemElements.clear();
        this.columnElements = [];

        this.emit(EVENTS.DESTROY);

        super.destroy();
    }
}
