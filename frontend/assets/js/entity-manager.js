import { metadataService } from './metadata-service.js';
import { dataService } from './data-service.js';
import { DynamicTable } from './dynamic-table.js';
import { DynamicForm } from './dynamic-form.js';
import FlexModal from './components/flex-modal.js';
import FlexButton from './components/flex-button.js';
import FlexAlert from './components/flex-alert.js';
import { apiFetch } from './api.js';

/**
 * Entity Manager - Complete CRUD UI for any entity (standard and nocode)
 *
 * Supports:
 * - Standard entities (using metadata-service and data-service)
 * - NoCode entities (using dynamic-data endpoints and entity definitions)
 */
export class EntityManager {
  constructor(container, entity) {
    this.container = container;
    this.entity = entity;
    this.metadata = null;
    this.table = null;
    this.modal = null;
    this.isNocodeEntity = false;
  }

  /**
   * Initialize and render
   */
  async init() {
    try {
      // Try to load standard metadata first
      try {
        this.metadata = await metadataService.getMetadata(this.entity);
        this.isNocodeEntity = false;
      } catch (standardError) {
        // Standard metadata failed - try nocode entity definition
        console.log(`Standard metadata not found for ${this.entity}, trying nocode entity...`);
        try {
          const entityDef = await this.loadNocodeEntityDefinition(this.entity);
          this.metadata = this.convertEntityDefToMetadata(entityDef);
          this.isNocodeEntity = true;
          console.log(`✅ Loaded nocode entity: ${this.entity}`);
        } catch (nocodeError) {
          // Neither standard nor nocode entity found
          throw new Error(`Entity "${this.entity}" not found (tried both standard and nocode)`);
        }
      }

      // Render UI
      this.render();

      // Setup modal
      this.setupModal();

      // Render table
      this.table = new DynamicTable(
        document.getElementById(`${this.entity}-table-container`),
        this.entity,
        this.metadata
      );

      // Handle row actions
      this.table.onRowAction = (action, row) => this.handleRowAction(action, row);

      await this.table.render();

    } catch (error) {
      console.error('Failed to initialize entity manager:', error);
      this.container.innerHTML = '';
      new FlexAlert(this.container, {
        message: `Failed to load entity: ${error.message}`,
        variant: 'danger',
        dismissible: false,
        icon: true
      });
    }
  }

  /**
   * Load nocode entity definition from API
   */
  async loadNocodeEntityDefinition(entityName) {
    const response = await apiFetch(`/data-model/entities/${entityName}`);
    if (!response.ok) {
      throw new Error(`Entity definition not found: ${response.status}`);
    }
    return await response.json();
  }

  /**
   * Convert nocode entity definition to metadata format
   */
  convertEntityDefToMetadata(entityDef) {
    // Convert entity definition fields to metadata format
    const fields = entityDef.fields.map(field => {
      // Convert raw allowed_values (string array) to the {value, label} format
      // expected by DynamicForm's createSelect / FlexSelect.
      let options;
      if (field.allowed_values && Array.isArray(field.allowed_values)) {
        options = field.allowed_values.map(v =>
          typeof v === 'object' && v !== null ? v : { value: String(v), label: String(v) }
        );
      } else if (field.options) {
        options = field.options;
      }

      return {
        field: field.name,
        name: field.name,
        label: field.label || field.name,
        type: field.field_type,
        required: field.is_required || field.required || false,
        max_length: field.max_length,
        decimal_places: field.decimal_places,
        options,
        default_value: field.default_value,
        help_text: field.help_text,
        validation_rules: field.validation_rules
      };
    });

    // Convert to table columns
    const columns = entityDef.fields
      .filter(field => !field.hidden)
      .map(field => ({
        field: field.name,
        title: field.label || field.name,
        type: field.field_type,
        sortable: true,
        filterable: true
      }));

    return {
      name: entityDef.name,
      display_name: entityDef.label || entityDef.name,
      description: entityDef.description,
      icon: entityDef.icon || 'database',
      fields,
      table: {
        columns,
        default_sort: [['created_at', 'desc']],
        page_size: 25,
        actions: ['view', 'edit', 'delete']
      },
      form: {
        fields: fields.filter(f => !['id', 'created_at', 'updated_at'].includes(f.name))
      },
      permissions: {}
    };
  }

