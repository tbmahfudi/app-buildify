/**
 * FlexTable - Flexible Data Table Component
 *
 * A powerful data table component with Tailwind styling supporting:
 * - Sorting (single/multi-column)
 * - Filtering per column
 * - Global search
 * - Row selection (single/multiple)
 * - Pagination
 * - Row actions with RBAC
 * - Bulk actions
 * - Custom cell rendering
 * - Responsive design
 * - Sticky header
 * - Loading state
 * - Empty state
 *
 * @author Claude Code
 * @version 1.0.0
 */

import BaseComponent from '../core/base-component.js';
import { hasPermission } from '../rbac.js';
import FlexPagination from './flex-pagination.js';

export default class FlexTable extends BaseComponent {
    /**
     * Default configuration
     */
    static DEFAULTS = {
        columns: [],                // Array of column definitions
        data: [],                   // Array of data objects
        keyField: 'id',             // Unique key field

        // Selection
        selectable: false,          // Enable row selection
        selectMode: 'multiple',     // single | multiple
        selectedRows: [],           // Pre-selected row keys

        // Sorting
        sortable: false,            // Enable global sorting
        defaultSort: null,          // { column: 'name', direction: 'asc' }

        // Filtering
        filterable: false,          // Enable column filtering
        filters: {},                // Active filters

        // Search
        searchable: false,          // Enable global search
        searchQuery: '',            // Current search query
        searchFields: [],           // Fields to search (empty = all)

        // Pagination
        pagination: false,          // Enable pagination
        itemsPerPage: 10,
        currentPage: 1,

        // Actions
        actions: [],                // Row actions
        bulkActions: [],            // Bulk actions for selected rows

        // Appearance
        striped: true,              // Striped rows
        hover: true,                // Hover effect
        bordered: false,            // Table borders
        compact: false,             // Compact mode
        stickyHeader: false,        // Sticky header on scroll
        responsive: true,           // Mobile responsive

        // States
        loading: false,             // Loading state
        emptyMessage: 'No data available',
        loadingMessage: 'Loading...',

        // Styling
        headerClass: '',
        rowClass: '',
        cellClass: '',
        classes: [],

        // Callbacks
        onSort: null,
        onFilter: null,
        onSearch: null,
        onSelect: null,
        onRowClick: null,
        onPageChange: null
    };

    /**
     * Constructor
     */
    constructor(container, options = {}) {
        super(container, options);

        this.state = {
            data: this.options.data,
            filteredData: [],
            sortedData: [],
            displayData: [],
            selectedKeys: new Set(this.options.selectedRows),
            sort: this.options.defaultSort,
            filters: this.options.filters,
            searchQuery: this.options.searchQuery,
            currentPage: this.options.currentPage
        };

        this.pagination = null;
        this.init();
    }

    /**
     * Initialize component
     */
    async init() {
        await this.processData();
        this.render();
        this.attachEventListeners();
        this.emit('init');
    }

    /**
     * Process data (filter, search, sort)
     */
    async processData() {
        let data = [...this.state.data];

        // Apply filters
        if (this.options.filterable && Object.keys(this.state.filters).length > 0) {
            data = this.applyFilters(data);
        }

        // Apply search
        if (this.options.searchable && this.state.searchQuery) {
            data = this.applySearch(data);
        }

        this.state.filteredData = data;

        // Apply sorting
        if (this.state.sort) {
            data = this.applySort(data);
        }

        this.state.sortedData = data;

        // Apply pagination
        if (this.options.pagination) {
            const start = (this.state.currentPage - 1) * this.options.itemsPerPage;
            const end = start + this.options.itemsPerPage;
            this.state.displayData = data.slice(start, end);
        } else {
            this.state.displayData = data;
        }
    }

    /**
     * Apply filters
     */
    applyFilters(data) {
        return data.filter(row => {
            return Object.entries(this.state.filters).every(([column, filterValue]) => {
                const cellValue = this.getCellValue(row, column);
                return String(cellValue).toLowerCase().includes(String(filterValue).toLowerCase());
            });
        });
    }

