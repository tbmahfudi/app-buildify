/**
 * Password Policy Display Component
 *
 * Shows password requirements to users during registration/password change.
 * Dynamically fetches the current password policy from the backend.
 */

class PasswordPolicyDisplay {
  constructor() {
    // Use /api/v1 prefix to work with nginx proxy
    this.apiBase = '/api/v1';
    this.policy = null;
  }

  /**
   * Initialize and display password policy requirements
   * @param {string} containerId - ID of the container element
   */
  async init(containerId) {
    this.containerId = containerId;
    await this.loadPolicy();
    this.render();
  }

  /**
   * Load password policy from backend
   */
  async loadPolicy() {
    try {
      // In a real implementation, fetch policy for current user's tenant
      const response = await fetch(`${this.apiBase}/auth/password-policy`);
      if (response.ok) {
        this.policy = await response.json();
      }
    } catch (error) {
      console.error('Failed to load password policy:', error);
      // Use sensible defaults if fetch fails
      this.policy = {
        min_length: 12,
        require_uppercase: true,
        require_lowercase: true,
        require_digit: true,
        require_special_char: true,
        expiration_days: 90,
        history_count: 5
      };
    }
  }

  /**
   * Render password policy requirements
   */
  render() {
    const container = document.getElementById(this.containerId);
    if (!container || !this.policy) return;

    const requirements = this.buildRequirements();

    container.innerHTML = `
      <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div class="flex items-start gap-3">
          <i class="ph-duotone ph-info text-blue-600 text-2xl flex-shrink-0"></i>
          <div class="flex-1">
            <h3 class="font-semibold text-blue-900 mb-2">Password Requirements</h3>
            <ul class="space-y-1 text-sm text-blue-800">
              ${requirements.map(req => `
                <li class="flex items-center gap-2">
                  <i class="ph ph-check-circle text-blue-600"></i>
                  <span>${req}</span>
                </li>
              `).join('')}
            </ul>
          </div>
        </div>
      </div>
    `;
  }

  /**
   * Build list of requirement strings from policy
   */
  buildRequirements() {
    const requirements = [];

    if (this.policy.min_length) {
      requirements.push(`At least ${this.policy.min_length} characters long`);
    }

    if (this.policy.require_uppercase) {
      requirements.push('Contains at least one uppercase letter (A-Z)');
    }

    if (this.policy.require_lowercase) {
      requirements.push('Contains at least one lowercase letter (a-z)');
    }

    if (this.policy.require_digit) {
      requirements.push('Contains at least one number (0-9)');
    }

    if (this.policy.require_special_char) {
      requirements.push('Contains at least one special character (!@#$%^&*...)');
    }

    if (this.policy.history_count && this.policy.history_count > 0) {
      requirements.push(`Cannot reuse your last ${this.policy.history_count} passwords`);
    }

    if (this.policy.expiration_days && this.policy.expiration_days > 0) {
      requirements.push(`Must be changed every ${this.policy.expiration_days} days`);
    }

    return requirements;
  }

  /**
   * Validate password against policy (client-side)
   * @param {string} password - Password to validate
   * @returns {Object} - {valid: boolean, errors: string[]}
   */
  validatePassword(password) {
    const errors = [];

    if (this.policy.min_length && password.length < this.policy.min_length) {
      errors.push(`Password must be at least ${this.policy.min_length} characters`);
    }

    if (this.policy.require_uppercase && !/[A-Z]/.test(password)) {
      errors.push('Password must contain an uppercase letter');
    }

    if (this.policy.require_lowercase && !/[a-z]/.test(password)) {
      errors.push('Password must contain a lowercase letter');
    }

    if (this.policy.require_digit && !/\d/.test(password)) {
      errors.push('Password must contain a number');
    }

    if (this.policy.require_special_char && !/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) {
      errors.push('Password must contain a special character');
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }

  /**
   * Show real-time validation feedback
   * @param {string} inputId - ID of password input element
   * @param {string} feedbackId - ID of feedback container element
   */
  attachRealTimeValidation(inputId, feedbackId) {
    const input = document.getElementById(inputId);
    const feedback = document.getElementById(feedbackId);

    if (!input || !feedback) return;

    input.addEventListener('input', () => {
      const result = this.validatePassword(input.value);

      if (!input.value) {
        feedback.innerHTML = '';
        return;
      }

      if (result.valid) {
        feedback.innerHTML = `
          <div class="text-green-600 text-sm flex items-center gap-2">
            <i class="ph ph-check-circle"></i>
            <span>Password meets all requirements</span>
          </div>
        `;
      } else {
        feedback.innerHTML = `
          <div class="text-red-600 text-sm space-y-1">
            ${result.errors.map(error => `
              <div class="flex items-start gap-2">
                <i class="ph ph-x-circle mt-0.5"></i>
                <span>${error}</span>
              </div>
            `).join('')}
          </div>
        `;
      }
    });
  }
}

// Create global instance
window.passwordPolicyDisplay = new PasswordPolicyDisplay();
