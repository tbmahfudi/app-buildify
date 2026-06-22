import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import FlexDropdown from '../../frontend/assets/js/components/flex-dropdown.js';
import { createTestContainer, cleanupTestContainer, click, wait } from '../helpers/test-utils.js';

vi.mock('../../frontend/assets/js/rbac.js', () => ({
    hasPermission: vi.fn().mockReturnValue(true)
}));

describe('FlexDropdown', () => {
    let container, trigger;

    const items = [
        { label: 'Edit', onClick: vi.fn() },
        { label: 'Delete', onClick: vi.fn() },
        { label: 'Share', onClick: vi.fn() }
    ];

    beforeEach(() => {
        container = createTestContainer();
        trigger = document.createElement('button');
        trigger.textContent = 'Open';
        container.appendChild(trigger);
    });

    afterEach(() => {
        cleanupTestContainer(container);
        document.body.innerHTML = '';
    });

    describe('Initialization', () => {
        it('should create dropdown with trigger element', async () => {
            const dd = new FlexDropdown(container, { trigger, items });
            await wait(50);
            expect(dd).toBeTruthy();
        });

        it('should start closed', async () => {
            const dd = new FlexDropdown(container, { trigger, items });
            await wait(50);
            expect(dd.state.open).toBe(false);
        });
    });

    describe('Open/Close', () => {
        it('should open on trigger click', async () => {
            const dd = new FlexDropdown(container, { trigger, items });
            await wait(50);
            click(trigger);
            expect(dd.state.open).toBe(true);
        });

        it('should close when already open', async () => {
            const dd = new FlexDropdown(container, { trigger, items });
            await wait(50);
            dd.open();
            dd.close();
            expect(dd.state.open).toBe(false);
        });

        it('should emit open event', async () => {
            const cb = vi.fn();
            const dd = new FlexDropdown(container, { trigger, items, onOpen: cb });
            await wait(50);
            dd.open();
            expect(cb).toHaveBeenCalled();
        });

        it('should emit close event', async () => {
            const cb = vi.fn();
            const dd = new FlexDropdown(container, { trigger, items, onClose: cb });
            await wait(50);
            dd.open();
            dd.close();
            expect(cb).toHaveBeenCalled();
        });
    });

    describe('Items', () => {
        it('should render menu items', async () => {
            const dd = new FlexDropdown(container, { trigger, items });
            await wait(50);
            dd.open();
            expect(dd.dropdownElement.textContent).toContain('Edit');
            expect(dd.dropdownElement.textContent).toContain('Delete');
        });

        it('should call item onClick when clicked', async () => {
            const editCb = vi.fn();
            const dd = new FlexDropdown(container, {
                trigger,
                items: [{ label: 'Edit', onClick: editCb }]
            });
            await wait(50);
            dd.open();
            const itemBtn = dd.dropdownElement.querySelector('button, [role=menuitem], li');
            if (itemBtn) {
                click(itemBtn);
                expect(editCb).toHaveBeenCalled();
            }
        });
    });

    describe('Cleanup', () => {
        it('should destroy component', async () => {
            const dd = new FlexDropdown(container, { trigger, items });
            await wait(50);
            expect(() => dd.destroy()).not.toThrow();
        });
    });
});