    /**
     * Apply search
     */
    applySearch(data) {
        const query = this.state.searchQuery.toLowerCase();
        const fields = this.options.searchFields.length > 0
            ? this.options.searchFields
            : this.options.columns.map(col => col.key);

        return data.filter(row => {
            return fields.some(field => {
                const value = this.getCellValue(row, field);
                return String(value).toLowerCase().includes(query);
            });
        });
    }

    /**
     * Apply sorting
     */
    applySort(data) {
        const { column, direction } = this.state.sort;

        return [...data].sort((a, b) => {
            const aVal = this.getCellValue(a, column);
            const bVal = this.getCellValue(b, column);

            let comparison = 0;
            if (aVal > bVal) comparison = 1;
            if (aVal < bVal) comparison = -1;

            return direction === 'asc' ? comparison : -comparison;
        });
    }

    /**
     * Get cell value from row
     */
    getCellValue(row, key) {
        return key.split('.').reduce((obj, k) => obj?.[k], row) ?? '';
    }

    /**
     * Render the table
     */
    render() {
        this.container.innerHTML = '';

        const wrapper = document.createElement('div');
        wrapper.className = `flex-table ${this.options.classes.join(' ')}`;

        // Toolbar (search, filters, bulk actions)
        if (this.options.searchable || this.options.bulkActions.length > 0) {
            wrapper.appendChild(this.renderToolbar());
        }

        // Table container
        const tableContainer = document.createElement('div');
        tableContainer.className = this.options.responsive
            ? 'overflow-x-auto'
            : '';

        if (this.options.loading) {
            tableContainer.appendChild(this.renderLoading());
        } else if (this.state.displayData.length === 0) {
            tableContainer.appendChild(this.renderEmpty());
        } else {
            tableContainer.appendChild(this.renderTable());
        }

        wrapper.appendChild(tableContainer);

        // Pagination
        if (this.options.pagination && !this.options.loading) {
            wrapper.appendChild(this.renderPagination());
        }

        this.container.appendChild(wrapper);
    }

    /**
     * Render toolbar
     */
    renderToolbar() {
        const toolbar = document.createElement('div');
        toolbar.className = 'flex flex-wrap items-center justify-between gap-4 mb-4 p-4 bg-white border border-gray-200 rounded-lg';

        // Left side: Search and bulk actions
        const left = document.createElement('div');
        left.className = 'flex items-center gap-3';

        // Bulk actions
        if (this.options.bulkActions.length > 0 && this.state.selectedKeys.size > 0) {
            left.appendChild(this.renderBulkActions());
        }

        // Search
        if (this.options.searchable) {
            left.appendChild(this.renderSearch());
        }

        toolbar.appendChild(left);

        return toolbar;
    }

    /**
     * Render search input
     */
    renderSearch() {
        const searchWrapper = document.createElement('div');
        searchWrapper.className = 'relative';

        const searchInput = document.createElement('input');
        searchInput.type = 'text';
        searchInput.placeholder = 'Search...';
        searchInput.value = this.state.searchQuery;
        searchInput.className = 'pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none w-64';
        searchInput.setAttribute('data-search', 'true');

        const icon = document.createElement('i');
        icon.className = 'ph ph-magnifying-glass absolute left-3 top-1/2 -translate-y-1/2 text-gray-400';

        searchWrapper.appendChild(icon);
        searchWrapper.appendChild(searchInput);

        return searchWrapper;
    }

    /**
     * Render bulk actions
     */
    renderBulkActions() {
        const wrapper = document.createElement('div');
        wrapper.className = 'flex items-center gap-2';

        const badge = document.createElement('span');
        badge.className = 'px-2 py-1 bg-blue-100 text-blue-800 text-sm rounded-md';
        badge.textContent = `${this.state.selectedKeys.size} selected`;

        wrapper.appendChild(badge);

        this.options.bulkActions.forEach((action, index) => {
            const button = document.createElement('button');
            button.className = `px-3 py-2 text-sm font-medium rounded-lg transition ${
                action.variant === 'danger'
                    ? 'bg-red-600 hover:bg-red-700 text-white'
                    : 'bg-gray-600 hover:bg-gray-700 text-white'
            }`;
            button.textContent = action.label;
            button.setAttribute('data-bulk-action', index);
            wrapper.appendChild(button);
        });

        return wrapper;
    }

