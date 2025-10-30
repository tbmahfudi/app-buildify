/**
 * FlexTextarea Component
 *
 * Multi-line text input with auto-resize, character counter, and validation
 *
 * @author Claude Code
 * @version 1.0.0
 */

import BaseComponent from '../core/base-component.js';

export default class FlexTextarea extends BaseComponent {
    /**
     * Default configuration
     */
    static DEFAULTS = {
        label: null,
        labelPosition: 'top',
        placeholder: '',
        value: '',
        required: false,
        disabled: false,
        readonly: false,
        rows: 3,
        minRows: 2,
        maxRows: 10,
        autoResize: true,
        size: 'md',                 // sm | md | lg
        variant: 'outlined',        // outlined | filled
        helperText: null,
        errorMessage: null,
        successMessage: null,
        maxLength: null,
        showCharCount: false,
        resizable: true,            // CSS resize handle
        validator: null,
        validateOn: 'blur',         // blur | change | submit
        classes: [],
        textareaClasses: [],
        onInput: null,
        onChange: null,
        onFocus: null,
        onBlur: null
    };

    /**
     * Size mappings
     */
    static SIZES = {
        sm: 'px-3 py-1.5 text-sm',
        md: 'px-4 py-2 text-base',
        lg: 'px-4 py-3 text-lg'
    };

    constructor(element, options = {}) {
        super(element, options);

        this.state = {
            value: this.options.value,
            focused: false,
            valid: true,
            touched: false,
            error: null
        };

        this.textareaElement = null;
        this.init();
    }

    /**
     * Initialize component
     */
    init() {
        this.render();
        this.attachEventListeners();
        if (this.options.autoResize) {
            this.resize();
        }
        this.emit('init');
    }

    /**
     * Render component
     */
    render() {
        const wrapper = this.createWrapper();
        const label = this.createLabel();
        const textareaWrapper = this.createTextareaWrapper();
        const textarea = this.createTextarea();
        const message = this.createMessage();

        if (label) wrapper.appendChild(label);
        textareaWrapper.appendChild(textarea);
        wrapper.appendChild(textareaWrapper);
        if (message) wrapper.appendChild(message);

        this.element.innerHTML = '';
        this.element.appendChild(wrapper);

        this.textareaElement = textarea;
        this.emit('render');
    }

    /**
     * Create wrapper
     */
    createWrapper() {
        const wrapper = document.createElement('div');
        wrapper.className = `flex-textarea-wrapper space-y-1.5 ${this.options.classes.join(' ')}`;
        return wrapper;
    }

    /**
     * Create label
     */
    createLabel() {
        if (!this.options.label) return null;

        const label = document.createElement('label');
        label.className = 'flex-textarea-label font-medium text-gray-700 text-sm';
        label.textContent = this.options.label;

        if (this.options.required) {
            const asterisk = document.createElement('span');
            asterisk.className = 'text-red-500 ml-1';
            asterisk.textContent = '*';
            label.appendChild(asterisk);
        }

        return label;
    }

    /**
     * Create textarea wrapper
     */
    createTextareaWrapper() {
        const wrapper = document.createElement('div');
        wrapper.className = 'relative';
        return wrapper;
    }

    /**
     * Create textarea
     */
    createTextarea() {
        const textarea = document.createElement('textarea');
        const sizeClasses = FlexTextarea.SIZES[this.options.size];

        let classes = [
            'flex-textarea',
            'w-full',
            'border',
            'rounded-lg',
            'transition-colors',
            'focus:outline-none',
            'focus:ring-2',
            sizeClasses,
            ...this.options.textareaClasses
        ];

        // Variant styles
        if (this.options.variant === 'outlined') {
            classes.push(
                'border-gray-300',
                'bg-white',
                'focus:border-indigo-500',
                'focus:ring-indigo-200'
            );
        } else if (this.options.variant === 'filled') {
            classes.push(
                'border-transparent',
                'bg-gray-100',
                'focus:bg-white',
                'focus:border-indigo-500',
                'focus:ring-indigo-200'
            );
        }

        // State classes
        if (this.options.disabled) {
            classes.push('bg-gray-50', 'text-gray-500', 'cursor-not-allowed');
        }

        if (!this.state.valid && this.state.touched) {
            classes = classes.filter(c => !c.includes('indigo'));
            classes.push('border-red-500', 'focus:border-red-500', 'focus:ring-red-200');
        }

        // Resizable
        if (!this.options.resizable) {
            classes.push('resize-none');
        }

        textarea.className = classes.join(' ');

        // Attributes
        textarea.value = this.state.value;
        textarea.placeholder = this.options.placeholder;
        textarea.required = this.options.required;
        textarea.disabled = this.options.disabled;
        textarea.readOnly = this.options.readonly;
        textarea.rows = this.options.rows;

        if (this.options.maxLength) {
            textarea.maxLength = this.options.maxLength;
        }

        // ARIA
        if (!this.state.valid && this.state.touched) {
            textarea.setAttribute('aria-invalid', 'true');
            textarea.setAttribute('aria-describedby', 'textarea-error');
        }

        return textarea;
    }

