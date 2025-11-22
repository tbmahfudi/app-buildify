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
        <div class="flex justify-between items-center mb-6">
          <div>
            <h2 class="text-xl font-semibold text-gray-900">Security Policies</h2>
            <p class="text-sm text-gray-600 mt-1">Manage password, lockout, session, and reset policies</p>
          </div>
          <button onclick="securityAdmin.showPolicyDialog()"
                  class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2 shadow-sm">
            <i class="ph ph-plus"></i>
            New Policy
          </button>
        </div>

        ${policies.length === 0 ? `
          <div class="bg-white rounded-lg shadow-sm border p-12 text-center">
            <i class="ph-duotone ph-shield-star text-gray-400 text-6xl mb-4"></i>
            <h3 class="text-lg font-semibold text-gray-900 mb-2">No Security Policies</h3>
            <p class="text-gray-600 mb-4">Get started by creating your first security policy</p>
            <button onclick="securityAdmin.showPolicyDialog()"
                    class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 inline-flex items-center gap-2">
              <i class="ph ph-plus"></i>
              Create Policy
            </button>
          </div>
        ` : `
          <div class="space-y-4">
            ${policies.map(policy => `
              <div class="bg-white rounded-lg shadow-sm border hover:shadow-md transition-shadow">
                <!-- Policy Header -->
                <div class="p-6 border-b bg-gradient-to-r from-gray-50 to-white">
                  <div class="flex justify-between items-start">
                    <div class="flex-1">
                      <div class="flex items-center gap-3 mb-2">
                        <h3 class="text-lg font-semibold text-gray-900">${policy.policy_name}</h3>
                        ${policy.tenant_id === null ?
                          '<span class="px-3 py-1 bg-purple-100 text-purple-700 text-xs font-medium rounded-full">System Default</span>' :
                          '<span class="px-3 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded-full">Tenant Policy</span>'
                        }
                        <span class="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">${policy.policy_type}</span>
                      </div>
                      <div class="flex items-center gap-4 text-xs text-gray-500">
                        ${policy.created_at ? `<span><i class="ph ph-calendar"></i> Created ${new Date(policy.created_at).toLocaleDateString()}</span>` : ''}
                        ${policy.updated_at ? `<span><i class="ph ph-clock-clockwise"></i> Updated ${new Date(policy.updated_at).toLocaleDateString()}</span>` : ''}
                      </div>
                    </div>
                    <div class="flex gap-2">
                      <button onclick="securityAdmin.editPolicy('${policy.id}')"
                              class="p-2 hover:bg-blue-50 rounded-lg transition flex items-center gap-1 text-blue-600">
                        <i class="ph ph-pencil"></i>
                        <span class="text-sm">Edit</span>
                      </button>
                      ${policy.tenant_id !== null ? `
                        <button onclick="securityAdmin.deletePolicy('${policy.id}')"
                                class="p-2 hover:bg-red-50 rounded-lg transition flex items-center gap-1 text-red-600">
                          <i class="ph ph-trash"></i>
                          <span class="text-sm">Delete</span>
                        </button>
                      ` : ''}
                    </div>
                  </div>
                </div>

                <!-- Policy Details -->
                <div class="p-6">
                  <div class="grid grid-cols-2 gap-6">
                    <!-- Password Policy -->
                    <div class="space-y-3">
                      <h4 class="font-semibold text-gray-900 flex items-center gap-2 border-b pb-2">
                        <i class="ph-duotone ph-lock-key text-blue-600"></i>
                        Password Policy
                      </h4>
                      <div class="space-y-2 text-sm">
                        <div class="flex justify-between">
                          <span class="text-gray-600">Length:</span>
                          <span class="font-medium">${policy.password_min_length || '-'} - ${policy.password_max_length || '-'} chars</span>
                        </div>
                        <div class="flex justify-between">
                          <span class="text-gray-600">Requirements:</span>
                          <div class="flex gap-1">
                            ${policy.password_require_uppercase ? '<span class="px-1.5 py-0.5 bg-blue-100 text-blue-700 text-xs rounded" title="Uppercase required">A</span>' : ''}
                            ${policy.password_require_lowercase ? '<span class="px-1.5 py-0.5 bg-blue-100 text-blue-700 text-xs rounded" title="Lowercase required">a</span>' : ''}
                            ${policy.password_require_digit ? '<span class="px-1.5 py-0.5 bg-blue-100 text-blue-700 text-xs rounded" title="Digit required">0</span>' : ''}
                            ${policy.password_require_special_char ? '<span class="px-1.5 py-0.5 bg-blue-100 text-blue-700 text-xs rounded" title="Special char required">@</span>' : ''}
                          </div>
                        </div>
                        <div class="flex justify-between">
                          <span class="text-gray-600">Expiration:</span>
                          <span class="font-medium">${policy.password_expiration_days ? policy.password_expiration_days + ' days' : 'Never'}</span>
                        </div>
                        <div class="flex justify-between">
                          <span class="text-gray-600">History:</span>
                          <span class="font-medium">${policy.password_history_count || '0'} passwords</span>
                        </div>
                      </div>
                    </div>

                    <!-- Lockout Policy -->
                    <div class="space-y-3">
                      <h4 class="font-semibold text-gray-900 flex items-center gap-2 border-b pb-2">
                        <i class="ph-duotone ph-lock text-red-600"></i>
                        Account Lockout
                      </h4>
                      <div class="space-y-2 text-sm">
                        <div class="flex justify-between">
                          <span class="text-gray-600">Max Attempts:</span>
                          <span class="font-medium">${policy.login_max_attempts || '-'}</span>
                        </div>
                        <div class="flex justify-between">
                          <span class="text-gray-600">Lockout Type:</span>
                          <span class="font-medium capitalize">${policy.login_lockout_type || '-'}</span>
                        </div>
                        <div class="flex justify-between">
                          <span class="text-gray-600">Duration:</span>
                          <span class="font-medium">${policy.login_lockout_duration_min || '-'} min</span>
                        </div>
                        <div class="flex justify-between">
                          <span class="text-gray-600">Reset After:</span>
                          <span class="font-medium">${policy.login_reset_attempts_after_min || '-'} min</span>
                        </div>
                      </div>
                    </div>

                    <!-- Session Policy -->
                    <div class="space-y-3">
                      <h4 class="font-semibold text-gray-900 flex items-center gap-2 border-b pb-2">
                        <i class="ph-duotone ph-devices text-green-600"></i>
                        Session Policy
                      </h4>
                      <div class="space-y-2 text-sm">
                        <div class="flex justify-between">
                          <span class="text-gray-600">Idle Timeout:</span>
                          <span class="font-medium">${policy.session_timeout_minutes || '-'} min</span>
                        </div>
                        <div class="flex justify-between">
                          <span class="text-gray-600">Absolute Timeout:</span>
                          <span class="font-medium">${policy.session_absolute_timeout_hours || '-'} hours</span>
                        </div>
                        <div class="flex justify-between">
                          <span class="text-gray-600">Max Concurrent:</span>
                          <span class="font-medium">${policy.session_max_concurrent || '∞'}</span>
                        </div>
                        <div class="flex justify-between">
                          <span class="text-gray-600">Terminate on Pwd Change:</span>
                          <span class="font-medium">${policy.session_terminate_on_password_change ? 'Yes' : 'No'}</span>
                        </div>
                      </div>
                    </div>

                    <!-- Reset Policy -->
                    <div class="space-y-3">
                      <h4 class="font-semibold text-gray-900 flex items-center gap-2 border-b pb-2">
                        <i class="ph-duotone ph-key text-purple-600"></i>
                        Password Reset
                      </h4>
                      <div class="space-y-2 text-sm">
                        <div class="flex justify-between">
                          <span class="text-gray-600">Token Expiration:</span>
                          <span class="font-medium">${policy.password_reset_token_expire_hours || '-'} hours</span>
                        </div>
                        <div class="flex justify-between">
                          <span class="text-gray-600">Max Attempts:</span>
                          <span class="font-medium">${policy.password_reset_max_attempts || '-'}</span>
                        </div>
                        <div class="flex justify-between">
                          <span class="text-gray-600">User Notification:</span>
                          <span class="font-medium">${policy.password_reset_notify_user ? 'Enabled' : 'Disabled'}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            `).join('')}
          </div>
        `}
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

  showPolicyDialog(policyId = null) {
    const policy = policyId ? this.data.policies.find(p => p.id === policyId) : null;
    const isEdit = !!policy;
    const isSystemPolicy = policy && policy.tenant_id === null;

    // Create modal overlay
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4';
    modal.innerHTML = `
      <div class="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        <!-- Header -->
        <div class="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-4 flex justify-between items-center">
          <h2 class="text-xl font-bold text-white flex items-center gap-2">
            <i class="ph-duotone ph-shield-star"></i>
            ${isEdit ? 'Edit Security Policy' : 'Create New Security Policy'}
          </h2>
          <button onclick="this.closest('.fixed').remove()" class="text-white hover:text-gray-200 transition">
            <i class="ph ph-x text-2xl"></i>
          </button>
        </div>

        <!-- Form Content -->
        <div class="flex-1 overflow-y-auto p-6">
          <form id="policyForm" class="space-y-6">
            <!-- Basic Info -->
            <div class="bg-gray-50 rounded-lg p-4 border border-gray-200">
              <h3 class="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <i class="ph-duotone ph-info text-blue-600"></i>
                Policy Information
              </h3>
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Policy Name *</label>
                  <input type="text" name="policy_name" required
                         value="${policy?.policy_name || ''}"
                         class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                         placeholder="e.g., Default Security Policy">
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Policy Type</label>
                  <select name="policy_type" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                    <option value="combined" ${policy?.policy_type === 'combined' ? 'selected' : ''}>Combined</option>
                    <option value="password" ${policy?.policy_type === 'password' ? 'selected' : ''}>Password Only</option>
                    <option value="session" ${policy?.policy_type === 'session' ? 'selected' : ''}>Session Only</option>
                    <option value="lockout" ${policy?.policy_type === 'lockout' ? 'selected' : ''}>Lockout Only</option>
                  </select>
                </div>
                ${!isEdit || !isSystemPolicy ? `
                  <div class="col-span-2">
                    <label class="block text-sm font-medium text-gray-700 mb-1">
                      Tenant ${isSystemPolicy ? '(System Default)' : ''}
                    </label>
                    <select name="tenant_id" ${isSystemPolicy ? 'disabled' : ''}
                            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                      <option value="">System Default (All Tenants)</option>
                      <!-- Tenant options would be loaded dynamically -->
                    </select>
                    ${isSystemPolicy ? '<input type="hidden" name="tenant_id" value="">' : ''}
                  </div>
                ` : ''}
              </div>
            </div>

            <!-- Password Policy -->
            <div class="bg-blue-50 rounded-lg p-4 border border-blue-200">
              <h3 class="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <i class="ph-duotone ph-lock-key text-blue-600"></i>
                Password Policy
              </h3>
              <div class="grid grid-cols-3 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Min Length</label>
                  <input type="number" name="password_min_length" min="8" max="128"
                         value="${policy?.password_min_length || 12}"
                         class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Max Length</label>
                  <input type="number" name="password_max_length" min="8" max="256"
                         value="${policy?.password_max_length || 128}"
                         class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Min Unique Chars</label>
                  <input type="number" name="password_min_unique_chars" min="0"
                         value="${policy?.password_min_unique_chars || 8}"
                         class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Max Repeating Chars</label>
                  <input type="number" name="password_max_repeating_chars" min="0"
                         value="${policy?.password_max_repeating_chars || 2}"
                         class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Expiration Days</label>
                  <input type="number" name="password_expiration_days" min="0"
                         value="${policy?.password_expiration_days || 90}"
                         class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Warning Days</label>
                  <input type="number" name="password_expiration_warning_days" min="0"
                         value="${policy?.password_expiration_warning_days || 14}"
                         class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Grace Logins</label>
                  <input type="number" name="password_grace_logins" min="0"
                         value="${policy?.password_grace_logins || 3}"
                         class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Password History</label>
                  <input type="number" name="password_history_count" min="0"
                         value="${policy?.password_history_count || 5}"
                         class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                </div>
              </div>

              <div class="mt-4 grid grid-cols-2 gap-4">
                <label class="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" name="password_require_uppercase"
                         ${policy?.password_require_uppercase !== false ? 'checked' : ''}
                         class="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500">
                  <span class="text-sm text-gray-700">Require Uppercase</span>
                </label>
                <label class="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" name="password_require_lowercase"
                         ${policy?.password_require_lowercase !== false ? 'checked' : ''}
                         class="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500">
                  <span class="text-sm text-gray-700">Require Lowercase</span>
                </label>
                <label class="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" name="password_require_digit"
                         ${policy?.password_require_digit !== false ? 'checked' : ''}
                         class="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500">
                  <span class="text-sm text-gray-700">Require Digit</span>
                </label>
                <label class="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" name="password_require_special_char"
                         ${policy?.password_require_special_char !== false ? 'checked' : ''}
                         class="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500">
                  <span class="text-sm text-gray-700">Require Special Character</span>
                </label>
                <label class="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" name="password_allow_common"
                         ${policy?.password_allow_common === true ? 'checked' : ''}
                         class="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500">
                  <span class="text-sm text-gray-700">Allow Common Passwords</span>
                </label>
                <label class="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" name="password_allow_username"
                         ${policy?.password_allow_username === true ? 'checked' : ''}
                         class="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500">
                  <span class="text-sm text-gray-700">Allow Username in Password</span>
                </label>
              </div>
            </div>

            <!-- Account Lockout Policy -->
            <div class="bg-red-50 rounded-lg p-4 border border-red-200">
              <h3 class="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <i class="ph-duotone ph-lock text-red-600"></i>
                Account Lockout Policy
              </h3>
              <div class="grid grid-cols-3 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Max Login Attempts</label>
                  <input type="number" name="login_max_attempts" min="1"
                         value="${policy?.login_max_attempts || 5}"
                         class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Lockout Duration (min)</label>
                  <input type="number" name="login_lockout_duration_min" min="1"
                         value="${policy?.login_lockout_duration_min || 30}"
                         class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Reset Attempts After (min)</label>
                  <input type="number" name="login_reset_attempts_after_min" min="1"
                         value="${policy?.login_reset_attempts_after_min || 60}"
                         class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Lockout Type</label>
                  <select name="login_lockout_type" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                    <option value="fixed" ${policy?.login_lockout_type === 'fixed' ? 'selected' : ''}>Fixed Duration</option>
                    <option value="progressive" ${policy?.login_lockout_type === 'progressive' ? 'selected' : ''}>Progressive</option>
                  </select>
                </div>
              </div>

              <div class="mt-4">
                <label class="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" name="login_notify_user_on_lockout"
                         ${policy?.login_notify_user_on_lockout !== false ? 'checked' : ''}
                         class="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500">
                  <span class="text-sm text-gray-700">Notify User on Lockout</span>
                </label>
              </div>
            </div>

            <!-- Session Policy -->
            <div class="bg-green-50 rounded-lg p-4 border border-green-200">
              <h3 class="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <i class="ph-duotone ph-devices text-green-600"></i>
                Session Policy
              </h3>
              <div class="grid grid-cols-3 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Idle Timeout (min)</label>
                  <input type="number" name="session_timeout_minutes" min="1"
                         value="${policy?.session_timeout_minutes || 60}"
                         class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Absolute Timeout (hours)</label>
                  <input type="number" name="session_absolute_timeout_hours" min="1"
                         value="${policy?.session_absolute_timeout_hours || 12}"
                         class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Max Concurrent Sessions</label>
                  <input type="number" name="session_max_concurrent" min="1"
                         value="${policy?.session_max_concurrent || 3}"
                         class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                </div>
              </div>

              <div class="mt-4">
                <label class="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" name="session_terminate_on_password_change"
                         ${policy?.session_terminate_on_password_change !== false ? 'checked' : ''}
                         class="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500">
                  <span class="text-sm text-gray-700">Terminate Sessions on Password Change</span>
                </label>
              </div>
            </div>

            <!-- Password Reset Policy -->
            <div class="bg-purple-50 rounded-lg p-4 border border-purple-200">
              <h3 class="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <i class="ph-duotone ph-key text-purple-600"></i>
                Password Reset Policy
              </h3>
              <div class="grid grid-cols-3 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Token Expiration (hours)</label>
                  <input type="number" name="password_reset_token_expire_hours" min="1"
                         value="${policy?.password_reset_token_expire_hours || 24}"
                         class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Max Reset Attempts</label>
                  <input type="number" name="password_reset_max_attempts" min="1"
                         value="${policy?.password_reset_max_attempts || 5}"
                         class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                </div>
              </div>

              <div class="mt-4">
                <label class="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" name="password_reset_notify_user"
                         ${policy?.password_reset_notify_user !== false ? 'checked' : ''}
                         class="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500">
                  <span class="text-sm text-gray-700">Notify User on Password Reset</span>
                </label>
              </div>
            </div>
          </form>
        </div>

        <!-- Footer -->
        <div class="bg-gray-50 px-6 py-4 flex justify-end gap-3 border-t">
          <button onclick="this.closest('.fixed').remove()"
                  class="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition">
            Cancel
          </button>
          <button onclick="securityAdmin.savePolicy('${policyId || ''}', this)"
                  class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center gap-2">
            <i class="ph ph-floppy-disk"></i>
            ${isEdit ? 'Update Policy' : 'Create Policy'}
          </button>
        </div>
      </div>
    `;

    document.body.appendChild(modal);
  }

  editPolicy(policyId) {
    this.showPolicyDialog(policyId);
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

  async savePolicy(policyId, button) {
    const form = document.getElementById('policyForm');
    if (!form.checkValidity()) {
      form.reportValidity();
      return;
    }

    // Show loading state
    const originalText = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '<i class="ph ph-spinner animate-spin"></i> Saving...';

    try {
      // Collect form data
      const formData = new FormData(form);
      const policyData = {};

      // Text and number fields
      const textFields = [
        'policy_name', 'policy_type', 'tenant_id', 'login_lockout_type'
      ];
      const numberFields = [
        'password_min_length', 'password_max_length', 'password_min_unique_chars',
        'password_max_repeating_chars', 'password_expiration_days',
        'password_expiration_warning_days', 'password_grace_logins', 'password_history_count',
        'login_max_attempts', 'login_lockout_duration_min', 'login_reset_attempts_after_min',
        'session_timeout_minutes', 'session_absolute_timeout_hours', 'session_max_concurrent',
        'password_reset_token_expire_hours', 'password_reset_max_attempts'
      ];
      const boolFields = [
        'password_require_uppercase', 'password_require_lowercase', 'password_require_digit',
        'password_require_special_char', 'password_allow_common', 'password_allow_username',
        'login_notify_user_on_lockout', 'session_terminate_on_password_change',
        'password_reset_notify_user'
      ];

      // Process text fields
      textFields.forEach(field => {
        const value = formData.get(field);
        if (value !== null && value !== '') {
          policyData[field] = value === '' ? null : value;
        }
      });

      // Process number fields
      numberFields.forEach(field => {
        const value = formData.get(field);
        if (value !== null && value !== '') {
          policyData[field] = parseInt(value, 10);
        }
      });

      // Process boolean fields
      boolFields.forEach(field => {
        policyData[field] = formData.get(field) === 'on';
      });

      // Convert empty tenant_id to null for system default
      if (policyData.tenant_id === '') {
        policyData.tenant_id = null;
      }

      const tokens = JSON.parse(localStorage.getItem('tokens') || '{}');
      const isEdit = !!policyId;
      const url = isEdit
        ? `${this.apiBase}/admin/security/policies/${policyId}`
        : `${this.apiBase}/admin/security/policies`;

      const response = await fetch(url, {
        method: isEdit ? 'PUT' : 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${tokens.access}`
        },
        body: JSON.stringify(policyData)
      });

      if (response.ok) {
        // Close modal
        const modal = button.closest('.fixed');
        modal.remove();

        // Show success message
        this.showNotification(
          `Policy ${isEdit ? 'updated' : 'created'} successfully`,
          'success'
        );

        // Reload data and refresh display
        await this.loadAllData();
        this.render();
      } else {
        const error = await response.json();
        throw new Error(error.detail || `Failed to ${isEdit ? 'update' : 'create'} policy`);
      }
    } catch (error) {
      console.error('Error saving policy:', error);
      this.showNotification(error.message || 'Failed to save policy', 'error');

      // Restore button state
      button.disabled = false;
      button.innerHTML = originalText;
    }
  }

  showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 z-[60] px-6 py-4 rounded-lg shadow-lg transform transition-all duration-300 ease-in-out ${
      type === 'success' ? 'bg-green-600 text-white' :
      type === 'error' ? 'bg-red-600 text-white' :
      'bg-blue-600 text-white'
    }`;

    notification.innerHTML = `
      <div class="flex items-center gap-3">
        <i class="ph ${type === 'success' ? 'ph-check-circle' : type === 'error' ? 'ph-x-circle' : 'ph-info'} text-2xl"></i>
        <span class="font-medium">${message}</span>
      </div>
    `;

    document.body.appendChild(notification);

    // Animate in
    setTimeout(() => notification.classList.add('translate-y-0'), 10);

    // Remove after 3 seconds
    setTimeout(() => {
      notification.classList.add('opacity-0', 'translate-y-[-20px]');
      setTimeout(() => notification.remove(), 300);
    }, 3000);
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
