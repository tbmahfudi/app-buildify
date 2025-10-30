/**
 * FlexCheckbox Component Tests
 *
 * Tests for the checkbox component with indeterminate state
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import FlexCheckbox from '../../frontend/assets/js/components/flex-checkbox.js';
import {
    createTestContainer,
    cleanupTestContainer,
    click,
    wait
} from '../helpers/test-utils.js';

describe('FlexCheckbox', () => {
    let container;

    beforeEach(() => {
        container = createTestContainer();
    });

    afterEach(() => {
        cleanupTestContainer(container);
    });

    describe('Initialization', () => {
        it('should create checkbox with default options', () => {
            const checkbox = new FlexCheckbox(container);

            expect(checkbox.element).toBe(container);
            expect(checkbox.state.checked).toBe(false);
            expect(checkbox.state.indeterminate).toBe(false);
        });

        it('should create checkbox with checked state', () => {
            const checkbox = new FlexCheckbox(container, { checked: true });

            expect(checkbox.state.checked).toBe(true);
            expect(checkbox.checkboxElement.checked).toBe(true);
        });

        it('should create checkbox with indeterminate state', () => {
            const checkbox = new FlexCheckbox(container, { indeterminate: true });

            expect(checkbox.state.indeterminate).toBe(true);
            expect(checkbox.checkboxElement.indeterminate).toBe(true);
        });

        it('should create checkbox with label', () => {
            const checkbox = new FlexCheckbox(container, { label: 'Accept terms' });

            const label = container.querySelector('.flex-checkbox-label');
            expect(label).toBeTruthy();
            expect(label.textContent).toContain('Accept terms');
        });

        it('should create checkbox with description', () => {
            const checkbox = new FlexCheckbox(container, {
                label: 'Accept terms',
                description: 'You must accept the terms to continue'
            });

            const description = container.querySelector('.flex-checkbox-description');
            expect(description).toBeTruthy();
            expect(description.textContent).toBe('You must accept the terms to continue');
        });

        it('should show required asterisk when required', () => {
            const checkbox = new FlexCheckbox(container, {
                label: 'Accept terms',
                required: true
            });

            const label = container.querySelector('.flex-checkbox-label');
            expect(label.textContent).toContain('*');
        });

        it('should emit init event', () => {
            const callback = vi.fn();
            const checkbox = new FlexCheckbox(container);

            checkbox.on('init', callback);
            checkbox.init();

            expect(callback).toHaveBeenCalled();
        });
    });

    describe('Rendering', () => {
        it('should render checkbox input element', () => {
            const checkbox = new FlexCheckbox(container);

            const input = container.querySelector('input[type="checkbox"]');
            expect(input).toBeTruthy();
            expect(input.classList.contains('peer')).toBe(true);
            expect(input.classList.contains('sr-only')).toBe(true);
        });

        it('should render visual checkmark element', () => {
            const checkbox = new FlexCheckbox(container);

            const checkmark = container.querySelector('.flex-checkbox-checkmark');
            expect(checkmark).toBeTruthy();
        });

        it('should apply size classes', () => {
            const checkbox = new FlexCheckbox(container, { size: 'lg' });

            const checkmark = container.querySelector('.flex-checkbox-checkmark');
            expect(checkmark.classList.contains('w-6')).toBe(true);
            expect(checkmark.classList.contains('h-6')).toBe(true);
        });

        it('should apply color classes', () => {
            const checkbox = new FlexCheckbox(container, { color: 'blue' });

            const checkmark = container.querySelector('.flex-checkbox-checkmark');
            expect(checkmark.className).toContain('peer-checked:bg-blue-600');
        });

        it('should apply disabled styles', () => {
            const checkbox = new FlexCheckbox(container, { disabled: true });

            const wrapper = container.querySelector('.flex-checkbox-wrapper');
            expect(wrapper.classList.contains('opacity-50')).toBe(true);
            expect(wrapper.classList.contains('cursor-not-allowed')).toBe(true);
        });

        it('should position label on left when labelPosition is left', () => {
            const checkbox = new FlexCheckbox(container, {
                label: 'Test',
                labelPosition: 'left'
            });

            const wrapper = container.querySelector('.flex-checkbox-wrapper');
            const labelWrapper = wrapper.querySelector('.flex-checkbox-label-wrapper');
            const inputWrapper = wrapper.querySelector('.flex-checkbox-input-wrapper');

            expect(wrapper.children[0]).toBe(labelWrapper);
            expect(wrapper.children[1]).toBe(inputWrapper);
        });

        it('should position label on right by default', () => {
            const checkbox = new FlexCheckbox(container, {
                label: 'Test'
            });

            const wrapper = container.querySelector('.flex-checkbox-wrapper');
            const labelWrapper = wrapper.querySelector('.flex-checkbox-label-wrapper');
            const inputWrapper = wrapper.querySelector('.flex-checkbox-input-wrapper');

            expect(wrapper.children[0]).toBe(inputWrapper);
            expect(wrapper.children[1]).toBe(labelWrapper);
        });
    });

    describe('User Interaction', () => {
        it('should toggle checked state on click', async () => {
            const checkbox = new FlexCheckbox(container);
            const input = checkbox.checkboxElement;

            click(input);
            await wait(50);

            expect(checkbox.state.checked).toBe(true);

            click(input);
            await wait(50);

            expect(checkbox.state.checked).toBe(false);
        });

        it('should emit change event on state change', async () => {
            const callback = vi.fn();
            const checkbox = new FlexCheckbox(container);

            checkbox.on('change', callback);
            const input = checkbox.checkboxElement;

            click(input);
            await wait(50);

            expect(callback).toHaveBeenCalledWith(
                expect.objectContaining({
                    checked: true,
                    value: 'on'
                })
            );
        });

        it('should call onChange callback', async () => {
            const onChange = vi.fn();
            const checkbox = new FlexCheckbox(container, { onChange });
            const input = checkbox.checkboxElement;

            click(input);
            await wait(50);

            expect(onChange).toHaveBeenCalledWith(true, expect.any(Event));
        });

        it('should call onCheck callback when checked', async () => {
            const onCheck = vi.fn();
            const checkbox = new FlexCheckbox(container, { onCheck });
            const input = checkbox.checkboxElement;

            click(input);
            await wait(50);

            expect(onCheck).toHaveBeenCalled();
        });

        it('should call onUncheck callback when unchecked', async () => {
            const onUncheck = vi.fn();
            const checkbox = new FlexCheckbox(container, { checked: true, onUncheck });
            const input = checkbox.checkboxElement;

            click(input);
            await wait(50);

            expect(onUncheck).toHaveBeenCalled();
        });

        it('should not respond to clicks when disabled', () => {
            const onChange = vi.fn();
            const checkbox = new FlexCheckbox(container, { disabled: true, onChange });
            const input = checkbox.checkboxElement;

            expect(input.disabled).toBe(true);
        });

        it('should clear indeterminate state when clicked', async () => {
            const checkbox = new FlexCheckbox(container, { indeterminate: true });
            const input = checkbox.checkboxElement;

            expect(checkbox.state.indeterminate).toBe(true);

            click(input);
            await wait(50);

            expect(checkbox.state.indeterminate).toBe(false);
        });
    });

    describe('API Methods', () => {
        it('should check with check()', () => {
            const checkbox = new FlexCheckbox(container);

            checkbox.check();

            expect(checkbox.state.checked).toBe(true);
            expect(checkbox.checkboxElement.checked).toBe(true);
        });

        it('should uncheck with uncheck()', () => {
            const checkbox = new FlexCheckbox(container, { checked: true });

            checkbox.uncheck();

            expect(checkbox.state.checked).toBe(false);
            expect(checkbox.checkboxElement.checked).toBe(false);
        });

        it('should toggle with toggle()', () => {
            const checkbox = new FlexCheckbox(container);

            checkbox.toggle();
            expect(checkbox.state.checked).toBe(true);

            checkbox.toggle();
            expect(checkbox.state.checked).toBe(false);
        });

        it('should set indeterminate with setIndeterminate()', () => {
            const checkbox = new FlexCheckbox(container);

            checkbox.setIndeterminate(true);

            expect(checkbox.state.indeterminate).toBe(true);
            expect(checkbox.checkboxElement.indeterminate).toBe(true);
        });

        it('should clear indeterminate when checking', () => {
            const checkbox = new FlexCheckbox(container, { indeterminate: true });

            checkbox.check();

            expect(checkbox.state.indeterminate).toBe(false);
            expect(checkbox.checkboxElement.indeterminate).toBe(false);
        });

        it('should return checked state with isChecked()', () => {
            const checkbox = new FlexCheckbox(container);

            expect(checkbox.isChecked()).toBe(false);

            checkbox.check();
            expect(checkbox.isChecked()).toBe(true);
        });

        it('should return indeterminate state with isIndeterminate()', () => {
            const checkbox = new FlexCheckbox(container);

            expect(checkbox.isIndeterminate()).toBe(false);

            checkbox.setIndeterminate(true);
            expect(checkbox.isIndeterminate()).toBe(true);
        });

        it('should set checked state with setChecked()', () => {
            const checkbox = new FlexCheckbox(container);

            checkbox.setChecked(true);
            expect(checkbox.isChecked()).toBe(true);

            checkbox.setChecked(false);
            expect(checkbox.isChecked()).toBe(false);
        });

        it('should update disabled state with setDisabled()', () => {
            const checkbox = new FlexCheckbox(container);

            checkbox.setDisabled(true);

            const input = checkbox.checkboxElement;
            expect(input.disabled).toBe(true);
        });

        it('should return checkbox element with getCheckboxElement()', () => {
            const checkbox = new FlexCheckbox(container);

            const element = checkbox.getCheckboxElement();

            expect(element).toBe(checkbox.checkboxElement);
            expect(element.type).toBe('checkbox');
        });
    });

    describe('Events', () => {
        it('should emit check event', () => {
            const callback = vi.fn();
            const checkbox = new FlexCheckbox(container);

            checkbox.on('check', callback);
            checkbox.check();

            expect(callback).toHaveBeenCalled();
        });

        it('should emit uncheck event', () => {
            const callback = vi.fn();
            const checkbox = new FlexCheckbox(container, { checked: true });

            checkbox.on('uncheck', callback);
            checkbox.uncheck();

            expect(callback).toHaveBeenCalled();
        });

        it('should emit indeterminate event', () => {
            const callback = vi.fn();
            const checkbox = new FlexCheckbox(container);

            checkbox.on('indeterminate', callback);
            checkbox.setIndeterminate(true);

            expect(callback).toHaveBeenCalledWith(
                expect.objectContaining({ indeterminate: true })
            );
        });
    });

    describe('Attributes', () => {
        it('should set name attribute', () => {
            const checkbox = new FlexCheckbox(container, { name: 'terms' });

            const input = checkbox.checkboxElement;
            expect(input.name).toBe('terms');
        });

        it('should set value attribute', () => {
            const checkbox = new FlexCheckbox(container, { value: 'accepted' });

            const input = checkbox.checkboxElement;
            expect(input.value).toBe('accepted');
        });

        it('should set required attribute', () => {
            const checkbox = new FlexCheckbox(container, { required: true });

            const input = checkbox.checkboxElement;
            expect(input.required).toBe(true);
        });

        it('should set aria-checked to mixed when indeterminate', () => {
            const checkbox = new FlexCheckbox(container, { indeterminate: true });

            const input = checkbox.checkboxElement;
            expect(input.getAttribute('aria-checked')).toBe('mixed');
        });
    });

    describe('Cleanup', () => {
        it('should destroy component', () => {
            const checkbox = new FlexCheckbox(container);

            // Destroy should clear the component
            checkbox.destroy();

            expect(checkbox.state.destroyed).toBe(true);
            expect(checkbox.events.size).toBe(0);
        });
    });
});
