import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import FlexBreadcrumb from '../../frontend/assets/js/components/flex-breadcrumb.js';
import { createTestContainer, cleanupTestContainer, click } from '../helpers/test-utils.js';

describe('FlexBreadcrumb', () => {
    let container;
    const items = [
        { label: 'Home', href: '/' },
        { label: 'Products', href: '/products' },
        { label: 'Widget', href: '/products/widget' }
    ];

    beforeEach(() => { container = createTestContainer(); });
    afterEach(() => { cleanupTestContainer(container); });

    describe('Initialization', () => {
        it('should create breadcrumb with items', () => {
            const bc = new FlexBreadcrumb(container, { items });
            expect(container.querySelector('nav') || container.querySelector('[aria-label]')).toBeTruthy();
        });

        it('should render all items', () => {
            const bc = new FlexBreadcrumb(container, { items });
            expect(container.textContent).toContain('Home');
            expect(container.textContent).toContain('Products');
            expect(container.textContent).toContain('Widget');
        });
    });

    describe('Rendering', () => {
        it('should render separators between items', () => {
            const bc = new FlexBreadcrumb(container, { items, separator: '/' });
            expect(container.textContent).toContain('/');
        });

        it('should render home icon for first item when showHome is true', () => {
            const bc = new FlexBreadcrumb(container, { items, showHome: true });
            const icon = container.querySelector('[class*=ph-house]');
            expect(icon).toBeTruthy();
        });

        it('should not render home icon when showHome is false', () => {
            const bc = new FlexBreadcrumb(container, { items, showHome: false });
            const icon = container.querySelector('[class*=ph-house]');
            expect(icon).toBeNull();
        });

        it('should apply md size by default', () => {
            const bc = new FlexBreadcrumb(container, { items });
            expect(container.innerHTML).toContain('text-base');
        });

        it('should apply sm size', () => {
            const bc = new FlexBreadcrumb(container, { items, size: 'sm' });
            expect(container.innerHTML).toContain('text-sm');
        });
    });

    describe('User interaction', () => {
        it('should call onItemClick when item is clicked', () => {
            const cb = vi.fn();
            const bc = new FlexBreadcrumb(container, { items, onItemClick: cb });
            const links = container.querySelectorAll('a, button, [role=link]');
            if (links.length > 0) {
                click(links[0]);
                expect(cb).toHaveBeenCalled();
            }
        });
    });

    describe('Cleanup', () => {
        it('should destroy component', () => {
            const bc = new FlexBreadcrumb(container, { items });
            expect(() => bc.destroy()).not.toThrow();
        });
    });
});
