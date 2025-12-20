/**
 * FlexSpinner - Flexible Spinner/Loading Component
 *
 * A reusable loading spinner component with Tailwind styling supporting:
 * - Multiple variants (border, dots, pulse, bars)
 * - Multiple sizes (xs, sm, md, lg, xl)
 * - Color customization
 * - Text label
 * - Overlay mode for full-page loading
 *
 * @author Claude Code
 * @version 1.0.0
 */

import BaseComponent from '../core/base-component.js';

export default class FlexSpinner extends BaseComponent {
    /**
     * Default configuration
     */
    static DEFAULTS = {
        variant: 'border',            // border | dots | pulse | bars
        size: 'md',                   // xs | sm | md | lg | xl
        color: 'blue',                // blue | gray | green | red | amber | etc.
        text: null,                   // Loading text
        overlay: false,               // Full-page overlay
        center: false,                // Center in container
        classes: []                   // Additional CSS classes
    };

    /**
     * Size mappings
     */
    static SIZES = {
        xs: { spinner: 'w-4 h-4', text: 'text-xs', gap: 'gap-2' },
        sm: { spinner: 'w-5 h-5', text: 'text-sm', gap: 'gap-2' },
        md: { spinner: 'w-8 h-8', text: 'text-base', gap: 'gap-3' },
        lg: { spinner: 'w-12 h-12', text: 'text-lg', gap: 'gap-3' },
        xl: { spinner: 'w-16 h-16', text: 'text-xl', gap: 'gap-4' }
    };

    /**
     * Constructor
     */
    constructor(container, options = {}) {
        super(container, options);

        this.spinnerElement = null;
        this.init();
    }

    /**
     * Initialize component
     */
    init() {
        this.render();
        this.emit('init');
    }

    /**
     * Render the spinner
     */
    render() {
        const size = FlexSpinner.SIZES[this.options.size];

        // Create wrapper
        this.spinnerElement = document.createElement('div');

        const wrapperClasses = [
            'flex items-center',
            size.gap,
            this.options.center ? 'justify-center' : '',
            this.options.overlay ? 'fixed inset-0 bg-black bg-opacity-50 z-50' : '',
            ...this.options.classes
        ].filter(Boolean);

        this.spinnerElement.className = wrapperClasses.join(' ');

        // Build content
        let content = '';

        // Spinner based on variant
        switch (this.options.variant) {
            case 'border':
                content += this.renderBorderSpinner(size);
                break;
            case 'dots':
                content += this.renderDotsSpinner(size);
                break;
            case 'pulse':
                content += this.renderPulseSpinner(size);
                break;
            case 'bars':
                content += this.renderBarsSpinner(size);
                break;
            default:
                content += this.renderBorderSpinner(size);
        }

        // Text label
        if (this.options.text) {
            content += `<span class="font-medium text-gray-700 ${size.text}">${this.escapeHtml(this.options.text)}</span>`;
        }

        this.spinnerElement.innerHTML = content;

        // Replace container content
        this.container.innerHTML = '';
        this.container.appendChild(this.spinnerElement);
    }

    /**
     * Render border spinner (spinning circle)
     */
    renderBorderSpinner(size) {
        return `
            <div class="${size.spinner} border-4 border-${this.options.color}-200 border-t-${this.options.color}-600 rounded-full animate-spin"></div>
        `;
    }

    /**
     * Render dots spinner (three bouncing dots)
     */
    renderDotsSpinner(size) {
        const dotSize = this.getDotSize(this.options.size);
        return `
            <div class="flex items-center gap-1">
                <div class="${dotSize} bg-${this.options.color}-600 rounded-full animate-bounce" style="animation-delay: 0ms"></div>
                <div class="${dotSize} bg-${this.options.color}-600 rounded-full animate-bounce" style="animation-delay: 150ms"></div>
                <div class="${dotSize} bg-${this.options.color}-600 rounded-full animate-bounce" style="animation-delay: 300ms"></div>
            </div>
        `;
    }

    /**
     * Render pulse spinner (pulsing circle)
     */
    renderPulseSpinner(size) {
        return `
            <div class="${size.spinner} bg-${this.options.color}-600 rounded-full animate-pulse"></div>
        `;
    }

    /**
     * Render bars spinner (vertical bars)
     */
    renderBarsSpinner(size) {
        const barSize = this.getBarSize(this.options.size);
        return `
            <div class="flex items-end gap-1 ${size.spinner.split(' ')[0]}">
                <div class="${barSize} bg-${this.options.color}-600 animate-pulse" style="animation-delay: 0ms"></div>
                <div class="${barSize} bg-${this.options.color}-600 animate-pulse" style="animation-delay: 150ms"></div>
                <div class="${barSize} bg-${this.options.color}-600 animate-pulse" style="animation-delay: 300ms"></div>
                <div class="${barSize} bg-${this.options.color}-600 animate-pulse" style="animation-delay: 450ms"></div>
            </div>
        `;
    }

    /**
     * Get dot size based on spinner size
     */
    getDotSize(size) {
        const sizes = {
            xs: 'w-1 h-1',
            sm: 'w-1.5 h-1.5',
            md: 'w-2 h-2',
            lg: 'w-3 h-3',
            xl: 'w-4 h-4'
        };
        return sizes[size] || sizes.md;
    }

    /**
     * Get bar size based on spinner size
     */
    getBarSize(size) {
        const sizes = {
            xs: 'w-0.5 h-3',
            sm: 'w-1 h-4',
            md: 'w-1 h-6',
            lg: 'w-1.5 h-8',
            xl: 'w-2 h-10'
        };
        return sizes[size] || sizes.md;
    }

    /**
     * Show spinner
     */
    show() {
        this.spinnerElement.classList.remove('hidden');
        this.emit('show');
    }

    /**
     * Hide spinner
     */
    hide() {
        this.spinnerElement.classList.add('hidden');
        this.emit('hide');
    }

    /**
     * Set text
     */
    setText(text) {
        this.options.text = text;
        this.render();
        this.emit('textChange', { text });
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
        if (this.spinnerElement) {
            this.spinnerElement.remove();
        }
        super.destroy();
    }
}
