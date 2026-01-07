/**
 * Data Model Designer Page
 *
 * Manages database entities without writing code
 *
 * Pattern: Template-based (similar to builder-pages-list.js)
 * - HTML template loaded from /assets/templates/nocode-data-model.html
 * - This script listens for 'route:loaded' event
 * - Initializes Data Model Designer after template is in DOM
 */

import { authService } from './auth-service.js';

let dataModelPage = null;

// Route change
document.addEventListener('route:loaded', async (event) => {
  if (event.detail.route === 'nocode-data-model') {
    // Ensure DOM from template is ready
    setTimeout(async () => {
      if (!dataModelPage) {
        dataModelPage = new DataModelPage();
      }
      await dataModelPage.init();
    }, 0);
  }
});

document.addEventListener('route:before-change', (event) => {
  if (event.detail.from === 'nocode-data-model' && dataModelPage) {
    dataModelPage.cleanup();
    dataModelPage = null;
  }
});

export class DataModelPage {
  constructor() {
    this.entities = [];
    this.currentFilter = 'all'; // 'all', 'platform', 'tenant'
  }

  async init() {
    await this.loadEntities();
    this.initializeFilters();

    // Make methods available globally for onclick handlers
    window.DataModelApp = {
      showCreateModal: () => this.showCreateModal(),
      closeCreateModal: () => this.closeCreateModal(),
      createEntity: (event) => this.createEntity(event),
      viewEntity: (id) => this.viewEntity(id),
      closeViewModal: () => this.closeViewModal(),
      deleteEntity: (id) => this.deleteEntity(id),
      editEntity: (id) => this.editEntity(id),
      manageFields: (id) => this.manageFields(id),
      viewRelationships: (id) => this.viewRelationships(id),
      cloneEntity: (id) => this.cloneEntity(id),
      filterEntities: (filter) => this.filterEntities(filter)
    };
  }

  initializeFilters() {
    const filterContainer = document.querySelector('.filter-buttons');
    if (filterContainer) {
      filterContainer.innerHTML = `
        <div class="flex gap-2">
          <button onclick="DataModelApp.filterEntities('all')"
                  class="filter-btn px-4 py-2 rounded-lg font-medium transition ${this.currentFilter === 'all' ? 'bg-purple-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}"
                  data-filter="all">
            All
          </button>
          <button onclick="DataModelApp.filterEntities('platform')"
                  class="filter-btn px-4 py-2 rounded-lg font-medium transition ${this.currentFilter === 'platform' ? 'bg-purple-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}"
                  data-filter="platform">
            <i class="ph ph-planet"></i> Platform
          </button>
          <button onclick="DataModelApp.filterEntities('tenant')"
                  class="filter-btn px-4 py-2 rounded-lg font-medium transition ${this.currentFilter === 'tenant' ? 'bg-purple-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}"
                  data-filter="tenant">
            <i class="ph ph-building"></i> My Tenant
          </button>
        </div>
      `;
    }
  }

  filterEntities(filter) {
    this.currentFilter = filter;

    // Update button styles
    document.querySelectorAll('.filter-btn').forEach(btn => {
      btn.classList.remove('bg-purple-600', 'text-white');
      btn.classList.add('bg-gray-100', 'text-gray-700');
    });
    const activeBtn = document.querySelector(`[data-filter="${filter}"]`);
    if (activeBtn) {
      activeBtn.classList.remove('bg-gray-100', 'text-gray-700');
      activeBtn.classList.add('bg-purple-600', 'text-white');
    }

    this.renderEntities();
  }

  async loadEntities() {
    try {
      const token = authService.getToken();
      const response = await fetch('/api/v1/data-model/entities', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        this.entities = await response.json();
        this.renderEntities();
      } else {
        this.showError('Failed to load entities');
      }
    } catch (error) {
      console.error('Error loading entities:', error);
      this.showError('Error loading entities');
    }
  }

