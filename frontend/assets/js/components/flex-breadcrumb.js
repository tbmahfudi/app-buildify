/**
 * FlexBreadcrumb Component
 *
 * Breadcrumb navigation component for hierarchical navigation
 *
 * @author Claude Code
 * @version 1.0.0
 */

import BaseComponent from '../core/base-component.js';

export default class FlexBreadcrumb extends BaseComponent {
    /**
     * Default configuration
     */
    static DEFAULTS = {
        items: [],                       // Array of breadcrumb items
        separator: '/',                  // Separator character or icon
        separatorIcon: null,             // Use icon as separator (e.g., 'ph ph-caret-right')
        showHome: true,                  // Show home icon for first item
        homeIcon: 'ph ph-house',         // Home icon class
        maxItems: null,                  // Max items before collapse
        collapseIcon: 'ph ph-dots-three',// Collapse indicator icon
        size: 'md',                      // sm | md | lg
        classes: [],                     // Additional CSS classes
        onItemClick: null                // Item click callback
    };

    /**
     * Size mappings
     */
    static SIZES = {
        sm: {
            text: 'text-sm',
            icon: 'text-sm',
            gap: 'gap-1.5'
        },
        md: {
            text: 'text-base',
            icon: 'text-base',
            gap: 'gap-2'
        },
        lg: {
            text: 'text-lg',
            icon: 'text-lg',
            gap: 'gap-3'
        }
    };

    /**
     * Constructor
     */
    constructor(element, options = {}) {
        super(element, options);

        this.state = {
            collapsed: false
        };

        this.init();
    }

    /**
     * Initialize component
     */
    init() {
        this.render();
        this.attachEventListeners();
        this.emit('init');
    }

    /**
     * Render component
     */
    render() {
        const nav = this.createNav();
        const list = this.createList();

        const itemsToShow = this.getItemsToShow();

        itemsToShow.forEach((item, index) => {
            const listItem = this.createListItem(item, index, itemsToShow.length);
            list.appendChild(listItem);
        });

        nav.appendChild(list);

        // Clear and replace content
        this.element.innerHTML = '';
        this.element.appendChild(nav);

        this.emit('render');
    }

    /**
     * Create nav element
     */
    createNav() {
        const nav = document.createElement('nav');
        nav.className = `flex-breadcrumb ${this.options.classes.join(' ')}`;
        nav.setAttribute('aria-label', 'Breadcrumb');

        return nav;
    }

    /**
     * Create list element
     */
    createList() {
        const list = document.createElement('ol');
        const gapClass = FlexBreadcrumb.SIZES[this.options.size].gap;

        list.className = `flex items-center ${gapClass} flex-wrap`;

        return list;
    }

    /**
     * Get items to show (with collapse if needed)
     */
    getItemsToShow() {
        if (!this.options.maxItems || this.options.items.length <= this.options.maxItems) {
            return this.options.items;
        }

        // Collapse middle items
        const items = [...this.options.items];
        const firstItem = items[0];
        const lastItems = items.slice(-(this.options.maxItems - 1));

        return [
            firstItem,
            { id: 'collapsed', label: '...', collapsed: true },
            ...lastItems
        ];
    }

    /**
     * Create list item
     */
    createListItem(item, index, totalItems) {
        const li = document.createElement('li');
        li.className = 'flex items-center gap-2';
        li.dataset.itemId = item.id;

        const isFirst = index === 0;
        const isLast = index === totalItems - 1;
        const isActive = item.active || isLast;
        const isDisabled = item.disabled || false;

        // Link or span
        const element = this.createItemElement(item, isFirst, isActive, isDisabled);
        li.appendChild(element);

        // Separator (except for last item)
        if (!isLast) {
            const separator = this.createSeparator();
            li.appendChild(separator);
        }

        return li;
    }

