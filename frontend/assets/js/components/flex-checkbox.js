/**
 * FlexCheckbox Component
 *
 * Checkbox input component with label, indeterminate state, and custom styling
 *
 * @author Claude Code
 * @version 1.0.0
 */

import BaseComponent from '../core/base-component.js';

export default class FlexCheckbox extends BaseComponent {
    /**
     * Default configuration
     */
    static DEFAULTS = {
        label: null,                     // Checkbox label
        description: null,               // Description text below label
        checked: false,                  // Initial checked state
        indeterminate: false,            // Indeterminate state
        disabled: false,                 // Disabled state
        required: false,                 // Required field
        name: null,                      // Input name attribute
        value: 'on',                     // Input value attribute
        size: 'md',                      // sm | md | lg
        color: 'indigo',                 // Tailwind color name
        labelPosition: 'right',          // left | right
        classes: [],                     // Additional CSS classes
        onChange: null,                  // Change event callback
        onCheck: null,                   // Check event callback
        onUncheck: null                  // Uncheck event callback
    };

    /**
     * Size mappings
     */
    static SIZES = {
        sm: {
            checkbox: 'w-4 h-4',
            label: 'text-sm',
            description: 'text-xs'
        },
        md: {
            checkbox: 'w-5 h-5',
            label: 'text-base',
            description: 'text-sm'
        },
        lg: {
            checkbox: 'w-6 h-6',
            label: 'text-lg',
            description: 'text-base'
        }
    };

    /**
     * Constructor
     */
    constructor(element, options = {}) {
        super(element, options);

        this.state = {
            checked: this.options.checked,
            indeterminate: this.options.indeterminate
        };

        this.checkboxElement = null;
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
        const inputWrapper = this.createInputWrapper();
        const checkbox = this.createCheckbox();
        const checkmark = this.createCheckmark();
        const labelWrapper = this.createLabelWrapper();

        // Build structure
        inputWrapper.appendChild(checkbox);
        inputWrapper.appendChild(checkmark);

        if (this.options.labelPosition === 'left') {
            if (labelWrapper) wrapper.appendChild(labelWrapper);
            wrapper.appendChild(inputWrapper);
        } else {
            wrapper.appendChild(inputWrapper);
            if (labelWrapper) wrapper.appendChild(labelWrapper);
        }

        // Clear and replace content
        this.element.innerHTML = '';
        this.element.appendChild(wrapper);

        this.checkboxElement = checkbox;

        // Set indeterminate if needed
        if (this.state.indeterminate) {
            this.checkboxElement.indeterminate = true;
        }

        this.emit('render');
    }

    /**
     * Create wrapper element
     */
    createWrapper() {
        const wrapper = document.createElement('label');
        wrapper.className = `flex-checkbox-wrapper flex items-start gap-2 cursor-pointer ${this.options.classes.join(' ')}`;

        if (this.options.disabled) {
            wrapper.classList.add('opacity-50', 'cursor-not-allowed');
        }

        return wrapper;
    }

    /**
     * Create input wrapper
     */
    createInputWrapper() {
        const wrapper = document.createElement('div');
        wrapper.className = 'flex-checkbox-input-wrapper relative flex items-center justify-center flex-shrink-0';

        return wrapper;
    }

    /**
     * Create checkbox input
     */
    createCheckbox() {
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'peer sr-only';  // Hide but keep accessible

        checkbox.checked = this.state.checked;
        checkbox.disabled = this.options.disabled;
        checkbox.required = this.options.required;

        if (this.options.name) checkbox.name = this.options.name;
        if (this.options.value) checkbox.value = this.options.value;

        // ARIA attributes
        if (this.state.indeterminate) {
            checkbox.setAttribute('aria-checked', 'mixed');
        }

        return checkbox;
    }

    /**
     * Create checkmark (visual checkbox)
     */
    createCheckmark() {
        const checkmark = document.createElement('div');
        const sizeClasses = FlexCheckbox.SIZES[this.options.size].checkbox;

        checkmark.className = `flex-checkbox-checkmark ${sizeClasses} border-2 rounded transition-all duration-200 flex items-center justify-center`;

        // Default state
        checkmark.classList.add('border-gray-300', 'bg-white');

        // Checked state (using peer)
        checkmark.classList.add(
            'peer-checked:bg-' + this.options.color + '-600',
            'peer-checked:border-' + this.options.color + '-600'
        );

        // Focus state
        checkmark.classList.add(
            'peer-focus:ring-2',
            'peer-focus:ring-' + this.options.color + '-200',
            'peer-focus:ring-offset-2'
        );

        // Disabled state
        if (this.options.disabled) {
            checkmark.classList.add('bg-gray-100');
        }

        // Icon
        const icon = document.createElement('i');

        if (this.state.indeterminate) {
            icon.className = 'ph-bold ph-minus text-white text-xs';
        } else {
            icon.className = 'ph-bold ph-check text-white text-xs opacity-0 peer-checked:opacity-100 transition-opacity';
        }

        checkmark.appendChild(icon);

        return checkmark;
    }