  /**
   * Render main UI
   */
  render() {
    this.container.innerHTML = `
      <div class="bg-white rounded-lg border border-gray-200 shadow-sm">
        <div class="p-6">
          <div class="flex justify-between items-center mb-3">
            <h5 class="text-xl font-semibold text-gray-900">
              ${this.metadata.icon ? `<i class="ph-duotone ph-${this.metadata.icon}"></i>` : ''}
              ${this.metadata.display_name}
            </h5>
            <div class="flex gap-2">
              <div id="btn-refresh-${this.entity}-container"></div>
              <div id="btn-add-${this.entity}-container"></div>
            </div>
          </div>

          ${this.metadata.description ? `
            <p class="text-gray-500 text-sm mb-4">${this.metadata.description}</p>
          ` : ''}

          <div id="${this.entity}-table-container"></div>
        </div>
      </div>
    `;

    // Create refresh button using FlexButton
    const refreshBtnContainer = document.getElementById(`btn-refresh-${this.entity}-container`);
    new FlexButton(refreshBtnContainer, {
      text: 'Refresh',
      icon: '<i class="ph-duotone ph-arrow-clockwise"></i>',
      variant: 'secondary',
      size: 'sm',
      onClick: () => this.table.refresh()
    });

    // Create add button using FlexButton
    const addBtnContainer = document.getElementById(`btn-add-${this.entity}-container`);
    new FlexButton(addBtnContainer, {
      text: `Add ${this.metadata.display_name.slice(0, -1)}`,
      icon: '<i class="ph-duotone ph-plus"></i>',
      variant: 'primary',
      size: 'sm',
      onClick: () => this.showCreateForm()
    });
  }

  /**
   * Setup modal
   */
  setupModal() {
    // Create modal container
    const modalContainer = document.createElement('div');
    modalContainer.id = `${this.entity}-modal-container`;
    document.body.appendChild(modalContainer);

    // Modal content will be created dynamically in showCreateForm/showEditForm
    this.modalContainer = modalContainer;
    this.modal = null;
  }

  /**
   * Show create form
   */
  showCreateForm() {
    const title = `Add ${this.metadata.display_name.slice(0, -1)}`;

    // Create form container
    const formContainer = document.createElement('div');
    formContainer.id = `${this.entity}-form-container`;

    // Create error container
    const errorContainer = document.createElement('div');
    errorContainer.id = `${this.entity}-error`;
    errorContainer.style.display = 'none';

    // Create modal content
    const modalContent = document.createElement('div');
    modalContent.appendChild(formContainer);
    modalContent.appendChild(errorContainer);

    // Create modal
    this.modalContainer.innerHTML = '';
    this.modal = new FlexModal(this.modalContainer, {
      title,
      content: modalContent,
      size: 'lg',
      actions: [
        {
          label: 'Cancel',
          variant: 'secondary',
          onClick: () => this.modal.close()
        },
        {
          label: 'Save',
          variant: 'primary',
          onClick: () => this.saveRecord()
        }
      ],
      closeOnBackdrop: false,
      closeOnEscape: true
    });

    // Render form
    const form = new DynamicForm(formContainer, this.metadata);
    form.render();

    this.currentForm = form;
    this.currentRecord = null;

    this.hideError();
    this.modal.open();
  }

