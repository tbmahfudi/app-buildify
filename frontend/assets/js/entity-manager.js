import { metadataService } from './metadata-service.js';
import { dataService } from './data-service.js';
import { DynamicTable } from './dynamic-table.js';
import { DynamicForm } from './dynamic-form.js';
import FlexModal from './components/flex-modal.js';
import FlexButton from './components/flex-button.js';
import FlexAlert from './components/flex-alert.js';

/**
 * Entity Manager - Complete CRUD UI for any entity
 */
export class EntityManager {
  constructor(container, entity) {
    this.container = container;
    this.entity = entity;
    this.metadata = null;
    this.table = null;
    this.modal = null;
  }

  /**
   * Initialize and render
   */
  async init() {
    try {
      // Load metadata
      this.metadata = await metadataService.getMetadata(this.entity);
      
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
      // Fetch full record
      const record = await dataService.get(this.entity, row.id);

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

      if (this.currentRecord) {
        // Update
        await dataService.update(this.entity, this.currentRecord.id, data);
      } else {
        // Create
        await dataService.create(this.entity, data);
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
      await dataService.delete(this.entity, row.id);
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
}
