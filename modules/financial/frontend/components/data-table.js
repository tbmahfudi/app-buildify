/**
 * DataTable Component
 *
 * Reusable data table with pagination, search, filtering, and sorting
 */

export class DataTable {
    constructor(config) {
        this.containerId = config.containerId;
        this.columns = config.columns || [];
        this.dataSource = config.dataSource; // Function that returns Promise<{data, total}>
        this.actions = config.actions || [];
        this.pageSize = config.pageSize || 10;
        this.searchable = config.searchable !== false;
        this.sortable = config.sortable !== false;
        this.selectable = config.selectable || false;
        this.onRowClick = config.onRowClick || null;

        // State
        this.currentPage = 1;
        this.totalPages = 1;
        this.totalRecords = 0;
        this.searchQuery = '';
        this.sortColumn = null;
        this.sortDirection = 'asc';
        this.filters = {};
        this.selectedRows = new Set();

        // Cache
        this.data = [];
        this.loading = false;
    }

    /**
     * Initialize the table
     */
    async init() {
        this.render();
        await this.loadData();
    }

    /**
     * Render the table structure
     */
    render() {
        const container = document.getElementById(this.containerId);
        if (!container) {
            console.error(`Container ${this.containerId} not found`);
            return;
        }

        container.innerHTML = `
            <div class="data-table">
                ${this.searchable ? this.renderSearchBar() : ''}
                <div class="data-table-wrapper">
                    <table class="w-full">
                        <thead>
                            ${this.renderHeader()}
                        </thead>
                        <tbody id="${this.containerId}-tbody">
                            ${this.renderLoadingRow()}
                        </tbody>
                    </table>
                </div>
                <div id="${this.containerId}-pagination" class="data-table-pagination">
                    <!-- Pagination will be rendered here -->
                </div>
            </div>
        `;

        this.attachEventListeners();
    }

    /**
     * Render search bar
     */
    renderSearchBar() {
        return `
            <div class="data-table-search mb-4 flex gap-4">
                <div class="flex-1">
                    <div class="relative">
                        <i class="ph ph-magnifying-glass absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"></i>
                        <input
                            type="text"
                            id="${this.containerId}-search"
                            placeholder="Search..."
                            class="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                    </div>
                </div>
                <button
                    id="${this.containerId}-refresh"
                    class="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition flex items-center gap-2"
                >
                    <i class="ph ph-arrow-clockwise"></i>
                    Refresh
                </button>
            </div>
        `;
    }

    /**
     * Render table header
     */
    renderHeader() {
        let headerHtml = '<tr class="bg-gray-50 border-b border-gray-200">';

        if (this.selectable) {
            headerHtml += `
                <th class="px-4 py-3 text-left">
                    <input type="checkbox" id="${this.containerId}-select-all" class="rounded border-gray-300">
                </th>
            `;
        }

        this.columns.forEach(column => {
            const sortable = this.sortable && column.sortable !== false;
            headerHtml += `
                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider ${sortable ? 'cursor-pointer hover:bg-gray-100' : ''}"
                    ${sortable ? `data-column="${column.field}"` : ''}>
                    <div class="flex items-center gap-2">
                        ${column.label}
                        ${sortable ? `
                            <i class="ph ph-arrows-down-up text-gray-400 sort-icon" data-column="${column.field}"></i>
                        ` : ''}
                    </div>
                </th>
            `;
        });

        if (this.actions.length > 0) {
            headerHtml += '<th class="px-4 py-3 text-right text-xs font-semibold text-gray-700 uppercase tracking-wider">Actions</th>';
        }

        headerHtml += '</tr>';
        return headerHtml;
    }

    /**
     * Render loading row
     */
    renderLoadingRow() {
        const colspan = this.columns.length + (this.selectable ? 1 : 0) + (this.actions.length > 0 ? 1 : 0);
        return `
            <tr>
                <td colspan="${colspan}" class="px-4 py-8 text-center">
                    <div class="flex items-center justify-center gap-3">
                        <div class="w-6 h-6 border-3 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                        <span class="text-gray-600">Loading...</span>
                    </div>
                </td>
            </tr>
        `;
    }

    /**
     * Render empty state
     */
    renderEmptyState() {
        const colspan = this.columns.length + (this.selectable ? 1 : 0) + (this.actions.length > 0 ? 1 : 0);
        return `
            <tr>
                <td colspan="${colspan}" class="px-4 py-12 text-center">
                    <i class="ph-duotone ph-database text-6xl text-gray-300 mb-4"></i>
                    <p class="text-gray-500 text-lg">No data available</p>
                    ${this.searchQuery ? '<p class="text-gray-400 text-sm mt-2">Try adjusting your search</p>' : ''}
                </td>
            </tr>
        `;
    }

