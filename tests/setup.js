/**
 * Test Setup File
 *
 * Global setup for all tests
 */

import { vi } from 'vitest';

// Mock console methods in tests to reduce noise
global.console = {
    ...console,
    log: vi.fn(),
    debug: vi.fn(),
    info: vi.fn(),
    warn: vi.fn(),
    // Keep error for debugging
    error: console.error
};

// Mock matchMedia for responsive components
Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation(query => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
    })),
});

// Add custom matchers or global setup here
beforeEach(() => {
    // Clear DOM before each test
    document.body.innerHTML = '';
});

afterEach(() => {
    // Cleanup after each test
    vi.clearAllMocks();
});
