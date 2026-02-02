/**
 * Automation Rules Page
 *
 * Manages automation rules and workflows without writing code
 *
 * Pattern: Template-based (similar to nocode-data-model.js)
 * - HTML template loaded from /assets/templates/nocode-automations.html
 * - This script listens for 'route:loaded' event
 * - Initializes Automation Rules page after template is in DOM
 */

import { authService } from './auth-service.js';
import { apiFetch } from './api.js';

let automationsPage = null;

// Route change
document.addEventListener('route:loaded', async (event) => {
  if (event.detail.route === 'nocode-automations') {
    // Ensure DOM from template is ready
    setTimeout(async () => {
      if (!automationsPage) {
        automationsPage = new AutomationsPage();
      }
      await automationsPage.init();
    }, 0);
  }
});

document.addEventListener('route:before-change', (event) => {
  if (event.detail.from === 'nocode-automations' && automationsPage) {
    automationsPage.cleanup();
    automationsPage = null;
  }
});

export class AutomationsPage {
  constructor() {
    this.currentTab = 'rules';
    this.rules = [];
    this.executions = [];
    this.webhooks = [];
    this.entities = [];
    this.workflows = [];
    this.conditionGroups = [];
    this.currentEntityFields = [];
    this.actions = [];
  }

  async init() {
    await this.loadRules();

    // Make methods available globally for onclick handlers
    window.AutomationApp = {
      switchTab: (tab) => this.switchTab(tab),
      showCreateModal: () => this.showCreateModal(),
      closeCreateModal: () => this.closeCreateModal(),
      createRule: (event) => this.createRule(event),
      viewRule: (id) => this.viewRule(id),
      closeViewModal: () => this.closeViewModal(),
      toggleActive: (id, isActive) => this.toggleActive(id, isActive),
      testRule: (id) => this.testRule(id),
      deleteRule: (id) => this.deleteRule(id),
      editRule: (id) => this.editRule(id),
      viewExecution: (id) => this.viewExecution(id),
      showCreateWebhookModal: () => this.showCreateWebhookModal(),
      viewWebhook: (id) => this.viewWebhook(id),
      deleteWebhook: (id) => this.deleteWebhook(id),
      closeRuleBuilder: () => this.closeRuleBuilder(),
      closeExecutionDetail: () => this.closeExecutionDetail(),
      closeCreateWebhookModal: () => this.closeCreateWebhookModal(),
      openVisualConditionBuilder: (id) => this.openVisualConditionBuilder(id),
      closeVisualConditionBuilder: () => this.closeVisualConditionBuilder(),
      addConditionGroup: () => this.addConditionGroup(),
      addCondition: (groupId) => this.addCondition(groupId),
      removeCondition: (groupId, condId) => this.removeCondition(groupId, condId),
      removeConditionGroup: (groupId) => this.removeConditionGroup(groupId),
      saveConditions: () => this.saveConditions(),
      openVisualActionBuilder: (id) => this.openVisualActionBuilder(id),
      closeVisualActionBuilder: () => this.closeVisualActionBuilder(),
      addAction: () => this.addAction(),
      removeAction: (actionId) => this.removeAction(actionId),
      moveActionUp: (actionId) => this.moveActionUp(actionId),
      moveActionDown: (actionId) => this.moveActionDown(actionId),
      saveActions: () => this.saveActions(),
      openActionLibrary: () => this.openActionLibrary(),
      closeActionLibrary: () => this.closeActionLibrary(),
      applyTemplate: (template) => this.applyTemplate(template),
      openScheduleBuilder: (id) => this.openScheduleBuilder(id),
      closeScheduleBuilder: () => this.closeScheduleBuilder(),
      saveSchedule: () => this.saveSchedule(),
      openMonitoringDashboard: () => this.openMonitoringDashboard(),
      closeMonitoringDashboard: () => this.closeMonitoringDashboard(),
      onTriggerTypeChange: (type) => this.onTriggerTypeChange(type),
      onScheduleTypeChange: (type) => this.onScheduleTypeChange(type),
      onEntityChange: (entityId) => this.onEntityChange(entityId),
      onActionTypeChange: (idx, type) => this.onActionTypeChange(idx, type)
    };

    // Load entities and workflows for the action builder
    await this.loadEntities();
    await this.loadWorkflows();
  }

  async loadWorkflows() {
    try {
      const response = await apiFetch('/workflows/', {
        headers: {
          'Authorization': `Bearer ${authService.getToken()}`
        }
      });

      if (response.ok) {
        this.workflows = await response.json();
      }
    } catch (error) {
      console.error('Error loading workflows:', error);
    }
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
    const select = document.getElementById('automationEntitySelect');
    if (!select) return;

    select.innerHTML = '<option value="">Select entity...</option>';
    this.entities.forEach(entity => {
      const option = document.createElement('option');
      option.value = entity.id;
      option.textContent = entity.display_name || entity.name;
      select.appendChild(option);
    });
  }

  onTriggerTypeChange(type) {
    const databaseOptions = document.getElementById('databaseEventOptions');
    const scheduledOptions = document.getElementById('scheduledOptions');
    const webhookOptions = document.getElementById('webhookOptions');

    // Hide all
    databaseOptions?.classList.add('hidden');
    scheduledOptions?.classList.add('hidden');
    webhookOptions?.classList.add('hidden');

    // Show relevant
    switch (type) {
      case 'database':
        databaseOptions?.classList.remove('hidden');
        break;
      case 'scheduled':
        scheduledOptions?.classList.remove('hidden');
        break;
      case 'webhook':
        webhookOptions?.classList.remove('hidden');
        break;
    }
  }

  onScheduleTypeChange(type) {
    const intervalOptions = document.getElementById('intervalOptions');
    const cronOptions = document.getElementById('cronOptions');

    if (type === 'cron') {
      intervalOptions?.classList.add('hidden');
      cronOptions?.classList.remove('hidden');
    } else {
      intervalOptions?.classList.remove('hidden');
      cronOptions?.classList.add('hidden');
    }
  }

  async onEntityChange(entityId) {
    const watchFieldsSelect = document.getElementById('watchFieldsSelect');
    if (!watchFieldsSelect) return;

    // Reset watch fields
    watchFieldsSelect.innerHTML = '';

    if (!entityId) {
      watchFieldsSelect.innerHTML = '<option value="" disabled>Select entity first...</option>';
      this.currentEntityFields = [];
      return;
    }

    try {
      const response = await apiFetch(`/data-model/entities/${entityId}/fields`, {
        headers: { 'Authorization': `Bearer ${authService.getToken()}` }
      });

      if (response.ok) {
        const fields = await response.json();
        this.currentEntityFields = fields;

        if (fields.length === 0) {
          watchFieldsSelect.innerHTML = '<option value="" disabled>No fields available</option>';
        } else {
          fields.forEach(field => {
            const option = document.createElement('option');
            option.value = field.name;
            option.textContent = field.label || field.name;
            watchFieldsSelect.appendChild(option);
          });
        }
      }
    } catch (error) {
      console.error('Error loading entity fields:', error);
      watchFieldsSelect.innerHTML = '<option value="" disabled>Error loading fields</option>';
    }
  }

  switchTab(tab) {
    this.currentTab = tab;

    // Update tab styles
    document.querySelectorAll('.automation-tab').forEach(t => {
      t.classList.remove('border-green-600', 'text-green-600');
      t.classList.add('border-transparent', 'text-gray-500');
    });
    document.getElementById(`tab-${tab}`).classList.remove('border-transparent', 'text-gray-500');
    document.getElementById(`tab-${tab}`).classList.add('border-green-600', 'text-green-600');

    // Show/hide content
    document.getElementById('content-rules').classList.toggle('hidden', tab !== 'rules');
    document.getElementById('content-executions').classList.toggle('hidden', tab !== 'executions');
    document.getElementById('content-webhooks').classList.toggle('hidden', tab !== 'webhooks');

    if (tab === 'executions') {
      this.loadExecutions();
    } else if (tab === 'webhooks') {
      this.loadWebhooks();
    }
  }

  async loadRules() {
    try {
      const response = await apiFetch('/automations/rules', {
        headers: {
          'Authorization': `Bearer ${authService.getToken()}`
        }
      });

      if (response.ok) {
        this.rules = await response.json();
        this.renderRules();
      } else {
        this.showError('Failed to load automation rules');
      }
    } catch (error) {
      console.error('Error loading rules:', error);
      this.showError('Error loading automation rules');
    }
  }

  renderRules() {
    const container = document.getElementById('rules-list');

    if (this.rules.length === 0) {
      container.innerHTML = `
        <div class="col-span-full text-center py-12">
          <i class="ph-duotone ph-robot text-6xl text-gray-300"></i>
          <h3 class="mt-4 text-lg font-medium text-gray-900">No automation rules yet</h3>
          <p class="mt-2 text-gray-500">Create your first automation rule to get started</p>
          <button onclick="AutomationApp.showCreateModal()" class="mt-4 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
            <i class="ph ph-plus"></i> Create Rule
          </button>
        </div>
      `;
      return;
    }

    container.innerHTML = this.rules.map(rule => `
      <div class="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-lg transition">
        <div class="flex items-start justify-between mb-3">
          <div class="flex-1">
            <div class="flex items-center gap-2 mb-1">
              <h3 class="text-lg font-semibold text-gray-900">${this.escapeHtml(rule.label)}</h3>
              ${rule.tenant_id === null ? '<span class="px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs font-medium">Platform</span>' : ''}
            </div>
            <p class="text-sm text-gray-500 mt-1">${this.escapeHtml(rule.description || 'No description')}</p>
          </div>
          <div class="ml-2 flex flex-col gap-2">
            <span class="px-3 py-1 rounded-full text-xs font-medium ${rule.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}">
              ${rule.is_active ? 'Active' : 'Inactive'}
            </span>
            ${rule.is_test_mode ? '<span class="px-3 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">Test Mode</span>' : ''}
          </div>
        </div>

        <div class="space-y-2 text-sm text-gray-600 mb-4">
          <div class="flex items-center gap-2">
            <i class="ph ph-lightning"></i>
            <span>Trigger: ${rule.trigger_type}</span>
          </div>
          <div class="flex items-center gap-2">
            <i class="ph ph-tag"></i>
            <span>${rule.category || 'Uncategorized'}</span>
          </div>
          <div class="flex items-center gap-2">
            <i class="ph ph-chart-line"></i>
            <span>${rule.total_executions || 0} executions (${rule.successful_executions || 0} successful)</span>
          </div>
        </div>

        <div class="flex gap-2">
          <button onclick="AutomationApp.viewRule('${rule.id}')" class="flex-1 px-3 py-2 bg-green-50 text-green-700 rounded-lg hover:bg-green-100 text-sm font-medium">
            <i class="ph ph-eye"></i> View
          </button>
          <button onclick="AutomationApp.toggleActive('${rule.id}', ${rule.is_active})" class="flex-1 px-3 py-2 bg-gray-50 text-gray-700 rounded-lg hover:bg-gray-100 text-sm font-medium">
            <i class="ph ph-${rule.is_active ? 'pause' : 'play'}"></i> ${rule.is_active ? 'Disable' : 'Enable'}
          </button>
          <button onclick="AutomationApp.testRule('${rule.id}')" class="px-3 py-2 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 text-sm">
            <i class="ph ph-play"></i> Test
          </button>
          <button onclick="AutomationApp.deleteRule('${rule.id}')" class="px-3 py-2 bg-red-50 text-red-700 rounded-lg hover:bg-red-100 text-sm">
            <i class="ph ph-trash"></i>
          </button>
        </div>
      </div>
    `).join('');
  }

