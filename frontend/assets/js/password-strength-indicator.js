/**
 * PasswordStrengthIndicator
 *
 * Fetches the tenant password policy from GET /api/v1/auth/password-policy,
 * renders a live requirement checklist below a target password <input>, and
 * toggles a submit button disabled state until all rules pass.
 *
 * Usage:
 *   import PasswordStrengthIndicator from './password-strength-indicator.js';
 *   const psi = new PasswordStrengthIndicator(inputEl, submitBtn, apiBase);
 *   // Detach if needed:
 *   psi.destroy();
 *
 * Story 24.2.1
 */

const API_PATH = '/api/v1/auth/password-policy';

const RULE_PATTERNS = [
  { key: 'uppercase',    pattern: /uppercase/i,      test: v => /[A-Z]/.test(v),          label: 'One uppercase letter (A–Z)' },
  { key: 'lowercase',    pattern: /lowercase/i,      test: v => /[a-z]/.test(v),          label: 'One lowercase letter (a–z)' },
  { key: 'digit',        pattern: /digit|number/i,   test: v => /[0-9]/.test(v),          label: 'One number (0–9)' },
  { key: 'special',      pattern: /special/i,        test: v => /[^A-Za-z0-9]/.test(v),  label: 'One special character (!@#…)' },
  { key: 'common',       pattern: /common/i,         test: () => true,                    label: 'Not a commonly used password' },
];

function buildLengthRule(minLen) {
  return {
    key: 'length',
    test: v => v.length >= minLen,
    label: `At least ${minLen} characters`,
  };
}

export default class PasswordStrengthIndicator {
  constructor(inputEl, submitBtn, apiBase = '') {
    this._input     = inputEl;
    this._submit    = submitBtn;
    this._apiBase   = apiBase.replace(/\/$/, '');
    this._rules     = [];
    this._container = null;
    this._handler   = () => this._evaluate();

    this._render();
    this._fetchPolicy();
    this._input.addEventListener('input', this._handler);
  }

  // ── Private ───────────────────────────────────────────────────────────────

  _render() {
    this._container = document.createElement('div');
    this._container.className = 'psi-container mt-2 space-y-1';
    this._container.innerHTML = `
      <p class="psi-loading text-xs text-gray-400 flex items-center gap-1">
        <i class="ph ph-spinner animate-spin"></i> Loading password rules…
      </p>`;
    this._input.insertAdjacentElement('afterend', this._container);
    if (this._submit) this._submit.disabled = true;
  }

  async _fetchPolicy() {
    try {
      const res = await fetch(`${this._apiBase}${API_PATH}`);
      if (!res.ok) throw new Error('policy fetch failed');
      const data = await res.json();
      this._buildRules(data);
    } catch {
      // Fail-open: remove loading indicator, enable submit
      this._container.innerHTML = '';
      if (this._submit) this._submit.disabled = false;
    }
  }

  _buildRules(policy) {
    this._rules = [];

    // Length rule — always present
    const minLen = policy.min_length ?? policy.password_min_length ?? 8;
    this._rules.push(buildLengthRule(minLen));

    // Text-based rules derived from policy.requirements array
    const reqs = Array.isArray(policy.requirements) ? policy.requirements : [];
    for (const rule of RULE_PATTERNS) {
      if (rule.key === 'length') continue; // already added
      if (reqs.some(r => rule.pattern.test(r))) {
        this._rules.push(rule);
      }
    }

    this._renderRules();
    this._evaluate();
  }

  _renderRules() {
    const items = this._rules.map(r => `
      <li class="psi-rule flex items-center gap-2 text-xs" data-key="${r.key}">
        <i class="ph ph-circle text-gray-300 flex-shrink-0"></i>
        <span>${r.label}</span>
      </li>`).join('');

    this._container.innerHTML = `
      <ul class="space-y-1">${items}</ul>
      <div class="psi-bar mt-2 h-1 rounded-full bg-gray-200 overflow-hidden">
        <div class="psi-bar-fill h-full rounded-full transition-all duration-300 bg-red-400" style="width:0%"></div>
      </div>`;
  }

  _evaluate() {
    if (!this._rules.length) return;
    const val = this._input.value;
    let passed = 0;

    for (const rule of this._rules) {
      const ok = rule.test(val);
      if (ok) passed++;
      const li = this._container.querySelector(`[data-key="${rule.key}"]`);
      if (!li) continue;
      const icon = li.querySelector('i');
      if (val.length === 0) {
        icon.className = 'ph ph-circle text-gray-300 flex-shrink-0';
      } else if (ok) {
        icon.className = 'ph ph-check-circle text-green-500 flex-shrink-0';
      } else {
        icon.className = 'ph ph-x-circle text-red-400 flex-shrink-0';
      }
    }

    const pct = this._rules.length ? Math.round((passed / this._rules.length) * 100) : 0;
    const fill = this._container.querySelector('.psi-bar-fill');
    if (fill) {
      fill.style.width = `${pct}%`;
      fill.className = fill.className.replace(/bg-\w+-\d+/, pct < 40 ? 'bg-red-400' : pct < 80 ? 'bg-amber-400' : 'bg-green-500');
    }

    if (this._submit) this._submit.disabled = passed < this._rules.length || val.length === 0;
  }

  // ── Public ────────────────────────────────────────────────────────────────

  destroy() {
    this._input.removeEventListener('input', this._handler);
    this._container?.remove();
  }
}
