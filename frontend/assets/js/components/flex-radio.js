/**
 * FlexRadio Component
 *
 * Radio button group component for single selection
 *
 * @author Claude Code
 * @version 1.0.0
 */

import BaseComponent from '../core/base-component.js';

export default class FlexRadio extends BaseComponent {
    /**
     * Default configuration
     */
    static DEFAULTS = {
        name: null,                      // Required: Radio group name
        label: null,                     // Group label
        options: [],                     // Array of radio options
        value: null,                     // Initially selected value
        direction: 'vertical',           // vertical | horizontal
        disabled: false,                 // Disable all options
        required: false,                 // Required field
        size: 'md',                      // sm | md | lg
        color: 'indigo',                 // Tailwind color name
        classes: [],                     // Additional CSS classes
        onChange: null,                  // Change event callback
        onSelect: null                   // Select event callback
    };

    /**
     * Size mappings
     */
    static SIZES = {
        sm: {
            radio: 'w-4 h-4',
            label: 'text-sm',
            description: 'text-xs',
            gap: 'gap-2'
        },
        md: {
            radio: 'w-5 h-5',
            label: 'text-base',
            description: 'text-sm',
            gap: 'gap-3'
        },
        lg: {
            radio: 'w-6 h-6',
            label: 'text-lg',
            description: 'text-base',
            gap: 'gap-4'
        }
    };

    /**
     * Constructor
     */
    constructor(element, options = {}) {
        super(element, options);

        if (!this.options.name) {
            console.warn('FlexRadio: name option is required');
            this.options.name = 'radio-' + Date.now();
        }

        this.state = {
            value: this.options.value
        };

        this.radioElements = [];
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

        if (this.options.label) {
            const groupLabel = this.createGroupLabel();
            wrapper.appendChild(groupLabel);
        }

        const radioGroup = this.createRadioGroup();
        wrapper.appendChild(radioGroup);

        // Clear and replace content
        this.element.innerHTML = '';
        this.element.appendChild(wrapper);

        this.emit('render');
    }

    /**
     * Create wrapper element
     */
    createWrapper() {
        const wrapper = document.createElement('div');
        wrapper.className = `flex-radio-wrapper ${this.options.classes.join(' ')}`;

        if (this.options.label) {
            wrapper.classList.add('space-y-2');
        }

        return wrapper;
    }

