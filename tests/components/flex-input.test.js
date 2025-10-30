/**
 * FlexInput Component Tests
 *
 * Tests for the universal input field component
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import FlexInput from '../../frontend/assets/js/components/flex-input.js';
import {
    createTestContainer,
    cleanupTestContainer,
    input,
    focus,
    blur,
    wait
} from '../helpers/test-utils.js';

describe('FlexInput', () => {
    let container;

    beforeEach(() => {
        container = createTestContainer();
    });

    afterEach(() => {
        cleanupTestContainer(container);
    });

    describe('Initialization', () => {
        it('should create input with default options', () => {
            const flexInput = new FlexInput(container);

            expect(flexInput.element).toBe(container);
            expect(flexInput.state.value).toBe('');
            expect(flexInput.state.valid).toBe(true);
            expect(flexInput.state.touched).toBe(false);
        });

        it('should create input with initial value', () => {
            const flexInput = new FlexInput(container, { value: 'test value' });

            expect(flexInput.state.value).toBe('test value');
            expect(flexInput.inputElement.value).toBe('test value');
        });

        it('should create input with label', () => {
            const flexInput = new FlexInput(container, { label: 'Email Address' });

            const label = container.querySelector('.flex-input-label');
            expect(label).toBeTruthy();
            expect(label.textContent).toContain('Email Address');
        });

        it('should show required asterisk when required', () => {
            const flexInput = new FlexInput(container, {
                label: 'Email',
                required: true
            });

            const label = container.querySelector('.flex-input-label');
            expect(label.textContent).toContain('*');
        });

        it('should emit init event', () => {
            const callback = vi.fn();
            const flexInput = new FlexInput(container);

            flexInput.on('init', callback);
            flexInput.init();

            expect(callback).toHaveBeenCalled();
        });
    });

    describe('Rendering', () => {
        it('should render input element', () => {
            const flexInput = new FlexInput(container);

            const input = container.querySelector('input.flex-input');
            expect(input).toBeTruthy();
            expect(input.type).toBe('text');
        });

        it('should apply size classes', () => {
            const flexInput = new FlexInput(container, { size: 'lg' });

            const input = container.querySelector('input.flex-input');
            expect(input.classList.contains('px-4')).toBe(true);
            expect(input.classList.contains('py-3')).toBe(true);
        });

        it('should apply outlined variant styles', () => {
            const flexInput = new FlexInput(container, { variant: 'outlined' });

            const input = container.querySelector('input.flex-input');
            expect(input.classList.contains('border-gray-300')).toBe(true);
            expect(input.classList.contains('bg-white')).toBe(true);
        });

        it('should apply filled variant styles', () => {
            const flexInput = new FlexInput(container, { variant: 'filled' });

            const input = container.querySelector('input.flex-input');
            expect(input.classList.contains('bg-gray-100')).toBe(true);
        });

        it('should apply underlined variant styles', () => {
            const flexInput = new FlexInput(container, { variant: 'underlined' });

            const input = container.querySelector('input.flex-input');
            expect(input.classList.contains('border-b-2')).toBe(true);
            expect(input.classList.contains('rounded-none')).toBe(true);
        });

        it('should apply disabled styles', () => {
            const flexInput = new FlexInput(container, { disabled: true });

            const input = container.querySelector('input.flex-input');
            expect(input.disabled).toBe(true);
            expect(input.classList.contains('bg-gray-50')).toBe(true);
        });

        it('should render helper text', () => {
            const flexInput = new FlexInput(container, {
                helperText: 'Enter your email address'
            });

            const message = container.querySelector('.flex-input-message');
            expect(message).toBeTruthy();
            expect(message.textContent).toBe('Enter your email address');
        });

        it('should render prefix icon', () => {
            const flexInput = new FlexInput(container, {
                prefixIcon: 'ph ph-envelope'
            });

            const icon = container.querySelector('.ph-envelope');
            expect(icon).toBeTruthy();
        });

        it('should render suffix icon', () => {
            const flexInput = new FlexInput(container, {
                suffixIcon: 'ph ph-check'
            });

            const icon = container.querySelector('.ph-check');
            expect(icon).toBeTruthy();
        });

        it('should render clear button when clearable and has value', () => {
            const flexInput = new FlexInput(container, {
                value: 'test',
                clearable: true
            });

            const clearBtn = container.querySelector('button[aria-label="Clear input"]');
            expect(clearBtn).toBeTruthy();
        });

        it('should not render clear button when no value', () => {
            const flexInput = new FlexInput(container, {
                clearable: true
            });

            const clearBtn = container.querySelector('button[aria-label="Clear input"]');
            expect(clearBtn).toBeNull();
        });

        it('should render password toggle button', () => {
            const flexInput = new FlexInput(container, {
                type: 'password',
                showPasswordToggle: true
            });

            const toggleBtn = container.querySelector('button[aria-label="Show password"]');
            expect(toggleBtn).toBeTruthy();
        });

        it('should render character counter', () => {
            const flexInput = new FlexInput(container, {
                value: 'test',
                maxLength: 100,
                showCharCount: true
            });

            const counter = container.querySelector('#char-counter');
            expect(counter).toBeTruthy();
            expect(counter.textContent).toBe('4/100');
        });
    });

    describe('Label Positions', () => {
        it('should render label on top by default', () => {
            const flexInput = new FlexInput(container, { label: 'Email' });

            const wrapper = container.querySelector('.flex-input-wrapper');
            expect(wrapper.classList.contains('space-y-1.5')).toBe(true);
        });

        it('should render inline label', () => {
            const flexInput = new FlexInput(container, {
                label: 'Email',
                labelPosition: 'inline'
            });

            const wrapper = container.querySelector('.flex-input-wrapper');
            expect(wrapper.classList.contains('flex')).toBe(true);
            expect(wrapper.classList.contains('items-center')).toBe(true);
        });

        it('should render floating label', () => {
            const flexInput = new FlexInput(container, {
                label: 'Email',
                labelPosition: 'floating'
            });

            const label = container.querySelector('.flex-input-label');
            expect(label.classList.contains('absolute')).toBe(true);
            expect(label.classList.contains('transition-all')).toBe(true);
        });

        it('should move floating label up when focused', async () => {
            const flexInput = new FlexInput(container, {
                label: 'Email',
                labelPosition: 'floating'
            });

            focus(flexInput.inputElement);
            await wait(50);

            const label = container.querySelector('.flex-input-label');
            expect(label.classList.contains('-top-2')).toBe(true);
            expect(label.classList.contains('text-xs')).toBe(true);
        });

        it('should move floating label up when has value', () => {
            const flexInput = new FlexInput(container, {
                label: 'Email',
                labelPosition: 'floating',
                value: 'test@example.com'
            });

            const label = container.querySelector('.flex-input-label');
            expect(label.classList.contains('-top-2')).toBe(true);
        });
    });

    describe('User Interaction', () => {
        it('should update value on input', async () => {
            const flexInput = new FlexInput(container);

            input(flexInput.inputElement, 'test value');
            await wait(50);

            expect(flexInput.state.value).toBe('test value');
        });

        it('should emit input event', async () => {
            const callback = vi.fn();
            const flexInput = new FlexInput(container);

            flexInput.on('input', callback);
            input(flexInput.inputElement, 'test');
            await wait(50);

            expect(callback).toHaveBeenCalledWith(
                expect.objectContaining({ value: 'test' })
            );
        });

        it('should call onInput callback', async () => {
            const onInput = vi.fn();
            const flexInput = new FlexInput(container, { onInput });

            input(flexInput.inputElement, 'test');
            await wait(50);

            expect(onInput).toHaveBeenCalledWith('test', expect.any(Event));
        });

        it('should emit change event', async () => {
            const callback = vi.fn();
            const flexInput = new FlexInput(container);

            flexInput.on('change', callback);

            // Simulate change event directly
            flexInput.inputElement.value = 'test';
            flexInput.inputElement.dispatchEvent(new Event('change', { bubbles: true }));
            await wait(50);

            expect(callback).toHaveBeenCalled();
        });

        it('should call onChange callback', async () => {
            const onChange = vi.fn();
            const flexInput = new FlexInput(container, { onChange });

            flexInput.inputElement.value = 'test';
            flexInput.inputElement.dispatchEvent(new Event('change', { bubbles: true }));
            await wait(50);

            expect(onChange).toHaveBeenCalled();
        });

        it('should set focused state on focus', async () => {
            const flexInput = new FlexInput(container);

            focus(flexInput.inputElement);
            await wait(50);

            expect(flexInput.state.focused).toBe(true);
        });

        it('should call onFocus callback', async () => {
            const onFocus = vi.fn();
            const flexInput = new FlexInput(container, { onFocus });

            focus(flexInput.inputElement);
            await wait(50);

            expect(onFocus).toHaveBeenCalled();
        });

        it('should set touched state on blur', async () => {
            const flexInput = new FlexInput(container);

            focus(flexInput.inputElement);
            blur(flexInput.inputElement);
            await wait(50);

            expect(flexInput.state.touched).toBe(true);
            expect(flexInput.state.focused).toBe(false);
        });

        it('should call onBlur callback', async () => {
            const onBlur = vi.fn();
            const flexInput = new FlexInput(container, { onBlur });

            focus(flexInput.inputElement);
            blur(flexInput.inputElement);
            await wait(50);

            expect(onBlur).toHaveBeenCalled();
        });

        it('should update character counter on input', async () => {
            const flexInput = new FlexInput(container, {
                maxLength: 100,
                showCharCount: true
            });

            input(flexInput.inputElement, 'test');
            await wait(50);

            const counter = container.querySelector('#char-counter');
            expect(counter.textContent).toBe('4/100');
        });
    });

    describe('Clear Functionality', () => {
        it('should clear value when clear button clicked', async () => {
            const flexInput = new FlexInput(container, {
                value: 'test',
                clearable: true
            });

            const clearBtn = container.querySelector('button[aria-label="Clear input"]');
            clearBtn.click();
            await wait(50);

            expect(flexInput.state.value).toBe('');
        });

        it('should emit clear event', () => {
            const callback = vi.fn();
            const flexInput = new FlexInput(container, { value: 'test' });

            flexInput.on('clear', callback);
            flexInput.clear();

            expect(callback).toHaveBeenCalled();
        });

        it('should call onClear callback', () => {
            const onClear = vi.fn();
            const flexInput = new FlexInput(container, {
                value: 'test',
                onClear
            });

            flexInput.clear();

            expect(onClear).toHaveBeenCalled();
        });

        it('should focus input after clear', () => {
            const flexInput = new FlexInput(container, { value: 'test' });
            const focusSpy = vi.spyOn(flexInput.inputElement, 'focus');

            flexInput.clear();

            expect(focusSpy).toHaveBeenCalled();
        });
    });

    describe('Password Toggle', () => {
        it('should toggle password visibility', () => {
            const flexInput = new FlexInput(container, {
                type: 'password',
                value: 'secret123',
                showPasswordToggle: true
            });

            expect(flexInput.inputElement.type).toBe('password');

            flexInput.togglePasswordVisibility();

            expect(flexInput.state.showPassword).toBe(true);
            expect(flexInput.inputElement.type).toBe('text');

            flexInput.togglePasswordVisibility();

            expect(flexInput.state.showPassword).toBe(false);
            expect(flexInput.inputElement.type).toBe('password');
        });

        it('should focus input after toggle', () => {
            const flexInput = new FlexInput(container, {
                type: 'password',
                showPasswordToggle: true
            });
            const focusSpy = vi.spyOn(flexInput.inputElement, 'focus');

            flexInput.togglePasswordVisibility();

            expect(focusSpy).toHaveBeenCalled();
        });
    });

    describe('Validation', () => {
        it('should validate required field', async () => {
            const flexInput = new FlexInput(container, {
                required: true,
                validateOn: 'blur'
            });

            focus(flexInput.inputElement);
            blur(flexInput.inputElement);
            await wait(50);

            expect(flexInput.state.valid).toBe(false);
            expect(flexInput.state.error).toBeTruthy();
        });

        it('should pass required validation with value', async () => {
            const flexInput = new FlexInput(container, {
                required: true,
                value: 'test',
                validateOn: 'blur'
            });

            focus(flexInput.inputElement);
            blur(flexInput.inputElement);
            await wait(50);

            expect(flexInput.state.valid).toBe(true);
        });

        it('should validate on blur when validateOn is blur', async () => {
            const flexInput = new FlexInput(container, {
                required: true,
                validateOn: 'blur'
            });

            focus(flexInput.inputElement);
            blur(flexInput.inputElement);
            await wait(50);

            expect(flexInput.state.valid).toBe(false);
        });

        it('should validate on change when validateOn is change', async () => {
            const flexInput = new FlexInput(container, {
                required: true,
                validateOn: 'change'
            });

            input(flexInput.inputElement, '');
            await wait(50);

            expect(flexInput.state.valid).toBe(false);
        });

        it('should use custom validator returning boolean', async () => {
            const validator = (value) => value.length >= 5;
            const flexInput = new FlexInput(container, {
                validator,
                validateOn: 'blur'
            });

            input(flexInput.inputElement, 'abc');
            focus(flexInput.inputElement);
            blur(flexInput.inputElement);
            await wait(50);

            expect(flexInput.state.valid).toBe(false);

            input(flexInput.inputElement, 'abcde');
            focus(flexInput.inputElement);
            blur(flexInput.inputElement);
            await wait(50);

            expect(flexInput.state.valid).toBe(true);
        });

        it('should use custom validator returning string error', async () => {
            const validator = (value) => {
                return value.length >= 5 ? true : 'Must be at least 5 characters';
            };
            const flexInput = new FlexInput(container, {
                validator,
                validateOn: 'blur'
            });

            input(flexInput.inputElement, 'abc');
            focus(flexInput.inputElement);
            blur(flexInput.inputElement);
            await wait(50);

            expect(flexInput.state.valid).toBe(false);
            expect(flexInput.state.error).toBe('Must be at least 5 characters');
        });

        it('should use custom validator returning object', async () => {
            const validator = (value) => ({
                valid: value.length >= 5,
                message: 'Must be at least 5 characters'
            });
            const flexInput = new FlexInput(container, {
                validator,
                validateOn: 'blur'
            });

            input(flexInput.inputElement, 'abc');
            focus(flexInput.inputElement);
            blur(flexInput.inputElement);
            await wait(50);

            expect(flexInput.state.valid).toBe(false);
            expect(flexInput.state.error).toBe('Must be at least 5 characters');
        });

        it('should show error message when invalid', async () => {
            const flexInput = new FlexInput(container, {
                required: true,
                errorMessage: 'This field is required',
                validateOn: 'blur'
            });

            focus(flexInput.inputElement);
            blur(flexInput.inputElement);
            await wait(50);

            const message = container.querySelector('.flex-input-message');
            expect(message).toBeTruthy();
            expect(message.textContent).toBe('This field is required');
            expect(message.classList.contains('text-red-600')).toBe(true);
        });

        it('should show success message when valid and touched', async () => {
            const flexInput = new FlexInput(container, {
                value: 'test',
                successMessage: 'Looks good!',
                validateOn: 'blur'
            });

            focus(flexInput.inputElement);
            blur(flexInput.inputElement);
            await wait(50);

            const message = container.querySelector('.flex-input-message');
            expect(message).toBeTruthy();
            expect(message.textContent).toBe('Looks good!');
            expect(message.classList.contains('text-green-600')).toBe(true);
        });

        it('should emit validate event', async () => {
            const callback = vi.fn();
            const flexInput = new FlexInput(container, { required: true });

            flexInput.on('validate', callback);
            flexInput.validate();

            expect(callback).toHaveBeenCalledWith(
                expect.objectContaining({
                    valid: expect.any(Boolean),
                    error: expect.anything()
                })
            );
        });

        it('should set ARIA attributes when invalid', async () => {
            const flexInput = new FlexInput(container, {
                required: true,
                validateOn: 'blur'
            });

            focus(flexInput.inputElement);
            blur(flexInput.inputElement);
            await wait(50);

            expect(flexInput.inputElement.getAttribute('aria-invalid')).toBe('true');
            expect(flexInput.inputElement.getAttribute('aria-describedby')).toBe('input-error');
        });
    });

    describe('API Methods', () => {
        it('should get value with getValue()', () => {
            const flexInput = new FlexInput(container, { value: 'test' });

            expect(flexInput.getValue()).toBe('test');
        });

        it('should set value with setValue()', () => {
            const flexInput = new FlexInput(container);

            flexInput.setValue('new value');

            expect(flexInput.state.value).toBe('new value');
            expect(flexInput.inputElement.value).toBe('new value');
        });

        it('should focus input with focus()', () => {
            const flexInput = new FlexInput(container);
            const focusSpy = vi.spyOn(flexInput.inputElement, 'focus');

            flexInput.focus();

            expect(focusSpy).toHaveBeenCalled();
        });

        it('should blur input with blur()', () => {
            const flexInput = new FlexInput(container);
            const blurSpy = vi.spyOn(flexInput.inputElement, 'blur');

            flexInput.blur();

            expect(blurSpy).toHaveBeenCalled();
        });

        it('should set disabled state with setDisabled()', () => {
            const flexInput = new FlexInput(container);

            flexInput.setDisabled(true);

            expect(flexInput.options.disabled).toBe(true);
            expect(flexInput.inputElement.disabled).toBe(true);
        });

        it('should set error with setError()', () => {
            const flexInput = new FlexInput(container);

            flexInput.setError('Custom error message');

            expect(flexInput.state.valid).toBe(false);
            expect(flexInput.state.error).toBe('Custom error message');
            expect(flexInput.state.touched).toBe(true);
        });

        it('should clear error with clearError()', () => {
            const flexInput = new FlexInput(container);

            flexInput.setError('Error');
            flexInput.clearError();

            expect(flexInput.state.valid).toBe(true);
            expect(flexInput.state.error).toBeNull();
        });

        it('should return input element with getInputElement()', () => {
            const flexInput = new FlexInput(container);

            const element = flexInput.getInputElement();

            expect(element).toBe(flexInput.inputElement);
            expect(element.tagName).toBe('INPUT');
        });
    });

    describe('Input Types', () => {
        it('should create email input', () => {
            const flexInput = new FlexInput(container, { type: 'email' });

            expect(flexInput.inputElement.type).toBe('email');
        });

        it('should create password input', () => {
            const flexInput = new FlexInput(container, { type: 'password' });

            expect(flexInput.inputElement.type).toBe('password');
        });

        it('should create number input', () => {
            const flexInput = new FlexInput(container, { type: 'number' });

            expect(flexInput.inputElement.type).toBe('number');
        });

        it('should create tel input', () => {
            const flexInput = new FlexInput(container, { type: 'tel' });

            expect(flexInput.inputElement.type).toBe('tel');
        });

        it('should create url input', () => {
            const flexInput = new FlexInput(container, { type: 'url' });

            expect(flexInput.inputElement.type).toBe('url');
        });

        it('should create search input', () => {
            const flexInput = new FlexInput(container, { type: 'search' });

            expect(flexInput.inputElement.type).toBe('search');
        });
    });

    describe('Attributes', () => {
        it('should set placeholder', () => {
            const flexInput = new FlexInput(container, {
                placeholder: 'Enter your email'
            });

            expect(flexInput.inputElement.placeholder).toBe('Enter your email');
        });

        it('should set required', () => {
            const flexInput = new FlexInput(container, { required: true });

            expect(flexInput.inputElement.required).toBe(true);
        });

        it('should set disabled', () => {
            const flexInput = new FlexInput(container, { disabled: true });

            expect(flexInput.inputElement.disabled).toBe(true);
        });

        it('should set readonly', () => {
            const flexInput = new FlexInput(container, { readonly: true });

            expect(flexInput.inputElement.readOnly).toBe(true);
        });

        it('should set maxLength', () => {
            const flexInput = new FlexInput(container, { maxLength: 50 });

            expect(flexInput.inputElement.maxLength).toBe(50);
        });

        it('should set pattern', () => {
            const flexInput = new FlexInput(container, { pattern: '[0-9]*' });

            expect(flexInput.inputElement.pattern).toBe('[0-9]*');
        });

        it('should set min for number input', () => {
            const flexInput = new FlexInput(container, {
                type: 'number',
                min: 0
            });

            expect(flexInput.inputElement.min).toBe('0');
        });

        it('should set max for number input', () => {
            const flexInput = new FlexInput(container, {
                type: 'number',
                max: 100
            });

            expect(flexInput.inputElement.max).toBe('100');
        });

        it('should set step for number input', () => {
            const flexInput = new FlexInput(container, {
                type: 'number',
                step: 0.5
            });

            expect(flexInput.inputElement.step).toBe('0.5');
        });

        it('should set autocomplete', () => {
            const flexInput = new FlexInput(container, { autoComplete: 'email' });

            expect(flexInput.inputElement.autocomplete).toBe('email');
        });
    });

    describe('Cleanup', () => {
        it('should destroy component', () => {
            const flexInput = new FlexInput(container);

            // Destroy should clear the component
            flexInput.destroy();

            expect(flexInput.state.destroyed).toBe(true);
            expect(flexInput.events.size).toBe(0);
        });
    });
});
