/**
 * Lookup Configuration Page
 *
 * Manages lookup tables and reference data
 *
 * Pattern: Template-based (similar to nocode-data-model.js)
 * - HTML template loaded from /assets/templates/nocode-lookups.html
 * - This script listens for 'route:loaded' event
 * - Initializes Lookup Configuration after template is in DOM
 */

import { authService } from './auth-service.js';
import { apiFetch } from './api.js';

let lookupsPage = null;

// Route change
document.addEventListener('route:loaded', async (event) => {
  if (event.detail.route === 'nocode-lookups') {
    // Ensure DOM from template is ready
    setTimeout(async () => {
      if (!lookupsPage) {
        lookupsPage = new LookupsPage();
      }
      await lookupsPage.init();
    }, 0);
  }
});

document.addEventListener('route:before-change', (event) => {
  if (event.detail.from === 'nocode-lookups' && lookupsPage) {
    lookupsPage.cleanup();
    lookupsPage = null;
  }
});

export class LookupsPage {
  constructor() {
    this.currentTab = 'lookups';
    this.lookups = [];
    this.cascadingRules = [];
    this.entities = [];
  }

  async init() {
    await this.loadLookups();
    await this.loadEntities();

    // Make methods available globally for onclick handlers
    window.LookupApp = {
      switchTab: (tab) => this.switchTab(tab),
      showCreateModal: () => this.showCreateModal(),
      closeCreateModal: () => this.closeCreateModal(),
      createLookup: (event) => this.createLookup(event),
      viewLookup: (id) => this.viewLookup(id),
      closeViewModal: () => this.closeViewModal(),
      testLookup: (id) => this.testLookup(id),
      deleteLookup: (id) => this.deleteLookup(id),
      editLookup: (id) => this.editLookup(id),
      viewData: (id) => this.viewData(id),
      showCreateCascadingModal: () => this.showCreateCascadingModal(),
      viewCascadingRule: (id) => this.viewCascadingRule(id),
      deleteCascadingRule: (id) => this.deleteCascadingRule(id),
      onSourceTypeChange: (sourceType) => this.onSourceTypeChange(sourceType)
    };
  }

  async loadEntities() {
    try {
      const response = await apiFetch('/data-model/entities', {
        headers: {
          'Authorization': `Bearer ${authService.getToken()}`
        }
      });

      if (response.ok) {
        this.entities = await response.json();
        this.populateEntitySelect();
      }
    } catch (error) {
      console.error('Error loading entities:', error);
    }
  }

  populateEntitySelect() {
    const select = document.getElementById('source_entity_select');
    if (!select) return;

    select.innerHTML = '<option value="">-- Select Entity --</option>';
    this.entities.forEach(entity => {
      const option = document.createElement('option');
      option.value = entity.id;
      option.textContent = entity.display_name || entity.name;
      select.appendChild(option);
    });
  }

  onSourceTypeChange(sourceType) {
    // Hide all source type field sections
    document.querySelectorAll('.source-type-fields').forEach(section => {
      section.classList.add('hidden');
    });

    // Show the relevant section
    switch (sourceType) {
      case 'entity':
        document.getElementById('entity-fields')?.classList.remove('hidden');
        break;
      case 'static_list':
        document.getElementById('static-list-fields')?.classList.remove('hidden');
        break;
      case 'custom_query':
        document.getElementById('custom-query-fields')?.classList.remove('hidden');
        break;
      case 'api':
        document.getElementById('api-fields')?.classList.remove('hidden');
        break;
    }
  }

  switchTab(tab) {
    this.currentTab = tab;

    // Update tab styles
    document.querySelectorAll('.lookup-tab').forEach(t => {
      t.classList.remove('border-orange-600', 'text-orange-600');
      t.classList.add('border-transparent', 'text-gray-500');
    });
    document.getElementById(`tab-${tab}`).classList.remove('border-transparent', 'text-gray-500');
    document.getElementById(`tab-${tab}`).classList.add('border-orange-600', 'text-orange-600');

    // Show/hide content
    document.getElementById('content-lookups').classList.toggle('hidden', tab !== 'lookups');
    document.getElementById('content-cascading').classList.toggle('hidden', tab !== 'cascading');

    if (tab === 'cascading') {
      this.loadCascadingRules();
    }
  }

  async loadLookups() {
    try {
      const response = await apiFetch('/lookups/configurations', {
        headers: {
          'Authorization': `Bearer ${authService.getToken()}`
        }
      });

      if (response.ok) {
        this.lookups = await response.json();
        this.renderLookups();
      } else {
        this.showError('Failed to load lookup configurations');
      }
    } catch (error) {
      console.error('Error loading lookups:', error);
      this.showError('Error loading lookup configurations');
    }
  }

