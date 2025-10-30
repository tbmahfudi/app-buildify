/**
 * FlexAccordion Component Tests
 *
 * Tests for the collapsible accordion component
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import FlexAccordion from '../../frontend/assets/js/components/flex-accordion.js';
import {
    createTestContainer,
    cleanupTestContainer,
    click,
    wait
} from '../helpers/test-utils.js';

describe('FlexAccordion', () => {
    let container;

    const defaultItems = [
        { id: 'item1', title: 'Item 1', content: 'Content 1' },
        { id: 'item2', title: 'Item 2', content: 'Content 2' },
        { id: 'item3', title: 'Item 3', content: 'Content 3' }
    ];

    beforeEach(() => {
        container = createTestContainer();
    });

    afterEach(() => {
        cleanupTestContainer(container);
    });

    describe('Initialization', () => {
        it('should create accordion with default options', () => {
            const accordion = new FlexAccordion(container, { items: defaultItems });

            expect(accordion.element).toBe(container);
            expect(accordion.state.openItems.size).toBe(0);
        });

        it('should create accordion with default open items', () => {
            const accordion = new FlexAccordion(container, {
                items: defaultItems,
                defaultOpen: ['item1', 'item3']
            });

            expect(accordion.state.openItems.has('item1')).toBe(true);
            expect(accordion.state.openItems.has('item3')).toBe(true);
        });

        it('should emit init event', () => {
            const callback = vi.fn();
            const accordion = new FlexAccordion(container, { items: defaultItems });

            accordion.on('init', callback);
            accordion.init();

            expect(callback).toHaveBeenCalled();
        });
    });

    describe('Rendering', () => {
        it('should render all accordion items', () => {
            const accordion = new FlexAccordion(container, { items: defaultItems });

            const items = container.querySelectorAll('.flex-accordion-item');
            expect(items.length).toBe(3);
        });

        it('should render item headers', () => {
            const accordion = new FlexAccordion(container, { items: defaultItems });

            const headers = container.querySelectorAll('.flex-accordion-header');
            expect(headers.length).toBe(3);
            expect(headers[0].textContent).toContain('Item 1');
            expect(headers[1].textContent).toContain('Item 2');
            expect(headers[2].textContent).toContain('Item 3');
        });

        it('should render item content', () => {
            const accordion = new FlexAccordion(container, { items: defaultItems });

            const contents = container.querySelectorAll('.flex-accordion-content');
            expect(contents.length).toBe(3);
            expect(contents[0].textContent).toContain('Content 1');
            expect(contents[1].textContent).toContain('Content 2');
            expect(contents[2].textContent).toContain('Content 3');
        });

        it('should render with bordered variant by default', () => {
            const accordion = new FlexAccordion(container, { items: defaultItems });

            const wrapper = container.querySelector('.flex-accordion');
            expect(wrapper.classList.contains('border')).toBe(true);
            expect(wrapper.classList.contains('rounded-lg')).toBe(true);
        });

        it('should render with separated variant', () => {
            const accordion = new FlexAccordion(container, {
                items: defaultItems,
                variant: 'separated'
            });

            const wrapper = container.querySelector('.flex-accordion');
            expect(wrapper.classList.contains('space-y-2')).toBe(true);
        });

        it('should render with flush variant', () => {
            const accordion = new FlexAccordion(container, {
                items: defaultItems,
                variant: 'flush'
            });

            const headers = container.querySelectorAll('.flex-accordion-header');
            expect(headers[0].classList.contains('border-b')).toBe(true);
        });

        it('should render icon on right by default', () => {
            const accordion = new FlexAccordion(container, { items: defaultItems });

            const header = container.querySelector('.flex-accordion-header');
            const icon = header.querySelector('.flex-accordion-icon');
            const lastChild = header.lastElementChild;

            expect(icon).toBeTruthy();
            expect(lastChild).toBe(icon.parentElement);
        });

        it('should render icon on left when specified', () => {
            const accordion = new FlexAccordion(container, {
                items: defaultItems,
                iconPosition: 'left'
            });

            const header = container.querySelector('.flex-accordion-header');
            const icon = header.querySelector('.flex-accordion-icon');
            const firstChild = header.firstElementChild;

            expect(icon).toBeTruthy();
            expect(firstChild).toBe(icon);
        });

        it('should render subtitle when provided', () => {
            const accordion = new FlexAccordion(container, {
                items: [
                    { id: 'item1', title: 'Item 1', subtitle: 'Subtitle 1', content: 'Content 1' }
                ]
            });

            const subtitle = container.querySelector('.flex-accordion-subtitle');
            expect(subtitle).toBeTruthy();
            expect(subtitle.textContent).toBe('Subtitle 1');
        });

        it('should render disabled items', () => {
            const accordion = new FlexAccordion(container, {
                items: [
                    { id: 'item1', title: 'Item 1', content: 'Content 1', disabled: true }
                ]
            });

            const header = container.querySelector('.flex-accordion-header');
            expect(header.disabled).toBe(true);
            expect(header.classList.contains('opacity-50')).toBe(true);
        });

        it('should set ARIA attributes correctly', () => {
            const accordion = new FlexAccordion(container, {
                items: defaultItems,
                defaultOpen: ['item1']
            });

            const headers = container.querySelectorAll('.flex-accordion-header');
            expect(headers[0].getAttribute('aria-expanded')).toBe('true');
            expect(headers[1].getAttribute('aria-expanded')).toBe('false');
            expect(headers[0].getAttribute('aria-controls')).toBe('accordion-content-item1');
        });

        it('should set initial open state with maxHeight', () => {
            const accordion = new FlexAccordion(container, {
                items: defaultItems,
                defaultOpen: ['item1']
            });

            const contents = container.querySelectorAll('.flex-accordion-content');
            expect(contents[0].style.opacity).toBe('1');
            expect(contents[1].style.maxHeight).toBe('0px');
            expect(contents[1].style.opacity).toBe('0');
        });
    });

    describe('User Interaction', () => {
        it('should toggle item on header click', async () => {
            const accordion = new FlexAccordion(container, { items: defaultItems });

            const header = container.querySelector('.flex-accordion-header');
            click(header);
            await wait(50);

            expect(accordion.state.openItems.has('item1')).toBe(true);

            click(header);
            await wait(50);

            expect(accordion.state.openItems.has('item1')).toBe(false);
        });

        it('should close other items when allowMultiple is false', async () => {
            const accordion = new FlexAccordion(container, {
                items: defaultItems,
                allowMultiple: false,
                defaultOpen: ['item1']
            });

            const headers = container.querySelectorAll('.flex-accordion-header');
            click(headers[1]);
            await wait(50);

            expect(accordion.state.openItems.has('item1')).toBe(false);
            expect(accordion.state.openItems.has('item2')).toBe(true);
        });

        it('should keep other items open when allowMultiple is true', async () => {
            const accordion = new FlexAccordion(container, {
                items: defaultItems,
                allowMultiple: true,
                defaultOpen: ['item1']
            });

            const headers = container.querySelectorAll('.flex-accordion-header');
            click(headers[1]);
            await wait(50);

            expect(accordion.state.openItems.has('item1')).toBe(true);
            expect(accordion.state.openItems.has('item2')).toBe(true);
        });

        it('should emit toggle event', async () => {
            const callback = vi.fn();
            const accordion = new FlexAccordion(container, { items: defaultItems });

            accordion.on('toggle', callback);
            const header = container.querySelector('.flex-accordion-header');

            click(header);
            await wait(50);

            expect(callback).toHaveBeenCalledWith(
                expect.objectContaining({
                    itemId: 'item1',
                    isOpen: true
                })
            );
        });

        it('should call onToggle callback', async () => {
            const onToggle = vi.fn();
            const accordion = new FlexAccordion(container, {
                items: defaultItems,
                onToggle
            });

            const header = container.querySelector('.flex-accordion-header');
            click(header);
            await wait(50);

            expect(onToggle).toHaveBeenCalledWith('item1', true);
        });

        it('should emit open event', async () => {
            const callback = vi.fn();
            const accordion = new FlexAccordion(container, { items: defaultItems });

            accordion.on('open', callback);
            const header = container.querySelector('.flex-accordion-header');

            click(header);
            await wait(50);

            expect(callback).toHaveBeenCalledWith(
                expect.objectContaining({ itemId: 'item1' })
            );
        });

        it('should call onOpen callback', async () => {
            const onOpen = vi.fn();
            const accordion = new FlexAccordion(container, {
                items: defaultItems,
                onOpen
            });

            const header = container.querySelector('.flex-accordion-header');
            click(header);
            await wait(50);

            expect(onOpen).toHaveBeenCalledWith('item1');
        });

        it('should emit close event', async () => {
            const callback = vi.fn();
            const accordion = new FlexAccordion(container, {
                items: defaultItems,
                defaultOpen: ['item1']
            });

            accordion.on('close', callback);
            const header = container.querySelector('.flex-accordion-header');

            click(header);
            await wait(50);

            expect(callback).toHaveBeenCalledWith(
                expect.objectContaining({ itemId: 'item1' })
            );
        });

        it('should call onClose callback', async () => {
            const onClose = vi.fn();
            const accordion = new FlexAccordion(container, {
                items: defaultItems,
                defaultOpen: ['item1'],
                onClose
            });

            const header = container.querySelector('.flex-accordion-header');
            click(header);
            await wait(50);

            expect(onClose).toHaveBeenCalledWith('item1');
        });

        it('should not toggle disabled items', async () => {
            const accordion = new FlexAccordion(container, {
                items: [
                    { id: 'item1', title: 'Item 1', content: 'Content 1', disabled: true }
                ]
            });

            const header = container.querySelector('.flex-accordion-header');
            click(header);
            await wait(50);

            expect(accordion.state.openItems.has('item1')).toBe(false);
        });

        it('should update icon on toggle', async () => {
            const accordion = new FlexAccordion(container, {
                items: defaultItems,
                icon: {
                    collapsed: 'ph-caret-right',
                    expanded: 'ph-caret-down'
                }
            });

            const header = container.querySelector('.flex-accordion-header');
            const icon = header.querySelector('.flex-accordion-icon');

            expect(icon.className).toContain('ph-caret-right');

            click(header);
            await wait(50);

            expect(icon.className).toContain('ph-caret-down');
        });
    });

    describe('API Methods', () => {
        it('should open item with open()', () => {
            const accordion = new FlexAccordion(container, { items: defaultItems });

            accordion.open('item2');

            expect(accordion.state.openItems.has('item2')).toBe(true);
            const content = container.querySelectorAll('.flex-accordion-content')[1];
            expect(content.style.opacity).toBe('1');
        });

        it('should close item with close()', () => {
            const accordion = new FlexAccordion(container, {
                items: defaultItems,
                defaultOpen: ['item1']
            });

            accordion.close('item1');

            expect(accordion.state.openItems.has('item1')).toBe(false);
            const content = container.querySelector('.flex-accordion-content');
            expect(content.style.maxHeight).toBe('0px');
        });

        it('should toggle item with toggle()', () => {
            const accordion = new FlexAccordion(container, { items: defaultItems });

            accordion.toggle('item1');
            expect(accordion.state.openItems.has('item1')).toBe(true);

            accordion.toggle('item1');
            expect(accordion.state.openItems.has('item1')).toBe(false);
        });

        it('should open all items with openAll()', () => {
            const accordion = new FlexAccordion(container, {
                items: defaultItems,
                allowMultiple: true
            });

            accordion.openAll();

            expect(accordion.state.openItems.size).toBe(3);
            expect(accordion.state.openItems.has('item1')).toBe(true);
            expect(accordion.state.openItems.has('item2')).toBe(true);
            expect(accordion.state.openItems.has('item3')).toBe(true);
        });

        it('should not open all items when allowMultiple is false', () => {
            const accordion = new FlexAccordion(container, {
                items: defaultItems,
                allowMultiple: false
            });

            accordion.openAll();

            expect(accordion.state.openItems.size).toBe(0);
        });

        it('should close all items with closeAll()', () => {
            const accordion = new FlexAccordion(container, {
                items: defaultItems,
                defaultOpen: ['item1', 'item2', 'item3']
            });

            accordion.closeAll();

            expect(accordion.state.openItems.size).toBe(0);
        });

        it('should check if item is open with isOpen()', () => {
            const accordion = new FlexAccordion(container, {
                items: defaultItems,
                defaultOpen: ['item1']
            });

            expect(accordion.isOpen('item1')).toBe(true);
            expect(accordion.isOpen('item2')).toBe(false);
        });

        it('should get open items with getOpenItems()', () => {
            const accordion = new FlexAccordion(container, {
                items: defaultItems,
                defaultOpen: ['item1', 'item3']
            });

            const openItems = accordion.getOpenItems();

            expect(openItems).toEqual(['item1', 'item3']);
        });

        it('should add item with addItem()', () => {
            const accordion = new FlexAccordion(container, { items: defaultItems });

            accordion.addItem({ id: 'item4', title: 'Item 4', content: 'Content 4' });

            expect(accordion.options.items.length).toBe(4);
            const items = container.querySelectorAll('.flex-accordion-item');
            expect(items.length).toBe(4);
        });

        it('should emit item:add event', () => {
            const callback = vi.fn();
            const accordion = new FlexAccordion(container, { items: defaultItems });

            accordion.on('item:add', callback);
            const newItem = { id: 'item4', title: 'Item 4', content: 'Content 4' };
            accordion.addItem(newItem);

            expect(callback).toHaveBeenCalledWith(
                expect.objectContaining({ item: newItem })
            );
        });

        it('should remove item with removeItem()', () => {
            const accordion = new FlexAccordion(container, { items: defaultItems });

            accordion.removeItem('item2');

            expect(accordion.options.items.length).toBe(2);
            const items = container.querySelectorAll('.flex-accordion-item');
            expect(items.length).toBe(2);
        });

        it('should emit item:remove event', () => {
            const callback = vi.fn();
            const accordion = new FlexAccordion(container, { items: defaultItems });

            accordion.on('item:remove', callback);
            accordion.removeItem('item2');

            expect(callback).toHaveBeenCalledWith(
                expect.objectContaining({ item: defaultItems[1] })
            );
        });

        it('should update item with updateItem()', () => {
            const accordion = new FlexAccordion(container, { items: defaultItems });

            accordion.updateItem('item2', { title: 'Updated Item 2' });

            const headers = container.querySelectorAll('.flex-accordion-header');
            expect(headers[1].textContent).toContain('Updated Item 2');
        });

        it('should emit item:update event', () => {
            const callback = vi.fn();
            const accordion = new FlexAccordion(container, { items: defaultItems });

            accordion.on('item:update', callback);
            accordion.updateItem('item2', { title: 'Updated' });

            expect(callback).toHaveBeenCalledWith(
                expect.objectContaining({
                    itemId: 'item2',
                    updates: { title: 'Updated' }
                })
            );
        });
    });

    describe('Content Types', () => {
        it('should render string content as HTML', () => {
            const accordion = new FlexAccordion(container, {
                items: [
                    { id: 'item1', title: 'Item 1', content: '<strong>Bold content</strong>' }
                ]
            });

            const content = container.querySelector('.flex-accordion-content');
            const strong = content.querySelector('strong');
            expect(strong).toBeTruthy();
            expect(strong.textContent).toBe('Bold content');
        });

        it('should render HTMLElement content', () => {
            const element = document.createElement('div');
            element.className = 'custom-content';
            element.textContent = 'Custom element';

            const accordion = new FlexAccordion(container, {
                items: [
                    { id: 'item1', title: 'Item 1', content: element }
                ]
            });

            const customContent = container.querySelector('.custom-content');
            expect(customContent).toBeTruthy();
            expect(customContent.textContent).toBe('Custom element');
        });
    });

    describe('Animations', () => {
        it('should apply transition styles when animated', () => {
            const accordion = new FlexAccordion(container, {
                items: defaultItems,
                animated: true
            });

            const content = container.querySelector('.flex-accordion-content');
            expect(content.style.transition).toContain('max-height');
            expect(content.style.transition).toContain('opacity');
        });

        it('should not apply transitions when animated is false', () => {
            const accordion = new FlexAccordion(container, {
                items: defaultItems,
                animated: false
            });

            const content = container.querySelector('.flex-accordion-content');
            expect(content.style.transition).toBe('');
        });
    });

    describe('Cleanup', () => {
        it('should destroy component', () => {
            const accordion = new FlexAccordion(container, { items: defaultItems });

            // Destroy should clear the component
            accordion.destroy();

            expect(accordion.state.destroyed).toBe(true);
            expect(accordion.events.size).toBe(0);
        });
    });
});
