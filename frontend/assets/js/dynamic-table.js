import { dataService } from './data-service.js';

/**
 * Dynamic Table - Renders data tables from metadata
 * Styled to match the Users management table pattern
 */
export class DynamicTable {
  constructor(container, entity, metadata) {
    this.container = container;
    this.entity = entity;
    this.metadata = metadata;
    this.currentPage = 1;
    this.pageSize = metadata.table.page_size || metadata.table.default_page_size || 25;
    this.filters = [];
    this.columnFilters = {};
    this.searchQuery = '';
    this.sort = (metadata.table.default_sort || []).map(s =>
      Array.isArray(s) ? s : [s.field || s.name, s.order || s.dir || 'asc']
    );
    this.onRowAction = null;
    this._searchTimer = null;
    this._tableCardId = `dtable-card-${entity}-${Math.random().toString(36).slice(2, 7)}`;
  }

  /**
   * Render the full table UI (search bar + table card)
   */
  async render() {
    this.container.innerHTML = '';

    const wrapper = document.createElement('div');
    wrapper.className = 'space-y-4';

    // Search + filter bar
    wrapper.appendChild(this._buildFilterBar());

    // Table card (initially loading)
    const tableCard = document.createElement('div');
    tableCard.id = this._tableCardId;
    tableCard.className = 'bg-white rounded-lg shadow-sm overflow-hidden';
    tableCard.appendChild(this._buildLoadingState());
    wrapper.appendChild(tableCard);

    this.container.appendChild(wrapper);

    await this._fetchAndRender();
  }

  /**
   * Refresh table data without re-rendering the filter bar
   */
  async refresh() {
    return this._fetchAndRender();
  }

  // ─── Private helpers ──────────────────────────────────────────────────────

  /**
   * Build search + filter bar
   */
  _buildFilterBar() {
    const bar = document.createElement('div');
    bar.className = 'bg-white rounded-lg shadow-sm p-4';

    const filterCols = this._getFilterableChoiceCols();
    const gridCols = Math.min(1 + filterCols.length + 1, 4);

    const grid = document.createElement('div');
    grid.className = `grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-${gridCols} gap-3`;

    // Search input
    const searchWrap = document.createElement('div');
    searchWrap.className = 'relative';

    const searchIcon = document.createElement('i');
    searchIcon.className = 'ph ph-magnifying-glass absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 text-sm pointer-events-none';

    const searchInput = document.createElement('input');
    searchInput.type = 'text';
    searchInput.placeholder = `Search ${this.metadata.display_name || this.entity}...`;
    searchInput.className = 'w-full pl-11 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm';
    searchInput.value = this.searchQuery;
    searchInput.addEventListener('input', (e) => {
      clearTimeout(this._searchTimer);
      this._searchTimer = setTimeout(() => {
        this.searchQuery = e.target.value;
        this.currentPage = 1;
        this._fetchAndRender();
      }, 350);
    });

    searchWrap.appendChild(searchIcon);
    searchWrap.appendChild(searchInput);
    grid.appendChild(searchWrap);

    // Choice / boolean filter dropdowns
    filterCols.forEach(col => {
      const select = document.createElement('select');
      select.className = 'px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm text-gray-700';

      const allOpt = document.createElement('option');
      allOpt.value = '';
      allOpt.textContent = `All ${col.title}`;
      select.appendChild(allOpt);

      if (col.type === 'boolean') {
        [['true', 'Yes'], ['false', 'No']].forEach(([val, label]) => {
          const opt = document.createElement('option');
          opt.value = val;
          opt.textContent = label;
          if (this.columnFilters[col.field] === val) opt.selected = true;
          select.appendChild(opt);
        });
      } else {
        (col.options || []).forEach(o => {
          const opt = document.createElement('option');
          opt.value = typeof o === 'object' ? o.value : o;
          opt.textContent = typeof o === 'object' ? o.label : o;
          if (this.columnFilters[col.field] === opt.value) opt.selected = true;
          select.appendChild(opt);
        });
      }

      select.addEventListener('change', (e) => {
        if (e.target.value) {
          this.columnFilters[col.field] = e.target.value;
        } else {
          delete this.columnFilters[col.field];
        }
        this.currentPage = 1;
        this._fetchAndRender();
      });

      grid.appendChild(select);
    });

    // Refresh button
    const refreshBtn = document.createElement('button');
    refreshBtn.type = 'button';
    refreshBtn.className = 'inline-flex items-center justify-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition text-sm text-gray-700';
    refreshBtn.innerHTML = '<i class="ph ph-arrow-clockwise"></i> Refresh';
    refreshBtn.addEventListener('click', () => this._fetchAndRender());
    grid.appendChild(refreshBtn);

    bar.appendChild(grid);
    return bar;
  }

