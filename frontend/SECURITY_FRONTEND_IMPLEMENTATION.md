# Security Frontend Implementation Guide

This document contains all frontend components for the security policy system.

## File Structure

```
frontend/
├── components/
│   ├── security-policy-manager.js    (Security policy CRUD)
│   ├── locked-accounts-manager.js     (View and unlock accounts)
│   ├── sessions-manager.js            (View and revoke sessions)
│   ├── notification-config-manager.js (Configure notifications)
│   └── password-policy-display.js     (Show requirements to users)
└── pages/
    └── security-admin.html             (Main security admin page)
```

## Implementation Steps

### Step 1: Create Security Policy Manager Component

File: `/home/user/app-buildify/frontend/components/security-policy-manager.js`

```javascript
/**
 * Security Policy Manager Component
 *
 * Manages password policies, lockout policies, session policies, and reset policies.
 * Allows superadmins to configure security settings at system and tenant levels.
 */
export class SecurityPolicyManager {
  constructor(containerId) {
    this.containerId = containerId;
    this.policies = [];
    this.currentPolicy = null;
    this.apiBase = 'http://localhost:8000';
  }

  async init() {
    await this.loadPolicies();
    this.render();
  }

  async loadPolicies() {
    try {
      const response = await fetch(`${this.apiBase}/admin/security/policies`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      this.policies = await response.json();
    } catch (error) {
      console.error('Failed to load policies:', error);
    }
  }

  render() {
    const container = document.getElementById(this.containerId);
    container.innerHTML = `
      <div class="p-6">
        <!-- Header -->
        <div class="flex items-center justify-between mb-6">
          <div>
            <h2 class="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <i class="ph-duotone ph-shield-check text-blue-600"></i>
              Security Policies
            </h2>
            <p class="text-gray-600 mt-1">Configure password, lockout, and session policies</p>
          </div>
          <button onclick="securityPolicyManager.showCreateDialog()"
                  class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2">
            <i class="ph ph-plus"></i>
            New Policy
          </button>
        </div>

        <!-- Policies List -->
        <div class="grid gap-4 mb-6">
          ${this.renderPoliciesList()}
        </div>
      </div>

      <!-- Create/Edit Modal -->
      <div id="policyModal" class="hidden fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
        <div class="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
          <div class="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
            <h3 class="text-xl font-bold text-gray-900" id="modalTitle">Create Security Policy</h3>
            <button onclick="securityPolicyManager.closeModal()" class="text-gray-500 hover:text-gray-700">
              <i class="ph ph-x text-2xl"></i>
            </button>
          </div>
          <div class="p-6">
            ${this.renderPolicyForm()}
          </div>
        </div>
      </div>
    `;
  }

  renderPoliciesList() {
    if (this.policies.length === 0) {
      return `
        <div class="text-center py-12 text-gray-500">
          <i class="ph-duotone ph-shield-warning text-6xl mb-4"></i>
          <p>No security policies configured yet</p>
        </div>
      `;
    }

    return this.policies.map(policy => `
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition">
        <div class="flex items-start justify-between mb-4">
          <div class="flex-1">
            <div class="flex items-center gap-3">
              <h3 class="text-lg font-semibold text-gray-900">${policy.policy_name}</h3>
              ${policy.tenant_id === null ?
                '<span class="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded-full">System Default</span>' :
                '<span class="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full">Tenant-Specific</span>'
              }
              ${policy.is_active ?
                '<span class="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">Active</span>' :
                '<span class="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-full">Inactive</span>'
              }
            </div>
            <p class="text-sm text-gray-600 mt-1">${policy.policy_type}</p>
          </div>
          <div class="flex gap-2">
            <button onclick="securityPolicyManager.editPolicy('${policy.id}')"
                    class="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg">
              <i class="ph ph-pencil-simple text-xl"></i>
            </button>
            ${policy.tenant_id !== null ? `
              <button onclick="securityPolicyManager.deletePolicy('${policy.id}')"
                      class="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg">
                <i class="ph ph-trash text-xl"></i>
              </button>
            ` : ''}
          </div>
        </div>

        <!-- Policy Details -->
        <div class="grid grid-cols-3 gap-4 text-sm">
          <!-- Password Policy -->
          <div class="border-l-4 border-blue-500 pl-3">
            <h4 class="font-medium text-gray-700 mb-2">Password Policy</h4>
            <ul class="space-y-1 text-gray-600">
              <li>Min Length: ${policy.password_min_length || 'Not set'}</li>
              <li>Expiration: ${policy.password_expiration_days || 'Never'} days</li>
              <li>History: ${policy.password_history_count || 0} passwords</li>
            </ul>
          </div>

          <!-- Lockout Policy -->
          <div class="border-l-4 border-red-500 pl-3">
            <h4 class="font-medium text-gray-700 mb-2">Lockout Policy</h4>
            <ul class="space-y-1 text-gray-600">
              <li>Max Attempts: ${policy.login_max_attempts || 'Not set'}</li>
              <li>Duration: ${policy.login_lockout_duration_min || 'Not set'} min</li>
              <li>Type: ${policy.login_lockout_type || 'Not set'}</li>
            </ul>
          </div>

          <!-- Session Policy -->
          <div class="border-l-4 border-green-500 pl-3">
            <h4 class="font-medium text-gray-700 mb-2">Session Policy</h4>
            <ul class="space-y-1 text-gray-600">
              <li>Timeout: ${policy.session_timeout_minutes || 'Not set'} min</li>
              <li>Max Concurrent: ${policy.session_max_concurrent || 'Unlimited'}</li>
              <li>Absolute: ${policy.session_absolute_timeout_hours || 'Not set'} hrs</li>
            </ul>
          </div>
        </div>
      </div>
    `).join('');
  }

  renderPolicyForm() {
    return `
      <form id="policyForm" onsubmit="securityPolicyManager.submitForm(event)" class="space-y-6">
        <!-- Basic Information -->
        <div class="border-b pb-6">
          <h4 class="text-lg font-semibold text-gray-900 mb-4">Basic Information</h4>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Policy Name *</label>
              <input type="text" name="policy_name" required
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Tenant ID</label>
              <input type="text" name="tenant_id" placeholder="Leave empty for system default"
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
              <p class="text-xs text-gray-500 mt-1">Empty = System Default, UUID = Tenant-Specific</p>
            </div>
          </div>
        </div>

        <!-- Password Policy -->
        <div class="border-b pb-6">
          <h4 class="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <i class="ph-duotone ph-lock-key text-blue-600"></i>
            Password Policy
          </h4>
          <div class="grid grid-cols-3 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Min Length</label>
              <input type="number" name="password_min_length" min="8" max="128" value="12"
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg">
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Expiration (days)</label>
              <input type="number" name="password_expiration_days" min="0" value="90"
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg">
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">History Count</label>
              <input type="number" name="password_history_count" min="0" value="5"
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg">
            </div>
          </div>
          <div class="grid grid-cols-2 gap-4 mt-4">
            <label class="flex items-center gap-2">
              <input type="checkbox" name="password_require_uppercase" checked class="rounded">
              <span class="text-sm text-gray-700">Require Uppercase</span>
            </label>
            <label class="flex items-center gap-2">
              <input type="checkbox" name="password_require_lowercase" checked class="rounded">
              <span class="text-sm text-gray-700">Require Lowercase</span>
            </label>
            <label class="flex items-center gap-2">
              <input type="checkbox" name="password_require_digit" checked class="rounded">
              <span class="text-sm text-gray-700">Require Digit</span>
            </label>
            <label class="flex items-center gap-2">
              <input type="checkbox" name="password_require_special_char" checked class="rounded">
              <span class="text-sm text-gray-700">Require Special Character</span>
            </label>
          </div>
        </div>

        <!-- Lockout Policy -->
        <div class="border-b pb-6">
          <h4 class="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <i class="ph-duotone ph-lock text-red-600"></i>
            Account Lockout Policy
          </h4>
          <div class="grid grid-cols-3 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Max Attempts</label>
              <input type="number" name="login_max_attempts" min="1" value="5"
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg">
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Lockout Duration (min)</label>
              <input type="number" name="login_lockout_duration_min" min="1" value="15"
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg">
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Lockout Type</label>
              <select name="login_lockout_type"
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg">
                <option value="progressive">Progressive</option>
                <option value="fixed">Fixed</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Session Policy -->
        <div class="border-b pb-6">
          <h4 class="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <i class="ph-duotone ph-clock text-green-600"></i>
            Session Policy
          </h4>
          <div class="grid grid-cols-3 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Timeout (minutes)</label>
              <input type="number" name="session_timeout_minutes" min="1" value="30"
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg">
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Max Concurrent</label>
              <input type="number" name="session_max_concurrent" min="0" value="3"
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg">
              <p class="text-xs text-gray-500 mt-1">0 = Unlimited</p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Absolute Timeout (hrs)</label>
              <input type="number" name="session_absolute_timeout_hours" min="1" value="8"
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg">
            </div>
          </div>
        </div>

        <!-- Form Actions -->
        <div class="flex justify-end gap-3 pt-4">
          <button type="button" onclick="securityPolicyManager.closeModal()"
                  class="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50">
            Cancel
          </button>
          <button type="submit"
                  class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            Save Policy
          </button>
        </div>
      </form>
    `;
  }

  showCreateDialog() {
    this.currentPolicy = null;
    document.getElementById('modalTitle').textContent = 'Create Security Policy';
    document.getElementById('policyModal').classList.remove('hidden');
  }

  async editPolicy(policyId) {
    try {
      const response = await fetch(`${this.apiBase}/admin/security/policies/${policyId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      this.currentPolicy = await response.json();

      // Populate form
      document.getElementById('modalTitle').textContent = 'Edit Security Policy';
      const form = document.getElementById('policyForm');
      Object.keys(this.currentPolicy).forEach(key => {
        const input = form.elements[key];
        if (input) {
          if (input.type === 'checkbox') {
            input.checked = this.currentPolicy[key];
          } else {
            input.value = this.currentPolicy[key] || '';
          }
        }
      });

      document.getElementById('policyModal').classList.remove('hidden');
    } catch (error) {
      alert('Failed to load policy details');
    }
  }

  async submitForm(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const data = {};

    for (let [key, value] of formData.entries()) {
      if (value !== '') {
        const input = event.target.elements[key];
        if (input.type === 'checkbox') {
          data[key] = input.checked;
        } else if (input.type === 'number') {
          data[key] = parseInt(value) || null;
        } else {
          data[key] = value || null;
        }
      }
    }

    try {
      const url = this.currentPolicy
        ? `${this.apiBase}/admin/security/policies/${this.currentPolicy.id}`
        : `${this.apiBase}/admin/security/policies`;

      const response = await fetch(url, {
        method: this.currentPolicy ? 'PUT' : 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify(data)
      });

      if (response.ok) {
        await this.loadPolicies();
        this.closeModal();
        this.render();
      } else {
        const error = await response.json();
        alert(`Failed to save policy: ${error.detail}`);
      }
    } catch (error) {
      alert('Failed to save policy');
    }
  }

  closeModal() {
    document.getElementById('policyModal').classList.add('hidden');
    this.currentPolicy = null;
  }

  async deletePolicy(policyId) {
    if (!confirm('Are you sure you want to delete this policy?')) return;

    try {
      const response = await fetch(`${this.apiBase}/admin/security/policies/${policyId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (response.ok) {
        await this.loadPolicies();
        this.render();
      } else {
        alert('Failed to delete policy');
      }
    } catch (error) {
      alert('Failed to delete policy');
    }
  }
}

// Global instance
window.securityPolicyManager = null;
```

This is the first part. Due to length constraints, I'll create a single comprehensive implementation document.