    /**
     * Render table
     */
    renderTable() {
        const table = document.createElement('table');

        const classes = [
            'w-full text-left',
            this.options.bordered ? 'border border-gray-200' : '',
            this.options.stickyHeader ? 'relative' : ''
        ];

        table.className = classes.filter(Boolean).join(' ');

        // Header
        table.appendChild(this.renderHeader());

        // Body
        table.appendChild(this.renderBody());

        return table;
    }

    /**
     * Render table header
     */
    renderHeader() {
        const thead = document.createElement('thead');
        thead.className = `bg-gray-50 ${this.options.stickyHeader ? 'sticky top-0 z-10' : ''} ${this.options.headerClass}`;

        const tr = document.createElement('tr');

        // Selection column
        if (this.options.selectable) {
            const th = document.createElement('th');
            th.className = 'px-4 py-3 border-b border-gray-200';

            if (this.options.selectMode === 'multiple') {
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.className = 'rounded border-gray-300 focus:ring-blue-500';
                checkbox.checked = this.state.selectedKeys.size === this.state.displayData.length && this.state.displayData.length > 0;
                checkbox.setAttribute('data-select-all', 'true');
                th.appendChild(checkbox);
            }

            tr.appendChild(th);
        }

        // Column headers
        this.options.columns.forEach(column => {
            const th = document.createElement('th');
            th.className = `px-4 py-3 border-b border-gray-200 text-sm font-semibold text-gray-700 ${
                column.sortable && this.options.sortable ? 'cursor-pointer hover:bg-gray-100' : ''
            }`;

            if (column.width) {
                th.style.width = column.width;
            }

            const content = document.createElement('div');
            content.className = 'flex items-center gap-2';

            const label = document.createElement('span');
            label.textContent = column.label;
            content.appendChild(label);

            // Sort indicator
            if (column.sortable && this.options.sortable) {
                const sortIcon = document.createElement('i');
                if (this.state.sort?.column === column.key) {
                    sortIcon.className = this.state.sort.direction === 'asc'
                        ? 'ph ph-caret-up'
                        : 'ph ph-caret-down';
                } else {
                    sortIcon.className = 'ph ph-caret-up-down text-gray-400';
                }
                content.appendChild(sortIcon);
                th.setAttribute('data-sort-column', column.key);
            }

            th.appendChild(content);
            tr.appendChild(th);
        });

        // Actions column
        if (this.options.actions.length > 0) {
            const th = document.createElement('th');
            th.className = 'px-4 py-3 border-b border-gray-200 text-sm font-semibold text-gray-700';
            th.textContent = 'Actions';
            tr.appendChild(th);
        }

        thead.appendChild(tr);
        return thead;
    }

    /**
     * Render table body
     */
    renderBody() {
        const tbody = document.createElement('tbody');

        this.state.displayData.forEach((row, index) => {
            const tr = this.renderRow(row, index);
            tbody.appendChild(tr);
        });

        return tbody;
    }

    /**
     * Render a row
     */
    renderRow(row, index) {
        const tr = document.createElement('tr');
        const rowKey = row[this.options.keyField];
        const isSelected = this.state.selectedKeys.has(rowKey);

        const classes = [
            this.options.striped && index % 2 === 0 ? 'bg-white' : 'bg-gray-50',
            this.options.hover ? 'hover:bg-gray-100' : '',
            isSelected ? 'bg-blue-50' : '',
            'border-b border-gray-200',
            this.options.rowClass
        ];

        tr.className = classes.filter(Boolean).join(' ');
        tr.setAttribute('data-row-key', rowKey);

        // Selection cell
        if (this.options.selectable) {
            const td = document.createElement('td');
            td.className = `px-4 py-3 ${this.options.cellClass}`;

            const checkbox = document.createElement('input');
            checkbox.type = this.options.selectMode === 'single' ? 'radio' : 'checkbox';
            checkbox.name = this.options.selectMode === 'single' ? 'row-selection' : '';
            checkbox.className = 'rounded border-gray-300 focus:ring-blue-500';
            checkbox.checked = isSelected;
            checkbox.setAttribute('data-row-select', rowKey);

            td.appendChild(checkbox);
            tr.appendChild(td);
        }

        // Data cells
        this.options.columns.forEach(column => {
            const td = document.createElement('td');
            td.className = `px-4 py-3 text-sm text-gray-900 ${this.options.cellClass}`;

            const value = this.getCellValue(row, column.key);

            if (column.render) {
                td.innerHTML = column.render(value, row);
            } else {
                td.textContent = value;
            }

            tr.appendChild(td);
        });

        // Actions cell
        if (this.options.actions.length > 0) {
            const td = document.createElement('td');
            td.className = `px-4 py-3 text-sm ${this.options.cellClass}`;
            td.appendChild(this.renderRowActions(row));
            tr.appendChild(td);
        }

        return tr;
    }

