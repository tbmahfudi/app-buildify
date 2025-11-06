/**
 * Enhanced Audit Module with Advanced Filtering
 * Provides comprehensive audit trail viewing with filters, search, and pagination
 */

import { apiFetch } from './api.js';
import { showToast, showLoading, hideLoading } from './ui-utils.js';

let auditEvents = [];
let currentPage = 1;
let pageSize = 25;
let totalEvents = 0;
let currentFilters = {};

// Initialize on route load
document.addEventListener('route:loaded', async (e) => {
  if (e.detail.route === 'audit') {
    initAudit();
  }
});

function initAudit() {
  // Event listeners
  document.getElementById('btn-refresh-audit')?.addEventListener('click', loadAuditEvents);
  document.getElementById('btn-apply-filters')?.addEventListener('click', applyFilters);
  document.getElementById('btn-clear-filters')?.addEventListener('click', clearFilters);

  // Pagination
  document.getElementById('btn-prev-page')?.addEventListener('click', () => changePage(-1));
  document.getElementById('btn-next-page')?.addEventListener('click', () => changePage(1));

  // Detail modal
  document.getElementById('btn-close-detail')?.addEventListener('click', closeDetailModal);
  document.getElementById('btn-close-detail-footer')?.addEventListener('click', closeDetailModal);

  // Load initial data
  loadAuditEvents();
  loadSummaryStats();
}

async function loadAuditEvents() {
  showLoading();

  try {
    const filters = buildFilters();

    const res = await apiFetch('/audit/list', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        filters,
        page: currentPage,
        page_size: pageSize,
        sort: [['created_at', 'desc']]
      })
    });

    if (!res.ok) throw new Error('Failed to load audit events');

    const data = await res.json();
    auditEvents = data.logs || [];
    totalEvents = data.total || auditEvents.length;

    renderAuditEvents(auditEvents);
    updatePagination();
  } catch (err) {
    console.error('Failed to load audit events:', err);
    showToast('Failed to load audit events', 'error');
    auditEvents = [];
    renderAuditEvents([]);
  } finally {
    hideLoading();
  }
}

async function loadSummaryStats() {
  try {
    const res = await apiFetch('/audit/summary');

    if (!res.ok) return;

    const stats = await res.json();

    document.getElementById('stat-total').textContent = stats.total_events || 0;
    document.getElementById('stat-success').textContent = stats.successful_events || 0;
    document.getElementById('stat-failure').textContent = stats.failed_events || 0;
    document.getElementById('stat-users').textContent = stats.unique_users || 0;
  } catch (err) {
    console.error('Failed to load audit stats:', err);
  }
}

function buildFilters() {
  const filters = [];

  // Action filter
  const action = document.getElementById('filter-action')?.value;
  if (action) {
    filters.push({ field: 'action', operator: 'eq', value: action });
  }

  // Entity type filter
  const entityType = document.getElementById('filter-entity-type')?.value;
  if (entityType) {
    filters.push({ field: 'entity_type', operator: 'eq', value: entityType });
  }

  // Status filter
  const status = document.getElementById('filter-status')?.value;
  if (status) {
    filters.push({ field: 'status', operator: 'eq', value: status });
  }

  // User email filter
  const userEmail = document.getElementById('filter-user')?.value;
  if (userEmail) {
    filters.push({ field: 'user_email', operator: 'like', value: `%${userEmail}%` });
  }

  // Date range filters
  const dateFrom = document.getElementById('filter-date-from')?.value;
  if (dateFrom) {
    filters.push({ field: 'created_at', operator: 'gte', value: `${dateFrom}T00:00:00` });
  }

  const dateTo = document.getElementById('filter-date-to')?.value;
  if (dateTo) {
    filters.push({ field: 'created_at', operator: 'lte', value: `${dateTo}T23:59:59` });
  }

  // Search in details (if backend supports it)
  const search = document.getElementById('filter-search')?.value;
  if (search) {
    // This might need custom backend support
    filters.push({ field: 'details', operator: 'like', value: `%${search}%` });
  }

  currentFilters = filters;
  return filters;
}

