/**
 * BaseComponent
 *
 * Base class for all layout components providing common functionality
 *
 * @author Claude Code
 * @version 1.0.0
 */

import { EVENTS } from './constants.js';

export class BaseComponent {
    /**
     * Create a new BaseComponent
     * @param {string|HTMLElement} container - Container selector or element
     * @param {Object} options - Configuration options
     */
    constructor(container, options = {}) {
        // Resolve container
        if (typeof container === 'string') {
            this.container = document.querySelector(container);
        } else if (container instanceof HTMLElement) {
            this.container = container;
        } else {
            throw new Error('Container must be a selector string or HTMLElement');
        }

        if (!this.container) {
            throw new Error('Container element not found');
        }

        // Store options
        this.options = options;

        // Component state
        this.state = {
            initialized: false,
            destroyed: false
        };

        // Event listeners storage
        this._listeners = new Map();

        // DOM references
        this.elements = {};

        // Generate unique ID
        this.id = this.generateId();
    }

    /**
     * Generate unique component ID
     */
    generateId() {
        return `component-${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Emit custom event
     * @param {string} eventName - Event name
     * @param {*} detail - Event detail data
     */
    emit(eventName, detail = null) {
        const event = new CustomEvent(eventName, {
            detail: {
                component: this,
                ...detail
            },
            bubbles: true
        });
        this.container.dispatchEvent(event);

        // Call callback if exists
        const callbackName = `on${eventName.charAt(0).toUpperCase() + eventName.slice(1).replace(/[:-]/g, '')}`;
        if (typeof this.options[callbackName] === 'function') {
            this.options[callbackName](detail);
        }
    }

    /**
     * Add event listener
     * @param {string} eventName - Event name
     * @param {Function} handler - Event handler
     */
    on(eventName, handler) {
        if (!this._listeners.has(eventName)) {
            this._listeners.set(eventName, []);
        }
        this._listeners.get(eventName).push(handler);
        this.container.addEventListener(eventName, handler);
    }

    /**
     * Remove event listener
     * @param {string} eventName - Event name
     * @param {Function} handler - Event handler
     */
    off(eventName, handler) {
        const handlers = this._listeners.get(eventName);
        if (handlers) {
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
        this.container.removeEventListener(eventName, handler);
    }

    /**
     * Remove all event listeners
     */
    removeAllListeners() {
        this._listeners.forEach((handlers, eventName) => {
            handlers.forEach(handler => {
                this.container.removeEventListener(eventName, handler);
            });
        });
        this._listeners.clear();
    }

    /**
     * Merge options with defaults
     * @param {Object} defaults - Default options
     * @param {Object} options - User options
     */
    mergeOptions(defaults, options) {
        return this.deepMerge(defaults, options);
    }

    /**
     * Deep merge objects
     * @param {Object} target - Target object
     * @param {Object} source - Source object
     */
    deepMerge(target, source) {
        const result = { ...target };

        for (const key in source) {
            if (source.hasOwnProperty(key)) {
                if (this.isObject(source[key]) && this.isObject(target[key])) {
                    result[key] = this.deepMerge(target[key], source[key]);
                } else {
                    result[key] = source[key];
                }
            }
        }

        return result;
    }

    /**
     * Check if value is a plain object
     * @param {*} value - Value to check
     */
    isObject(value) {
        return value !== null && typeof value === 'object' && !Array.isArray(value);
    }

    /**
     * Create element with classes
     * @param {string} tag - HTML tag name
     * @param {string|string[]} classes - CSS classes
     * @param {Object} attributes - HTML attributes
     */
    createElement(tag, classes = [], attributes = {}) {
        const element = document.createElement(tag);

        // Add classes
        if (typeof classes === 'string') {
            classes = classes.split(' ').filter(c => c);
        }
        if (classes.length > 0) {
            element.classList.add(...classes);
        }

        // Add attributes
        for (const [key, value] of Object.entries(attributes)) {
            if (key === 'dataset') {
                for (const [dataKey, dataValue] of Object.entries(value)) {
                    element.dataset[dataKey] = dataValue;
                }
            } else if (value !== null && value !== undefined) {
                element.setAttribute(key, value);
            }
        }

        return element;
    }

    /**
     * Add classes to element
     * @param {HTMLElement} element - Target element
     * @param {string|string[]} classes - Classes to add
     */
    addClass(element, classes) {
        if (typeof classes === 'string') {
            classes = classes.split(' ').filter(c => c);
        }
        element.classList.add(...classes);
    }

    /**
     * Remove classes from element
     * @param {HTMLElement} element - Target element
     * @param {string|string[]} classes - Classes to remove
     */
    removeClass(element, classes) {
        if (typeof classes === 'string') {
            classes = classes.split(' ').filter(c => c);
        }
        element.classList.remove(...classes);
    }

    /**
     * Toggle classes on element
     * @param {HTMLElement} element - Target element
     * @param {string|string[]} classes - Classes to toggle
     */
    toggleClass(element, classes) {
        if (typeof classes === 'string') {
            classes = classes.split(' ').filter(c => c);
        }
        classes.forEach(cls => element.classList.toggle(cls));
    }

    /**
     * Get responsive value based on current breakpoint
     * @param {*} value - Value or object with breakpoint keys
     * @param {string} currentBreakpoint - Current breakpoint
     */
    getResponsiveValue(value, currentBreakpoint) {
        if (typeof value !== 'object' || value === null || Array.isArray(value)) {
            return value;
        }

        // If it's a responsive object, find the appropriate value
        const breakpoints = ['xs', 'sm', 'md', 'lg', 'xl', '2xl'];
        const currentIndex = breakpoints.indexOf(currentBreakpoint);

        // Find the closest defined value at or below current breakpoint
        for (let i = currentIndex; i >= 0; i--) {
            const bp = breakpoints[i];
            if (value[bp] !== undefined) {
                return value[bp];
            }
        }

        // Fallback to xs or first available value
        return value.xs || value[breakpoints.find(bp => value[bp] !== undefined)];
    }

    /**
     * Debounce function
     * @param {Function} func - Function to debounce
     * @param {number} wait - Wait time in ms
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
     * Throttle function
     * @param {Function} func - Function to throttle
     * @param {number} limit - Time limit in ms
     */
    throttle(func, limit) {
        let inThrottle;
        return function executedFunction(...args) {
            if (!inThrottle) {
                func(...args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    /**
     * Get component state
     */
    getState() {
        return { ...this.state };
    }

    /**
     * Update component state
     * @param {Object} updates - State updates
     */
    setState(updates) {
        const oldState = { ...this.state };
        this.state = { ...this.state, ...updates };
        this.emit(EVENTS.STATE_CHANGE, { oldState, newState: this.state });
    }

    /**
     * Get all items (to be implemented by child classes)
     */
    getItems() {
        return [];
    }

    /**
     * Clear all items (to be implemented by child classes)
     */
    clear() {
        // Override in child classes
    }

    /**
     * Destroy component and cleanup
     */
    destroy() {
        if (this.state.destroyed) return;

        this.emit(EVENTS.DESTROY);
        this.removeAllListeners();

        if (this.container) {
            this.container.innerHTML = '';
        }

        this.state.destroyed = true;
        this.elements = {};
    }

    /**
     * Get main component element
     */
    getElement() {
        return this.elements.main || this.container;
    }
}

export default BaseComponent;