    /**
     * Render row actions
     */
    renderRowActions(row) {
        const wrapper = document.createElement('div');
        wrapper.className = 'flex items-center gap-2';

        this.options.actions.forEach((action, index) => {
            const button = document.createElement('button');
            button.className = `px-2 py-1 text-sm rounded hover:bg-gray-200 transition ${
                action.variant === 'danger' ? 'text-red-600 hover:bg-red-50' : 'text-gray-700'
            }`;
            button.innerHTML = action.icon || action.label;
            button.title = action.label;
            button.setAttribute('data-row-action', index);
            button.setAttribute('data-row-key', row[this.options.keyField]);

            wrapper.appendChild(button);
        });

        return wrapper;
    }

    /**
     * Render loading state
     */
    renderLoading() {
        const div = document.createElement('div');
        div.className = 'flex items-center justify-center py-12 bg-white border border-gray-200 rounded-lg';

        const spinner = document.createElement('div');
        spinner.className = 'w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin';

        const text = document.createElement('p');
        text.className = 'ml-4 text-gray-600';
        text.textContent = this.options.loadingMessage;

        div.appendChild(spinner);
        div.appendChild(text);

        return div;
    }

    /**
     * Render empty state
     */
    renderEmpty() {
        const div = document.createElement('div');
        div.className = 'flex flex-col items-center justify-center py-12 bg-white border border-gray-200 rounded-lg';

        const icon = document.createElement('i');
        icon.className = 'ph-duotone ph-database text-6xl text-gray-400 mb-4';

        const text = document.createElement('p');
        text.className = 'text-gray-600 text-lg';
        text.textContent = this.options.emptyMessage;

        div.appendChild(icon);
        div.appendChild(text);

        return div;
    }

