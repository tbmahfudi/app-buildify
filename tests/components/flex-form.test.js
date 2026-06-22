/**
 * FlexForm Component Tests
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import FlexForm from '../../frontend/assets/js/components/flex-form.js';
import { createTestContainer, cleanupTestContainer } from '../helpers/test-utils.js';

// Minimal mock Flex component with getValue/setValue/setError/clearError
function mockField(initialValue = '') {
    return {
        getValue: vi.fn(() => initialValue),
        setValue: vi.fn((v) => { initialValue = v; }),
        setError: vi.fn(),
        clearError: vi.fn(),
        container: document.createElement('div'),
    };
}

describe('FlexForm', () => {
    let container;

    beforeEach(() => { container = createTestContainer(); });
    afterEach(() => { cleanupTestContainer(container); });

    describe('Initialization', () => {
        it('renders form element', () => {
            new FlexForm(container);
            expect(container.querySelector('form')).toBeTruthy();
        });

        it('renders submit button with default label', () => {
            new FlexForm(container);
            const btn = container.querySelector('.flex-form-submit');
            expect(btn.textContent.trim()).toBe('Submit');
        });

        it('renders reset button when resetLabel is provided', () => {
            new FlexForm(container, { resetLabel: 'Cancel' });
            const btn = container.querySelector('.flex-form-reset');
            expect(btn).toBeTruthy();
            expect(btn.textContent.trim()).toBe('Cancel');
        });

        it('renders error summary container hidden by default', () => {
            new FlexForm(container);
            expect(container.querySelector('.flex-form-errors').classList.contains('hidden')).toBe(true);
        });
    });

    describe('Field registration', () => {
        it('register() stores field and getData returns its value', () => {
            const form = new FlexForm(container);
            const field = mockField('hello');
            form.register('username', field, {});
            expect(form.getData().username).toBe('hello');
        });

        it('register() with container appends it to fields area', () => {
            const form = new FlexForm(container);
            const field = mockField();
            const wrapper = document.createElement('div');
            wrapper.className = 'field-wrapper';
            form.register('email', field, {}, wrapper);
            expect(container.querySelector('.field-wrapper')).toBeTruthy();
        });

        it('unregister() removes field from data and DOM', () => {
            const form = new FlexForm(container);
            const field = mockField('test');
            const wrapper = document.createElement('div');
            form.register('name', field, {}, wrapper);
            form.unregister('name');
            expect(form.getData().name).toBeUndefined();
        });
    });

    describe('Validation', () => {
        it('validate() returns true when no rules are defined', () => {
            const form = new FlexForm(container);
            form.register('name', mockField('Alice'), {});
            expect(form.validate()).toBe(true);
        });

        it('validate() returns false when required field is empty', () => {
            const form = new FlexForm(container);
            form.register('name', mockField(''), { required: true });
            expect(form.validate()).toBe(false);
        });

        it('validate() calls setError on the field component', () => {
            const form  = new FlexForm(container);
            const field = mockField('');
            form.register('email', field, { required: true, requiredMessage: 'Email is required' });
            form.validate();
            expect(field.setError).toHaveBeenCalledWith('Email is required');
        });

        it('validate() calls clearError on valid fields', () => {
            const form  = new FlexForm(container);
            const field = mockField('alice@example.com');
            form.register('email', field, { required: true });
            form.validate();
            expect(field.clearError).toHaveBeenCalled();
        });

        it('minLength rule fires for short values', () => {
            const form = new FlexForm(container);
            form.register('pass', mockField('ab'), { minLength: 6 });
            expect(form.validate()).toBe(false);
            expect(form.state.errors.pass).toContain('6');
        });

        it('pattern rule fires for non-matching values', () => {
            const form = new FlexForm(container);
            form.register('code', mockField('abc'), { pattern: '^[0-9]+$', patternMessage: 'Numbers only' });
            expect(form.validate()).toBe(false);
            expect(form.state.errors.code).toBe('Numbers only');
        });

        it('email rule fires for invalid email', () => {
            const form = new FlexForm(container);
            form.register('email', mockField('not-an-email'), { email: true });
            expect(form.validate()).toBe(false);
        });

        it('custom rule fires and returns custom message', () => {
            const form = new FlexForm(container);
            form.register('age', mockField('15'), {
                custom: (v) => Number(v) >= 18 ? true : 'Must be 18 or older',
            });
            expect(form.validate()).toBe(false);
            expect(form.state.errors.age).toBe('Must be 18 or older');
        });

        it('shows error summary when validate fails', () => {
            const form = new FlexForm(container);
            form.register('name', mockField(''), { required: true });
            form.validate();
            expect(container.querySelector('.flex-form-errors').classList.contains('hidden')).toBe(false);
        });
    });

    describe('Submission', () => {
        it('calls onSubmit with form data on valid submit', async () => {
            const onSubmit = vi.fn().mockResolvedValue({ ok: true });
            const form = new FlexForm(container, { onSubmit });
            form.register('name', mockField('Alice'), {});
            const formEl = container.querySelector('form');
            formEl.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
            await new Promise(r => setTimeout(r, 10));
            expect(onSubmit).toHaveBeenCalledOnce();
            expect(onSubmit.mock.calls[0][0]).toEqual({ name: 'Alice' });
        });

        it('does not call onSubmit when validation fails', async () => {
            const onSubmit = vi.fn();
            const form = new FlexForm(container, { onSubmit });
            form.register('name', mockField(''), { required: true });
            container.querySelector('form').dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
            await new Promise(r => setTimeout(r, 10));
            expect(onSubmit).not.toHaveBeenCalled();
        });

        it('calls onSuccess after successful onSubmit', async () => {
            const onSuccess = vi.fn();
            const form = new FlexForm(container, {
                onSubmit: async () => ({ result: 'ok' }),
                onSuccess,
            });
            form.register('x', mockField('val'), {});
            container.querySelector('form').dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
            await new Promise(r => setTimeout(r, 20));
            expect(onSuccess).toHaveBeenCalledWith(expect.objectContaining({ result: { result: 'ok' } }));
        });

        it('calls onError after failed onSubmit', async () => {
            const onError = vi.fn();
            const form = new FlexForm(container, {
                onSubmit: async () => { throw new Error('server error'); },
                onError,
            });
            form.register('x', mockField('val'), {});
            container.querySelector('form').dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
            await new Promise(r => setTimeout(r, 20));
            expect(onError).toHaveBeenCalled();
        });
    });

    describe('Reset', () => {
        it('reset() clears errors and calls onReset', () => {
            const onReset = vi.fn();
            const form = new FlexForm(container, { onReset, resetLabel: 'Reset' });
            form.register('name', mockField(''), { required: true });
            form.validate();
            form.reset();
            expect(container.querySelector('.flex-form-errors').classList.contains('hidden')).toBe(true);
            expect(onReset).toHaveBeenCalled();
        });
    });

    describe('Public API', () => {
        it('setError marks specific field error', () => {
            const form  = new FlexForm(container);
            const field = mockField('bad');
            form.register('email', field, {});
            form.setError('email', 'Email already taken');
            expect(field.setError).toHaveBeenCalledWith('Email already taken');
            expect(container.querySelector('.flex-form-errors').classList.contains('hidden')).toBe(false);
        });

        it('setFieldErrors sets multiple field errors at once', () => {
            const form   = new FlexForm(container);
            const field1 = mockField('');
            const field2 = mockField('');
            form.register('name', field1, {});
            form.register('email', field2, {});
            form.setFieldErrors({ name: 'Too short', email: 'Invalid' });
            expect(field1.setError).toHaveBeenCalledWith('Too short');
            expect(field2.setError).toHaveBeenCalledWith('Invalid');
        });

        it('getData returns all registered field values', () => {
            const form = new FlexForm(container);
            form.register('first', mockField('John'), {});
            form.register('last',  mockField('Doe'),  {});
            expect(form.getData()).toEqual({ first: 'John', last: 'Doe' });
        });
    });
});