  renderLookups() {
    const container = document.getElementById('lookups-list');

    if (this.lookups.length === 0) {
      container.innerHTML = `
        <div class="col-span-full text-center py-12">
          <i class="ph-duotone ph-list-magnifying-glass text-6xl text-gray-300"></i>
          <h3 class="mt-4 text-lg font-medium text-gray-900">No lookup configurations yet</h3>
          <p class="mt-2 text-gray-500">Create your first lookup configuration to get started</p>
          <button onclick="LookupApp.showCreateModal()" class="mt-4 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700">
            <i class="ph ph-plus"></i> Create Lookup
          </button>
        </div>
      `;
      return;
    }

    container.innerHTML = this.lookups.map(lookup => `
      <div class="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-lg transition">
        <div class="flex items-start justify-between mb-3">
          <div class="flex-1">
            <div class="flex items-center gap-2 mb-1">
              <h3 class="text-lg font-semibold text-gray-900">${this.escapeHtml(lookup.label)}</h3>
              ${lookup.tenant_id === null ? '<span class="px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs font-medium">Platform</span>' : ''}
            </div>
            <p class="text-sm text-gray-500 mt-1">${this.escapeHtml(lookup.description || 'No description')}</p>
          </div>
          <span class="ml-2 px-3 py-1 rounded-full text-xs font-medium ${lookup.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}">
            ${lookup.is_active ? 'Active' : 'Inactive'}
          </span>
        </div>

        <div class="space-y-2 text-sm text-gray-600 mb-4">
          <div class="flex items-center gap-2">
            <i class="ph ph-database"></i>
            <span>Source: ${lookup.source_type}</span>
          </div>
          <div class="flex items-center gap-2">
            <i class="ph ph-text-columns"></i>
            <span>Display: ${lookup.display_field || 'N/A'}</span>
          </div>
          <div class="flex items-center gap-2">
            <i class="ph ph-key"></i>
            <span>Value: ${lookup.value_field || 'id'}</span>
          </div>
          ${lookup.enable_search ? `
            <div class="flex items-center gap-2">
              <i class="ph ph-magnifying-glass"></i>
              <span>Searchable</span>
            </div>
          ` : ''}
          ${lookup.enable_caching ? `
            <div class="flex items-center gap-2">
              <i class="ph ph-clock-clockwise"></i>
              <span>Cached (${lookup.cache_ttl_seconds || 3600}s)</span>
            </div>
          ` : ''}
        </div>

        <div class="flex gap-2">
          <button onclick="LookupApp.viewLookup('${lookup.id}')" class="flex-1 px-3 py-2 bg-orange-50 text-orange-700 rounded-lg hover:bg-orange-100 text-sm font-medium">
            <i class="ph ph-eye"></i> View
          </button>
          <button onclick="LookupApp.testLookup('${lookup.id}')" class="flex-1 px-3 py-2 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 text-sm font-medium">
            <i class="ph ph-play"></i> Test
          </button>
          <button onclick="LookupApp.deleteLookup('${lookup.id}')" class="px-3 py-2 bg-red-50 text-red-700 rounded-lg hover:bg-red-100 text-sm">
            <i class="ph ph-trash"></i>
          </button>
        </div>
      </div>
    `).join('');
  }

  async loadCascadingRules() {
    try {
      const response = await apiFetch('/lookups/cascading-rules', {
        headers: {
          'Authorization': `Bearer ${authService.getToken()}`
        }
      });

      if (response.ok) {
        this.cascadingRules = await response.json();
        this.renderCascadingRules();
      }
    } catch (error) {
      console.error('Error loading cascading rules:', error);
    }
  }

