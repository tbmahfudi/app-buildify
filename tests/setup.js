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

// Add custom matchers or global setup here
beforeEach(() => {
    // Clear DOM before each test
    document.body.innerHTML = '';
});

afterEach(() => {
    // Cleanup after each test
    vi.clearAllMocks();
});