  /**
   * Show edit form
   */
  async showEditForm(row) {
    const title = `Edit ${this.metadata.display_name.slice(0, -1)}`;

    try {
      // Fetch full record using appropriate service
      const record = this.isNocodeEntity
        ? await this.getNocodeRecord(row.id)
        : await dataService.get(this.entity, row.id);

      // Create form container
      const formContainer = document.createElement('div');
      formContainer.id = `${this.entity}-form-container`;

      // Create error container
      const errorContainer = document.createElement('div');
      errorContainer.id = `${this.entity}-error`;
      errorContainer.style.display = 'none';

      // Create modal content
      const modalContent = document.createElement('div');
      modalContent.appendChild(formContainer);
      modalContent.appendChild(errorContainer);

      // Create modal
      this.modalContainer.innerHTML = '';
      this.modal = new FlexModal(this.modalContainer, {
        title,
        content: modalContent,
        size: 'lg',
        actions: [
          {
            label: 'Cancel',
            variant: 'secondary',
            onClick: () => this.modal.close()
          },
          {
            label: 'Save',
            variant: 'primary',
            onClick: () => this.saveRecord()
          }
        ],
        closeOnBackdrop: false,
        closeOnEscape: true
      });

      // Render form
      const form = new DynamicForm(formContainer, this.metadata, record);
      form.render();

      this.currentForm = form;
      this.currentRecord = record;

      this.hideError();
      this.modal.open();

    } catch (error) {
      alert(`Failed to load record: ${error.message}`);
    }
  }

  /**
   * Save record (create or update)
   */
  async saveRecord() {
    if (!this.currentForm.validate()) {
      return;
    }

    const data = this.currentForm.getValues();

    try {
      // Set loading state on the save button
      this.modal.setLoading(true);

      if (this.isNocodeEntity) {
        // Use nocode endpoints
        if (this.currentRecord) {
          await this.updateNocodeRecord(this.currentRecord.id, data);
        } else {
          await this.createNocodeRecord(data);
        }
      } else {
        // Use standard endpoints
        if (this.currentRecord) {
          await dataService.update(this.entity, this.currentRecord.id, data);
        } else {
          await dataService.create(this.entity, data);
        }
      }

      this.modal.close();
      await this.table.refresh();

    } catch (error) {
      this.showError(error.message);
      this.modal.setLoading(false);
    }
  }

  /**
   * Delete record
   */
  async deleteRecord(row) {
    if (!confirm(`Are you sure you want to delete this ${this.metadata.display_name.slice(0, -1)}?`)) {
      return;
    }

    try {
      if (this.isNocodeEntity) {
        await this.deleteNocodeRecord(row.id);
      } else {
        await dataService.delete(this.entity, row.id);
      }
      await this.table.refresh();
    } catch (error) {
      alert(`Failed to delete: ${error.message}`);
    }
  }

  /**
   * Handle row action
   */
  handleRowAction(action, row) {
    switch (action) {
      case 'view':
        this.showViewDialog(row);
        break;
      case 'edit':
        this.showEditForm(row);
        break;
      case 'delete':
        this.deleteRecord(row);
        break;
    }
  }

  /**
   * Show view dialog (read-only)
   */
  showViewDialog(row) {
    // Create details container
    const detailsContainer = document.createElement('div');
    detailsContainer.className = 'space-y-3';

    this.metadata.table.columns.forEach(col => {
      const rowDiv = document.createElement('div');
      rowDiv.className = 'flex gap-2';

      const label = document.createElement('strong');
      label.className = 'text-gray-700 min-w-[120px]';
      label.textContent = `${col.title}:`;

      const value = document.createElement('span');
      value.className = 'text-gray-900';
      value.textContent = row[col.field] || 'N/A';

      rowDiv.appendChild(label);
      rowDiv.appendChild(value);
      detailsContainer.appendChild(rowDiv);
    });

    // Create modal container
    const viewModalContainer = document.createElement('div');
    document.body.appendChild(viewModalContainer);

    // Create modal
    const viewModal = new FlexModal(viewModalContainer, {
      title: `${this.metadata.display_name} Details`,
      content: detailsContainer,
      size: 'md',
      actions: [
        {
          label: 'History',
          variant: 'secondary',
          onClick: () => {
            viewModal.close();
            setTimeout(() => viewModalContainer.remove(), 300);
            this.showVersionHistoryDrawer(row);
          }
        },
        {
          label: 'Close',
          variant: 'secondary',
          onClick: () => {
            viewModal.close();
            setTimeout(() => viewModalContainer.remove(), 300);
          }
        }
      ],
      closeOnBackdrop: true,
      closeOnEscape: true,
      onClose: () => {
        setTimeout(() => viewModalContainer.remove(), 300);
      }
    });

    viewModal.open();
  }

