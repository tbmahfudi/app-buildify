import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import FlexPagination from '../../frontend/assets/js/components/flex-pagination.js';
import { createTestContainer, cleanupTestContainer, click } from '../helpers/test-utils.js';

describe('FlexPagination', () => {
    let container;

    beforeEach(() => { container = createTestContainer(); });
    afterEach(() => { cleanupTestContainer(container); });

    describe('Initialization', () => {
        it('should create pagination with defaults', () => {
            const pager = new FlexPagination(container, { totalItems: 100 });
            expect(pager.state.currentPage).toBe(1);
            expect(pager.state.itemsPerPage).toBe(10);
        });

        it('should calculate total pages correctly', () => {
            const pager = new FlexPagination(container, { totalItems: 100, itemsPerPage: 10 });
            expect(pager.state.totalPages).toBe(10);
        });

        it('should handle zero items', () => {
            const pager = new FlexPagination(container, { totalItems: 0 });
            expect(pager.state.totalPages).toBe(1);
        });
    });

    describe('Rendering', () => {
        it('should render page buttons', () => {
            const pager = new FlexPagination(container, { totalItems: 50, itemsPerPage: 10 });
            const buttons = container.querySelectorAll('button');
            expect(buttons.length).toBeGreaterThan(0);
        });

        it('should render page info when showInfo is true', () => {
            const pager = new FlexPagination(container, { totalItems: 50, showInfo: true });
            expect(container.textContent).toMatch(/\d/);
        });
    });

    describe('Navigation', () => {
        it('should call onChange when navigating', () => {
            const cb = vi.fn();
            const pager = new FlexPagination(container, { totalItems: 50, onChange: cb });
            pager.goToPage(2);
            expect(cb).toHaveBeenCalledWith(2);
        });

        it('should emit pageChange event on navigation', () => {
            const cb = vi.fn();
            const pager = new FlexPagination(container, { totalItems: 50 });
            pager.on('pageChange', cb);
            pager.goToPage(2);
            expect(cb).toHaveBeenCalled();
        });

        it('should not go below page 1', () => {
            const pager = new FlexPagination(container, { totalItems: 50 });
            pager.goToPage(-1);
            expect(pager.state.currentPage).toBe(1);
        });

        it('should not exceed total pages', () => {
            const pager = new FlexPagination(container, { totalItems: 50, itemsPerPage: 10 });
            pager.goToPage(100);
            expect(pager.state.currentPage).toBe(1);
        });

        it('should go to next page with nextPage()', () => {
            const pager = new FlexPagination(container, { totalItems: 50 });
            pager.nextPage();
            expect(pager.state.currentPage).toBe(2);
        });

        it('should go to previous page with previousPage()', () => {
            const pager = new FlexPagination(container, { totalItems: 50, currentPage: 3 });
            pager.previousPage();
            expect(pager.state.currentPage).toBe(2);
        });
    });

    describe('API methods', () => {
        it('should return current page with getCurrentPage()', () => {
            const pager = new FlexPagination(container, { totalItems: 50, currentPage: 3 });
            expect(pager.getCurrentPage()).toBe(3);
        });

        it('should return total pages with getTotalPages()', () => {
            const pager = new FlexPagination(container, { totalItems: 50, itemsPerPage: 10 });
            expect(pager.getTotalPages()).toBe(5);
        });
    });

    describe('Cleanup', () => {
        it('should destroy component', () => {
            const pager = new FlexPagination(container, { totalItems: 50 });
            expect(() => pager.destroy()).not.toThrow();
        });
    });
});
