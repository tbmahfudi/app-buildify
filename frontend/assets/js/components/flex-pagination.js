/**
 * FlexPagination - Flexible Pagination Component
 *
 * A reusable pagination component with Tailwind styling supporting:
 * - Multiple display modes (full, compact, simple)
 * - Configurable page button range
 * - First/Last page buttons
 * - Previous/Next buttons
 * - Page info display
 * - Items per page selector
 * - Keyboard navigation
 *
 * @author Claude Code
 * @version 1.0.0
 */

import BaseComponent from '../core/base-component.js';

export default class FlexPagination extends BaseComponent {
    /**
     * Default configuration
     */
    static DEFAULTS = {
        totalItems: 0,              // Total number of items
        itemsPerPage: 10,           // Items per page
        currentPage: 1,             // Current page number
        maxButtons: 5,              // Maximum page buttons to show
        showFirstLast: true,        // Show "First" and "Last" buttons
        showPrevNext: true,         // Show "Previous" and "Next" buttons
        showInfo: true,             // Show "Showing X-Y of Z items"
        showItemsPerPage: true,     // Show items per page selector
        itemsPerPageOptions: [10, 25, 50, 100],
        mode: 'full',               // full | compact | simple
        size: 'md',                 // sm | md | lg
        variant: 'outline',         // outline | filled
        alignment: 'center',        // left | center | right
        classes: [],                // Additional CSS classes
        onChange: null,             // Page change callback
        onItemsPerPageChange: null  // Items per page change callback
    };

    /**
     * Size mappings
     */
    static SIZES = {
        sm: 'px-2 py-1 text-sm',
        md: 'px-3 py-2 text-base',
        lg: 'px-4 py-3 text-lg'
    };

    /**
     * Constructor
     */
    constructor(container, options = {}) {
        super(container, options);

        this.state = {
            currentPage: this.options.currentPage,
            itemsPerPage: this.options.itemsPerPage,
            totalPages: this.calculateTotalPages()
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
     * Calculate total pages
     */
    calculateTotalPages() {
        return Math.ceil(this.options.totalItems / this.state.itemsPerPage) || 1;
    }

    /**
     * Render the pagination
     */
    render() {
        this.state.totalPages = this.calculateTotalPages();

        const wrapper = document.createElement('div');
        const alignmentClasses = {
            left: 'justify-start',
            center: 'justify-center',
            right: 'justify-end'
        };

        wrapper.className = `flex flex-wrap items-center gap-4 ${alignmentClasses[this.options.alignment]} ${this.options.classes.join(' ')}`;

        // Info section
        if (this.options.showInfo && this.options.mode !== 'simple') {
            wrapper.appendChild(this.renderInfo());
        }

        // Page buttons
        wrapper.appendChild(this.renderPageButtons());

        // Items per page selector
        if (this.options.showItemsPerPage && this.options.mode === 'full') {
            wrapper.appendChild(this.renderItemsPerPageSelector());
        }

        this.container.innerHTML = '';
        this.container.appendChild(wrapper);
    }

    /**
     * Render info section
     */
    renderInfo() {
        const start = (this.state.currentPage - 1) * this.state.itemsPerPage + 1;
        const end = Math.min(this.state.currentPage * this.state.itemsPerPage, this.options.totalItems);

        const info = document.createElement('div');
        info.className = 'text-sm text-gray-700';
        info.textContent = this.options.totalItems > 0
            ? `Showing ${start}-${end} of ${this.options.totalItems} items`
            : 'No items';

        return info;
    }

    /**
     * Render page buttons
     */
    renderPageButtons() {
        const nav = document.createElement('nav');
        nav.className = 'flex items-center gap-1';
        nav.setAttribute('role', 'navigation');
        nav.setAttribute('aria-label', 'Pagination');

        const ul = document.createElement('ul');
        ul.className = 'flex items-center gap-1';

        // First button
        if (this.options.showFirstLast && this.options.mode === 'full') {
            ul.appendChild(this.renderButton('First', 1, this.state.currentPage === 1,
                '<i class="ph ph-caret-double-left"></i>'));
        }

        // Previous button
        if (this.options.showPrevNext) {
            ul.appendChild(this.renderButton('Previous', this.state.currentPage - 1, this.state.currentPage === 1,
                '<i class="ph ph-caret-left"></i>'));
        }

        // Page number buttons
        const pageNumbers = this.getPageNumbers();
        pageNumbers.forEach(page => {
            if (page === '...') {
                ul.appendChild(this.renderEllipsis());
            } else {
                ul.appendChild(this.renderButton(page.toString(), page, false, page.toString()));
            }
        });

        // Next button
        if (this.options.showPrevNext) {
            ul.appendChild(this.renderButton('Next', this.state.currentPage + 1,
                this.state.currentPage === this.state.totalPages,
                '<i class="ph ph-caret-right"></i>'));
        }

        // Last button
        if (this.options.showFirstLast && this.options.mode === 'full') {
            ul.appendChild(this.renderButton('Last', this.state.totalPages,
                this.state.currentPage === this.state.totalPages,
                '<i class="ph ph-caret-double-right"></i>'));
        }

        nav.appendChild(ul);
        return nav;
    }

    /**
     * Render a button
     */
    renderButton(label, page, disabled, content) {
        const li = document.createElement('li');
        const button = document.createElement('button');

        const isActive = page === this.state.currentPage;
        const sizeClass = FlexPagination.SIZES[this.options.size];

        let classes = [
            sizeClass,
            'rounded-lg border transition-all duration-200',
            'focus:outline-none focus:ring-2 focus:ring-blue-500',
            'disabled:opacity-50 disabled:cursor-not-allowed'
        ];

        if (this.options.variant === 'outline') {
            classes.push(
                isActive
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
            );
        } else {
            classes.push(
                isActive
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-gray-100 text-gray-700 border-transparent hover:bg-gray-200'
            );
        }

        button.className = classes.join(' ');
        button.disabled = disabled;
        button.setAttribute('aria-label', label);
        button.setAttribute('data-page', page);
        button.innerHTML = content;

        if (isActive) {
            button.setAttribute('aria-current', 'page');
        }

        li.appendChild(button);
        return li;
    }

    /**
     * Render ellipsis
     */
    renderEllipsis() {
        const li = document.createElement('li');
        const span = document.createElement('span');
        span.className = `${FlexPagination.SIZES[this.options.size]} text-gray-500`;
        span.textContent = '...';
        li.appendChild(span);
        return li;
    }

    /**
     * Get page numbers to display
     */
    getPageNumbers() {
        const { currentPage } = this.state;
        const { totalPages } = this.state;
        const { maxButtons } = this.options;

        if (totalPages <= maxButtons) {
            return Array.from({ length: totalPages }, (_, i) => i + 1);
        }

        const pages = [];
        const halfMax = Math.floor(maxButtons / 2);

        let startPage = Math.max(1, currentPage - halfMax);
        let endPage = Math.min(totalPages, currentPage + halfMax);

        // Adjust if at the beginning
        if (currentPage <= halfMax) {
            endPage = maxButtons;
        }

        // Adjust if at the end
        if (currentPage + halfMax >= totalPages) {
            startPage = totalPages - maxButtons + 1;
        }

        // Add first page and ellipsis
        if (startPage > 1) {
            pages.push(1);
            if (startPage > 2) {
                pages.push('...');
            }
        }

        // Add page range
        for (let i = startPage; i <= endPage; i++) {
            pages.push(i);
        }

        // Add ellipsis and last page
        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                pages.push('...');
            }
            pages.push(totalPages);
        }

        return pages;
    }

