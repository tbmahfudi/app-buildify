import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import FlexBadge from '../../frontend/assets/js/components/flex-badge.js';
import { createTestContainer, cleanupTestContainer, click } from '../helpers/test-utils.js';

describe('FlexBadge', () => {
    let container;

    beforeEach(() => { container = createTestContainer(); });
    afterEach(() => { cleanupTestContainer(container); vi.useRealTimers(); });

    describe('Initialization', () => {
        it('should create badge element', () => {
            const badge = new FlexBadge(container, { text: 'New' });
            expect(badge.badgeElement).toBeTruthy();
        });

        it('should render text', () => {
            const badge = new FlexBadge(container, { text: 'Active' });
            expect(badge.badgeElement.textContent).toContain('Active');
        });

        it('should emit init event', () => {
            const cb = vi.fn();
            const badge = new FlexBadge(container, { text: 'X' });
            badge.on('init', cb);
            badge.emit('init');
            expect(cb).toHaveBeenCalled();
        });
    });

    describe('Variants', () => {
        it('should apply primary variant by default', () => {
            const badge = new FlexBadge(container, { text: 'X', variant: 'primary' });
            expect(badge.badgeElement.className).toContain('bg-blue-100');
        });

        it('should apply success variant', () => {
            const badge = new FlexBadge(container, { text: 'OK', variant: 'success' });
            expect(badge.badgeElement.className).toContain('bg-green-100');
        });

        it('should apply danger variant', () => {
            const badge = new FlexBadge(container, { text: 'Error', variant: 'danger' });
            expect(badge.badgeElement.className).toContain('bg-red-100');
        });

        it('should apply warning variant', () => {
            const badge = new FlexBadge(container, { text: 'Warn', variant: 'warning' });
            expect(badge.badgeElement.className).toContain('bg-amber-100');
        });
    });

    describe('Sizes', () => {
        it('should apply md size by default', () => {
            const badge = new FlexBadge(container, { text: 'X' });
            expect(badge.badgeElement.className).toContain('px-3');
        });

        it('should apply xs size', () => {
            const badge = new FlexBadge(container, { text: 'X', size: 'xs' });
            expect(badge.badgeElement.className).toContain('px-2');
        });
    });

    describe('Dot indicator', () => {
        it('should render dot when dot is true', () => {
            const badge = new FlexBadge(container, { text: 'X', dot: true });
            const dot = badge.badgeElement.querySelector('.rounded-full');
            expect(dot).toBeTruthy();
        });
    });

    describe('Dismissible', () => {
        it('should render close button when dismissible', () => {
            const badge = new FlexBadge(container, { text: 'X', dismissible: true });
            const closeBtn = badge.badgeElement.querySelector('button');
            expect(closeBtn).toBeTruthy();
        });

        it('should call onDismiss when close clicked', () => {
            vi.useFakeTimers();
            const cb = vi.fn();
            const badge = new FlexBadge(container, { text: 'X', dismissible: true, onDismiss: cb });
            const closeBtn = badge.badgeElement.querySelector('[data-dismiss=true]');
            click(closeBtn);
            vi.advanceTimersByTime(300);
            expect(cb).toHaveBeenCalled();
        });

        it('should emit dismiss event', () => {
            vi.useFakeTimers();
            const cb = vi.fn();
            const badge = new FlexBadge(container, { text: 'X', dismissible: true });
            badge.on('dismiss', cb);
            const closeBtn = badge.badgeElement.querySelector('[data-dismiss=true]');
            click(closeBtn);
            vi.advanceTimersByTime(300);
            expect(cb).toHaveBeenCalled();
        });
    });

    describe('Cleanup', () => {
        it('should destroy component', () => {
            const badge = new FlexBadge(container, { text: 'X' });
            expect(() => badge.destroy()).not.toThrow();
        });
    });
});