    /**
     * Render pagination
     */
    renderPagination() {
        const wrapper = document.createElement('div');
        wrapper.className = 'mt-4';

        const paginationContainer = document.createElement('div');

        this.pagination = new FlexPagination(paginationContainer, {
            totalItems: this.state.filteredData.length,
            itemsPerPage: this.options.itemsPerPage,
            currentPage: this.state.currentPage,
            onChange: (page) => {
                this.state.currentPage = page;
                this.processData().then(() => {
                    this.render();
                    this.attachEventListeners();

                    if (this.options.onPageChange) {
                        this.options.onPageChange(page);
                    }
                });
            }
        });

        wrapper.appendChild(paginationContainer);
        return wrapper;
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Search
        const searchInput = this.container.querySelector('[data-search]');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.search(e.target.value);
            });
        }

        // Select all
        const selectAllCheckbox = this.container.querySelector('[data-select-all]');
        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', (e) => {
                this.selectAll(e.target.checked);
            });
        }

        // Row selection
        this.container.addEventListener('change', (e) => {
            const rowSelect = e.target.closest('[data-row-select]');
            if (rowSelect) {
                const rowKey = rowSelect.getAttribute('data-row-select');
                this.toggleRowSelection(rowKey, rowSelect.checked);
            }
        });

        // Sorting
        this.container.addEventListener('click', (e) => {
            const sortHeader = e.target.closest('[data-sort-column]');
            if (sortHeader) {
                const column = sortHeader.getAttribute('data-sort-column');
                this.sort(column);
            }
        });

        // Row actions
        this.container.addEventListener('click', (e) => {
            const actionButton = e.target.closest('[data-row-action]');
            if (actionButton) {
                const actionIndex = parseInt(actionButton.getAttribute('data-row-action'));
                const rowKey = actionButton.getAttribute('data-row-key');
                const row = this.state.data.find(r => r[this.options.keyField] === rowKey);
                const action = this.options.actions[actionIndex];

                if (action.onClick) {
                    action.onClick(row);
                }

                this.emit('rowAction', { action, row });
            }
        });

        // Bulk actions
        this.container.addEventListener('click', (e) => {
            const bulkActionButton = e.target.closest('[data-bulk-action]');
            if (bulkActionButton) {
                const actionIndex = parseInt(bulkActionButton.getAttribute('data-bulk-action'));
                const action = this.options.bulkActions[actionIndex];
                const selectedRows = this.getSelectedRows();

                if (action.onClick) {
                    action.onClick(selectedRows);
                }

                this.emit('bulkAction', { action, rows: selectedRows });
            }
        });

        // Row click
        if (this.options.onRowClick) {
            this.container.addEventListener('click', (e) => {
                const row = e.target.closest('[data-row-key]');
                if (row && !e.target.closest('input') && !e.target.closest('button')) {
                    const rowKey = row.getAttribute('data-row-key');
                    const rowData = this.state.data.find(r => r[this.options.keyField] === rowKey);
                    this.options.onRowClick(rowData);
                }
            });
        }
    }

    /**
     * Search
     */
    search(query) {
        this.state.searchQuery = query;
        this.state.currentPage = 1;

        this.processData().then(() => {
            this.render();
            this.attachEventListeners();

            if (this.options.onSearch) {
                this.options.onSearch(query);
            }

            this.emit('search', { query });
        });
    }

    /**
     * Sort by column
     */
    sort(column) {
        const currentSort = this.state.sort;
        let direction = 'asc';

        if (currentSort?.column === column) {
            direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
        }

        this.state.sort = { column, direction };

        this.processData().then(() => {
            this.render();
            this.attachEventListeners();

            if (this.options.onSort) {
                this.options.onSort(column, direction);
            }

            this.emit('sort', { column, direction });
        });
    }

    /**
     * Toggle row selection
     */
    toggleRowSelection(rowKey, selected) {
        if (this.options.selectMode === 'single') {
            this.state.selectedKeys.clear();
            if (selected) {
                this.state.selectedKeys.add(rowKey);
            }
        } else {
            if (selected) {
                this.state.selectedKeys.add(rowKey);
            } else {
                this.state.selectedKeys.delete(rowKey);
            }
        }

        this.render();
        this.attachEventListeners();

        if (this.options.onSelect) {
            this.options.onSelect(this.getSelectedRows());
        }

        this.emit('select', { selectedRows: this.getSelectedRows() });
    }

    /**
     * Select all rows
     */
    selectAll(selected) {
        if (selected) {
            this.state.displayData.forEach(row => {
                this.state.selectedKeys.add(row[this.options.keyField]);
            });
        } else {
            this.state.selectedKeys.clear();
        }

        this.render();
        this.attachEventListeners();

        if (this.options.onSelect) {
            this.options.onSelect(this.getSelectedRows());
        }

        this.emit('selectAll', { selected, selectedRows: this.getSelectedRows() });
    }

    /**
     * Get selected rows
     */
    getSelectedRows() {
        return this.state.data.filter(row =>
            this.state.selectedKeys.has(row[this.options.keyField])
        );
    }

    /**
     * Set data
     */
    setData(data) {
        this.state.data = data;
        this.state.currentPage = 1;
        this.processData().then(() => {
            this.render();
            this.attachEventListeners();
        });
    }

    /**
     * Set loading state
     */
    setLoading(loading) {
        this.options.loading = loading;
        this.render();
        this.attachEventListeners();
    }

    /**
     * Refresh table
     */
    async refresh() {
        await this.processData();
        this.render();
        this.attachEventListeners();
    }

    /**
     * Destroy component
     */
    destroy() {
        if (this.pagination) {
            this.pagination.destroy();
        }
        this.container.innerHTML = '';
        super.destroy();
    }
}