    /**
     * Render items per page selector
     */
    renderItemsPerPageSelector() {
        const wrapper = document.createElement('div');
        wrapper.className = 'flex items-center gap-2';

        const label = document.createElement('label');
        label.className = 'text-sm text-gray-700';
        label.textContent = 'Items per page:';

        const select = document.createElement('select');
        select.className = `${FlexPagination.SIZES[this.options.size]} border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none`;
        select.setAttribute('data-items-per-page', 'true');

        this.options.itemsPerPageOptions.forEach(option => {
            const opt = document.createElement('option');
            opt.value = option;
            opt.textContent = option;
            opt.selected = option === this.state.itemsPerPage;
            select.appendChild(opt);
        });

        wrapper.appendChild(label);
        wrapper.appendChild(select);

        return wrapper;
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Page button clicks
        this.container.addEventListener('click', (e) => {
            const button = e.target.closest('[data-page]');
            if (button && !button.disabled) {
                const page = parseInt(button.getAttribute('data-page'));
                this.goToPage(page);
            }
        });

        // Items per page change
        const itemsPerPageSelect = this.container.querySelector('[data-items-per-page]');
        if (itemsPerPageSelect) {
            itemsPerPageSelect.addEventListener('change', (e) => {
                const newItemsPerPage = parseInt(e.target.value);
                this.setItemsPerPage(newItemsPerPage);
            });
        }

        // Keyboard navigation
        this.container.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft') {
                this.previousPage();
            } else if (e.key === 'ArrowRight') {
                this.nextPage();
            }
        });
    }

    /**
     * Go to specific page
     */
    goToPage(page) {
        if (page < 1 || page > this.state.totalPages || page === this.state.currentPage) {
            return;
        }

        this.state.currentPage = page;
        this.render();
        this.attachEventListeners();

        if (this.options.onChange) {
            this.options.onChange(page);
        }

        this.emit('pageChange', { page });
    }

    /**
     * Go to next page
     */
    nextPage() {
        this.goToPage(this.state.currentPage + 1);
    }

    /**
     * Go to previous page
     */
    previousPage() {
        this.goToPage(this.state.currentPage - 1);
    }

    /**
     * Set items per page
     */
    setItemsPerPage(itemsPerPage) {
        if (itemsPerPage === this.state.itemsPerPage) {
            return;
        }

        this.state.itemsPerPage = itemsPerPage;
        this.state.currentPage = 1; // Reset to first page
        this.render();
        this.attachEventListeners();

        if (this.options.onItemsPerPageChange) {
            this.options.onItemsPerPageChange(itemsPerPage);
        }

        this.emit('itemsPerPageChange', { itemsPerPage });
    }

    /**
     * Set total items
     */
    setTotalItems(totalItems) {
        this.options.totalItems = totalItems;
        this.render();
        this.attachEventListeners();
    }

    /**
     * Get current page
     */
    getCurrentPage() {
        return this.state.currentPage;
    }

    /**
     * Get items per page
     */
    getItemsPerPage() {
        return this.state.itemsPerPage;
    }

    /**
     * Get total pages
     */
    getTotalPages() {
        return this.state.totalPages;
    }

    /**
     * Destroy component
     */
    destroy() {
        this.container.innerHTML = '';
        super.destroy();
    }
}
