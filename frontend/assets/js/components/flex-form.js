/**
 * FlexForm Component
 *
 * Form container with validation orchestration, field registration,
 * submission handling, and error display.
 *
 * @version 1.0.0
 */

import BaseComponent from '../core/base-component.js';

export default class FlexForm extends BaseComponent {
    static DEFAULTS = {
        action: null,           // URL — if set, submits via fetch
        method: 'POST',
        headers: {},
        layout: 'vertical',     // vertical | horizontal | grid
        columns: 2,             // for grid layout
        gap: 'md',              // sm | md | lg
        validateOn: 'submit',   // submit | blur | change
        showErrorSummary: true,
        submitLabel: 'Submit',
        resetLabel: null,       // if set, show reset button
        loadingLabel: 'Saving…',
        disabled: false,
        classes: [],
        onSubmit: null,         // (data, event) => void | Promise
        onSuccess: null,        // (response) => void
        onError: null,          // (errors) => void
        onReset: null,
    };

    static GAP = { sm: 'gap-3', md: 'gap-4', lg: 'gap-6' };

    constructor(element, options = {}) {
        super(element, options);
        this.state = {
            ...this.state,
            fields: new Map(),   // name -> { component, rules, element }
            loading: false,
            errors: {},
            submitted: false,
        };
        this.init();
    }

    init() {
        this.render();
        this._bindEvents();
        this.state.initialized = true;
    }

    // ── Rendering ──────────────────────────────────────────────────────────

    render() {
        const { layout, columns, gap, submitLabel, resetLabel, loadingLabel,
                disabled, classes, showErrorSummary } = this.options;

        const layoutClass = layout === 'grid'
            ? `grid grid-cols-1 md:grid-cols-${columns} ${FlexForm.GAP[gap] || FlexForm.GAP.md}`
            : layout === 'horizontal'
                ? `space-y-4`
                : `flex flex-col ${FlexForm.GAP[gap] || FlexForm.GAP.md}`;

        this.container.innerHTML = `
            <form class="flex-form ${layoutClass} ${classes.join(' ')}"
                  novalidate
                  data-flex-form>
                ${showErrorSummary ? `
                    <div class="flex-form-errors hidden col-span-full p-4 bg-red-50 border border-red-200 rounded-lg">
                        <p class="text-sm font-medium text-red-800 mb-1 flex items-center gap-2">
                            <i class="ph ph-warning-circle"></i> Please fix the following errors:
                        </p>
                        <ul class="flex-form-error-list text-sm text-red-700 list-disc list-inside space-y-0.5"></ul>
                    </div>` : ''}

                <div class="flex-form-fields ${layoutClass}">
                    <!-- fields rendered by register() calls -->
                </div>

                <div class="flex-form-actions col-span-full flex items-center gap-3 pt-2">
                    <button type="submit"
                        class="flex-form-submit px-6 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg
                               hover:bg-blue-700 active:scale-95 transition disabled:opacity-50 disabled:cursor-not-allowed
                               flex items-center gap-2"
                        ${disabled || this.state.loading ? 'disabled' : ''}>
                        ${this.state.loading ? `<i class="ph ph-spinner-gap animate-spin"></i> ${loadingLabel}` : submitLabel}
                    </button>
                    ${resetLabel ? `
                        <button type="reset"
                            class="flex-form-reset px-6 py-2.5 border border-gray-300 text-gray-700 text-sm font-medium rounded-lg
                                   hover:bg-gray-50 transition">
                            ${resetLabel}
                        </button>` : ''}
                    <div class="flex-form-status text-sm"></div>
                </div>
            </form>`;

        this.elements.form    = this.container.querySelector('form');
        this.elements.fields  = this.container.querySelector('.flex-form-fields');
        this.elements.submit  = this.container.querySelector('.flex-form-submit');
        this.elements.status  = this.container.querySelector('.flex-form-status');
        this.elements.errBox  = this.container.querySelector('.flex-form-errors');
        this.elements.errList = this.container.querySelector('.flex-form-error-list');
    }

