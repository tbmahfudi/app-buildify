import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import FlexTextarea from '../../frontend/assets/js/components/flex-textarea.js';
import { createTestContainer, cleanupTestContainer, blur } from '../helpers/test-utils.js';

describe('FlexTextarea', () => {
    let container;

    beforeEach(() => { container = createTestContainer(); });
    afterEach(() => { cleanupTestContainer(container); });

    describe('Initialization', () => {
        it('should create textarea element', () => {
            const ta = new FlexTextarea(container);
            const el = container.querySelector('textarea');
            expect(el).toBeTruthy();
        });

        it('should set initial value', () => {
            const ta = new FlexTextarea(container, { value: 'Hello' });
            const el = container.querySelector('textarea');
            expect(el.value).toBe('Hello');
        });

        it('should render label when provided', () => {
            const ta = new FlexTextarea(container, { label: 'Notes' });
            const label = container.querySelector('label');
            expect(label).toBeTruthy();
            expect(label.textContent).toContain('Notes');
        });

        it('should show required asterisk when required', () => {
            const ta = new FlexTextarea(container, { label: 'Notes', required: true });
            const label = container.querySelector('label');
            expect(label.textContent).toContain('*');
        });
    });

    describe('Rendering', () => {
        it('should set rows attribute', () => {
            const ta = new FlexTextarea(container, { rows: 5 });
            const el = container.querySelector('textarea');
            expect(el.rows).toBe(5);
        });

        it('should set placeholder', () => {
            const ta = new FlexTextarea(container, { placeholder: 'Enter text' });
            const el = container.querySelector('textarea');
            expect(el.placeholder).toBe('Enter text');
        });

        it('should disable textarea', () => {
            const ta = new FlexTextarea(container, { disabled: true });
            const el = container.querySelector('textarea');
            expect(el.disabled).toBe(true);
        });

        it('should set readonly textarea', () => {
            const ta = new FlexTextarea(container, { readonly: true });
            const el = container.querySelector('textarea');
            expect(el.readOnly).toBe(true);
        });

        it('should render character counter when showCharCount is true', () => {
            const ta = new FlexTextarea(container, { showCharCount: true, maxLength: 100 });
            expect(container.textContent).toContain('100');
        });
    });

    describe('Variants', () => {
        it('should apply outlined variant by default', () => {
            const ta = new FlexTextarea(container);
            const el = container.querySelector('textarea');
            expect(el.className).toContain('border');
        });
    });

    describe('API methods', () => {
        it('should get value with getValue()', () => {
            const ta = new FlexTextarea(container, { value: 'test' });
            expect(ta.getValue()).toBe('test');
        });

        it('should set value with setValue()', () => {
            const ta = new FlexTextarea(container);
            ta.setValue('new value');
            expect(ta.getValue()).toBe('new value');
        });

        it('should set disabled state with setDisabled()', () => {
            const ta = new FlexTextarea(container);
            ta.setDisabled(true);
            const el = container.querySelector('textarea');
            expect(el.disabled).toBe(true);
        });
    });

    describe('Validation', () => {
        it('should validate required field on blur', () => {
            const ta = new FlexTextarea(container, { required: true, validateOn: 'blur' });
            const el = container.querySelector('textarea');
            blur(el);
            const isValid = ta.validate();
            expect(isValid).toBe(false);
        });

        it('should pass validation when value is set', () => {
            const ta = new FlexTextarea(container, { required: true });
            ta.setValue('some text');
            const isValid = ta.validate();
            expect(isValid).toBe(true);
        });
    });

    describe('Cleanup', () => {
        it('should destroy component', () => {
            const ta = new FlexTextarea(container);
            expect(() => ta.destroy()).not.toThrow();
        });
    });
});
