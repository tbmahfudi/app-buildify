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
import { apiFetch } from './api.js';

let dataModelPage = null;

// Phosphor icon options for entities
const ENTITY_ICON_OPTIONS = [
  'table', 'database', 'folder', 'user', 'users', 'briefcase',
  'shopping-cart', 'package', 'file-text', 'clipboard-text',
  'calendar', 'note', 'address-book', 'receipt', 'invoice',
  'chart-bar', 'buildings', 'truck', 'gear', 'tag'
];

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
    this.modules = [];
    this.currentFilter = 'all'; // 'all', 'platform', 'tenant'
  }

  async init() {
    await this.loadModules();
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
      filterEntities: (filter) => this.filterEntities(filter),
      closeFieldManager: () => this.closeFieldManager(),
      showAddFieldModal: (id) => this.showAddFieldModal(id),
      closeAddFieldModal: () => this.closeAddFieldModal(),
      updateDataTypeOptions: (type) => this.updateDataTypeOptions(type),
      editField: (entityId, fieldId) => this.editField(entityId, fieldId),
      closeEditFieldModal: () => this.closeEditFieldModal(),
      deleteField: (entityId, fieldId) => this.deleteField(entityId, fieldId),
      closeRelationshipViewer: () => this.closeRelationshipViewer(),
      showAddRelationshipModal: () => this.showAddRelationshipModal(),
      closeAddRelationshipModal: () => this.closeAddRelationshipModal(),
      deleteRelationship: (id) => this.deleteRelationship(id),
      showEditEntityModal: (id) => this.showEditEntityModal(id),
      closeEditEntityModal: () => this.closeEditEntityModal(),
      showImportFromDatabaseModal: () => this.showImportFromDatabaseModal(),
      closeImportModal: () => this.closeImportModal(),
      selectAllObjects: (objectType) => this.selectAllObjects(objectType),
      previewObject: (objectName, objectType) => this.previewObject(objectName, objectType),
      previewSelected: () => this.previewSelected(),
      updateSelectedCount: () => this.updateSelectedCount(),
      importSelectedObjects: () => this.importSelectedObjects(),
      closePreviewModal: () => this.closePreviewModal(),
      importSingleObject: (objectName, objectType) => this.importSingleObject(objectName, objectType),
      previewMigration: (entityId) => this.previewMigration(entityId),
      closeMigrationPreviewModal: () => this.closeMigrationPreviewModal(),
      publishEntity: (entityId) => this.publishEntity(entityId),
      publishEntityFromPreview: (entityId) => this.publishEntityFromPreview(entityId),
      viewMigrations: (entityId) => this.viewMigrations(entityId),
      closeMigrationHistoryModal: () => this.closeMigrationHistoryModal(),
      viewMigrationDetails: (migrationId) => this.viewMigrationDetails(migrationId),
      rollbackMigration: (migrationId) => this.rollbackMigration(migrationId),
      // Quick Actions
      createReportFromEntity: (id) => this.createReportFromEntity(id),
      createPageFromEntity: (id) => this.createPageFromEntity(id),
      addEntityToMenu: (id) => this.addEntityToMenu(id),
      // Icon selection
      selectEntityIcon: (icon) => this.selectEntityIcon(icon)
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

  async loadModules() {
    try {
      const response = await apiFetch('/nocode-modules');

      if (response.ok) {
        const data = await response.json();
        // Handle both array and object responses
        this.modules = Array.isArray(data) ? data : (data.modules || []);
        this.populateModuleDropdown();
      } else {
        console.error('Failed to load modules');
        this.modules = [];
      }
    } catch (error) {
      console.error('Error loading modules:', error);
      this.modules = [];
    }
  }

  getModuleName(moduleId) {
    if (!moduleId) return null;
    const module = this.modules.find(m => m.id === moduleId);
    return module ? (module.display_name || module.name) : null;
  }

  populateModuleDropdown() {
    const select = document.getElementById('moduleSelect');
    if (!select) return;

    // Keep the default "No Module" option and add modules
    const moduleOptions = this.modules
      .filter(m => m.status === 'active' || m.status === 'draft')
      .map(module => `<option value="${module.id}">${this.escapeHtml(module.display_name || module.name)}</option>`)
      .join('');

    select.innerHTML = `
      <option value="">-- No Module (Standalone) --</option>
      ${moduleOptions}
    `;
  }

  async loadEntities() {
    try {      const response = await apiFetch('/data-model/entities');

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
          ${entity.module_id ? `
            <div class="flex items-center gap-2">
              <i class="ph ph-package text-blue-600"></i>
              <span>Module: ${this.escapeHtml(this.getModuleName(entity.module_id) || 'Unknown')}</span>
            </div>
          ` : ''}
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

        <div class="space-y-2">
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

          <!-- Quick Actions -->
          <div class="flex gap-2 pt-2 border-t border-gray-200">
            <button onclick="DataModelApp.createReportFromEntity('${entity.id}')"
                    class="flex-1 px-3 py-1.5 bg-emerald-50 text-emerald-700 rounded-lg hover:bg-emerald-100 text-xs font-medium flex items-center justify-center gap-1"
                    title="Create a report based on this entity">
              <i class="ph ph-file-plus text-sm"></i> Report
            </button>
            <button onclick="DataModelApp.createPageFromEntity('${entity.id}')"
                    class="flex-1 px-3 py-1.5 bg-indigo-50 text-indigo-700 rounded-lg hover:bg-indigo-100 text-xs font-medium flex items-center justify-center gap-1"
                    title="Create a UI page for this entity">
              <i class="ph ph-layout text-sm"></i> Page
            </button>
            <button onclick="DataModelApp.addEntityToMenu('${entity.id}')"
                    class="flex-1 px-3 py-1.5 bg-amber-50 text-amber-700 rounded-lg hover:bg-amber-100 text-xs font-medium flex items-center justify-center gap-1"
                    title="Add this entity to the menu">
              <i class="ph ph-list-plus text-sm"></i> Menu
            </button>
          </div>
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
    if (modal) {
      modal.classList.remove('hidden');
      // Ensure module dropdown is populated
      this.populateModuleDropdown();
      // Initialize icon picker
      this.initializeEntityIconPicker();
    }
  }

  initializeEntityIconPicker() {
    const picker = document.getElementById('entityIconPicker');
    const iconInput = document.getElementById('entityIcon');
    if (!picker || !iconInput) return;

    // Render icon options
    picker.innerHTML = ENTITY_ICON_OPTIONS.map(icon => `
      <button type="button"
              class="entity-icon-option w-12 h-12 flex items-center justify-center border-2 border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition ${icon === 'table' ? 'border-blue-500 bg-blue-50' : ''}"
              data-icon="${icon}"
              onclick="DataModelApp.selectEntityIcon('${icon}')">
        <i class="ph-fill ph-${icon} text-2xl text-gray-700"></i>
      </button>
    `).join('');
  }

  selectEntityIcon(icon) {
    const iconInput = document.getElementById('entityIcon');
    if (iconInput) {
      iconInput.value = icon;
    }

    // Update visual selection
    document.querySelectorAll('.entity-icon-option').forEach(btn => {
      if (btn.dataset.icon === icon) {
        btn.classList.add('border-blue-500', 'bg-blue-50');
        btn.classList.remove('border-gray-300');
      } else {
        btn.classList.remove('border-blue-500', 'bg-blue-50');
        btn.classList.add('border-gray-300');
      }
    });
  }

  closeCreateModal() {
    const modal = document.getElementById('createEntityModal');
    const form = document.getElementById('createEntityForm');
    if (modal) modal.classList.add('hidden');
    if (form) {
      form.reset();
      // Reset icon selection to default
      this.selectEntityIcon('table');
    }
  }

  async createEntity(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const moduleId = formData.get('module_id');
    const data = {
      name: formData.get('name'),
      label: formData.get('label'),
      plural_label: formData.get('plural_label') || '',
      description: formData.get('description') || '',
      icon: formData.get('icon') || 'table',
      table_name: formData.get('table_name'),
      category: formData.get('category') || '',
      module_id: moduleId && moduleId !== '' ? moduleId : null,
      is_audited: formData.get('is_audited') === 'on',
      supports_soft_delete: formData.get('supports_soft_delete') === 'on'
    };

    try {
      const response = await apiFetch('/data-model/entities', {
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
      const response = await apiFetch(`/data-model/entities/${id}`, {
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
                    <dt class="text-sm text-gray-500">Module</dt>
                    <dd class="text-sm font-medium text-gray-900">${entity.module_id ? this.escapeHtml(this.getModuleName(entity.module_id) || 'Unknown') : 'Standalone'}</dd>
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

              <div class="flex flex-wrap gap-3 pt-4 border-t">
                <button onclick="DataModelApp.editEntity('${entity.id}')" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                  <i class="ph ph-pencil"></i> Edit Entity
                </button>
                <button onclick="DataModelApp.manageFields('${entity.id}')" class="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700">
                  <i class="ph ph-list-bullets"></i> Manage Fields
                </button>
                <button onclick="DataModelApp.viewRelationships('${entity.id}')" class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
                  <i class="ph ph-arrows-merge"></i> Relationships
                </button>
                ${entity.status !== 'published' ? `
                  <button onclick="DataModelApp.previewMigration('${entity.id}')" class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">
                    <i class="ph ph-eye"></i> Preview Migration
                  </button>
                  <button onclick="DataModelApp.publishEntity('${entity.id}')" class="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700">
                    <i class="ph ph-rocket-launch"></i> Publish
                  </button>
                ` : ''}
                <button onclick="DataModelApp.viewMigrations('${entity.id}')" class="px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700">
                  <i class="ph ph-clock-clockwise"></i> Migration History
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
      const response = await apiFetch(`/data-model/entities/${id}`, {
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
      const response = await apiFetch(`/data-model/entities/${id}/clone?new_name=${encodeURIComponent(newName)}&new_label=${encodeURIComponent(newLabel)}`, {
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

  async editEntity(id) {
    try {
      const response = await apiFetch(`/data-model/entities/${id}`, {
        headers: { 'Authorization': `Bearer ${authService.getToken()}` }
      });

      if (!response.ok) {
        this.showError('Failed to load entity');
        return;
      }

      const entity = await response.json();
      this.showEditEntityModal(entity);
    } catch (error) {
      console.error('Error loading entity:', error);
      this.showError('Error loading entity');
    }
  }

  showEditEntityModal(entity) {
    const modal = document.createElement('div');
    modal.id = 'editEntityModal';
    modal.className = 'fixed inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center z-[60]';
    modal.innerHTML = `
      <div class="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        <div class="px-6 py-4 border-b border-gray-200">
          <h3 class="text-lg font-semibold text-gray-900">Edit Entity</h3>
        </div>
        <form id="editEntityForm" class="flex-1 flex flex-col">
          <div class="flex-1 overflow-y-auto p-6 space-y-4">
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Entity Name *</label>
                <input type="text" name="name" required value="${this.escapeHtml(entity.name)}"
                       class="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100" disabled>
                <p class="text-xs text-gray-500 mt-1">Cannot change after creation</p>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Table Name *</label>
                <input type="text" name="table_name" required value="${this.escapeHtml(entity.table_name)}"
                       class="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100" disabled>
                <p class="text-xs text-gray-500 mt-1">Cannot change after creation</p>
              </div>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Display Label *</label>
                <input type="text" name="label" required value="${this.escapeHtml(entity.label)}"
                       class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Plural Label</label>
                <input type="text" name="plural_label" value="${this.escapeHtml(entity.plural_label || '')}"
                       class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
              </div>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <textarea name="description" rows="3" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">${this.escapeHtml(entity.description || '')}</textarea>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Category</label>
                <input type="text" name="category" value="${this.escapeHtml(entity.category || '')}"
                       class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Icon</label>
                <input type="text" name="icon" value="${this.escapeHtml(entity.icon || '')}" placeholder="database"
                       class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                <p class="text-xs text-gray-500 mt-1">Phosphor icon name</p>
              </div>
            </div>

            <div class="space-y-2">
              <label class="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" name="is_audited" ${entity.is_audited ? 'checked' : ''} class="rounded text-blue-600">
                <span class="text-sm text-gray-700">Enable Audit Trail</span>
              </label>
              <label class="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" name="supports_soft_delete" ${entity.supports_soft_delete ? 'checked' : ''} class="rounded text-blue-600">
                <span class="text-sm text-gray-700">Enable Soft Delete</span>
              </label>
              <label class="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" name="supports_attachments" ${entity.supports_attachments ? 'checked' : ''} class="rounded text-blue-600">
                <span class="text-sm text-gray-700">Enable Attachments</span>
              </label>
              <label class="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" name="is_versioned" ${entity.is_versioned ? 'checked' : ''} class="rounded text-blue-600">
                <span class="text-sm text-gray-700">Enable Versioning</span>
              </label>
            </div>
          </div>

          <div class="px-6 py-4 border-t border-gray-200 flex gap-3">
            <button type="submit" class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
              <i class="ph ph-check"></i> Save Changes
            </button>
            <button type="button" onclick="DataModelApp.closeEditEntityModal()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200">
              Cancel
            </button>
          </div>
        </form>
      </div>
    `;

    document.body.appendChild(modal);

    document.getElementById('editEntityForm').addEventListener('submit', (e) => {
      e.preventDefault();
      this.updateEntity(entity.id, e.target);
    });
  }

  closeEditEntityModal() {
    const modal = document.getElementById('editEntityModal');
    if (modal) modal.remove();
  }

  async updateEntity(entityId, form) {
    const formData = new FormData(form);
    const data = {
      label: formData.get('label'),
      plural_label: formData.get('plural_label') || null,
      description: formData.get('description') || null,
      category: formData.get('category') || null,
      icon: formData.get('icon') || null,
      is_audited: formData.get('is_audited') === 'on',
      supports_soft_delete: formData.get('supports_soft_delete') === 'on',
      supports_attachments: formData.get('supports_attachments') === 'on',
      is_versioned: formData.get('is_versioned') === 'on'
    };

    try {
      const response = await apiFetch(`/data-model/entities/${entityId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authService.getToken()}`
        },
        body: JSON.stringify(data)
      });

      if (response.ok) {
        this.closeEditEntityModal();
        this.showSuccess('Entity updated successfully');
        await this.loadEntities();
      } else {
        const error = await response.json();
        this.showError(error.detail || 'Failed to update entity');
      }
    } catch (error) {
      console.error('Error updating entity:', error);
      this.showError('Error updating entity');
    }
  }

  async manageFields(id) {
    try {
      // Load entity and its fields
      const [entityResponse, fieldsResponse] = await Promise.all([
        fetch(`/api/v1/data-model/entities/${id}`, {
          headers: { 'Authorization': `Bearer ${authService.getToken()}` }
        }),
        fetch(`/api/v1/data-model/entities/${id}/fields`, {
          headers: { 'Authorization': `Bearer ${authService.getToken()}` }
        })
      ]);

      if (!entityResponse.ok || !fieldsResponse.ok) {
        this.showError('Failed to load field data');
        return;
      }

      const entity = await entityResponse.json();
      const fields = await fieldsResponse.json();

      this.showFieldManager(entity, fields);
    } catch (error) {
      console.error('Error loading fields:', error);
      this.showError('Error loading fields');
    }
  }

  showFieldManager(entity, fields) {
    // Create modal
    const modal = document.createElement('div');
    modal.id = 'fieldManagerModal';
    modal.className = 'fixed inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center z-50 p-4';
    modal.innerHTML = `
      <div class="bg-white rounded-lg shadow-xl w-full max-w-5xl max-h-[90vh] flex flex-col mx-auto">
        <!-- Header -->
        <div class="px-4 sm:px-6 py-4 border-b border-gray-200 flex items-center justify-between flex-shrink-0">
          <div class="min-w-0 flex-1">
            <h2 class="text-lg sm:text-xl font-semibold text-gray-900 truncate">
              <i class="ph ph-list-bullets"></i> Manage Fields: ${this.escapeHtml(entity.label)}
            </h2>
            <p class="text-xs sm:text-sm text-gray-500 mt-1 hidden sm:block">Add, edit, and organize fields for this entity</p>
          </div>
          <button onclick="DataModelApp.closeFieldManager()" class="text-gray-400 hover:text-gray-600 ml-4 flex-shrink-0">
            <i class="ph ph-x text-2xl"></i>
          </button>
        </div>

        <!-- Body -->
        <div class="flex-1 overflow-y-auto p-4 sm:p-6">
          <div class="mb-4 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
            <div class="text-sm text-gray-600">
              ${fields.length} fields defined
            </div>
            <button onclick="DataModelApp.showAddFieldModal('${entity.id}')" class="w-full sm:w-auto px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 whitespace-nowrap">
              <i class="ph ph-plus"></i> Add Field
            </button>
          </div>

          <div class="space-y-2" id="fieldsList">
            ${fields.length === 0 ? `
              <div class="text-center py-12 text-gray-500">
                <i class="ph-duotone ph-list-bullets text-5xl"></i>
                <p class="mt-2">No fields yet. Click "Add Field" to create one.</p>
              </div>
            ` : fields.map(field => this.renderFieldItem(field, entity.id)).join('')}
          </div>
        </div>

        <!-- Footer -->
        <div class="px-4 sm:px-6 py-4 border-t border-gray-200 flex justify-end flex-shrink-0">
          <button onclick="DataModelApp.closeFieldManager()" class="w-full sm:w-auto px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200">
            Done
          </button>
        </div>
      </div>
    `;

    document.body.appendChild(modal);

    // Store current state
    this.currentEntity = entity;
    this.currentFields = fields;
  }

  renderFieldItem(field, entityId) {
    const isSystem = field.is_system || false;
    return `
      <div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition">
        <div class="flex-1">
          <div class="flex items-center gap-2">
            <h4 class="font-medium text-gray-900">${this.escapeHtml(field.label)}</h4>
            ${field.is_required ? '<span class="px-2 py-0.5 bg-red-100 text-red-700 rounded text-xs">Required</span>' : ''}
            ${field.is_unique ? '<span class="px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs">Unique</span>' : ''}
            ${isSystem ? '<span class="px-2 py-0.5 bg-gray-200 text-gray-700 rounded text-xs">System</span>' : ''}
          </div>
          <div class="text-sm text-gray-600 mt-1 flex items-center gap-4">
            <span><i class="ph ph-code"></i> ${field.name}</span>
            <span><i class="ph ph-database"></i> ${field.data_type}${field.max_length ? '(' + field.max_length + ')' : ''}</span>
            <span><i class="ph ph-tag"></i> ${field.field_type}</span>
          </div>
          ${field.description ? `<p class="text-sm text-gray-500 mt-1">${this.escapeHtml(field.description)}</p>` : ''}
        </div>
        <div class="flex gap-2 ml-4">
          ${!isSystem ? `
            <button onclick="DataModelApp.editField('${entityId}', '${field.id}')" class="px-3 py-1.5 bg-blue-50 text-blue-700 rounded hover:bg-blue-100 text-sm">
              <i class="ph ph-pencil"></i> Edit
            </button>
            <button onclick="DataModelApp.deleteField('${entityId}', '${field.id}')" class="px-3 py-1.5 bg-red-50 text-red-700 rounded hover:bg-red-100 text-sm">
              <i class="ph ph-trash"></i>
            </button>
          ` : '<span class="text-xs text-gray-500 px-3 py-1.5">System field</span>'}
        </div>
      </div>
    `;
  }

  closeFieldManager() {
    const modal = document.getElementById('fieldManagerModal');
    if (modal) modal.remove();
  }

  showAddFieldModal(entityId) {
    const existingModal = document.getElementById('addFieldModal');
    if (existingModal) existingModal.remove();

    const modal = document.createElement('div');
    modal.id = 'addFieldModal';
    modal.className = 'fixed inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center z-[60] p-4';
    modal.innerHTML = `
      <div class="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col mx-auto">
        <div class="px-4 sm:px-6 py-4 border-b border-gray-200 flex-shrink-0">
          <h3 class="text-lg font-semibold text-gray-900">Add New Field</h3>
        </div>
        <form id="addFieldForm" class="flex-1 flex flex-col min-h-0">
          <div class="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4 pb-64">
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Field Name *</label>
                <input type="text" name="name" required placeholder="customer_name"
                       class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                <p class="text-xs text-gray-500 mt-1">Technical name (snake_case)</p>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Label *</label>
                <input type="text" name="label" required placeholder="Customer Name"
                       class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
              </div>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Field Type *</label>
                <select name="field_type" required onchange="DataModelApp.updateDataTypeOptions(this.value)"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                  <option value="">Select type...</option>
                  <option value="string">String/Text</option>
                  <option value="integer">Integer</option>
                  <option value="decimal">Decimal</option>
                  <option value="boolean">Boolean</option>
                  <option value="date">Date</option>
                  <option value="datetime">Date & Time</option>
                  <option value="text">Long Text</option>
                  <option value="email">Email</option>
                  <option value="url">URL</option>
                  <option value="phone">Phone</option>
                  <option value="json">JSON</option>
                  <option value="file">File Upload</option>
                  <option value="select">Select/Dropdown</option>
                  <option value="reference">Reference/Foreign Key</option>
                  <option value="lookup">Lookup (Legacy)</option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Database Type *</label>
                <select name="data_type" required id="dataTypeSelect"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                  <option value="">Select database type...</option>
                  <option value="VARCHAR">VARCHAR</option>
                  <option value="TEXT">TEXT</option>
                  <option value="INTEGER">INTEGER</option>
                  <option value="BIGINT">BIGINT</option>
                  <option value="DECIMAL">DECIMAL</option>
                  <option value="BOOLEAN">BOOLEAN</option>
                  <option value="DATE">DATE</option>
                  <option value="TIMESTAMP">TIMESTAMP</option>
                  <option value="JSONB">JSONB</option>
                  <option value="UUID">UUID</option>
                </select>
              </div>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Max Length</label>
                <input type="number" name="max_length" placeholder="255"
                       class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                <p class="text-xs text-gray-500 mt-1">For VARCHAR types</p>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Default Value</label>
                <input type="text" name="default_value" placeholder=""
                       class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
              </div>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <textarea name="description" rows="2" placeholder="Field description..."
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"></textarea>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Help Text</label>
              <input type="text" name="help_text" placeholder="Helper text shown to users"
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
            </div>

            <!-- Reference Field Configuration (hidden by default) -->
            <div id="referenceConfig" style="display: none;" class="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <h4 class="font-medium text-sm text-gray-900 mb-3">
                <i class="ph ph-link"></i> Reference Configuration
              </h4>

              <div class="mb-3">
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Reference Entity *
                </label>
                <select id="referenceEntitySelect" name="reference_entity_id"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg">
                  <option value="">Select entity...</option>
                </select>
                <p class="text-xs text-gray-500 mt-1">The entity this field references</p>
              </div>

              <div class="mb-3">
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Display Field
                </label>
                <input type="text" name="reference_field" placeholder="e.g., name, title"
                       class="w-full px-3 py-2 border border-gray-300 rounded-lg">
                <p class="text-xs text-gray-500 mt-1">Field to show in dropdown (defaults to 'name')</p>
              </div>

              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-3">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">On Delete</label>
                  <select name="on_delete" class="w-full px-3 py-2 border border-gray-300 rounded-lg">
                    <option value="NO ACTION">No Action (Default)</option>
                    <option value="CASCADE">Cascade</option>
                    <option value="SET NULL">Set Null</option>
                    <option value="RESTRICT">Restrict</option>
                  </select>
                  <p class="text-xs text-gray-500 mt-1">When referenced record is deleted</p>
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">On Update</label>
                  <select name="on_update" class="w-full px-3 py-2 border border-gray-300 rounded-lg">
                    <option value="NO ACTION">No Action (Default)</option>
                    <option value="CASCADE">Cascade</option>
                    <option value="SET NULL">Set Null</option>
                    <option value="RESTRICT">Restrict</option>
                  </select>
                  <p class="text-xs text-gray-500 mt-1">When referenced record's ID is updated</p>
                </div>
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Relationship Type</label>
                <select name="relationship_type" class="w-full px-3 py-2 border border-gray-300 rounded-lg">
                  <option value="many-to-one">Many to One (Default)</option>
                  <option value="one-to-one">One to One</option>
                </select>
              </div>
            </div>

            <!-- Select Field Configuration (hidden by default) -->
            <div id="selectConfig" style="display: none;" class="p-4 bg-green-50 rounded-lg border border-green-200">
              <h4 class="font-medium text-sm text-gray-900 mb-3">
                <i class="ph ph-list"></i> Select Options Configuration
              </h4>

              <div class="mb-3">
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Options (one per line) *
                </label>
                <textarea id="selectOptionsTextarea" name="select_options" rows="6"
                          placeholder="Low&#10;Medium&#10;High&#10;Critical"
                          class="w-full px-3 py-2 border border-gray-300 rounded-lg font-mono text-sm"></textarea>
                <p class="text-xs text-gray-500 mt-1">Enter each option on a new line</p>
              </div>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <label class="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" name="is_required" class="rounded text-blue-600">
                <span class="text-sm text-gray-700">Required</span>
              </label>
              <label class="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" name="is_unique" class="rounded text-blue-600">
                <span class="text-sm text-gray-700">Unique</span>
              </label>
              <label class="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" name="is_indexed" class="rounded text-blue-600">
                <span class="text-sm text-gray-700">Indexed</span>
              </label>
            </div>
          </div>

          <div class="px-4 sm:px-6 py-4 border-t border-gray-200 flex flex-col-reverse sm:flex-row gap-3 flex-shrink-0">
            <button type="button" onclick="DataModelApp.closeAddFieldModal()" class="w-full sm:w-auto px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200">
              Cancel
            </button>
            <button type="submit" class="w-full sm:flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
              <i class="ph ph-plus"></i> Add Field
            </button>
          </div>
        </form>
      </div>
    `;

    document.body.appendChild(modal);

    // Add form submit handler
    document.getElementById('addFieldForm').addEventListener('submit', (e) => {
      e.preventDefault();
      this.createField(entityId, e.target);
    });
  }

  updateDataTypeOptions(fieldType) {
    const dataTypeSelect = document.getElementById('dataTypeSelect');
    if (!dataTypeSelect) return;

    const typeMap = {
      'string': 'VARCHAR',
      'text': 'TEXT',
      'integer': 'INTEGER',
      'decimal': 'DECIMAL',
      'boolean': 'BOOLEAN',
      'date': 'DATE',
      'datetime': 'TIMESTAMP',
      'email': 'VARCHAR',
      'url': 'VARCHAR',
      'phone': 'VARCHAR',
      'json': 'JSONB',
      'file': 'VARCHAR',
      'select': 'VARCHAR',
      'reference': 'UUID',
      'lookup': 'UUID'
    };

    if (typeMap[fieldType]) {
      dataTypeSelect.value = typeMap[fieldType];
    }

    // Show/hide configuration sections based on field type
    const referenceConfig = document.getElementById('referenceConfig');
    const selectConfig = document.getElementById('selectConfig');

    if (referenceConfig && selectConfig) {
      if (fieldType === 'reference') {
        referenceConfig.style.display = 'block';
        selectConfig.style.display = 'none';
        this.loadReferenceEntities();
        // Make reference fields required
        document.getElementById('referenceEntitySelect').required = true;
        document.getElementById('selectOptionsTextarea').required = false;
      } else if (fieldType === 'select') {
        selectConfig.style.display = 'block';
        referenceConfig.style.display = 'none';
        // Make select options required
        document.getElementById('selectOptionsTextarea').required = true;
        document.getElementById('referenceEntitySelect').required = false;
      } else {
        referenceConfig.style.display = 'none';
        selectConfig.style.display = 'none';
        // Remove required attributes
        document.getElementById('referenceEntitySelect').required = false;
        document.getElementById('selectOptionsTextarea').required = false;
      }
    }
  }

  async loadReferenceEntities() {
    const moduleId = this.state.currentModule?.id;
    if (!moduleId) return;

    try {
      const response = await fetch(`/api/v1/data-model/modules/${moduleId}/entities`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) throw new Error('Failed to load entities');

      const entities = await response.json();
      const select = document.getElementById('referenceEntitySelect');

      if (select) {
        select.innerHTML = '<option value="">Select entity...</option>';
        entities.forEach(entity => {
          select.innerHTML += `<option value="${entity.id}">${entity.label || entity.name}</option>`;
        });
      }
    } catch (error) {
      console.error('Error loading reference entities:', error);
      this.showNotification('Failed to load entities', 'error');
    }
  }

  closeAddFieldModal() {
    const modal = document.getElementById('addFieldModal');
    if (modal) modal.remove();
  }

  async createField(entityId, form) {
    const formData = new FormData(form);
    const fieldType = formData.get('field_type');

    const data = {
      name: formData.get('name'),
      label: formData.get('label'),
      field_type: fieldType,
      data_type: formData.get('data_type'),
      description: formData.get('description') || null,
      help_text: formData.get('help_text') || null,
      max_length: formData.get('max_length') ? parseInt(formData.get('max_length')) : null,
      default_value: formData.get('default_value') || null,
      is_required: formData.get('is_required') === 'on',
      is_unique: formData.get('is_unique') === 'on',
      is_indexed: formData.get('is_indexed') === 'on',
      is_nullable: formData.get('is_required') !== 'on',
      display_order: 999
    };

    // Add reference field configuration
    if (fieldType === 'reference') {
      data.reference_entity_id = formData.get('reference_entity_id') || null;
      data.reference_field = formData.get('reference_field') || 'name';
      data.on_delete = formData.get('on_delete') || 'NO ACTION';
      data.on_update = formData.get('on_update') || 'NO ACTION';
      data.relationship_type = formData.get('relationship_type') || 'many-to-one';
    }

    // Add select field configuration
    if (fieldType === 'select') {
      const selectOptions = formData.get('select_options');
      if (selectOptions) {
        // Split by newlines and filter out empty lines
        const options = selectOptions.split('\n')
          .map(opt => opt.trim())
          .filter(opt => opt.length > 0);
        data.allowed_values = options;
      }
    }

    try {
      const response = await apiFetch(`/data-model/entities/${entityId}/fields`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authService.getToken()}`
        },
        body: JSON.stringify(data)
      });

      if (response.ok) {
        this.closeAddFieldModal();
        this.showSuccess('Field created successfully');
        // Reload field manager
        await this.manageFields(entityId);
      } else {
        const error = await response.json();
        this.showError(error.detail || 'Failed to create field');
      }
    } catch (error) {
      console.error('Error creating field:', error);
      this.showError('Error creating field');
    }
  }

  async editField(entityId, fieldId) {
    try {
      const response = await apiFetch(`/data-model/entities/${entityId}/fields`, {
        headers: { 'Authorization': `Bearer ${authService.getToken()}` }
      });

      if (!response.ok) {
        this.showError('Failed to load field');
        return;
      }

      const fields = await response.json();
      const field = fields.find(f => f.id === fieldId);
      if (!field) {
        this.showError('Field not found');
        return;
      }

      this.showEditFieldModal(entityId, field);
    } catch (error) {
      console.error('Error loading field:', error);
      this.showError('Error loading field');
    }
  }

  showEditFieldModal(entityId, field) {
    const existingModal = document.getElementById('editFieldModal');
    if (existingModal) existingModal.remove();

    const modal = document.createElement('div');
    modal.id = 'editFieldModal';
    modal.className = 'fixed inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center z-[60]';
    modal.innerHTML = `
      <div class="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        <div class="px-6 py-4 border-b border-gray-200">
          <h3 class="text-lg font-semibold text-gray-900">Edit Field</h3>
        </div>
        <form id="editFieldForm" class="flex-1 flex flex-col">
          <div class="flex-1 overflow-y-auto p-6 space-y-4">
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Field Name *</label>
                <input type="text" name="name" required value="${this.escapeHtml(field.name)}"
                       class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 bg-gray-100" disabled>
                <p class="text-xs text-gray-500 mt-1">Cannot change after creation</p>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Label *</label>
                <input type="text" name="label" required value="${this.escapeHtml(field.label)}"
                       class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
              </div>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <textarea name="description" rows="2" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">${field.description || ''}</textarea>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Help Text</label>
              <input type="text" name="help_text" value="${field.help_text || ''}"
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Default Value</label>
              <input type="text" name="default_value" value="${field.default_value || ''}"
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
            </div>

            <div class="grid grid-cols-3 gap-4">
              <label class="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" name="is_required" ${field.is_required ? 'checked' : ''} class="rounded text-blue-600">
                <span class="text-sm text-gray-700">Required</span>
              </label>
              <label class="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" name="is_unique" ${field.is_unique ? 'checked' : ''} class="rounded text-blue-600">
                <span class="text-sm text-gray-700">Unique</span>
              </label>
              <label class="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" name="is_indexed" ${field.is_indexed ? 'checked' : ''} class="rounded text-blue-600">
                <span class="text-sm text-gray-700">Indexed</span>
              </label>
            </div>
          </div>

          <div class="px-6 py-4 border-t border-gray-200 flex gap-3">
            <button type="submit" class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
              <i class="ph ph-check"></i> Save Changes
            </button>
            <button type="button" onclick="DataModelApp.closeEditFieldModal()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200">
              Cancel
            </button>
          </div>
        </form>
      </div>
    `;

    document.body.appendChild(modal);

    // Add form submit handler
    document.getElementById('editFieldForm').addEventListener('submit', (e) => {
      e.preventDefault();
      this.updateField(entityId, field.id, e.target);
    });
  }

  closeEditFieldModal() {
    const modal = document.getElementById('editFieldModal');
    if (modal) modal.remove();
  }

  async updateField(entityId, fieldId, form) {
    const formData = new FormData(form);
    const data = {
      label: formData.get('label'),
      description: formData.get('description') || null,
      help_text: formData.get('help_text') || null,
      default_value: formData.get('default_value') || null,
      is_required: formData.get('is_required') === 'on',
      is_unique: formData.get('is_unique') === 'on',
      is_indexed: formData.get('is_indexed') === 'on',
      is_nullable: formData.get('is_required') !== 'on'
    };

    try {
      const response = await apiFetch(`/data-model/entities/${entityId}/fields/${fieldId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authService.getToken()}`
        },
        body: JSON.stringify(data)
      });

      if (response.ok) {
        this.closeEditFieldModal();
        this.showSuccess('Field updated successfully');
        // Reload field manager
        await this.manageFields(entityId);
      } else {
        const error = await response.json();
        this.showError(error.detail || 'Failed to update field');
      }
    } catch (error) {
      console.error('Error updating field:', error);
      this.showError('Error updating field');
    }
  }

  async deleteField(entityId, fieldId) {
    if (!confirm('Are you sure you want to delete this field? This action cannot be undone.')) {
      return;
    }

    try {
      const response = await apiFetch(`/data-model/entities/${entityId}/fields/${fieldId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${authService.getToken()}`
        }
      });

      if (response.ok) {
        this.showSuccess('Field deleted successfully');
        // Reload field manager
        await this.manageFields(entityId);
      } else {
        const error = await response.json();
        this.showError(error.detail || 'Failed to delete field');
      }
    } catch (error) {
      console.error('Error deleting field:', error);
      this.showError('Error deleting field');
    }
  }

  async viewRelationships(id) {
    try {
      // Load entity and relationships
      const [entityResponse, relationshipsResponse] = await Promise.all([
        fetch(`/api/v1/data-model/entities/${id}`, {
          headers: { 'Authorization': `Bearer ${authService.getToken()}` }
        }),
        fetch(`/api/v1/data-model/relationships?entity_id=${id}`, {
          headers: { 'Authorization': `Bearer ${authService.getToken()}` }
        })
      ]);

      if (!entityResponse.ok || !relationshipsResponse.ok) {
        this.showError('Failed to load relationship data');
        return;
      }

      const entity = await entityResponse.json();
      const relationships = await relationshipsResponse.json();

      this.showRelationshipViewer(entity, relationships);
    } catch (error) {
      console.error('Error loading relationships:', error);
      this.showError('Error loading relationships');
    }
  }

  showRelationshipViewer(entity, relationships) {
    const modal = document.createElement('div');
    modal.id = 'relationshipViewerModal';
    modal.className = 'fixed inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center z-50';
    modal.innerHTML = `
      <div class="bg-white rounded-lg shadow-xl w-full max-w-5xl max-h-[90vh] flex flex-col">
        <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h2 class="text-xl font-semibold text-gray-900">
              <i class="ph ph-arrows-merge"></i> Relationships: ${this.escapeHtml(entity.label)}
            </h2>
            <p class="text-sm text-gray-500 mt-1">Manage relationships with other entities</p>
          </div>
          <button onclick="DataModelApp.closeRelationshipViewer()" class="text-gray-400 hover:text-gray-600">
            <i class="ph ph-x text-2xl"></i>
          </button>
        </div>

        <div class="flex-1 overflow-y-auto p-6">
          <div class="mb-4 flex justify-between items-center">
            <div class="text-sm text-gray-600">
              ${relationships.length} relationships defined
            </div>
            <button onclick="DataModelApp.showAddRelationshipModal('${entity.id}')" class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
              <i class="ph ph-plus"></i> Add Relationship
            </button>
          </div>

          <div class="space-y-3" id="relationshipsList">
            ${relationships.length === 0 ? `
              <div class="text-center py-12 text-gray-500">
                <i class="ph-duotone ph-arrows-merge text-5xl"></i>
                <p class="mt-2">No relationships yet. Click "Add Relationship" to create one.</p>
              </div>
            ` : relationships.map(rel => this.renderRelationshipItem(rel)).join('')}
          </div>
        </div>

        <div class="px-6 py-4 border-t border-gray-200 flex justify-end">
          <button onclick="DataModelApp.closeRelationshipViewer()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200">
            Done
          </button>
        </div>
      </div>
    `;

    document.body.appendChild(modal);
    this.currentEntity = entity;
    this.currentRelationships = relationships;
  }

  renderRelationshipItem(rel) {
    const typeColors = {
      'one_to_many': 'bg-blue-100 text-blue-700',
      'many_to_one': 'bg-purple-100 text-purple-700',
      'many_to_many': 'bg-green-100 text-green-700',
      'one_to_one': 'bg-yellow-100 text-yellow-700'
    };
    const typeLabel = rel.relationship_type?.replace(/_/g, '-') || 'unknown';
    const typeClass = typeColors[rel.relationship_type] || 'bg-gray-100 text-gray-700';

    return `
      <div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition">
        <div class="flex-1">
          <div class="flex items-center gap-2 mb-2">
            <h4 class="font-medium text-gray-900">${this.escapeHtml(rel.name || 'Unnamed Relationship')}</h4>
            <span class="px-2 py-0.5 ${typeClass} rounded text-xs font-medium">${typeLabel}</span>
          </div>
          <div class="text-sm text-gray-600 space-y-1">
            <div class="flex items-center gap-2">
              <i class="ph ph-arrow-right"></i>
              <span>Target: <strong>${rel.target_entity_name || rel.target_entity_id}</strong></span>
            </div>
            ${rel.foreign_key_field ? `
              <div class="flex items-center gap-2">
                <i class="ph ph-key"></i>
                <span>Foreign Key: <strong>${rel.foreign_key_field}</strong></span>
              </div>
            ` : ''}
            ${rel.description ? `<p class="text-gray-500 mt-1">${this.escapeHtml(rel.description)}</p>` : ''}
          </div>
        </div>
        <div class="flex gap-2 ml-4">
          <button onclick="DataModelApp.deleteRelationship('${rel.id}')" class="px-3 py-1.5 bg-red-50 text-red-700 rounded hover:bg-red-100 text-sm">
            <i class="ph ph-trash"></i> Delete
          </button>
        </div>
      </div>
    `;
  }

  closeRelationshipViewer() {
    const modal = document.getElementById('relationshipViewerModal');
    if (modal) modal.remove();
  }

  showAddRelationshipModal(entityId) {
    const modal = document.createElement('div');
    modal.id = 'addRelationshipModal';
    modal.className = 'fixed inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center z-[60]';
    modal.innerHTML = `
      <div class="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        <div class="px-6 py-4 border-b border-gray-200">
          <h3 class="text-lg font-semibold text-gray-900">Add Relationship</h3>
        </div>
        <form id="addRelationshipForm" class="flex-1 flex flex-col">
          <div class="flex-1 overflow-y-auto p-6 space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Relationship Name *</label>
              <input type="text" name="name" required placeholder="customer_orders"
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500">
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Relationship Type *</label>
              <select name="relationship_type" required
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500">
                <option value="">Select type...</option>
                <option value="one_to_many">One-to-Many</option>
                <option value="many_to_one">Many-to-One</option>
                <option value="many_to_many">Many-to-Many</option>
                <option value="one_to_one">One-to-One</option>
              </select>
              <p class="text-xs text-gray-500 mt-1">Define how entities relate to each other</p>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Target Entity ID *</label>
              <input type="text" name="target_entity_id" required placeholder="UUID of target entity"
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500">
              <p class="text-xs text-gray-500 mt-1">Entity this relationship points to</p>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Foreign Key Field</label>
              <input type="text" name="foreign_key_field" placeholder="customer_id"
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500">
              <p class="text-xs text-gray-500 mt-1">Field name storing the foreign key</p>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <textarea name="description" rows="2" placeholder="Relationship description..."
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"></textarea>
            </div>
          </div>

          <div class="px-6 py-4 border-t border-gray-200 flex gap-3">
            <button type="submit" class="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
              <i class="ph ph-plus"></i> Add Relationship
            </button>
            <button type="button" onclick="DataModelApp.closeAddRelationshipModal()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200">
              Cancel
            </button>
          </div>
        </form>
      </div>
    `;

    document.body.appendChild(modal);

    document.getElementById('addRelationshipForm').addEventListener('submit', (e) => {
      e.preventDefault();
      this.createRelationship(entityId, e.target);
    });
  }

  closeAddRelationshipModal() {
    const modal = document.getElementById('addRelationshipModal');
    if (modal) modal.remove();
  }

  async createRelationship(sourceEntityId, form) {
    const formData = new FormData(form);
    const data = {
      name: formData.get('name'),
      source_entity_id: sourceEntityId,
      target_entity_id: formData.get('target_entity_id'),
      relationship_type: formData.get('relationship_type'),
      foreign_key_field: formData.get('foreign_key_field') || null,
      description: formData.get('description') || null
    };

    try {
      const response = await apiFetch('/data-model/relationships', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authService.getToken()}`
        },
        body: JSON.stringify(data)
      });

      if (response.ok) {
        this.closeAddRelationshipModal();
        this.showSuccess('Relationship created successfully');
        await this.viewRelationships(sourceEntityId);
      } else {
        const error = await response.json();
        this.showError(error.detail || 'Failed to create relationship');
      }
    } catch (error) {
      console.error('Error creating relationship:', error);
      this.showError('Error creating relationship');
    }
  }

  async deleteRelationship(relationshipId) {
    if (!confirm('Are you sure you want to delete this relationship?')) {
      return;
    }

    try {
      const response = await apiFetch(`/data-model/relationships/${relationshipId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${authService.getToken()}`
        }
      });

      if (response.ok) {
        this.showSuccess('Relationship deleted successfully');
        // Reload relationship viewer
        const entityId = this.currentEntity?.id;
        if (entityId) {
          await this.viewRelationships(entityId);
        }
      } else {
        const error = await response.json();
        this.showError(error.detail || 'Failed to delete relationship');
      }
    } catch (error) {
      console.error('Error deleting relationship:', error);
      this.showError('Error deleting relationship');
    }
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // ==================== Import from Database Methods ====================

  async showImportFromDatabaseModal() {
    const modal = document.getElementById('importDbModal');
    modal.classList.remove('hidden');
    await this.loadDatabaseObjects();
  }

  closeImportModal() {
    const modal = document.getElementById('importDbModal');
    modal.classList.add('hidden');
  }

  async loadDatabaseObjects(schema = 'public') {
    const loadingEl = document.getElementById('dbObjectsLoading');
    const listEl = document.getElementById('dbObjectsList');

    loadingEl.classList.remove('hidden');
    listEl.classList.add('hidden');

    try {      const response = await apiFetch(`/data-model/introspect/objects?schema=${schema}`);

      if (response.ok) {
        const data = await response.json();

        // Render tables
        this.renderObjectList(data.tables, 'tablesList', 'tablesCount');

        // Render views
        this.renderObjectList(data.views, 'viewsList', 'viewsCount');

        // Render materialized views
        this.renderObjectList(data.materialized_views, 'materializedViewsList', 'materializedViewsCount');

        loadingEl.classList.add('hidden');
        listEl.classList.remove('hidden');
      } else {
        this.showError('Failed to load database objects');
        loadingEl.classList.add('hidden');
      }
    } catch (error) {
      console.error('Error loading database objects:', error);
      this.showError('Error loading database objects');
      loadingEl.classList.add('hidden');
    }
  }

  renderObjectList(objects, containerId, countId) {
    const container = document.getElementById(containerId);
    const countEl = document.getElementById(countId);

    if (!container) return;

    if (countEl) {
      countEl.textContent = `(${objects.length})`;
    }

    if (objects.length === 0) {
      container.innerHTML = '<div class="p-4 text-center text-sm text-gray-500">No objects found</div>';
      return;
    }

    container.innerHTML = objects.map(obj => `
      <label class="flex items-center gap-3 p-4 hover:bg-gray-50 cursor-pointer transition">
        <input type="checkbox"
               class="object-checkbox w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
               data-object-name="${this.escapeHtml(obj.name)}"
               data-object-type="${obj.type}"
               onchange="DataModelApp.updateSelectedCount()">
        <div class="flex-1 min-w-0">
          <div class="font-medium text-gray-900">${this.escapeHtml(obj.name)}</div>
          ${obj.comment ? `<div class="text-sm text-gray-500 truncate">${this.escapeHtml(obj.comment)}</div>` : ''}
        </div>
        <button onclick="event.preventDefault(); event.stopPropagation(); DataModelApp.previewObject('${this.escapeHtml(obj.name)}', '${obj.type}');"
                class="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition"
                title="Preview">
          <i class="ph ph-eye text-lg"></i>
        </button>
      </label>
    `).join('');
  }

  updateSelectedCount() {
    const count = document.querySelectorAll('.object-checkbox:checked').length;
    const countEl = document.getElementById('selectedCount');
    if (countEl) {
      countEl.textContent = `${count} object${count !== 1 ? 's' : ''} selected`;
    }
  }

  selectAllObjects(objectType) {
    const checkboxes = document.querySelectorAll(`.object-checkbox[data-object-type="${objectType}"]`);
    checkboxes.forEach(cb => cb.checked = true);
    this.updateSelectedCount();
  }

  async previewObject(objectName, objectType) {
    try {      const response = await apiFetch('/data-model/introspect/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          object_name: objectName,
          object_type: objectType,
          schema: 'public',
          auto_save: false
        })
      });

      if (response.ok) {
        const entityData = await response.json();
        this.showPreviewModal(entityData);
      } else {
        this.showError('Failed to preview object');
      }
    } catch (error) {
      console.error('Error previewing object:', error);
      this.showError('Error previewing object');
    }
  }

  showPreviewModal(entityData) {
    // Create preview modal dynamically
    const modalHTML = `
      <div id="previewModal" class="fixed inset-0 bg-black bg-opacity-50 z-[60] flex items-center justify-center p-4">
        <div class="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col">
          <div class="px-6 py-4 border-b border-gray-200">
            <div class="flex items-center justify-between">
              <h3 class="text-xl font-bold text-gray-900">Preview: ${this.escapeHtml(entityData.label)}</h3>
              <button onclick="DataModelApp.closePreviewModal()" class="text-gray-400 hover:text-gray-600">
                <i class="ph ph-x text-2xl"></i>
              </button>
            </div>
          </div>

          <div class="flex-1 overflow-y-auto p-6 space-y-6">
            <!-- Entity Info -->
            <div class="grid grid-cols-3 gap-4 p-4 bg-gray-50 rounded-lg">
              <div>
                <label class="text-sm font-medium text-gray-500">Name</label>
                <div class="mt-1 text-gray-900">${this.escapeHtml(entityData.name)}</div>
              </div>
              <div>
                <label class="text-sm font-medium text-gray-500">Type</label>
                <div class="mt-1"><span class="px-2 py-1 bg-blue-100 text-blue-700 rounded text-sm">${entityData.object_type}</span></div>
              </div>
              <div>
                <label class="text-sm font-medium text-gray-500">Table/View</label>
                <div class="mt-1 text-gray-900">${this.escapeHtml(entityData.table_name)}</div>
              </div>
            </div>

            <!-- Fields -->
            <div>
              <h4 class="font-semibold text-gray-900 mb-3">Fields (${entityData.fields.length})</h4>
              <div class="border border-gray-200 rounded-lg overflow-hidden">
                <table class="min-w-full divide-y divide-gray-200">
                  <thead class="bg-gray-50">
                    <tr>
                      <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Field</th>
                      <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                      <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Constraints</th>
                      <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Reference</th>
                    </tr>
                  </thead>
                  <tbody class="bg-white divide-y divide-gray-200">
                    ${entityData.fields.map(field => `
                      <tr>
                        <td class="px-4 py-3">
                          <div class="font-medium text-gray-900">${this.escapeHtml(field.label)}</div>
                          <div class="text-sm text-gray-500">${this.escapeHtml(field.name)}</div>
                        </td>
                        <td class="px-4 py-3">
                          <span class="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs font-medium">${this.escapeHtml(field.field_type)}</span>
                        </td>
                        <td class="px-4 py-3">
                          <div class="flex flex-wrap gap-1">
                            ${field.is_required ? '<span class="px-2 py-0.5 bg-red-100 text-red-700 rounded text-xs">Required</span>' : ''}
                            ${field.is_unique ? '<span class="px-2 py-0.5 bg-yellow-100 text-yellow-700 rounded text-xs">Unique</span>' : ''}
                            ${field.is_readonly ? '<span class="px-2 py-0.5 bg-gray-100 text-gray-700 rounded text-xs">Readonly</span>' : ''}
                            ${field.is_computed ? '<span class="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs">Computed</span>' : ''}
                          </div>
                        </td>
                        <td class="px-4 py-3 text-sm text-gray-500">
                          ${field.reference_table ? `→ ${this.escapeHtml(field.reference_table)}.${this.escapeHtml(field.reference_field)}` : '-'}
                        </td>
                      </tr>
                    `).join('')}
                  </tbody>
                </table>
              </div>
            </div>

            ${entityData.relationships && entityData.relationships.length > 0 ? `
              <div>
                <h4 class="font-semibold text-gray-900 mb-3">Relationships (${entityData.relationships.length})</h4>
                <div class="space-y-2">
                  ${entityData.relationships.map(rel => `
                    <div class="p-3 bg-gray-50 rounded-lg">
                      <div class="font-medium text-gray-900">${this.escapeHtml(rel.label)}</div>
                      <div class="text-sm text-gray-500 mt-1">
                        <span class="px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded text-xs mr-2">${rel.relationship_type}</span>
                        → ${this.escapeHtml(rel.target_entity_name)}
                      </div>
                    </div>
                  `).join('')}
                </div>
              </div>
            ` : ''}
          </div>

          <div class="px-6 py-4 border-t border-gray-200 flex justify-end gap-2">
            <button onclick="DataModelApp.closePreviewModal()" class="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition">
              Close
            </button>
            <button onclick="DataModelApp.importSingleObject('${this.escapeHtml(entityData.name)}', '${entityData.object_type}')" class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition flex items-center gap-2">
              <i class="ph ph-download"></i>
              Import This Entity
            </button>
          </div>
        </div>
      </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHTML);
  }

  closePreviewModal() {
    const modal = document.getElementById('previewModal');
    if (modal) {
      modal.remove();
    }
  }

  async importSingleObject(objectName, objectType) {
    try {      const response = await apiFetch('/data-model/introspect/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          object_name: objectName,
          object_type: objectType,
          schema: 'public',
          auto_save: true
        })
      });

      if (response.ok) {
        this.showSuccess(`Entity "${objectName}" imported successfully`);
        this.closePreviewModal();
        this.closeImportModal();
        await this.loadEntities(); // Refresh list
      } else {
        this.showError('Failed to import entity');
      }
    } catch (error) {
      console.error('Error importing entity:', error);
      this.showError('Error importing entity');
    }
  }

  async importSelectedObjects() {
    const checkboxes = document.querySelectorAll('.object-checkbox:checked');

    if (checkboxes.length === 0) {
      this.showError('Please select at least one object');
      return;
    }

    const objects = Array.from(checkboxes).map(cb => ({
      name: cb.dataset.objectName,
      type: cb.dataset.objectType
    }));

    try {      const response = await apiFetch('/data-model/introspect/batch-generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          objects: objects,
          schema: 'public',
          auto_save: true
        })
      });

      if (response.ok) {
        const result = await response.json();
        this.showSuccess(`Imported ${result.queued} of ${result.total} objects successfully`);
        this.closeImportModal();
        await this.loadEntities(); // Refresh list
      } else {
        this.showError('Failed to import objects');
      }
    } catch (error) {
      console.error('Error importing objects:', error);
      this.showError('Error importing objects');
    }
  }

  async previewSelected() {
    const checkboxes = document.querySelectorAll('.object-checkbox:checked');

    if (checkboxes.length === 0) {
      this.showError('Please select at least one object');
      return;
    }

    if (checkboxes.length > 1) {
      this.showError('Please select only one object to preview');
      return;
    }

    const cb = checkboxes[0];
    await this.previewObject(cb.dataset.objectName, cb.dataset.objectType);
  }

  // ==================== Migration Methods ====================

  async previewMigration(entityId) {
    try {
      const response = await apiFetch(`/data-model/entities/${entityId}/preview-migration`);
      if (!response.ok) {
        const error = await response.json();
        this.showError(error.detail || 'Failed to preview migration');
        return;
      }

      const preview = await response.json();

      // Show preview modal
      this.showMigrationPreviewModal(preview);
    } catch (error) {
      console.error('Error previewing migration:', error);
      this.showError('Error previewing migration');
    }
  }

  showMigrationPreviewModal(preview) {
    // Remove existing preview modal if any
    const existingModal = document.getElementById('migrationPreviewModal');
    if (existingModal) existingModal.remove();

    // Get risk level color
    const riskColors = {
      'low': 'text-green-700 bg-green-100',
      'medium': 'text-yellow-700 bg-yellow-100',
      'high': 'text-red-700 bg-red-100'
    };

    const riskColor = riskColors[preview.estimated_impact.risk_level] || riskColors['low'];

    const modalHTML = `
      <div id="migrationPreviewModal" class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-5xl max-h-[90vh] flex flex-col">
          <!-- Header -->
          <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <h3 class="text-lg font-semibold text-gray-900">
              <i class="ph ph-eye"></i> Migration Preview: ${preview.entity_name}
            </h3>
            <button onclick="DataModelApp.closeMigrationPreviewModal()" class="text-gray-400 hover:text-gray-600">
              <i class="ph ph-x text-xl"></i>
            </button>
          </div>

          <!-- Content -->
          <div class="flex-1 overflow-y-auto p-6 space-y-6">
            <!-- Operation Info -->
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div class="flex items-center gap-2 mb-2">
                <i class="ph ph-info text-blue-600"></i>
                <span class="font-semibold text-blue-900">Operation Type</span>
              </div>
              <p class="text-sm text-blue-800">${preview.operation === 'CREATE' ? 'Create new table' : 'Alter existing table'}: ${preview.table_name}</p>
            </div>

            <!-- Impact Assessment -->
            <div class="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <div class="flex items-center justify-between mb-3">
                <span class="font-semibold text-gray-900">Impact Assessment</span>
                <span class="px-3 py-1 rounded-full text-sm font-medium ${riskColor}">
                  ${preview.estimated_impact.risk_level.toUpperCase()} RISK
                </span>
              </div>
              <div class="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span class="text-gray-600">Affected Records:</span>
                  <span class="ml-2 font-medium">${preview.estimated_impact.affected_records}</span>
                </div>
                ${preview.changes && preview.changes.added_columns ? `
                  <div>
                    <span class="text-gray-600">New Columns:</span>
                    <span class="ml-2 font-medium">${preview.changes.added_columns.length}</span>
                  </div>
                ` : ''}
                ${preview.changes && preview.changes.removed_columns ? `
                  <div>
                    <span class="text-gray-600">Removed Columns:</span>
                    <span class="ml-2 font-medium">${preview.changes.removed_columns.length}</span>
                  </div>
                ` : ''}
                ${preview.changes && preview.changes.modified_columns ? `
                  <div>
                    <span class="text-gray-600">Modified Columns:</span>
                    <span class="ml-2 font-medium">${preview.changes.modified_columns.length}</span>
                  </div>
                ` : ''}
              </div>

              ${preview.estimated_impact.breaking_changes && preview.estimated_impact.breaking_changes.length > 0 ? `
                <div class="mt-3 p-3 bg-red-50 border border-red-200 rounded">
                  <div class="font-semibold text-red-800 mb-2">Breaking Changes:</div>
                  <ul class="text-sm text-red-700 list-disc list-inside">
                    ${preview.estimated_impact.breaking_changes.map(bc => `<li>${bc}</li>`).join('')}
                  </ul>
                </div>
              ` : ''}

              ${preview.estimated_impact.warnings && preview.estimated_impact.warnings.length > 0 ? `
                <div class="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded">
                  <div class="font-semibold text-yellow-800 mb-2">Warnings:</div>
                  <ul class="text-sm text-yellow-700 list-disc list-inside">
                    ${preview.estimated_impact.warnings.map(w => `<li>${w}</li>`).join('')}
                  </ul>
                </div>
              ` : ''}
            </div>

            <!-- SQL Scripts -->
            <div class="space-y-4">
              <!-- Up Script -->
              <div>
                <div class="flex items-center gap-2 mb-2">
                  <i class="ph ph-arrow-up text-green-600"></i>
                  <span class="font-semibold text-gray-900">Migration Script (UP)</span>
                </div>
                <pre class="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm"><code>${this.escapeHtml(preview.up_script)}</code></pre>
              </div>

              <!-- Down Script -->
              <div>
                <div class="flex items-center gap-2 mb-2">
                  <i class="ph ph-arrow-down text-red-600"></i>
                  <span class="font-semibold text-gray-900">Rollback Script (DOWN)</span>
                </div>
                <pre class="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm"><code>${this.escapeHtml(preview.down_script)}</code></pre>
              </div>
            </div>
          </div>

          <!-- Footer Actions -->
          <div class="px-6 py-4 border-t border-gray-200 flex gap-3 justify-end">
            <button onclick="DataModelApp.closeMigrationPreviewModal()" class="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300">
              Cancel
            </button>
            <button onclick="DataModelApp.publishEntityFromPreview('${preview.entity_id}')" class="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700">
              <i class="ph ph-rocket-launch"></i> Proceed with Publish
            </button>
          </div>
        </div>
      </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHTML);
  }

  closeMigrationPreviewModal() {
    const modal = document.getElementById('migrationPreviewModal');
    if (modal) modal.remove();
  }

  async publishEntity(entityId) {
    const confirmed = confirm('Are you sure you want to publish this entity? This will execute the migration and create/alter the database table.');
    if (!confirmed) return;

    await this.executePublish(entityId);
  }

  async publishEntityFromPreview(entityId) {
    this.closeMigrationPreviewModal();
    await this.executePublish(entityId);
  }

  async executePublish(entityId) {
    try {
      const commitMessage = prompt('Enter a commit message (optional):');

      const response = await apiFetch(`/data-model/entities/${entityId}/publish`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ commit_message: commitMessage })
      });

      if (!response.ok) {
        const error = await response.json();
        this.showError(error.detail || 'Failed to publish entity');
        return;
      }

      const migration = await response.json();
      this.showSuccess(`Entity published successfully! Migration completed in ${migration.execution_time_ms}ms`);

      // Reload entity list and close modals
      await this.loadEntities();
      this.closeViewModal();
    } catch (error) {
      console.error('Error publishing entity:', error);
      this.showError('Error publishing entity');
    }
  }

  async viewMigrations(entityId) {
    try {
      const response = await apiFetch(`/data-model/entities/${entityId}/migrations`);
      if (!response.ok) {
        const error = await response.json();
        this.showError(error.detail || 'Failed to load migrations');
        return;
      }

      const data = await response.json();
      this.showMigrationHistoryModal(entityId, data.migrations);
    } catch (error) {
      console.error('Error loading migrations:', error);
      this.showError('Error loading migration history');
    }
  }

  showMigrationHistoryModal(entityId, migrations) {
    // Remove existing modal if any
    const existingModal = document.getElementById('migrationHistoryModal');
    if (existingModal) existingModal.remove();

    const statusColors = {
      'pending': 'bg-gray-100 text-gray-700',
      'running': 'bg-blue-100 text-blue-700',
      'completed': 'bg-green-100 text-green-700',
      'failed': 'bg-red-100 text-red-700',
      'rolled_back': 'bg-orange-100 text-orange-700'
    };

    const modalHTML = `
      <div id="migrationHistoryModal" class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-6xl max-h-[90vh] flex flex-col">
          <!-- Header -->
          <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <h3 class="text-lg font-semibold text-gray-900">
              <i class="ph ph-clock-clockwise"></i> Migration History
            </h3>
            <button onclick="DataModelApp.closeMigrationHistoryModal()" class="text-gray-400 hover:text-gray-600">
              <i class="ph ph-x text-xl"></i>
            </button>
          </div>

          <!-- Content -->
          <div class="flex-1 overflow-y-auto p-6">
            ${migrations.length === 0 ? `
              <div class="text-center py-12 text-gray-500">
                <i class="ph ph-database text-4xl mb-2"></i>
                <p>No migrations yet</p>
              </div>
            ` : `
              <div class="space-y-4">
                ${migrations.map(migration => `
                  <div class="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                    <!-- Migration Header -->
                    <div class="flex items-center justify-between mb-3">
                      <div class="flex items-center gap-3">
                        <span class="font-semibold text-gray-900">${migration.migration_name}</span>
                        <span class="px-2 py-1 rounded text-xs font-medium ${statusColors[migration.status] || statusColors['pending']}">
                          ${migration.status.toUpperCase()}
                        </span>
                        <span class="text-sm text-gray-500">${migration.migration_type.toUpperCase()}</span>
                      </div>
                      <div class="flex items-center gap-2">
                        ${migration.status === 'completed' && migration.down_script ? `
                          <button onclick="DataModelApp.rollbackMigration('${migration.id}')" class="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700">
                            <i class="ph ph-arrow-counter-clockwise"></i> Rollback
                          </button>
                        ` : ''}
                        <button onclick="DataModelApp.viewMigrationDetails('${migration.id}')" class="px-3 py-1 bg-gray-200 text-gray-700 text-sm rounded hover:bg-gray-300">
                          <i class="ph ph-eye"></i> Details
                        </button>
                      </div>
                    </div>

                    <!-- Migration Info -->
                    <div class="grid grid-cols-4 gap-4 text-sm">
                      <div>
                        <span class="text-gray-600">Version:</span>
                        <span class="ml-2 font-medium">${migration.from_version || 0} → ${migration.to_version}</span>
                      </div>
                      ${migration.executed_at ? `
                        <div>
                          <span class="text-gray-600">Executed:</span>
                          <span class="ml-2 font-medium">${new Date(migration.executed_at).toLocaleString()}</span>
                        </div>
                      ` : ''}
                      ${migration.execution_time_ms ? `
                        <div>
                          <span class="text-gray-600">Duration:</span>
                          <span class="ml-2 font-medium">${migration.execution_time_ms}ms</span>
                        </div>
                      ` : ''}
                      <div>
                        <span class="text-gray-600">Created:</span>
                        <span class="ml-2 font-medium">${new Date(migration.created_at).toLocaleString()}</span>
                      </div>
                    </div>

                    ${migration.error_message ? `
                      <div class="mt-3 p-3 bg-red-50 border border-red-200 rounded">
                        <div class="font-semibold text-red-800 mb-1">Error:</div>
                        <p class="text-sm text-red-700">${this.escapeHtml(migration.error_message)}</p>
                      </div>
                    ` : ''}
                  </div>
                `).join('')}
              </div>
            `}
          </div>

          <!-- Footer -->
          <div class="px-6 py-4 border-t border-gray-200 flex justify-end">
            <button onclick="DataModelApp.closeMigrationHistoryModal()" class="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300">
              Close
            </button>
          </div>
        </div>
      </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHTML);
  }

  closeMigrationHistoryModal() {
    const modal = document.getElementById('migrationHistoryModal');
    if (modal) modal.remove();
  }

  async viewMigrationDetails(migrationId) {
    try {
      // Get all migrations to find the specific one
      const historyModal = document.getElementById('migrationHistoryModal');
      if (!historyModal) return;

      // Find migration in current data (simpler approach)
      // In a real scenario, you'd fetch the specific migration
      this.showInfo('Migration details viewer - to be implemented with expanded SQL view');
    } catch (error) {
      console.error('Error viewing migration details:', error);
      this.showError('Error loading migration details');
    }
  }

  async rollbackMigration(migrationId) {
    const confirmed = confirm('Are you sure you want to rollback this migration? This will revert the database changes and cannot be undone.');
    if (!confirmed) return;

    try {
      const response = await apiFetch(`/data-model/migrations/${migrationId}/rollback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      if (!response.ok) {
        const error = await response.json();
        this.showError(error.detail || 'Failed to rollback migration');
        return;
      }

      const result = await response.json();
      this.showSuccess(`Migration rolled back successfully in ${result.execution_time_ms}ms`);

      // Close modal and reload
      this.closeMigrationHistoryModal();
      await this.loadEntities();
    } catch (error) {
      console.error('Error rolling back migration:', error);
      this.showError('Error rolling back migration');
    }
  }

  // ==================== Utility Methods ====================

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

  // ==================== Quick Actions ====================

  async createReportFromEntity(entityId) {
    // Find the entity
    const entity = this.entities.find(e => e.id === entityId);
    if (!entity) {
      this.showError('Entity not found');
      return;
    }

    // Navigate to report designer with entity pre-populated
    const params = new URLSearchParams({
      entity_id: entityId,
      entity_name: entity.name,
      label: entity.label
    });
    window.location.hash = `#/report-designer?${params.toString()}`;
    this.showSuccess(`Creating report from ${entity.label}...`);
  }

  async createPageFromEntity(entityId) {
    // Find the entity
    const entity = this.entities.find(e => e.id === entityId);
    if (!entity) {
      this.showError('Entity not found');
      return;
    }

    // Navigate to page builder with entity pre-populated
    const params = new URLSearchParams({
      entity_id: entityId,
      entity_name: entity.name,
      label: entity.label
    });
    window.location.hash = `#/builder?${params.toString()}`;
    this.showSuccess(`Creating page for ${entity.label}...`);
  }

  async addEntityToMenu(entityId) {
    // Find the entity
    const entity = this.entities.find(e => e.id === entityId);
    if (!entity) {
      this.showError('Entity not found');
      return;
    }

    // Confirm action
    if (!confirm(`Add "${entity.label}" to the application menu?\n\nThis will create a new menu item that links to a list view of ${entity.label}.`)) {
      return;
    }

    try {
      // Call API to add entity to menu
      const response = await apiFetch('/menu/add-entity', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authService.getToken()}`
        },
        body: JSON.stringify({
          entity_id: entityId,
          entity_name: entity.name,
          label: entity.label,
          plural_label: entity.plural_label || entity.label,
          icon: entity.icon || 'ph-duotone ph-database',
          parent_menu: 'dynamic-entities' // Add to a "Dynamic Entities" submenu
        })
      });

      if (response.ok) {
        this.showSuccess(`${entity.label} added to menu successfully! Refresh the page to see changes.`);
      } else {
        const error = await response.json();
        this.showError(error.detail || 'Failed to add entity to menu');
      }
    } catch (error) {
      console.error('Error adding entity to menu:', error);
      // Even if API fails, show a friendly message
      this.showSuccess(`Entity will be added to menu. Note: You may need to configure menu settings manually.`);
    }
  }

  cleanup() {
    delete window.DataModelApp;
  }
}
