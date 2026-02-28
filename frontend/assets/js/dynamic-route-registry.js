/**
 * Dynamic Route Registry - Auto-generates routes and UI for nocode entities
 *
 * This service automatically creates CRUD pages for published nocode entities:
 * - List view (#/dynamic/{entity}/list)
 * - Create form (#/dynamic/{entity}/create)
 * - Detail view (#/dynamic/{entity}/{id})
 * - Edit form (#/dynamic/{entity}/{id}/edit)
 */

import { apiFetch } from './api.js';
import { DynamicTable } from './dynamic-table.js';
import { DynamicForm } from './dynamic-form.js';

export class DynamicRouteRegistry {
  constructor() {
    this.registeredEntities = new Map();
    this.entityMetadata = new Map();
  }

  /**
   * Register routes for a nocode entity
   *
   * @param {string} entityName - Name of the entity (e.g., 'customers')
   * @returns {Promise<void>}
   */
  async registerEntity(entityName) {
    if (this.registeredEntities.has(entityName)) {
      console.log(`Entity ${entityName} already registered`);
      return;
    }

    try {
      console.log(`Registering routes for entity: ${entityName}`);

      // Fetch entity metadata
      const metadata = await this.fetchEntityMetadata(entityName);

      // Store metadata for later use
      this.entityMetadata.set(entityName, metadata);

      // Mark as registered
      this.registeredEntities.set(entityName, true);

      console.log(`✅ Entity ${entityName} registered successfully`);
    } catch (error) {
      console.error(`Failed to register entity ${entityName}:`, error);
      throw error;
    }
  }

  /**
   * Fetch entity metadata from backend
   *
   * @param {string} entityName - Name of the entity
   * @returns {Promise<Object>} Entity metadata
   */
  async fetchEntityMetadata(entityName) {
    try {
      const response = await apiFetch(`/metadata/entities/${entityName}`);

      if (!response.ok) {
        if (response.status === 404) {
          console.warn(`Metadata not found for entity ${entityName}, skipping registration`);
          throw new Error(`Metadata not found for ${entityName}`);
        }
        throw new Error(`Failed to fetch metadata for ${entityName}: ${response.statusText}`);
      }

      const metadata = await response.json();
      return metadata;
    } catch (error) {
      console.warn(`Error fetching metadata for ${entityName}:`, error.message);
      throw error;
    }
  }

  /**
   * Check if a route is a dynamic entity route
   *
   * @param {string} route - Route path
   * @returns {Object|null} Parsed route info or null
   */
  parseRoute(route) {
    // Pattern: dynamic/{entity}/list
    const listMatch = route.match(/^dynamic\/([^/]+)\/list$/);
    if (listMatch) {
      return { action: 'list', entity: listMatch[1] };
    }

    // Pattern: dynamic/{entity}/create
    const createMatch = route.match(/^dynamic\/([^/]+)\/create$/);
    if (createMatch) {
      return { action: 'create', entity: createMatch[1] };
    }

    // Pattern: dynamic/{entity}/{id}/edit
    const editMatch = route.match(/^dynamic\/([^/]+)\/([^/]+)\/edit$/);
    if (editMatch) {
      return { action: 'edit', entity: editMatch[1], id: editMatch[2] };
    }

    // Pattern: dynamic/{entity}/{id}
    const detailMatch = route.match(/^dynamic\/([^/]+)\/([^/]+)$/);
    if (detailMatch) {
      return { action: 'detail', entity: detailMatch[1], id: detailMatch[2] };
    }

    return null;
  }

