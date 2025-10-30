/**
 * FlexInput Component
 *
 * Universal input field component with validation, icons, and multiple states
 *
 * @author Claude Code
 * @version 1.0.0
 */

import BaseComponent from '../core/base-component.js';

export default class FlexInput extends BaseComponent {
    /**
     * Default configuration
     */
    static DEFAULTS = {
        type: 'text',                    // text | email | password | number | tel | url | search
        label: null,                     // Input label
        labelPosition: 'top',            // top | floating | inline
        placeholder: '',                 // Placeholder text
        value: '',                       // Initial value
        required: false,                 // Required field
        disabled: false,                 // Disabled state
        readonly: false,                 // Readonly state
        size: 'md',                      // sm | md | lg
        variant: 'outlined',             // outlined | filled | underlined
        helperText: null,                // Helper text below input
        errorMessage: null,              // Error message
        successMessage: null,            // Success message
        prefixIcon: null,                // Icon before input
        suffixIcon: null,                // Icon after input
        clearable: false,                // Show clear button
        showPasswordToggle: false,       // Show password visibility toggle
        maxLength: null,                 // Maximum character length
        showCharCount: false,            // Show character counter
        validator: null,                 // Custom validation function
        validateOn: 'blur',              // blur | change | submit
        autoComplete: 'off',             // Autocomplete attribute
        pattern: null,                   // HTML5 pattern validation
        min: null,                       // Min value (for number type)
        max: null,                       // Max value (for number type)
        step: null,                      // Step value (for number type)
        classes: [],                     // Additional CSS classes
        inputClasses: [],                // Additional input CSS classes
        onInput: null,                   // Input event callback
        onChange: null,                  // Change event callback
        onFocus: null,                   // Focus event callback
        onBlur: null,                    // Blur event callback
        onClear: null                    // Clear event callback
    };

    /**
     * Size mappings to Tailwind classes
     */
    static SIZES = {
        sm: {
            input: 'px-3 py-1.5 text-sm',
            label: 'text-sm',
            icon: 'text-sm'
        },
        md: {
            input: 'px-4 py-2 text-base',
            label: 'text-sm',
            icon: 'text-base'
        },
        lg: {
            input: 'px-4 py-3 text-lg',
            label: 'text-base',
            icon: 'text-lg'
        }
    };

    /**
     * Constructor
     */
    constructor(element, options = {}) {
        super(element, options);

        this.state = {
            value: this.options.value,
            focused: false,
            valid: true,
            touched: false,
            error: null,
            showPassword: false
        };

        this.inputElement = null;
        this.init();
    }

    /**
     * Initialize component
     */
    init() {
        this.render();
        this.attachEventListeners();
        this.emit('init');
    }

    /**
     * Render component
     */
    render() {
        const wrapper = this.createWrapper();
        const label = this.createLabel();
        const inputWrapper = this.createInputWrapper();
        const input = this.createInput();
        const prefixIcon = this.createPrefixIcon();
        const suffixIcons = this.createSuffixIcons();
        const message = this.createMessage();

        // Build structure
        if (label && this.options.labelPosition !== 'floating') {
            wrapper.appendChild(label);
        }

        if (prefixIcon) {
            inputWrapper.appendChild(prefixIcon);
        }

        inputWrapper.appendChild(input);

        if (suffixIcons) {
            inputWrapper.appendChild(suffixIcons);
        }

        wrapper.appendChild(inputWrapper);

        if (label && this.options.labelPosition === 'floating') {
            inputWrapper.appendChild(label);
        }

        if (message) {
            wrapper.appendChild(message);
        }

        // Clear and replace content
        this.element.innerHTML = '';
        this.element.appendChild(wrapper);

        this.inputElement = input;

        this.emit('render');
    }

    /**
     * Create wrapper element
     */
    createWrapper() {
        const wrapper = document.createElement('div');
        wrapper.className = `flex-input-wrapper ${this.options.classes.join(' ')}`;

        if (this.options.labelPosition === 'inline') {
            wrapper.classList.add('flex', 'items-center', 'gap-3');
        } else {
            wrapper.classList.add('space-y-1.5');
        }

        return wrapper;
    }

