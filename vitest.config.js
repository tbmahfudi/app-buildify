import { defineConfig } from 'vitest/config';

export default defineConfig({
    test: {
        // Use jsdom environment for DOM testing
        environment: 'jsdom',

        // Global test APIs (describe, it, expect, etc.)
        globals: true,

        // Setup files
        setupFiles: ['./tests/setup.js'],

        // Coverage configuration
        coverage: {
            provider: 'v8',
            reporter: ['text', 'html', 'lcov'],
            exclude: [
                'node_modules/',
                'tests/',
                '**/*.test.js',
                '**/*.spec.js',
                '**/showcase.js',
                'vitest.config.js'
            ],
            // Coverage thresholds
            statements: 80,
            branches: 75,
            functions: 80,
            lines: 80
        },

        // Test file patterns
        include: ['tests/**/*.test.js', 'tests/**/*.spec.js'],

        // Watch mode configuration
        watch: false,

        // Reporter
        reporter: ['verbose', 'html'],

        // Timeout
        testTimeout: 10000
    },

    // Resolve configuration
    resolve: {
        alias: {
            '@': '/frontend/assets/js'
        }
    }
});
