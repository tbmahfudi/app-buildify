import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import FlexSpinner from '../../frontend/assets/js/components/flex-spinner.js';
import { createTestContainer, cleanupTestContainer } from '../helpers/test-utils.js';

describe('FlexSpinner', () => {
    let container;

    beforeEach(() => { container = createTestContainer(); });
    afterEach(() => { cleanupTestContainer(container); });

    describe('Initialization', () => {
        it('should create spinner element', () => {
            const spinner = new FlexSpinner(container);
            expect(spinner.spinnerElement).toBeTruthy();
        });

        it('should emit init event', () => {
            const cb = vi.fn();
            const spinner = new FlexSpinner(container);
            spinner.on('init', cb);
            spinner.emit('init');
            expect(cb).toHaveBeenCalled();
        });
    });

    describe('Variants', () => {
        it('should render border variant by default', () => {
            const spinner = new FlexSpinner(container, { variant: 'border' });
            expect(spinner.spinnerElement.innerHTML).toContain('animate-spin');
        });

        it('should render dots variant', () => {
            const spinner = new FlexSpinner(container, { variant: 'dots' });
            expect(spinner.spinnerElement).toBeTruthy();
        });

        it('should render pulse variant', () => {
            const spinner = new FlexSpinner(container, { variant: 'pulse' });
            expect(spinner.spinnerElement).toBeTruthy();
        });
    });

    describe('Sizes', () => {
        it('should apply md size by default', () => {
            const spinner = new FlexSpinner(container);
            expect(spinner.spinnerElement.innerHTML).toContain('w-8');
        });

        it('should apply sm size', () => {
            const spinner = new FlexSpinner(container, { size: 'sm' });
            expect(spinner.spinnerElement.innerHTML).toContain('w-5');
        });

        it('should apply lg size', () => {
            const spinner = new FlexSpinner(container, { size: 'lg' });
            expect(spinner.spinnerElement.innerHTML).toContain('w-12');
        });
    });

    describe('Text label', () => {
        it('should render text when provided', () => {
            const spinner = new FlexSpinner(container, { text: 'Loading...' });
            expect(spinner.spinnerElement.textContent).toContain('Loading...');
        });

        it('should not render text when not provided', () => {
            const spinner = new FlexSpinner(container);
            const textEl = spinner.spinnerElement.querySelector('.spinner-text');
            expect(textEl).toBeNull();
        });
    });

    describe('Overlay mode', () => {
        it('should add overlay class when overlay is true', () => {
            const spinner = new FlexSpinner(container, { overlay: true });
            expect(spinner.spinnerElement.className).toContain('fixed');
        });
    });

    describe('Cleanup', () => {
        it('should destroy component', () => {
            const spinner = new FlexSpinner(container);
            expect(() => spinner.destroy()).not.toThrow();
        });
    });
});