    /**
     * Create label element
     */
    createLabel() {
        if (!this.options.label) return null;

        const label = document.createElement('label');
        const sizeClasses = FlexInput.SIZES[this.options.size].label;

        label.className = `flex-input-label font-medium text-gray-700 ${sizeClasses}`;

        if (this.options.labelPosition === 'floating') {
            label.className = `flex-input-label absolute left-3 transition-all duration-200 pointer-events-none ${sizeClasses}`;

            if (this.state.focused || this.state.value) {
                label.classList.add('-top-2', 'text-xs', 'bg-white', 'px-1');
            } else {
                label.classList.add('top-2.5', 'text-gray-400');
            }
        }

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
     * Create input wrapper
     */
    createInputWrapper() {
        const wrapper = document.createElement('div');
        wrapper.className = 'flex-input-inner relative flex items-center';

        if (this.options.labelPosition === 'floating') {
            wrapper.classList.add('relative');
        }

        return wrapper;
    }

    /**
     * Create input element
     */
    createInput() {
        const input = document.createElement('input');
        const sizeClasses = FlexInput.SIZES[this.options.size].input;

        // Type
        input.type = this.state.showPassword ? 'text' : this.options.type;

        // Base classes
        let classes = [
            'flex-input',
            'w-full',
            'border',
            'rounded-lg',
            'transition-colors',
            'focus:outline-none',
            'focus:ring-2',
            sizeClasses,
            ...this.options.inputClasses
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
        } else if (this.options.variant === 'underlined') {
            classes.push(
                'border-0',
                'border-b-2',
                'border-gray-300',
                'bg-transparent',
                'rounded-none',
                'focus:border-indigo-500',
                'focus:ring-0',
                'px-0'
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

        if (this.options.prefixIcon) {
            classes.push('pl-10');
        }

        if (this.options.suffixIcon || this.options.clearable ||
            (this.options.type === 'password' && this.options.showPasswordToggle)) {
            classes.push('pr-10');
        }

        input.className = classes.join(' ');

        // Attributes
        input.value = this.state.value;
        input.placeholder = this.options.placeholder;
        input.required = this.options.required;
        input.disabled = this.options.disabled;
        input.readOnly = this.options.readonly;
        input.autocomplete = this.options.autoComplete;

        if (this.options.maxLength) input.maxLength = this.options.maxLength;
        if (this.options.pattern) input.pattern = this.options.pattern;
        if (this.options.min !== null) input.min = this.options.min;
        if (this.options.max !== null) input.max = this.options.max;
        if (this.options.step) input.step = this.options.step;

        // ARIA attributes
        if (!this.state.valid && this.state.touched) {
            input.setAttribute('aria-invalid', 'true');
            input.setAttribute('aria-describedby', 'input-error');
        }

        return input;
    }

    /**
     * Create prefix icon
     */
    createPrefixIcon() {
        if (!this.options.prefixIcon) return null;

        const wrapper = document.createElement('div');
        wrapper.className = 'absolute left-3 flex items-center pointer-events-none';

        const icon = document.createElement('i');
        icon.className = `${this.options.prefixIcon} text-gray-400 ${FlexInput.SIZES[this.options.size].icon}`;

        wrapper.appendChild(icon);
        return wrapper;
    }

    /**
     * Create suffix icons (clear, password toggle, custom icon, counter)
     */
    createSuffixIcons() {
        const hasIcons = this.options.suffixIcon ||
                        this.options.clearable ||
                        (this.options.type === 'password' && this.options.showPasswordToggle) ||
                        this.options.showCharCount;

        if (!hasIcons) return null;

        const wrapper = document.createElement('div');
        wrapper.className = 'absolute right-3 flex items-center gap-1';

        // Character counter
        if (this.options.showCharCount && this.options.maxLength) {
            const counter = document.createElement('span');
            counter.className = 'text-xs text-gray-400';
            counter.textContent = `${this.state.value.length}/${this.options.maxLength}`;
            counter.id = 'char-counter';
            wrapper.appendChild(counter);
        }

        // Clear button
        if (this.options.clearable && this.state.value && !this.options.disabled) {
            const clearBtn = document.createElement('button');
            clearBtn.type = 'button';
            clearBtn.className = `text-gray-400 hover:text-gray-600 transition-colors ${FlexInput.SIZES[this.options.size].icon}`;
            clearBtn.innerHTML = '<i class="ph ph-x-circle"></i>';
            clearBtn.setAttribute('aria-label', 'Clear input');
            clearBtn.onclick = (e) => {
                e.stopPropagation();
                this.clear();
            };
            wrapper.appendChild(clearBtn);
        }

        // Password toggle
        if (this.options.type === 'password' && this.options.showPasswordToggle) {
            const toggleBtn = document.createElement('button');
            toggleBtn.type = 'button';
            toggleBtn.className = `text-gray-400 hover:text-gray-600 transition-colors ${FlexInput.SIZES[this.options.size].icon}`;
            toggleBtn.innerHTML = this.state.showPassword ?
                '<i class="ph ph-eye-slash"></i>' :
                '<i class="ph ph-eye"></i>';
            toggleBtn.setAttribute('aria-label', this.state.showPassword ? 'Hide password' : 'Show password');
            toggleBtn.onclick = (e) => {
                e.stopPropagation();
                this.togglePasswordVisibility();
            };
            wrapper.appendChild(toggleBtn);
        }

        // Custom suffix icon
        if (this.options.suffixIcon) {
            const icon = document.createElement('i');
            icon.className = `${this.options.suffixIcon} text-gray-400 ${FlexInput.SIZES[this.options.size].icon}`;
            wrapper.appendChild(icon);
        }

        return wrapper;
    }

    /**
     * Create message (helper, error, success)
     */
    createMessage() {
        let message = null;
        let className = 'flex-input-message text-sm mt-1';

        if (!this.state.valid && this.state.touched && this.state.error) {
            message = this.state.error;
            className += ' text-red-600';
        } else if (this.options.successMessage && this.state.valid && this.state.touched) {
            message = this.options.successMessage;
            className += ' text-green-600';
        } else if (this.options.helperText) {
            message = this.options.helperText;
            className += ' text-gray-500';
        }

        if (!message) return null;

        const messageEl = document.createElement('div');
        messageEl.className = className;
        messageEl.id = 'input-error';
        messageEl.textContent = message;

        return messageEl;
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        if (!this.inputElement) return;

        // Input event
        this.inputElement.addEventListener('input', (e) => {
            this.state.value = e.target.value;

            // Update character counter
            if (this.options.showCharCount) {
                const counter = this.element.querySelector('#char-counter');
                if (counter) {
                    counter.textContent = `${this.state.value.length}/${this.options.maxLength}`;
                }
            }

            // Validate on change if configured
            if (this.options.validateOn === 'change') {
                this.validate();
            }

            // Update floating label
            if (this.options.labelPosition === 'floating') {
                this.updateFloatingLabel();
            }

            this.emit('input', { value: this.state.value });

            if (this.options.onInput) {
                this.options.onInput(this.state.value, e);
            }
        });

        // Change event
        this.inputElement.addEventListener('change', (e) => {
            this.emit('change', { value: this.state.value });

            if (this.options.onChange) {
                this.options.onChange(this.state.value, e);
            }
        });

        // Focus event
        this.inputElement.addEventListener('focus', (e) => {
            this.state.focused = true;

            if (this.options.labelPosition === 'floating') {
                this.updateFloatingLabel();
            }

            this.emit('focus', { value: this.state.value });

            if (this.options.onFocus) {
                this.options.onFocus(e);
            }
        });

        // Blur event
        this.inputElement.addEventListener('blur', (e) => {
            this.state.focused = false;
            this.state.touched = true;

            // Validate on blur if configured
            if (this.options.validateOn === 'blur') {
                this.validate();
            }

            if (this.options.labelPosition === 'floating') {
                this.updateFloatingLabel();
            }

            this.emit('blur', { value: this.state.value });

            if (this.options.onBlur) {
                this.options.onBlur(e);
            }
        });
    }

    /**
     * Update floating label position
     */
    updateFloatingLabel() {
        const label = this.element.querySelector('.flex-input-label');
        if (!label) return;

        if (this.state.focused || this.state.value) {
            label.classList.remove('top-2.5', 'text-gray-400');
            label.classList.add('-top-2', 'text-xs', 'bg-white', 'px-1');
        } else {
            label.classList.add('top-2.5', 'text-gray-400');
            label.classList.remove('-top-2', 'text-xs', 'bg-white', 'px-1');
        }
    }

    /**
     * Validate input
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

        // HTML5 validation
        if (isValid && this.inputElement && !this.inputElement.checkValidity()) {
            isValid = false;
            error = this.inputElement.validationMessage || 'Invalid value';
        }

        this.state.valid = isValid;
        this.state.error = error;

        if (this.state.touched) {
            this.render();
            this.attachEventListeners();
        }

        this.emit('validate', { valid: isValid, error });

        return isValid;
    }

    /**
     * Clear input value
     */
    clear() {
        this.state.value = '';
        if (this.inputElement) {
            this.inputElement.value = '';
            this.inputElement.focus();
        }

        this.render();
        this.attachEventListeners();
        this.emit('clear');

        if (this.options.onClear) {
            this.options.onClear();
        }
    }

    /**
     * Toggle password visibility
     */
    togglePasswordVisibility() {
        this.state.showPassword = !this.state.showPassword;
        this.render();
        this.attachEventListeners();
        this.inputElement.focus();
    }

    /**
     * Get input value
     */
    getValue() {
        return this.state.value;
    }

    /**
     * Set input value
     */
    setValue(value) {
        this.state.value = value;
        if (this.inputElement) {
            this.inputElement.value = value;
        }
        this.render();
        this.attachEventListeners();
        this.emit('change', { value });
    }

    /**
     * Focus input
     */
    focus() {
        if (this.inputElement) {
            this.inputElement.focus();
        }
    }

    /**
     * Blur input
     */
    blur() {
        if (this.inputElement) {
            this.inputElement.blur();
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
     * Get input element
     */
    getInputElement() {
        return this.inputElement;
    }

    /**
     * Destroy component
     */
    destroy() {
        if (this.inputElement) {
            this.inputElement.removeEventListener('input', this.handleInput);
            this.inputElement.removeEventListener('change', this.handleChange);
            this.inputElement.removeEventListener('focus', this.handleFocus);
            this.inputElement.removeEventListener('blur', this.handleBlur);
        }

        super.destroy();
    }
}