    /**
     * Render table rows
     */
    renderRows() {
        if (this.data.length === 0) {
            return this.renderEmptyState();
        }

        return this.data.map(row => {
            const rowId = row.id || Math.random().toString(36).substr(2, 9);
            let rowHtml = `<tr class="border-b border-gray-200 hover:bg-gray-50 transition ${this.onRowClick ? 'cursor-pointer' : ''}" data-row-id="${rowId}">`;

            if (this.selectable) {
                rowHtml += `
                    <td class="px-4 py-3">
                        <input type="checkbox" class="row-select rounded border-gray-300" data-row-id="${rowId}">
                    </td>
                `;
            }

            this.columns.forEach(column => {
                const value = this.getCellValue(row, column);
                const formatted = column.formatter ? column.formatter(value, row) : value;
                rowHtml += `<td class="px-4 py-3 ${column.className || ''}">${formatted}</td>`;
            });

            if (this.actions.length > 0) {
                rowHtml += `<td class="px-4 py-3 text-right">${this.renderActions(row)}</td>`;
            }

            rowHtml += '</tr>';
            return rowHtml;
        }).join('');
    }

    /**
     * Get cell value from row
     */
    getCellValue(row, column) {
        if (column.field.includes('.')) {
            const parts = column.field.split('.');
            let value = row;
            for (const part of parts) {
                value = value?.[part];
            }
            return value ?? '';
        }
        return row[column.field] ?? '';
    }

    /**
     * Render action buttons
     */
    renderActions(row) {
        return this.actions.map(action => {
            if (action.condition && !action.condition(row)) {
                return '';
            }

            const icon = action.icon || 'ph-dots-three';
            const className = action.className || 'text-gray-600 hover:text-blue-600';
            const title = action.title || action.label;

            return `
                <button
                    class="action-btn px-2 py-1 ${className} transition"
                    data-action="${action.name}"
                    data-row-id="${row.id}"
                    title="${title}"
                >
                    <i class="ph ${icon}"></i>
                    ${action.label ? `<span class="ml-1">${action.label}</span>` : ''}
                </button>
            `;
        }).join('');
    }

    /**
     * Render pagination
     */
    renderPagination() {
        if (this.totalRecords === 0) {
            return '';
        }

        const startRecord = (this.currentPage - 1) * this.pageSize + 1;
        const endRecord = Math.min(this.currentPage * this.pageSize, this.totalRecords);

        let paginationHtml = `
            <div class="flex items-center justify-between mt-4">
                <div class="text-sm text-gray-600">
                    Showing ${startRecord} to ${endRecord} of ${this.totalRecords} records
                </div>
                <div class="flex gap-2">
                    <button
                        class="px-3 py-1 border border-gray-300 rounded-lg hover:bg-gray-50 transition ${this.currentPage === 1 ? 'opacity-50 cursor-not-allowed' : ''}"
                        data-page="prev"
                        ${this.currentPage === 1 ? 'disabled' : ''}
                    >
                        <i class="ph ph-caret-left"></i>
                    </button>
        `;

        // Page numbers
        const maxPages = 5;
        let startPage = Math.max(1, this.currentPage - Math.floor(maxPages / 2));
        let endPage = Math.min(this.totalPages, startPage + maxPages - 1);

        if (endPage - startPage < maxPages - 1) {
            startPage = Math.max(1, endPage - maxPages + 1);
        }

        for (let i = startPage; i <= endPage; i++) {
            paginationHtml += `
                <button
                    class="px-3 py-1 border border-gray-300 rounded-lg transition ${i === this.currentPage ? 'bg-blue-600 text-white border-blue-600' : 'hover:bg-gray-50'}"
                    data-page="${i}"
                >
                    ${i}
                </button>
            `;
        }

        paginationHtml += `
                    <button
                        class="px-3 py-1 border border-gray-300 rounded-lg hover:bg-gray-50 transition ${this.currentPage === this.totalPages ? 'opacity-50 cursor-not-allowed' : ''}"
                        data-page="next"
                        ${this.currentPage === this.totalPages ? 'disabled' : ''}
                    >
                        <i class="ph ph-caret-right"></i>
                    </button>
                </div>
            </div>
        `;

        return paginationHtml;
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        const container = document.getElementById(this.containerId);

        // Search
        if (this.searchable) {
            const searchInput = document.getElementById(`${this.containerId}-search`);
            if (searchInput) {
                let searchTimeout;
                searchInput.addEventListener('input', (e) => {
                    clearTimeout(searchTimeout);
                    searchTimeout = setTimeout(() => {
                        this.searchQuery = e.target.value;
                        this.currentPage = 1;
                        this.loadData();
                    }, 300);
                });
            }

            const refreshBtn = document.getElementById(`${this.containerId}-refresh`);
            if (refreshBtn) {
                refreshBtn.addEventListener('click', () => this.refresh());
            }
        }

        // Sort
        if (this.sortable) {
            container.querySelectorAll('th[data-column]').forEach(th => {
                th.addEventListener('click', () => {
                    const column = th.dataset.column;
                    if (this.sortColumn === column) {
                        this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
                    } else {
                        this.sortColumn = column;
                        this.sortDirection = 'asc';
                    }
                    this.loadData();
                });
            });
        }

        // Select all
        if (this.selectable) {
            const selectAllCheckbox = document.getElementById(`${this.containerId}-select-all`);
            if (selectAllCheckbox) {
                selectAllCheckbox.addEventListener('change', (e) => {
                    const checked = e.target.checked;
                    container.querySelectorAll('.row-select').forEach(checkbox => {
                        checkbox.checked = checked;
                        const rowId = checkbox.dataset.rowId;
                        if (checked) {
                            this.selectedRows.add(rowId);
                        } else {
                            this.selectedRows.delete(rowId);
                        }
                    });
                });
            }
        }
    }