    /**
     * Create group label
     */
    createGroupLabel() {
        const label = document.createElement('div');
        const sizeClasses = FlexRadio.SIZES[this.options.size].label;
        label.className = `flex-radio-group-label font-medium text-gray-900 ${sizeClasses}`;
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
     * Create radio group
     */
    createRadioGroup() {
        const group = document.createElement('div');
        const gapClass = FlexRadio.SIZES[this.options.size].gap;

        group.className = `flex-radio-group flex ${gapClass}`;
        group.setAttribute('role', 'radiogroup');

        if (this.options.direction === 'vertical') {
            group.classList.add('flex-col');
        } else {
            group.classList.add('flex-row', 'flex-wrap');
        }

        if (this.options.label) {
            group.setAttribute('aria-labelledby', 'radio-group-label');
        }

        this.radioElements = [];

        this.options.options.forEach((option, index) => {
            const radioItem = this.createRadioItem(option, index);
            group.appendChild(radioItem);
        });

        return group;
    }

    /**
     * Create radio item
     */
    createRadioItem(option, index) {
        const wrapper = document.createElement('label');
        wrapper.className = 'flex-radio-item flex items-start gap-2 cursor-pointer';

        const isDisabled = option.disabled || this.options.disabled;

        if (isDisabled) {
            wrapper.classList.add('opacity-50', 'cursor-not-allowed');
        }

        // Radio input wrapper
        const inputWrapper = document.createElement('div');
        inputWrapper.className = 'flex-radio-input-wrapper relative flex items-center justify-center flex-shrink-0 mt-0.5';

        // Hidden radio input
        const radio = document.createElement('input');
        radio.type = 'radio';
        radio.name = this.options.name;
        radio.value = option.value;
        radio.className = 'peer sr-only';
        radio.checked = this.state.value === option.value;
        radio.disabled = isDisabled;
        radio.required = this.options.required && index === 0;  // Only first needs required

        if (option.id) radio.id = option.id;

        this.radioElements.push(radio);

        // Visual radio button
        const radioMark = document.createElement('div');
        const sizeClasses = FlexRadio.SIZES[this.options.size].radio;

        radioMark.className = `flex-radio-mark ${sizeClasses} border-2 rounded-full transition-all duration-200 flex items-center justify-center`;

        // Default state
        radioMark.classList.add('border-gray-300', 'bg-white');

        // Checked state
        radioMark.classList.add(
            'peer-checked:border-' + this.options.color + '-600',
            'peer-checked:bg-white'
        );

        // Focus state
        radioMark.classList.add(
            'peer-focus:ring-2',
            'peer-focus:ring-' + this.options.color + '-200',
            'peer-focus:ring-offset-2'
        );

        // Disabled state
        if (isDisabled) {
            radioMark.classList.add('bg-gray-100');
        }

        // Inner dot
        const dot = document.createElement('div');
        dot.className = `w-2.5 h-2.5 rounded-full bg-${this.options.color}-600 opacity-0 peer-checked:opacity-100 transition-opacity`;

        radioMark.appendChild(dot);
        inputWrapper.appendChild(radio);
        inputWrapper.appendChild(radioMark);

        // Label wrapper
        const labelWrapper = document.createElement('div');
        labelWrapper.className = 'flex flex-col';

        const label = document.createElement('span');
        const labelSizeClasses = FlexRadio.SIZES[this.options.size].label;
        label.className = `flex-radio-label font-medium text-gray-900 ${labelSizeClasses}`;
        label.textContent = option.label;

        labelWrapper.appendChild(label);

        if (option.description) {
            const description = document.createElement('span');
            const descSizeClasses = FlexRadio.SIZES[this.options.size].description;
            description.className = `flex-radio-description text-gray-500 ${descSizeClasses} mt-0.5`;
            description.textContent = option.description;
            labelWrapper.appendChild(description);
        }

        wrapper.appendChild(inputWrapper);
        wrapper.appendChild(labelWrapper);

        return wrapper;
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        this.radioElements.forEach((radio) => {
            radio.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.state.value = e.target.value;

                    const option = this.options.options.find(opt => opt.value === e.target.value);

                    this.emit('change', {
                        value: this.state.value,
                        option: option
                    });

                    if (this.options.onChange) {
                        this.options.onChange(this.state.value, option, e);
                    }

                    if (this.options.onSelect) {
                        this.options.onSelect(this.state.value, option, e);
                    }
                }
            });
        });
    }

    /**
     * Get selected value
     */
    getValue() {
        return this.state.value;
    }

    /**
     * Set selected value
     */
    setValue(value) {
        this.state.value = value;

        this.radioElements.forEach(radio => {
            radio.checked = radio.value === value;
        });

        this.emit('change', { value });
    }

    /**
     * Get selected option
     */
    getSelectedOption() {
        return this.options.options.find(opt => opt.value === this.state.value);
    }

    /**
     * Add option
     */
    addOption(option) {
        this.options.options.push(option);
        this.render();
        this.attachEventListeners();
        this.emit('option:add', { option });
    }

    /**
     * Remove option by value
     */
    removeOption(value) {
        const index = this.options.options.findIndex(opt => opt.value === value);

        if (index !== -1) {
            const removed = this.options.options.splice(index, 1)[0];
            this.render();
            this.attachEventListeners();
            this.emit('option:remove', { option: removed });

            // Clear value if removed option was selected
            if (this.state.value === value) {
                this.state.value = null;
            }
        }
    }

    /**
     * Update option
     */
    updateOption(value, updates) {
        const option = this.options.options.find(opt => opt.value === value);

        if (option) {
            Object.assign(option, updates);
            this.render();
            this.attachEventListeners();
            this.emit('option:update', { value, updates });
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
     * Disable specific option
     */
    disableOption(value) {
        const option = this.options.options.find(opt => opt.value === value);

        if (option) {
            option.disabled = true;
            this.render();
            this.attachEventListeners();
        }
    }

    /**
     * Enable specific option
     */
    enableOption(value) {
        const option = this.options.options.find(opt => opt.value === value);

        if (option) {
            option.disabled = false;
            this.render();
            this.attachEventListeners();
        }
    }

    /**
     * Clear selection
     */
    clear() {
        this.state.value = null;

        this.radioElements.forEach(radio => {
            radio.checked = false;
        });

        this.emit('clear');
    }

    /**
     * Destroy component
     */
    destroy() {
        this.radioElements.forEach(radio => {
            radio.removeEventListener('change', this.handleChange);
        });

        super.destroy();
    }
}
