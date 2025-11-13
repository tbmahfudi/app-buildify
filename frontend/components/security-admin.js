/**
 * Security Administration Module
 *
 * Unified component for managing:
 * - Security policies
 * - Locked accounts
 * - Active sessions
 * - Notification configuration
 */

class SecurityAdmin {
  constructor() {
    // Use /api/v1 prefix to work with nginx proxy
    this.apiBase = '/api/v1';
    this.currentTab = 'policies';
    this.data = {
      policies: [],
      lockedAccounts: [],
      sessions: [],
      loginAttempts: [],
      notificationConfig: null
    };
    this.loadError = null; // Track if there was a load error
  }

  async init(containerId) {
    this.containerId = containerId;
    await this.loadAllData();
    this.render();
  }

  async loadAllData() {
    // Get token from localStorage (stored by api.js)
    const tokens = JSON.parse(localStorage.getItem('tokens') || '{}');
    const token = tokens.access;
    const headers = { 'Authorization': `Bearer ${token}` };

    // Helper to fetch and handle errors properly
    const fetchWithErrorHandling = async (url) => {
      try {
        const response = await fetch(url, { headers });

        // Check if response is ok before parsing
        if (!response.ok) {
          // Handle specific error codes
          if (response.status === 403) {
            throw new Error('Access forbidden - you don\'t have permission to access this resource');
          } else if (response.status === 401) {
            throw new Error('Unauthorized - please log in again');
          } else if (response.status === 404) {
            throw new Error('Resource not found');
          } else {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
          }
        }

        return await response.json();
      } catch (error) {
        console.error(`Failed to fetch ${url}:`, error.message);
        throw error; // Re-throw to be caught by outer try-catch
      }
    };

    try {
      this.loadError = null; // Clear any previous errors

      const [policies, locked, sessions, attempts, notifConfig] = await Promise.all([
        fetchWithErrorHandling(`${this.apiBase}/admin/security/policies`),
        fetchWithErrorHandling(`${this.apiBase}/admin/security/locked-accounts`),
        fetchWithErrorHandling(`${this.apiBase}/admin/security/sessions?limit=50`),
        fetchWithErrorHandling(`${this.apiBase}/admin/security/login-attempts?limit=50`),
        fetchWithErrorHandling(`${this.apiBase}/admin/security/notification-config`)
      ]);

      this.data.policies = Array.isArray(policies) ? policies : [];
      this.data.lockedAccounts = Array.isArray(locked) ? locked : [];
      this.data.sessions = Array.isArray(sessions) ? sessions : [];
      this.data.loginAttempts = Array.isArray(attempts) ? attempts : [];
      this.data.notificationConfig = Array.isArray(notifConfig) ? (notifConfig[0] || null) : (notifConfig || null);
    } catch (error) {
      console.error('Failed to load security data:', error);
      this.loadError = error.message || 'Failed to load security data';

      // Set default empty values to prevent rendering errors
      this.data.policies = [];
      this.data.lockedAccounts = [];
      this.data.sessions = [];
      this.data.loginAttempts = [];
      this.data.notificationConfig = null;
    }
  }

