/**
 * FlexResponsive - Responsive Utility System
 *
 * Centralized responsive behavior management with breakpoint detection,
 * media query listeners, and viewport tracking.
 *
 * @author Claude Code
 * @version 1.0.0
 */

import { BREAKPOINTS, BREAKPOINT_ORDER, EVENTS } from '../core/constants.js';

export class FlexResponsive {
    /**
     * Create a new FlexResponsive instance
     * @param {Object} options - Configuration options
     */
    constructor(options = {}) {
        this.options = {
            breakpoints: BREAKPOINTS,
            debounceDelay: 150,
            ...options
        };

        // Current state
        this.state = {
            breakpoint: null,
            previousBreakpoint: null,
            viewport: {
                width: 0,
                height: 0,
                orientation: null
            }
        };

        // Listeners
        this._listeners = {
            breakpoint: [],
            orientation: [],
            resize: []
        };

        // Bound handlers
        this._handleResize = this.debounce(this._onResize.bind(this), this.options.debounceDelay);
        this._handleOrientationChange = this._onOrientationChange.bind(this);

        // Initialize
        this.init();
    }

    /**
     * Initialize responsive system
     */
    init() {
        // Set initial state
        this._updateState();

        // Add event listeners
        window.addEventListener('resize', this._handleResize);
        window.addEventListener('orientationchange', this._handleOrientationChange);

        // Create media query listeners for each breakpoint
        this._createMediaQueryListeners();
    }

    /**
     * Create media query listeners for breakpoint detection
     */
    _createMediaQueryListeners() {
        this.mediaQueries = {};

        BREAKPOINT_ORDER.forEach((bp, index) => {
            const minWidth = this.options.breakpoints[bp];
            const nextBp = BREAKPOINT_ORDER[index + 1];
            const maxWidth = nextBp ? this.options.breakpoints[nextBp] - 1 : Infinity;

            let query;
            if (maxWidth === Infinity) {
                query = `(min-width: ${minWidth}px)`;
            } else {
                query = `(min-width: ${minWidth}px) and (max-width: ${maxWidth}px)`;
            }

            const mql = window.matchMedia(query);
            this.mediaQueries[bp] = mql;

            // Add listener
            const handler = (e) => {
                if (e.matches) {
                    this._setBreakpoint(bp);
                }
            };

            // Modern browsers
            if (mql.addEventListener) {
                mql.addEventListener('change', handler);
            } else {
                // Fallback for older browsers
                mql.addListener(handler);
            }
        });
    }

    /**
     * Handle window resize
     */
    _onResize() {
        this._updateState();

        // Trigger resize listeners
        this._listeners.resize.forEach(callback => {
            callback(this.state.viewport);
        });
    }

    /**
     * Handle orientation change
     */
    _onOrientationChange() {
        setTimeout(() => {
            this._updateState();

            // Trigger orientation listeners
            this._listeners.orientation.forEach(callback => {
                callback(this.state.viewport.orientation);
            });
        }, 100); // Small delay for accurate dimensions
    }

    /**
     * Update current state
     */
    _updateState() {
        // Update viewport
        this.state.viewport = {
            width: window.innerWidth,
            height: window.innerHeight,
            orientation: window.innerWidth > window.innerHeight ? 'landscape' : 'portrait'
        };

        // Update breakpoint
        const newBreakpoint = this._detectBreakpoint();
        if (newBreakpoint !== this.state.breakpoint) {
            this._setBreakpoint(newBreakpoint);
        }
    }

    /**
     * Detect current breakpoint
     */
    _detectBreakpoint() {
        const width = window.innerWidth;

        // Find the largest breakpoint that matches
        for (let i = BREAKPOINT_ORDER.length - 1; i >= 0; i--) {
            const bp = BREAKPOINT_ORDER[i];
            if (width >= this.options.breakpoints[bp]) {
                return bp;
            }
        }

        return 'xs';
    }

    /**
     * Set current breakpoint and trigger callbacks
     */
    _setBreakpoint(breakpoint) {
        if (breakpoint === this.state.breakpoint) return;

        this.state.previousBreakpoint = this.state.breakpoint;
        this.state.breakpoint = breakpoint;

        // Trigger breakpoint listeners
        this._listeners.breakpoint.forEach(callback => {
            callback(breakpoint, this.state.previousBreakpoint);
        });

        // Trigger callback option if exists
        if (this.options.onBreakpointChange) {
            this.options.onBreakpointChange(breakpoint, this.state.previousBreakpoint);
        }
    }

    /**
     * Get current breakpoint
     * @returns {string} Current breakpoint name
     */
    getCurrentBreakpoint() {
        return this.state.breakpoint;
    }

    /**
     * Check if current breakpoint matches
     * @param {string} breakpoint - Breakpoint to check
     * @returns {boolean}
     */
    isBreakpoint(breakpoint) {
        return this.state.breakpoint === breakpoint;
    }

    /**
     * Check if current breakpoint is above given breakpoint
     * @param {string} breakpoint - Breakpoint to compare
     * @returns {boolean}
     */
    isAbove(breakpoint) {
        const currentIndex = BREAKPOINT_ORDER.indexOf(this.state.breakpoint);
        const targetIndex = BREAKPOINT_ORDER.indexOf(breakpoint);
        return currentIndex > targetIndex;
    }