    /**
     * Create label wrapper
     */
    createLabelWrapper() {
        if (!this.options.label) return null;

        const wrapper = document.createElement('div');
        wrapper.className = 'flex-checkbox-label-wrapper flex flex-col';

        const label = document.createElement('span');
        const sizeClasses = FlexCheckbox.SIZES[this.options.size].label;
        label.className = `flex-checkbox-label font-medium text-gray-900 ${sizeClasses}`;
        label.textContent = this.options.label;

        if (this.options.required) {
            const asterisk = document.createElement('span');
            asterisk.className = 'text-red-500 ml-1';
            asterisk.textContent = '*';
            label.appendChild(asterisk);
        }

        wrapper.appendChild(label);

        if (this.options.description) {
            const description = document.createElement('span');
            const descSizeClasses = FlexCheckbox.SIZES[this.options.size].description;
            description.className = `flex-checkbox-description text-gray-500 ${descSizeClasses} mt-0.5`;
            description.textContent = this.options.description;
            wrapper.appendChild(description);
        }

        return wrapper;
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        if (!this.checkboxElement) return;

        this.checkboxElement.addEventListener('change', (e) => {
            this.state.checked = e.target.checked;
            this.state.indeterminate = false;

            // Update visual
            const icon = this.element.querySelector('.flex-checkbox-checkmark i');
            if (icon) {
                icon.className = 'ph-bold ph-check text-white text-xs opacity-0 peer-checked:opacity-100 transition-opacity';
            }

            this.emit('change', {
                checked: this.state.checked,
                value: this.options.value
            });

            if (this.options.onChange) {
                this.options.onChange(this.state.checked, e);
            }

            if (this.state.checked && this.options.onCheck) {
                this.options.onCheck(e);
            } else if (!this.state.checked && this.options.onUncheck) {
                this.options.onUncheck(e);
            }
        });
    }

    /**
     * Check checkbox
     */
    check() {
        this.state.checked = true;
        this.state.indeterminate = false;

        if (this.checkboxElement) {
            this.checkboxElement.checked = true;
            this.checkboxElement.indeterminate = false;
        }

        this.emit('check');

        if (this.options.onCheck) {
            this.options.onCheck();
        }
    }

    /**
     * Uncheck checkbox
     */
    uncheck() {
        this.state.checked = false;
        this.state.indeterminate = false;

        if (this.checkboxElement) {
            this.checkboxElement.checked = false;
            this.checkboxElement.indeterminate = false;
        }

        this.emit('uncheck');

        if (this.options.onUncheck) {
            this.options.onUncheck();
        }
    }

    /**
     * Toggle checkbox
     */
    toggle() {
        if (this.state.checked) {
            this.uncheck();
        } else {
            this.check();
        }
    }

    /**
     * Set indeterminate state
     */
    setIndeterminate(indeterminate) {
        this.state.indeterminate = indeterminate;

        if (this.checkboxElement) {
            this.checkboxElement.indeterminate = indeterminate;
        }

        this.render();
        this.emit('indeterminate', { indeterminate });
    }

    /**
     * Get checked state
     */
    isChecked() {
        return this.state.checked;
    }

    /**
     * Get indeterminate state
     */
    isIndeterminate() {
        return this.state.indeterminate;
    }

    /**
     * Set checked state
     */
    setChecked(checked) {
        if (checked) {
            this.check();
        } else {
            this.uncheck();
        }
    }

    /**
     * Set disabled state
     */
    setDisabled(disabled) {
        this.options.disabled = disabled;
        this.render();
    }

    /**
     * Get checkbox element
     */
    getCheckboxElement() {
        return this.checkboxElement;
    }

    /**
     * Destroy component
     */
    destroy() {
        if (this.checkboxElement) {
            this.checkboxElement.removeEventListener('change', this.handleChange);
        }

        super.destroy();
    }
}