  renderEntities() {
    const container = document.getElementById('entities-list');
    if (!container) return;

    // Apply filter
    let filteredEntities = this.entities;
    if (this.currentFilter === 'platform') {
      filteredEntities = this.entities.filter(e => e.tenant_id === null);
    } else if (this.currentFilter === 'tenant') {
      filteredEntities = this.entities.filter(e => e.tenant_id !== null);
    }

    if (filteredEntities.length === 0) {
      const message = this.currentFilter === 'platform'
        ? 'No platform templates yet'
        : this.currentFilter === 'tenant'
        ? 'No tenant-specific entities yet'
        : 'No entities defined yet';

      container.innerHTML = `
        <div class="col-span-full text-center py-12">
          <i class="ph-duotone ph-database text-6xl text-gray-300"></i>
          <h3 class="mt-4 text-lg font-medium text-gray-900">${message}</h3>
          <p class="mt-2 text-gray-500">Create your first entity to get started</p>
          <button onclick="DataModelApp.showCreateModal()" class="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            <i class="ph ph-plus"></i> Create Entity
          </button>
        </div>
      `;
      return;
    }

    container.innerHTML = filteredEntities.map(entity => `
      <div class="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-lg transition">
        <div class="flex items-start justify-between mb-3">
          <div class="flex-1">
            <div class="flex items-center gap-2 mb-1">
              <h3 class="text-lg font-semibold text-gray-900">${this.escapeHtml(entity.label)}</h3>
              ${entity.tenant_id === null ? '<span class="px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs font-medium">Platform</span>' : ''}
            </div>
            <p class="text-sm text-gray-500 mt-1">${this.escapeHtml(entity.description || 'No description')}</p>
          </div>
          <span class="ml-2 px-3 py-1 rounded-full text-xs font-medium ${this.getStatusClass(entity.status)}">
            ${entity.status}
          </span>
        </div>

        <div class="space-y-2 text-sm text-gray-600 mb-4">
          <div class="flex items-center gap-2">
            <i class="ph ph-table"></i>
            <span>Table: ${entity.table_name}</span>
          </div>
          <div class="flex items-center gap-2">
            <i class="ph ph-tag"></i>
            <span>${entity.category || 'Uncategorized'}</span>
          </div>
          <div class="flex items-center gap-2">
            <i class="ph ph-list"></i>
            <span>${entity.field_count || 0} fields</span>
          </div>
          ${entity.is_audited ? `
            <div class="flex items-center gap-2">
              <i class="ph ph-check-circle text-green-600"></i>
              <span>Audit Enabled</span>
            </div>
          ` : ''}
        </div>

        <div class="flex gap-2">
          <button onclick="DataModelApp.viewEntity('${entity.id}')" class="flex-1 px-3 py-2 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 text-sm font-medium">
            <i class="ph ph-eye"></i> View
          </button>
          <button onclick="DataModelApp.manageFields('${entity.id}')" class="flex-1 px-3 py-2 bg-purple-50 text-purple-700 rounded-lg hover:bg-purple-100 text-sm font-medium">
            <i class="ph ph-list-bullets"></i> Fields
          </button>
          ${entity.tenant_id === null ? `
          <button onclick="DataModelApp.cloneEntity('${entity.id}')" class="px-3 py-2 bg-green-50 text-green-700 rounded-lg hover:bg-green-100 text-sm font-medium" title="Clone to my tenant">
            <i class="ph ph-copy"></i>
          </button>
          ` : ''}
          <button onclick="DataModelApp.deleteEntity('${entity.id}')" class="px-3 py-2 bg-red-50 text-red-700 rounded-lg hover:bg-red-100 text-sm">
            <i class="ph ph-trash"></i>
          </button>
        </div>
      </div>
    `).join('');
  }

  getStatusClass(status) {
    const classes = {
      'draft': 'bg-yellow-100 text-yellow-800',
      'active': 'bg-green-100 text-green-800',
      'published': 'bg-blue-100 text-blue-800'
    };
    return classes[status] || 'bg-gray-100 text-gray-800';
  }

  showCreateModal() {
    const modal = document.getElementById('createEntityModal');
    if (modal) modal.classList.remove('hidden');
  }

  closeCreateModal() {
    const modal = document.getElementById('createEntityModal');
    const form = document.getElementById('createEntityForm');
    if (modal) modal.classList.add('hidden');
    if (form) form.reset();
  }