  renderCascadingRules() {
    const tbody = document.getElementById('cascading-tbody');

    if (this.cascadingRules.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="5" class="px-6 py-12 text-center text-gray-500">No cascading rules configured</td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = this.cascadingRules.map(rule => `
      <tr class="hover:bg-gray-50">
        <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
          ${this.escapeHtml(rule.name)}
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
          ${rule.parent_lookup_name || 'Unknown'}
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
          ${rule.child_lookup_name || 'Unknown'}
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
          <span class="px-2 py-1 text-xs font-medium rounded-full ${rule.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}">
            ${rule.is_active ? 'Active' : 'Inactive'}
          </span>
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-sm">
          <button onclick="LookupApp.viewCascadingRule('${rule.id}')" class="text-orange-600 hover:text-orange-900 mr-3">
            <i class="ph ph-eye"></i> View
          </button>
          <button onclick="LookupApp.deleteCascadingRule('${rule.id}')" class="text-red-600 hover:text-red-900">
            <i class="ph ph-trash"></i>
          </button>
        </td>
      </tr>
    `).join('');
  }

  showCreateModal() {
    // Reset the form first
    document.getElementById('createLookupForm').reset();
    // Reset to default source type (entity) field visibility
    this.onSourceTypeChange('entity');
    // Show the modal
    document.getElementById('createLookupModal').classList.remove('hidden');
  }

  closeCreateModal() {
    document.getElementById('createLookupModal').classList.add('hidden');
    document.getElementById('createLookupForm').reset();
    // Reset source type fields to default (entity)
    this.onSourceTypeChange('entity');
  }

  async createLookup(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const sourceType = formData.get('source_type');

    // Base data
    const data = {
      name: formData.get('name'),
      label: formData.get('label'),
      description: formData.get('description') || '',
      source_type: sourceType,
      enable_search: formData.get('enable_search') === 'on',
      enable_caching: formData.get('enable_caching') === 'on',
      is_active: true
    };

    // Add source-type specific fields
    switch (sourceType) {
      case 'entity':
        const entityId = formData.get('source_entity_id');
        if (!entityId) {
          this.showError('Please select a source entity');
          return;
        }
        data.source_entity_id = entityId;
        data.display_field = formData.get('display_field') || 'name';
        data.value_field = formData.get('value_field') || 'id';
        break;

      case 'static_list':
        const staticOptionsRaw = formData.get('static_options');
        if (!staticOptionsRaw || !staticOptionsRaw.trim()) {
          this.showError('Please enter static options JSON');
          return;
        }
        try {
          const staticOptions = JSON.parse(staticOptionsRaw);
          if (!Array.isArray(staticOptions)) {
            this.showError('Static options must be a JSON array');
            return;
          }
          // Validate each option has value and label
          for (const opt of staticOptions) {
            if (!opt.value || !opt.label) {
              this.showError('Each option must have "value" and "label" properties');
              return;
            }
          }
          data.static_options = staticOptions;
          // For static lists, set display/value fields to label/value
          data.display_field = 'label';
          data.value_field = 'value';
        } catch (e) {
          this.showError('Invalid JSON format for static options: ' + e.message);
          return;
        }
        break;

      case 'custom_query':
        const customQuery = formData.get('custom_query');
        if (!customQuery || !customQuery.trim()) {
          this.showError('Please enter a SQL query');
          return;
        }
        data.custom_query = customQuery;
        // Parse query parameters if provided
        const queryParamsRaw = formData.get('query_parameters');
        if (queryParamsRaw && queryParamsRaw.trim()) {
          try {
            data.query_parameters = JSON.parse(queryParamsRaw);
          } catch (e) {
            this.showError('Invalid JSON format for query parameters: ' + e.message);
            return;
          }
        }
        data.display_field = 'label';
        data.value_field = 'value';
        break;

      case 'api':
        const apiEndpoint = formData.get('api_endpoint');
        if (!apiEndpoint || !apiEndpoint.trim()) {
          this.showError('Please enter an API endpoint');
          return;
        }
        data.api_endpoint = apiEndpoint;
        data.api_method = formData.get('api_method') || 'GET';

        // Parse API headers if provided
        const apiHeadersRaw = formData.get('api_headers');
        if (apiHeadersRaw && apiHeadersRaw.trim()) {
          try {
            data.api_headers = JSON.parse(apiHeadersRaw);
          } catch (e) {
            this.showError('Invalid JSON format for API headers: ' + e.message);
            return;
          }
        }

        // Parse response mapping if provided
        const apiMappingRaw = formData.get('api_response_mapping');
        if (apiMappingRaw && apiMappingRaw.trim()) {
          try {
            data.api_response_mapping = JSON.parse(apiMappingRaw);
          } catch (e) {
            this.showError('Invalid JSON format for response mapping: ' + e.message);
            return;
          }
        }
        data.display_field = 'label';
        data.value_field = 'value';
        break;
    }

    try {
      const response = await apiFetch('/lookups/configurations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authService.getToken()}`
        },
        body: JSON.stringify(data)
      });

      if (response.ok) {
        this.closeCreateModal();
        await this.loadLookups();
        this.showSuccess('Lookup configuration created successfully');
      } else {
        const error = await response.json();
        this.showError(error.detail || 'Failed to create lookup configuration');
      }
    } catch (error) {
      console.error('Error creating lookup:', error);
      this.showError('Error creating lookup configuration');
    }
  }

  async viewLookup(id) {
    try {
      const response = await apiFetch(`/lookups/configurations/${id}`, {
        headers: {
          'Authorization': `Bearer ${authService.getToken()}`
        }
      });

      if (response.ok) {
        const lookup = await response.json();
        document.getElementById('viewLookupTitle').textContent = lookup.label;
        document.getElementById('viewLookupContent').innerHTML = `
          <div class="space-y-6">
            <div>
              <h4 class="font-semibold text-gray-900 mb-2">Basic Information</h4>
              <dl class="grid grid-cols-2 gap-4">
                <div>
                  <dt class="text-sm text-gray-500">Name</dt>
                  <dd class="text-sm font-medium text-gray-900">${this.escapeHtml(lookup.name)}</dd>
                </div>
                <div>
                  <dt class="text-sm text-gray-500">Source Type</dt>
                  <dd class="text-sm font-medium text-gray-900">${lookup.source_type}</dd>
                </div>
                <div>
                  <dt class="text-sm text-gray-500">Display Field</dt>
                  <dd class="text-sm font-medium text-gray-900">${lookup.display_field || 'N/A'}</dd>
                </div>
                <div>
                  <dt class="text-sm text-gray-500">Value Field</dt>
                  <dd class="text-sm font-medium text-gray-900">${lookup.value_field || 'id'}</dd>
                </div>
              </dl>
            </div>

            <div>
              <h4 class="font-semibold text-gray-900 mb-2">Features</h4>
              <div class="grid grid-cols-2 gap-4">
                <div class="flex items-center gap-2">
                  <i class="ph ph-${lookup.enable_search ? 'check-circle text-green-600' : 'x-circle text-gray-400'}"></i>
                  <span class="text-sm">Search ${lookup.enable_search ? 'Enabled' : 'Disabled'}</span>
                </div>
                <div class="flex items-center gap-2">
                  <i class="ph ph-${lookup.enable_caching ? 'check-circle text-green-600' : 'x-circle text-gray-400'}"></i>
                  <span class="text-sm">Caching ${lookup.enable_caching ? 'Enabled' : 'Disabled'}</span>
                </div>
                <div class="flex items-center gap-2">
                  <i class="ph ph-${lookup.allow_multiple ? 'check-circle text-green-600' : 'x-circle text-gray-400'}"></i>
                  <span class="text-sm">Multiple Selection ${lookup.allow_multiple ? 'Enabled' : 'Disabled'}</span>
                </div>
                <div class="flex items-center gap-2">
                  <i class="ph ph-${lookup.lazy_load ? 'check-circle text-green-600' : 'x-circle text-gray-400'}"></i>
                  <span class="text-sm">Lazy Load ${lookup.lazy_load ? 'Enabled' : 'Disabled'}</span>
                </div>
              </div>
            </div>

            ${lookup.description ? `
              <div>
                <h4 class="font-semibold text-gray-900 mb-2">Description</h4>
                <p class="text-sm text-gray-600">${this.escapeHtml(lookup.description)}</p>
              </div>
            ` : ''}

            <div class="flex gap-3 pt-4 border-t">
              <button onclick="LookupApp.editLookup('${lookup.id}')" class="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700">
                <i class="ph ph-pencil"></i> Edit Configuration
              </button>
              <button onclick="LookupApp.viewData('${lookup.id}')" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                <i class="ph ph-eye"></i> View Data
              </button>
            </div>
          </div>
        `;
        document.getElementById('viewLookupModal').classList.remove('hidden');
      }
    } catch (error) {
      console.error('Error loading lookup:', error);
      this.showError('Error loading lookup details');
    }
  }

  closeViewModal() {
    document.getElementById('viewLookupModal').classList.add('hidden');
  }

  async testLookup(id) {
    try {
      const response = await apiFetch(`/lookups/configurations/${id}/data`, {
        headers: {
          'Authorization': `Bearer ${authService.getToken()}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        this.showSuccess(`Lookup test successful! Retrieved ${data.length} items.`);
      } else {
        this.showError('Failed to retrieve lookup data');
      }
    } catch (error) {
      console.error('Error testing lookup:', error);
      this.showError('Error testing lookup');
    }
  }

  async deleteLookup(id) {
    if (!confirm('Are you sure you want to delete this lookup configuration?')) return;

    try {
      const response = await apiFetch(`/lookups/configurations/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${authService.getToken()}`
        }
      });

      if (response.ok) {
        await this.loadLookups();
        this.showSuccess('Lookup configuration deleted successfully');
      } else {
        this.showError('Failed to delete lookup configuration');
      }
    } catch (error) {
      console.error('Error deleting lookup:', error);
      this.showError('Error deleting lookup configuration');
    }
  }

  editLookup(id) {
    this.showError('Edit feature coming soon - will open configuration editor');
  }

  viewData(id) {
    this.showError('Data viewer coming soon - will display lookup options');
  }

  showCreateCascadingModal() {
    this.showError('Cascading rule creation UI coming soon');
  }

  viewCascadingRule(id) {
    this.showError('Cascading rule detail view coming soon');
  }

  deleteCascadingRule(id) {
    this.showError('Cascading rule deletion coming soon');
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
    delete window.LookupApp;
  }
}
