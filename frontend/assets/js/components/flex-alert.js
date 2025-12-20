/**
 * FlexAlert - Flexible Alert Component
 *
 * A reusable alert/notification component with Tailwind styling supporting:
 * - Multiple variants (success, error, warning, info)
 * - Dismissible option
 * - Icon support
 * - Title and description
 * - Auto-dismiss with timeout
 * - Actions/buttons
 *
 * @author Claude Code
 * @version 1.0.0
 */

import BaseComponent from '../core/base-component.js';

export default class FlexAlert extends BaseComponent {
    /**
     * Default configuration
     */
    static DEFAULTS = {
        variant: 'info',              // success | error | warning | info
        title: null,                  // Alert title
        message: '',                  // Alert message
        icon: null,                   // Custom icon HTML
        dismissible: true,            // Show close button
        autoDismiss: false,           // Auto dismiss after timeout
        dismissTimeout: 5000,         // Timeout in milliseconds
        actions: [],                  // Array of {label, onClick, variant}
        classes: [],                  // Additional CSS classes
        onDismiss: null               // Dismiss callback
    };

    /**
     * Variant mappings to Tailwind classes
     */
    static VARIANTS = {
        success: {
            container: 'bg-green-50 border-green-500 text-green-800',
            icon: 'ph-check-circle text-green-600',
            defaultIcon: '<i class="ph-duotone ph-check-circle text-xl"></i>'
        },
        error: {
            container: 'bg-red-50 border-red-500 text-red-800',
            icon: 'ph-x-circle text-red-600',
            defaultIcon: '<i class="ph-duotone ph-x-circle text-xl"></i>'
        },
        warning: {
            container: 'bg-amber-50 border-amber-500 text-amber-800',
            icon: 'ph-warning text-amber-600',
            defaultIcon: '<i class="ph-duotone ph-warning text-xl"></i>'
        },
        info: {
            container: 'bg-blue-50 border-blue-500 text-blue-800',
            icon: 'ph-info text-blue-600',
            defaultIcon: '<i class="ph-duotone ph-info text-xl"></i>'
        }
    };

    /**
     * Constructor
     */
    constructor(container, options = {}) {
        super(container, options);

        this.state = {
            dismissed: false
        };

        this.alertElement = null;
        this.dismissTimer = null;
        this.init();
    }

    /**
     * Initialize component
     */
    init() {
        this.render();
        this.attachEventListeners();

        if (this.options.autoDismiss && this.options.dismissTimeout > 0) {
            this.startDismissTimer();
        }

        this.emit('init');
    }

    /**
     * Render the alert
     */
    render() {
        const variant = FlexAlert.VARIANTS[this.options.variant];

        // Create alert container
        this.alertElement = document.createElement('div');

        const classes = [
            'border-l-4 rounded-lg shadow-sm p-4',
            'transform transition-all duration-300',
            variant.container,
            ...this.options.classes
        ].filter(Boolean);

        this.alertElement.className = classes.join(' ');

        // Build content
        let content = '<div class="flex items-start gap-3">';

        // Icon
        const iconHTML = this.options.icon || variant.defaultIcon;
        content += `<div class="flex-shrink-0 mt-0.5">${iconHTML}</div>`;

        // Content
        content += '<div class="flex-1 min-w-0">';

        // Title
        if (this.options.title) {
            content += `<h4 class="text-sm font-semibold mb-1">${this.escapeHtml(this.options.title)}</h4>`;
        }

        // Message
        if (this.options.message) {
            content += `<p class="text-sm ${this.options.title ? '' : 'font-medium'}">${this.escapeHtml(this.options.message)}</p>`;
        }

        // Actions
        if (this.options.actions && this.options.actions.length > 0) {
            content += '<div class="flex gap-2 mt-3">';
            this.options.actions.forEach((action, index) => {
                const btnClass = action.variant === 'primary'
                    ? `bg-${this.options.variant}-600 hover:bg-${this.options.variant}-700 text-white`
                    : `bg-transparent hover:bg-${this.options.variant}-100 text-${this.options.variant}-800 border border-${this.options.variant}-300`;
                content += `
                    <button
                        class="px-3 py-1.5 text-sm font-medium rounded-lg transition ${btnClass}"
                        data-action-index="${index}"
                    >
                        ${this.escapeHtml(action.label)}
                    </button>
                `;
            });
            content += '</div>';
        }

        content += '</div>'; // End content

        // Dismiss button
        if (this.options.dismissible) {
            content += `
                <button class="flex-shrink-0 text-gray-500 hover:text-gray-700 transition" data-dismiss="true">
                    <i class="ph ph-x text-lg"></i>
                </button>
            `;
        }

        content += '</div>'; // End flex container

        this.alertElement.innerHTML = content;

        // Replace container content
        this.container.innerHTML = '';
        this.container.appendChild(this.alertElement);
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Dismiss button
        if (this.options.dismissible) {
            const dismissBtn = this.alertElement.querySelector('[data-dismiss="true"]');
            if (dismissBtn) {
                dismissBtn.addEventListener('click', () => this.dismiss());
            }
        }

        // Action buttons
        this.options.actions.forEach((action, index) => {
            const btn = this.alertElement.querySelector(`[data-action-index="${index}"]`);
            if (btn && action.onClick) {
                btn.addEventListener('click', (e) => {
                    action.onClick(e);
                    this.emit('actionClick', { action, index });
                });
            }
        });
    }

    /**
     * Start auto-dismiss timer
     */
    startDismissTimer() {
        this.dismissTimer = setTimeout(() => {
            this.dismiss();
        }, this.options.dismissTimeout);
    }

    /**
     * Stop auto-dismiss timer
     */
    stopDismissTimer() {
        if (this.dismissTimer) {
            clearTimeout(this.dismissTimer);
            this.dismissTimer = null;
        }
    }

    /**
     * Dismiss the alert
     */
    dismiss() {
        if (this.state.dismissed) return;

        this.state.dismissed = true;
        this.stopDismissTimer();

        // Fade out animation
        this.alertElement.style.opacity = '0';
        this.alertElement.style.transform = 'translateX(100%)';

        setTimeout(() => {
            this.alertElement.remove();
            if (this.options.onDismiss) {
                this.options.onDismiss();
            }
            this.emit('dismiss');
            this.destroy();
        }, 300);
    }

    /**
     * Show the alert (if hidden)
     */
    show() {
        this.alertElement.style.opacity = '1';
        this.alertElement.style.transform = 'translateX(0)';
        this.state.dismissed = false;
        this.emit('show');
    }

    /**
     * Update message
     */
    setMessage(message) {
        this.options.message = message;
        this.render();
        this.attachEventListeners();
        this.emit('messageChange', { message });
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
        this.stopDismissTimer();
        if (this.alertElement) {
            this.alertElement.remove();
        }
        super.destroy();
    }
}
