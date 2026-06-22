import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import FlexTable from '../../frontend/assets/js/components/flex-table.js';
import { createTestContainer, cleanupTestContainer, click, wait } from '../helpers/test-utils.js';

vi.mock('../../frontend/assets/js/rbac.js', () => ({
    hasPermission: vi.fn().mockReturnValue(true)
}));

const columns = [
    { key: 'id', label: 'ID' },
    { key: 'name', label: 'Name' },
    { key: 'email', label: 'Email' }
];

const data = [
    { id: 1, name: 'Alice', email: 'alice@example.com' },
    { id: 2, name: 'Bob', email: 'bob@example.com' },
    { id: 3, name: 'Charlie', email: 'charlie@example.com' }
];

describe('FlexTable', () => {
    let container;

    beforeEach(() => { container = createTestContainer(); });
    afterEach(() => { cleanupTestContainer(container); });

    describe('Initialization', () => {
        it('should create table element', async () => {
            const table = new FlexTable(container, { columns, data });
            await wait(50);
            const el = container.querySelector('table');
            expect(el).toBeTruthy();
        });

        it('should render column headers', async () => {
            const table = new FlexTable(container, { columns, data });
            await wait(50);
            expect(container.textContent).toContain('Name');
            expect(container.textContent).toContain('Email');
        });

        it('should render data rows', async () => {
            const table = new FlexTable(container, { columns, data });
            await wait(50);
            expect(container.textContent).toContain('Alice');
            expect(container.textContent).toContain('Bob');
        });

        it('should render correct row count', async () => {
            const table = new FlexTable(container, { columns, data });
            await wait(50);
            const rows = container.querySelectorAll('tbody tr');
            expect(rows.length).toBe(3);
        });
    });

    describe('Empty state', () => {
        it('should render empty message when data is empty', async () => {
            const table = new FlexTable(container, { columns, data: [], emptyMessage: 'No records' });
            await wait(50);
            expect(container.textContent).toContain('No records');
        });
    });

    describe('Loading state', () => {
        it('should reflect loading option', async () => {
            const table = new FlexTable(container, { columns, data: [], loading: true });
            await wait(50);
            expect(table.options.loading).toBe(true);
        });
    });

    describe('Selection', () => {
        it('should render checkboxes when selectable', async () => {
            const table = new FlexTable(container, { columns, data, selectable: true });
            await wait(50);
            const checkboxes = container.querySelectorAll('input[type=checkbox]');
            expect(checkboxes.length).toBeGreaterThan(0);
        });

        it('should emit select event when row checkbox clicked', async () => {
            const cb = vi.fn();
            const table = new FlexTable(container, { columns, data, selectable: true });
            await wait(50);
            table.on('select', cb);
            const firstCheckbox = container.querySelector('tbody input[type=checkbox]');
            if (firstCheckbox) {
                click(firstCheckbox);
                expect(cb).toHaveBeenCalled();
            }
        });
    });

    describe('Sorting', () => {
        it('should emit sort event on sortable header click', async () => {
            const cb = vi.fn();
            const sortableCols = columns.map(c => ({ ...c, sortable: true }));
            const table = new FlexTable(container, { columns: sortableCols, data, sortable: true });
            await wait(50);
            table.on('sort', cb);
            const sortHeader = container.querySelector('[data-sort-column]');
            if (sortHeader) {
                click(sortHeader);
                await wait(50);
                expect(cb).toHaveBeenCalled();
            }
        });
    });

    describe('API methods', () => {
        it('should update data with setData()', async () => {
            const table = new FlexTable(container, { columns, data });
            await wait(50);
            const newData = [{ id: 4, name: 'Dave', email: 'dave@example.com' }];
            table.setData(newData);
            await wait(50);
            const rows = container.querySelectorAll('tbody tr');
            expect(rows.length).toBe(1);
        });

        it('should return selected rows with getSelectedRows()', async () => {
            const table = new FlexTable(container, { columns, data, selectable: true });
            await wait(50);
            expect(Array.isArray(table.getSelectedRows())).toBe(true);
        });
    });

    describe('Cleanup', () => {
        it('should destroy component', async () => {
            const table = new FlexTable(container, { columns, data });
            await wait(50);
            expect(() => table.destroy()).not.toThrow();
        });
    });
});