  async loadExecutions() {
    try {
      const response = await apiFetch('/automations/executions', {
        headers: {
          'Authorization': `Bearer ${authService.getToken()}`
        }
      });

      if (response.ok) {
        this.executions = await response.json();
        this.renderExecutions();
      }
    } catch (error) {
      console.error('Error loading executions:', error);
    }
  }

  renderExecutions() {
    const tbody = document.getElementById('executions-tbody');

    if (this.executions.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="6" class="px-6 py-12 text-center text-gray-500">No execution history available</td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = this.executions.map(exec => `
      <tr class="hover:bg-gray-50">
        <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
          ${exec.rule_name || 'Unknown'}
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
          ${exec.trigger_type}
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
          <span class="px-2 py-1 text-xs font-medium rounded-full ${this.getExecutionStatusClass(exec.status)}">
            ${exec.status}
          </span>
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
          ${new Date(exec.triggered_at).toLocaleString()}
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
          ${exec.execution_time_ms ? exec.execution_time_ms + 'ms' : 'N/A'}
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-sm">
          <button onclick="AutomationApp.viewExecution('${exec.id}')" class="text-green-600 hover:text-green-900">
            <i class="ph ph-eye"></i> View
          </button>
        </td>
      </tr>
    `).join('');
  }

  async loadWebhooks() {
    try {
      const response = await apiFetch('/automations/webhooks', {
        headers: {
          'Authorization': `Bearer ${authService.getToken()}`
        }
      });

      if (response.ok) {
        this.webhooks = await response.json();
        this.renderWebhooks();
      }
    } catch (error) {
      console.error('Error loading webhooks:', error);
    }
  }

  renderWebhooks() {
    const container = document.getElementById('webhooks-list');

    if (this.webhooks.length === 0) {
      container.innerHTML = `
        <div class="col-span-full text-center py-12">
          <i class="ph-duotone ph-webhooks-logo text-6xl text-gray-300"></i>
          <h3 class="mt-4 text-lg font-medium text-gray-900">No webhooks configured</h3>
          <p class="mt-2 text-gray-500">Create a webhook to receive or send data</p>
          <button onclick="AutomationApp.showCreateWebhookModal()" class="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            <i class="ph ph-plus"></i> Create Webhook
          </button>
        </div>
      `;
      return;
    }

    container.innerHTML = this.webhooks.map(webhook => `
      <div class="bg-white border border-gray-200 rounded-lg p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-2">${this.escapeHtml(webhook.label)}</h3>
        <p class="text-sm text-gray-500 mb-4">${this.escapeHtml(webhook.description || 'No description')}</p>
        <div class="space-y-2 text-sm">
          <div class="flex items-center gap-2 text-gray-600">
            <i class="ph ph-arrows-left-right"></i>
            <span>Type: ${webhook.webhook_type}</span>
          </div>
          <div class="flex items-center gap-2 text-gray-600">
            <i class="ph ph-chart-line"></i>
            <span>${webhook.total_calls || 0} calls (${webhook.successful_calls || 0} successful)</span>
          </div>
        </div>
        <div class="mt-4 flex gap-2">
          <button onclick="AutomationApp.viewWebhook('${webhook.id}')" class="flex-1 px-3 py-2 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 text-sm">
            <i class="ph ph-eye"></i> View
          </button>
          <button onclick="AutomationApp.deleteWebhook('${webhook.id}')" class="px-3 py-2 bg-red-50 text-red-700 rounded-lg hover:bg-red-100 text-sm">
            <i class="ph ph-trash"></i>
          </button>
        </div>
      </div>
    `).join('');
  }

  getExecutionStatusClass(status) {
    const classes = {
      'pending': 'bg-yellow-100 text-yellow-800',
      'running': 'bg-blue-100 text-blue-800',
      'completed': 'bg-green-100 text-green-800',
      'failed': 'bg-red-100 text-red-800'
    };
    return classes[status] || 'bg-gray-100 text-gray-800';
  }

  showCreateModal() {
    const modal = document.getElementById('createRuleModal');
    const form = document.getElementById('createRuleForm');
    if (form) form.reset();

    // Reset trigger type visibility
    this.onTriggerTypeChange('database');
    this.onScheduleTypeChange('interval');

    // Repopulate entity select
    this.populateEntitySelect();

    // Reset watch fields
    const watchFieldsSelect = document.getElementById('watchFieldsSelect');
    if (watchFieldsSelect) {
      watchFieldsSelect.innerHTML = '<option value="" disabled>Select entity first...</option>';
    }
    this.currentEntityFields = [];

    if (modal) modal.classList.remove('hidden');
  }

  closeCreateModal() {
    document.getElementById('createRuleModal').classList.add('hidden');
    document.getElementById('createRuleForm').reset();
  }

  async createRule(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const triggerType = formData.get('trigger_type');

    // Build trigger config based on trigger type
    let triggerConfig = {};

    switch (triggerType) {
      case 'database':
        // Get selected watch fields from multi-select
        const watchFieldsSelect = document.getElementById('watchFieldsSelect');
        const selectedWatchFields = watchFieldsSelect
          ? Array.from(watchFieldsSelect.selectedOptions).map(opt => opt.value)
          : [];

        triggerConfig = {
          event: formData.get('event_type'),
          entity_id: formData.get('entity_id') || null,
          watch_fields: selectedWatchFields
        };
        break;
      case 'scheduled':
        const scheduleType = formData.get('schedule_type');
        if (scheduleType === 'cron') {
          triggerConfig = {
            schedule_type: 'cron',
            cron_expression: formData.get('cron_expression')
          };
        } else {
          triggerConfig = {
            schedule_type: 'interval',
            interval_value: parseInt(formData.get('interval_value')) || 1,
            interval_unit: formData.get('interval_unit') || 'hours'
          };
        }
        break;
      case 'webhook':
        triggerConfig = {
          // Webhook URL will be generated by backend
        };
        break;
    }

    const data = {
      name: formData.get('name'),
      label: formData.get('label'),
      description: formData.get('description') || '',
      category: formData.get('category') || '',
      trigger_type: triggerType,
      trigger_config: triggerConfig,
      execution_config: {
        run_async: formData.get('run_async') === 'on',
        max_retries: parseInt(formData.get('max_retries')) || 3,
        timeout_seconds: parseInt(formData.get('timeout_seconds')) || 30
      },
      actions: [],
      is_active: formData.get('is_active') === 'on'
    };

    try {
      const response = await apiFetch('/automations/rules', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authService.getToken()}`
        },
        body: JSON.stringify(data)
      });

      if (response.ok) {
        this.closeCreateModal();
        await this.loadRules();
        this.showSuccess('Automation rule created successfully');
      } else {
        const error = await response.json();
        this.showError(error.detail || 'Failed to create automation rule');
      }
    } catch (error) {
      console.error('Error creating rule:', error);
      this.showError('Error creating automation rule');
    }
  }

  async viewRule(id) {
    try {
      const response = await apiFetch(`/automations/rules/${id}`, {
        headers: {
          'Authorization': `Bearer ${authService.getToken()}`
        }
      });

      if (response.ok) {
        const rule = await response.json();
        document.getElementById('viewRuleTitle').textContent = rule.label;
        document.getElementById('viewRuleContent').innerHTML = `
          <div class="space-y-6">
            <div>
              <h4 class="font-semibold text-gray-900 mb-2">Basic Information</h4>
              <dl class="grid grid-cols-2 gap-4">
                <div>
                  <dt class="text-sm text-gray-500">Name</dt>
                  <dd class="text-sm font-medium text-gray-900">${this.escapeHtml(rule.name)}</dd>
                </div>
                <div>
                  <dt class="text-sm text-gray-500">Category</dt>
                  <dd class="text-sm font-medium text-gray-900">${this.escapeHtml(rule.category || 'N/A')}</dd>
                </div>
                <div>
                  <dt class="text-sm text-gray-500">Trigger Type</dt>
                  <dd class="text-sm font-medium text-gray-900">${rule.trigger_type}</dd>
                </div>
                <div>
                  <dt class="text-sm text-gray-500">Status</dt>
                  <dd class="text-sm font-medium text-gray-900">${rule.is_active ? 'Active' : 'Inactive'}</dd>
                </div>
              </dl>
            </div>

            <div>
              <h4 class="font-semibold text-gray-900 mb-2">Statistics</h4>
              <dl class="grid grid-cols-3 gap-4">
                <div>
                  <dt class="text-sm text-gray-500">Total Executions</dt>
                  <dd class="text-sm font-medium text-gray-900">${rule.total_executions || 0}</dd>
                </div>
                <div>
                  <dt class="text-sm text-gray-500">Successful</dt>
                  <dd class="text-sm font-medium text-green-600">${rule.successful_executions || 0}</dd>
                </div>
                <div>
                  <dt class="text-sm text-gray-500">Failed</dt>
                  <dd class="text-sm font-medium text-red-600">${rule.failed_executions || 0}</dd>
                </div>
              </dl>
            </div>

            ${rule.description ? `
              <div>
                <h4 class="font-semibold text-gray-900 mb-2">Description</h4>
                <p class="text-sm text-gray-600">${this.escapeHtml(rule.description)}</p>
              </div>
            ` : ''}

            <div class="space-y-3 pt-4 border-t">
              <div class="flex gap-3">
                <button onclick="AutomationApp.openVisualConditionBuilder('${rule.id}')" class="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center justify-center gap-2">
                  <i class="ph ph-tree-structure"></i> Condition Builder
                </button>
                <button onclick="AutomationApp.openVisualActionBuilder('${rule.id}')" class="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 flex items-center justify-center gap-2">
                  <i class="ph ph-steps"></i> Action Builder
                </button>
                <button onclick="AutomationApp.openScheduleBuilder('${rule.id}')" class="flex-1 px-4 py-2 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 flex items-center justify-center gap-2">
                  <i class="ph ph-clock"></i> Schedule
                </button>
              </div>
              <div class="flex gap-3">
                <button onclick="AutomationApp.editRule('${rule.id}')" class="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
                  <i class="ph ph-pencil"></i> Edit Rule
                </button>
                <button onclick="AutomationApp.testRule('${rule.id}')" class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                  <i class="ph ph-play"></i> Test Run
                </button>
              </div>
            </div>
          </div>
        `;
        document.getElementById('viewRuleModal').classList.remove('hidden');
      }
    } catch (error) {
      console.error('Error loading rule:', error);
      this.showError('Error loading rule details');
    }
  }

  closeViewModal() {
    document.getElementById('viewRuleModal').classList.add('hidden');
  }

  async toggleActive(id, isActive) {
    try {
      const response = await apiFetch(`/automations/rules/${id}/toggle`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authService.getToken()}`
        }
      });