  render() {
    const container = document.getElementById(this.containerId);

    // Show error state if data failed to load
    if (this.loadError) {
      const is403 = this.loadError.toLowerCase().includes('forbidden');
      const is401 = this.loadError.toLowerCase().includes('unauthorized');

      container.innerHTML = `
        <div class="h-full flex items-center justify-center bg-gray-50 p-6">
          <div class="max-w-2xl w-full">
            <div class="bg-red-50 border-l-4 border-red-500 p-6 rounded-lg shadow-lg">
              <div class="flex items-start gap-4">
                <i class="ph-duotone ph-${is403 ? 'lock' : is401 ? 'sign-in' : 'warning-circle'} text-red-500 text-4xl flex-shrink-0"></i>
                <div class="flex-1">
                  <h3 class="text-xl font-bold text-red-800 mb-2">
                    ${is403 ? 'Access Forbidden' : is401 ? 'Authentication Required' : 'Failed to Load Security Data'}
                  </h3>

                  <p class="text-red-700 mb-4">
                    ${this.loadError}
                  </p>

                  ${is403 ? `
                    <p class="text-sm text-red-600 mb-4">
                      You need administrator privileges to access security administration features.
                      Please contact your system administrator if you believe you should have access.
                    </p>
                  ` : ''}

                  ${is401 ? `
                    <p class="text-sm text-red-600 mb-4">
                      Your session may have expired. Please log in again to continue.
                    </p>
                  ` : ''}

                  <div class="flex gap-3">
                    <button
                      onclick="window.location.hash = 'dashboard'"
                      class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition flex items-center gap-2 shadow">
                      <i class="ph ph-house"></i>
                      Go to Dashboard
                    </button>

                    ${!is403 ? `
                      <button
                        onclick="window.location.reload()"
                        class="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition flex items-center gap-2 shadow">
                        <i class="ph ph-arrow-clockwise"></i>
                        Retry
                      </button>
                    ` : ''}

                    <button
                      onclick="history.back()"
                      class="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition flex items-center gap-2">
                      <i class="ph ph-arrow-left"></i>
                      Go Back
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      `;
      return;
    }

    // Normal render when data loaded successfully
    container.innerHTML = `
      <div class="h-full flex flex-col bg-gray-50">
        <!-- Header -->
        <div class="bg-white border-b px-6 py-4">
          <h1 class="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <i class="ph-duotone ph-shield-star text-blue-600"></i>
            Security Administration
          </h1>
          <p class="text-gray-600 mt-1">Manage security policies, locked accounts, and sessions</p>
        </div>

        <!-- Tabs -->
        <div class="bg-white border-b px-6">
          <div id="tabButtons" class="flex gap-6">
            ${this.renderTabButtons()}
          </div>
        </div>

        <!-- Content -->
        <div class="flex-1 overflow-y-auto p-6">
          <div id="tabContent">${this.renderTabContent()}</div>
        </div>
      </div>
    `;

    // Attach event listeners
    this.attachEventListeners();
  }

  renderTab(id, icon, label, count) {
    const isActive = this.currentTab === id;
    return `
      <button onclick="securityAdmin.switchTab('${id}')"
              class="flex items-center gap-2 px-4 py-3 border-b-2 transition ${
                isActive
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }">
        <i class="ph-duotone ph-${icon}"></i>
        <span class="font-medium">${label}</span>
        ${count > 0 ? `<span class="px-2 py-0.5 bg-gray-100 text-gray-700 text-xs rounded-full">${count}</span>` : ''}
      </button>
    `;
  }

  renderTabContent() {
    switch (this.currentTab) {
      case 'policies':
        return this.renderPoliciesTab();
      case 'locked':
        return this.renderLockedAccountsTab();
      case 'sessions':
        return this.renderSessionsTab();
      case 'attempts':
        return this.renderAttemptsTab();
      case 'notifications':
        return this.renderNotificationsTab();
      default:
        return '';
    }
  }

