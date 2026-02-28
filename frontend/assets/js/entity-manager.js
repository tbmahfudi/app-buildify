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