  /**
   * Fetch data and update the table card
   */
  async _fetchAndRender() {
    const card = document.getElementById(this._tableCardId);
    if (!card) return;

    card.innerHTML = '';
    card.appendChild(this._buildLoadingState());

    try {
      const filters = [...this.filters];
      Object.entries(this.columnFilters).forEach(([field, value]) => {
        filters.push({ field, operator: 'eq', value });
      });

      const data = await dataService.list(this.entity, {
        page: this.currentPage,
        pageSize: this.pageSize,
        filters,
        sort: this.sort,
        search: this.searchQuery || null
      });

      card.innerHTML = '';

      // Header bar
      card.appendChild(this._buildCardHeader(data));

      // Table or empty state
      if (data.rows.length === 0) {
        card.appendChild(this._buildEmptyState());
      } else {
        card.appendChild(this._buildTable(data));
      }

      // Pagination
      if (data.total > this.pageSize) {
        card.appendChild(this._buildPagination(data));
      }
    } catch (error) {
      card.innerHTML = '';
      card.appendChild(this._buildError(error.message));
    }
  }

  /**
   * Card header: entity name + record count
   */
  _buildCardHeader(data) {
    const div = document.createElement('div');
    div.className = 'px-6 py-4 border-b border-gray-200 bg-gray-50 flex items-center justify-between';

    const title = document.createElement('h3');
    title.className = 'text-sm font-semibold text-gray-700 uppercase tracking-wider';
    title.textContent = `${this.metadata.display_name || this.entity} List`;

    const count = document.createElement('span');
    count.className = 'text-sm text-gray-500';
    count.textContent = `${data.total} ${data.total === 1 ? 'record' : 'records'}`;

    div.appendChild(title);
    div.appendChild(count);
    return div;
  }

  /**
   * Build table with styled headers and rows
   */
  _buildTable(data) {
    const wrapper = document.createElement('div');
    wrapper.className = 'overflow-x-auto';

    const table = document.createElement('table');
    table.className = 'w-full';

    // Header
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    headerRow.className = 'border-b border-gray-200 bg-gray-50';

    this.metadata.table.columns.forEach(col => {
      const th = document.createElement('th');
      th.className = 'px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider select-none';

      if (col.sortable !== false) {
        th.style.cursor = 'pointer';
        th.addEventListener('click', () => this.toggleSort(col.field));

        const span = document.createElement('span');
        span.textContent = col.title;
        th.appendChild(span);

        const currentSort = this.sort.find(s => s[0] === col.field);
        const icon = document.createElement('i');
        if (currentSort) {
          icon.className = `ph ph-caret-${currentSort[1] === 'asc' ? 'up' : 'down'} ml-1`;
        } else {
          icon.className = 'ph ph-caret-up-down ml-1 text-gray-300';
        }
        th.appendChild(icon);
      } else {
        th.textContent = col.title;
      }

      if (col.width) th.style.width = col.width + 'px';
      headerRow.appendChild(th);
    });

    // Actions column header
    if (this.metadata.table.actions && this.metadata.table.actions.length > 0) {
      const th = document.createElement('th');
      th.className = 'px-6 py-3 text-right text-xs font-semibold text-gray-700 uppercase tracking-wider';
      th.textContent = 'Actions';
      headerRow.appendChild(th);
    }

    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Body
    const tbody = document.createElement('tbody');
    tbody.className = 'divide-y divide-gray-200';
    data.rows.forEach(row => tbody.appendChild(this._buildRow(row)));
    table.appendChild(tbody);

    wrapper.appendChild(table);
    return wrapper;
  }