    // ── Field registration ─────────────────────────────────────────────────

    /**
     * Register a field with the form.
     * @param {string} name - Field name (key in submitted data)
     * @param {HTMLElement|Object} elementOrComponent - DOM element or Flex component with getValue()
     * @param {Object} rules - Validation rules: { required, minLength, maxLength, pattern, min, max, custom }
     * @param {HTMLElement} [container] - Optional wrapper element to append to form fields area
     */
    register(name, elementOrComponent, rules = {}, container = null) {
        this.state.fields.set(name, {
            component: elementOrComponent,
            rules,
            element: container,
        });

        if (container && this.elements.fields) {
            this.elements.fields.appendChild(container);
        }

        // Wire change/blur validation if validateOn !== 'submit'
        if (this.options.validateOn !== 'submit') {
            const el = elementOrComponent?.container || elementOrComponent;
            const eventType = this.options.validateOn === 'blur' ? 'blur' : 'input';
            el?.addEventListener?.(eventType, () => this._validateField(name));
        }
    }

    /**
     * Unregister a field.
     */
    unregister(name) {
        const entry = this.state.fields.get(name);
        if (entry?.element) entry.element.remove();
        this.state.fields.delete(name);
    }

    // ── Validation ─────────────────────────────────────────────────────────

    validate() {
        this.state.errors = {};
        for (const [name, entry] of this.state.fields) {
            const err = this._validateField(name, true);
            if (err) this.state.errors[name] = err;
        }
        this._renderErrors();
        return Object.keys(this.state.errors).length === 0;
    }

    _validateField(name, renderInline = true) {
        const entry = this.state.fields.get(name);
        if (!entry) return null;

        const value = this._getValue(entry.component);
        const rules = entry.rules;
        let error = null;

        if (rules.required && this._isEmpty(value)) {
            error = rules.requiredMessage || `${this._humanize(name)} is required`;
        } else if (!this._isEmpty(value)) {
            if (rules.minLength && String(value).length < rules.minLength)
                error = `Minimum ${rules.minLength} characters`;
            else if (rules.maxLength && String(value).length > rules.maxLength)
                error = `Maximum ${rules.maxLength} characters`;
            else if (rules.min !== undefined && Number(value) < rules.min)
                error = `Minimum value is ${rules.min}`;
            else if (rules.max !== undefined && Number(value) > rules.max)
                error = `Maximum value is ${rules.max}`;
            else if (rules.pattern && !new RegExp(rules.pattern).test(String(value)))
                error = rules.patternMessage || `Invalid format`;
            else if (rules.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(value)))
                error = `Invalid email address`;
            else if (rules.custom) {
                const result = rules.custom(value, this.getData());
                if (result !== true && result) error = result;
            }
        }

        if (renderInline) {
            // Try to call setError on Flex components
            const comp = entry.component;
            if (comp && typeof comp.setError === 'function') {
                if (error) comp.setError(error);
                else if (typeof comp.clearError === 'function') comp.clearError();
            }
        }

