/**
 * FlexContainer Component
 *
 * Responsive container for controlling content width, alignment, and horizontal padding.
 * Provides preset width configurations and custom breakpoint-based max-widths.
 *
 * @extends BaseComponent
 *
 * Features:
 * - Preset width configurations (narrow, standard, wide, full)
 * - Custom breakpoint-based max-widths
 * - Responsive horizontal padding (gutters)
 * - Alignment control (left, center, right)
 * - Breakout utilities for full-width children
 * - Responsive value resolution via FlexResponsive
 *
 * @example
 * // Simple preset usage
 * const container = new FlexContainer('#content', {
 *   preset: 'standard',
 *   align: 'center',
 *   gutter: true
 * });
 *
 * @example
 * // Custom configuration
 * const container = new FlexContainer('#content', {
 *   maxWidth: { xs: '100%', lg: '1200px', xl: '1400px' },
 *   padding: { xs: 4, lg: 8 },
 *   align: 'center',
 *   allowBreakout: true
 * });
 */

import { BREAKPOINTS, SPACING_SCALE, EVENTS } from '../core/constants.js';
import BaseComponent from '../core/base-component.js';
import { getResponsive } from '../utilities/flex-responsive.js';

export default class FlexContainer extends BaseComponent {
    /**
     * Preset width configurations for common use cases
     */
    static PRESETS = {
        narrow: {
            xs: '100%',
            md: '768px'
        },
        standard: {
            xs: '100%',
            xl: '1280px'
        },
        wide: {
            xs: '100%',
            xl: '1536px',
            '2xl': '1600px'
        },
        full: {
            xs: '100%'
        }
    };

    /**
     * Default gutter (horizontal padding) configuration
     */
    static DEFAULT_GUTTER = {
        xs: 4,   // 1rem (16px)
        md: 6,   // 1.5rem (24px)
        lg: 8    // 2rem (32px)
    };

    /**
     * Default options
     */
    static DEFAULTS = {
        preset: null,
        maxWidth: null,
        padding: null,
        gutter: true,
        align: 'center',
        allowBreakout: false,
        tag: 'div',
        classes: []
    };

    constructor(container, options = {}) {
        super(container, { ...FlexContainer.DEFAULTS, ...options });

        this.responsive = getResponsive();
        this.containerElement = null;

        this.init();
    }

    /**
     * Initialize the container
     */
    init() {
        this.resolveOptions();
        this.render();
        this.attachEventListeners();
        this.emit(EVENTS.INIT);
    }

    /**
     * Resolve configuration options
     * Priority: custom maxWidth/padding > preset > defaults
     */
    resolveOptions() {
        const { preset, maxWidth, padding, gutter } = this.options;

        // Resolve max-width
        if (preset && FlexContainer.PRESETS[preset]) {
            this.maxWidthConfig = { ...FlexContainer.PRESETS[preset] };
        } else if (maxWidth) {
            this.maxWidthConfig = typeof maxWidth === 'object' ? maxWidth : { xs: maxWidth };
        } else {
            this.maxWidthConfig = FlexContainer.PRESETS.standard;
        }

        // Resolve padding/gutter
        if (padding) {
            this.paddingConfig = typeof padding === 'object' ? padding : { xs: padding };
        } else if (gutter === true) {
            this.paddingConfig = { ...FlexContainer.DEFAULT_GUTTER };
        } else if (typeof gutter === 'object') {
            this.paddingConfig = gutter;
        } else {
            this.paddingConfig = null;
        }
    }

    /**
     * Render the container
     */
    render() {
        // If container is already the element, wrap its content
        if (this.container instanceof HTMLElement) {
            this.containerElement = this.container;
        } else {
            this.containerElement = document.querySelector(this.container);
        }

        if (!this.containerElement) {
            console.error(`FlexContainer: Container not found: ${this.container}`);
            return;
        }

        // Add base classes
        this.containerElement.classList.add('flex-container');

        // Add custom classes
        if (this.options.classes.length > 0) {
            this.containerElement.classList.add(...this.options.classes);
        }

        // Apply initial styles
        this.applyStyles();

        this.emit(EVENTS.RENDER);
    }

    /**
     * Apply all container styles
     */
    applyStyles() {
        this.applyWidthConstraints();
        this.applyAlignment();
        this.applyGutters();
        this.applyBreakoutSupport();
    }

    /**
     * Apply width constraints based on current breakpoint
     */
    applyWidthConstraints() {
        const currentBreakpoint = this.responsive.getCurrentBreakpoint();
        const maxWidth = this.getResponsiveValue(this.maxWidthConfig, currentBreakpoint);

        if (maxWidth === '100%') {
            this.containerElement.style.maxWidth = '100%';
            this.containerElement.style.width = '100%';
        } else {
            this.containerElement.style.maxWidth = maxWidth;
            this.containerElement.style.width = '100%';
        }
    }

    /**
     * Apply alignment styles
     */
    applyAlignment() {
        const { align } = this.options;

        // Reset margins
        this.containerElement.style.marginLeft = '0';
        this.containerElement.style.marginRight = '0';

        if (align === 'center') {
            this.containerElement.style.marginLeft = 'auto';
            this.containerElement.style.marginRight = 'auto';
        } else if (align === 'right') {
            this.containerElement.style.marginLeft = 'auto';
        } else if (align === 'left') {
            this.containerElement.style.marginRight = 'auto';
        }
    }