function renderAuditEvents(events) {
  const container = document.getElementById('audit-container');
  const emptyState = document.getElementById('empty-state');
  const countEl = document.getElementById('audit-count');

  if (!container) return;

  if (events.length === 0) {
    container.innerHTML = '';
    if (emptyState) emptyState.classList.remove('hidden');
    if (countEl) countEl.textContent = '0 events';
    return;
  }

  if (emptyState) emptyState.classList.add('hidden');
  if (countEl) countEl.textContent = `${totalEvents} events`;

  container.innerHTML = events.map(event => {
    const statusColors = {
      success: 'bg-green-100 text-green-800',
      failure: 'bg-red-100 text-red-800',
      warning: 'bg-yellow-100 text-yellow-800'
    };

    const actionIcons = {
      CREATE: 'bi-plus-circle-fill text-green-600',
      UPDATE: 'bi-pencil-fill text-blue-600',
      DELETE: 'bi-trash-fill text-red-600',
      LOGIN: 'bi-box-arrow-in-right text-purple-600',
      LOGOUT: 'bi-box-arrow-right text-gray-600'
    };

    const statusColor = statusColors[event.status] || 'bg-gray-100 text-gray-800';
    const actionIcon = actionIcons[event.action] || 'bi-circle-fill text-gray-600';

    return `
      <div class="px-6 py-4 hover:bg-gray-50 transition cursor-pointer" onclick="window.viewAuditDetail('${event.id}')">
        <div class="flex items-start gap-4">
          <!-- Icon -->
          <div class="flex-shrink-0 w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center mt-1">
            <i class="bi ${actionIcon}"></i>
          </div>

          <!-- Content -->
          <div class="flex-1 min-w-0">
            <div class="flex items-start justify-between gap-4">
              <div>
                <div class="flex items-center gap-2 mb-1">
                  <span class="text-sm font-semibold text-gray-900">${escapeHtml(event.action)}</span>
                  ${event.entity_type ? `
                    <span class="text-xs text-gray-500">on</span>
                    <span class="text-xs font-medium text-blue-600">${escapeHtml(event.entity_type)}</span>
                  ` : ''}
                  ${event.entity_id ? `
                    <span class="text-xs text-gray-400">#${escapeHtml(event.entity_id).substring(0, 8)}</span>
                  ` : ''}
                </div>

                <div class="flex items-center gap-3 text-xs text-gray-600 mb-2">
                  <span class="flex items-center gap-1">
                    <i class="bi bi-person"></i>
                    ${escapeHtml(event.user_email || 'System')}
                  </span>
                  <span class="flex items-center gap-1">
                    <i class="bi bi-clock"></i>
                    ${formatTimestamp(event.created_at)}
                  </span>
                  ${event.ip_address ? `
                    <span class="flex items-center gap-1">
                      <i class="bi bi-geo-alt"></i>
                      ${escapeHtml(event.ip_address)}
                    </span>
                  ` : ''}
                </div>

                ${event.details ? `
                  <p class="text-sm text-gray-700 line-clamp-2">${escapeHtml(truncate(event.details, 100))}</p>
                ` : ''}
              </div>

              <!-- Status Badge -->
              <span class="flex-shrink-0 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusColor}">
                ${event.status || 'unknown'}
              </span>
            </div>

            <!-- Changes Summary -->
            ${event.changes_before || event.changes_after ? `
              <div class="mt-2 flex items-center gap-2 text-xs">
                <span class="text-gray-500">
                  <i class="bi bi-arrow-left-right"></i>
                  Changes detected
                </span>
                <button
                  class="text-blue-600 hover:text-blue-700 font-medium"
                  onclick="event.stopPropagation(); window.viewAuditDetail('${event.id}')">
                  View details →
                </button>
              </div>
            ` : ''}
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function viewAuditDetail(id) {
  const event = auditEvents.find(e => e.id === id);
  if (!event) return;

  const modal = document.getElementById('audit-detail-modal');
  const content = document.getElementById('audit-detail-content');

  if (!modal || !content) return;

  // Build detail view
  content.innerHTML = `
    <div class="space-y-4">
      <!-- Event Info -->
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="text-xs font-medium text-gray-500 uppercase">Action</label>
          <p class="text-sm font-semibold text-gray-900 mt-1">${escapeHtml(event.action)}</p>
        </div>
        <div>
          <label class="text-xs font-medium text-gray-500 uppercase">Status</label>
          <p class="text-sm font-semibold text-gray-900 mt-1">${escapeHtml(event.status || 'unknown')}</p>
        </div>
        <div>
          <label class="text-xs font-medium text-gray-500 uppercase">User</label>
          <p class="text-sm text-gray-900 mt-1">${escapeHtml(event.user_email || 'System')}</p>
        </div>
        <div>
          <label class="text-xs font-medium text-gray-500 uppercase">Timestamp</label>
          <p class="text-sm text-gray-900 mt-1">${formatTimestamp(event.created_at)}</p>
        </div>
        ${event.entity_type ? `
          <div>
            <label class="text-xs font-medium text-gray-500 uppercase">Entity Type</label>
            <p class="text-sm text-gray-900 mt-1">${escapeHtml(event.entity_type)}</p>
          </div>
        ` : ''}
        ${event.entity_id ? `
          <div>
            <label class="text-xs font-medium text-gray-500 uppercase">Entity ID</label>
            <p class="text-sm font-mono text-gray-900 mt-1">${escapeHtml(event.entity_id)}</p>
          </div>
        ` : ''}
        ${event.ip_address ? `
          <div>
            <label class="text-xs font-medium text-gray-500 uppercase">IP Address</label>
            <p class="text-sm text-gray-900 mt-1">${escapeHtml(event.ip_address)}</p>
          </div>
        ` : ''}
        ${event.user_agent ? `
          <div class="col-span-2">
            <label class="text-xs font-medium text-gray-500 uppercase">User Agent</label>
            <p class="text-xs text-gray-700 mt-1 font-mono break-all">${escapeHtml(event.user_agent)}</p>
          </div>
        ` : ''}
      </div>

      ${event.details ? `
        <div>
          <label class="text-xs font-medium text-gray-500 uppercase">Details</label>
          <div class="mt-1 p-3 bg-gray-50 rounded-lg border border-gray-200">
            <p class="text-sm text-gray-900 whitespace-pre-wrap">${escapeHtml(event.details)}</p>
          </div>
        </div>
      ` : ''}

      <!-- Changes Comparison -->
      ${event.changes_before || event.changes_after ? `
        <div>
          <label class="text-xs font-medium text-gray-500 uppercase mb-2 block">Changes</label>
          <div class="grid grid-cols-2 gap-3">
            <!-- Before -->
            <div>
              <div class="text-xs font-medium text-red-600 mb-1 flex items-center gap-1">
                <i class="bi bi-dash-circle"></i>
                Before
              </div>
              <div class="p-3 bg-red-50 rounded-lg border border-red-200 max-h-48 overflow-y-auto">
                <pre class="text-xs text-gray-900 whitespace-pre-wrap font-mono">${escapeHtml(JSON.stringify(event.changes_before, null, 2) || 'N/A')}</pre>
              </div>
            </div>

            <!-- After -->
            <div>
              <div class="text-xs font-medium text-green-600 mb-1 flex items-center gap-1">
                <i class="bi bi-plus-circle"></i>
                After
              </div>
              <div class="p-3 bg-green-50 rounded-lg border border-green-200 max-h-48 overflow-y-auto">
                <pre class="text-xs text-gray-900 whitespace-pre-wrap font-mono">${escapeHtml(JSON.stringify(event.changes_after, null, 2) || 'N/A')}</pre>
              </div>
            </div>
          </div>
        </div>
      ` : ''}
    </div>
  `;

  modal.classList.remove('hidden');
}

function closeDetailModal() {
  document.getElementById('audit-detail-modal')?.classList.add('hidden');
}

function applyFilters() {
  currentPage = 1;
  loadAuditEvents();
}

function clearFilters() {
  document.getElementById('filter-action').value = '';
  document.getElementById('filter-entity-type').value = '';
  document.getElementById('filter-status').value = '';
  document.getElementById('filter-user').value = '';
  document.getElementById('filter-date-from').value = '';
  document.getElementById('filter-date-to').value = '';
  document.getElementById('filter-search').value = '';

  currentFilters = {};
  currentPage = 1;
  loadAuditEvents();
}

function changePage(delta) {
  const newPage = currentPage + delta;
  const maxPage = Math.ceil(totalEvents / pageSize);

  if (newPage < 1 || newPage > maxPage) return;

  currentPage = newPage;
  loadAuditEvents();
}

function updatePagination() {
  const pageStart = (currentPage - 1) * pageSize + 1;
  const pageEnd = Math.min(currentPage * pageSize, totalEvents);
  const maxPage = Math.ceil(totalEvents / pageSize);

  document.getElementById('page-start').textContent = totalEvents > 0 ? pageStart : 0;
  document.getElementById('page-end').textContent = pageEnd;
  document.getElementById('total-events').textContent = totalEvents;
  document.getElementById('page-info').textContent = `Page ${currentPage} of ${maxPage || 1}`;

  const btnPrev = document.getElementById('btn-prev-page');
  const btnNext = document.getElementById('btn-next-page');

  if (btnPrev) btnPrev.disabled = currentPage <= 1;
  if (btnNext) btnNext.disabled = currentPage >= maxPage;
}

function formatTimestamp(timestamp) {
  if (!timestamp) return 'N/A';

  try {
    const date = new Date(timestamp);
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

    // Less than 7 days
    if (diff < 604800000) {
      const days = Math.floor(diff / 86400000);
      return `${days} day${days > 1 ? 's' : ''} ago`;
    }

    // Full date
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (err) {
    return timestamp;
  }
}

function truncate(text, maxLength) {
  if (!text || text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Expose functions for inline onclick handlers
window.viewAuditDetail = viewAuditDetail;
