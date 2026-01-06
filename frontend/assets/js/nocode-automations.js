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
      deleteWebhook: (id) => this.deleteWebhook(id)
    };
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
      const response = await fetch('/api/v1/automations/rules', {
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
      const response = await fetch('/api/v1/automations/executions', {
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
      const response = await fetch('/api/v1/automations/webhooks', {
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
    document.getElementById('createRuleModal').classList.remove('hidden');
  }

  closeCreateModal() {
    document.getElementById('createRuleModal').classList.add('hidden');
    document.getElementById('createRuleForm').reset();
  }

  async createRule(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const data = {
      name: formData.get('name'),
      label: formData.get('label'),
      description: formData.get('description') || '',
      category: formData.get('category') || '',
      trigger_type: formData.get('trigger_type'),
      trigger_config: {},
      actions: [],
      is_active: formData.get('is_active') === 'on'
    };

    try {
      const response = await fetch('/api/v1/automations/rules', {
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
      const response = await fetch(`/api/v1/automations/rules/${id}`, {
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

            <div class="flex gap-3 pt-4 border-t">
              <button onclick="AutomationApp.editRule('${rule.id}')" class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
                <i class="ph ph-pencil"></i> Edit Rule
              </button>
              <button onclick="AutomationApp.testRule('${rule.id}')" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                <i class="ph ph-play"></i> Test Run
              </button>
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
      const response = await fetch(`/api/v1/automations/rules/${id}/toggle`, {
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
      const response = await fetch(`/api/v1/automations/rules/${id}/test`, {
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
      const response = await fetch(`/api/v1/automations/rules/${id}`, {
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

  editRule(id) {
    this.showError('Edit feature coming soon - will open rule builder');
  }

  viewExecution(id) {
    this.showError('Execution detail view coming soon');
  }

  showCreateWebhookModal() {
    this.showError('Webhook creation UI coming soon');
  }

  viewWebhook(id) {
    this.showError('Webhook detail view coming soon');
  }

  deleteWebhook(id) {
    this.showError('Webhook deletion coming soon');
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