    /**
     * Create item element (link or span)
     */
    createItemElement(item, isFirst, isActive, isDisabled) {
        const element = item.href && !isActive && !isDisabled
            ? document.createElement('a')
            : document.createElement('span');

        const textSizeClass = FlexBreadcrumb.SIZES[this.options.size].text;
        const iconSizeClass = FlexBreadcrumb.SIZES[this.options.size].icon;

        element.className = `flex items-center gap-1.5 ${textSizeClass}`;

        // Styling based on state
        if (isActive) {
            element.className += ' text-gray-900 font-medium';
            element.setAttribute('aria-current', 'page');
        } else if (isDisabled) {
            element.className += ' text-gray-400 cursor-not-allowed';
        } else {
            element.className += ' text-gray-600 hover:text-gray-900 transition-colors cursor-pointer';
        }

        if (element.tagName === 'A') {
            element.href = item.href;
        }

        // Home icon for first item
        if (isFirst && this.options.showHome) {
            const homeIcon = document.createElement('i');
            homeIcon.className = `${this.options.homeIcon} ${iconSizeClass}`;
            element.appendChild(homeIcon);
        }

        // Item icon
        if (item.icon) {
            const icon = document.createElement('i');
            icon.className = `${item.icon} ${iconSizeClass}`;
            element.appendChild(icon);
        }

        // Collapsed indicator
        if (item.collapsed) {
            const collapseIcon = document.createElement('i');
            collapseIcon.className = `${this.options.collapseIcon} ${iconSizeClass}`;
            element.appendChild(collapseIcon);
            return element;
        }

        // Label
        const label = document.createElement('span');
        label.textContent = item.label;
        element.appendChild(label);

        return element;
    }

    /**
     * Create separator
     */
    createSeparator() {
        const separator = document.createElement('span');
        separator.className = 'flex-breadcrumb-separator text-gray-400';
        separator.setAttribute('aria-hidden', 'true');

        if (this.options.separatorIcon) {
            const icon = document.createElement('i');
            const iconSizeClass = FlexBreadcrumb.SIZES[this.options.size].icon;
            icon.className = `${this.options.separatorIcon} ${iconSizeClass}`;
            separator.appendChild(icon);
        } else {
            separator.textContent = this.options.separator;
        }

        return separator;
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        const items = this.element.querySelectorAll('li');

        items.forEach((li, index) => {
            const link = li.querySelector('a, span[class*="cursor-pointer"]');

            if (link && link.tagName === 'A') {
                link.addEventListener('click', (e) => {
                    const itemId = li.dataset.itemId;
                    const item = this.options.items.find(i => i.id === itemId);

                    this.emit('item-click', { item, index });

                    if (this.options.onItemClick) {
                        this.options.onItemClick(item, index, e);
                    }
                });
            }
        });
    }

    /**
     * Add item
     */
    addItem(item, index = null) {
        if (index !== null && index >= 0 && index < this.options.items.length) {
            this.options.items.splice(index, 0, item);
        } else {
            this.options.items.push(item);
        }

        this.render();
        this.attachEventListeners();
        this.emit('item:add', { item, index });
    }

    /**
     * Remove item
     */
    removeItem(itemId) {
        const index = this.options.items.findIndex(i => i.id === itemId);

        if (index !== -1) {
            const removed = this.options.items.splice(index, 1)[0];
            this.render();
            this.attachEventListeners();
            this.emit('item:remove', { item: removed });
        }
    }

    /**
     * Update item
     */
    updateItem(itemId, updates) {
        const item = this.options.items.find(i => i.id === itemId);

        if (item) {
            Object.assign(item, updates);
            this.render();
            this.attachEventListeners();
            this.emit('item:update', { itemId, updates });
        }
    }

    /**
     * Set items
     */
    setItems(items) {
        this.options.items = items;
        this.render();
        this.attachEventListeners();
        this.emit('items-set', { items });
    }

    /**
     * Get items
     */
    getItems() {
        return [...this.options.items];
    }

    /**
     * Navigate to item
     */
    navigateToItem(itemId) {
        const item = this.options.items.find(i => i.id === itemId);

        if (item && item.href) {
            window.location.href = item.href;
        }
    }

    /**
     * Set active item
     */
    setActiveItem(itemId) {
        this.options.items.forEach(item => {
            item.active = item.id === itemId;
        });

        this.render();
        this.attachEventListeners();
    }

    /**
     * Destroy component
     */
    destroy() {
        const items = this.element.querySelectorAll('a');
        items.forEach(item => {
            item.removeEventListener('click', this.handleClick);
        });

        super.destroy();
    }
}
