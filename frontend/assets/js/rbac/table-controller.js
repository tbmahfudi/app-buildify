/**
 * Generic Table Controller
 * Eliminates duplication across roles/permissions/groups/users tables
 */

import { apiFetch } from '../api.js';
import { showToast } from '../ui-utils.js';

export class TableController {
  constructor(config) {
    this.config = {
      name: config.name,                    // 'roles', 'permissions', etc.
      endpoint: config.endpoint,            // '/rbac/roles'
      columns: config.columns,              // Column definitions
      filters: config.filters || [],        // Filter configurations
      actions: config.actions || [],        // Action buttons
      emptyMessage: config.emptyMessage || 'No items found',
      onRowClick: config.onRowClick || null,
      transformData: config.transformData || (item => item)
    };

    this.state = {
      data: [],
      total: 0,
      currentPage: 0,
      pageSize: 20,
      filters: {},
      selectedRows: new Set()
    };

    this.elements = {};
    this.init();
  }

  init() {
    // Get DOM elements
    this.elements.container = document.getElementById(`content-${this.config.name}`);
    this.elements.tbody = document.getElementById(`${this.config.name}-table-body`);
    this.elements.searchInput = document.getElementById(`${this.config.name}-search`);
    this.elements.prevBtn = document.getElementById(`${this.config.name}-prev-page`);
    this.elements.nextBtn = document.getElementById(`${this.config.name}-next-page`);

    // Setup event listeners
    this.setupEventListeners();
  }

  setupEventListeners() {
    // Search
    if (this.elements.searchInput) {
      this.elements.searchInput.addEventListener('input', this.debounce(() => {
        this.state.filters.search = this.elements.searchInput.value;
        this.state.currentPage = 0;
        this.load();
      }, 300));
    }

    // Filter dropdowns
    this.config.filters.forEach(filter => {
      const element = document.getElementById(`${this.config.name}-${filter.id}-filter`);
      if (element) {
        element.addEventListener('change', () => {
          this.state.filters[filter.id] = element.value;
          this.state.currentPage = 0;
          this.load();
        });
      }
    });

    // Pagination
    if (this.elements.prevBtn) {
      this.elements.prevBtn.addEventListener('click', () => {
        if (this.state.currentPage > 0) {
          this.state.currentPage--;
          this.load();
        }
      });
    }

    if (this.elements.nextBtn) {
      this.elements.nextBtn.addEventListener('click', () => {
        this.state.currentPage++;
        this.load();
      });
    }

    // Bulk select all
    const selectAllCheckbox = document.getElementById(`${this.config.name}-select-all`);
    if (selectAllCheckbox) {
      selectAllCheckbox.addEventListener('change', (e) => {
        this.toggleSelectAll(e.target.checked);
      });
    }
  }

  async load() {
    try {
      this.showLoading();

      const params = new URLSearchParams({
        skip: this.state.currentPage * this.state.pageSize,
        limit: this.state.pageSize
      });

      // Add filters to params
      Object.entries(this.state.filters).forEach(([key, value]) => {
        if (value) {
          // Handle special boolean filters
          if (key === 'status') {
            params.append('is_active', value === 'active');
          } else if (key === 'type') {
            params.append(`${this.config.name.slice(0, -1)}_type`, value);
          } else {
            params.append(key, value);
          }
        }
      });

      const response = await apiFetch(`${this.config.endpoint}?${params}`);
      const data = await response.json();

      this.state.data = data.items || [];
      this.state.total = data.total || 0;

      this.render();
      this.updatePagination();

    } catch (error) {
      console.error(`Error loading ${this.config.name}:`, error);
      showToast(`Failed to load ${this.config.name}`, 'error');
      this.showError();
    }
  }

  render() {
    if (!this.elements.tbody) return;

    if (this.state.data.length === 0) {
      this.elements.tbody.innerHTML = `
        <tr>
          <td colspan="${this.config.columns.length + 2}" class="px-6 py-12 text-center text-gray-500">
            <i class="ph ph-${this.config.icon || 'database'} text-4xl mb-2"></i>
            <div>${this.config.emptyMessage}</div>
          </td>
        </tr>
      `;
      return;
    }

    this.elements.tbody.innerHTML = this.state.data.map(item => this.renderRow(item)).join('');

    // Add row click handlers
    if (this.config.onRowClick) {
      this.elements.tbody.querySelectorAll('tr').forEach((row, index) => {
        row.addEventListener('click', (e) => {
          // Don't trigger if clicking checkbox or action button
          if (e.target.type === 'checkbox' || e.target.closest('button')) return;
          this.config.onRowClick(this.state.data[index]);
        });
      });
    }

    // Add checkbox handlers
    this.elements.tbody.querySelectorAll('.row-checkbox').forEach((checkbox, index) => {
      checkbox.addEventListener('change', (e) => {
        this.toggleRowSelection(this.state.data[index].id, e.target.checked);
      });
    });
  }