    /**
     * Create message
     */
    createMessage() {
        const messageContainer = document.createElement('div');
        messageContainer.className = 'flex items-center justify-between gap-2';

        // Error/Success/Helper message
        let message = null;
        let messageClass = 'text-sm';

        if (!this.state.valid && this.state.touched && this.state.error) {
            message = this.state.error;
            messageClass += ' text-red-600';
        } else if (this.options.successMessage && this.state.valid && this.state.touched) {
            message = this.options.successMessage;
            messageClass += ' text-green-600';
        } else if (this.options.helperText) {
            message = this.options.helperText;
            messageClass += ' text-gray-500';
        }

        if (message) {
            const messageEl = document.createElement('div');
            messageEl.className = messageClass;
            messageEl.id = 'textarea-error';
            messageEl.textContent = message;
            messageContainer.appendChild(messageEl);
        }

        // Character counter
        if (this.options.showCharCount && this.options.maxLength) {
            const counter = document.createElement('div');
            counter.className = 'text-sm text-gray-500';
            counter.textContent = `${this.state.value.length}/${this.options.maxLength}`;
            messageContainer.appendChild(counter);
        }

        return messageContainer.children.length > 0 ? messageContainer : null;
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        if (!this.textareaElement) return;

        // Input event
        this.textareaElement.addEventListener('input', (e) => {
            this.state.value = e.target.value;

            if (this.options.autoResize) {
                this.resize();
            }

            if (this.options.validateOn === 'change') {
                this.validate();
            }

            this.emit('input', { value: this.state.value });

            if (this.options.onInput) {
                this.options.onInput(this.state.value, e);
            }
        });

        // Change event
        this.textareaElement.addEventListener('change', (e) => {
            this.emit('change', { value: this.state.value });

            if (this.options.onChange) {
                this.options.onChange(this.state.value, e);
            }
        });

        // Focus event
        this.textareaElement.addEventListener('focus', (e) => {
            this.state.focused = true;

            this.emit('focus', { value: this.state.value });

            if (this.options.onFocus) {
                this.options.onFocus(e);
            }
        });

        // Blur event
        this.textareaElement.addEventListener('blur', (e) => {
            this.state.focused = false;
            this.state.touched = true;

            if (this.options.validateOn === 'blur') {
                this.validate();
            }

            this.emit('blur', { value: this.state.value });

            if (this.options.onBlur) {
                this.options.onBlur(e);
            }
        });
    }

    /**
     * Auto-resize textarea
     */
    resize() {
        if (!this.textareaElement || !this.options.autoResize) return;

        // Reset height to get accurate scrollHeight
        this.textareaElement.style.height = 'auto';

        // Calculate new height
        const lineHeight = parseInt(getComputedStyle(this.textareaElement).lineHeight) || 24;
        const minHeight = lineHeight * this.options.minRows;
        const maxHeight = lineHeight * this.options.maxRows;

        let newHeight = Math.max(this.textareaElement.scrollHeight, minHeight);
        if (maxHeight) {
            newHeight = Math.min(newHeight, maxHeight);
        }

        this.textareaElement.style.height = newHeight + 'px';
    }

    /**
     * Validate textarea
     */
    validate() {
        let isValid = true;
        let error = null;

        // Required validation
        if (this.options.required && !this.state.value) {
            isValid = false;
            error = this.options.errorMessage || 'This field is required';
        }

        // Custom validator
        if (isValid && this.options.validator && this.state.value) {
            const result = this.options.validator(this.state.value);

            if (typeof result === 'boolean') {
                isValid = result;
                if (!isValid) {
                    error = this.options.errorMessage || 'Invalid value';
                }
            } else if (typeof result === 'string') {
                isValid = false;
                error = result;
            } else if (result && typeof result === 'object') {
                isValid = result.valid;
                error = result.message;
            }
        }

        this.state.valid = isValid;
        this.state.error = error;

        if (this.state.touched) {
            this.render();
            this.attachEventListeners();
            if (this.options.autoResize) {
                this.resize();
            }
        }

        this.emit('validate', { valid: isValid, error });

        return isValid;
    }

    /**
     * Get value
     */
    getValue() {
        return this.state.value;
    }

    /**
     * Set value
     */
    setValue(value) {
        this.state.value = value;
        if (this.textareaElement) {
            this.textareaElement.value = value;
        }
        if (this.options.autoResize) {
            this.resize();
        }
        this.render();
        this.attachEventListeners();
        this.emit('change', { value });
    }

    /**
     * Focus textarea
     */
    focus() {
        if (this.textareaElement) {
            this.textareaElement.focus();
        }
    }

    /**
     * Blur textarea
     */
    blur() {
        if (this.textareaElement) {
            this.textareaElement.blur();
        }
    }

    /**
     * Set disabled state
     */
    setDisabled(disabled) {
        this.options.disabled = disabled;
        this.render();
        this.attachEventListeners();
    }

    /**
     * Set error state
     */
    setError(error) {
        this.state.valid = false;
        this.state.error = error;
        this.state.touched = true;
        this.render();
        this.attachEventListeners();
    }

    /**
     * Clear error state
     */
    clearError() {
        this.state.valid = true;
        this.state.error = null;
        this.render();
        this.attachEventListeners();
    }

    /**
     * Get textarea element
     */
    getTextareaElement() {
        return this.textareaElement;
    }

    /**
     * Destroy component
     */
    destroy() {
        super.destroy();
    }
}