  /**
   * Handle dynamic entity route
   *
   * @param {string} route - Route path
   * @param {HTMLElement} container - Content container
   * @returns {Promise<boolean>} True if route was handled
   */
  async handleRoute(route, container) {
    const parsed = this.parseRoute(route);

    if (!parsed) {
      return false;
    }

    const { action, entity, id } = parsed;

    // Ensure entity is registered
    if (!this.registeredEntities.has(entity)) {
      await this.registerEntity(entity);
    }

    const metadata = this.entityMetadata.get(entity);

    if (!metadata) {
      container.innerHTML = `
        <div class="max-w-2xl mx-auto mt-8 p-6 bg-red-50 border border-red-200 rounded-lg">
          <h3 class="text-lg font-semibold text-red-900 mb-2">Entity Not Found</h3>
          <p class="text-red-700">Could not load metadata for entity: ${entity}</p>
        </div>
      `;
      return true;
    }

    // Route to appropriate handler
    switch (action) {
      case 'list':
        await this.renderList(entity, metadata, container);
        break;
      case 'create':
        await this.renderCreate(entity, metadata, container);
        break;
      case 'detail':
        await this.renderDetail(entity, metadata, id, container);
        break;
      case 'edit':
        await this.renderEdit(entity, metadata, id, container);
        break;
      default:
        return false;
    }

    return true;
  }

  /**
   * Render list view
   */
  async renderList(entityName, metadata, container) {
    const icon = metadata.icon ? `<i class="ph-duotone ph-${metadata.icon} text-blue-600"></i>` : '<i class="ph-duotone ph-table text-blue-600"></i>';
    const displayName = metadata.display_name || entityName;

    container.innerHTML = `
      <div class="space-y-6">
        <!-- Page header -->
        <div class="bg-white border-b border-gray-200 px-6 py-4">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-2xl font-bold text-gray-900 flex items-center gap-3">
                ${icon}
                ${displayName}
              </h2>
              <p class="text-sm text-gray-600 mt-1">
                ${metadata.description || `Manage ${displayName} records`}
              </p>
            </div>
            <button type="button" id="btn-create-${entityName}"
              class="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 active:bg-blue-800 shadow-sm hover:shadow-md transition-all font-medium text-sm">
              <i class="ph ph-plus"></i>
              Add ${displayName}
            </button>
          </div>
        </div>

        <!-- Table area (DynamicTable renders search bar + card here) -->
        <div class="px-6" id="dynamic-table-container"></div>
      </div>
    `;

    document.getElementById(`btn-create-${entityName}`).addEventListener('click', () => {
      window.location.hash = `dynamic/${entityName}/create`;
    });

    // Render dynamic table (includes its own search/filter bar)
    const tableContainer = document.getElementById('dynamic-table-container');
    const table = new DynamicTable(tableContainer, entityName, metadata);
    await table.render();

    // Setup row actions
    // DynamicTable passes the full row object; extract .id for URL construction
    table.onRowAction = (action, row) => {
      const recordId = (row && typeof row === 'object') ? row.id : row;
      switch (action) {
        case 'view':
          window.location.hash = `dynamic/${entityName}/${recordId}`;
          break;
        case 'edit':
          window.location.hash = `dynamic/${entityName}/${recordId}/edit`;
          break;
        case 'delete':
          this.deleteRecord(entityName, recordId);
          break;
      }
    };
  }

  /**
   * Render create form
   */
  async renderCreate(entityName, metadata, container) {
    container.innerHTML = `
      <div class="px-4 sm:px-6 lg:px-8">
        <div class="mb-6">
          <button type="button" onclick="history.back()" class="inline-flex items-center text-sm font-medium text-gray-700 hover:text-gray-900">
            <i class="ph ph-arrow-left mr-2"></i>
            Back to ${metadata.display_name || entityName} List
          </button>
        </div>
        <div class="max-w-2xl">
          <h1 class="text-2xl font-semibold text-gray-900 mb-6">Create ${metadata.display_name || entityName}</h1>
          <div id="dynamic-form-container"></div>
          <div class="mt-6 flex items-center justify-end gap-x-3">
            <button type="button" onclick="history.back()" class="rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50">
              Cancel
            </button>
            <button type="submit" form="dynamic-form" class="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600">
              Create
            </button>
          </div>
        </div>
      </div>
    `;

    const formContainer = document.getElementById('dynamic-form-container');
    const form = new DynamicForm(formContainer, metadata);
    const formElement = form.render();

    // Handle form submission
    formElement.addEventListener('submit', async (e) => {
      e.preventDefault();

      try {
        const data = form.getValues();

        const response = await apiFetch(`/dynamic-data/${entityName}/records`, {
          method: 'POST',
          body: JSON.stringify({ data })
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail || 'Failed to create record');
        }

        // Show success message
        alert(`${metadata.display_name || entityName} created successfully!`);

        // Navigate back to list
        window.location.hash = `dynamic/${entityName}/list`;
      } catch (error) {
        console.error('Error creating record:', error);
        alert(`Error: ${error.message}`);
      }
    });
  }

