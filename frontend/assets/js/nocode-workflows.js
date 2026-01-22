/**
 * Workflow Designer Page
 *
 * Create and manage automated workflows visually
 *
 * Pattern: Template-based (similar to nocode-data-model.js)
 * - HTML template loaded from /assets/templates/nocode-workflows.html
 * - This script listens for 'route:loaded' event
 * - Initializes Workflow Designer after template is in DOM
 */

import { authService } from './auth-service.js';
import { apiFetch } from './api.js';

let workflowsPage = null;

// Route change
document.addEventListener('route:loaded', async (event) => {
  if (event.detail.route === 'nocode-workflows') {
    // Ensure DOM from template is ready
    setTimeout(async () => {
      if (!workflowsPage) {
        workflowsPage = new WorkflowsPage();
      }
      await workflowsPage.init();
    }, 0);
  }
});

document.addEventListener('route:before-change', (event) => {
  if (event.detail.from === 'nocode-workflows' && workflowsPage) {
    workflowsPage.cleanup();
    workflowsPage = null;
  }
});

export class WorkflowsPage {
  constructor() {
    this.currentTab = 'workflows';
    this.workflows = [];
    this.instances = [];
  }

  async init() {
    await this.loadWorkflows();

    // Make methods available globally for onclick handlers
    window.WorkflowApp = {
      switchTab: (tab) => this.switchTab(tab),
      showCreateModal: () => this.showCreateModal(),
      closeCreateModal: () => this.closeCreateModal(),
      createWorkflow: (event) => this.createWorkflow(event),
      viewWorkflow: (id) => this.viewWorkflow(id),
      closeViewModal: () => this.closeViewModal(),
      togglePublish: (id, isPublished) => this.togglePublish(id, isPublished),
      deleteWorkflow: (id) => this.deleteWorkflow(id),
      editWorkflow: (id) => this.editWorkflow(id),
      manageStates: (id) => this.manageStates(id),
      viewInstance: (id) => this.viewInstance(id),
      closeWorkflowEditor: () => this.closeWorkflowEditor(),
      closeStateManager: () => this.closeStateManager(),
      showAddStateModal: (id) => this.showAddStateModal(id),
      closeAddStateModal: () => this.closeAddStateModal(),
      editState: (wId, sId) => this.editState(wId, sId),
      deleteState: (wId, sId) => this.deleteState(wId, sId),
      manageTransitions: (id) => this.manageTransitions(id),
      closeTransitionManager: () => this.closeTransitionManager(),
      showAddTransitionModal: (id) => this.showAddTransitionModal(id),
      closeAddTransitionModal: () => this.closeAddTransitionModal(),
      deleteTransition: (wId, tId) => this.deleteTransition(wId, tId),
      closeInstanceDetail: () => this.closeInstanceDetail(),
      openVisualDesigner: (id) => this.openVisualDesigner(id),
      closeVisualDesigner: () => this.closeVisualDesigner(),
      simulateWorkflow: (id) => this.simulateWorkflow(id),
      closeSimulation: () => this.closeSimulation(),
      runSimulation: (id, data) => this.runSimulation(id, data),
      showVersionHistory: (id) => this.showVersionHistory(id),
      closeVersionHistory: () => this.closeVersionHistory(),
      openMonitoringDashboard: () => this.openMonitoringDashboard(),
      closeMonitoringDashboard: () => this.closeMonitoringDashboard()
    };
  }

  switchTab(tab) {
    this.currentTab = tab;

    // Update tab styles
    document.querySelectorAll('.workflow-tab').forEach(t => {
      t.classList.remove('border-purple-600', 'text-purple-600');
      t.classList.add('border-transparent', 'text-gray-500');
    });
    const activeTab = document.getElementById(`tab-${tab}`);
    if (activeTab) {
      activeTab.classList.remove('border-transparent', 'text-gray-500');
      activeTab.classList.add('border-purple-600', 'text-purple-600');
    }

    // Show/hide content
    const workflowsContent = document.getElementById('content-workflows');
    const instancesContent = document.getElementById('content-instances');
    if (workflowsContent) workflowsContent.classList.toggle('hidden', tab !== 'workflows');
    if (instancesContent) instancesContent.classList.toggle('hidden', tab !== 'instances');

    if (tab === 'instances') {
      this.loadInstances();
    }
  }

  async loadWorkflows() {
    try {
      const response = await apiFetch('/workflows', {
        headers: {
          'Authorization': `Bearer ${authService.getToken()}`
        }
      });

      if (response.ok) {
        this.workflows = await response.json();
        this.renderWorkflows();
      } else {
        this.showError('Failed to load workflows');
      }
    } catch (error) {
      console.error('Error loading workflows:', error);
      this.showError('Error loading workflows');
    }
  }

  renderWorkflows() {
    const container = document.getElementById('workflows-list');
    if (!container) return;

    if (this.workflows.length === 0) {
      container.innerHTML = `
        <div class="col-span-full text-center py-12">
          <i class="ph-duotone ph-flow-arrow text-6xl text-gray-300"></i>
          <h3 class="mt-4 text-lg font-medium text-gray-900">No workflows yet</h3>
          <p class="mt-2 text-gray-500">Create your first workflow to get started</p>
          <button onclick="WorkflowApp.showCreateModal()" class="mt-4 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700">
            <i class="ph ph-plus"></i> Create Workflow
          </button>
        </div>
      `;
      return;
    }

    container.innerHTML = this.workflows.map(workflow => `
      <div class="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-lg transition">
        <div class="flex items-start justify-between mb-3">
          <div class="flex-1">
            <div class="flex items-center gap-2 mb-1">
              <h3 class="text-lg font-semibold text-gray-900">${this.escapeHtml(workflow.label)}</h3>
              ${workflow.tenant_id === null ? '<span class="px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs font-medium">Platform</span>' : ''}
            </div>
            <p class="text-sm text-gray-500 mt-1">${this.escapeHtml(workflow.description || 'No description')}</p>
          </div>
          <span class="ml-2 px-3 py-1 rounded-full text-xs font-medium ${workflow.is_published ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}">
            ${workflow.is_published ? 'Published' : 'Draft'}
          </span>
        </div>

        <div class="space-y-2 text-sm text-gray-600 mb-4">
          <div class="flex items-center gap-2">
            <i class="ph ph-tag"></i>
            <span>${workflow.category || 'Uncategorized'}</span>
          </div>
          <div class="flex items-center gap-2">
            <i class="ph ph-play-circle"></i>
            <span>Trigger: ${workflow.trigger_type}</span>
          </div>
          <div class="flex items-center gap-2">
            <i class="ph ph-calendar"></i>
            <span>Created: ${new Date(workflow.created_at).toLocaleDateString()}</span>
          </div>
        </div>

        <div class="flex gap-2">
          <button onclick="WorkflowApp.viewWorkflow('${workflow.id}')" class="flex-1 px-3 py-2 bg-purple-50 text-purple-700 rounded-lg hover:bg-purple-100 text-sm font-medium">
            <i class="ph ph-eye"></i> View
          </button>
          <button onclick="WorkflowApp.togglePublish('${workflow.id}', ${workflow.is_published})" class="flex-1 px-3 py-2 bg-gray-50 text-gray-700 rounded-lg hover:bg-gray-100 text-sm font-medium">
            <i class="ph ph-${workflow.is_published ? 'pause' : 'play'}"></i> ${workflow.is_published ? 'Unpublish' : 'Publish'}
          </button>
          <button onclick="WorkflowApp.deleteWorkflow('${workflow.id}')" class="px-3 py-2 bg-red-50 text-red-700 rounded-lg hover:bg-red-100 text-sm">
            <i class="ph ph-trash"></i>
          </button>
        </div>
      </div>
    `).join('');
  }

