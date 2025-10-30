/**
 * BaseComponent Tests
 *
 * Tests for the base component class that all components extend
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import BaseComponent from '../../frontend/assets/js/core/base-component.js';
import { createTestContainer, cleanupTestContainer } from '../helpers/test-utils.js';

describe('BaseComponent', () => {
    let container;

    beforeEach(() => {
        container = createTestContainer();
    });

    afterEach(() => {
        cleanupTestContainer(container);
    });

    describe('Constructor', () => {
        it('should initialize with element and default options', () => {
            const component = new BaseComponent(container);

            expect(component.element).toBe(container);
            expect(component.options).toEqual({});
            expect(component.events).toBeInstanceOf(Map);
        });

        it('should merge custom options with defaults', () => {
            class TestComponent extends BaseComponent {
                static DEFAULTS = {
                    color: 'blue',
                    size: 'md'
                };
            }

            const component = new TestComponent(container, { color: 'red' });

            expect(component.options.color).toBe('red');
            expect(component.options.size).toBe('md');
        });

        it('should throw error if element is not provided', () => {
            expect(() => new BaseComponent(null)).toThrow();
        });

        it('should accept string selector for element', () => {
            container.id = 'test-component';
            const component = new BaseComponent('#test-component');

            expect(component.element).toBe(container);
        });
    });

    describe('Event System', () => {
        let component;

        beforeEach(() => {
            component = new BaseComponent(container);
        });

        it('should register event listener with on()', () => {
            const callback = vi.fn();
            component.on('test-event', callback);

            expect(component.events.has('test-event')).toBe(true);
            expect(component.events.get('test-event')).toContain(callback);
        });

        it('should emit events with emit()', () => {
            const callback = vi.fn();
            component.on('test-event', callback);

            component.emit('test-event', { data: 'test' });

            expect(callback).toHaveBeenCalledOnce();
            expect(callback).toHaveBeenCalledWith(
                expect.objectContaining({
                    data: 'test',
                    component: component
                })
            );
        });

        it('should support multiple listeners for same event', () => {
            const callback1 = vi.fn();
            const callback2 = vi.fn();

            component.on('test-event', callback1);
            component.on('test-event', callback2);
            component.emit('test-event');

            expect(callback1).toHaveBeenCalledOnce();
            expect(callback2).toHaveBeenCalledOnce();
        });

        it('should remove event listener with off()', () => {
            const callback = vi.fn();
            component.on('test-event', callback);
            component.off('test-event', callback);

            component.emit('test-event');

            expect(callback).not.toHaveBeenCalled();
        });

        it('should remove all listeners for event when no callback provided', () => {
            const callback1 = vi.fn();
            const callback2 = vi.fn();

            component.on('test-event', callback1);
            component.on('test-event', callback2);
            component.off('test-event');

            component.emit('test-event');

            expect(callback1).not.toHaveBeenCalled();
            expect(callback2).not.toHaveBeenCalled();
        });

        it('should emit event once with once()', () => {
            const callback = vi.fn();
            component.once('test-event', callback);

            component.emit('test-event');
            component.emit('test-event');

            expect(callback).toHaveBeenCalledOnce();
        });
    });

    describe('Options Management', () => {
        it('should update options with setOption()', () => {
            const component = new BaseComponent(container, { color: 'blue' });

            component.setOption('color', 'red');

            expect(component.options.color).toBe('red');
        });

        it('should get option with getOption()', () => {
            const component = new BaseComponent(container, { color: 'blue' });

            expect(component.getOption('color')).toBe('blue');
        });

        it('should return undefined for non-existent option', () => {
            const component = new BaseComponent(container);

            expect(component.getOption('nonexistent')).toBeUndefined();
        });

        it('should update multiple options with setOptions()', () => {
            const component = new BaseComponent(container, { color: 'blue', size: 'md' });

            component.setOptions({ color: 'red', size: 'lg' });

            expect(component.options.color).toBe('red');
            expect(component.options.size).toBe('lg');
        });
    });

    describe('Lifecycle', () => {
        it('should call destroy() and clean up events', () => {
            const component = new BaseComponent(container);
            const testCallback = vi.fn();

            component.on('test-event', testCallback);

            // Destroy emits a destroy event, so we need to filter that out
            const destroyCallbackCalls = testCallback.mock.calls.filter(call =>
                !call[0] || call[0].component !== component
            );

            component.destroy();
            component.emit('test-event');

            // After destroy, the test-event should not be handled
            expect(component.events.size).toBe(0);
        });

        it('should emit destroy event', () => {
            const component = new BaseComponent(container);
            const callback = vi.fn();

            component.on('destroy', callback);
            component.destroy();

            expect(callback).toHaveBeenCalledOnce();
        });
    });

    describe('DOM Utilities', () => {
        it('should add class to element', () => {
            const component = new BaseComponent(container);
            component.addClass('test-class');

            expect(container.classList.contains('test-class')).toBe(true);
        });

        it('should remove class from element', () => {
            container.classList.add('test-class');
            const component = new BaseComponent(container);

            component.removeClass('test-class');

            expect(container.classList.contains('test-class')).toBe(false);
        });

        it('should toggle class on element', () => {
            const component = new BaseComponent(container);

            component.toggleClass('test-class');
            expect(container.classList.contains('test-class')).toBe(true);

            component.toggleClass('test-class');
            expect(container.classList.contains('test-class')).toBe(false);
        });

        it('should check if element has class', () => {
            container.classList.add('test-class');
            const component = new BaseComponent(container);

            expect(component.hasClass('test-class')).toBe(true);
            expect(component.hasClass('nonexistent')).toBe(false);
        });
    });

    describe('State Management', () => {
        it('should initialize with internal state', () => {
            const component = new BaseComponent(container);

            expect(component.state).toHaveProperty('initialized');
            expect(component.state).toHaveProperty('destroyed');
        });

        it('should allow state updates', () => {
            const component = new BaseComponent(container);
            component.state = { active: true };

            expect(component.state.active).toBe(true);
        });

        it('should maintain state across operations', () => {
            const component = new BaseComponent(container);
            component.state = { count: 0 };

            component.state.count++;
            component.state.count++;

            expect(component.state.count).toBe(2);
        });
    });

    describe('Element Queries', () => {
        it('should find elements within component', () => {
            container.innerHTML = '<div class="child"></div>';
            const component = new BaseComponent(container);

            const child = component.element.querySelector('.child');

            expect(child).toBeTruthy();
            expect(child.classList.contains('child')).toBe(true);
        });

        it('should find all matching elements', () => {
            container.innerHTML = '<div class="child"></div><div class="child"></div>';
            const component = new BaseComponent(container);

            const children = component.element.querySelectorAll('.child');

            expect(children.length).toBe(2);
        });
    });
});
