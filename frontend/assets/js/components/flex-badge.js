/**
 * FlexBadge - Flexible Badge Component
 *
 * A reusable badge component with Tailwind styling supporting:
 * - Multiple variants (primary, secondary, success, danger, warning, info)
 * - Multiple sizes (xs, sm, md, lg)
 * - Icon support
 * - Dot indicator
 * - Dismissible option
 * - Rounded or pill shape
 *
 * @author Claude Code
 * @version 1.0.0
 */

import BaseComponent from '../core/base-component.js';

export default class FlexBadge extends BaseComponent {
    /**
     * Default configuration
     */
    static DEFAULTS = {
        text: '',
        variant: 'primary',           // primary | secondary | success | danger | warning | info
        size: 'md',                   // xs | sm | md | lg
        icon: null,                   // Icon HTML string
        dot: false,                   // Show dot indicator
        dismissible: false,           // Show close button
        rounded: 'md',                // sm | md | lg | full (pill)
        classes: [],                  // Additional CSS classes
        onDismiss: null               // Dismiss callback
    };

    /**
     * Size mappings to Tailwind classes
     */
    static SIZES = {
        xs: 'px-2 py-0.5 text-xs',
        sm: 'px-2.5 py-0.5 text-sm',
        md: 'px-3 py-1 text-sm',
        lg: 'px-3.5 py-1.5 text-base'
    };

    /**
     * Variant mappings to Tailwind classes
     */
    static VARIANTS = {
        primary: 'bg-blue-100 text-blue-800 border-blue-200',
        secondary: 'bg-gray-100 text-gray-800 border-gray-200',
        success: 'bg-green-100 text-green-800 border-green-200',
        danger: 'bg-red-100 text-red-800 border-red-200',
        warning: 'bg-amber-100 text-amber-800 border-amber-200',
        info: 'bg-cyan-100 text-cyan-800 border-cyan-200'
    };

    /**
     * Rounded mappings
     */
    static ROUNDED = {
        sm: 'rounded',
        md: 'rounded-md',
        lg: 'rounded-lg',
        full: 'rounded-full'
    };

    /**
     * Constructor
     */
    constructor(container, options = {}) {
        super(container, options);

        this.state = {
            dismissed: false
        };

        this.badgeElement = null;
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
     * Render the badge
     */
    render() {
        // Create badge element
        this.badgeElement = document.createElement('span');

        const classes = [
            'inline-flex items-center gap-1.5',
            'font-medium border',
            'transition-all duration-200',
            FlexBadge.SIZES[this.options.size],
            FlexBadge.VARIANTS[this.options.variant],
            FlexBadge.ROUNDED[this.options.rounded],
            ...this.options.classes
        ].filter(Boolean);

        this.badgeElement.className = classes.join(' ');

        // Build content
        let content = '';

        // Dot indicator
        if (this.options.dot) {
            const dotColor = this.getDotColor(this.options.variant);
            content += `<span class="w-1.5 h-1.5 rounded-full ${dotColor}"></span>`;
        }

        // Icon
        if (this.options.icon) {
            content += this.options.icon;
        }

        // Text
        if (this.options.text) {
            content += `<span>${this.escapeHtml(this.options.text)}</span>`;
        }

        // Dismiss button
        if (this.options.dismissible) {
            content += `
                <button type="button" class="-mr-1 hover:opacity-75 transition" data-dismiss="true">
                    <i class="ph ph-x text-xs"></i>
                </button>
            `;
        }

        this.badgeElement.innerHTML = content;

        // Replace container content
        this.container.innerHTML = '';
        this.container.appendChild(this.badgeElement);
    }

    /**
     * Get dot color based on variant
     */
    getDotColor(variant) {
        const colors = {
            primary: 'bg-blue-600',
            secondary: 'bg-gray-600',
            success: 'bg-green-600',
            danger: 'bg-red-600',
            warning: 'bg-amber-600',
            info: 'bg-cyan-600'
        };
        return colors[variant] || colors.primary;
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        if (this.options.dismissible) {
            const dismissBtn = this.badgeElement.querySelector('[data-dismiss="true"]');
            if (dismissBtn) {
                dismissBtn.addEventListener('click', () => this.dismiss());
            }
        }
    }

    /**
     * Dismiss the badge
     */
    dismiss() {
        if (this.state.dismissed) return;

        this.state.dismissed = true;

        // Fade out animation
        this.badgeElement.style.opacity = '0';
        this.badgeElement.style.transform = 'scale(0.8)';

        setTimeout(() => {
            this.badgeElement.remove();
            if (this.options.onDismiss) {
                this.options.onDismiss();
            }
            this.emit('dismiss');
            this.destroy();
        }, 200);
    }

    /**
     * Set text
     */
    setText(text) {
        this.options.text = text;
        this.render();
        this.attachEventListeners();
        this.emit('textChange', { text });
    }

    /**
     * Set variant
     */
    setVariant(variant) {
        this.options.variant = variant;
        this.render();
        this.attachEventListeners();
        this.emit('variantChange', { variant });
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
     * Destroy component
     */
    destroy() {
        if (this.badgeElement) {
            this.badgeElement.remove();
        }
        super.destroy();
    }
}