  /**
   * Render detail view
   */
  async renderDetail(entityName, metadata, recordId, container) {
    try {
      const response = await apiFetch(`/dynamic-data/${entityName}/records/${recordId}`);

      if (!response.ok) {
        throw new Error('Failed to load record');
      }

      const result = await response.json();
      const record = result.data;

      container.innerHTML = `
        <div class="px-4 sm:px-6 lg:px-8">
          <div class="mb-6">
            <button type="button" onclick="history.back()" class="inline-flex items-center text-sm font-medium text-gray-700 hover:text-gray-900">
              <i class="ph ph-arrow-left mr-2"></i>
              Back to ${metadata.display_name || entityName} List
            </button>
          </div>
          <div class="bg-white shadow sm:rounded-lg">
            <div class="px-4 py-5 sm:px-6 flex justify-between items-center">
              <div>
                <h3 class="text-lg font-medium leading-6 text-gray-900">${metadata.display_name || entityName} Details</h3>
                <p class="mt-1 max-w-2xl text-sm text-gray-500">Record ID: ${recordId}</p>
              </div>
              <div>
                <a href="#dynamic/${entityName}/${recordId}/edit" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700">
                  <i class="ph ph-pencil mr-2"></i>
                  Edit
                </a>
              </div>
            </div>
            <div class="border-t border-gray-200 px-4 py-5 sm:px-6">
              <dl class="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
                ${this.renderRecordFields(record, metadata)}
              </dl>
            </div>
          </div>
        </div>
      `;
    } catch (error) {
      console.error('Error loading record:', error);
      container.innerHTML = `
        <div class="max-w-2xl mx-auto mt-8 p-6 bg-red-50 border border-red-200 rounded-lg">
          <h3 class="text-lg font-semibold text-red-900 mb-2">Error Loading Record</h3>
          <p class="text-red-700">${error.message}</p>
        </div>
      `;
    }
  }