  /**
   * Build a single table row
   */
  _buildRow(row) {
    const tr = document.createElement('tr');
    tr.className = 'hover:bg-gray-50 transition-colors';

    this.metadata.table.columns.forEach(col => {
      const td = document.createElement('td');
      td.className = 'px-6 py-4 text-sm text-gray-900 whitespace-nowrap';
      const raw = row[col.field];
      td.textContent = this.formatValue(raw, col.type || col.format);
      tr.appendChild(td);
    });

    // Action buttons
    if (this.metadata.table.actions && this.metadata.table.actions.length > 0) {
      const td = document.createElement('td');
      td.className = 'px-6 py-4 text-right';

      const group = document.createElement('div');
      group.className = 'flex justify-end gap-1';

      this.metadata.table.actions.forEach(action => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.title = action.charAt(0).toUpperCase() + action.slice(1);
        btn.className = `p-1.5 rounded-lg transition-colors ${this._actionBtnClass(action)}`;

        const icon = document.createElement('i');
        icon.className = `ph ${this._actionIcon(action)} text-base`;
        btn.appendChild(icon);

        btn.addEventListener('click', () => {
          if (this.onRowAction) this.onRowAction(action, row);
        });

        group.appendChild(btn);
      });

      td.appendChild(group);
      tr.appendChild(td);
    }