  renderRow(item) {
    const transformed = this.config.transformData(item);

    return `
      <tr class="hover:bg-gray-50 cursor-pointer ${this.state.selectedRows.has(item.id) ? 'bg-blue-50' : ''}">
        ${this.config.bulkActions ? `
          <td class="px-6 py-4">
            <input type="checkbox" class="row-checkbox w-4 h-4 text-blue-600 rounded"
              data-id="${item.id}" ${this.state.selectedRows.has(item.id) ? 'checked' : ''}>
          </td>
        ` : ''}
        ${this.config.columns.map(col => `
          <td class="px-6 py-4 ${col.class || ''}">
            ${col.render ? col.render(transformed) : transformed[col.field] || '-'}
          </td>
        `).join('')}
        <td class="px-6 py-4">
          <div class="flex gap-2">
            ${this.config.actions.map(action => `
              <button onclick="rbacManager.${action.handler}('${item.id}')"
                class="text-${action.color || 'blue'}-600 hover:text-${action.color || 'blue'}-800"
                title="${action.label}">
                <i class="ph ph-${action.icon}"></i>
              </button>
            `).join('')}
          </div>
        </td>
      </tr>
    `;
  }

  updatePagination() {
    const start = this.state.currentPage * this.state.pageSize + 1;
    const end = Math.min((this.state.currentPage + 1) * this.state.pageSize, this.state.total);

    const startEl = document.getElementById(`${this.config.name}-showing-start`);
    const endEl = document.getElementById(`${this.config.name}-showing-end`);
    const totalEl = document.getElementById(`${this.config.name}-total`);

    if (startEl) startEl.textContent = start;
    if (endEl) endEl.textContent = end;
    if (totalEl) totalEl.textContent = this.state.total;

    // Update button states
    if (this.elements.prevBtn) {
      this.elements.prevBtn.disabled = this.state.currentPage === 0;
    }
    if (this.elements.nextBtn) {
      this.elements.nextBtn.disabled = end >= this.state.total;
    }

    // Update selection indicator
    this.updateBulkActionBar();
  }

  toggleRowSelection(id, selected) {
    if (selected) {
      this.state.selectedRows.add(id);
    } else {
      this.state.selectedRows.delete(id);
    }
    this.updateBulkActionBar();
    this.render();
  }

  toggleSelectAll(selected) {
    if (selected) {
      this.state.data.forEach(item => this.state.selectedRows.add(item.id));
    } else {
      this.state.selectedRows.clear();
    }
    this.updateBulkActionBar();
    this.render();
  }

  updateBulkActionBar() {
    const bulkBar = document.getElementById(`${this.config.name}-bulk-actions`);
    if (!bulkBar) return;

    const count = this.state.selectedRows.size;
    if (count > 0) {
      bulkBar.classList.remove('hidden');
      const countEl = bulkBar.querySelector('.selection-count');
      if (countEl) countEl.textContent = count;
    } else {
      bulkBar.classList.add('hidden');
    }
  }

  getSelectedIds() {
    return Array.from(this.state.selectedRows);
  }

  clearSelection() {
    this.state.selectedRows.clear();
    this.updateBulkActionBar();
    this.render();
  }

  showLoading() {
    if (this.elements.tbody) {
      this.elements.tbody.innerHTML = `
        <tr>
          <td colspan="${this.config.columns.length + 2}" class="px-6 py-12 text-center">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <div class="mt-2 text-gray-500">Loading...</div>
          </td>
        </tr>
      `;
    }
  }

  showError() {
    if (this.elements.tbody) {
      this.elements.tbody.innerHTML = `
        <tr>
          <td colspan="${this.config.columns.length + 2}" class="px-6 py-12 text-center text-red-500">
            <i class="ph ph-warning-circle text-4xl mb-2"></i>
            <div>Failed to load data</div>
            <button onclick="location.reload()" class="mt-2 text-sm text-blue-600 hover:underline">
              Retry
            </button>
          </td>
        </tr>
      `;
    }
  }

  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  refresh() {
    return this.load();
  }

  reset() {
    this.state.filters = {};
    this.state.currentPage = 0;
    this.state.selectedRows.clear();

    // Reset UI inputs
    if (this.elements.searchInput) this.elements.searchInput.value = '';
    this.config.filters.forEach(filter => {
      const element = document.getElementById(`${this.config.name}-${filter.id}-filter`);
      if (element) element.value = '';
    });

    return this.load();
  }
}