  renderPoliciesTab() {
    // Defensive check to ensure policies is always an array
    const policies = Array.isArray(this.data.policies) ? this.data.policies : [];

    return `
      <div>
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-xl font-semibold text-gray-900">Security Policies</h2>
          <button onclick="securityAdmin.showPolicyDialog()"
                  class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2">
            <i class="ph ph-plus"></i>
            New Policy
          </button>
        </div>

        <div class="grid gap-4">
          ${policies.length === 0 ? `
            <div class="text-center py-12 text-gray-500">
              <i class="ph-duotone ph-shield-star text-6xl mb-4"></i>
              <p>No security policies configured</p>
            </div>
          ` : policies.map(policy => `
            <div class="bg-white rounded-lg shadow-sm border p-6">
              <div class="flex justify-between items-start mb-4">
                <div>
                  <div class="flex items-center gap-2 mb-1">
                    <h3 class="text-lg font-semibold">${policy.policy_name}</h3>
                    ${policy.tenant_id === null ?
                      '<span class="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded-full">System Default</span>' :
                      '<span class="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full">Tenant</span>'
                    }
                  </div>
                  <p class="text-sm text-gray-600">${policy.policy_type}</p>
                </div>
                <div class="flex gap-2">
                  <button onclick="securityAdmin.editPolicy('${policy.id}')" class="p-2 hover:bg-gray-100 rounded">
                    <i class="ph ph-pencil text-gray-600"></i>
                  </button>
                  ${policy.tenant_id ? `
                    <button onclick="securityAdmin.deletePolicy('${policy.id}')" class="p-2 hover:bg-red-50 rounded">
                      <i class="ph ph-trash text-red-600"></i>
                    </button>
                  ` : ''}
                </div>
              </div>
              <div class="grid grid-cols-3 gap-4 text-sm">
                <div class="border-l-2 border-blue-500 pl-3">
                  <p class="font-medium text-gray-700">Password</p>
                  <p class="text-gray-600">Min: ${policy.password_min_length || 'N/A'}, Expires: ${policy.password_expiration_days || 'Never'} days</p>
                </div>
                <div class="border-l-2 border-red-500 pl-3">
                  <p class="font-medium text-gray-700">Lockout</p>
                  <p class="text-gray-600">Max: ${policy.login_max_attempts || 'N/A'} attempts, ${policy.login_lockout_type || 'N/A'}</p>
                </div>
                <div class="border-l-2 border-green-500 pl-3">
                  <p class="font-medium text-gray-700">Session</p>
                  <p class="text-gray-600">Timeout: ${policy.session_timeout_minutes || 'N/A'}min, Max: ${policy.session_max_concurrent || '∞'}</p>
                </div>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  renderLockedAccountsTab() {
    // Defensive check to ensure lockedAccounts is always an array
    const lockedAccounts = Array.isArray(this.data.lockedAccounts) ? this.data.lockedAccounts : [];

    return `
      <div>
        <h2 class="text-xl font-semibold text-gray-900 mb-4">Locked User Accounts</h2>

        ${lockedAccounts.length === 0 ? `
          <div class="text-center py-12 text-gray-500">
            <i class="ph-duotone ph-lock-open text-6xl mb-4"></i>
            <p>No locked accounts</p>
          </div>
        ` : `
          <div class="bg-white rounded-lg shadow-sm border">
            <table class="w-full">
              <thead class="bg-gray-50 border-b">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">User</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Locked Until</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Failed Attempts</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody class="divide-y">
                ${lockedAccounts.map(account => `
                  <tr>
                    <td class="px-6 py-4">${account.full_name || 'N/A'}</td>
                    <td class="px-6 py-4">${account.email}</td>
                    <td class="px-6 py-4">${new Date(account.locked_until).toLocaleString()}</td>
                    <td class="px-6 py-4">${account.failed_attempts}</td>
                    <td class="px-6 py-4">
                      <button onclick="securityAdmin.unlockAccount('${account.user_id}')"
                              class="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700">
                        Unlock
                      </button>
                    </td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        `}
      </div>
    `;
  }

  renderSessionsTab() {
    // Defensive check to ensure sessions is always an array
    const sessions = Array.isArray(this.data.sessions) ? this.data.sessions : [];

    return `
      <div>
        <h2 class="text-xl font-semibold text-gray-900 mb-4">Active User Sessions</h2>

        ${sessions.length === 0 ? `
          <div class="text-center py-12 text-gray-500">
            <i class="ph-duotone ph-devices text-6xl mb-4"></i>
            <p>No active sessions</p>
          </div>
        ` : `
          <div class="bg-white rounded-lg shadow-sm border">
            <table class="w-full">
              <thead class="bg-gray-50 border-b">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Device</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">IP Address</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Last Activity</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Expires</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody class="divide-y">
                ${sessions.map(session => `
                  <tr>
                    <td class="px-6 py-4">
                      <div class="flex items-center gap-2">
                        <i class="ph ph-device-mobile text-gray-400"></i>
                        <span>${session.device_name || 'Unknown Device'}</span>
                      </div>
                    </td>
                    <td class="px-6 py-4 text-sm text-gray-600">${session.ip_address || 'N/A'}</td>
                    <td class="px-6 py-4 text-sm text-gray-600">${new Date(session.last_activity).toLocaleString()}</td>
                    <td class="px-6 py-4 text-sm text-gray-600">${new Date(session.expires_at).toLocaleString()}</td>
                    <td class="px-6 py-4">
                      <button onclick="securityAdmin.revokeSession('${session.id}')"
                              class="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700">
                        Revoke
                      </button>
                    </td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        `}
      </div>
    `;
  }

  renderAttemptsTab() {
    // Defensive check to ensure loginAttempts is always an array
    const loginAttempts = Array.isArray(this.data.loginAttempts) ? this.data.loginAttempts : [];

    return `
      <div>
        <h2 class="text-xl font-semibold text-gray-900 mb-4">Recent Login Attempts</h2>

        ${loginAttempts.length === 0 ? `
          <div class="text-center py-12 text-gray-500">
            <i class="ph-duotone ph-list-checks text-6xl mb-4"></i>
            <p>No login attempts recorded</p>
          </div>
        ` : `
          <div class="bg-white rounded-lg shadow-sm border">
            <table class="w-full">
              <thead class="bg-gray-50 border-b">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">IP Address</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Reason</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
                </tr>
              </thead>
              <tbody class="divide-y">
                ${loginAttempts.map(attempt => `
                <tr>
                  <td class="px-6 py-4">${attempt.email}</td>
                  <td class="px-6 py-4 text-sm text-gray-600">${attempt.ip_address || 'N/A'}</td>
                  <td class="px-6 py-4">
                    ${attempt.success ?
                      '<span class="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">Success</span>' :
                      '<span class="px-2 py-1 bg-red-100 text-red-700 text-xs rounded-full">Failed</span>'
                    }
                  </td>
                  <td class="px-6 py-4 text-sm text-gray-600">${attempt.failure_reason || '-'}</td>
                  <td class="px-6 py-4 text-sm text-gray-600">${new Date(attempt.created_at).toLocaleString()}</td>
                </tr>
              `).join('')}
              </tbody>
            </table>
          </div>
        `}
      </div>
    `;
  }

  renderNotificationsTab() {
    const config = this.data.notificationConfig;
    return `
      <div>
        <h2 class="text-xl font-semibold text-gray-900 mb-4">Notification Configuration</h2>

        <div class="bg-white rounded-lg shadow-sm border p-6">
          <p class="text-gray-600 mb-4">Configure notification delivery methods and settings.</p>

          ${config ? `
            <div class="space-y-4">
              <div class="border-b pb-4">
                <h3 class="font-semibold mb-2">Account Locked</h3>
                <p class="text-sm text-gray-600">Enabled: ${config.account_locked_enabled ? 'Yes' : 'No'}</p>
                <p class="text-sm text-gray-600">Methods: ${config.account_locked_methods?.join(', ') || 'None'}</p>
              </div>

              <div class="border-b pb-4">
                <h3 class="font-semibold mb-2">Password Expiring</h3>
                <p class="text-sm text-gray-600">Enabled: ${config.password_expiring_enabled ? 'Yes' : 'No'}</p>
                <p class="text-sm text-gray-600">Methods: ${config.password_expiring_methods?.join(', ') || 'None'}</p>
              </div>

              <div class="border-b pb-4">
                <h3 class="font-semibold mb-2">Email Configuration</h3>
                <p class="text-sm text-gray-600">Enabled: ${config.email_enabled ? 'Yes' : 'No'}</p>
                <p class="text-sm text-gray-600">From: ${config.email_from || 'Not configured'}</p>
                <p class="text-sm text-gray-600">SMTP Host: ${config.email_smtp_host || 'Not configured'}</p>
              </div>

              <button onclick="securityAdmin.editNotificationConfig()"
                      class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                Edit Configuration
              </button>
            </div>
          ` : `
            <p class="text-gray-500">No notification configuration found. Contact system administrator.</p>
          `}
        </div>
      </div>
    `;
  }

  renderTabButtons() {
    // Defensive checks to ensure all data properties are arrays
    const policies = Array.isArray(this.data.policies) ? this.data.policies : [];
    const lockedAccounts = Array.isArray(this.data.lockedAccounts) ? this.data.lockedAccounts : [];
    const sessions = Array.isArray(this.data.sessions) ? this.data.sessions : [];
    const loginAttempts = Array.isArray(this.data.loginAttempts) ? this.data.loginAttempts : [];

    return `
      ${this.renderTab('policies', 'shield-check', 'Policies', policies.length)}
      ${this.renderTab('locked', 'lock', 'Locked Accounts', lockedAccounts.length)}
      ${this.renderTab('sessions', 'devices', 'Active Sessions', sessions.length)}
      ${this.renderTab('attempts', 'list-checks', 'Login Attempts', loginAttempts.length)}
      ${this.renderTab('notifications', 'bell', 'Notifications', 0)}
    `;
  }

  switchTab(tab) {
    this.currentTab = tab;
    // Update both tab buttons and content
    document.getElementById('tabButtons').innerHTML = this.renderTabButtons();
    document.getElementById('tabContent').innerHTML = this.renderTabContent();
  }

  async unlockAccount(userId) {
    const reason = prompt('Enter reason for unlocking:');
    if (!reason) return;

    try {
      const tokens = JSON.parse(localStorage.getItem('tokens') || '{}');
      const response = await fetch(`${this.apiBase}/admin/security/unlock-account`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${tokens.access}`
        },
        body: JSON.stringify({ user_id: userId, reason })
      });

      if (response.ok) {
        alert('Account unlocked successfully');
        await this.loadAllData();
        this.render();
      } else {
        alert('Failed to unlock account');
      }
    } catch (error) {
      alert('Failed to unlock account');
    }
  }

  async revokeSession(sessionId) {
    if (!confirm('Are you sure you want to revoke this session?')) return;

    try {
      const tokens = JSON.parse(localStorage.getItem('tokens') || '{}');
      const response = await fetch(`${this.apiBase}/admin/security/sessions/revoke`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${tokens.access}`
        },
        body: JSON.stringify({ session_id: sessionId })
      });

      if (response.ok) {
        alert('Session revoked successfully');
        await this.loadAllData();
        this.render();
      } else {
        alert('Failed to revoke session');
      }
    } catch (error) {
      alert('Failed to revoke session');
    }
  }

  showPolicyDialog() {
    // Implementation for creating new policy dialog
    alert('Policy creation dialog - implement with modal');
  }

  editPolicy(policyId) {
    // Implementation for editing policy
    alert(`Edit policy ${policyId} - implement with modal`);
  }

  async deletePolicy(policyId) {
    if (!confirm('Are you sure you want to delete this policy?')) return;

    try {
      const tokens = JSON.parse(localStorage.getItem('tokens') || '{}');
      const response = await fetch(`${this.apiBase}/admin/security/policies/${policyId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${tokens.access}`
        }
      });

      if (response.ok) {
        await this.loadAllData();
        this.render();
      } else {
        alert('Failed to delete policy');
      }
    } catch (error) {
      alert('Failed to delete policy');
    }
  }

  editNotificationConfig() {
    alert('Notification config editor - implement with modal');
  }

  attachEventListeners() {
    // Additional event listeners can be attached here
  }
}

// Global instance
window.securityAdmin = new SecurityAdmin();