  // ── Screen 3: Version History Drawer ──────────────────────────────────────
  showVersionHistoryDrawer(record) {
    const host = document.createElement('div');
    host.id = 'version-history-host';
    document.body.appendChild(host);

    function fmtDate(iso) {
      try { return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(iso)); }
      catch { return iso || '—'; }
    }

    function renderDiff(version) {
      if (!version || !version.changes) return '<p class="text-xs text-gray-400">No diff available</p>';
      return Object.entries(version.changes).map(([field, change]) => `
        <div class="mb-3">
          <p class="text-xs font-semibold text-gray-600 mb-1">${field}</p>
          <div class="grid grid-cols-2 gap-2 text-xs">
            <div class="bg-red-50 border border-red-200 rounded p-2 text-red-700">
              <span class="text-red-400 text-[10px] font-semibold uppercase tracking-wide block mb-0.5">Before</span>
              ${String(change.before ?? '—')}
            </div>
            <div class="bg-green-50 border border-green-200 rounded p-2 text-green-700">
              <span class="text-green-400 text-[10px] font-semibold uppercase tracking-wide block mb-0.5">After</span>
              ${String(change.after ?? '—')}
            </div>
          </div>
        </div>`).join('');
    }

    const entity  = this.entityType || this.entity;
    const recordId = record.id;

    host.innerHTML = `
      <div id="vh-backdrop" class="fixed inset-0 bg-gray-900/50 z-40 transition-opacity duration-300 opacity-0"></div>
      <div id="vh-panel"
           class="fixed top-0 right-0 bottom-0 z-50 w-[520px] max-w-full bg-white shadow-2xl flex flex-col translate-x-full transition-transform duration-300">
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <div>
            <h2 class="text-base font-semibold text-gray-900 flex items-center gap-2">
              <i class="ph-duotone ph-clock-counter-clockwise text-blue-600 text-xl"></i>
              Version History
            </h2>
            <p class="text-xs text-gray-400 mt-0.5">Record ID: ${recordId}</p>
          </div>
          <button id="vh-close" class="w-8 h-8 rounded-lg hover:bg-gray-100 flex items-center justify-center text-gray-500">
            <i class="ph ph-x text-lg"></i>
          </button>
        </div>

        <div class="flex-1 flex overflow-hidden">
          <!-- Version list -->
          <div id="vh-list" class="w-2/5 border-r border-gray-100 overflow-y-auto">
            <div class="p-3 space-y-2">
              ${Array.from({length: 4}).map(() => `
                <div class="animate-pulse p-3 rounded-lg bg-gray-50 space-y-1.5">
                  <div class="h-2 bg-gray-200 rounded w-4/5"></div>
                  <div class="h-2 bg-gray-200 rounded w-3/5"></div>
                </div>`).join('')}
            </div>
          </div>
          <!-- Diff panel -->
          <div id="vh-diff" class="flex-1 overflow-y-auto p-4">
            <p class="text-xs text-gray-400">Select a version to see changes</p>
          </div>
        </div>
      </div>`;

    requestAnimationFrame(() => {
      host.querySelector('#vh-backdrop').classList.replace('opacity-0', 'opacity-100');
      host.querySelector('#vh-panel').classList.replace('translate-x-full', 'translate-x-0');
    });

