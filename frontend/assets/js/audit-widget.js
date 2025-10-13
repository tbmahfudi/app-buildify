import { apiFetch } from './api.js';

/**
 * Audit Trail Widget - Display audit logs
 */
export class AuditWidget {
  constructor(container, options = {}) {
    this.container = container;
    this.options = {
      entityType: options.entityType || null,
      entityId: options.entityId || null,
      pageSize: options.pageSize || 20,
      showFilters: options.showFilters !== false
    };
    this.currentPage = 1;
    this.filters = {};
  }

  /**
   * Render the widget
   */
  async render() {
    this.container.innerHTML = '<div class="flex items-center justify-center p-8"><div class="text-center"><div class="inline-block"><div class="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div></div><p class="mt-3 text-gray-600">Loading...</p></div></div>';

    try {
      const logs = await this.fetchLogs();
      this.renderLogs(logs);
    } catch (error) {
      this.renderError(error.message);
    }
  }

  /**
   * Fetch audit logs
   */
  async fetchLogs() {
    const payload = {
      page: this.currentPage,
      page_size: this.options.pageSize,
      ...this.filters
    };

    if (this.options.entityType) {
      payload.entity_type = this.options.entityType;
    }
    if (this.options.entityId) {
      payload.entity_id = this.options.entityId;
    }

    const response = await apiFetch('/audit/list', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    return await response.json();
  }

  /**
   * Render logs
   */
  renderLogs(data) {
    this.container.innerHTML = '';

    // Filters (if enabled)
    if (this.options.showFilters) {
      this.renderFilters();
    }

    // Timeline
    const timeline = document.createElement('div');
    timeline.className = 'audit-timeline space-y-4';

    if (data.logs.length === 0) {
      timeline.innerHTML = '<div class="text-center py-8 text-gray-500"><i class="bi bi-inbox text-2xl block mb-2"></i><p>No audit logs found</p></div>';
    } else {
      data.logs.forEach(log => {
        const item = this.renderLogItem(log);
        timeline.appendChild(item);
      });
    }

    this.container.appendChild(timeline);

    // Pagination
    if (data.total > this.options.pageSize) {
      this.renderPagination(data);
    }
  }

  /**
   * Render single log item
   */
  renderLogItem(log) {
    const div = document.createElement('div');
    const borderColor = this.getActionBorderClass(log.action);
    div.className = `audit-item bg-white rounded-lg border-l-4 ${borderColor} p-4 shadow-sm`;

    const header = document.createElement('div');
    header.className = 'flex items-start justify-between mb-3';

    const titleDiv = document.createElement('div');
    titleDiv.className = 'flex items-center gap-3 flex-1';
    
    const icon = document.createElement('div');
    icon.className = `flex items-center justify-center w-10 h-10 rounded-lg ${this.getActionBgClass(log.action)}`;
    icon.innerHTML = this.getActionIcon(log.action);
    
    const titleContent = document.createElement('div');
    titleContent.innerHTML = `
      <div class="font-semibold text-gray-900">${log.action}</div>
      <div class="text-sm text-gray-600">
        ${log.entity_type ? `<span class="inline-block bg-gray-100 px-2 py-1 rounded text-xs mr-2">${log.entity_type}</span>` : ''}
        ${log.status === 'failure' ? '<span class="inline-block bg-red-100 text-red-700 px-2 py-1 rounded text-xs font-medium">Failed</span>' : ''}
      </div>
    `;
    
    titleDiv.appendChild(icon);
    titleDiv.appendChild(titleContent);

    const timestamp = document.createElement('small');
    timestamp.className = 'text-gray-500 text-sm whitespace-nowrap ml-4';
    timestamp.textContent = this.formatDate(log.created_at);

    header.appendChild(titleDiv);
    header.appendChild(timestamp);
    div.appendChild(header);

    // User info
    if (log.user_email) {
      const user = document.createElement('div');
      user.className = 'text-sm text-gray-600 mb-3 flex items-center gap-2';
      user.innerHTML = `
        <i class="bi bi-person-circle"></i>
        <span>${log.user_email}</span>
        ${log.ip_address ? `<span class="text-gray-500">from ${log.ip_address}</span>` : ''}
      `;
      div.appendChild(user);
    }

    // Changes (if any)
    if (log.changes) {
      const changesDiv = this.renderChanges(log.changes);
      div.appendChild(changesDiv);
    }

    // Context info
    if (log.context_info) {
      const contextDiv = this.renderContextInfo(log.context_info);
      div.appendChild(contextDiv);
    }

    // Error message (if failed)
    if (log.error_message) {
      const error = document.createElement('div');
      error.className = 'mt-3 p-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded';
      error.textContent = log.error_message;
      div.appendChild(error);
    }

    return div;
  }

  /**
   * Render changes diff
   */
  renderChanges(changes) {
    const div = document.createElement('div');
    div.className = 'audit-changes mt-3';

    const details = document.createElement('details');
    details.className = 'cursor-pointer';
    
    const summary = document.createElement('summary');
    summary.className = 'text-blue-600 font-medium text-sm hover:text-blue-700';
    summary.textContent = 'View changes';
    summary.style.listStyle = 'none';
    details.appendChild(summary);

    const changesList = document.createElement('div');
    changesList.className = 'mt-2 p-3 bg-gray-50 rounded border border-gray-200 space-y-2';

    Object.entries(changes).forEach(([field, change]) => {
      const item = document.createElement('div');
      item.className = 'text-sm';
      item.innerHTML = `
        <div class="font-medium text-gray-900">${field}</div>
        <div class="flex gap-2 mt-1">
          <span class="flex-1 text-red-700"><i class="bi bi-dash"></i> ${change.before !== null ? change.before : '<em class="text-gray-500">null</em>'}</span>
          <span class="flex-1 text-green-700"><i class="bi bi-plus"></i> ${change.after !== null ? change.after : '<em class="text-gray-500">null</em>'}</span>
        </div>
      `;
      changesList.appendChild(item);
    });

    details.appendChild(changesList);
    div.appendChild(details);

    return div;
  }

  /**
   * Render context info
   */
  renderContextInfo(contextInfo) {
    const div = document.createElement('div');
    div.className = 'audit-context mt-3';
    
    const details = document.createElement('details');
    details.className = 'cursor-pointer';
    
    const summary = document.createElement('summary');
    summary.className = 'text-blue-600 font-medium text-sm hover:text-blue-700';
    summary.textContent = 'View context';
    summary.style.listStyle = 'none';
    details.appendChild(summary);
    
    const contextList = document.createElement('div');
    contextList.className = 'mt-2 p-3 bg-gray-50 rounded border border-gray-200 overflow-x-auto';
    
    const pre = document.createElement('pre');
    pre.className = 'text-xs text-gray-600 font-mono whitespace-pre-wrap break-words';
    pre.textContent = JSON.stringify(contextInfo, null, 2);
    contextList.appendChild(pre);
    
    details.appendChild(contextList);
    div.appendChild(details);
    
    return div;
  }

  /**
   * Render filters
   */
  renderFilters() {
    const filters = document.createElement('div');
    filters.className = 'mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200';
    filters.innerHTML = `
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Action</label>
          <select class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" id="filter-action">
            <option value="">All actions</option>
            <option value="CREATE">Create</option>
            <option value="UPDATE">Update</option>
            <option value="DELETE">Delete</option>
            <option value="LOGIN">Login</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Status</label>
          <select class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" id="filter-status">
            <option value="">All statuses</option>
            <option value="success">Success</option>
            <option value="failure">Failure</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">&nbsp;</label>
          <div class="flex gap-2">
            <button type="button" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition text-sm font-medium" id="btn-apply-filters">
              <i class="bi bi-check-lg"></i> Apply
            </button>
            <button type="button" class="px-4 py-2 bg-gray-300 text-gray-900 rounded-lg hover:bg-gray-400 transition text-sm font-medium" id="btn-clear-filters">
              <i class="bi bi-arrow-counterclockwise"></i> Clear
            </button>
          </div>
        </div>
      </div>
    `;

    this.container.appendChild(filters);

    // Wire up buttons
    document.getElementById('btn-apply-filters').onclick = () => {
      this.filters.action = document.getElementById('filter-action').value;
      this.filters.status = document.getElementById('filter-status').value;
      this.currentPage = 1;
      this.render();
    };

    document.getElementById('btn-clear-filters').onclick = () => {
      this.filters = {};
      this.currentPage = 1;
      document.getElementById('filter-action').value = '';
      document.getElementById('filter-status').value = '';
      this.render();
    };
  }

  /**
   * Render pagination
   */
  renderPagination(data) {
    const totalPages = Math.ceil(data.total / this.options.pageSize);
    
    const nav = document.createElement('nav');
    nav.className = 'mt-6 flex items-center justify-center gap-2';

    // Previous
    const prevBtn = document.createElement('button');
    prevBtn.className = 'px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition disabled:opacity-50 disabled:cursor-not-allowed';
    prevBtn.textContent = '← Previous';
    prevBtn.disabled = this.currentPage === 1;
    prevBtn.onclick = () => {
      if (this.currentPage > 1) {
        this.currentPage--;
        this.render();
      }
    };
    nav.appendChild(prevBtn);

    // Page info
    const pageInfo = document.createElement('span');
    pageInfo.className = 'px-4 py-2 text-gray-700 font-medium';
    pageInfo.textContent = `Page ${this.currentPage} of ${totalPages}`;
    nav.appendChild(pageInfo);

    // Next
    const nextBtn = document.createElement('button');
    nextBtn.className = 'px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition disabled:opacity-50 disabled:cursor-not-allowed';
    nextBtn.textContent = 'Next →';
    nextBtn.disabled = this.currentPage === totalPages;
    nextBtn.onclick = () => {
      if (this.currentPage < totalPages) {
        this.currentPage++;
        this.render();
      }
    };
    nav.appendChild(nextBtn);

    this.container.appendChild(nav);
  }

  /**
   * Get action color
   */
  getActionBorderClass(action) {
    const colors = {
      'CREATE': 'border-green-500',
      'UPDATE': 'border-blue-500',
      'DELETE': 'border-red-500',
      'LOGIN': 'border-cyan-500',
      'LOGOUT': 'border-gray-500'
    };
    return colors[action] || 'border-gray-500';
  }

  /**
   * Get action background class
   */
  getActionBgClass(action) {
    const colors = {
      'CREATE': 'bg-green-100',
      'UPDATE': 'bg-blue-100',
      'DELETE': 'bg-red-100',
      'LOGIN': 'bg-cyan-100',
      'LOGOUT': 'bg-gray-100'
    };
    return colors[action] || 'bg-gray-100';
  }

  /**
   * Get action icon
   */
  getActionIcon(action) {
    const icons = {
      'CREATE': '<i class="bi bi-plus-circle text-green-600"></i>',
      'UPDATE': '<i class="bi bi-pencil-square text-blue-600"></i>',
      'DELETE': '<i class="bi bi-trash text-red-600"></i>',
      'LOGIN': '<i class="bi bi-key text-cyan-600"></i>',
      'LOGOUT': '<i class="bi bi-door-open text-gray-600"></i>'
    };
    return icons[action] || '<i class="bi bi-file-earmark text-gray-600"></i>';
  }

  /**
   * Format date
   */
  formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) {
      return 'Just now';
    }
    
    if (diff < 3600000) {
      const minutes = Math.floor(diff / 60000);
      return `${minutes}m ago`;
    }
    
    if (diff < 86400000) {
      const hours = Math.floor(diff / 3600000);
      return `${hours}h ago`;
    }
    
    return date.toLocaleDateString();
  }

  /**
   * Render error
   */
  renderError(message) {
    this.container.innerHTML = `
      <div class="p-4 bg-red-50 border border-red-200 rounded-lg">
        <strong class="text-red-800">Error:</strong>
        <p class="text-red-700 text-sm mt-1">${message}</p>
      </div>
    `;
  }

  /**
   * Refresh widget
   */
  refresh() {
    return this.render();
  }
}