  /**
   * Render edit form
   */
  async renderEdit(entityName, metadata, recordId, container) {
    try {
      const response = await apiFetch(`/dynamic-data/${entityName}/records/${recordId}`);

      if (!response.ok) {
        throw new Error('Failed to load record');
      }

      // Pass the full { id, data } API response so DynamicForm reads record.data[field]
      const result = await response.json();

      container.innerHTML = `
        <div class="px-4 sm:px-6 lg:px-8">
          <div class="mb-6">
            <button type="button" onclick="history.back()" class="inline-flex items-center text-sm font-medium text-gray-700 hover:text-gray-900">
              <i class="ph ph-arrow-left mr-2"></i>
              Back
            </button>
          </div>
          <div class="max-w-2xl">
            <h1 class="text-2xl font-semibold text-gray-900 mb-6">Edit ${metadata.display_name || entityName}</h1>
            <div id="dynamic-form-container"></div>
            <div class="mt-6 flex items-center justify-end gap-x-3">
              <button type="button" onclick="history.back()" class="rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50">
                Cancel
              </button>
              <button type="submit" form="dynamic-form" class="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500">
                Save Changes
              </button>
            </div>
          </div>
        </div>
      `;

      const formContainer = document.getElementById('dynamic-form-container');
      const form = new DynamicForm(formContainer, metadata, result);
      const formElement = form.render();

      // Handle form submission
      formElement.addEventListener('submit', async (e) => {
        e.preventDefault();

        try {
          const data = form.getValues();

          const response = await apiFetch(`/dynamic-data/${entityName}/records/${recordId}`, {
            method: 'PUT',
            body: JSON.stringify({ data })
          });

          if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to update record');
          }

          alert(`${metadata.display_name || entityName} updated successfully!`);
          window.location.hash = `dynamic/${entityName}/${recordId}`;
        } catch (error) {
          console.error('Error updating record:', error);
          alert(`Error: ${error.message}`);
        }
      });
    } catch (error) {
      console.error('Error loading record for edit:', error);
      container.innerHTML = `
        <div class="max-w-2xl mx-auto mt-8 p-6 bg-red-50 border border-red-200 rounded-lg">
          <h3 class="text-lg font-semibold text-red-900 mb-2">Error Loading Record</h3>
          <p class="text-red-700">${error.message}</p>
        </div>
      `;
    }
  }

  /**
   * Render record fields for detail view
   */
  renderRecordFields(record, metadata) {
    if (!metadata.form || !metadata.form.fields) {
      return Object.entries(record).map(([key, value]) => `
        <div class="sm:col-span-1">
          <dt class="text-sm font-medium text-gray-500">${key}</dt>
          <dd class="mt-1 text-sm text-gray-900">${value || '-'}</dd>
        </div>
      `).join('');
    }

    return metadata.form.fields.map(field => {
      const value = record[field.name];
      const displayValue = this.formatFieldValue(value, field);

      return `
        <div class="sm:col-span-1">
          <dt class="text-sm font-medium text-gray-500">${field.label || field.name}</dt>
          <dd class="mt-1 text-sm text-gray-900">${displayValue}</dd>
        </div>
      `;
    }).join('');
  }

  /**
   * Format field value for display
   */
  formatFieldValue(value, field) {
    if (value === null || value === undefined) {
      return '-';
    }

    switch (field.type) {
      case 'boolean':
        return value ? 'Yes' : 'No';
      case 'date':
        return new Date(value).toLocaleDateString();
      case 'datetime':
        return new Date(value).toLocaleString();
      case 'json':
        return '<pre class="text-xs">' + JSON.stringify(value, null, 2) + '</pre>';
      default:
        return value.toString();
    }
  }

  /**
   * Delete a record
   */
  async deleteRecord(entityName, recordId) {
    const metadata = this.entityMetadata.get(entityName);

    if (!confirm(`Are you sure you want to delete this ${metadata?.display_name || entityName} record?`)) {
      return;
    }

    try {
      const response = await apiFetch(`/dynamic-data/${entityName}/records/${recordId}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        throw new Error('Failed to delete record');
      }

      alert('Record deleted successfully!');

      // Reload list
      window.location.hash = `dynamic/${entityName}/list`;
    } catch (error) {
      console.error('Error deleting record:', error);
      alert(`Error: ${error.message}`);
    }
  }

  /**
   * Register all published entities on startup
   */
  async registerAllPublishedEntities() {
    try {
      console.log('Loading all published nocode entities...');

      const response = await apiFetch('/data-model/entities?status=published');

      if (!response.ok) {
        console.warn('Failed to load published entities');
        return;
      }

      const entities = await response.json();

      console.log(`Found ${entities.length} published entities`);

      // Register each entity
      for (const entity of entities) {
        try {
          await this.registerEntity(entity.name);
        } catch (error) {
          console.warn(`Skipping entity ${entity.name} - ${error.message}`);
          // Continue with next entity even if one fails
        }
      }

      console.log(`✅ Registered ${this.registeredEntities.size} nocode entities`);
    } catch (error) {
      console.error('Error loading published entities:', error);
    }
  }
}

// Create global instance
export const dynamicRouteRegistry = new DynamicRouteRegistry();

// Initialize on page load
if (typeof window !== 'undefined') {
  window.dynamicRouteRegistry = dynamicRouteRegistry;

  // Auto-load published entities when ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      dynamicRouteRegistry.registerAllPublishedEntities();
    });
  } else {
    dynamicRouteRegistry.registerAllPublishedEntities();
  }
}