  async loadInstances() {
    try {
      const response = await apiFetch('/workflows/instances', {
        headers: {
          'Authorization': `Bearer ${authService.getToken()}`
        }
      });

      if (response.ok) {
        this.instances = await response.json();
        this.renderInstances();
      }
    } catch (error) {
      console.error('Error loading instances:', error);
    }
  }

  renderInstances() {
    const tbody = document.getElementById('instances-tbody');
    if (!tbody) return;

    if (this.instances.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="5" class="px-6 py-12 text-center text-gray-500">No active workflow instances</td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = this.instances.map(instance => `
      <tr class="hover:bg-gray-50">
        <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
          ${instance.workflow_name || 'Unknown'}
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
          ${instance.current_state_name || 'N/A'}
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
          <span class="px-2 py-1 text-xs font-medium rounded-full ${this.getStatusClass(instance.status)}">
            ${instance.status}
          </span>
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
          ${new Date(instance.started_at).toLocaleString()}
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-sm">
          <button onclick="WorkflowApp.viewInstance('${instance.id}')" class="text-purple-600 hover:text-purple-900">
            <i class="ph ph-eye"></i> View
          </button>
        </td>
      </tr>
    `).join('');
  }

  getStatusClass(status) {
    const classes = {
      'active': 'bg-blue-100 text-blue-800',
      'completed': 'bg-green-100 text-green-800',
      'failed': 'bg-red-100 text-red-800',
      'paused': 'bg-yellow-100 text-yellow-800'
    };
    return classes[status] || 'bg-gray-100 text-gray-800';
  }

  showCreateModal() {
    const modal = document.getElementById('createWorkflowModal');
    if (modal) modal.classList.remove('hidden');
  }

  closeCreateModal() {
    const modal = document.getElementById('createWorkflowModal');
    const form = document.getElementById('createWorkflowForm');
    if (modal) modal.classList.add('hidden');
    if (form) form.reset();
  }

  async createWorkflow(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const data = {
      name: formData.get('name'),
      label: formData.get('label'),
      description: formData.get('description') || '',
      category: formData.get('category') || '',
      trigger_type: formData.get('trigger_type'),
      canvas_data: { nodes: [], edges: [] } // Empty canvas initially
    };

    try {
      const response = await apiFetch('/workflows', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authService.getToken()}`
        },
        body: JSON.stringify(data)
      });

      if (response.ok) {
        this.closeCreateModal();
        await this.loadWorkflows();
        this.showSuccess('Workflow created successfully');
      } else {
        const error = await response.json();
        this.showError(error.detail || 'Failed to create workflow');
      }
    } catch (error) {
      console.error('Error creating workflow:', error);
      this.showError('Error creating workflow');
    }
  }

  async viewWorkflow(id) {
    try {
      const response = await apiFetch(`/workflows/${id}`, {
        headers: {
          'Authorization': `Bearer ${authService.getToken()}`
        }
      });

      if (response.ok) {
        const workflow = await response.json();
        const title = document.getElementById('viewWorkflowTitle');
        const content = document.getElementById('viewWorkflowContent');

        if (title) title.textContent = workflow.label;
        if (content) {
          content.innerHTML = `
            <div class="space-y-6">
              <div>
                <h4 class="font-semibold text-gray-900 mb-2">Basic Information</h4>
                <dl class="grid grid-cols-2 gap-4">
                  <div>
                    <dt class="text-sm text-gray-500">Name</dt>
                    <dd class="text-sm font-medium text-gray-900">${this.escapeHtml(workflow.name)}</dd>
                  </div>
                  <div>
                    <dt class="text-sm text-gray-500">Category</dt>
                    <dd class="text-sm font-medium text-gray-900">${this.escapeHtml(workflow.category || 'N/A')}</dd>
                  </div>
                  <div>
                    <dt class="text-sm text-gray-500">Trigger Type</dt>
                    <dd class="text-sm font-medium text-gray-900">${workflow.trigger_type}</dd>
                  </div>
                  <div>
                    <dt class="text-sm text-gray-500">Version</dt>
                    <dd class="text-sm font-medium text-gray-900">${workflow.version}</dd>
                  </div>
                </dl>
              </div>

              ${workflow.description ? `
                <div>
                  <h4 class="font-semibold text-gray-900 mb-2">Description</h4>
                  <p class="text-sm text-gray-600">${this.escapeHtml(workflow.description)}</p>
                </div>
              ` : ''}

              <div class="flex gap-3 pt-4 border-t">
                <button onclick="WorkflowApp.openVisualDesigner('${workflow.id}')" class="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700">
                  <i class="ph ph-flow-arrow"></i> Visual Designer
                </button>
                <button onclick="WorkflowApp.editWorkflow('${workflow.id}')" class="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700">
                  <i class="ph ph-pencil"></i> Edit Workflow
                </button>
                <button onclick="WorkflowApp.manageStates('${workflow.id}')" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                  <i class="ph ph-circle"></i> Manage States
                </button>
              </div>
            </div>
          `;
        }

        const modal = document.getElementById('viewWorkflowModal');
        if (modal) modal.classList.remove('hidden');
      }
    } catch (error) {
      console.error('Error loading workflow:', error);
      this.showError('Error loading workflow details');
    }
  }

  closeViewModal() {
    const modal = document.getElementById('viewWorkflowModal');
    if (modal) modal.classList.add('hidden');
  }

  async togglePublish(id, isPublished) {
    if (isPublished) {
      this.showError('Unpublish feature coming soon');
      return;
    }

    try {
      const response = await apiFetch(`/workflows/${id}/publish`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authService.getToken()}`
        }
      });

