import { metadataService } from './metadata-service.js';
import { dataService } from './data-service.js';
import { DynamicTable } from './dynamic-table.js';
import { DynamicForm } from './dynamic-form.js';

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
      this.container.innerHTML = `
        <div class="alert alert-danger">
          Failed to load entity: ${error.message}
        </div>
      `;
    }
  }

  /**
   * Render main UI
   */
  render() {
    this.container.innerHTML = `
      <div class="card shadow-sm">
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-center mb-3">
            <h5 class="mb-0">
              ${this.metadata.icon ? `<i class="bi bi-${this.metadata.icon}"></i>` : ''}
              ${this.metadata.display_name}
            </h5>
            <div>
              <button id="btn-refresh-${this.entity}" class="btn btn-outline-secondary btn-sm me-2">
                <i class="bi bi-arrow-clockwise"></i> Refresh
              </button>
              <button id="btn-add-${this.entity}" class="btn btn-primary btn-sm">
                <i class="bi bi-plus-lg"></i> Add ${this.metadata.display_name.slice(0, -1)}
              </button>
            </div>
          </div>
          
          ${this.metadata.description ? `
            <p class="text-muted small">${this.metadata.description}</p>
          ` : ''}
          
          <div id="${this.entity}-table-container"></div>
        </div>
      </div>

      <!-- Modal -->
      <div class="modal fade" id="${this.entity}-modal" tabindex="-1">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title" id="${this.entity}-modal-title">Record</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
              <div id="${this.entity}-form-container"></div>
              <div id="${this.entity}-error" class="alert alert-danger mt-3" style="display:none"></div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
              <button type="button" id="btn-save-${this.entity}" class="btn btn-primary">Save</button>
            </div>
          </div>
        </div>
      </div>
    `;

    // Wire up buttons
    document.getElementById(`btn-add-${this.entity}`).onclick = () => this.showCreateForm();
    document.getElementById(`btn-refresh-${this.entity}`).onclick = () => this.table.refresh();
    document.getElementById(`btn-save-${this.entity}`).onclick = () => this.saveRecord();
  }

  /**
   * Setup modal
   */
  setupModal() {
    const modalEl = document.getElementById(`${this.entity}-modal`);
    this.modal = new window.bootstrap.Modal(modalEl);
  }

  /**
   * Show create form
   */
  showCreateForm() {
    document.getElementById(`${this.entity}-modal-title`).textContent = 
      `Add ${this.metadata.display_name.slice(0, -1)}`;
    
    const container = document.getElementById(`${this.entity}-form-container`);
    const form = new DynamicForm(container, this.metadata);
    form.render();
    
    this.currentForm = form;
    this.currentRecord = null;
    
    this.hideError();
    this.modal.show();
  }

  /**
   * Show edit form
   */
  async showEditForm(row) {
    document.getElementById(`${this.entity}-modal-title`).textContent = 
      `Edit ${this.metadata.display_name.slice(0, -1)}`;
    
    try {
      // Fetch full record
      const record = await dataService.get(this.entity, row.id);
      
      const container = document.getElementById(`${this.entity}-form-container`);
      const form = new DynamicForm(container, this.metadata, record);
      form.render();
      
      this.currentForm = form;
      this.currentRecord = record;
      
      this.hideError();
      this.modal.show();
      
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
    const saveBtn = document.getElementById(`btn-save-${this.entity}`);
    
    try {
      saveBtn.disabled = true;
      saveBtn.textContent = 'Saving...';
      
      if (this.currentRecord) {
        // Update
        await dataService.update(this.entity, this.currentRecord.id, data);
      } else {
        // Create
        await dataService.create(this.entity, data);
      }
      
      this.modal.hide();
      await this.table.refresh();
      
    } catch (error) {
      this.showError(error.message);
    } finally {
      saveBtn.disabled = false;
      saveBtn.textContent = 'Save';
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
    // Create backdrop
    const backdrop = document.createElement('div');
    backdrop.id = 'modal-backdrop';
    backdrop.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 9998;';

    // Create modal container
    const modal = document.createElement('div');
    modal.style.cssText = 'position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); z-index: 9999; max-width: 500px; width: 90%;';

    // Create title
    const title = document.createElement('h5');
    title.textContent = `${this.metadata.display_name} Details`;
    modal.appendChild(title);

    // Create separator
    const hr = document.createElement('hr');
    modal.appendChild(hr);

    // Create details list
    const detailsContainer = document.createElement('div');
    detailsContainer.className = 'mt-3';

    this.metadata.table.columns.forEach(col => {
      const row_div = document.createElement('div');
      row_div.className = 'mb-2';

      const label = document.createElement('strong');
      label.textContent = `${col.title}: `;

      const value = document.createTextNode(row[col.field] || 'N/A');

      row_div.appendChild(label);
      row_div.appendChild(value);
      detailsContainer.appendChild(row_div);
    });

    modal.appendChild(detailsContainer);

    // Create close button
    const closeBtn = document.createElement('button');
    closeBtn.className = 'btn btn-secondary mt-3';
    closeBtn.textContent = 'Close';
    closeBtn.onclick = () => {
      modal.remove();
      backdrop.remove();
    };
    modal.appendChild(closeBtn);

    // Add to DOM
    document.body.appendChild(backdrop);
    document.body.appendChild(modal);

    // Close on backdrop click
    backdrop.onclick = () => {
      modal.remove();
      backdrop.remove();
    };
  }

  /**
   * Show error message (XSS-safe)
   */
  showError(message) {
    const errorDiv = document.getElementById(`${this.entity}-error`);
    errorDiv.textContent = message; // Already safe with textContent
    errorDiv.style.display = 'block';
  }

  /**
   * Hide error message
   */
  hideError() {
    const errorDiv = document.getElementById(`${this.entity}-error`);
    errorDiv.style.display = 'none';
  }
}
