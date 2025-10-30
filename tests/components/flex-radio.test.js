/**
 * FlexRadio Component Tests
 *
 * Tests for the radio button group component
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import FlexRadio from '../../frontend/assets/js/components/flex-radio.js';
import {
    createTestContainer,
    cleanupTestContainer,
    click,
    wait
} from '../helpers/test-utils.js';

describe('FlexRadio', () => {
    let container;

    const defaultOptions = [
        { value: 'option1', label: 'Option 1' },
        { value: 'option2', label: 'Option 2' },
        { value: 'option3', label: 'Option 3' }
    ];

    beforeEach(() => {
        container = createTestContainer();
    });

    afterEach(() => {
        cleanupTestContainer(container);
    });

    describe('Initialization', () => {
        it('should create radio group with default options', () => {
            const radio = new FlexRadio(container, {
                name: 'test-radio',
                options: defaultOptions
            });

            expect(radio.element).toBe(container);
            expect(radio.state.value).toBeNull();
            expect(radio.radioElements.length).toBe(3);
        });

        it('should create radio group with initial value', () => {
            const radio = new FlexRadio(container, {
                name: 'test-radio',
                options: defaultOptions,
                value: 'option2'
            });

            expect(radio.state.value).toBe('option2');
            expect(radio.radioElements[1].checked).toBe(true);
        });

        it('should generate name if not provided', () => {
            const radio = new FlexRadio(container, { options: defaultOptions });

            expect(radio.options.name).toBeTruthy();
            expect(radio.options.name).toMatch(/^radio-\d+$/);
        });

        it('should create radio group with label', () => {
            const radio = new FlexRadio(container, {
                name: 'test-radio',
                label: 'Choose an option',
                options: defaultOptions
            });

            const label = container.querySelector('.flex-radio-group-label');
            expect(label).toBeTruthy();
            expect(label.textContent).toContain('Choose an option');
        });

        it('should show required asterisk when required', () => {
            const radio = new FlexRadio(container, {
                name: 'test-radio',
                label: 'Choose an option',
                required: true,
                options: defaultOptions
            });

            const label = container.querySelector('.flex-radio-group-label');
            expect(label.textContent).toContain('*');
        });

        it('should emit init event', () => {
            const callback = vi.fn();
            const radio = new FlexRadio(container, {
                name: 'test-radio',
                options: defaultOptions
            });

            radio.on('init', callback);
            radio.init();

            expect(callback).toHaveBeenCalled();
        });
    });

    describe('Rendering', () => {
        it('should render all radio options', () => {
            const radio = new FlexRadio(container, {
                name: 'test-radio',
                options: defaultOptions
            });

            const items = container.querySelectorAll('.flex-radio-item');
            expect(items.length).toBe(3);
        });

        it('should render radio inputs with correct names', () => {
            const radio = new FlexRadio(container, {
                name: 'test-radio',
                options: defaultOptions
            });

            const inputs = container.querySelectorAll('input[type="radio"]');
            inputs.forEach(input => {
                expect(input.name).toBe('test-radio');
            });
        });

        it('should render radio inputs with correct values', () => {
            const radio = new FlexRadio(container, {
                name: 'test-radio',
                options: defaultOptions
            });

            const inputs = container.querySelectorAll('input[type="radio"]');
            expect(inputs[0].value).toBe('option1');
            expect(inputs[1].value).toBe('option2');
            expect(inputs[2].value).toBe('option3');
        });

        it('should render labels', () => {
            const radio = new FlexRadio(container, {
                name: 'test-radio',
                options: defaultOptions
            });

            const labels = container.querySelectorAll('.flex-radio-label');
            expect(labels[0].textContent).toBe('Option 1');
            expect(labels[1].textContent).toBe('Option 2');
            expect(labels[2].textContent).toBe('Option 3');
        });

        it('should render descriptions when provided', () => {
            const radio = new FlexRadio(container, {
                name: 'test-radio',
                options: [
                    { value: 'opt1', label: 'Option 1', description: 'Description 1' },
                    { value: 'opt2', label: 'Option 2', description: 'Description 2' }
                ]
            });

            const descriptions = container.querySelectorAll('.flex-radio-description');
            expect(descriptions.length).toBe(2);
            expect(descriptions[0].textContent).toBe('Description 1');
            expect(descriptions[1].textContent).toBe('Description 2');
        });

        it('should apply vertical layout by default', () => {
            const radio = new FlexRadio(container, {
                name: 'test-radio',
                options: defaultOptions
            });

            const group = container.querySelector('.flex-radio-group');
            expect(group.classList.contains('flex-col')).toBe(true);
        });

        it('should apply horizontal layout when specified', () => {
            const radio = new FlexRadio(container, {
                name: 'test-radio',
                direction: 'horizontal',
                options: defaultOptions
            });

            const group = container.querySelector('.flex-radio-group');
            expect(group.classList.contains('flex-row')).toBe(true);
        });

        it('should apply size classes', () => {
            const radio = new FlexRadio(container, {
                name: 'test-radio',
                size: 'lg',
                options: defaultOptions
            });

            const radioMark = container.querySelector('.flex-radio-mark');
            expect(radioMark.classList.contains('w-6')).toBe(true);
            expect(radioMark.classList.contains('h-6')).toBe(true);
        });

        it('should apply color classes', () => {
            const radio = new FlexRadio(container, {
                name: 'test-radio',
                color: 'blue',
                options: defaultOptions
            });

            const radioMark = container.querySelector('.flex-radio-mark');
            expect(radioMark.className).toContain('peer-checked:border-blue-600');
        });

        it('should apply disabled styles to disabled options', () => {
            const radio = new FlexRadio(container, {
                name: 'test-radio',
                options: [
                    { value: 'opt1', label: 'Option 1' },
                    { value: 'opt2', label: 'Option 2', disabled: true }
                ]
            });

            const items = container.querySelectorAll('.flex-radio-item');
            expect(items[0].classList.contains('opacity-50')).toBe(false);
            expect(items[1].classList.contains('opacity-50')).toBe(true);
        });

        it('should disable all options when component is disabled', () => {
            const radio = new FlexRadio(container, {
                name: 'test-radio',
                disabled: true,
                options: defaultOptions
            });

            const inputs = container.querySelectorAll('input[type="radio"]');
            inputs.forEach(input => {
                expect(input.disabled).toBe(true);
            });
        });
    });

    describe('User Interaction', () => {
        it('should select option on click', async () => {
            const radio = new FlexRadio(container, {
                name: 'test-radio',
                options: defaultOptions
            });

            const input = radio.radioElements[1];
            click(input);
            await wait(50);

            expect(radio.state.value).toBe('option2');
            expect(input.checked).toBe(true);
        });

        it('should deselect previous option when selecting new one', async () => {
            const radio = new FlexRadio(container, {
                name: 'test-radio',
                value: 'option1',
                options: defaultOptions
            });

            const input = radio.radioElements[1];
            click(input);
            await wait(50);

            expect(radio.radioElements[0].checked).toBe(false);
            expect(radio.radioElements[1].checked).toBe(true);
        });

        it('should emit change event on selection', async () => {
            const callback = vi.fn();
            const radio = new FlexRadio(container, {
                name: 'test-radio',
                options: defaultOptions
            });

            radio.on('change', callback);
            const input = radio.radioElements[1];

            click(input);
            await wait(50);

            expect(callback).toHaveBeenCalledWith(
                expect.objectContaining({
                    value: 'option2',
                    option: defaultOptions[1]
                })
            );
        });

        it('should call onChange callback', async () => {
            const onChange = vi.fn();
            const radio = new FlexRadio(container, {
                name: 'test-radio',
                onChange,
                options: defaultOptions
            });

            const input = radio.radioElements[1];
            click(input);
            await wait(50);

            expect(onChange).toHaveBeenCalledWith(
                'option2',
                defaultOptions[1],
                expect.any(Event)
            );
        });

        it('should call onSelect callback', async () => {
            const onSelect = vi.fn();
            const radio = new FlexRadio(container, {
                name: 'test-radio',
                onSelect,
                options: defaultOptions
            });

            const input = radio.radioElements[1];
            click(input);
            await wait(50);

            expect(onSelect).toHaveBeenCalledWith(
                'option2',
                defaultOptions[1],
                expect.any(Event)
            );
        });

        it('should not respond to clicks on disabled options', () => {
            const onChange = vi.fn();
            const radio = new FlexRadio(container, {
                name: 'test-radio',
                onChange,
                options: [
                    { value: 'opt1', label: 'Option 1' },
                    { value: 'opt2', label: 'Option 2', disabled: true }
                ]
            });

            const input = radio.radioElements[1];
            expect(input.disabled).toBe(true);
        });
    });

    describe('API Methods', () => {
        it('should return value with getValue()', () => {
            const radio = new FlexRadio(container, {
                name: 'test-radio',
                value: 'option2',
                options: defaultOptions
            });

            expect(radio.getValue()).toBe('option2');
        });

        it('should set value with setValue()', () => {
            const radio = new FlexRadio(container, {
                name: 'test-radio',
                options: defaultOptions
            });

            radio.setValue('option3');

            expect(radio.state.value).toBe('option3');
            expect(radio.radioElements[2].checked).toBe(true);
        });

        it('should return selected option with getSelectedOption()', () => {
            const radio = new FlexRadio(container, {
                name: 'test-radio',
                value: 'option2',
                options: defaultOptions
            });

            const selected = radio.getSelectedOption();

            expect(selected).toEqual(defaultOptions[1]);
        });

        it('should add option with addOption()', () => {
            const radio = new FlexRadio(container, {
                name: 'test-radio',
                options: defaultOptions
            });

            radio.addOption({ value: 'option4', label: 'Option 4' });

            expect(radio.options.options.length).toBe(4);
            const items = container.querySelectorAll('.flex-radio-item');
            expect(items.length).toBe(4);
        });

        it('should remove option with removeOption()', () => {
            const radio = new FlexRadio(container, {
                name: 'test-radio',
                options: defaultOptions
            });

            radio.removeOption('option2');

            expect(radio.options.options.length).toBe(2);
            const items = container.querySelectorAll('.flex-radio-item');
            expect(items.length).toBe(2);
        });

        it('should clear value when removing selected option', () => {
            const radio = new FlexRadio(container, {
                name: 'test-radio',
                value: 'option2',
                options: defaultOptions
            });

            radio.removeOption('option2');

            expect(radio.state.value).toBeNull();
        });

        it('should update option with updateOption()', () => {
            const radio = new FlexRadio(container, {
                name: 'test-radio',
                options: defaultOptions
            });

            radio.updateOption('option2', { label: 'Updated Option 2' });

            const label = container.querySelectorAll('.flex-radio-label')[1];
            expect(label.textContent).toBe('Updated Option 2');
        });

        it('should set disabled state with setDisabled()', () => {
            const radio = new FlexRadio(container, {
                name: 'test-radio',
                options: defaultOptions
            });

            radio.setDisabled(true);

            const inputs = container.querySelectorAll('input[type="radio"]');
            inputs.forEach(input => {
                expect(input.disabled).toBe(true);
            });
        });

        it('should disable specific option with disableOption()', () => {
            const radio = new FlexRadio(container, {
                name: 'test-radio',
                options: defaultOptions
            });

            radio.disableOption('option2');

            expect(radio.options.options[1].disabled).toBe(true);
            expect(radio.radioElements[1].disabled).toBe(true);
        });

        it('should enable specific option with enableOption()', () => {
            const radio = new FlexRadio(container, {
                name: 'test-radio',
                options: [
                    { value: 'opt1', label: 'Option 1' },
                    { value: 'opt2', label: 'Option 2', disabled: true }
                ]
            });

            radio.enableOption('opt2');

            expect(radio.options.options[1].disabled).toBe(false);
            expect(radio.radioElements[1].disabled).toBe(false);
        });

        it('should clear selection with clear()', () => {
            const radio = new FlexRadio(container, {
                name: 'test-radio',
                value: 'option2',
                options: defaultOptions
            });

            radio.clear();

            expect(radio.state.value).toBeNull();
            radio.radioElements.forEach(input => {
                expect(input.checked).toBe(false);
            });
        });
    });

    describe('Events', () => {
        it('should emit option:add event when adding option', () => {
            const callback = vi.fn();
            const radio = new FlexRadio(container, {
                name: 'test-radio',
                options: defaultOptions
            });

            radio.on('option:add', callback);
            const newOption = { value: 'option4', label: 'Option 4' };
            radio.addOption(newOption);

            expect(callback).toHaveBeenCalledWith(
                expect.objectContaining({ option: newOption })
            );
        });

        it('should emit option:remove event when removing option', () => {
            const callback = vi.fn();
            const radio = new FlexRadio(container, {
                name: 'test-radio',
                options: defaultOptions
            });

            radio.on('option:remove', callback);
            radio.removeOption('option2');

            expect(callback).toHaveBeenCalledWith(
                expect.objectContaining({ option: defaultOptions[1] })
            );
        });

        it('should emit option:update event when updating option', () => {
            const callback = vi.fn();
            const radio = new FlexRadio(container, {
                name: 'test-radio',
                options: defaultOptions
            });

            radio.on('option:update', callback);
            radio.updateOption('option2', { label: 'Updated' });

            expect(callback).toHaveBeenCalledWith(
                expect.objectContaining({
                    value: 'option2',
                    updates: { label: 'Updated' }
                })
            );
        });

        it('should emit clear event when clearing', () => {
            const callback = vi.fn();
            const radio = new FlexRadio(container, {
                name: 'test-radio',
                value: 'option2',
                options: defaultOptions
            });

            radio.on('clear', callback);
            radio.clear();

            expect(callback).toHaveBeenCalled();
        });
    });

    describe('Attributes', () => {
        it('should set required attribute on first radio', () => {
            const radio = new FlexRadio(container, {
                name: 'test-radio',
                required: true,
                options: defaultOptions
            });

            expect(radio.radioElements[0].required).toBe(true);
            expect(radio.radioElements[1].required).toBe(false);
        });

        it('should set custom id when provided', () => {
            const radio = new FlexRadio(container, {
                name: 'test-radio',
                options: [
                    { value: 'opt1', label: 'Option 1', id: 'custom-id' }
                ]
            });

            expect(radio.radioElements[0].id).toBe('custom-id');
        });

        it('should set role="radiogroup" on container', () => {
            const radio = new FlexRadio(container, {
                name: 'test-radio',
                options: defaultOptions
            });

            const group = container.querySelector('.flex-radio-group');
            expect(group.getAttribute('role')).toBe('radiogroup');
        });
    });

    describe('Cleanup', () => {
        it('should destroy component', () => {
            const radio = new FlexRadio(container, {
                name: 'test-radio',
                options: defaultOptions
            });

            // Destroy should clear the component
            radio.destroy();

            expect(radio.state.destroyed).toBe(true);
            expect(radio.events.size).toBe(0);
        });
    });
});