    /**
     * Load data from source
     */
    async loadData() {
        if (this.loading) return;

        this.loading = true;
        const tbody = document.getElementById(`${this.containerId}-tbody`);
        if (tbody) {
            tbody.innerHTML = this.renderLoadingRow();
        }

        try {
            const params = {
                page: this.currentPage,
                page_size: this.pageSize,
                search: this.searchQuery,
                sort_by: this.sortColumn,
                sort_dir: this.sortDirection,
                ...this.filters
            };

            const result = await this.dataSource(params);
            this.data = result.data || [];
            this.totalRecords = result.total || 0;
            this.totalPages = Math.ceil(this.totalRecords / this.pageSize) || 1;

            if (tbody) {
                tbody.innerHTML = this.renderRows();
                this.attachRowEventListeners();
            }

            const paginationContainer = document.getElementById(`${this.containerId}-pagination`);
            if (paginationContainer) {
                paginationContainer.innerHTML = this.renderPagination();
                this.attachPaginationListeners();
            }

        } catch (error) {
            console.error('Error loading data:', error);
            if (tbody) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="${this.columns.length + (this.selectable ? 1 : 0) + (this.actions.length > 0 ? 1 : 0)}" class="px-4 py-8 text-center">
                            <i class="ph-duotone ph-warning-circle text-6xl text-red-400 mb-4"></i>
                            <p class="text-red-600 text-lg">Error loading data</p>
                            <p class="text-gray-500 text-sm mt-2">${error.message}</p>
                        </td>
                    </tr>
                `;
            }
        } finally {
            this.loading = false;
        }
    }

    /**
     * Attach row event listeners
     */
    attachRowEventListeners() {
        const container = document.getElementById(this.containerId);

        // Row click
        if (this.onRowClick) {
            container.querySelectorAll('tbody tr[data-row-id]').forEach(tr => {
                tr.addEventListener('click', (e) => {
                    if (e.target.closest('.action-btn') || e.target.closest('.row-select')) {
                        return;
                    }
                    const rowId = tr.dataset.rowId;
                    const row = this.data.find(r => r.id == rowId);
                    if (row) {
                        this.onRowClick(row);
                    }
                });
            });
        }

        // Row selection
        if (this.selectable) {
            container.querySelectorAll('.row-select').forEach(checkbox => {
                checkbox.addEventListener('change', (e) => {
                    const rowId = e.target.dataset.rowId;
                    if (e.target.checked) {
                        this.selectedRows.add(rowId);
                    } else {
                        this.selectedRows.delete(rowId);
                    }
                });
            });
        }

        // Action buttons
        container.querySelectorAll('.action-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const actionName = btn.dataset.action;
                const rowId = btn.dataset.rowId;
                const row = this.data.find(r => r.id == rowId);
                const action = this.actions.find(a => a.name === actionName);

                if (action && action.handler && row) {
                    action.handler(row);
                }
            });
        });
    }

    /**
     * Attach pagination listeners
     */
    attachPaginationListeners() {
        const paginationContainer = document.getElementById(`${this.containerId}-pagination`);
        if (!paginationContainer) return;

        paginationContainer.querySelectorAll('button[data-page]').forEach(btn => {
            btn.addEventListener('click', () => {
                const page = btn.dataset.page;

                if (page === 'prev' && this.currentPage > 1) {
                    this.currentPage--;
                } else if (page === 'next' && this.currentPage < this.totalPages) {
                    this.currentPage++;
                } else if (page !== 'prev' && page !== 'next') {
                    this.currentPage = parseInt(page);
                }

                this.loadData();
            });
        });
    }

    /**
     * Refresh the table
     */
    async refresh() {
        this.currentPage = 1;
        this.selectedRows.clear();
        await this.loadData();
    }

    /**
     * Get selected rows
     */
    getSelectedRows() {
        return this.data.filter(row => this.selectedRows.has(row.id.toString()));
    }

    /**
     * Set filters
     */
    setFilters(filters) {
        this.filters = filters;
        this.currentPage = 1;
        this.loadData();
    }
}