        return error;
    }

    _renderErrors() {
        if (!this.options.showErrorSummary || !this.elements.errBox) return;
        const errs = Object.entries(this.state.errors);
        if (errs.length === 0) {
            this.elements.errBox.classList.add('hidden');
            return;
        }
        this.elements.errBox.classList.remove('hidden');
        if (this.elements.errList) {
            this.elements.errList.innerHTML = errs
                .map(([, msg]) => `<li>${msg}</li>`)
                .join('');
        }
    }

    // ── Data extraction ────────────────────────────────────────────────────

    getData() {
        const data = {};
        for (const [name, entry] of this.state.fields) {
            data[name] = this._getValue(entry.component);
        }
        return data;
    }

    _getValue(comp) {
        if (!comp) return null;
        if (typeof comp.getValue === 'function') return comp.getValue();
        if (comp instanceof HTMLInputElement || comp instanceof HTMLTextAreaElement || comp instanceof HTMLSelectElement)
            return comp.type === 'checkbox' ? comp.checked : comp.value;
        if (comp instanceof HTMLElement) {
            const input = comp.querySelector('input,textarea,select');
            if (input) return input.type === 'checkbox' ? input.checked : input.value;
        }
        return null;
    }

    reset() {
        for (const [, entry] of this.state.fields) {
            const comp = entry.component;
            if (typeof comp.setValue === 'function') comp.setValue(null);
            else if (typeof comp.clearError === 'function') comp.clearError();
            const el = comp instanceof HTMLElement ? comp
                     : comp?.container instanceof HTMLElement ? comp.container : null;
            el?.querySelectorAll('input,textarea,select').forEach(i => {
                if (i.type === 'checkbox') i.checked = false;
                else i.value = '';
            });
        }
        this.state.errors  = {};
        this.state.submitted = false;
        if (this.elements.errBox) this.elements.errBox.classList.add('hidden');
        if (this.elements.status) this.elements.status.textContent = '';
        this.emit('reset');
        
    }

    // ── Events ─────────────────────────────────────────────────────────────

    _bindEvents() {
        const form = this.container.querySelector('form');
        form?.addEventListener('submit', (e) => { e.preventDefault(); this._handleSubmit(e); });
        form?.addEventListener('reset',  (e) => { e.preventDefault(); this.reset(); });
    }

    async _handleSubmit(event) {
        this.state.submitted = true;
        if (!this.validate()) {
            this.emit('form:invalid', { errors: this.state.errors });
            return;
        }

        const data = this.getData();
        this.emit('form:submit', { data, event });

        if (this.options.onSubmit) {
            this._setLoading(true);
            try {
                const result = await this.options.onSubmit(data, event);
                this._setLoading(false);
                this._setStatus('success', null);
                this.emit('success', { data, result });
            } catch (err) {
                this._setLoading(false);
                const msg = err?.message || 'Submission failed';
                this._setStatus('error', msg);
                this.emit('error', { error: err });
            }
            return;
        }

        if (this.options.action) {
            this._setLoading(true);
            try {
                const resp = await fetch(this.options.action, {
                    method: this.options.method,
                    headers: { 'Content-Type': 'application/json', ...this.options.headers },
                    body: JSON.stringify(data),
                });
                const body = await resp.json().catch(() => ({}));
                this._setLoading(false);
                if (!resp.ok) throw Object.assign(new Error(body.message || 'Request failed'), { body });
                this._setStatus('success', null);
                this.emit('success', { data, result: body });
            } catch (err) {
                this._setLoading(false);
                this._setStatus('error', err.message);
                this.emit('error', { error: err });
            }
        }
    }

    _setLoading(val) {
        this.state.loading = val;
        const btn = this.elements.submit;
        if (!btn) return;
        btn.disabled = val || this.options.disabled;
        btn.innerHTML = val
            ? `<i class="ph ph-spinner-gap animate-spin"></i> ${this.options.loadingLabel}`
            : this.options.submitLabel;
    }

    _setStatus(type, message) {
        const el = this.elements.status;
        if (!el) return;
        if (!message) { el.textContent = ''; return; }
        el.className = `flex-form-status text-sm ${type === 'error' ? 'text-red-600' : 'text-green-600'}`;
        el.textContent = message;
    }

    // ── Public API ─────────────────────────────────────────────────────────

    setError(name, message) {
        this.state.errors[name] = message;
        const entry = this.state.fields.get(name);
        if (entry?.component && typeof entry.component.setError === 'function')
            entry.component.setError(message);
        this._renderErrors();
    }

    setFieldErrors(errors) {
        Object.entries(errors).forEach(([name, msg]) => this.setError(name, msg));
    }

    disable() { this.options.disabled = true; this._setLoading(false); }
    enable()  { this.options.disabled = false; if (this.elements.submit) this.elements.submit.disabled = false; }

    // ── Utilities ──────────────────────────────────────────────────────────

    _isEmpty(val) {
        return val === null || val === undefined || val === '' ||
               (Array.isArray(val) && val.length === 0);
    }

    _humanize(name) {
        return name.replace(/[_-]/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
    }
}