    return tr;
  }

  /**
   * Loading spinner state
   */
  _buildLoadingState() {
    const div = document.createElement('div');
    div.className = 'px-6 py-12 text-center';
    div.innerHTML = `
      <div class="inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-3"></div>
      <p class="text-sm text-gray-500">Loading records…</p>
    `;
    return div;
  }

  /**
   * Empty state
   */
  _buildEmptyState() {
    const div = document.createElement('div');
    div.className = 'px-6 py-12 text-center';

    const hasSearch = this.searchQuery || Object.keys(this.columnFilters).length > 0;
    div.innerHTML = `
      <div class="w-16 h-16 mx-auto bg-gray-100 rounded-full flex items-center justify-center mb-4">
        <i class="ph ph-table text-3xl text-gray-400"></i>
      </div>
      <h3 class="text-lg font-medium text-gray-900 mb-1">No records found</h3>
      <p class="text-gray-500 text-sm">
        ${hasSearch ? 'Try adjusting your search or filters.' : 'Get started by creating your first record.'}
      </p>
    `;
    return div;
  }

  /**
   * Pagination bar: "Showing X to Y of Z" + Prev/Next
   */
  _buildPagination(data) {
    const div = document.createElement('div');
    div.className = 'px-6 py-4 border-t border-gray-200 bg-gray-50 flex items-center justify-between';

    const start = (this.currentPage - 1) * this.pageSize + 1;
    const end = Math.min(this.currentPage * this.pageSize, data.total);

    const info = document.createElement('div');
    info.className = 'text-sm text-gray-700';
    info.textContent = `Showing ${start}–${end} of ${data.total} records`;

    const btnGroup = document.createElement('div');
    btnGroup.className = 'flex gap-2 items-center';

    const prevBtn = document.createElement('button');
    prevBtn.type = 'button';
    prevBtn.className = 'px-3 py-1 border border-gray-300 rounded-lg hover:bg-gray-50 transition disabled:opacity-50 disabled:cursor-not-allowed';
    prevBtn.innerHTML = '<i class="ph ph-caret-left"></i>';
    prevBtn.disabled = this.currentPage <= 1;
    prevBtn.addEventListener('click', () => {
      if (this.currentPage > 1) { this.currentPage--; this._fetchAndRender(); }
    });

    const pageInfo = document.createElement('span');
    pageInfo.className = 'px-4 py-1 text-sm text-gray-700';
    pageInfo.textContent = `Page ${this.currentPage} of ${data.pages}`;

    const nextBtn = document.createElement('button');
    nextBtn.type = 'button';
    nextBtn.className = 'px-3 py-1 border border-gray-300 rounded-lg hover:bg-gray-50 transition disabled:opacity-50 disabled:cursor-not-allowed';
    nextBtn.innerHTML = '<i class="ph ph-caret-right"></i>';
    nextBtn.disabled = this.currentPage >= data.pages;
    nextBtn.addEventListener('click', () => {
      if (this.currentPage < data.pages) { this.currentPage++; this._fetchAndRender(); }
    });

    btnGroup.appendChild(prevBtn);
    btnGroup.appendChild(pageInfo);
    btnGroup.appendChild(nextBtn);

    div.appendChild(info);
    div.appendChild(btnGroup);
    return div;
  }

  /**
   * Error state
   */
  _buildError(message) {
    const div = document.createElement('div');
    div.className = 'px-6 py-6';
    const inner = document.createElement('div');
    inner.className = 'flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-lg';
    inner.innerHTML = `
      <i class="ph ph-warning-circle text-red-600 text-xl mt-0.5 flex-shrink-0"></i>
      <div>
        <p class="text-sm font-medium text-red-900">Error loading records</p>
        <p class="text-sm text-red-700 mt-1"></p>
      </div>
    `;
    inner.querySelector('p:last-child').textContent = message;
    div.appendChild(inner);
    return div;
  }

  /**
   * Returns filterable columns that have choice/boolean types (for dropdown filters).
   * Merges form field options into the column descriptor.
   */
  _getFilterableChoiceCols() {
    const formFieldMap = new Map();
    if (this.metadata.form && this.metadata.form.fields) {
      this.metadata.form.fields.forEach(f => {
        formFieldMap.set(f.field || f.name, f);
      });
    }

    return (this.metadata.table.columns || [])
      .filter(col => col.filterable !== false)
      .filter(col => {
        const t = col.type || col.format || '';
        return t === 'choice' || t === 'select' || t === 'enum' || t === 'boolean';
      })
      .map(col => ({
        ...col,
        options: formFieldMap.get(col.field)?.options || []
      }));
  }

  /**
   * Action button hover/color classes
   */
  _actionBtnClass(action) {
    switch (action) {
      case 'view':   return 'text-gray-500 hover:text-blue-600 hover:bg-blue-50';
      case 'edit':   return 'text-gray-500 hover:text-indigo-600 hover:bg-indigo-50';
      case 'delete': return 'text-gray-500 hover:text-red-600 hover:bg-red-50';
      default:       return 'text-gray-500 hover:text-gray-700 hover:bg-gray-100';
    }
  }

  /**
   * Phosphor icon name for each action
   */
  _actionIcon(action) {
    switch (action) {
      case 'view':   return 'ph-eye';
      case 'edit':   return 'ph-pencil';
      case 'delete': return 'ph-trash';
      case 'create': return 'ph-plus';
      default:       return 'ph-gear';
    }
  }

  /**
   * Format a cell value for display
   */
  formatValue(value, type) {
    if (value === null || value === undefined || value === '') return '—';
    switch (type) {
      case 'date':
        try { return new Date(value).toLocaleDateString(); } catch { return value; }
      case 'datetime':
        try { return new Date(value).toLocaleString(); } catch { return value; }
      case 'currency':
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);
      case 'number':
      case 'integer':
      case 'decimal':
        return new Intl.NumberFormat('en-US').format(value);
      case 'boolean':
        return value ? 'Yes' : 'No';
      default:
        return String(value);
    }
  }

  /**
   * Toggle sort direction for a column
   */
  async toggleSort(field) {
    const idx = this.sort.findIndex(s => s[0] === field);
    if (idx >= 0) {
      const newDir = this.sort[idx][1] === 'asc' ? 'desc' : 'asc';
      this.sort[idx] = [field, newDir];
    } else {
      this.sort = [[field, 'asc']];
    }
    await this._fetchAndRender();
  }

  /**
   * Add a programmatic filter and re-render
   */
  addFilter(field, operator, value) {
    this.filters.push({ field, operator, value });
    this.currentPage = 1;
    return this._fetchAndRender();
  }

  /**
   * Clear all filters and re-render from scratch
   */
  clearFilters() {
    this.filters = [];
    this.columnFilters = {};
    this.searchQuery = '';
    this.currentPage = 1;
    return this.render();
  }
}
