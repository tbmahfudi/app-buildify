/**
 * FlexButton - Flexible Button Component
 *
 * A reusable button component with Tailwind styling supporting:
 * - Multiple variants (primary, secondary, success, danger, warning, ghost, outline)
 * - Multiple sizes (xs, sm, md, lg, xl)
 * - Icon support (prefix/suffix)
 * - Loading state with spinner
 * - Disabled state
 * - RBAC integration
 * - Full width option
 *
 * @author Claude Code
 * @version 1.0.0
 */

import BaseComponent from '../core/base-component.js';
import { hasPermission } from '../rbac.js';

export default class FlexButton extends BaseComponent {
    /**
     * Default configuration
     */
    static DEFAULTS = {
        text: 'Button',
        variant: 'primary',           // primary | secondary | success | danger | warning | ghost | outline
        size: 'md',                   // xs | sm | md | lg | xl
        icon: null,                   // Icon HTML string or element
        iconPosition: 'left',         // left | right
        disabled: false,
        loading: false,
        fullWidth: false,
        type: 'button',               // button | submit | reset
        permission: null,             // RBAC permission required
        classes: [],                  // Additional CSS classes
        onClick: null                 // Click event callback
    };

    /**
     * Size mappings to Tailwind classes
     */
    static SIZES = {
        xs: 'px-2.5 py-1.5 text-xs',
        sm: 'px-3 py-2 text-sm',
        md: 'px-4 py-2.5 text-base',
        lg: 'px-5 py-3 text-lg',
        xl: 'px-6 py-3.5 text-xl'
    };

    /**
     * Variant mappings to Tailwind classes
     */
    static VARIANTS = {
        primary: 'bg-blue-600 hover:bg-blue-700 text-white border-transparent shadow-sm hover:shadow-md focus:ring-blue-500',
        secondary: 'bg-gray-600 hover:bg-gray-700 text-white border-transparent shadow-sm hover:shadow-md focus:ring-gray-500',
        success: 'bg-green-600 hover:bg-green-700 text-white border-transparent shadow-sm hover:shadow-md focus:ring-green-500',
        danger: 'bg-red-600 hover:bg-red-700 text-white border-transparent shadow-sm hover:shadow-md focus:ring-red-500',
        warning: 'bg-amber-600 hover:bg-amber-700 text-white border-transparent shadow-sm hover:shadow-md focus:ring-amber-500',
        ghost: 'bg-transparent hover:bg-gray-100 text-gray-700 border-transparent focus:ring-gray-400',
        outline: 'bg-transparent hover:bg-gray-50 text-gray-700 border-gray-300 focus:ring-gray-400'
    };

    /**
     * Constructor
     */
    constructor(container, options = {}) {
        super(container, options);

        this.state = {
            loading: this.options.loading,
            disabled: this.options.disabled,
            hasPermission: true
        };

        this.buttonElement = null;
        this.init();
    }

    /**
     * Initialize component
     */
    async init() {
        // Check permission if required
        if (this.options.permission) {
            this.state.hasPermission = await hasPermission(this.options.permission);
            if (!this.state.hasPermission) {
                this.container.style.display = 'none';
                return;
            }
        }

        this.render();
        this.attachEventListeners();
        this.emit('init');
    }

    /**
     * Render the button
     */
    render() {
        // Create button element
        this.buttonElement = document.createElement('button');
        this.buttonElement.type = this.options.type;

        // Build class list
        const classes = [
            'inline-flex items-center justify-center gap-2',
            'font-medium rounded-lg border',
            'transition-all duration-200',
            'focus:outline-none focus:ring-2 focus:ring-offset-2',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            FlexButton.SIZES[this.options.size],
            FlexButton.VARIANTS[this.options.variant],
            this.options.fullWidth ? 'w-full' : '',
            ...this.options.classes
        ].filter(Boolean);

        this.buttonElement.className = classes.join(' ');

        // Set disabled state
        this.buttonElement.disabled = this.state.disabled || this.state.loading;

        // Build content
        this.updateContent();

        // Replace container content
        this.container.innerHTML = '';
        this.container.appendChild(this.buttonElement);
    }

    /**
     * Update button content
     */
    updateContent() {
        if (this.state.loading) {
            this.buttonElement.innerHTML = this.getSpinnerHTML();
        } else {
            let content = '';

            // Icon on left
            if (this.options.icon && this.options.iconPosition === 'left') {
                content += this.getIconHTML(this.options.icon);
            }

            // Text
            content += `<span>${this.escapeHtml(this.options.text)}</span>`;

            // Icon on right
            if (this.options.icon && this.options.iconPosition === 'right') {
                content += this.getIconHTML(this.options.icon);
            }

            this.buttonElement.innerHTML = content;
        }
    }

    /**
     * Get spinner HTML
     */
    getSpinnerHTML() {
        return `
            <svg class="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
        `;
    }

    /**
     * Get icon HTML
     */
    getIconHTML(icon) {
        if (typeof icon === 'string') {
            return icon;
        } else if (icon instanceof HTMLElement) {
            return icon.outerHTML;
        }
        return '';
    }

    /**
     * Escape HTML
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        if (this.options.onClick) {
            this.buttonElement.addEventListener('click', (e) => {
                if (!this.state.disabled && !this.state.loading) {
                    this.options.onClick(e);
                    this.emit('click', { event: e });
                }
            });
        }
    }

    /**
     * Set loading state
     */
    setLoading(loading) {
        this.state.loading = loading;
        this.buttonElement.disabled = this.state.disabled || loading;
        this.updateContent();
        this.emit('loadingChange', { loading });
    }

    /**
     * Set disabled state
     */
    setDisabled(disabled) {
        this.state.disabled = disabled;
        this.buttonElement.disabled = disabled || this.state.loading;
        this.emit('disabledChange', { disabled });
    }

    /**
     * Set button text
     */
    setText(text) {
        this.options.text = text;
        this.updateContent();
        this.emit('textChange', { text });
    }

    /**
     * Set button variant
     */
    setVariant(variant) {
        // Remove old variant class
        Object.values(FlexButton.VARIANTS).forEach(variantClass => {
            this.buttonElement.classList.remove(...variantClass.split(' '));
        });

        // Add new variant class
        this.options.variant = variant;
        this.buttonElement.classList.add(...FlexButton.VARIANTS[variant].split(' '));
        this.emit('variantChange', { variant });
    }

    /**
     * Simulate click
     */
    click() {
        this.buttonElement.click();
    }

    /**
     * Get button element
     */
    getElement() {
        return this.buttonElement;
    }

    /**
     * Destroy component
     */
    destroy() {
        if (this.buttonElement) {
            this.buttonElement.remove();
        }
        super.destroy();
    }
}
