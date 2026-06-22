import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import FlexTooltip from '../../frontend/assets/js/components/flex-tooltip.js';
import { createTestContainer, cleanupTestContainer } from '../helpers/test-utils.js';

describe('FlexTooltip', () => {
    let container, triggerEl;

    beforeEach(() => {
        container = createTestContainer();
        triggerEl = document.createElement('button');
        triggerEl.textContent = 'Hover me';
        container.appendChild(triggerEl);
    });

    afterEach(() => {
        cleanupTestContainer(container);
        vi.useRealTimers();
        document.body.innerHTML = '';
    });

    describe('Initialization', () => {
        it('should create tooltip instance', () => {
            const tt = new FlexTooltip(triggerEl, { content: 'Tooltip text' });
            expect(tt).toBeTruthy();
        });

        it('should default to hidden', () => {
            const tt = new FlexTooltip(triggerEl, { content: 'Tooltip' });
            expect(tt.state.visible).toBe(false);
        });

        it('should create tooltipElement', () => {
            const tt = new FlexTooltip(triggerEl, { content: 'Tooltip' });
            expect(tt.tooltipElement).toBeTruthy();
        });
    });

    describe('Show/Hide', () => {
        it('should show tooltip', () => {
            vi.useFakeTimers();
            const tt = new FlexTooltip(triggerEl, { content: 'Tooltip', trigger: 'manual', delay: 0 });
            tt.show();
            vi.advanceTimersByTime(50);
            expect(tt.state.visible).toBe(true);
        });

        it('should hide tooltip', () => {
            vi.useFakeTimers();
            const tt = new FlexTooltip(triggerEl, { content: 'Tooltip', trigger: 'manual', delay: 0 });
            tt.show();
            vi.advanceTimersByTime(50);
            tt.hide();
            vi.advanceTimersByTime(50);
            expect(tt.state.visible).toBe(false);
        });

        it('should call onShow callback', () => {
            vi.useFakeTimers();
            const cb = vi.fn();
            const tt = new FlexTooltip(triggerEl, { content: 'Tooltip', trigger: 'manual', delay: 0, onShow: cb });
            tt.show();
            vi.advanceTimersByTime(50);
            expect(cb).toHaveBeenCalled();
        });

        it('should call onHide callback', () => {
            vi.useFakeTimers();
            const cb = vi.fn();
            const tt = new FlexTooltip(triggerEl, { content: 'Tooltip', trigger: 'manual', delay: 0, onHide: cb });
            tt.show();
            vi.advanceTimersByTime(50);
            tt.hide();
            vi.advanceTimersByTime(50);
            expect(cb).toHaveBeenCalled();
        });
    });

    describe('Content', () => {
        it('should render tooltip content', () => {
            const tt = new FlexTooltip(triggerEl, { content: 'My tooltip' });
            expect(tt.tooltipElement.textContent).toContain('My tooltip');
        });

        it('should update content with setContent()', () => {
            const tt = new FlexTooltip(triggerEl, { content: 'Old' });
            tt.setContent('New content');
            expect(tt.tooltipElement.textContent).toContain('New content');
        });
    });

    describe('Positions', () => {
        it('should default to top position', () => {
            const tt = new FlexTooltip(triggerEl, { content: 'X' });
            expect(tt.options.position).toBe('top');
        });

        it('should accept bottom position', () => {
            const tt = new FlexTooltip(triggerEl, { content: 'X', position: 'bottom' });
            expect(tt.options.position).toBe('bottom');
        });
    });

    describe('Cleanup', () => {
        it('should destroy component', () => {
            const tt = new FlexTooltip(triggerEl, { content: 'X' });
            expect(() => tt.destroy()).not.toThrow();
        });
    });
});
