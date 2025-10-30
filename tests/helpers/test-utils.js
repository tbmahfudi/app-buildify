/**
 * Test Utilities
 *
 * Helper functions for testing components
 */

/**
 * Create a test container
 */
export function createTestContainer(id = 'test-container') {
    const container = document.createElement('div');
    container.id = id;
    document.body.appendChild(container);
    return container;
}

/**
 * Clean up test container
 */
export function cleanupTestContainer(container) {
    if (container && container.parentNode) {
        container.parentNode.removeChild(container);
    }
}

/**
 * Wait for next tick
 */
export function nextTick() {
    return new Promise(resolve => setTimeout(resolve, 0));
}

/**
 * Wait for specified time
 */
export function wait(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Trigger event on element
 */
export function triggerEvent(element, eventName, detail = {}) {
    const event = new CustomEvent(eventName, {
        bubbles: true,
        cancelable: true,
        detail
    });
    element.dispatchEvent(event);
    return event;
}

/**
 * Simulate click
 */
export function click(element) {
    const event = new MouseEvent('click', {
        bubbles: true,
        cancelable: true
    });
    element.dispatchEvent(event);
}

/**
 * Simulate input
 */
export function input(element, value) {
    element.value = value;
    const event = new Event('input', {
        bubbles: true,
        cancelable: true
    });
    element.dispatchEvent(event);
}

/**
 * Simulate change
 */
export function change(element, value) {
    if (value !== undefined) {
        element.value = value;
    }
    const event = new Event('change', {
        bubbles: true,
        cancelable: true
    });
    element.dispatchEvent(event);
}

/**
 * Simulate focus
 */
export function focus(element) {
    const event = new FocusEvent('focus', {
        bubbles: true,
        cancelable: true
    });
    element.dispatchEvent(event);
}

/**
 * Simulate blur
 */
export function blur(element) {
    const event = new FocusEvent('blur', {
        bubbles: true,
        cancelable: true
    });
    element.dispatchEvent(event);
}

/**
 * Get computed style property
 */
export function getStyle(element, property) {
    return window.getComputedStyle(element).getPropertyValue(property);
}

/**
 * Check if element is visible
 */
export function isVisible(element) {
    const style = window.getComputedStyle(element);
    return style.display !== 'none' &&
           style.visibility !== 'hidden' &&
           style.opacity !== '0';
}

/**
 * Query selector with error
 */
export function query(selector, parent = document) {
    const element = parent.querySelector(selector);
    if (!element) {
        throw new Error(`Element not found: ${selector}`);
    }
    return element;
}

/**
 * Query all with array return
 */
export function queryAll(selector, parent = document) {
    return Array.from(parent.querySelectorAll(selector));
}

/**
 * Create spy for event listener
 */
export function createEventSpy() {
    const calls = [];
    const spy = (...args) => {
        calls.push(args);
    };
    spy.calls = calls;
    spy.called = () => calls.length > 0;
    spy.callCount = () => calls.length;
    spy.lastCall = () => calls[calls.length - 1];
    spy.reset = () => calls.length = 0;
    return spy;
}

/**
 * Resize window for responsive testing
 */
export function resizeWindow(width, height = 768) {
    Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: width
    });
    Object.defineProperty(window, 'innerHeight', {
        writable: true,
        configurable: true,
        value: height
    });
    window.dispatchEvent(new Event('resize'));
}

/**
 * Assert element has class
 */
export function assertHasClass(element, className) {
    if (!element.classList.contains(className)) {
        throw new Error(`Element does not have class: ${className}`);
    }
}

/**
 * Assert element text content
 */
export function assertTextContent(element, expected) {
    const actual = element.textContent.trim();
    if (actual !== expected) {
        throw new Error(`Expected text "${expected}" but got "${actual}"`);
    }
}

/**
 * Mock IntersectionObserver
 */
export function mockIntersectionObserver() {
    global.IntersectionObserver = class IntersectionObserver {
        constructor(callback) {
            this.callback = callback;
        }
        observe() {}
        unobserve() {}
        disconnect() {}
    };
}

/**
 * Mock ResizeObserver
 */
export function mockResizeObserver() {
    global.ResizeObserver = class ResizeObserver {
        constructor(callback) {
            this.callback = callback;
        }
        observe() {}
        unobserve() {}
        disconnect() {}
    };
}
