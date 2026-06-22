import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import FlexButton from '../../frontend/assets/js/components/flex-button.js';
import { createTestContainer, cleanupTestContainer, click } from '../helpers/test-utils.js';

vi.mock('../../frontend/assets/js/rbac.js', () => ({
    hasPermission: vi.fn().mockReturnValue(true)
}));

describe('FlexButton', () => {
    let container;

    beforeEach(() => { container = createTestContainer(); });
    afterEach(() => { cleanupTestContainer(container); });

    describe('Initialization', () => {
        it('should create button with default options', () => {
            const btn = new FlexButton(container);
            expect(btn.buttonElement).toBeTruthy();
            expect(btn.buttonElement.tagName).toBe('BUTTON');
        });

        it('should render default text', () => {
            const btn = new FlexButton(container);
            expect(btn.buttonElement.textContent).toContain('Button');
        });

        it('should emit init event', () => {
            const cb = vi.fn();
            const btn = new FlexButton(container);
            btn.on('init', cb);
            btn.emit('init');
            expect(cb).toHaveBeenCalled();
        });
    });

    describe('Variants', () => {
        it('should apply primary variant by default', () => {
            const btn = new FlexButton(container, { variant: 'primary' });
            expect(btn.buttonElement.className).toContain('bg-blue-600');
        });

        it('should apply danger variant', () => {
            const btn = new FlexButton(container, { variant: 'danger' });
            expect(btn.buttonElement.className).toContain('bg-red-600');
        });

        it('should apply outline variant', () => {
            const btn = new FlexButton(container, { variant: 'outline' });
            expect(btn.buttonElement.className).toContain('bg-transparent');
        });
    });

    describe('Sizes', () => {
        it('should apply md size by default', () => {
            const btn = new FlexButton(container);
            expect(btn.buttonElement.className).toContain('px-4');
        });

        it('should apply sm size', () => {
            const btn = new FlexButton(container, { size: 'sm' });
            expect(btn.buttonElement.className).toContain('px-3');
        });

        it('should apply lg size', () => {
            const btn = new FlexButton(container, { size: 'lg' });
            expect(btn.buttonElement.className).toContain('px-5');
        });
    });

    describe('States', () => {
        it('should disable button when disabled option is true', () => {
            const btn = new FlexButton(container, { disabled: true });
            expect(btn.buttonElement.disabled).toBe(true);
        });

        it('should show loading state', () => {
            const btn = new FlexButton(container, { loading: true });
            expect(btn.state.loading).toBe(true);
            const spinner = container.querySelector('.animate-spin');
            expect(spinner).toBeTruthy();
        });

        it('should render full width button', () => {
            const btn = new FlexButton(container, { fullWidth: true });
            expect(btn.buttonElement.className).toContain('w-full');
        });
    });

    describe('Click interaction', () => {
        it('should emit click event', () => {
            const cb = vi.fn();
            const btn = new FlexButton(container);
            btn.on('click', cb);
            click(btn.buttonElement);
            expect(cb).toHaveBeenCalled();
        });

        it('should call onClick callback', () => {
            const cb = vi.fn();
            const btn = new FlexButton(container, { onClick: cb });
            click(btn.buttonElement);
            expect(cb).toHaveBeenCalled();
        });

        it('should not fire click when disabled', () => {
            const cb = vi.fn();
            const btn = new FlexButton(container, { disabled: true, onClick: cb });
            click(btn.buttonElement);
            expect(cb).not.toHaveBeenCalled();
        });

        it('should not fire click when loading', () => {
            const cb = vi.fn();
            const btn = new FlexButton(container, { loading: true, onClick: cb });
            click(btn.buttonElement);
            expect(cb).not.toHaveBeenCalled();
        });
    });

    describe('API methods', () => {
        it('should set loading state with setLoading()', () => {
            const btn = new FlexButton(container);
            btn.setLoading(true);
            expect(btn.state.loading).toBe(true);
        });

        it('should set disabled state with setDisabled()', () => {
            const btn = new FlexButton(container);
            btn.setDisabled(true);
            expect(btn.state.disabled).toBe(true);
            expect(btn.buttonElement.disabled).toBe(true);
        });

        it('should update text with setText()', () => {
            const btn = new FlexButton(container);
            btn.setText('Save');
            expect(btn.buttonElement.textContent).toContain('Save');
        });
    });

    describe('Cleanup', () => {
        it('should destroy component', () => {
            const btn = new FlexButton(container);
            expect(() => btn.destroy()).not.toThrow();
        });
    });
});
