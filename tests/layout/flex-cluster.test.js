/**
 * FlexCluster Component Tests
 *
 * Tests for the horizontal grouping/cluster component
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import FlexCluster from '../../frontend/assets/js/layout/flex-cluster.js';
import {
    createTestContainer,
    cleanupTestContainer
} from '../helpers/test-utils.js';

describe('FlexCluster', () => {
    let container;

    const defaultItems = [
        { id: 'item1', content: '<span>Item 1</span>' },
        { id: 'item2', content: '<span>Item 2</span>' },
        { id: 'item3', content: '<span>Item 3</span>' }
    ];

    beforeEach(() => {
        container = createTestContainer();
    });

    afterEach(() => {
        cleanupTestContainer(container);
    });

    describe('Initialization', () => {
        it('should create cluster with default options', () => {
            const cluster = new FlexCluster(container);

            expect(cluster.container).toBe(container);
            expect(cluster.options.gap).toBe(2);
            expect(cluster.options.justify).toBe('start');
            expect(cluster.options.align).toBe('center');
            expect(cluster.options.wrap).toBe(true);
        });

        it('should create cluster with custom options', () => {
            const cluster = new FlexCluster(container, {
                gap: 4,
                justify: 'center',
                align: 'start',
                wrap: false
            });

            expect(cluster.options.gap).toBe(4);
            expect(cluster.options.justify).toBe('center');
            expect(cluster.options.align).toBe('start');
            expect(cluster.options.wrap).toBe(false);
        });

        it('should create cluster with items', () => {
            const cluster = new FlexCluster(container, {
                items: defaultItems
            });

            expect(cluster.options.items.length).toBe(3);
        });

        it('should emit init event', () => {
            const callback = vi.fn();
            const cluster = new FlexCluster(container);

            cluster.on('init', callback);
            cluster.init();

            expect(callback).toHaveBeenCalled();
        });
    });

    describe('Rendering', () => {
        it('should add flex-cluster class to container', () => {
            const cluster = new FlexCluster(container);

            expect(container.classList.contains('flex-cluster')).toBe(true);
        });

        it('should apply flex styles', () => {
            const cluster = new FlexCluster(container);

            expect(container.classList.contains('flex')).toBe(true);
        });

        it('should apply wrap styles when wrap is true', () => {
            const cluster = new FlexCluster(container, { wrap: true });

            expect(container.classList.contains('flex-wrap')).toBe(true);
        });

        it('should apply no-wrap styles when wrap is false', () => {
            const cluster = new FlexCluster(container, { wrap: false });

            expect(container.classList.contains('flex-nowrap')).toBe(true);
        });

        it('should render items', () => {
            const cluster = new FlexCluster(container, {
                items: defaultItems
            });

            const items = container.querySelectorAll('.flex-cluster-item');
            expect(items.length).toBe(3);
        });

        it('should render item content', () => {
            const cluster = new FlexCluster(container, {
                items: [{ id: 'test', content: '<strong>Test Content</strong>' }]
            });

            const strong = container.querySelector('strong');
            expect(strong).toBeTruthy();
            expect(strong.textContent).toBe('Test Content');
        });
    });

    describe('Justify Alignment', () => {
        it('should apply justify-start', () => {
            const cluster = new FlexCluster(container, { justify: 'start' });

            expect(container.classList.contains('justify-start')).toBe(true);
        });

        it('should apply justify-center', () => {
            const cluster = new FlexCluster(container, { justify: 'center' });

            expect(container.classList.contains('justify-center')).toBe(true);
        });

        it('should apply justify-end', () => {
            const cluster = new FlexCluster(container, { justify: 'end' });

            expect(container.classList.contains('justify-end')).toBe(true);
        });

        it('should apply justify-between', () => {
            const cluster = new FlexCluster(container, { justify: 'between' });

            expect(container.classList.contains('justify-between')).toBe(true);
        });

        it('should apply justify-around', () => {
            const cluster = new FlexCluster(container, { justify: 'around' });

            expect(container.classList.contains('justify-around')).toBe(true);
        });

        it('should apply justify-evenly', () => {
            const cluster = new FlexCluster(container, { justify: 'evenly' });

            expect(container.classList.contains('justify-evenly')).toBe(true);
        });
    });

    describe('Align Alignment', () => {
        it('should apply items-center by default', () => {
            const cluster = new FlexCluster(container);

            expect(container.classList.contains('items-center')).toBe(true);
        });

        it('should apply items-start', () => {
            const cluster = new FlexCluster(container, { align: 'start' });

            expect(container.classList.contains('items-start')).toBe(true);
        });

        it('should apply items-end', () => {
            const cluster = new FlexCluster(container, { align: 'end' });

            expect(container.classList.contains('items-end')).toBe(true);
        });

        it('should apply items-stretch', () => {
            const cluster = new FlexCluster(container, { align: 'stretch' });

            expect(container.classList.contains('items-stretch')).toBe(true);
        });

        it('should apply items-baseline', () => {
            const cluster = new FlexCluster(container, { align: 'baseline' });

            expect(container.classList.contains('items-baseline')).toBe(true);
        });
    });

    describe('Gap Spacing', () => {
        it('should apply gap-2 by default', () => {
            const cluster = new FlexCluster(container);

            expect(container.classList.contains('gap-2')).toBe(true);
        });

        it('should apply custom gap', () => {
            const cluster = new FlexCluster(container, { gap: 4 });

            expect(container.classList.contains('gap-4')).toBe(true);
        });

        it('should update gap with setGap()', () => {
            const cluster = new FlexCluster(container, { gap: 2 });

            cluster.setGap(6);

            expect(container.classList.contains('gap-6')).toBe(true);
            expect(container.classList.contains('gap-2')).toBe(false);
        });
    });

    describe('Item Management', () => {
        it('should add item with addItem()', () => {
            const cluster = new FlexCluster(container, {
                items: [...defaultItems]
            });

            const initialLength = cluster.options.items.length;
            cluster.addItem({ id: 'item4', content: '<span>Item 4</span>' });

            expect(cluster.options.items.length).toBe(initialLength + 1);
            expect(cluster.options.items.find(item => item.id === 'item4')).toBeDefined();
        });

        it('should add item at specific index', () => {
            const cluster = new FlexCluster(container, {
                items: [...defaultItems]
            });

            cluster.addItem({ id: 'item4', content: '<span>Item 4</span>' }, 1);

            expect(cluster.options.items[1].id).toBe('item4');
        });

        it('should emit item:add event', () => {
            const callback = vi.fn();
            const cluster = new FlexCluster(container, {
                items: [...defaultItems]
            });

            cluster.on('item:add', callback);
            const newItem = { id: 'item4', content: '<span>Item 4</span>' };
            cluster.addItem(newItem);

            expect(callback).toHaveBeenCalled();
            const eventData = callback.mock.calls[0][0];
            expect(eventData.item).toEqual(newItem);
        });

        it('should remove item with removeItem()', () => {
            const cluster = new FlexCluster(container, {
                items: [...defaultItems]
            });

            const initialLength = cluster.options.items.length;
            cluster.removeItem('item2');

            expect(cluster.options.items.length).toBe(initialLength - 1);
            expect(cluster.options.items.find(item => item.id === 'item2')).toBeUndefined();
        });

        it('should emit item:remove event', () => {
            const callback = vi.fn();
            const cluster = new FlexCluster(container, {
                items: [...defaultItems]
            });

            cluster.on('item:remove', callback);
            cluster.removeItem('item2');

            expect(callback).toHaveBeenCalled();
            const eventData = callback.mock.calls[0][0];
            expect(eventData.item.id).toBe('item2');
        });

        it('should update item with updateItem()', () => {
            const cluster = new FlexCluster(container, {
                items: [...defaultItems]
            });

            cluster.updateItem('item2', { content: '<span>Updated Item 2</span>' });

            const item = cluster.options.items.find(item => item.id === 'item2');
            expect(item.content).toBe('<span>Updated Item 2</span>');
        });

        it('should emit item:update event', () => {
            const callback = vi.fn();
            const cluster = new FlexCluster(container, {
                items: [...defaultItems]
            });

            cluster.on('item:update', callback);
            cluster.updateItem('item2', { content: 'Updated' });

            expect(callback).toHaveBeenCalled();
            const eventData = callback.mock.calls[0][0];
            expect(eventData.itemId).toBe('item2');
        });

        it('should clear all items with clearItems()', () => {
            const cluster = new FlexCluster(container, {
                items: [...defaultItems]
            });

            cluster.clearItems();

            expect(cluster.options.items.length).toBe(0);
        });

        it('should emit clear event', () => {
            const callback = vi.fn();
            const cluster = new FlexCluster(container, {
                items: [...defaultItems]
            });

            cluster.on('clear', callback);
            cluster.clearItems();

            expect(callback).toHaveBeenCalled();
        });
    });

    describe('Dynamic Updates', () => {
        it('should update justify with setJustify()', () => {
            const cluster = new FlexCluster(container, { justify: 'start' });

            cluster.setJustify('center');

            expect(container.classList.contains('justify-center')).toBe(true);
            expect(container.classList.contains('justify-start')).toBe(false);
        });

        it('should update align with setAlign()', () => {
            const cluster = new FlexCluster(container, { align: 'center' });

            cluster.setAlign('start');

            expect(container.classList.contains('items-start')).toBe(true);
            expect(container.classList.contains('items-center')).toBe(false);
        });

        it('should update wrap with setWrap()', () => {
            const cluster = new FlexCluster(container, { wrap: true });

            cluster.setWrap(false);

            expect(container.classList.contains('flex-nowrap')).toBe(true);
            expect(container.classList.contains('flex-wrap')).toBe(false);
        });
    });

    describe('Priority Ordering', () => {
        it('should order items by priority', () => {
            const cluster = new FlexCluster(container, {
                items: [
                    { id: 'low', content: '<span>Low</span>', priority: 0 },
                    { id: 'high', content: '<span>High</span>', priority: 2 },
                    { id: 'medium', content: '<span>Medium</span>', priority: 1 }
                ]
            });

            const items = container.querySelectorAll('.flex-cluster-item');
            expect(items[0].getAttribute('data-item-id')).toBe('high');
            expect(items[1].getAttribute('data-item-id')).toBe('medium');
            expect(items[2].getAttribute('data-item-id')).toBe('low');
        });

        it('should maintain original order when priority is same', () => {
            const cluster = new FlexCluster(container, {
                items: [
                    { id: 'first', content: '<span>First</span>', priority: 1 },
                    { id: 'second', content: '<span>Second</span>', priority: 1 },
                    { id: 'third', content: '<span>Third</span>', priority: 1 }
                ]
            });

            const items = container.querySelectorAll('.flex-cluster-item');
            expect(items[0].getAttribute('data-item-id')).toBe('first');
            expect(items[1].getAttribute('data-item-id')).toBe('second');
            expect(items[2].getAttribute('data-item-id')).toBe('third');
        });
    });

    describe('Animations', () => {
        it('should apply transition classes when animated', () => {
            const cluster = new FlexCluster(container, { animated: true });

            const clusterElement = container;
            expect(clusterElement.classList.contains('transition-all')).toBe(true);
        });

        it('should not apply transition classes when not animated', () => {
            const cluster = new FlexCluster(container, { animated: false });

            const clusterElement = container;
            expect(clusterElement.classList.contains('transition-all')).toBe(false);
        });
    });

    describe('Custom Classes', () => {
        it('should apply custom classes', () => {
            const cluster = new FlexCluster(container, {
                classes: ['custom-class-1', 'custom-class-2']
            });

            expect(container.classList.contains('custom-class-1')).toBe(true);
            expect(container.classList.contains('custom-class-2')).toBe(true);
        });
    });

    describe('Cleanup', () => {
        it('should destroy component', () => {
            const cluster = new FlexCluster(container, {
                items: defaultItems
            });

            cluster.destroy();

            expect(cluster.state.destroyed).toBe(true);
        });
    });
});