      if (response.ok) {
        await this.loadRules();
        this.showSuccess(`Rule ${isActive ? 'disabled' : 'enabled'} successfully`);
      } else {
        this.showError('Failed to toggle rule status');
      }
    } catch (error) {
      console.error('Error toggling rule:', error);
      this.showError('Error toggling rule status');
    }
  }

  async testRule(id) {
    try {
      const response = await apiFetch(`/automations/rules/${id}/test`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authService.getToken()}`
        },
        body: JSON.stringify({ test_data: {} })
      });

      if (response.ok) {
        const result = await response.json();
        this.showSuccess('Test execution completed. Check execution history for details.');
      } else {
        this.showError('Test execution failed');
      }
    } catch (error) {
      console.error('Error testing rule:', error);
      this.showError('Error testing rule');
    }
  }

  async deleteRule(id) {
    if (!confirm('Are you sure you want to delete this automation rule?')) return;

    try {
      const response = await apiFetch(`/automations/rules/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${authService.getToken()}`
        }
      });

      if (response.ok) {
        await this.loadRules();
        this.showSuccess('Automation rule deleted successfully');
      } else {
        this.showError('Failed to delete automation rule');
      }
    } catch (error) {
      console.error('Error deleting rule:', error);
      this.showError('Error deleting automation rule');
    }
  }

  async editRule(id) {
    try {
      const response = await apiFetch(`/automations/rules/${id}`, {
        headers: { 'Authorization': `Bearer ${authService.getToken()}` }
      });

      if (!response.ok) {
        this.showError('Failed to load automation rule');
        return;
      }

      const rule = await response.json();
      this.showRuleBuilder(rule);
    } catch (error) {
      console.error('Error loading rule:', error);
      this.showError('Error loading automation rule');
    }
  }

  showRuleBuilder(rule) {
    const modal = document.createElement('div');
    modal.id = 'ruleBuilderModal';
    modal.className = 'fixed inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center z-50';
    modal.innerHTML = `
      <div class="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h3 class="text-lg font-semibold text-gray-900">
            <i class="ph ph-gear"></i> Edit Automation Rule
          </h3>
          <button onclick="AutomationApp.closeRuleBuilder()" class="text-gray-400 hover:text-gray-600">
            <i class="ph ph-x text-2xl"></i>
          </button>
        </div>
        <form id="editRuleForm" class="p-6 space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Rule Name *</label>
              <input type="text" name="name" required value="${this.escapeHtml(rule.name)}"
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100" disabled>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Label *</label>
              <input type="text" name="label" required value="${this.escapeHtml(rule.label)}"
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea name="description" rows="2" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">${this.escapeHtml(rule.description || '')}</textarea>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Trigger Type</label>
              <select name="trigger_type" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                <option value="onCreate" ${rule.trigger_type === 'onCreate' ? 'selected' : ''}>On Create</option>
                <option value="onUpdate" ${rule.trigger_type === 'onUpdate' ? 'selected' : ''}>On Update</option>
                <option value="onDelete" ${rule.trigger_type === 'onDelete' ? 'selected' : ''}>On Delete</option>
                <option value="scheduled" ${rule.trigger_type === 'scheduled' ? 'selected' : ''}>Scheduled</option>
                <option value="manual" ${rule.trigger_type === 'manual' ? 'selected' : ''}>Manual</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Priority</label>
              <input type="number" name="priority" value="${rule.priority || 0}"
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Trigger Conditions (JSON)</label>
            <textarea name="trigger_conditions" rows="4" placeholder='{"field": "status", "operator": "equals", "value": "active"}'
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono text-sm">${rule.trigger_conditions ? JSON.stringify(rule.trigger_conditions, null, 2) : ''}</textarea>
            <p class="text-xs text-gray-500 mt-1">Define conditions for when this rule should execute</p>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Actions (JSON)</label>
            <textarea name="actions" rows="6" placeholder='[{"type": "send_email", "to": "user@example.com", "subject": "Notification"}]'
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono text-sm">${rule.actions ? JSON.stringify(rule.actions, null, 2) : '[]'}</textarea>
            <p class="text-xs text-gray-500 mt-1">Define actions to execute when conditions are met</p>
          </div>

          <div class="flex gap-3 pt-4 border-t">
            <button type="submit" class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
              <i class="ph ph-check"></i> Save Changes
            </button>
            <button type="button" onclick="AutomationApp.closeRuleBuilder()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200">
              Cancel
            </button>
          </div>
        </form>
      </div>
    `;

    document.body.appendChild(modal);

    document.getElementById('editRuleForm').addEventListener('submit', (e) => {
      e.preventDefault();
      this.updateRule(rule.id, e.target);
    });
  }

  closeRuleBuilder() {
    const modal = document.getElementById('ruleBuilderModal');
    if (modal) modal.remove();
  }

  async updateRule(ruleId, form) {
    const formData = new FormData(form);

    let triggerConditions = null;
    let actions = null;

    try {
      const conditionsText = formData.get('trigger_conditions');
      if (conditionsText && conditionsText.trim()) {
        triggerConditions = JSON.parse(conditionsText);
      }

      const actionsText = formData.get('actions');
      if (actionsText && actionsText.trim()) {
        actions = JSON.parse(actionsText);
      }
    } catch (err) {
      this.showError('Invalid JSON in conditions or actions');
      return;
    }

    const data = {
      label: formData.get('label'),
      description: formData.get('description') || null,
      trigger_type: formData.get('trigger_type'),
      trigger_conditions: triggerConditions,
      actions: actions,
      priority: parseInt(formData.get('priority')) || 0
    };

    try {
      const response = await apiFetch(`/automations/rules/${ruleId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authService.getToken()}`
        },
        body: JSON.stringify(data)
      });

      if (response.ok) {
        this.closeRuleBuilder();
        this.showSuccess('Automation rule updated successfully');
        await this.loadRules();
      } else {
        const error = await response.json();
        this.showError(error.detail || 'Failed to update rule');
      }
    } catch (error) {
      console.error('Error updating rule:', error);
      this.showError('Error updating rule');
    }
  }

  async viewExecution(id) {
    try {
      const response = await apiFetch(`/automations/executions/${id}`, {
        headers: { 'Authorization': `Bearer ${authService.getToken()}` }
      });

      if (!response.ok) {
        this.showError('Failed to load execution details');
        return;
      }

      const execution = await response.json();
      this.showExecutionDetail(execution);
    } catch (error) {
      console.error('Error loading execution:', error);
      this.showError('Error loading execution details');
    }
  }

  showExecutionDetail(execution) {
    const modal = document.createElement('div');
    modal.id = 'executionDetailModal';
    modal.className = 'fixed inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center z-50';
    modal.innerHTML = `
      <div class="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h3 class="text-lg font-semibold text-gray-900">
            <i class="ph ph-play-circle"></i> Execution Details
          </h3>
          <button onclick="AutomationApp.closeExecutionDetail()" class="text-gray-400 hover:text-gray-600">
            <i class="ph ph-x text-2xl"></i>
          </button>
        </div>
        <div class="p-6 space-y-6">
          <div>
            <h4 class="font-semibold text-gray-900 mb-3">Execution Information</h4>
            <dl class="grid grid-cols-2 gap-4">
              <div>
                <dt class="text-sm text-gray-500">Status</dt>
                <dd><span class="px-2 py-1 text-xs font-medium rounded-full ${this.getStatusClass(execution.status)}">${execution.status}</span></dd>
              </div>
              <div>
                <dt class="text-sm text-gray-500">Execution Time</dt>
                <dd class="text-sm font-medium text-gray-900">${execution.execution_time_ms || 0}ms</dd>
              </div>
              <div>
                <dt class="text-sm text-gray-500">Started At</dt>
                <dd class="text-sm font-medium text-gray-900">${new Date(execution.executed_at).toLocaleString()}</dd>
              </div>
              <div>
                <dt class="text-sm text-gray-500">Triggered By</dt>
                <dd class="text-sm font-medium text-gray-900">${execution.triggered_by || 'System'}</dd>
              </div>
            </dl>
          </div>

          ${execution.error_message ? `
            <div>
              <h4 class="font-semibold text-gray-900 mb-2 text-red-700">Error Message</h4>
              <div class="bg-red-50 border border-red-200 rounded p-3">
                <pre class="text-xs text-red-800 whitespace-pre-wrap">${this.escapeHtml(execution.error_message)}</pre>
              </div>
            </div>
          ` : ''}

          ${execution.context_data ? `
            <div>
              <h4 class="font-semibold text-gray-900 mb-2">Context Data</h4>
              <pre class="bg-gray-50 p-3 rounded text-xs overflow-x-auto">${JSON.stringify(execution.context_data, null, 2)}</pre>
            </div>
          ` : ''}

          ${execution.result_data ? `
            <div>
              <h4 class="font-semibold text-gray-900 mb-2">Result Data</h4>
              <pre class="bg-gray-50 p-3 rounded text-xs overflow-x-auto">${JSON.stringify(execution.result_data, null, 2)}</pre>
            </div>
          ` : ''}
        </div>
        <div class="px-6 py-4 border-t border-gray-200 flex justify-end">
          <button onclick="AutomationApp.closeExecutionDetail()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200">
            Close
          </button>
        </div>
      </div>
    `;

    document.body.appendChild(modal);
  }

  closeExecutionDetail() {
    const modal = document.getElementById('executionDetailModal');
    if (modal) modal.remove();
  }

  showCreateWebhookModal() {
    const modal = document.createElement('div');
    modal.id = 'createWebhookModal';
    modal.className = 'fixed inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center z-50';
    modal.innerHTML = `
      <div class="bg-white rounded-lg shadow-xl w-full max-w-2xl">
        <div class="px-6 py-4 border-b border-gray-200">
          <h3 class="text-lg font-semibold text-gray-900">Create Webhook</h3>
        </div>
        <form id="createWebhookForm" class="p-6 space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Webhook Name *</label>
            <input type="text" name="name" required placeholder="order_notification"
                   class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Label *</label>
            <input type="text" name="label" required placeholder="Order Notification Webhook"
                   class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Webhook Type</label>
            <select name="webhook_type" required class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
              <option value="incoming">Incoming (Receive data)</option>
              <option value="outgoing">Outgoing (Send data)</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Target URL</label>
            <input type="url" name="url" placeholder="https://api.example.com/webhook"
                   class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
            <p class="text-xs text-gray-500 mt-1">For outgoing webhooks only</p>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea name="description" rows="2" placeholder="Webhook description..."
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"></textarea>
          </div>

          <div class="flex gap-3 pt-4 border-t">
            <button type="submit" class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
              <i class="ph ph-plus"></i> Create Webhook
            </button>
            <button type="button" onclick="AutomationApp.closeCreateWebhookModal()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200">
              Cancel
            </button>
          </div>
        </form>
      </div>
    `;

    document.body.appendChild(modal);

    document.getElementById('createWebhookForm').addEventListener('submit', (e) => {
      e.preventDefault();
      this.createWebhook(e.target);
    });
  }

  closeCreateWebhookModal() {
    const modal = document.getElementById('createWebhookModal');
    if (modal) modal.remove();
  }

  async createWebhook(form) {
    const formData = new FormData(form);
    const data = {
      name: formData.get('name'),
      label: formData.get('label'),
      webhook_type: formData.get('webhook_type'),
      url: formData.get('url') || null,
      description: formData.get('description') || null
    };

    try {
      const response = await apiFetch('/automations/webhooks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authService.getToken()}`
        },
        body: JSON.stringify(data)
      });

      if (response.ok) {
        this.closeCreateWebhookModal();
        this.showSuccess('Webhook created successfully');
        await this.loadWebhooks();
      } else {
        const error = await response.json();
        this.showError(error.detail || 'Failed to create webhook');
      }
    } catch (error) {
      console.error('Error creating webhook:', error);
      this.showError('Error creating webhook');
    }
  }

  viewWebhook(id) {
    this.showError('Webhook detail view coming soon');
  }

  deleteWebhook(id) {
    this.showError('Webhook deletion coming soon');
  }

  // ========== VISUAL CONDITION BUILDER ==========
  async openVisualConditionBuilder(ruleId) {
    try {
      const response = await apiFetch(`/automations/rules/${ruleId}`, {
        headers: { 'Authorization': `Bearer ${authService.getToken()}` }
      });

      if (!response.ok) {
        this.showError('Failed to load rule');
        return;
      }

      const rule = await response.json();
      this.currentRule = rule;

      // Parse conditions - handle both dictionary format (with groups) and legacy array format
      if (rule.conditions && typeof rule.conditions === 'object') {
        if (Array.isArray(rule.conditions.groups) && rule.conditions.groups.length > 0) {
          // New dictionary format: { groups: [...], logic: 'AND' }
          this.conditionGroups = rule.conditions.groups;
        } else if (Array.isArray(rule.conditions) && rule.conditions.length > 0) {
          // Legacy array format
          this.conditionGroups = rule.conditions;
        } else {
          this.conditionGroups = [{ operator: 'AND', conditions: [] }];
        }
      } else {
        this.conditionGroups = [{ operator: 'AND', conditions: [] }];
      }

      // Load entity fields if this is a database trigger
      this.currentEntityFields = [];
      if (rule.trigger_config?.entity_id) {
        try {
          const fieldsResponse = await apiFetch(`/data-model/entities/${rule.trigger_config.entity_id}/fields`, {
            headers: { 'Authorization': `Bearer ${authService.getToken()}` }
          });
          if (fieldsResponse.ok) {
            this.currentEntityFields = await fieldsResponse.json();
          }
        } catch (e) {
          console.error('Error loading entity fields:', e);
        }
      }

      this.showVisualConditionBuilder();
    } catch (error) {
      console.error('Error loading rule:', error);
      this.showError('Error loading rule');
    }
  }

  showVisualConditionBuilder() {
    const modal = document.createElement('div');
    modal.id = 'visualConditionBuilderModal';
    modal.className = 'fixed inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center z-50';

    modal.innerHTML = `
      <div class="bg-white rounded-lg shadow-xl w-full max-w-6xl max-h-[90vh] flex flex-col">
        <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 class="text-xl font-semibold text-gray-900">
            <i class="ph ph-flow-arrow"></i> Visual Condition Builder
          </h2>
          <button onclick="AutomationApp.closeVisualConditionBuilder()" class="text-gray-400 hover:text-gray-600">
            <i class="ph ph-x text-2xl"></i>
          </button>
        </div>

        <div class="flex-1 overflow-y-auto p-6">
          <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <div class="flex items-start gap-3">
              <i class="ph ph-info text-blue-600 text-xl"></i>
              <div>
                <h4 class="font-semibold text-blue-900 mb-1">Build Conditions Visually</h4>
                <p class="text-sm text-blue-800">Create complex conditional logic using drag-and-drop. Group conditions with AND/OR operators.</p>
              </div>
            </div>
          </div>

          <div id="conditionGroupsContainer" class="space-y-4"></div>

          <button onclick="AutomationApp.addConditionGroup()" class="mt-4 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 flex items-center gap-2">
            <i class="ph ph-plus"></i> Add Condition Group
          </button>
        </div>

        <div class="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
          <button onclick="AutomationApp.saveConditions()" class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
            <i class="ph ph-check"></i> Save Conditions
          </button>
          <button onclick="AutomationApp.closeVisualConditionBuilder()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200">
            Cancel
          </button>
        </div>
      </div>
    `;

    document.body.appendChild(modal);
    this.renderConditionGroups();
  }

  renderConditionGroups() {
    const container = document.getElementById('conditionGroupsContainer');
    if (!container) return;

    // Ensure conditionGroups is always an array
    if (!Array.isArray(this.conditionGroups)) {
      this.conditionGroups = [{ operator: 'AND', conditions: [] }];
    }

    // Build field options from entity fields
    const fieldOptions = this.currentEntityFields.length > 0
      ? this.currentEntityFields.map(f => `<option value="${f.name}">${f.label || f.name}</option>`).join('')
      : '<option value="">No fields available</option>';

    container.innerHTML = this.conditionGroups.map((group, groupIdx) => `
      <div class="border-2 border-gray-300 rounded-lg p-4 bg-gray-50">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-3">
            <span class="font-semibold text-gray-900">Group ${groupIdx + 1}</span>
            <select onchange="this.parentElement.parentElement.parentElement.dataset.operator = this.value" class="px-3 py-1 border border-gray-300 rounded text-sm">
              <option value="AND" ${group.operator === 'AND' ? 'selected' : ''}>AND (All must match)</option>
              <option value="OR" ${group.operator === 'OR' ? 'selected' : ''}>OR (Any can match)</option>
            </select>
          </div>
          <button onclick="AutomationApp.removeConditionGroup(${groupIdx})" class="text-red-600 hover:text-red-800">
            <i class="ph ph-trash text-lg"></i>
          </button>
        </div>

        <div class="space-y-2">
          ${(group.conditions || []).map((cond, condIdx) => `
            <div class="flex items-center gap-2 bg-white p-3 rounded border border-gray-200">
              <select class="flex-1 px-3 py-2 border border-gray-300 rounded text-sm" data-field="${groupIdx}-${condIdx}">
                ${this.currentEntityFields.map(f =>
                  `<option value="${f.name}" ${cond.field === f.name ? 'selected' : ''}>${f.label || f.name}</option>`
                ).join('') || '<option value="">No fields available</option>'}
              </select>
              <select class="px-3 py-2 border border-gray-300 rounded text-sm" data-operator="${groupIdx}-${condIdx}">
                <option value="equals" ${cond.operator === 'equals' ? 'selected' : ''}>Equals</option>
                <option value="not_equals" ${cond.operator === 'not_equals' ? 'selected' : ''}>Not Equals</option>
                <option value="contains" ${cond.operator === 'contains' ? 'selected' : ''}>Contains</option>
                <option value="not_contains" ${cond.operator === 'not_contains' ? 'selected' : ''}>Does Not Contain</option>
                <option value="greater_than" ${cond.operator === 'greater_than' ? 'selected' : ''}>Greater Than</option>
                <option value="less_than" ${cond.operator === 'less_than' ? 'selected' : ''}>Less Than</option>
                <option value="is_null" ${cond.operator === 'is_null' ? 'selected' : ''}>Is Null</option>
                <option value="is_not_null" ${cond.operator === 'is_not_null' ? 'selected' : ''}>Is Not Null</option>
                <option value="in" ${cond.operator === 'in' ? 'selected' : ''}>In List</option>
              </select>
              <input type="text" value="${this.escapeHtml(cond.value || '')}" placeholder="Value" class="flex-1 px-3 py-2 border border-gray-300 rounded text-sm" data-value="${groupIdx}-${condIdx}">
              <button onclick="AutomationApp.removeCondition(${groupIdx}, ${condIdx})" class="text-red-600 hover:text-red-800">
                <i class="ph ph-x text-lg"></i>
              </button>
            </div>
          `).join('')}
        </div>

        <button onclick="AutomationApp.addCondition(${groupIdx})" class="mt-3 px-3 py-1.5 bg-white border border-gray-300 text-gray-700 rounded text-sm hover:bg-gray-50">
          <i class="ph ph-plus"></i> Add Condition
        </button>
      </div>
    `).join('');
  }

  addConditionGroup() {
    this.conditionGroups.push({ operator: 'AND', conditions: [] });
    this.renderConditionGroups();
  }

  addCondition(groupIdx) {
    this.conditionGroups[groupIdx].conditions.push({ field: '', operator: 'equals', value: '' });
    this.renderConditionGroups();
  }

  removeCondition(groupIdx, condIdx) {
    this.conditionGroups[groupIdx].conditions.splice(condIdx, 1);
    this.renderConditionGroups();
  }

  removeConditionGroup(groupIdx) {
    this.conditionGroups.splice(groupIdx, 1);
    this.renderConditionGroups();
  }

  async saveConditions() {
    // Collect condition data from DOM
    const groups = [];
    this.conditionGroups.forEach((group, groupIdx) => {
      const conditions = [];
      group.conditions.forEach((cond, condIdx) => {
        const fieldSelect = document.querySelector(`[data-field="${groupIdx}-${condIdx}"]`);
        const operatorSelect = document.querySelector(`[data-operator="${groupIdx}-${condIdx}"]`);
        const valueInput = document.querySelector(`[data-value="${groupIdx}-${condIdx}"]`);

        if (fieldSelect && operatorSelect && valueInput) {
          conditions.push({
            field: fieldSelect.value,
            operator: operatorSelect.value,
            value: valueInput.value
          });
        }
      });

      groups.push({
        operator: group.operator,
        conditions
      });
    });

    // Wrap groups in a dictionary as expected by the backend
    const conditionsData = {
      groups: groups,
      logic: 'AND' // Default logic between groups
    };

    try {
      const response = await apiFetch(`/automations/rules/${this.currentRule.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authService.getToken()}`
        },
        body: JSON.stringify({
          conditions: conditionsData,
          has_conditions: groups.length > 0 && groups.some(g => g.conditions.length > 0)
        })
      });

      if (response.ok) {
        this.closeVisualConditionBuilder();
        this.showSuccess('Conditions saved successfully');
        await this.loadRules();
      } else {
        const error = await response.json();
        this.showError(error.detail || 'Failed to save conditions');
      }
    } catch (error) {
      console.error('Error saving conditions:', error);
      this.showError('Error saving conditions');
    }
  }

  closeVisualConditionBuilder() {
    const modal = document.getElementById('visualConditionBuilderModal');
    if (modal) modal.remove();
  }

  // ========== VISUAL ACTION BUILDER ==========
  async openVisualActionBuilder(ruleId) {
    try {
      const response = await apiFetch(`/automations/rules/${ruleId}`, {
        headers: { 'Authorization': `Bearer ${authService.getToken()}` }
      });

      if (!response.ok) {
        this.showError('Failed to load rule');
        return;
      }

      const rule = await response.json();
      this.currentRule = rule;
      this.actions = rule.actions || [];
      this.showVisualActionBuilder();
    } catch (error) {
      console.error('Error loading rule:', error);
      this.showError('Error loading rule');
    }
  }

  showVisualActionBuilder() {
    const modal = document.createElement('div');
    modal.id = 'visualActionBuilderModal';
    modal.className = 'fixed inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center z-50';

    modal.innerHTML = `
      <div class="bg-white rounded-lg shadow-xl w-full max-w-6xl max-h-[90vh] flex flex-col">
        <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 class="text-xl font-semibold text-gray-900">
            <i class="ph ph-play-circle"></i> Visual Action Builder
          </h2>
          <button onclick="AutomationApp.closeVisualActionBuilder()" class="text-gray-400 hover:text-gray-600">
            <i class="ph ph-x text-2xl"></i>
          </button>
        </div>

        <div class="flex-1 overflow-y-auto p-6">
          <div class="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
            <div class="flex items-start gap-3">
              <i class="ph ph-info text-green-600 text-xl"></i>
              <div class="flex-1">
                <h4 class="font-semibold text-green-900 mb-1">Build Action Workflow</h4>
                <p class="text-sm text-green-800">Define actions to execute when conditions are met. Actions run in sequence from top to bottom.</p>
              </div>
              <button onclick="AutomationApp.openActionLibrary()" class="px-3 py-1.5 bg-green-600 text-white rounded text-sm hover:bg-green-700">
                <i class="ph ph-books"></i> Templates
              </button>
            </div>
          </div>

          <div id="actionsContainer" class="space-y-3"></div>

          <button onclick="AutomationApp.addAction()" class="mt-4 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2">
            <i class="ph ph-plus"></i> Add Action
          </button>
        </div>

        <div class="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
          <button onclick="AutomationApp.saveActions()" class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
            <i class="ph ph-check"></i> Save Actions
          </button>
          <button onclick="AutomationApp.closeVisualActionBuilder()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200">
            Cancel
          </button>
        </div>
      </div>
    `;

    document.body.appendChild(modal);
    this.renderActions();
  }

  renderActions() {
    const container = document.getElementById('actionsContainer');
    if (!container) return;

    if (this.actions.length === 0) {
      container.innerHTML = `
        <div class="text-center py-12 text-gray-500">
          <i class="ph-duotone ph-play-circle text-5xl"></i>
          <p class="mt-2">No actions yet. Click "Add Action" to create one.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = this.actions.map((action, idx) => `
      <div class="flex items-start gap-3 bg-white p-4 rounded-lg border-2 border-gray-300">
        <div class="flex flex-col gap-1">
          <button onclick="AutomationApp.moveActionUp(${idx})" class="text-gray-400 hover:text-gray-700 ${idx === 0 ? 'invisible' : ''}" title="Move Up">
            <i class="ph ph-caret-up text-lg"></i>
          </button>
          <span class="w-8 h-8 bg-green-100 text-green-700 rounded-full flex items-center justify-center text-sm font-bold">${idx + 1}</span>
          <button onclick="AutomationApp.moveActionDown(${idx})" class="text-gray-400 hover:text-gray-700 ${idx === this.actions.length - 1 ? 'invisible' : ''}" title="Move Down">
            <i class="ph ph-caret-down text-lg"></i>
          </button>
        </div>

        <div class="flex-1 space-y-3">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Action Type</label>
            <select data-action-type="${idx}" onchange="AutomationApp.onActionTypeChange(${idx}, this.value)" class="w-full px-3 py-2 border border-gray-300 rounded">
              <option value="send_email" ${action.type === 'send_email' ? 'selected' : ''}>Send Email</option>
              <option value="update_record" ${action.type === 'update_record' ? 'selected' : ''}>Update Record</option>
              <option value="create_record" ${action.type === 'create_record' ? 'selected' : ''}>Create Record</option>
              <option value="delete_record" ${action.type === 'delete_record' ? 'selected' : ''}>Delete Record</option>
              <option value="query_data" ${action.type === 'query_data' ? 'selected' : ''}>Query Data</option>
              <option value="webhook" ${action.type === 'webhook' ? 'selected' : ''}>Call Webhook</option>
              <option value="notification" ${action.type === 'notification' ? 'selected' : ''}>Send Notification</option>
              <option value="assign_user" ${action.type === 'assign_user' ? 'selected' : ''}>Assign User</option>
              <option value="run_workflow" ${action.type === 'run_workflow' ? 'selected' : ''}>Run Workflow</option>
              <option value="set_variable" ${action.type === 'set_variable' ? 'selected' : ''}>Set Variable</option>
            </select>
          </div>

          <!-- Type-specific configuration fields -->
          <div id="action-config-${idx}" class="space-y-3">
            ${this.renderActionConfigFields(idx, action)}
          </div>

          <div class="flex items-center gap-4">
            <label class="flex items-center gap-2">
              <input type="checkbox" data-action-continue="${idx}" ${action.continue_on_error ? 'checked' : ''} class="rounded">
              <span class="text-sm text-gray-700">Continue on error</span>
            </label>
          </div>
        </div>

        <button onclick="AutomationApp.removeAction(${idx})" class="text-red-600 hover:text-red-800">
          <i class="ph ph-trash text-xl"></i>
        </button>
      </div>
    `).join('');
  }

  renderActionConfigFields(idx, action) {
    const config = action.config || {};
    const type = action.type || 'send_email';

    switch (type) {
      case 'send_email':
        return `
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">To (Email)</label>
              <input type="text" data-action-field="${idx}-to" value="${this.escapeHtml(config.to || '')}"
                placeholder="{{record.customer_email}}" class="w-full px-3 py-2 border border-gray-300 rounded text-sm">
              <p class="mt-1 text-xs text-gray-500">Use <code class="bg-gray-100 px-1 rounded">{{record.field}}</code> for dynamic values or enter email directly</p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">CC (optional)</label>
              <input type="text" data-action-field="${idx}-cc" value="${this.escapeHtml(config.cc || '')}"
                placeholder="manager@example.com, {{record.supervisor_email}}" class="w-full px-3 py-2 border border-gray-300 rounded text-sm">
              <p class="mt-1 text-xs text-gray-500">Comma-separated list of email addresses</p>
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Subject</label>
            <input type="text" data-action-field="${idx}-subject" value="${this.escapeHtml(config.subject || '')}"
              placeholder="Ticket #{{record.ticket_number}} - Status Update" class="w-full px-3 py-2 border border-gray-300 rounded text-sm">
            <p class="mt-1 text-xs text-gray-500">Use <code class="bg-gray-100 px-1 rounded">{{record.field}}</code> to include record data in subject</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Body</label>
            <textarea data-action-field="${idx}-body" rows="4"
              placeholder="Dear {{record.customer_name}},\n\nYour ticket has been updated to status: {{record.status}}.\n\nBest regards,\nSupport Team" class="w-full px-3 py-2 border border-gray-300 rounded text-sm">${this.escapeHtml(config.body || '')}</textarea>
            <p class="mt-1 text-xs text-gray-500">HTML supported. Use <code class="bg-gray-100 px-1 rounded">{{record.field}}</code> for dynamic content</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Template ID (optional)</label>
            <input type="text" data-action-field="${idx}-template_id" value="${this.escapeHtml(config.template_id || '')}"
              placeholder="ticket_status_update" class="w-full px-3 py-2 border border-gray-300 rounded text-sm">
            <p class="mt-1 text-xs text-gray-500">Use a predefined email template instead of custom body</p>
          </div>
        `;

      case 'update_record':
        return `
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Entity</label>
              <select data-action-field="${idx}-entity" class="w-full px-3 py-2 border border-gray-300 rounded text-sm">
                <option value="">Select entity...</option>
                ${this.entities.map(e => `<option value="${e.id}" ${config.entity === e.id || config.entity === e.name ? 'selected' : ''}>${e.display_name || e.name}</option>`).join('')}
              </select>
              <p class="mt-1 text-xs text-gray-500">The entity/table containing the record to update</p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Record ID</label>
              <input type="text" data-action-field="${idx}-record_id" value="${this.escapeHtml(config.record_id || '')}"
                placeholder="{{record.id}}" class="w-full px-3 py-2 border border-gray-300 rounded text-sm">
              <p class="mt-1 text-xs text-gray-500">Use <code class="bg-gray-100 px-1 rounded">{{record.id}}</code> to update trigger record</p>
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Fields to Update (JSON)</label>
            <textarea data-action-field="${idx}-fields" rows="3"
              placeholder='{\n  "status": "completed",\n  "resolved_at": "{{now}}",\n  "resolved_by": "{{user.id}}"\n}'
              class="w-full px-3 py-2 border border-gray-300 rounded font-mono text-sm">${JSON.stringify(config.fields || {}, null, 2)}</textarea>
            <p class="mt-1 text-xs text-gray-500">
              <i class="ph ph-info mr-1"></i> JSON format: <code class="bg-gray-100 px-1 rounded">{"field_name": "value"}</code>. Use <code class="bg-gray-100 px-1 rounded">{{record.field}}</code> or <code class="bg-gray-100 px-1 rounded">{{user.id}}</code> for dynamic values
            </p>
          </div>
        `;

      case 'create_record':
        return `
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Entity</label>
            <select data-action-field="${idx}-entity" class="w-full px-3 py-2 border border-gray-300 rounded text-sm">
              <option value="">Select entity...</option>
              ${this.entities.map(e => `<option value="${e.id}" ${config.entity === e.id || config.entity === e.name ? 'selected' : ''}>${e.display_name || e.name}</option>`).join('')}
            </select>
            <p class="mt-1 text-xs text-gray-500">The entity/table where the new record will be created</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Record Data (JSON)</label>
            <textarea data-action-field="${idx}-data" rows="4"
              placeholder='{\n  "title": "Follow-up: {{record.subject}}",\n  "parent_id": "{{record.id}}",\n  "status": "new",\n  "created_by": "{{user.id}}"\n}'
              class="w-full px-3 py-2 border border-gray-300 rounded font-mono text-sm">${JSON.stringify(config.data || {}, null, 2)}</textarea>
            <p class="mt-1 text-xs text-gray-500">
              <i class="ph ph-info mr-1"></i> JSON format: <code class="bg-gray-100 px-1 rounded">{"field_name": "value"}</code>. Use <code class="bg-gray-100 px-1 rounded">{{record.field}}</code> to copy values from trigger record
            </p>
          </div>
        `;

      case 'delete_record':
        return `
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Entity</label>
              <select data-action-field="${idx}-entity" class="w-full px-3 py-2 border border-gray-300 rounded text-sm">
                <option value="">Select entity...</option>
                ${this.entities.map(e => `<option value="${e.id}" ${config.entity === e.id || config.entity === e.name ? 'selected' : ''}>${e.display_name || e.name}</option>`).join('')}
              </select>
              <p class="mt-1 text-xs text-gray-500">The entity/table containing the record to delete</p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Record ID</label>
              <input type="text" data-action-field="${idx}-record_id" value="${this.escapeHtml(config.record_id || '')}"
                placeholder="{{record.related_id}}" class="w-full px-3 py-2 border border-gray-300 rounded text-sm">
              <p class="mt-1 text-xs text-gray-500">Use <code class="bg-gray-100 px-1 rounded">{{record.field}}</code> or enter a specific UUID</p>
            </div>
          </div>
          <div class="bg-yellow-50 border border-yellow-200 rounded p-3 text-sm text-yellow-800">
            <i class="ph ph-warning mr-1"></i> This action will soft-delete the specified record (sets is_deleted=true). The record can be recovered if needed.
          </div>
        `;

      case 'query_data':
        return `
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Entity</label>
            <select data-action-field="${idx}-entity" class="w-full px-3 py-2 border border-gray-300 rounded text-sm">
              <option value="">Select entity...</option>
              ${this.entities.map(e => `<option value="${e.id}" ${config.entity === e.id || config.entity === e.name ? 'selected' : ''}>${e.display_name || e.name}</option>`).join('')}
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Filters (JSON format)</label>
            <textarea data-action-field="${idx}-filters" rows="3"
              placeholder='{"category_id": "{{record.category_id}}", "status": "open"}'
              class="w-full px-3 py-2 border border-gray-300 rounded font-mono text-sm">${JSON.stringify(config.filters || {}, null, 2)}</textarea>
            <p class="mt-1 text-xs text-gray-500">
              <i class="ph ph-info mr-1"></i> Use JSON format: <code class="bg-gray-100 px-1 rounded">{"field": "value"}</code> or <code class="bg-gray-100 px-1 rounded">{"field": "{{variable}}"}</code>. Leave empty <code class="bg-gray-100 px-1 rounded">{}</code> for no filters.
            </p>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Aggregation</label>
              <select data-action-field="${idx}-aggregation" class="w-full px-3 py-2 border border-gray-300 rounded text-sm">
                <option value="" ${!config.aggregation ? 'selected' : ''}>None (return records)</option>
                <option value="count" ${config.aggregation === 'count' ? 'selected' : ''}>Count</option>
                <option value="sum" ${config.aggregation === 'sum' ? 'selected' : ''}>Sum</option>
                <option value="avg" ${config.aggregation === 'avg' ? 'selected' : ''}>Average</option>
                <option value="min" ${config.aggregation === 'min' ? 'selected' : ''}>Min</option>
                <option value="max" ${config.aggregation === 'max' ? 'selected' : ''}>Max</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Aggregation Field</label>
              <input type="text" data-action-field="${idx}-aggregation_field" value="${this.escapeHtml(config.aggregation_field || '')}"
                placeholder="e.g., amount, hours" class="w-full px-3 py-2 border border-gray-300 rounded text-sm">
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Store Result As</label>
            <input type="text" data-action-field="${idx}-result_variable" value="${this.escapeHtml(config.result_variable || '')}"
              placeholder="e.g., query_result (access via {{query_result}})" class="w-full px-3 py-2 border border-gray-300 rounded text-sm">
          </div>
        `;

      case 'webhook':
        return `
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">URL</label>
              <input type="text" data-action-field="${idx}-url" value="${this.escapeHtml(config.url || '')}"
                placeholder="https://api.example.com/webhooks/notify" class="w-full px-3 py-2 border border-gray-300 rounded text-sm">
              <p class="mt-1 text-xs text-gray-500">The external API endpoint to call</p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Method</label>
              <select data-action-field="${idx}-method" class="w-full px-3 py-2 border border-gray-300 rounded text-sm">
                <option value="POST" ${config.method === 'POST' || !config.method ? 'selected' : ''}>POST</option>
                <option value="GET" ${config.method === 'GET' ? 'selected' : ''}>GET</option>
                <option value="PUT" ${config.method === 'PUT' ? 'selected' : ''}>PUT</option>
                <option value="PATCH" ${config.method === 'PATCH' ? 'selected' : ''}>PATCH</option>
                <option value="DELETE" ${config.method === 'DELETE' ? 'selected' : ''}>DELETE</option>
              </select>
              <p class="mt-1 text-xs text-gray-500">HTTP method for the request</p>
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Headers (JSON)</label>
            <textarea data-action-field="${idx}-headers" rows="2"
              placeholder='{\n  "Authorization": "Bearer your-api-key",\n  "Content-Type": "application/json"\n}'
              class="w-full px-3 py-2 border border-gray-300 rounded font-mono text-sm">${JSON.stringify(config.headers || {}, null, 2)}</textarea>
            <p class="mt-1 text-xs text-gray-500">
              <i class="ph ph-info mr-1"></i> JSON format: <code class="bg-gray-100 px-1 rounded">{"Header-Name": "value"}</code>. Leave empty <code class="bg-gray-100 px-1 rounded">{}</code> for no custom headers
            </p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Body (JSON)</label>
            <textarea data-action-field="${idx}-body" rows="3"
              placeholder='{\n  "event": "ticket_updated",\n  "ticket_id": "{{record.id}}",\n  "status": "{{record.status}}",\n  "timestamp": "{{now}}"\n}'
              class="w-full px-3 py-2 border border-gray-300 rounded font-mono text-sm">${JSON.stringify(config.body || {}, null, 2)}</textarea>
            <p class="mt-1 text-xs text-gray-500">
              <i class="ph ph-info mr-1"></i> JSON format. Use <code class="bg-gray-100 px-1 rounded">{{record.field}}</code> for dynamic values. Leave empty <code class="bg-gray-100 px-1 rounded">{}</code> for GET requests
            </p>
          </div>
        `;

      case 'notification':
        return `
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Notification Type</label>
            <select data-action-field="${idx}-notification_type" class="w-full px-3 py-2 border border-gray-300 rounded text-sm">
              <option value="in_app" ${config.notification_type === 'in_app' || !config.notification_type ? 'selected' : ''}>In-App Notification</option>
              <option value="push" ${config.notification_type === 'push' ? 'selected' : ''}>Push Notification</option>
              <option value="sms" ${config.notification_type === 'sms' ? 'selected' : ''}>SMS</option>
            </select>
            <p class="mt-1 text-xs text-gray-500">How the notification will be delivered to recipients</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Recipients</label>
            <input type="text" data-action-field="${idx}-recipients" value="${this.escapeHtml(config.recipients || '')}"
              placeholder="{{record.assigned_to}}, {{record.created_by}}" class="w-full px-3 py-2 border border-gray-300 rounded text-sm">
            <p class="mt-1 text-xs text-gray-500">Use <code class="bg-gray-100 px-1 rounded">{{record.user_field}}</code> or enter user UUIDs (comma-separated)</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Title</label>
            <input type="text" data-action-field="${idx}-title" value="${this.escapeHtml(config.title || '')}"
              placeholder="New Assignment: {{record.subject}}" class="w-full px-3 py-2 border border-gray-300 rounded text-sm">
            <p class="mt-1 text-xs text-gray-500">Short title for the notification</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Message</label>
            <textarea data-action-field="${idx}-message" rows="2"
              placeholder="You have been assigned ticket #{{record.ticket_number}}: {{record.subject}}" class="w-full px-3 py-2 border border-gray-300 rounded text-sm">${this.escapeHtml(config.message || '')}</textarea>
            <p class="mt-1 text-xs text-gray-500">Use <code class="bg-gray-100 px-1 rounded">{{record.field}}</code> for dynamic content</p>
          </div>
        `;

      case 'assign_user':
        return `
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Entity</label>
              <select data-action-field="${idx}-entity" class="w-full px-3 py-2 border border-gray-300 rounded text-sm">
                <option value="">Select entity...</option>
                ${this.entities.map(e => `<option value="${e.id}" ${config.entity === e.id || config.entity === e.name ? 'selected' : ''}>${e.display_name || e.name}</option>`).join('')}
              </select>
              <p class="mt-1 text-xs text-gray-500">The entity containing the record to assign</p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Record ID</label>
              <input type="text" data-action-field="${idx}-record_id" value="${this.escapeHtml(config.record_id || '')}"
                placeholder="{{record.id}}" class="w-full px-3 py-2 border border-gray-300 rounded text-sm">
              <p class="mt-1 text-xs text-gray-500">Use <code class="bg-gray-100 px-1 rounded">{{record.id}}</code> to assign trigger record</p>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Assignment Field</label>
              <input type="text" data-action-field="${idx}-assignment_field" value="${this.escapeHtml(config.assignment_field || 'assigned_to')}"
                placeholder="assigned_to" class="w-full px-3 py-2 border border-gray-300 rounded text-sm">
              <p class="mt-1 text-xs text-gray-500">The field that stores the user reference</p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Assign To</label>
              <input type="text" data-action-field="${idx}-assign_to" value="${this.escapeHtml(config.assign_to || '')}"
                placeholder="{{user.id}} or specific-user-uuid" class="w-full px-3 py-2 border border-gray-300 rounded text-sm">
              <p class="mt-1 text-xs text-gray-500">User UUID or variable (ignored for round_robin/least_loaded)</p>
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Assignment Strategy</label>
            <select data-action-field="${idx}-strategy" class="w-full px-3 py-2 border border-gray-300 rounded text-sm">
              <option value="specific" ${config.strategy === 'specific' || !config.strategy ? 'selected' : ''}>Specific User</option>
              <option value="round_robin" ${config.strategy === 'round_robin' ? 'selected' : ''}>Round Robin (from team)</option>
              <option value="least_loaded" ${config.strategy === 'least_loaded' ? 'selected' : ''}>Least Loaded (from team)</option>
            </select>
            <p class="mt-1 text-xs text-gray-500">
              <b>Specific:</b> Assign to specified user | <b>Round Robin:</b> Rotate among team members | <b>Least Loaded:</b> Assign to user with fewest active items
            </p>
          </div>
        `;

      case 'run_workflow':
        return `
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Workflow</label>
            <select data-action-field="${idx}-workflow_id" class="w-full px-3 py-2 border border-gray-300 rounded text-sm">
              <option value="">Select workflow...</option>
              ${(this.workflows || []).map(w => `<option value="${w.id}" ${config.workflow_id === w.id ? 'selected' : ''}>${w.label || w.name}</option>`).join('')}
            </select>
            <p class="mt-1 text-xs text-gray-500">The workflow to trigger. Must be published and active.</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Initial Context Data (JSON)</label>
            <textarea data-action-field="${idx}-context_data" rows="3"
              placeholder='{\n  "entity_id": "{{record.id}}",\n  "ticket_number": "{{record.ticket_number}}",\n  "priority": "{{record.priority}}"\n}'
              class="w-full px-3 py-2 border border-gray-300 rounded font-mono text-sm">${JSON.stringify(config.context_data || {}, null, 2)}</textarea>
            <p class="mt-1 text-xs text-gray-500">
              <i class="ph ph-info mr-1"></i> JSON format. Pass data to the workflow using <code class="bg-gray-100 px-1 rounded">{{record.field}}</code>. Leave empty <code class="bg-gray-100 px-1 rounded">{}</code> for no initial data
            </p>
          </div>
        `;

      case 'set_variable':
        return `
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Variable Name</label>
              <input type="text" data-action-field="${idx}-variable_name" value="${this.escapeHtml(config.variable_name || '')}"
                placeholder="total_count" class="w-full px-3 py-2 border border-gray-300 rounded text-sm">
              <p class="mt-1 text-xs text-gray-500">Name to reference this variable (no spaces)</p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Value Type</label>
              <select data-action-field="${idx}-value_type" class="w-full px-3 py-2 border border-gray-300 rounded text-sm">
                <option value="static" ${config.value_type === 'static' || !config.value_type ? 'selected' : ''}>Static Value</option>
                <option value="expression" ${config.value_type === 'expression' ? 'selected' : ''}>Expression</option>
                <option value="from_record" ${config.value_type === 'from_record' ? 'selected' : ''}>From Record Field</option>
              </select>
              <p class="mt-1 text-xs text-gray-500">How the value will be determined</p>
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Value</label>
            <input type="text" data-action-field="${idx}-value" value="${this.escapeHtml(config.value || '')}"
              placeholder="{{record.status}}" class="w-full px-3 py-2 border border-gray-300 rounded text-sm">
            <p class="mt-1 text-xs text-gray-500">
              <b>Static:</b> Enter a fixed value | <b>Expression:</b> Use <code class="bg-gray-100 px-1 rounded">{{record.field}}</code> | <b>From Record:</b> Field name only
            </p>
          </div>
          <div class="bg-blue-50 border border-blue-200 rounded p-3 text-sm text-blue-800">
            <i class="ph ph-info mr-1"></i> Access this variable in subsequent actions using <code class="bg-blue-100 px-1 rounded">{{variable_name}}</code>
          </div>
        `;

      default:
        return `
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Configuration (JSON)</label>
            <textarea data-action-config="${idx}" rows="3" class="w-full px-3 py-2 border border-gray-300 rounded font-mono text-sm">${JSON.stringify(config, null, 2)}</textarea>
          </div>
        `;
    }
  }

  onActionTypeChange(idx, newType) {
    this.actions[idx].type = newType;
    this.actions[idx].config = {};
    this.renderActions();
  }

  addAction() {
    this.actions.push({
      type: 'send_email',
      config: {},
      continue_on_error: false
    });
    this.renderActions();
  }

  removeAction(idx) {
    this.actions.splice(idx, 1);
    this.renderActions();
  }

  moveActionUp(idx) {
    if (idx > 0) {
      [this.actions[idx - 1], this.actions[idx]] = [this.actions[idx], this.actions[idx - 1]];
      this.renderActions();
    }
  }

  moveActionDown(idx) {
    if (idx < this.actions.length - 1) {
      [this.actions[idx], this.actions[idx + 1]] = [this.actions[idx + 1], this.actions[idx]];
      this.renderActions();
    }
  }

  async saveActions() {
    // Collect action data from DOM based on type-specific fields
    const actions = [];
    let hasError = false;

    this.actions.forEach((action, idx) => {
      if (hasError) return;

      const typeSelect = document.querySelector(`[data-action-type="${idx}"]`);
      const continueCheckbox = document.querySelector(`[data-action-continue="${idx}"]`);

      if (!typeSelect) return;

      const type = typeSelect.value;
      const config = this.collectActionConfig(idx, type);

      if (config === null) {
        hasError = true;
        return;
      }

      actions.push({
        type,
        config,
        continue_on_error: continueCheckbox?.checked || false
      });
    });

    if (hasError) return;

    try {
      const response = await apiFetch(`/automations/rules/${this.currentRule.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authService.getToken()}`
        },
        body: JSON.stringify({
          actions
        })
      });

      if (response.ok) {
        this.closeVisualActionBuilder();
        this.showSuccess('Actions saved successfully');
        await this.loadRules();
      } else {
        this.showError('Failed to save actions');
      }
    } catch (error) {
      console.error('Error saving actions:', error);
      this.showError('Error saving actions');
    }
  }

  collectActionConfig(idx, type) {
    const getFieldValue = (field) => {
      const el = document.querySelector(`[data-action-field="${idx}-${field}"]`);
      return el ? el.value : '';
    };

    const parseJsonField = (field) => {
      const value = getFieldValue(field);
      if (!value || value.trim() === '' || value.trim() === '{}') return {};
      try {
        return JSON.parse(value);
      } catch (e) {
        this.showError(`Invalid JSON in action ${idx + 1} - ${field}`);
        return null;
      }
    };

    switch (type) {
      case 'send_email':
        return {
          to: getFieldValue('to'),
          cc: getFieldValue('cc'),
          subject: getFieldValue('subject'),
          body: getFieldValue('body'),
          template_id: getFieldValue('template_id')
        };

      case 'update_record': {
        const fields = parseJsonField('fields');
        if (fields === null) return null;
        return {
          entity: getFieldValue('entity'),
          record_id: getFieldValue('record_id'),
          fields
        };
      }

      case 'create_record': {
        const data = parseJsonField('data');
        if (data === null) return null;
        return {
          entity: getFieldValue('entity'),
          data
        };
      }

      case 'delete_record':
        return {
          entity: getFieldValue('entity'),
          record_id: getFieldValue('record_id')
        };

      case 'query_data': {
        const filters = parseJsonField('filters');
        if (filters === null) return null;
        return {
          entity: getFieldValue('entity'),
          filters,
          aggregation: getFieldValue('aggregation'),
          aggregation_field: getFieldValue('aggregation_field'),
          result_variable: getFieldValue('result_variable')
        };
      }

      case 'webhook': {
        const headers = parseJsonField('headers');
        if (headers === null) return null;
        const body = parseJsonField('body');
        if (body === null) return null;
        return {
          url: getFieldValue('url'),
          method: getFieldValue('method'),
          headers,
          body
        };
      }

      case 'notification':
        return {
          notification_type: getFieldValue('notification_type'),
          recipients: getFieldValue('recipients'),
          title: getFieldValue('title'),
          message: getFieldValue('message')
        };

      case 'assign_user':
        return {
          entity: getFieldValue('entity'),
          record_id: getFieldValue('record_id'),
          assignment_field: getFieldValue('assignment_field'),
          assign_to: getFieldValue('assign_to'),
          strategy: getFieldValue('strategy')
        };

      case 'run_workflow': {
        const contextData = parseJsonField('context_data');
        if (contextData === null) return null;
        return {
          workflow_id: getFieldValue('workflow_id'),
          context_data: contextData
        };
      }

      case 'set_variable':
        return {
          variable_name: getFieldValue('variable_name'),
          value_type: getFieldValue('value_type'),
          value: getFieldValue('value')
        };

      default: {
        // Fallback for unknown types - try to parse generic config textarea
        const configTextarea = document.querySelector(`[data-action-config="${idx}"]`);
        if (configTextarea) {
          try {
            return JSON.parse(configTextarea.value);
          } catch (e) {
            this.showError(`Invalid JSON in action ${idx + 1}`);
            return null;
          }
        }
        return {};
      }
    }
  }

  closeVisualActionBuilder() {
    const modal = document.getElementById('visualActionBuilderModal');
    if (modal) modal.remove();
  }

  // ========== ACTION TEMPLATE LIBRARY ==========
  openActionLibrary() {
    const modal = document.createElement('div');
    modal.id = 'actionLibraryModal';
    modal.className = 'fixed inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center z-[60]';

    const templates = [
      {
        name: 'Send Welcome Email',
        description: 'Send a welcome email to new users',
        actions: [
          { type: 'send_email', config: { to: '{{user.email}}', subject: 'Welcome!', body: 'Welcome to our platform!' }, continue_on_error: false }
        ]
      },
      {
        name: 'Update & Notify',
        description: 'Update a record and send notification',
        actions: [
          { type: 'update_record', config: { entity: '', record_id: '{{record.id}}', fields: { status: 'active' } }, continue_on_error: false },
          { type: 'notification', config: { notification_type: 'in_app', recipients: '{{record.assigned_to}}', title: 'Record Updated', message: 'Record has been updated' }, continue_on_error: true }
        ]
      },
      {
        name: 'Webhook Chain',
        description: 'Call external webhooks in sequence',
        actions: [
          { type: 'webhook', config: { url: 'https://api.example.com/notify', method: 'POST', headers: {}, body: {} }, continue_on_error: true },
          { type: 'webhook', config: { url: 'https://api.example.com/log', method: 'POST', headers: {}, body: {} }, continue_on_error: true }
        ]
      },
      {
        name: 'Query & Email Report',
        description: 'Query data metrics and send summary email',
        actions: [
          { type: 'query_data', config: { entity: '', filters: { status: 'open' }, aggregation: 'count', aggregation_field: '', result_variable: 'open_count' }, continue_on_error: false },
          { type: 'send_email', config: { to: 'manager@example.com', subject: 'Daily Report', body: 'Total open items: {{open_count}}' }, continue_on_error: false }
        ]
      },
      {
        name: 'Auto-Assign Ticket',
        description: 'Automatically assign new tickets to team',
        actions: [
          { type: 'assign_user', config: { entity: '', record_id: '{{record.id}}', assignment_field: 'assigned_to', assign_to: '', strategy: 'round_robin' }, continue_on_error: false },
          { type: 'notification', config: { notification_type: 'in_app', recipients: '{{record.assigned_to}}', title: 'New Assignment', message: 'You have been assigned a new ticket' }, continue_on_error: true }
        ]
      },
      {
        name: 'Create Related Record',
        description: 'Create a related record when triggered',
        actions: [
          { type: 'create_record', config: { entity: '', data: { parent_id: '{{record.id}}', status: 'new', created_from: 'automation' } }, continue_on_error: false }
        ]
      },
      {
        name: 'Set Variable & Conditional',
        description: 'Set a variable for use in subsequent actions',
        actions: [
          { type: 'set_variable', config: { variable_name: 'priority_level', value_type: 'from_record', value: '{{record.priority}}' }, continue_on_error: false },
          { type: 'notification', config: { notification_type: 'in_app', recipients: '{{record.created_by}}', title: 'Processing', message: 'Your request with priority {{priority_level}} is being processed' }, continue_on_error: true }
        ]
      }
    ];

    modal.innerHTML = `
      <div class="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h3 class="text-lg font-semibold text-gray-900">
            <i class="ph ph-books"></i> Action Templates
          </h3>
          <button onclick="AutomationApp.closeActionLibrary()" class="text-gray-400 hover:text-gray-600">
            <i class="ph ph-x text-2xl"></i>
          </button>
        </div>

        <div class="p-6 space-y-4">
          ${templates.map((template, idx) => `
            <div class="border-2 border-gray-200 rounded-lg p-4 hover:border-green-300 transition">
              <div class="flex items-start justify-between mb-2">
                <div>
                  <h4 class="font-semibold text-gray-900">${this.escapeHtml(template.name)}</h4>
                  <p class="text-sm text-gray-600 mt-1">${this.escapeHtml(template.description)}</p>
                </div>
                <button onclick='AutomationApp.applyTemplate(${JSON.stringify(template.actions).replace(/'/g, "&apos;")})' class="px-3 py-1.5 bg-green-600 text-white rounded text-sm hover:bg-green-700">
                  Apply
                </button>
              </div>
              <div class="mt-3 bg-gray-50 rounded p-2 text-xs">
                <span class="font-medium text-gray-700">${template.actions.length} action(s)</span>
              </div>
            </div>
          `).join('')}
        </div>

        <div class="px-6 py-4 border-t border-gray-200 flex justify-end">
          <button onclick="AutomationApp.closeActionLibrary()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200">
            Close
          </button>
        </div>
      </div>
    `;

    document.body.appendChild(modal);
  }

  applyTemplate(template) {
    if (typeof template === 'string') {
      template = JSON.parse(template);
    }
    this.actions = [...template];
    this.renderActions();
    this.closeActionLibrary();
    this.showSuccess('Template applied successfully');
  }

  closeActionLibrary() {
    const modal = document.getElementById('actionLibraryModal');
    if (modal) modal.remove();
  }

  // ========== SCHEDULE CONFIGURATION UI ==========
  async openScheduleBuilder(ruleId) {
    try {
      const response = await apiFetch(`/automations/rules/${ruleId}`, {
        headers: { 'Authorization': `Bearer ${authService.getToken()}` }
      });

      if (!response.ok) {
        this.showError('Failed to load rule');
        return;
      }

      const rule = await response.json();
      this.currentRule = rule;
      this.showScheduleBuilder();
    } catch (error) {
      console.error('Error loading rule:', error);
      this.showError('Error loading rule');
    }
  }

  showScheduleBuilder() {
    const modal = document.createElement('div');
    modal.id = 'scheduleBuilderModal';
    modal.className = 'fixed inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center z-50';

    const schedule = this.currentRule.schedule_config || {};

    modal.innerHTML = `
      <div class="bg-white rounded-lg shadow-xl w-full max-w-4xl">
        <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 class="text-xl font-semibold text-gray-900">
            <i class="ph ph-clock"></i> Schedule Configuration
          </h2>
          <button onclick="AutomationApp.closeScheduleBuilder()" class="text-gray-400 hover:text-gray-600">
            <i class="ph ph-x text-2xl"></i>
          </button>
        </div>

        <div class="p-6 space-y-6">
          <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div class="flex items-start gap-3">
              <i class="ph ph-info text-yellow-600 text-xl"></i>
              <div>
                <h4 class="font-semibold text-yellow-900 mb-1">Cron Expression Builder</h4>
                <p class="text-sm text-yellow-800">Build cron expressions visually or enter them manually.</p>
              </div>
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Schedule Type</label>
            <select id="scheduleType" class="w-full px-3 py-2 border border-gray-300 rounded">
              <option value="simple">Simple Schedule</option>
              <option value="cron" ${schedule.type === 'cron' ? 'selected' : ''}>Cron Expression</option>
            </select>
          </div>

          <div id="simpleSchedule" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Frequency</label>
              <select id="frequency" class="w-full px-3 py-2 border border-gray-300 rounded">
                <option value="hourly">Every Hour</option>
                <option value="daily">Every Day</option>
                <option value="weekly">Every Week</option>
                <option value="monthly">Every Month</option>
              </select>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Time</label>
              <input type="time" id="scheduleTime" value="09:00" class="w-full px-3 py-2 border border-gray-300 rounded">
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Days of Week (for weekly)</label>
              <div class="flex gap-2">
                ${['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day, idx) => `
                  <label class="flex-1 text-center">
                    <input type="checkbox" value="${idx + 1}" class="day-checkbox">
                    <div class="text-sm">${day}</div>
                  </label>
                `).join('')}
              </div>
            </div>
          </div>

          <div id="cronSchedule" class="hidden space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Cron Expression</label>
              <input type="text" id="cronExpression" value="${schedule.cron_expression || '0 9 * * *'}" placeholder="0 9 * * *" class="w-full px-3 py-2 border border-gray-300 rounded font-mono">
              <p class="text-xs text-gray-500 mt-1">Format: minute hour day month weekday</p>
            </div>

            <div class="bg-gray-50 rounded p-3">
              <h5 class="text-sm font-medium text-gray-900 mb-2">Common Examples:</h5>
              <ul class="text-xs text-gray-600 space-y-1">
                <li><code class="bg-white px-1 py-0.5 rounded">0 9 * * *</code> - Every day at 9:00 AM</li>
                <li><code class="bg-white px-1 py-0.5 rounded">0 */6 * * *</code> - Every 6 hours</li>
                <li><code class="bg-white px-1 py-0.5 rounded">0 9 * * 1</code> - Every Monday at 9:00 AM</li>
                <li><code class="bg-white px-1 py-0.5 rounded">0 0 1 * *</code> - First day of every month at midnight</li>
              </ul>
            </div>
          </div>
        </div>

        <div class="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
          <button onclick="AutomationApp.saveSchedule()" class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
            <i class="ph ph-check"></i> Save Schedule
          </button>
          <button onclick="AutomationApp.closeScheduleBuilder()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200">
            Cancel
          </button>
        </div>
      </div>
    `;

    document.body.appendChild(modal);

    // Setup schedule type toggle
    document.getElementById('scheduleType').addEventListener('change', (e) => {
      if (e.target.value === 'cron') {
        document.getElementById('simpleSchedule').classList.add('hidden');
        document.getElementById('cronSchedule').classList.remove('hidden');
      } else {
        document.getElementById('simpleSchedule').classList.remove('hidden');
        document.getElementById('cronSchedule').classList.add('hidden');
      }
    });
  }

  async saveSchedule() {
    const scheduleType = document.getElementById('scheduleType').value;
    let scheduleConfig;

    if (scheduleType === 'cron') {
      scheduleConfig = {
        type: 'cron',
        cron_expression: document.getElementById('cronExpression').value
      };
    } else {
      scheduleConfig = {
        type: 'simple',
        frequency: document.getElementById('frequency').value,
        time: document.getElementById('scheduleTime').value
      };
    }

    try {
      const response = await apiFetch(`/automations/rules/${this.currentRule.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authService.getToken()}`
        },
        body: JSON.stringify({
          trigger_type: 'scheduled',
          schedule_config: scheduleConfig
        })
      });

      if (response.ok) {
        this.closeScheduleBuilder();
        this.showSuccess('Schedule saved successfully');
        await this.loadRules();
      } else {
        this.showError('Failed to save schedule');
      }
    } catch (error) {
      console.error('Error saving schedule:', error);
      this.showError('Error saving schedule');
    }
  }

  closeScheduleBuilder() {
    const modal = document.getElementById('scheduleBuilderModal');
    if (modal) modal.remove();
  }

  // ========== EXECUTION MONITORING DASHBOARD ==========
  async openMonitoringDashboard() {
    try {
      const response = await apiFetch('/automations/executions', {
        headers: { 'Authorization': `Bearer ${authService.getToken()}` }
      });

      if (!response.ok) {
        this.showError('Failed to load monitoring data');
        return;
      }

      const executions = await response.json();
      this.showMonitoringDashboard(executions);
    } catch (error) {
      console.error('Error loading monitoring data:', error);
      this.showError('Error loading monitoring data');
    }
  }

  showMonitoringDashboard(executions) {
    const modal = document.createElement('div');
    modal.id = 'automationMonitoringModal';
    modal.className = 'fixed inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center z-50';

    const successCount = executions.filter(e => e.status === 'success').length;
    const failedCount = executions.filter(e => e.status === 'failed').length;
    const runningCount = executions.filter(e => e.status === 'running').length;
    const totalCount = executions.length;

    modal.innerHTML = `
      <div class="bg-white rounded-lg shadow-xl w-full max-w-7xl max-h-[90vh] flex flex-col">
        <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 class="text-xl font-semibold text-gray-900">
            <i class="ph ph-chart-line"></i> Automation Monitoring Dashboard
          </h2>
          <button onclick="AutomationApp.closeMonitoringDashboard()" class="text-gray-400 hover:text-gray-600">
            <i class="ph ph-x text-2xl"></i>
          </button>
        </div>

        <div class="flex-1 overflow-y-auto p-6 space-y-6">
          <!-- Stats Cards -->
          <div class="grid grid-cols-4 gap-4">
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-sm text-blue-600 font-medium">Total Executions</p>
                  <p class="text-2xl font-bold text-blue-900">${totalCount}</p>
                </div>
                <i class="ph ph-play-circle text-3xl text-blue-600"></i>
              </div>
            </div>

            <div class="bg-green-50 border border-green-200 rounded-lg p-4">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-sm text-green-600 font-medium">Successful</p>
                  <p class="text-2xl font-bold text-green-900">${successCount}</p>
                </div>
                <i class="ph ph-check-circle text-3xl text-green-600"></i>
              </div>
            </div>

            <div class="bg-red-50 border border-red-200 rounded-lg p-4">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-sm text-red-600 font-medium">Failed</p>
                  <p class="text-2xl font-bold text-red-900">${failedCount}</p>
                </div>
                <i class="ph ph-x-circle text-3xl text-red-600"></i>
              </div>
            </div>

            <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-sm text-yellow-600 font-medium">Running</p>
                  <p class="text-2xl font-bold text-yellow-900">${runningCount}</p>
                </div>
                <i class="ph ph-spinner text-3xl text-yellow-600"></i>
              </div>
            </div>
          </div>

          <!-- Success Rate Chart -->
          <div class="bg-white border border-gray-200 rounded-lg p-4">
            <h3 class="text-lg font-semibold text-gray-900 mb-3">Success Rate</h3>
            <div class="h-4 bg-gray-200 rounded-full overflow-hidden">
              <div class="h-full bg-green-500" style="width: ${totalCount > 0 ? (successCount / totalCount * 100) : 0}%"></div>
            </div>
            <p class="text-sm text-gray-600 mt-2">${totalCount > 0 ? Math.round(successCount / totalCount * 100) : 0}% success rate</p>
          </div>

          <!-- Recent Executions -->
          <div>
            <h3 class="text-lg font-semibold text-gray-900 mb-3">Recent Executions</h3>
            <div class="bg-white border border-gray-200 rounded-lg overflow-hidden">
              <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                  <tr>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rule</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Duration</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Started</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  ${executions.slice(0, 10).map(exec => `
                    <tr class="hover:bg-gray-50">
                      <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        ${this.escapeHtml(exec.rule_name || 'Unknown')}
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap">
                        <span class="px-2 py-1 text-xs font-medium rounded-full ${this.getExecutionStatusClass(exec.status)}">
                          ${exec.status}
                        </span>
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        ${exec.duration_ms || 0}ms
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        ${new Date(exec.started_at).toLocaleString()}
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap text-sm">
                        <button onclick="AutomationApp.viewExecution('${exec.id}')" class="text-green-600 hover:text-green-900">
                          <i class="ph ph-eye"></i> View
                        </button>
                      </td>
                    </tr>
                  `).join('')}
                  ${executions.length === 0 ? `
                    <tr>
                      <td colspan="5" class="px-6 py-12 text-center text-gray-500">No executions found</td>
                    </tr>
                  ` : ''}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div class="px-6 py-4 border-t border-gray-200 flex justify-end">
          <button onclick="AutomationApp.closeMonitoringDashboard()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200">
            Close
          </button>
        </div>
      </div>
    `;

    document.body.appendChild(modal);
  }

  getExecutionStatusClass(status) {
    const classes = {
      'success': 'bg-green-100 text-green-800',
      'failed': 'bg-red-100 text-red-800',
      'running': 'bg-yellow-100 text-yellow-800'
    };
    return classes[status] || 'bg-gray-100 text-gray-800';
  }

  closeMonitoringDashboard() {
    const modal = document.getElementById('automationMonitoringModal');
    if (modal) modal.remove();
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
    delete window.AutomationApp;
  }
}
