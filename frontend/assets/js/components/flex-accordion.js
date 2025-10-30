/**
 * FlexAccordion Component
 *
 * Collapsible accordion/disclosure component with animated transitions
 *
 * @author Claude Code
 * @version 1.0.0
 */

import BaseComponent from '../core/base-component.js';

export default class FlexAccordion extends BaseComponent {
    /**
     * Default configuration
     */
    static DEFAULTS = {
        items: [],                       // Array of accordion items
        allowMultiple: false,            // Allow multiple panels open
        defaultOpen: [],                 // IDs of items open by default
        animated: true,                  // Animated transitions
        iconPosition: 'right',           // left | right
        icon: {
            collapsed: 'ph ph-caret-right',
            expanded: 'ph ph-caret-down'
        },
        variant: 'bordered',             // bordered | separated | flush
        classes: [],                     // Additional CSS classes
        onToggle: null,                  // Toggle event callback
        onOpen: null,                    // Open event callback
        onClose: null                    // Close event callback
    };

    /**
     * Constructor
     */
    constructor(element, options = {}) {
        super(element, options);

        this.state = {
            openItems: new Set(this.options.defaultOpen)
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
        const wrapper = this.createWrapper();

        this.options.items.forEach((item, index) => {
            const accordionItem = this.createAccordionItem(item, index);
            wrapper.appendChild(accordionItem);
        });

        // Clear and replace content
        this.element.innerHTML = '';
        this.element.appendChild(wrapper);

        this.emit('render');
    }

    /**
     * Create wrapper element
     */
    createWrapper() {
        const wrapper = document.createElement('div');
        wrapper.className = `flex-accordion ${this.options.classes.join(' ')}`;

        if (this.options.variant === 'bordered') {
            wrapper.classList.add('border', 'border-gray-200', 'rounded-lg', 'divide-y', 'divide-gray-200');
        } else if (this.options.variant === 'separated') {
            wrapper.classList.add('space-y-2');
        }
        // flush variant has no special classes

        return wrapper;
    }

    /**
     * Create accordion item
     */
    createAccordionItem(item, index) {
        const itemWrapper = document.createElement('div');
        itemWrapper.className = 'flex-accordion-item';
        itemWrapper.dataset.itemId = item.id;

        if (this.options.variant === 'separated') {
            itemWrapper.classList.add('border', 'border-gray-200', 'rounded-lg', 'overflow-hidden');
        }

        const isOpen = this.state.openItems.has(item.id);
        const isDisabled = item.disabled || false;

        // Header
        const header = this.createHeader(item, isOpen, isDisabled);
        itemWrapper.appendChild(header);

        // Content
        const content = this.createContent(item, isOpen);
        itemWrapper.appendChild(content);

        return itemWrapper;
    }

    /**
     * Create header element
     */
    createHeader(item, isOpen, isDisabled) {
        const header = document.createElement('button');
        header.type = 'button';
        header.className = 'flex-accordion-header w-full flex items-center justify-between gap-3 px-4 py-3 text-left transition-colors';
        header.dataset.itemId = item.id;

        if (this.options.variant === 'flush') {
            header.classList.add('border-b', 'border-gray-200');
        }

        if (isDisabled) {
            header.classList.add('opacity-50', 'cursor-not-allowed');
            header.disabled = true;
        } else {
            header.classList.add('hover:bg-gray-50', 'cursor-pointer');
        }

        // Icon (left position)
        if (this.options.iconPosition === 'left') {
            const icon = this.createIcon(isOpen);
            header.appendChild(icon);
        }

        // Title wrapper
        const titleWrapper = document.createElement('div');
        titleWrapper.className = 'flex-1';

        const title = document.createElement('span');
        title.className = 'flex-accordion-title font-medium text-gray-900';
        title.textContent = item.title || item.header;

        titleWrapper.appendChild(title);

        if (item.subtitle) {
            const subtitle = document.createElement('span');
            subtitle.className = 'flex-accordion-subtitle block text-sm text-gray-500 mt-0.5';
            subtitle.textContent = item.subtitle;
            titleWrapper.appendChild(subtitle);
        }

        header.appendChild(titleWrapper);

        // Icon (right position)
        if (this.options.iconPosition === 'right') {
            const icon = this.createIcon(isOpen);
            header.appendChild(icon);
        }

        // ARIA attributes
        header.setAttribute('aria-expanded', isOpen.toString());
        header.setAttribute('aria-controls', `accordion-content-${item.id}`);

        return header;
    }

    /**
     * Create icon element
     */
    createIcon(isOpen) {
        const icon = document.createElement('i');
        icon.className = `flex-accordion-icon transition-transform duration-200 text-gray-500`;

        if (isOpen) {
            icon.className += ` ${this.options.icon.expanded}`;
        } else {
            icon.className += ` ${this.options.icon.collapsed}`;
        }

        return icon;
    }

    /**
     * Create content element
     */
    createContent(item, isOpen) {
        const content = document.createElement('div');
        content.className = 'flex-accordion-content overflow-hidden';
        content.id = `accordion-content-${item.id}`;
        content.setAttribute('role', 'region');

        // Content wrapper (for padding)
        const contentWrapper = document.createElement('div');
        contentWrapper.className = 'px-4 py-3 text-gray-700';

        if (typeof item.content === 'string') {
            contentWrapper.innerHTML = item.content;
        } else if (item.content instanceof HTMLElement) {
            contentWrapper.appendChild(item.content);
        }

        content.appendChild(contentWrapper);

        // Set initial state
        if (this.options.animated) {
            content.style.transition = 'max-height 0.3s ease-out, opacity 0.3s ease-out';
        }

        if (isOpen) {
            content.style.maxHeight = content.scrollHeight + 'px';
            content.style.opacity = '1';
        } else {
            content.style.maxHeight = '0';
            content.style.opacity = '0';
        }

        return content;
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        const headers = this.element.querySelectorAll('.flex-accordion-header');

        headers.forEach(header => {
            header.addEventListener('click', (e) => {
                const itemId = header.dataset.itemId;

                if (!header.disabled) {
                    this.toggle(itemId);
                }
            });
        });
    }

    /**
     * Toggle accordion item
     */
    toggle(itemId) {
        const isOpen = this.state.openItems.has(itemId);

        if (isOpen) {
            this.close(itemId);
        } else {
            this.open(itemId);
        }

        this.emit('toggle', { itemId, isOpen: !isOpen });

        if (this.options.onToggle) {
            this.options.onToggle(itemId, !isOpen);
        }
    }

    /**
     * Open accordion item
     */
    open(itemId) {
        // Close others if not allowing multiple
        if (!this.options.allowMultiple) {
            this.state.openItems.forEach(id => {
                if (id !== itemId) {
                    this.close(id);
                }
            });
        }

        this.state.openItems.add(itemId);

        // Update UI
        const itemElement = this.element.querySelector(`[data-item-id="${itemId}"]`);
        if (!itemElement) return;

        const header = itemElement.querySelector('.flex-accordion-header');
        const content = itemElement.querySelector('.flex-accordion-content');
        const icon = header?.querySelector('.flex-accordion-icon');

        if (header) {
            header.setAttribute('aria-expanded', 'true');
        }

        if (icon) {
            icon.className = `flex-accordion-icon transition-transform duration-200 text-gray-500 ${this.options.icon.expanded}`;
        }

        if (content) {
            content.style.maxHeight = content.scrollHeight + 'px';
            content.style.opacity = '1';
        }

        this.emit('open', { itemId });

        if (this.options.onOpen) {
            this.options.onOpen(itemId);
        }
    }

    /**
     * Close accordion item
     */
    close(itemId) {
        this.state.openItems.delete(itemId);

        // Update UI
        const itemElement = this.element.querySelector(`[data-item-id="${itemId}"]`);
        if (!itemElement) return;

        const header = itemElement.querySelector('.flex-accordion-header');
        const content = itemElement.querySelector('.flex-accordion-content');
        const icon = header?.querySelector('.flex-accordion-icon');

        if (header) {
            header.setAttribute('aria-expanded', 'false');
        }

        if (icon) {
            icon.className = `flex-accordion-icon transition-transform duration-200 text-gray-500 ${this.options.icon.collapsed}`;
        }

        if (content) {
            content.style.maxHeight = '0';
            content.style.opacity = '0';
        }

        this.emit('close', { itemId });

        if (this.options.onClose) {
            this.options.onClose(itemId);
        }
    }

    /**
     * Open all items
     */
    openAll() {
        if (this.options.allowMultiple) {
            this.options.items.forEach(item => {
                if (!item.disabled) {
                    this.open(item.id);
                }
            });
        }
    }

    /**
     * Close all items
     */
    closeAll() {
        this.options.items.forEach(item => {
            this.close(item.id);
        });
    }

    /**
     * Check if item is open
     */
    isOpen(itemId) {
        return this.state.openItems.has(itemId);
    }

    /**
     * Get open items
     */
    getOpenItems() {
        return Array.from(this.state.openItems);
    }

    /**
     * Add item
     */
    addItem(item) {
        this.options.items.push(item);
        this.render();
        this.attachEventListeners();
        this.emit('item:add', { item });
    }

    /**
     * Remove item
     */
    removeItem(itemId) {
        const index = this.options.items.findIndex(item => item.id === itemId);

        if (index !== -1) {
            const removed = this.options.items.splice(index, 1)[0];
            this.state.openItems.delete(itemId);
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
     * Destroy component
     */
    destroy() {
        const headers = this.element.querySelectorAll('.flex-accordion-header');
        headers.forEach(header => {
            header.removeEventListener('click', this.handleClick);
        });

        super.destroy();
    }
}