    /**
     * Check if current breakpoint is below given breakpoint
     * @param {string} breakpoint - Breakpoint to compare
     * @returns {boolean}
     */
    isBelow(breakpoint) {
        const currentIndex = BREAKPOINT_ORDER.indexOf(this.state.breakpoint);
        const targetIndex = BREAKPOINT_ORDER.indexOf(breakpoint);
        return currentIndex < targetIndex;
    }

    /**
     * Check if current breakpoint is at or above given breakpoint
     * @param {string} breakpoint - Breakpoint to compare
     * @returns {boolean}
     */
    isAtLeast(breakpoint) {
        const currentIndex = BREAKPOINT_ORDER.indexOf(this.state.breakpoint);
        const targetIndex = BREAKPOINT_ORDER.indexOf(breakpoint);
        return currentIndex >= targetIndex;
    }

    /**
     * Get current viewport dimensions and orientation
     * @returns {Object} Viewport info
     */
    getViewport() {
        return { ...this.state.viewport };
    }

    /**
     * Subscribe to breakpoint changes
     * @param {Function} callback - Callback function
     * @returns {Function} Unsubscribe function
     */
    onBreakpointChange(callback) {
        this._listeners.breakpoint.push(callback);

        // Return unsubscribe function
        return () => {
            const index = this._listeners.breakpoint.indexOf(callback);
            if (index > -1) {
                this._listeners.breakpoint.splice(index, 1);
            }
        };
    }

    /**
     * Subscribe to orientation changes
     * @param {Function} callback - Callback function
     * @returns {Function} Unsubscribe function
     */
    onOrientationChange(callback) {
        this._listeners.orientation.push(callback);

        return () => {
            const index = this._listeners.orientation.indexOf(callback);
            if (index > -1) {
                this._listeners.orientation.splice(index, 1);
            }
        };
    }

    /**
     * Subscribe to resize events
     * @param {Function} callback - Callback function
     * @returns {Function} Unsubscribe function
     */
    onResize(callback) {
        this._listeners.resize.push(callback);

        return () => {
            const index = this._listeners.resize.indexOf(callback);
            if (index > -1) {
                this._listeners.resize.splice(index, 1);
            }
        };
    }

    /**
     * Show element on specified breakpoints
     * @param {HTMLElement} element - Target element
     * @param {string[]} breakpoints - Breakpoints to show on
     */
    showOn(element, breakpoints) {
        const update = () => {
            const shouldShow = breakpoints.includes(this.state.breakpoint);
            element.style.display = shouldShow ? '' : 'none';
        };

        update();
        return this.onBreakpointChange(update);
    }

    /**
     * Hide element on specified breakpoints
     * @param {HTMLElement} element - Target element
     * @param {string[]} breakpoints - Breakpoints to hide on
     */
    hideOn(element, breakpoints) {
        const update = () => {
            const shouldHide = breakpoints.includes(this.state.breakpoint);
            element.style.display = shouldHide ? 'none' : '';
        };

        update();
        return this.onBreakpointChange(update);
    }

    /**
     * Swap components based on breakpoint
     * @param {Object} config - Configuration object
     */
    swap(config) {
        const { element, components } = config;
        const container = typeof element === 'string'
            ? document.querySelector(element)
            : element;

        if (!container) return;

        const update = () => {
            const bp = this.state.breakpoint;
            const component = this.getResponsiveValue(components, bp);

            if (component) {
                container.innerHTML = '';
                if (typeof component === 'string') {
                    container.innerHTML = component;
                } else if (component instanceof HTMLElement) {
                    container.appendChild(component);
                }
            }
        };

        update();
        return this.onBreakpointChange(update);
    }

    /**
     * Get responsive value based on current breakpoint
     * @param {*} value - Value or object with breakpoint keys
     * @param {string} breakpoint - Breakpoint to use (defaults to current)
     */
    getResponsiveValue(value, breakpoint = null) {
        if (typeof value !== 'object' || value === null || Array.isArray(value)) {
            return value;
        }

        const bp = breakpoint || this.state.breakpoint;
        const currentIndex = BREAKPOINT_ORDER.indexOf(bp);

        // Find the closest defined value at or below current breakpoint
        for (let i = currentIndex; i >= 0; i--) {
            const breakpointKey = BREAKPOINT_ORDER[i];
            if (value[breakpointKey] !== undefined) {
                return value[breakpointKey];
            }
        }

        // Fallback to xs or first available value
        return value.xs || value[BREAKPOINT_ORDER.find(key => value[key] !== undefined)];
    }

    /**
     * Debounce function
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * Destroy and cleanup
     */
    destroy() {
        // Remove event listeners
        window.removeEventListener('resize', this._handleResize);
        window.removeEventListener('orientationchange', this._handleOrientationChange);

        // Remove media query listeners
        Object.values(this.mediaQueries).forEach(mql => {
            if (mql.removeEventListener) {
                mql.removeEventListener('change', () => {});
            } else {
                mql.removeListener(() => {});
            }
        });

        // Clear listeners
        this._listeners = {
            breakpoint: [],
            orientation: [],
            resize: []
        };
    }
}

// Create singleton instance
let instance = null;

/**
 * Get or create FlexResponsive singleton instance
 * @param {Object} options - Configuration options
 * @returns {FlexResponsive}
 */
export function getResponsive(options = {}) {
    if (!instance) {
        instance = new FlexResponsive(options);
    }
    return instance;
}

export default FlexResponsive;
