import { dataService } from './data-service.js';
import { metadataService } from './metadata-service.js';

/**
 * Dynamic Table - Renders data tables from metadata
 */
export class DynamicTable {
  constructor(container, entity, metadata) {
    this.container = container;
    this.entity = entity;
    this.metadata = metadata;
    this.currentPage = 1;
    this.pageSize = metadata.table.page_size || 25;
    this.filters = [];
    this.sort = metadata.table.default_sort || [];
    this.onRowAction = null;
  }

  /**
   * Render the table
   */
  async render() {
    this.container.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div></div>';

    try {
      const data = await dataService.list(this.entity, {
        page: this.currentPage,
        pageSize: this.pageSize,
        filters: this.filters,
        sort: this.sort
      });

      this.renderTable(data);
      this.renderPagination(data);
    } catch (error) {
      this.renderError(error.message);
    }
  }

  /**
   * Render table structure
   */
  renderTable(data) {
    const wrapper = document.createElement('div');
    wrapper.className = 'table-responsive';

    const table = document.createElement('table');
    table.className = 'table table-striped table-hover';

    // Header
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    
    this.metadata.table.columns.forEach(col => {
      const th = document.createElement('th');
      th.textContent = col.title;
      
      if (col.sortable) {
        th.style.cursor = 'pointer';
        th.onclick = () => this.toggleSort(col.field);
        
        // Show sort indicator
        const currentSort = this.sort.find(s => s[0] === col.field);
        if (currentSort) {
          const icon = currentSort[1] === 'asc' ? '▲' : '▼';
          th.innerHTML += ` ${icon}`;
        }
      }
      
      if (col.width) {
        th.style.width = col.width + 'px';
      }
      
      headerRow.appendChild(th);
    });

    // Actions column
    if (this.metadata.table.actions && this.metadata.table.actions.length > 0) {
      const th = document.createElement('th');
      th.textContent = 'Actions';
      th.style.width = '150px';
      headerRow.appendChild(th);
    }

    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Body
    const tbody = document.createElement('tbody');
    
    if (data.rows.length === 0) {
      const tr = document.createElement('tr');
      const td = document.createElement('td');
      td.colSpan = this.metadata.table.columns.length + (this.metadata.table.actions ? 1 : 0);
      td.className = 'text-center text-muted';
      td.textContent = 'No records found';
      tr.appendChild(td);
      tbody.appendChild(tr);
    } else {
      data.rows.forEach(row => {
        const tr = this.renderRow(row);
        tbody.appendChild(tr);
      });
    }

    table.appendChild(tbody);
    wrapper.appendChild(table);
    
    this.container.innerHTML = '';
    this.container.appendChild(wrapper);
  }

  /**
   * Render single row
   */
  renderRow(row) {
    const tr = document.createElement('tr');

    this.metadata.table.columns.forEach(col => {
      const td = document.createElement('td');
      td.textContent = this.formatValue(row[col.field], col.format);
      tr.appendChild(td);
    });

    // Actions
    if (this.metadata.table.actions && this.metadata.table.actions.length > 0) {
      const td = document.createElement('td');
      td.className = 'table-actions';
      
      this.metadata.table.actions.forEach(action => {
        const btn = document.createElement('button');
        btn.className = `btn btn-sm btn-outline-${this.getActionClass(action)} me-1`;
        btn.textContent = action.charAt(0).toUpperCase() + action.slice(1);
        btn.onclick = () => {
          if (this.onRowAction) {
            this.onRowAction(action, row);
          }
        };
        td.appendChild(btn);
      });
      
      tr.appendChild(td);
    }

    return tr;
  }

  /**
   * Format value based on format type
   */
  formatValue(value, format) {
    if (value === null || value === undefined) return '';

    switch (format) {
      case 'date':
        return new Date(value).toLocaleDateString();
      case 'datetime':
        return new Date(value).toLocaleString();
      case 'currency':
        return new Intl.NumberFormat('en-US', { 
          style: 'currency', 
          currency: 'USD' 
        }).format(value);
      case 'number':
        return new Intl.NumberFormat('en-US').format(value);
      default:
        return value;
    }
  }

  /**
   * Get action button class
   */
  getActionClass(action) {
    switch (action) {
      case 'view': return 'info';
      case 'edit': return 'primary';
      case 'delete': return 'danger';
      default: return 'secondary';
    }
  }

  /**
   * Toggle sort direction
   */
  async toggleSort(field) {
    const existing = this.sort.findIndex(s => s[0] === field);
    
    if (existing >= 0) {
      // Toggle direction
      const direction = this.sort[existing][1] === 'asc' ? 'desc' : 'asc';
      this.sort[existing] = [field, direction];
    } else {
      // Add new sort
      this.sort = [[field, 'asc']];
    }

    await this.render();
  }

  /**
   * Render pagination
   */
  renderPagination(data) {
    const totalPages = Math.ceil(data.total / this.pageSize);
    
    if (totalPages <= 1) return;

    const nav = document.createElement('nav');
    nav.setAttribute('aria-label', 'Table pagination');
    
    const ul = document.createElement('ul');
    ul.className = 'pagination justify-content-center';

    // Previous
    const prevLi = document.createElement('li');
    prevLi.className = 'page-item' + (this.currentPage === 1 ? ' disabled' : '');
    const prevA = document.createElement('a');
    prevA.className = 'page-link';
    prevA.href = '#';
    prevA.textContent = 'Previous';
    prevA.onclick = (e) => {
      e.preventDefault();
      if (this.currentPage > 1) {
        this.currentPage--;
        this.render();
      }
    };
    prevLi.appendChild(prevA);
    ul.appendChild(prevLi);

    // Page numbers
    const startPage = Math.max(1, this.currentPage - 2);
    const endPage = Math.min(totalPages, this.currentPage + 2);

    for (let i = startPage; i <= endPage; i++) {
      const li = document.createElement('li');
      li.className = 'page-item' + (i === this.currentPage ? ' active' : '');
      const a = document.createElement('a');
      a.className = 'page-link';
      a.href = '#';
      a.textContent = i;
      a.onclick = (e) => {
        e.preventDefault();
        this.currentPage = i;
        this.render();
      };
      li.appendChild(a);
      ul.appendChild(li);
    }

    // Next
    const nextLi = document.createElement('li');
    nextLi.className = 'page-item' + (this.currentPage === totalPages ? ' disabled' : '');
    const nextA = document.createElement('a');
    nextA.className = 'page-link';
    nextA.href = '#';
    nextA.textContent = 'Next';
    nextA.onclick = (e) => {
      e.preventDefault();
      if (this.currentPage < totalPages) {
        this.currentPage++;
        this.render();
      }
    };
    nextLi.appendChild(nextA);
    ul.appendChild(nextLi);

    nav.appendChild(ul);
    this.container.appendChild(nav);
  }

  /**
   * Render error message
   */
  renderError(message) {
    this.container.innerHTML = `
      <div class="alert alert-danger" role="alert">
        <strong>Error:</strong> ${message}
      </div>
    `;
  }

  /**
   * Add filter
   */
  addFilter(field, operator, value) {
    this.filters.push({ field, operator, value });
    this.currentPage = 1;
    return this.render();
  }

  /**
   * Clear filters
   */
  clearFilters() {
    this.filters = [];
    this.currentPage = 1;
    return this.render();
  }

  /**
   * Refresh table
   */
  refresh() {
    return this.render();
  }
}