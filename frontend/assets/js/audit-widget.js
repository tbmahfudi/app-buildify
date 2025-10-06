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
    this.container.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div></div>';

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
    timeline.className = 'audit-timeline';

    if (data.logs.length === 0) {
      timeline.innerHTML = '<p class="text-muted text-center">No audit logs found</p>';
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
    div.className = 'audit-item border-start border-3 ps-3 pb-3 mb-3';
    div.style.borderColor = this.getActionColor(log.action);

    const header = document.createElement('div');
    header.className = 'd-flex justify-content-between align-items-start mb-2';

    const title = document.createElement('div');
    title.innerHTML = `
      <strong>${this.getActionIcon(log.action)} ${log.action}</strong>
      ${log.entity_type ? `on <span class="badge bg-secondary">${log.entity_type}</span>` : ''}
      ${log.status === 'failure' ? '<span class="badge bg-danger">Failed</span>' : ''}
    `;

    const timestamp = document.createElement('small');
    timestamp.className = 'text-muted';
    timestamp.textContent = this.formatDate(log.created_at);

    header.appendChild(title);
    header.appendChild(timestamp);
    div.appendChild(header);

    // User info
    if (log.user_email) {
      const user = document.createElement('div');
      user.className = 'text-muted small mb-2';
      user.innerHTML = `<i class="bi bi-person"></i> ${log.user_email}`;
      if (log.ip_address) {
        user.innerHTML += ` from ${log.ip_address}`;
      }
      div.appendChild(user);
    }

    // Changes (if any)
    if (log.changes) {
      const changesDiv = this.renderChanges(log.changes);
      div.appendChild(changesDiv);
    }

    if (log.context_info) {
        const contextDiv = this.renderContextInfo(log.context_info);
        div.appendChild(contextDiv);
    }    

    // Error message (if failed)
    if (log.error_message) {
      const error = document.createElement('div');
      error.className = 'alert alert-danger alert-sm mt-2 mb-0';
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
    div.className = 'audit-changes mt-2';

    const details = document.createElement('details');
    const summary = document.createElement('summary');
    summary.className = 'text-primary small';
    summary.style.cursor = 'pointer';
    summary.textContent = 'View changes';
    details.appendChild(summary);

    const changesList = document.createElement('div');
    changesList.className = 'mt-2 p-2 bg-light rounded';

    Object.entries(changes).forEach(([field, change]) => {
      const item = document.createElement('div');
      item.className = 'mb-2';
      item.innerHTML = `
        <strong>${field}:</strong><br>
        <span class="text-danger">- ${change.before !== null ? change.before : 'null'}</span><br>
        <span class="text-success">+ ${change.after !== null ? change.after : 'null'}</span>
      `;
      changesList.appendChild(item);
    });

    details.appendChild(changesList);
    div.appendChild(details);

    return div;
  }

  /**
   * Render filters
   */
  renderFilters() {
    const filters = document.createElement('div');
    filters.className = 'mb-3 p-3 bg-light rounded';
    filters.innerHTML = `
      <div class="row g-2">
        <div class="col-md-4">
          <label class="form-label small">Action</label>
          <select class="form-select form-select-sm" id="filter-action">
            <option value="">All actions</option>
            <option value="CREATE">Create</option>
            <option value="UPDATE">Update</option>
            <option value="DELETE">Delete</option>
            <option value="LOGIN">Login</option>
          </select>
        </div>
        <div class="col-md-4">
          <label class="form-label small">Status</label>
          <select class="form-select form-select-sm" id="filter-status">
            <option value="">All statuses</option>
            <option value="success">Success</option>
            <option value="failure">Failure</option>
          </select>
        </div>
        <div class="col-md-4">
          <label class="form-label small">&nbsp;</label>
          <div>
            <button class="btn btn-primary btn-sm" id="btn-apply-filters">Apply</button>
            <button class="btn btn-secondary btn-sm" id="btn-clear-filters">Clear</button>
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
    const ul = document.createElement('ul');
    ul.className = 'pagination pagination-sm justify-content-center';

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

    // Page info
    const infoLi = document.createElement('li');
    infoLi.className = 'page-item disabled';
    const infoSpan = document.createElement('span');
    infoSpan.className = 'page-link';
    infoSpan.textContent = `Page ${this.currentPage} of ${totalPages}`;
    infoLi.appendChild(infoSpan);
    ul.appendChild(infoLi);

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

    renderContextInfo(contextInfo) {
        const div = document.createElement('div');
        div.className = 'audit-context mt-2';
        
        const details = document.createElement('details');
        const summary = document.createElement('summary');
        summary.className = 'text-info small';
        summary.style.cursor = 'pointer';
        summary.textContent = 'View context';
        details.appendChild(summary);
        
        const contextList = document.createElement('div');
        contextList.className = 'mt-2 p-2 bg-light rounded';
        contextList.innerHTML = '<pre>' + JSON.stringify(contextInfo, null, 2) + '</pre>';
        
        details.appendChild(contextList);
        div.appendChild(details);
        
        return div;
    }  

  /**
   * Get action color
   */
  getActionColor(action) {
    const colors = {
      'CREATE': '#28a745',
      'UPDATE': '#007bff',
      'DELETE': '#dc3545',
      'LOGIN': '#17a2b8',
      'LOGOUT': '#6c757d'
    };
    return colors[action] || '#6c757d';
  }

  /**
   * Get action icon
   */
  getActionIcon(action) {
    const icons = {
      'CREATE': '➕',
      'UPDATE': '✏️',
      'DELETE': '🗑️',
      'LOGIN': '🔑',
      'LOGOUT': '🚪'
    };
    return icons[action] || '📝';
  }

  /**
   * Format date
   */
  formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    // Less than 1 minute
    if (diff < 60000) {
      return 'Just now';
    }
    
    // Less than 1 hour
    if (diff < 3600000) {
      const minutes = Math.floor(diff / 60000);
      return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    }
    
    // Less than 24 hours
    if (diff < 86400000) {
      const hours = Math.floor(diff / 3600000);
      return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    }
    
    // Otherwise show full date
    return date.toLocaleString();
  }

  /**
   * Render error
   */
  renderError(message) {
    this.container.innerHTML = `
      <div class="alert alert-danger">
        <strong>Error:</strong> ${message}
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

// Add CSS for audit timeline
const style = document.createElement('style');
style.textContent = `
  .audit-timeline {
    position: relative;
  }
  .audit-item {
    position: relative;
  }
  .audit-changes details summary {
    list-style: none;
  }
  .audit-changes details summary::-webkit-details-marker {
    display: none;
  }
`;
document.head.appendChild(style);