    /**
     * Apply horizontal padding (gutters)
     */
    applyGutters() {
        if (!this.paddingConfig) {
            return;
        }

        const currentBreakpoint = this.responsive.getCurrentBreakpoint();
        const padding = this.getResponsiveValue(this.paddingConfig, currentBreakpoint);

        if (padding !== null && padding !== undefined) {
            const paddingValue = SPACING_SCALE[padding] || padding;
            this.containerElement.style.paddingLeft = paddingValue;
            this.containerElement.style.paddingRight = paddingValue;
        }
    }

    /**
     * Apply breakout support utilities
     */
    applyBreakoutSupport() {
        if (this.options.allowBreakout) {
            this.containerElement.classList.add('flex-container--breakout-enabled');

            // Add CSS custom property for breakout calculations
            const currentBreakpoint = this.responsive.getCurrentBreakpoint();
            const maxWidth = this.getResponsiveValue(this.maxWidthConfig, currentBreakpoint);

            this.containerElement.style.setProperty('--container-max-width', maxWidth);
        }
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Listen for breakpoint changes
        this.responsive.onBreakpointChange(() => {
            this.applyStyles();
            this.emit(EVENTS.UPDATE, {
                breakpoint: this.responsive.getCurrentBreakpoint(),
                width: this.getComputedWidth()
            });
        });
    }

    /**
     * Set container preset
     * @param {string} preset - Preset name (narrow, standard, wide, full)
     */
    setPreset(preset) {
        if (!FlexContainer.PRESETS[preset]) {
            console.warn(`FlexContainer: Invalid preset "${preset}"`);
            return;
        }

        this.options.preset = preset;
        this.maxWidthConfig = { ...FlexContainer.PRESETS[preset] };
        this.applyWidthConstraints();

        this.emit(EVENTS.UPDATE, { preset });
    }

    /**
     * Set alignment
     * @param {string} align - Alignment value (left, center, right)
     */
    setAlign(align) {
        if (!['left', 'center', 'right'].includes(align)) {
            console.warn(`FlexContainer: Invalid align value "${align}"`);
            return;
        }

        this.options.align = align;
        this.applyAlignment();

        this.emit(EVENTS.UPDATE, { align });
    }

    /**
     * Update padding/gutters
     * @param {number|object} padding - Padding value or responsive config
     */
    updatePadding(padding) {
        if (typeof padding === 'object') {
            this.paddingConfig = padding;
        } else {
            this.paddingConfig = { xs: padding };
        }

        this.applyGutters();

        this.emit(EVENTS.UPDATE, { padding });
    }

    /**
     * Update max-width configuration
     * @param {string|object} maxWidth - Max-width value or responsive config
     */
    updateMaxWidth(maxWidth) {
        if (typeof maxWidth === 'object') {
            this.maxWidthConfig = maxWidth;
        } else {
            this.maxWidthConfig = { xs: maxWidth };
        }

        this.applyWidthConstraints();

        this.emit(EVENTS.UPDATE, { maxWidth });
    }

    /**
     * Enable or disable breakout support
     * @param {boolean} enabled - Whether to enable breakout
     */
    enableBreakout(enabled) {
        this.options.allowBreakout = enabled;

        if (enabled) {
            this.applyBreakoutSupport();
        } else {
            this.containerElement.classList.remove('flex-container--breakout-enabled');
            this.containerElement.style.removeProperty('--container-max-width');
        }

        this.emit(EVENTS.UPDATE, { allowBreakout: enabled });
    }

    /**
     * Get computed width of container
     * @returns {number} Width in pixels
     */
    getComputedWidth() {
        return this.containerElement.getBoundingClientRect().width;
    }

    /**
     * Get current max-width for current breakpoint
     * @returns {string} Max-width value
     */
    getCurrentMaxWidth() {
        const currentBreakpoint = this.responsive.getCurrentBreakpoint();
        return this.getResponsiveValue(this.maxWidthConfig, currentBreakpoint);
    }

    /**
     * Get current padding for current breakpoint
     * @returns {number|string|null} Padding value
     */
    getCurrentPadding() {
        if (!this.paddingConfig) return null;

        const currentBreakpoint = this.responsive.getCurrentBreakpoint();
        return this.getResponsiveValue(this.paddingConfig, currentBreakpoint);
    }

    /**
     * Get container element
     * @returns {HTMLElement}
     */
    getElement() {
        return this.containerElement;
    }

    /**
     * Destroy the container
     */
    destroy() {
        // Remove classes
        this.containerElement.classList.remove('flex-container', 'flex-container--breakout-enabled');

        // Remove custom classes
        if (this.options.classes.length > 0) {
            this.containerElement.classList.remove(...this.options.classes);
        }

        // Remove inline styles
        this.containerElement.style.maxWidth = '';
        this.containerElement.style.width = '';
        this.containerElement.style.marginLeft = '';
        this.containerElement.style.marginRight = '';
        this.containerElement.style.paddingLeft = '';
        this.containerElement.style.paddingRight = '';
        this.containerElement.style.removeProperty('--container-max-width');

        this.emit(EVENTS.DESTROY);

        super.destroy();
    }
}
