/**
 * FlexTooltip - Flexible Tooltip Component
 *
 * A reusable tooltip component with Tailwind styling supporting:
 * - Multiple positions (top, bottom, left, right)
 * - Trigger events (hover, click, focus)
 * - Auto-positioning to stay in viewport
 * - Arrow indicator
 * - Delay options
 *
 * @author Claude Code
 * @version 1.0.0
 */

import BaseComponent from '../core/base-component.js';

export default class FlexTooltip extends BaseComponent {
    /**
     * Default configuration
     */
    static DEFAULTS = {
        content: '',                  // Tooltip content
        position: 'top',              // top | bottom | left | right
        trigger: 'hover',             // hover | click | focus | manual
        delay: 0,                     // Show delay in milliseconds
        hideDelay: 0,                 // Hide delay in milliseconds
        arrow: true,                  // Show arrow
        offset: 8,                    // Distance from trigger element
        maxWidth: '300px',            // Maximum width
        classes: [],                  // Additional CSS classes
        onShow: null,                 // Show callback
        onHide: null                  // Hide callback
    };

    /**
     * Constructor
     */
    constructor(triggerElement, options = {}) {
        // Create a wrapper div to use as container
        const wrapper = document.createElement('div');
        wrapper.style.display = 'inline-block';
        wrapper.style.position = 'relative';

        super(wrapper, options);

        this.triggerElement = triggerElement;
        this.tooltipElement = null;
        this.showTimer = null;
        this.hideTimer = null;

        this.state = {
            visible: false
        };

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
     * Render the tooltip
     */
    render() {
        // Create tooltip element
        this.tooltipElement = document.createElement('div');

        const classes = [
            'absolute z-50 px-3 py-2',
            'bg-gray-900 text-white text-sm rounded-lg shadow-lg',
            'opacity-0 invisible',
            'transition-all duration-200',
            'pointer-events-none',
            ...this.options.classes
        ].filter(Boolean);

        this.tooltipElement.className = classes.join(' ');
        this.tooltipElement.style.maxWidth = this.options.maxWidth;

        // Set content
        this.tooltipElement.textContent = this.options.content;

        // Add arrow if enabled
        if (this.options.arrow) {
            const arrow = document.createElement('div');
            arrow.className = 'tooltip-arrow absolute w-2 h-2 bg-gray-900 transform rotate-45';
            this.tooltipElement.appendChild(arrow);
        }

        // Add to body (to avoid z-index/overflow issues)
        document.body.appendChild(this.tooltipElement);
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        if (this.options.trigger === 'hover') {
            this.triggerElement.addEventListener('mouseenter', () => this.show());
            this.triggerElement.addEventListener('mouseleave', () => this.hide());
        } else if (this.options.trigger === 'click') {
            this.triggerElement.addEventListener('click', () => this.toggle());
            document.addEventListener('click', (e) => {
                if (!this.triggerElement.contains(e.target) && !this.tooltipElement.contains(e.target)) {
                    this.hide();
                }
            });
        } else if (this.options.trigger === 'focus') {
            this.triggerElement.addEventListener('focus', () => this.show());
            this.triggerElement.addEventListener('blur', () => this.hide());
        }
    }

    /**
     * Show tooltip
     */
    show() {
        if (this.state.visible) return;

        this.clearTimers();

        this.showTimer = setTimeout(() => {
            this.state.visible = true;
            this.position();
            this.tooltipElement.classList.remove('opacity-0', 'invisible');
            this.tooltipElement.classList.add('opacity-100', 'visible');

            if (this.options.onShow) {
                this.options.onShow();
            }
            this.emit('show');
        }, this.options.delay);
    }

    /**
     * Hide tooltip
     */
    hide() {
        if (!this.state.visible) return;

        this.clearTimers();

        this.hideTimer = setTimeout(() => {
            this.state.visible = false;
            this.tooltipElement.classList.remove('opacity-100', 'visible');
            this.tooltipElement.classList.add('opacity-0', 'invisible');

            if (this.options.onHide) {
                this.options.onHide();
            }
            this.emit('hide');
        }, this.options.hideDelay);
    }

    /**
     * Toggle tooltip
     */
    toggle() {
        if (this.state.visible) {
            this.hide();
        } else {
            this.show();
        }
    }

    /**
     * Position tooltip relative to trigger element
     */
    position() {
        const triggerRect = this.triggerElement.getBoundingClientRect();
        const tooltipRect = this.tooltipElement.getBoundingClientRect();
        const arrow = this.tooltipElement.querySelector('.tooltip-arrow');

        let top, left;

        switch (this.options.position) {
            case 'top':
                top = triggerRect.top - tooltipRect.height - this.options.offset;
                left = triggerRect.left + (triggerRect.width / 2) - (tooltipRect.width / 2);
                if (arrow) {
                    arrow.style.bottom = '-4px';
                    arrow.style.left = '50%';
                    arrow.style.transform = 'translateX(-50%) rotate(45deg)';
                }
                break;

            case 'bottom':
                top = triggerRect.bottom + this.options.offset;
                left = triggerRect.left + (triggerRect.width / 2) - (tooltipRect.width / 2);
                if (arrow) {
                    arrow.style.top = '-4px';
                    arrow.style.left = '50%';
                    arrow.style.transform = 'translateX(-50%) rotate(45deg)';
                }
                break;

            case 'left':
                top = triggerRect.top + (triggerRect.height / 2) - (tooltipRect.height / 2);
                left = triggerRect.left - tooltipRect.width - this.options.offset;
                if (arrow) {
                    arrow.style.right = '-4px';
                    arrow.style.top = '50%';
                    arrow.style.transform = 'translateY(-50%) rotate(45deg)';
                }
                break;

            case 'right':
                top = triggerRect.top + (triggerRect.height / 2) - (tooltipRect.height / 2);
                left = triggerRect.right + this.options.offset;
                if (arrow) {
                    arrow.style.left = '-4px';
                    arrow.style.top = '50%';
                    arrow.style.transform = 'translateY(-50%) rotate(45deg)';
                }
                break;
        }

        // Keep tooltip in viewport
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;

        if (left < 0) left = 8;
        if (left + tooltipRect.width > viewportWidth) left = viewportWidth - tooltipRect.width - 8;
        if (top < 0) top = 8;
        if (top + tooltipRect.height > viewportHeight) top = viewportHeight - tooltipRect.height - 8;

        this.tooltipElement.style.top = `${top + window.scrollY}px`;
        this.tooltipElement.style.left = `${left + window.scrollX}px`;
    }

    /**
     * Clear timers
     */
    clearTimers() {
        if (this.showTimer) {
            clearTimeout(this.showTimer);
            this.showTimer = null;
        }
        if (this.hideTimer) {
            clearTimeout(this.hideTimer);
            this.hideTimer = null;
        }
    }

    /**
     * Update content
     */
    setContent(content) {
        this.options.content = content;
        this.tooltipElement.textContent = content;
        if (this.options.arrow) {
            const arrow = document.createElement('div');
            arrow.className = 'tooltip-arrow absolute w-2 h-2 bg-gray-900 transform rotate-45';
            this.tooltipElement.appendChild(arrow);
        }
        this.emit('contentChange', { content });
    }

    /**
     * Destroy component
     */
    destroy() {
        this.clearTimers();
        if (this.tooltipElement) {
            this.tooltipElement.remove();
        }
        super.destroy();
    }
}