  async createEntity(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const data = {
      name: formData.get('name'),
      label: formData.get('label'),
      plural_label: formData.get('plural_label') || '',
      description: formData.get('description') || '',
      table_name: formData.get('table_name'),
      category: formData.get('category') || '',
      is_audited: formData.get('is_audited') === 'on',
      supports_soft_delete: formData.get('supports_soft_delete') === 'on'
    };

    try {
      const response = await fetch('/api/v1/data-model/entities', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authService.getToken()}`
        },
        body: JSON.stringify(data)
      });

      if (response.ok) {
        this.closeCreateModal();
        await this.loadEntities();
        this.showSuccess('Entity created successfully');
      } else {
        const error = await response.json();
        this.showError(error.detail || 'Failed to create entity');
      }
    } catch (error) {
      console.error('Error creating entity:', error);
      this.showError('Error creating entity');
    }
  }

  async viewEntity(id) {
    try {
      const response = await fetch(`/api/v1/data-model/entities/${id}`, {
        headers: {
          'Authorization': `Bearer ${authService.getToken()}`
        }
      });

      if (response.ok) {
        const entity = await response.json();
        const title = document.getElementById('viewEntityTitle');
        const content = document.getElementById('viewEntityContent');

        if (title) title.textContent = entity.label;
        if (content) {
          content.innerHTML = `
            <div class="space-y-6">
              <div>
                <h4 class="font-semibold text-gray-900 mb-2">Basic Information</h4>
                <dl class="grid grid-cols-2 gap-4">
                  <div>
                    <dt class="text-sm text-gray-500">Name</dt>
                    <dd class="text-sm font-medium text-gray-900">${this.escapeHtml(entity.name)}</dd>
                  </div>
                  <div>
                    <dt class="text-sm text-gray-500">Table Name</dt>
                    <dd class="text-sm font-medium text-gray-900">${entity.table_name}</dd>
                  </div>
                  <div>
                    <dt class="text-sm text-gray-500">Category</dt>
                    <dd class="text-sm font-medium text-gray-900">${entity.category || 'N/A'}</dd>
                  </div>
                  <div>
                    <dt class="text-sm text-gray-500">Status</dt>
                    <dd class="text-sm font-medium text-gray-900">${entity.status}</dd>
                  </div>
                </dl>
              </div>

              <div>
                <h4 class="font-semibold text-gray-900 mb-2">Configuration</h4>
                <div class="grid grid-cols-2 gap-4">
                  <div class="flex items-center gap-2">
                    <i class="ph ph-${entity.is_audited ? 'check-circle text-green-600' : 'x-circle text-gray-400'}"></i>
                    <span class="text-sm">Audit Trail ${entity.is_audited ? 'Enabled' : 'Disabled'}</span>
                  </div>
                  <div class="flex items-center gap-2">
                    <i class="ph ph-${entity.supports_soft_delete ? 'check-circle text-green-600' : 'x-circle text-gray-400'}"></i>
                    <span class="text-sm">Soft Delete ${entity.supports_soft_delete ? 'Enabled' : 'Disabled'}</span>
                  </div>
                  <div class="flex items-center gap-2">
                    <i class="ph ph-${entity.supports_attachments ? 'check-circle text-green-600' : 'x-circle text-gray-400'}"></i>
                    <span class="text-sm">Attachments ${entity.supports_attachments ? 'Enabled' : 'Disabled'}</span>
                  </div>
                  <div class="flex items-center gap-2">
                    <i class="ph ph-${entity.is_versioned ? 'check-circle text-green-600' : 'x-circle text-gray-400'}"></i>
                    <span class="text-sm">Versioning ${entity.is_versioned ? 'Enabled' : 'Disabled'}</span>
                  </div>
                </div>
              </div>

              ${entity.description ? `
                <div>
                  <h4 class="font-semibold text-gray-900 mb-2">Description</h4>
                  <p class="text-sm text-gray-600">${this.escapeHtml(entity.description)}</p>
                </div>
              ` : ''}

              <div class="flex gap-3 pt-4 border-t">
                <button onclick="DataModelApp.editEntity('${entity.id}')" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                  <i class="ph ph-pencil"></i> Edit Entity
                </button>
                <button onclick="DataModelApp.manageFields('${entity.id}')" class="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700">
                  <i class="ph ph-list-bullets"></i> Manage Fields
                </button>
                <button onclick="DataModelApp.viewRelationships('${entity.id}')" class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
                  <i class="ph ph-arrows-merge"></i> Relationships
                </button>
              </div>
            </div>
          `;
        }

        const modal = document.getElementById('viewEntityModal');
        if (modal) modal.classList.remove('hidden');
      }
    } catch (error) {
      console.error('Error loading entity:', error);
      this.showError('Error loading entity details');
    }
  }

  closeViewModal() {
    const modal = document.getElementById('viewEntityModal');
    if (modal) modal.classList.add('hidden');
  }

  async deleteEntity(id) {
    if (!confirm('Are you sure you want to delete this entity?')) return;

    try {
      const response = await fetch(`/api/v1/data-model/entities/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${authService.getToken()}`
        }
      });

      if (response.ok) {
        await this.loadEntities();
        this.showSuccess('Entity deleted successfully');
      } else {
        this.showError('Failed to delete entity');
      }
    } catch (error) {
      console.error('Error deleting entity:', error);
      this.showError('Error deleting entity');
    }
  }

  async cloneEntity(id) {
    const entity = this.entities.find(e => e.id === id);
    if (!entity) return;

    const newName = prompt('Enter a name for the cloned entity:', `${entity.name}_copy`);
    if (!newName) return;

    const newLabel = prompt('Enter a label for the cloned entity:', `${entity.label} (Copy)`);
    if (!newLabel) return;

    try {
      const response = await fetch(`/api/v1/data-model/entities/${id}/clone?new_name=${encodeURIComponent(newName)}&new_label=${encodeURIComponent(newLabel)}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authService.getToken()}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        await this.loadEntities();
        this.showSuccess(`Platform template cloned successfully as "${newLabel}"`);
      } else {
        const error = await response.json();
        this.showError(error.detail || 'Failed to clone entity');
      }
    } catch (error) {
      console.error('Error cloning entity:', error);
      this.showError('Error cloning entity');
    }
  }

  editEntity(id) {
    this.showError('Edit feature coming soon - will open entity editor');
  }

  manageFields(id) {
    this.showError('Field management UI coming soon');
  }

  viewRelationships(id) {
    this.showError('Relationship viewer coming soon');
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  showSuccess(message) {
    if (window.showNotification) {
      window.showNotification(message, 'success');
    } else {
      alert(message);
    }
  }

  showError(message) {
    if (window.showNotification) {
      window.showNotification(message, 'error');
    } else {
      alert(message);
    }
  }

  cleanup() {
    delete window.DataModelApp;
  }
}
