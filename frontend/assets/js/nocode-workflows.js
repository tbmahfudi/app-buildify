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
      viewInstance: (id) => this.viewInstance(id)
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
      const response = await fetch('/api/v1/workflows', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
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
            <h3 class="text-lg font-semibold text-gray-900">${this.escapeHtml(workflow.label)}</h3>
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
      const response = await fetch('/api/v1/workflows/instances', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
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
      const response = await fetch('/api/v1/workflows', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
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
      const response = await fetch(`/api/v1/workflows/${id}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
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
                <button onclick="WorkflowApp.editWorkflow('${workflow.id}')" class="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700">
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
      const response = await fetch(`/api/v1/workflows/${id}/publish`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
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
      const response = await fetch(`/api/v1/workflows/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
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

  editWorkflow(id) {
    this.showError('Edit feature coming soon - will open visual workflow designer');
  }

  manageStates(id) {
    this.showError('State management UI coming soon');
  }

  viewInstance(id) {
    this.showError('Instance detail view coming soon');
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