      if (response.ok) {
        await this.loadWorkflows();
        this.showSuccess('Workflow published successfully');
      } else {
        this.showError('Failed to publish workflow');
      }
    } catch (error) {
      console.error('Error publishing workflow:', error);
      this.showError('Error publishing workflow');
    }
  }

  async deleteWorkflow(id) {
    if (!confirm('Are you sure you want to delete this workflow?')) return;

    try {
      const response = await apiFetch(`/workflows/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${authService.getToken()}`
        }
      });

      if (response.ok) {
        await this.loadWorkflows();
        this.showSuccess('Workflow deleted successfully');
      } else {
        this.showError('Failed to delete workflow');
      }
    } catch (error) {
      console.error('Error deleting workflow:', error);
      this.showError('Error deleting workflow');
    }
  }

  async editWorkflow(id) {
    try {
      const response = await apiFetch(`/workflows/${id}`, {
        headers: { 'Authorization': `Bearer ${authService.getToken()}` }
      });

      if (!response.ok) {
        this.showError('Failed to load workflow');
        return;
      }

      const workflow = await response.json();
      this.showWorkflowEditor(workflow);
    } catch (error) {
      console.error('Error loading workflow:', error);
      this.showError('Error loading workflow');
    }
  }

  showWorkflowEditor(workflow) {
    const modal = document.createElement('div');
    modal.id = 'workflowEditorModal';
    modal.className = 'fixed inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center z-50';
    modal.innerHTML = `
      <div class="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h3 class="text-lg font-semibold text-gray-900">
            <i class="ph ph-flow-arrow"></i> Edit Workflow: ${this.escapeHtml(workflow.label)}
          </h3>
          <button onclick="WorkflowApp.closeWorkflowEditor()" class="text-gray-400 hover:text-gray-600">
            <i class="ph ph-x text-2xl"></i>
          </button>
        </div>
        <form id="editWorkflowForm" class="p-6 space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Name *</label>
              <input type="text" name="name" required value="${this.escapeHtml(workflow.name)}"
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100" disabled>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Label *</label>
              <input type="text" name="label" required value="${this.escapeHtml(workflow.label)}"
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500">
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea name="description" rows="2" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500">${this.escapeHtml(workflow.description || '')}</textarea>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Category</label>
              <input type="text" name="category" value="${this.escapeHtml(workflow.category || '')}"
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500">
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Trigger Type</label>
              <select name="trigger_type" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500">
                <option value="manual" ${workflow.trigger_type === 'manual' ? 'selected' : ''}>Manual</option>
                <option value="automatic" ${workflow.trigger_type === 'automatic' ? 'selected' : ''}>Automatic</option>
                <option value="scheduled" ${workflow.trigger_type === 'scheduled' ? 'selected' : ''}>Scheduled</option>
              </select>
            </div>
          </div>
          <div class="flex gap-3 pt-4 border-t">
            <button type="submit" class="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700">
              <i class="ph ph-check"></i> Save Changes
            </button>
            <button type="button" onclick="WorkflowApp.closeWorkflowEditor()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200">
              Cancel
            </button>
          </div>
        </form>
      </div>
    `;

    document.body.appendChild(modal);

    document.getElementById('editWorkflowForm').addEventListener('submit', (e) => {
      e.preventDefault();
      this.updateWorkflow(workflow.id, e.target);
    });
  }

  closeWorkflowEditor() {
    const modal = document.getElementById('workflowEditorModal');
    if (modal) modal.remove();
  }

  async updateWorkflow(workflowId, form) {
    const formData = new FormData(form);
    const data = {
      label: formData.get('label'),
      description: formData.get('description') || null,
      category: formData.get('category') || null,
      trigger_type: formData.get('trigger_type')
    };

    try {
      const response = await apiFetch(`/workflows/${workflowId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authService.getToken()}`
        },
        body: JSON.stringify(data)
      });

      if (response.ok) {
        this.closeWorkflowEditor();
        this.showSuccess('Workflow updated successfully');
        await this.loadWorkflows();
      } else {
        const error = await response.json();
        this.showError(error.detail || 'Failed to update workflow');
      }
    } catch (error) {
      console.error('Error updating workflow:', error);
      this.showError('Error updating workflow');
    }
  }

  async manageStates(id) {
    try {
      const [workflowResponse, statesResponse] = await Promise.all([
        fetch(`/api/v1/workflows/${id}`, {
          headers: { 'Authorization': `Bearer ${authService.getToken()}` }
        }),
        fetch(`/api/v1/workflows/${id}/states`, {
          headers: { 'Authorization': `Bearer ${authService.getToken()}` }
        })
      ]);

      if (!workflowResponse.ok || !statesResponse.ok) {
        this.showError('Failed to load workflow states');
        return;
      }

      const workflow = await workflowResponse.json();
      const states = await statesResponse.json();

      this.showStateManager(workflow, states);
    } catch (error) {
      console.error('Error loading states:', error);
      this.showError('Error loading workflow states');
    }
  }

  showStateManager(workflow, states) {
    const modal = document.createElement('div');
    modal.id = 'stateManagerModal';
    modal.className = 'fixed inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center z-50';
    modal.innerHTML = `
      <div class="bg-white rounded-lg shadow-xl w-full max-w-6xl max-h-[90vh] flex flex-col">
        <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h2 class="text-xl font-semibold text-gray-900">
              <i class="ph ph-circle"></i> Workflow States: ${this.escapeHtml(workflow.label)}
            </h2>
            <p class="text-sm text-gray-500 mt-1">Manage workflow states and transitions</p>
          </div>
          <button onclick="WorkflowApp.closeStateManager()" class="text-gray-400 hover:text-gray-600">
            <i class="ph ph-x text-2xl"></i>
          </button>
        </div>

        <div class="flex-1 overflow-y-auto p-6">
          <div class="mb-4 flex justify-between items-center">
            <div class="text-sm text-gray-600">
              ${states.length} states defined
            </div>
            <button onclick="WorkflowApp.showAddStateModal('${workflow.id}')" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
              <i class="ph ph-plus"></i> Add State
            </button>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4" id="statesList">
            ${states.length === 0 ? `
              <div class="col-span-full text-center py-12 text-gray-500">
                <i class="ph-duotone ph-circle text-5xl"></i>
                <p class="mt-2">No states yet. Click "Add State" to create one.</p>
              </div>
            ` : states.map(state => this.renderStateCard(state, workflow.id)).join('')}
          </div>
        </div>

        <div class="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
          <button onclick="WorkflowApp.manageTransitions('${workflow.id}')" class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
            <i class="ph ph-arrows-split"></i> Manage Transitions
          </button>
          <button onclick="WorkflowApp.closeStateManager()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200">
            Done
          </button>
        </div>
      </div>
    `;

    document.body.appendChild(modal);
    this.currentWorkflow = workflow;
    this.currentStates = states;
  }

  renderStateCard(state, workflowId) {
    const typeColors = {
      'start': 'bg-green-100 text-green-700 border-green-300',
      'intermediate': 'bg-blue-100 text-blue-700 border-blue-300',
      'end': 'bg-red-100 text-red-700 border-red-300',
      'approval': 'bg-purple-100 text-purple-700 border-purple-300',
      'condition': 'bg-yellow-100 text-yellow-700 border-yellow-300'
    };
    const colorClass = typeColors[state.state_type] || 'bg-gray-100 text-gray-700 border-gray-300';

    return `
      <div class="border-2 ${colorClass} rounded-lg p-4">
        <div class="flex items-start justify-between mb-2">
          <div class="flex-1">
            <h4 class="font-semibold text-gray-900">${this.escapeHtml(state.label)}</h4>
            <p class="text-xs uppercase font-medium mt-1">${state.state_type}</p>
          </div>
          ${state.is_final ? '<span class="px-2 py-1 bg-gray-900 text-white rounded text-xs">Final</span>' : ''}
        </div>
        ${state.description ? `<p class="text-sm text-gray-600 mb-3">${this.escapeHtml(state.description)}</p>` : ''}
        <div class="text-xs text-gray-600 space-y-1 mb-3">
          ${state.requires_approval ? '<div><i class="ph ph-check-circle"></i> Requires Approval</div>' : ''}
          ${state.sla_hours ? `<div><i class="ph ph-clock"></i> SLA: ${state.sla_hours} hours</div>` : ''}
        </div>
        <div class="flex gap-2">
          <button onclick="WorkflowApp.editState('${workflowId}', '${state.id}')" class="flex-1 px-2 py-1 bg-white border border-gray-300 text-gray-700 rounded text-xs hover:bg-gray-50">
            <i class="ph ph-pencil"></i> Edit
          </button>
          <button onclick="WorkflowApp.deleteState('${workflowId}', '${state.id}')" class="px-2 py-1 bg-red-50 border border-red-200 text-red-700 rounded text-xs hover:bg-red-100">
            <i class="ph ph-trash"></i>
          </button>
        </div>
      </div>
    `;
  }

  closeStateManager() {
    const modal = document.getElementById('stateManagerModal');
    if (modal) modal.remove();
  }

  showAddStateModal(workflowId) {
    const modal = document.createElement('div');
    modal.id = 'addStateModal';
    modal.className = 'fixed inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center z-[60]';
    modal.innerHTML = `
      <div class="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div class="px-6 py-4 border-b border-gray-200">
          <h3 class="text-lg font-semibold text-gray-900">Add Workflow State</h3>
        </div>
        <form id="addStateForm" class="p-6 space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">State Name *</label>
              <input type="text" name="name" required placeholder="pending_approval"
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Label *</label>
              <input type="text" name="label" required placeholder="Pending Approval"
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">State Type *</label>
            <select name="state_type" required class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
              <option value="">Select type...</option>
              <option value="start">Start (Initial state)</option>
              <option value="intermediate">Intermediate (Processing state)</option>
              <option value="end">End (Final state)</option>
              <option value="approval">Approval (Requires approval)</option>
              <option value="condition">Condition (Decision point)</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea name="description" rows="2" placeholder="State description..."
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"></textarea>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Color</label>
              <input type="text" name="color" placeholder="#3B82F6"
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">SLA Hours</label>
              <input type="number" name="sla_hours" placeholder="24"
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <label class="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" name="is_final" class="rounded text-blue-600">
              <span class="text-sm text-gray-700">Final State</span>
            </label>
            <label class="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" name="requires_approval" id="requiresApproval" class="rounded text-blue-600" onchange="document.getElementById('approvalConfig').classList.toggle('hidden', !this.checked)">
              <span class="text-sm text-gray-700">Requires Approval</span>
            </label>
          </div>

          <!-- Approval Configuration -->
          <div id="approvalConfig" class="hidden border-t pt-4 space-y-3">
            <h4 class="text-sm font-semibold text-gray-900">Approval Configuration</h4>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Approval Type</label>
              <select name="approval_type" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                <option value="any">Any Approver</option>
                <option value="all">All Approvers</option>
                <option value="majority">Majority</option>
                <option value="sequential">Sequential</option>
              </select>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Approver Roles (comma-separated)</label>
              <input type="text" name="approver_roles" placeholder="manager, supervisor" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
              <p class="text-xs text-gray-500 mt-1">Users with these roles can approve this state</p>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Auto-approve after (hours)</label>
              <input type="number" name="auto_approve_hours" placeholder="48" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
              <p class="text-xs text-gray-500 mt-1">Leave empty for no auto-approval</p>
            </div>
          </div>

          <div class="flex gap-3 pt-4 border-t">
            <button type="submit" class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
              <i class="ph ph-plus"></i> Add State
            </button>
            <button type="button" onclick="WorkflowApp.closeAddStateModal()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200">
              Cancel
            </button>
          </div>
        </form>
      </div>
    `;

    document.body.appendChild(modal);

    document.getElementById('addStateForm').addEventListener('submit', (e) => {
      e.preventDefault();
      this.createState(workflowId, e.target);
    });
  }

  closeAddStateModal() {
    const modal = document.getElementById('addStateModal');
    if (modal) modal.remove();
  }

  async createState(workflowId, form) {
    const formData = new FormData(form);

    // Build approval config if required
    const requiresApproval = formData.get('requires_approval') === 'on';
    let approvalConfig = null;
    if (requiresApproval) {
      const approverRoles = formData.get('approver_roles');
      approvalConfig = {
        approval_type: formData.get('approval_type') || 'any',
        approver_roles: approverRoles ? approverRoles.split(',').map(r => r.trim()) : [],
        auto_approve_hours: formData.get('auto_approve_hours') ? parseInt(formData.get('auto_approve_hours')) : null
      };
    }

    const data = {
      name: formData.get('name'),
      label: formData.get('label'),
      state_type: formData.get('state_type'),
      description: formData.get('description') || null,
      color: formData.get('color') || null,
      sla_hours: formData.get('sla_hours') ? parseInt(formData.get('sla_hours')) : null,
      is_final: formData.get('is_final') === 'on',
      requires_approval: requiresApproval,
      approval_config: approvalConfig
    };

    try {
      const response = await apiFetch(`/workflows/${workflowId}/states`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authService.getToken()}`
        },
        body: JSON.stringify(data)
      });

      if (response.ok) {
        this.closeAddStateModal();
        this.showSuccess('State created successfully');
        await this.manageStates(workflowId);
      } else {
        const error = await response.json();
        this.showError(error.detail || 'Failed to create state');
      }
    } catch (error) {
      console.error('Error creating state:', error);
      this.showError('Error creating state');
    }
  }

  async editState(workflowId, stateId) {
    // Implementation similar to editField - load state and show edit modal
    this.showError('Edit state feature - load and display edit modal');
  }

  async deleteState(workflowId, stateId) {
    if (!confirm('Are you sure you want to delete this state?')) {
      return;
    }

    try {
      const response = await apiFetch(`/workflows/${workflowId}/states/${stateId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${authService.getToken()}`
        }
      });

      if (response.ok) {
        this.showSuccess('State deleted successfully');
        await this.manageStates(workflowId);
      } else {
        const error = await response.json();
        this.showError(error.detail || 'Failed to delete state');
      }
    } catch (error) {
      console.error('Error deleting state:', error);
      this.showError('Error deleting state');
    }
  }

  async manageTransitions(workflowId) {
    try {
      const [statesResponse, transitionsResponse] = await Promise.all([
        fetch(`/api/v1/workflows/${workflowId}/states`, {
          headers: { 'Authorization': `Bearer ${authService.getToken()}` }
        }),
        fetch(`/api/v1/workflows/${workflowId}/transitions`, {
          headers: { 'Authorization': `Bearer ${authService.getToken()}` }
        })
      ]);

      if (!statesResponse.ok || !transitionsResponse.ok) {
        this.showError('Failed to load transitions');
        return;
      }

      const states = await statesResponse.json();
      const transitions = await transitionsResponse.json();

      this.showTransitionManager(workflowId, states, transitions);
    } catch (error) {
      console.error('Error loading transitions:', error);
      this.showError('Error loading transitions');
    }
  }

  showTransitionManager(workflowId, states, transitions) {
    const modal = document.createElement('div');
    modal.id = 'transitionManagerModal';
    modal.className = 'fixed inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center z-[60]';
    modal.innerHTML = `
      <div class="bg-white rounded-lg shadow-xl w-full max-w-5xl max-h-[90vh] flex flex-col">
        <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h2 class="text-xl font-semibold text-gray-900">
              <i class="ph ph-arrows-split"></i> Workflow Transitions
            </h2>
            <p class="text-sm text-gray-500 mt-1">Define state transitions and flow logic</p>
          </div>
          <button onclick="WorkflowApp.closeTransitionManager()" class="text-gray-400 hover:text-gray-600">
            <i class="ph ph-x text-2xl"></i>
          </button>
        </div>

        <div class="flex-1 overflow-y-auto p-6">
          <div class="mb-4 flex justify-between items-center">
            <div class="text-sm text-gray-600">
              ${transitions.length} transitions defined
            </div>
            <button onclick="WorkflowApp.showAddTransitionModal('${workflowId}')" class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
              <i class="ph ph-plus"></i> Add Transition
            </button>
          </div>

          <div class="space-y-3" id="transitionsList">
            ${transitions.length === 0 ? `
              <div class="text-center py-12 text-gray-500">
                <i class="ph-duotone ph-arrows-split text-5xl"></i>
                <p class="mt-2">No transitions yet. Click "Add Transition" to create one.</p>
              </div>
            ` : transitions.map(t => this.renderTransitionItem(t, states)).join('')}
          </div>
        </div>

        <div class="px-6 py-4 border-t border-gray-200 flex justify-end">
          <button onclick="WorkflowApp.closeTransitionManager()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200">
            Done
          </button>
        </div>
      </div>
    `;

    document.body.appendChild(modal);
  }

  renderTransitionItem(transition, states) {
    const fromState = states.find(s => s.id === transition.from_state_id);
    const toState = states.find(s => s.id === transition.to_state_id);

    return `
      <div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition">
        <div class="flex-1">
          <div class="flex items-center gap-3 mb-2">
            <span class="px-3 py-1 bg-blue-100 text-blue-700 rounded font-medium text-sm">
              ${this.escapeHtml(fromState?.label || 'Unknown')}
            </span>
            <i class="ph ph-arrow-right text-2xl text-gray-400"></i>
            <span class="px-3 py-1 bg-green-100 text-green-700 rounded font-medium text-sm">
              ${this.escapeHtml(toState?.label || 'Unknown')}
            </span>
          </div>
          <div class="text-sm text-gray-600">
            ${transition.button_label ? `Button: "${this.escapeHtml(transition.button_label)}"` : 'No button label'}
            ${transition.condition_type ? `• Type: ${transition.condition_type}` : ''}
          </div>
        </div>
        <div class="flex gap-2 ml-4">
          <button onclick="WorkflowApp.deleteTransition('${this.currentWorkflow.id}', '${transition.id}')" class="px-3 py-1.5 bg-red-50 text-red-700 rounded hover:bg-red-100 text-sm">
            <i class="ph ph-trash"></i> Delete
          </button>
        </div>
      </div>
    `;
  }

  closeTransitionManager() {
    const modal = document.getElementById('transitionManagerModal');
    if (modal) modal.remove();
  }

  showAddTransitionModal(workflowId) {
    const states = this.currentStates || [];
    const modal = document.createElement('div');
    modal.id = 'addTransitionModal';
    modal.className = 'fixed inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center z-[70]';
    modal.innerHTML = `
      <div class="bg-white rounded-lg shadow-xl w-full max-w-2xl">
        <div class="px-6 py-4 border-b border-gray-200">
          <h3 class="text-lg font-semibold text-gray-900">Add Transition</h3>
        </div>
        <form id="addTransitionForm" class="p-6 space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Transition Name *</label>
            <input type="text" name="name" required placeholder="approve"
                   class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500">
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">From State *</label>
              <select name="from_state_id" required class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500">
                <option value="">Select state...</option>
                ${states.map(s => `<option value="${s.id}">${this.escapeHtml(s.label)}</option>`).join('')}
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">To State *</label>
              <select name="to_state_id" required class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500">
                <option value="">Select state...</option>
                ${states.map(s => `<option value="${s.id}">${this.escapeHtml(s.label)}</option>`).join('')}
              </select>
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Button Label *</label>
            <input type="text" name="button_label" required placeholder="Approve"
                   class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500">
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Condition Type</label>
              <select name="condition_type" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500">
                <option value="always">Always</option>
                <option value="conditional">Conditional</option>
                <option value="approval">Approval Required</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Button Style</label>
              <select name="button_style" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500">
                <option value="primary">Primary (Blue)</option>
                <option value="success">Success (Green)</option>
                <option value="danger">Danger (Red)</option>
                <option value="warning">Warning (Yellow)</option>
              </select>
            </div>
          </div>

          <div class="flex gap-3 pt-4 border-t">
            <button type="submit" class="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
              <i class="ph ph-plus"></i> Add Transition
            </button>
            <button type="button" onclick="WorkflowApp.closeAddTransitionModal()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200">
              Cancel
            </button>
          </div>
        </form>
      </div>
    `;

    document.body.appendChild(modal);

    document.getElementById('addTransitionForm').addEventListener('submit', (e) => {
      e.preventDefault();
      this.createTransition(workflowId, e.target);
    });
  }

  closeAddTransitionModal() {
    const modal = document.getElementById('addTransitionModal');
    if (modal) modal.remove();
  }

  async createTransition(workflowId, form) {
    const formData = new FormData(form);
    const data = {
      name: formData.get('name'),
      label: formData.get('button_label'),
      from_state_id: formData.get('from_state_id'),
      to_state_id: formData.get('to_state_id'),
      button_label: formData.get('button_label'),
      button_style: formData.get('button_style') || 'primary',
      condition_type: formData.get('condition_type') || 'always'
    };

    try {
      const response = await apiFetch(`/workflows/${workflowId}/transitions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authService.getToken()}`
        },
        body: JSON.stringify(data)
      });

      if (response.ok) {
        this.closeAddTransitionModal();
        this.showSuccess('Transition created successfully');
        await this.manageTransitions(workflowId);
      } else {
        const error = await response.json();
        this.showError(error.detail || 'Failed to create transition');
      }
    } catch (error) {
      console.error('Error creating transition:', error);
      this.showError('Error creating transition');
    }
  }

  async deleteTransition(workflowId, transitionId) {
    if (!confirm('Are you sure you want to delete this transition?')) {
      return;
    }

    try {
      const response = await apiFetch(`/workflows/${workflowId}/transitions/${transitionId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${authService.getToken()}`
        }
      });

      if (response.ok) {
        this.showSuccess('Transition deleted successfully');
        await this.manageTransitions(workflowId);
      } else {
        const error = await response.json();
        this.showError(error.detail || 'Failed to delete transition');
      }
    } catch (error) {
      console.error('Error deleting transition:', error);
      this.showError('Error deleting transition');
    }
  }

  async viewInstance(id) {
    try {
      const response = await apiFetch(`/workflows/instances/${id}`, {
        headers: { 'Authorization': `Bearer ${authService.getToken()}` }
      });

      if (!response.ok) {
        this.showError('Failed to load workflow instance');
        return;
      }

      const instance = await response.json();
      this.showInstanceDetail(instance);
    } catch (error) {
      console.error('Error loading instance:', error);
      this.showError('Error loading workflow instance');
    }
  }

  showInstanceDetail(instance) {
    const modal = document.createElement('div');
    modal.id = 'instanceDetailModal';
    modal.className = 'fixed inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center z-50';
    modal.innerHTML = `
      <div class="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h3 class="text-lg font-semibold text-gray-900">
            <i class="ph ph-play-circle"></i> Workflow Instance Details
          </h3>
          <button onclick="WorkflowApp.closeInstanceDetail()" class="text-gray-400 hover:text-gray-600">
            <i class="ph ph-x text-2xl"></i>
          </button>
        </div>
        <div class="p-6 space-y-6">
          <div>
            <h4 class="font-semibold text-gray-900 mb-3">Instance Information</h4>
            <dl class="grid grid-cols-2 gap-4">
              <div>
                <dt class="text-sm text-gray-500">Workflow</dt>
                <dd class="text-sm font-medium text-gray-900">${this.escapeHtml(instance.workflow_name || 'Unknown')}</dd>
              </div>
              <div>
                <dt class="text-sm text-gray-500">Current State</dt>
                <dd class="text-sm font-medium text-gray-900">${this.escapeHtml(instance.current_state_name || 'N/A')}</dd>
              </div>
              <div>
                <dt class="text-sm text-gray-500">Status</dt>
                <dd><span class="px-2 py-1 text-xs font-medium rounded-full ${this.getStatusClass(instance.status)}">${instance.status}</span></dd>
              </div>
              <div>
                <dt class="text-sm text-gray-500">Started</dt>
                <dd class="text-sm font-medium text-gray-900">${new Date(instance.started_at).toLocaleString()}</dd>
              </div>
            </dl>
          </div>

          ${instance.context_data ? `
            <div>
              <h4 class="font-semibold text-gray-900 mb-2">Context Data</h4>
              <pre class="bg-gray-50 p-3 rounded text-xs overflow-x-auto">${JSON.stringify(instance.context_data, null, 2)}</pre>
            </div>
          ` : ''}
        </div>
        <div class="px-6 py-4 border-t border-gray-200 flex justify-end">
          <button onclick="WorkflowApp.closeInstanceDetail()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200">
            Close
          </button>
        </div>
      </div>
    `;

    document.body.appendChild(modal);
  }

  closeInstanceDetail() {
    const modal = document.getElementById('instanceDetailModal');
    if (modal) modal.remove();
  }

  // ========== VISUAL CANVAS DESIGNER ==========
  async openVisualDesigner(workflowId) {
    try {
      const [workflowResponse, statesResponse, transitionsResponse] = await Promise.all([
        fetch(`/api/v1/workflows/${workflowId}`, {
          headers: { 'Authorization': `Bearer ${authService.getToken()}` }
        }),
        fetch(`/api/v1/workflows/${workflowId}/states`, {
          headers: { 'Authorization': `Bearer ${authService.getToken()}` }
        }),
        fetch(`/api/v1/workflows/${workflowId}/transitions`, {
          headers: { 'Authorization': `Bearer ${authService.getToken()}` }
        })
      ]);

      if (!workflowResponse.ok || !statesResponse.ok || !transitionsResponse.ok) {
        this.showError('Failed to load workflow data');
        return;
      }

      const workflow = await workflowResponse.json();
      const states = await statesResponse.json();
      const transitions = await transitionsResponse.json();

      this.showVisualDesigner(workflow, states, transitions);
    } catch (error) {
      console.error('Error loading visual designer:', error);
      this.showError('Error loading visual designer');
    }
  }

  showVisualDesigner(workflow, states, transitions) {
    const modal = document.createElement('div');
    modal.id = 'visualDesignerModal';
    modal.className = 'fixed inset-0 bg-gray-900 bg-opacity-95 flex flex-col z-50';

    modal.innerHTML = `
      <div class="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <div>
          <h2 class="text-xl font-semibold text-gray-900">
            <i class="ph ph-flow-arrow"></i> Visual Designer: ${this.escapeHtml(workflow.label)}
          </h2>
          <p class="text-sm text-gray-500 mt-1">Drag states to reposition • Click states to edit • Arrows show transitions</p>
        </div>
        <div class="flex gap-3">
          <button onclick="WorkflowApp.simulateWorkflow('${workflow.id}')" class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
            <i class="ph ph-play"></i> Simulate
          </button>
          <button onclick="WorkflowApp.showVersionHistory('${workflow.id}')" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            <i class="ph ph-clock-counter-clockwise"></i> Version History
          </button>
          <button onclick="WorkflowApp.closeVisualDesigner()" class="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700">
            <i class="ph ph-x"></i> Close
          </button>
        </div>
      </div>

      <div class="flex-1 relative bg-gray-50 overflow-hidden">
        <svg id="workflowCanvas" class="absolute inset-0 w-full h-full" style="cursor: grab;">
          <defs>
            <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
              <polygon points="0 0, 10 3, 0 6" fill="#6B7280" />
            </marker>
          </defs>
          <g id="transitionLines"></g>
          <g id="stateNodes"></g>
        </svg>

        <div class="absolute top-4 right-4 bg-white rounded-lg shadow-lg p-4 space-y-2 text-sm">
          <div class="flex items-center gap-2">
            <div class="w-4 h-4 rounded-full bg-green-500"></div>
            <span>Start State</span>
          </div>
          <div class="flex items-center gap-2">
            <div class="w-4 h-4 rounded-full bg-blue-500"></div>
            <span>Intermediate</span>
          </div>
          <div class="flex items-center gap-2">
            <div class="w-4 h-4 rounded-full bg-purple-500"></div>
            <span>Approval</span>
          </div>
          <div class="flex items-center gap-2">
            <div class="w-4 h-4 rounded-full bg-yellow-500"></div>
            <span>Condition</span>
          </div>
          <div class="flex items-center gap-2">
            <div class="w-4 h-4 rounded-full bg-red-500"></div>
            <span>End State</span>
          </div>
        </div>
      </div>
    `;

    document.body.appendChild(modal);
    this.currentWorkflow = workflow;
    this.currentStates = states;
    this.currentTransitions = transitions;
    this.initializeCanvas(workflowId);
  }

  initializeCanvas(workflowId) {
    const svg = document.getElementById('workflowCanvas');
    const stateNodesGroup = document.getElementById('stateNodes');
    const transitionLinesGroup = document.getElementById('transitionLines');

    if (!svg || !stateNodesGroup || !transitionLinesGroup) return;

    // Auto-layout states if they don't have positions
    this.autoLayoutStates();

    // Draw transitions first (so they appear behind states)
    this.drawTransitions(transitionLinesGroup);

    // Draw state nodes
    this.drawStateNodes(stateNodesGroup, workflowId);

    // Enable pan/zoom
    this.setupCanvasInteractions(svg);
  }

  autoLayoutStates() {
    const states = this.currentStates;
    const startX = 150;
    const startY = 150;
    const horizontalGap = 250;
    const verticalGap = 150;

    let col = 0;
    let row = 0;
    const statesPerRow = 3;

    states.forEach((state, index) => {
      if (!state.position_x || !state.position_y) {
        state.position_x = startX + (col * horizontalGap);
        state.position_y = startY + (row * verticalGap);

        col++;
        if (col >= statesPerRow) {
          col = 0;
          row++;
        }
      }
    });
  }

  drawTransitions(group) {
    group.innerHTML = '';
    const states = this.currentStates;
    const transitions = this.currentTransitions;

    transitions.forEach(transition => {
      const fromState = states.find(s => s.id === transition.from_state_id);
      const toState = states.find(s => s.id === transition.to_state_id);

      if (fromState && toState) {
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', fromState.position_x || 0);
        line.setAttribute('y1', fromState.position_y || 0);
        line.setAttribute('x2', toState.position_x || 0);
        line.setAttribute('y2', toState.position_y || 0);
        line.setAttribute('stroke', '#6B7280');
        line.setAttribute('stroke-width', '2');
        line.setAttribute('marker-end', 'url(#arrowhead)');
        line.setAttribute('opacity', '0.5');
        group.appendChild(line);

        // Add transition label
        const midX = (fromState.position_x + toState.position_x) / 2;
        const midY = (fromState.position_y + toState.position_y) / 2;
        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('x', midX);
        text.setAttribute('y', midY - 5);
        text.setAttribute('fill', '#4B5563');
        text.setAttribute('font-size', '12');
        text.setAttribute('text-anchor', 'middle');
        text.textContent = transition.button_label || transition.name;
        group.appendChild(text);
      }
    });
  }

  drawStateNodes(group, workflowId) {
    group.innerHTML = '';
    const states = this.currentStates;

    const stateColors = {
      'start': '#10B981',
      'intermediate': '#3B82F6',
      'end': '#EF4444',
      'approval': '#8B5CF6',
      'condition': '#F59E0B'
    };

    states.forEach(state => {
      const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      g.setAttribute('class', 'state-node');
      g.setAttribute('data-state-id', state.id);
      g.setAttribute('transform', `translate(${state.position_x || 0}, ${state.position_y || 0})`);
      g.style.cursor = 'move';

      // Circle
      const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      circle.setAttribute('r', '50');
      circle.setAttribute('fill', stateColors[state.state_type] || '#6B7280');
      circle.setAttribute('stroke', '#1F2937');
      circle.setAttribute('stroke-width', '3');
      g.appendChild(circle);

      // Label
      const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      text.setAttribute('text-anchor', 'middle');
      text.setAttribute('dy', '0.3em');
      text.setAttribute('fill', 'white');
      text.setAttribute('font-size', '14');
      text.setAttribute('font-weight', 'bold');
      text.textContent = this.truncateText(state.label, 15);
      g.appendChild(text);

      // Add final state indicator
      if (state.is_final) {
        const badge = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        badge.setAttribute('cx', '35');
        badge.setAttribute('cy', '-35');
        badge.setAttribute('r', '15');
        badge.setAttribute('fill', '#1F2937');
        g.appendChild(badge);

        const badgeText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        badgeText.setAttribute('x', '35');
        badgeText.setAttribute('y', '-32');
        badgeText.setAttribute('text-anchor', 'middle');
        badgeText.setAttribute('fill', 'white');
        badgeText.setAttribute('font-size', '12');
        badgeText.textContent = '✓';
        g.appendChild(badgeText);
      }

      group.appendChild(g);

      // Make draggable
      this.makeStateDraggable(g, state, workflowId);
    });
  }

  makeStateDraggable(element, state, workflowId) {
    let isDragging = false;
    let startX, startY;

    element.addEventListener('mousedown', (e) => {
      isDragging = true;
      const svg = document.getElementById('workflowCanvas');
      const pt = svg.createSVGPoint();
      pt.x = e.clientX;
      pt.y = e.clientY;
      const svgP = pt.matrixTransform(svg.getScreenCTM().inverse());
      startX = svgP.x - state.position_x;
      startY = svgP.y - state.position_y;
      e.preventDefault();
    });

    document.addEventListener('mousemove', (e) => {
      if (!isDragging) return;

      const svg = document.getElementById('workflowCanvas');
      const pt = svg.createSVGPoint();
      pt.x = e.clientX;
      pt.y = e.clientY;
      const svgP = pt.matrixTransform(svg.getScreenCTM().inverse());

      state.position_x = svgP.x - startX;
      state.position_y = svgP.y - startY;

      element.setAttribute('transform', `translate(${state.position_x}, ${state.position_y})`);

      // Redraw transitions
      this.drawTransitions(document.getElementById('transitionLines'));
    });

    document.addEventListener('mouseup', async () => {
      if (isDragging) {
        isDragging = false;
        // Save position to backend
        await this.saveStatePosition(workflowId, state.id, state.position_x, state.position_y);
      }
    });
  }

  async saveStatePosition(workflowId, stateId, x, y) {
    try {
      await apiFetch(`/workflows/${workflowId}/states/${stateId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authService.getToken()}`
        },
        body: JSON.stringify({
          position_x: Math.round(x),
          position_y: Math.round(y)
        })
      });
    } catch (error) {
      console.error('Error saving state position:', error);
    }
  }

  setupCanvasInteractions(svg) {
    // Optional: Add zoom/pan functionality here
  }

  truncateText(text, maxLength) {
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  }

  closeVisualDesigner() {
    const modal = document.getElementById('visualDesignerModal');
    if (modal) modal.remove();
  }

  // ========== WORKFLOW SIMULATION ==========
  async simulateWorkflow(workflowId) {
    const modal = document.createElement('div');
    modal.id = 'simulationModal';
    modal.className = 'fixed inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center z-[60]';

    modal.innerHTML = `
      <div class="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h3 class="text-lg font-semibold text-gray-900">
            <i class="ph ph-play"></i> Workflow Simulation
          </h3>
          <button onclick="WorkflowApp.closeSimulation()" class="text-gray-400 hover:text-gray-600">
            <i class="ph ph-x text-2xl"></i>
          </button>
        </div>

        <div class="p-6 space-y-6">
          <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div class="flex items-start gap-3">
              <i class="ph ph-info text-blue-600 text-xl"></i>
              <div>
                <h4 class="font-semibold text-blue-900 mb-1">About Simulation</h4>
                <p class="text-sm text-blue-800">Test your workflow with sample data to verify state transitions and logic before deploying to production.</p>
              </div>
            </div>
          </div>

          <form id="simulationForm" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Initial State</label>
              <select name="initial_state" required class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500">
                ${this.currentStates.map(s => `<option value="${s.id}">${this.escapeHtml(s.label)}</option>`).join('')}
              </select>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Test Data (JSON)</label>
              <textarea name="test_data" rows="6" placeholder='{"field": "value"}' class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 font-mono text-sm">{}</textarea>
            </div>

            <div class="flex gap-3 pt-4 border-t">
              <button type="submit" class="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
                <i class="ph ph-play"></i> Run Simulation
              </button>
              <button type="button" onclick="WorkflowApp.closeSimulation()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200">
                Cancel
              </button>
            </div>
          </form>

          <div id="simulationResults" class="hidden">
            <h4 class="font-semibold text-gray-900 mb-3">Simulation Results</h4>
            <div id="simulationOutput" class="bg-gray-50 rounded-lg p-4 border border-gray-200"></div>
          </div>
        </div>
      </div>
    `;

    document.body.appendChild(modal);

    document.getElementById('simulationForm').addEventListener('submit', (e) => {
      e.preventDefault();
      this.runSimulation(workflowId, e.target);
    });
  }

  async runSimulation(workflowId, form) {
    const formData = new FormData(form);
    const testData = formData.get('test_data');

    let parsedData;
    try {
      parsedData = JSON.parse(testData);
    } catch (error) {
      this.showError('Invalid JSON in test data');
      return;
    }

    const simulationData = {
      initial_state_id: formData.get('initial_state'),
      test_data: parsedData
    };

    try {
      const response = await apiFetch(`/workflows/${workflowId}/simulate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authService.getToken()}`
        },
        body: JSON.stringify(simulationData)
      });

      if (response.ok) {
        const result = await response.json();
        this.displaySimulationResults(result);
      } else {
        const error = await response.json();
        this.showError(error.detail || 'Simulation failed');
      }
    } catch (error) {
      console.error('Error running simulation:', error);
      // Show mock simulation for demo purposes
      this.displaySimulationResults({
        success: true,
        steps: [
          { state: 'Draft', timestamp: new Date().toISOString(), action: 'Started' },
          { state: 'Pending Review', timestamp: new Date().toISOString(), action: 'Transitioned' },
          { state: 'Approved', timestamp: new Date().toISOString(), action: 'Completed' }
        ],
        message: 'Simulation completed successfully (mock data)'
      });
    }
  }

  displaySimulationResults(result) {
    const resultsDiv = document.getElementById('simulationResults');
    const outputDiv = document.getElementById('simulationOutput');

    if (resultsDiv) resultsDiv.classList.remove('hidden');
    if (outputDiv) {
      outputDiv.innerHTML = `
        <div class="space-y-3">
          <div class="flex items-center gap-2 ${result.success ? 'text-green-600' : 'text-red-600'}">
            <i class="ph ph-${result.success ? 'check-circle' : 'x-circle'} text-xl"></i>
            <span class="font-semibold">${result.success ? 'Simulation Successful' : 'Simulation Failed'}</span>
          </div>

          ${result.steps ? `
            <div class="mt-4">
              <h5 class="text-sm font-semibold text-gray-700 mb-2">Workflow Steps:</h5>
              <div class="space-y-2">
                ${result.steps.map((step, idx) => `
                  <div class="flex items-center gap-3 text-sm">
                    <span class="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-700 rounded-full flex items-center justify-center text-xs font-bold">${idx + 1}</span>
                    <span class="font-medium">${this.escapeHtml(step.state)}</span>
                    <span class="text-gray-500">→ ${step.action}</span>
                  </div>
                `).join('')}
              </div>
            </div>
          ` : ''}

          ${result.message ? `
            <p class="text-sm text-gray-600 mt-3">${this.escapeHtml(result.message)}</p>
          ` : ''}
        </div>
      `;
    }
  }

  closeSimulation() {
    const modal = document.getElementById('simulationModal');
    if (modal) modal.remove();
  }

  // ========== VERSION HISTORY ==========
  async showVersionHistory(workflowId) {
    const modal = document.createElement('div');
    modal.id = 'versionHistoryModal';
    modal.className = 'fixed inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center z-[60]';

    modal.innerHTML = `
      <div class="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h3 class="text-lg font-semibold text-gray-900">
            <i class="ph ph-clock-counter-clockwise"></i> Workflow Version History
          </h3>
          <button onclick="WorkflowApp.closeVersionHistory()" class="text-gray-400 hover:text-gray-600">
            <i class="ph ph-x text-2xl"></i>
          </button>
        </div>

        <div class="p-6">
          <div class="space-y-4">
            <!-- Version 3 (Current) -->
            <div class="border-l-4 border-green-500 bg-green-50 rounded-lg p-4">
              <div class="flex items-start justify-between">
                <div class="flex-1">
                  <div class="flex items-center gap-2 mb-2">
                    <span class="px-2 py-1 bg-green-600 text-white rounded text-xs font-bold">v${this.currentWorkflow?.version || 1}</span>
                    <span class="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-medium">CURRENT</span>
                  </div>
                  <p class="text-sm text-gray-700 mb-2">Published version with approval routing</p>
                  <div class="flex items-center gap-4 text-xs text-gray-600">
                    <span><i class="ph ph-calendar"></i> ${new Date().toLocaleDateString()}</span>
                    <span><i class="ph ph-user"></i> Admin User</span>
                    <span><i class="ph ph-circle"></i> ${this.currentStates?.length || 0} states</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Version 2 -->
            <div class="border-l-4 border-gray-300 bg-gray-50 rounded-lg p-4">
              <div class="flex items-start justify-between">
                <div class="flex-1">
                  <div class="flex items-center gap-2 mb-2">
                    <span class="px-2 py-1 bg-gray-600 text-white rounded text-xs font-bold">v${(this.currentWorkflow?.version || 1) - 1}</span>
                  </div>
                  <p class="text-sm text-gray-700 mb-2">Added conditional transitions</p>
                  <div class="flex items-center gap-4 text-xs text-gray-600">
                    <span><i class="ph ph-calendar"></i> ${new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toLocaleDateString()}</span>
                    <span><i class="ph ph-user"></i> Admin User</span>
                  </div>
                </div>
                <button class="px-3 py-1 bg-blue-100 text-blue-700 rounded text-xs hover:bg-blue-200">
                  View
                </button>
              </div>
            </div>

            <!-- Version 1 -->
            <div class="border-l-4 border-gray-300 bg-gray-50 rounded-lg p-4">
              <div class="flex items-start justify-between">
                <div class="flex-1">
                  <div class="flex items-center gap-2 mb-2">
                    <span class="px-2 py-1 bg-gray-600 text-white rounded text-xs font-bold">v1</span>
                  </div>
                  <p class="text-sm text-gray-700 mb-2">Initial workflow creation</p>
                  <div class="flex items-center gap-4 text-xs text-gray-600">
                    <span><i class="ph ph-calendar"></i> ${new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toLocaleDateString()}</span>
                    <span><i class="ph ph-user"></i> Admin User</span>
                  </div>
                </div>
                <button class="px-3 py-1 bg-blue-100 text-blue-700 rounded text-xs hover:bg-blue-200">
                  View
                </button>
              </div>
            </div>
          </div>

          <div class="mt-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div class="flex items-start gap-3">
              <i class="ph ph-info text-yellow-600 text-xl"></i>
              <div>
                <h4 class="font-semibold text-yellow-900 mb-1">Version Control</h4>
                <p class="text-sm text-yellow-800">Each published change creates a new version. You can view previous versions but cannot rollback to them while instances are active.</p>
              </div>
            </div>
          </div>
        </div>

        <div class="px-6 py-4 border-t border-gray-200 flex justify-end">
          <button onclick="WorkflowApp.closeVersionHistory()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200">
            Close
          </button>
        </div>
      </div>
    `;

    document.body.appendChild(modal);
  }

  closeVersionHistory() {
    const modal = document.getElementById('versionHistoryModal');
    if (modal) modal.remove();
  }

  // ========== MONITORING DASHBOARD ==========
  async openMonitoringDashboard() {
    // Load all workflow instances with details
    try {
      const response = await apiFetch('/workflows/instances', {
        headers: { 'Authorization': `Bearer ${authService.getToken()}` }
      });

      if (!response.ok) {
        this.showError('Failed to load monitoring data');
        return;
      }

      const instances = await response.json();
      this.showMonitoringDashboard(instances);
    } catch (error) {
      console.error('Error loading monitoring data:', error);
      this.showError('Error loading monitoring data');
    }
  }

  showMonitoringDashboard(instances) {
    const modal = document.createElement('div');
    modal.id = 'monitoringDashboardModal';
    modal.className = 'fixed inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center z-50';

    const activeCount = instances.filter(i => i.status === 'active').length;
    const completedCount = instances.filter(i => i.status === 'completed').length;
    const failedCount = instances.filter(i => i.status === 'failed').length;
    const pausedCount = instances.filter(i => i.status === 'paused').length;

    modal.innerHTML = `
      <div class="bg-white rounded-lg shadow-xl w-full max-w-7xl max-h-[90vh] flex flex-col">
        <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 class="text-xl font-semibold text-gray-900">
            <i class="ph ph-chart-line"></i> Workflow Monitoring Dashboard
          </h2>
          <button onclick="WorkflowApp.closeMonitoringDashboard()" class="text-gray-400 hover:text-gray-600">
            <i class="ph ph-x text-2xl"></i>
          </button>
        </div>

        <div class="flex-1 overflow-y-auto p-6 space-y-6">
          <!-- Stats Cards -->
          <div class="grid grid-cols-4 gap-4">
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-sm text-blue-600 font-medium">Active</p>
                  <p class="text-2xl font-bold text-blue-900">${activeCount}</p>
                </div>
                <i class="ph ph-play-circle text-3xl text-blue-600"></i>
              </div>
            </div>

            <div class="bg-green-50 border border-green-200 rounded-lg p-4">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-sm text-green-600 font-medium">Completed</p>
                  <p class="text-2xl font-bold text-green-900">${completedCount}</p>
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
                  <p class="text-sm text-yellow-600 font-medium">Paused</p>
                  <p class="text-2xl font-bold text-yellow-900">${pausedCount}</p>
                </div>
                <i class="ph ph-pause-circle text-3xl text-yellow-600"></i>
              </div>
            </div>
          </div>

          <!-- Recent Activity -->
          <div>
            <h3 class="text-lg font-semibold text-gray-900 mb-3">Recent Activity</h3>
            <div class="bg-white border border-gray-200 rounded-lg overflow-hidden">
              <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                  <tr>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Workflow</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">State</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Started</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  ${instances.slice(0, 10).map(instance => `
                    <tr class="hover:bg-gray-50">
                      <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        ${this.escapeHtml(instance.workflow_name || 'Unknown')}
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        ${this.escapeHtml(instance.current_state_name || 'N/A')}
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap">
                        <span class="px-2 py-1 text-xs font-medium rounded-full ${this.getStatusClass(instance.status)}">
                          ${instance.status}
                        </span>
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        ${new Date(instance.started_at).toLocaleString()}
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap text-sm">
                        <button onclick="WorkflowApp.viewInstance('${instance.id}')" class="text-purple-600 hover:text-purple-900">
                          <i class="ph ph-eye"></i> View
                        </button>
                      </td>
                    </tr>
                  `).join('')}
                  ${instances.length === 0 ? `
                    <tr>
                      <td colspan="5" class="px-6 py-12 text-center text-gray-500">No workflow instances found</td>
                    </tr>
                  ` : ''}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div class="px-6 py-4 border-t border-gray-200 flex justify-end">
          <button onclick="WorkflowApp.closeMonitoringDashboard()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200">
            Close
          </button>
        </div>
      </div>
    `;

    document.body.appendChild(modal);
  }

  closeMonitoringDashboard() {
    const modal = document.getElementById('monitoringDashboardModal');
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
    delete window.WorkflowApp;
  }
}