    function close() {
      host.querySelector('#vh-backdrop').classList.replace('opacity-100', 'opacity-0');
      host.querySelector('#vh-panel').classList.replace('translate-x-0', 'translate-x-full');
      setTimeout(() => host.remove(), 320);
    }

    host.querySelector('#vh-close').addEventListener('click', close);
    host.querySelector('#vh-backdrop').addEventListener('click', close);

    // Load versions
    import('./api.js').then(({ apiFetch }) => {
      apiFetch(`/${entity}/records/${recordId}/versions`).then(async res => {
        const listEl = host.querySelector('#vh-list');
        if (!res.ok) {
          listEl.innerHTML = `<p class="p-3 text-xs text-red-500">Failed: HTTP ${res.status}</p>`;
          return;
        }
        const data = await res.json();
        const versions = Array.isArray(data) ? data : (data.versions || []);
        if (!versions.length) {
          listEl.innerHTML = `<div class="p-4 text-center text-xs text-gray-400">No version history</div>`;
          return;
        }
        listEl.innerHTML = versions.map((v, i) => `
          <button class="vh-version-row w-full text-left p-3 border-b border-gray-100 hover:bg-blue-50 transition text-xs ${i === 0 ? 'bg-blue-50' : ''}"
                  data-version-idx="${i}">
            <p class="font-medium text-gray-800">${fmtDate(v.changed_at)}</p>
            <p class="text-gray-500">${v.changed_by || '—'}</p>
            <p class="text-gray-400">${v.fields_changed_count ?? Object.keys(v.changes || {}).length} field(s) changed</p>
          </button>`).join('');

        // Show first version diff immediately
        host.querySelector('#vh-diff').innerHTML = renderDiff(versions[0]);

        listEl.addEventListener('click', e => {
          const btn = e.target.closest('.vh-version-row');
          if (!btn) return;
          listEl.querySelectorAll('.vh-version-row').forEach(r => r.classList.remove('bg-blue-50'));
          btn.classList.add('bg-blue-50');
          host.querySelector('#vh-diff').innerHTML = renderDiff(versions[+btn.dataset.versionIdx]);
        });
      }).catch(err => {
        host.querySelector('#vh-list').innerHTML = `<p class="p-3 text-xs text-red-500">${err.message}</p>`;
      });
    });
  }

  // ── Screen 4: Relationship Traversal Sub-Panel ──────────────────────────────
  async showRelationshipsPanel(record) {
    const relationships = this.metadata?.relationships || [];
    if (!relationships.length) return null;

    const entity = this.entityType || this.entity;
    const recordId = record.id;

    const container = document.createElement('div');
    container.className = 'mt-4 border-t border-gray-200 pt-4';

    // Build tab header
    const tabsHtml = relationships.map((rel, i) => `
      <button class="rel-tab py-2 px-3 text-xs font-medium rounded-md mr-1 transition
                     ${i === 0 ? 'bg-blue-100 text-blue-700' : 'text-gray-500 hover:bg-gray-100'}"
              data-rel="${rel.name}" data-rel-idx="${i}">
        ${rel.display_name || rel.name}
      </button>`).join('');

    container.innerHTML = `
      <h4 class="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
        <i class="ph-duotone ph-graph text-blue-500"></i>
        Related Records
      </h4>
      <div class="flex flex-wrap gap-1 mb-3">${tabsHtml}</div>
      <div id="rel-panel-body" class="min-h-[80px]">
        <div class="text-xs text-gray-400 flex items-center gap-2 py-4">
          <div class="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin"></div>
          Loading…
        </div>
      </div>`;

    // Load first relationship immediately
    const loadRelationship = async (relName) => {
      const panelBody = container.querySelector('#rel-panel-body');
      panelBody.innerHTML = `<div class="text-xs text-gray-400 flex items-center gap-2 py-4">
        <div class="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin"></div>Loading…</div>`;
      try {
        const { apiFetch } = await import('./api.js');
        const res = await apiFetch(`/${entity}/records/${recordId}/${relName}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const items = Array.isArray(data) ? data : (data.items || data.results || []);
        if (!items.length) {
          panelBody.innerHTML = `<p class="text-xs text-gray-400 py-2">No related records found</p>`;
          return;
        }
        // Build simple table from first record keys
        const keys = Object.keys(items[0]).filter(k => !['id','tenant_id'].includes(k)).slice(0, 5);
        panelBody.innerHTML = `
          <div class="overflow-x-auto rounded-lg border border-gray-200">
            <table class="min-w-full text-xs divide-y divide-gray-100">
              <thead class="bg-gray-50">
                <tr>${keys.map(k => `<th class="px-3 py-2 text-left font-medium text-gray-500 capitalize">${k}</th>`).join('')}</tr>
              </thead>
              <tbody class="divide-y divide-gray-100 bg-white">
                ${items.map(row => `<tr class="hover:bg-gray-50">${keys.map(k => `<td class="px-3 py-2 text-gray-700">${row[k] ?? '—'}</td>`).join('')}</tr>`).join('')}
              </tbody>
            </table>
          </div>
          ${data.total > items.length ? `<p class="text-xs text-gray-400 mt-2">Showing ${items.length} of ${data.total}</p>` : ''}`;
      } catch (err) {
        panelBody.innerHTML = `<p class="text-xs text-red-500 py-2">${err.message}</p>`;
      }
    };

    if (relationships[0]) await loadRelationship(relationships[0].name);

    container.addEventListener('click', e => {
      const tab = e.target.closest('.rel-tab');
      if (!tab) return;
      container.querySelectorAll('.rel-tab').forEach(t => {
        t.classList.remove('bg-blue-100', 'text-blue-700');
        t.classList.add('text-gray-500');
      });
      tab.classList.add('bg-blue-100', 'text-blue-700');
      tab.classList.remove('text-gray-500');
      loadRelationship(tab.dataset.rel);
    });

    return container;
  }

  /**
   * Show error message (XSS-safe)
   */
  showError(message) {
    const errorDiv = document.getElementById(`${this.entity}-error`);
    errorDiv.innerHTML = '';
    errorDiv.style.display = 'block';

    // Create FlexAlert
    new FlexAlert(errorDiv, {
      message,
      variant: 'danger',
      dismissible: false,
      icon: true
    });
  }

  /**
   * Hide error message
   */
  hideError() {
    const errorDiv = document.getElementById(`${this.entity}-error`);
    errorDiv.innerHTML = '';
    errorDiv.style.display = 'none';
  }

  /**
   * ========================================
   * NoCode Entity CRUD Adapter Methods
   * ========================================
   * These methods handle CRUD operations for dynamically-defined nocode entities
   * using the /dynamic-data endpoints
   */

  /**
   * Get a single nocode record
   */
  async getNocodeRecord(id) {
    const response = await apiFetch(`/dynamic-data/${this.entity}/records/${id}`);
    if (!response.ok) {
      throw new Error(`Failed to load record: ${response.status}`);
    }
    // Return the full { id, data } API response so DynamicForm can read record.data[field]
    return await response.json();
  }

  /**
   * Create a nocode record
   */
  async createNocodeRecord(data) {
    const response = await apiFetch(`/dynamic-data/${this.entity}/records`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ data })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Create failed');
    }

    return await response.json();
  }

  /**
   * Update a nocode record
   */
  async updateNocodeRecord(id, data) {
    const response = await apiFetch(`/dynamic-data/${this.entity}/records/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ data })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Update failed');
    }

    return await response.json();
  }

  /**
   * Delete a nocode record
   */
  async deleteNocodeRecord(id) {
    const response = await apiFetch(`/dynamic-data/${this.entity}/records/${id}`, {
      method: 'DELETE'
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Delete failed');
    }

    return true;
  }
}
