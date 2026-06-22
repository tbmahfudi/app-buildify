import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import FlexDrawer from '../../frontend/assets/js/components/flex-drawer.js';
import { createTestContainer, cleanupTestContainer, click, wait } from '../helpers/test-utils.js';

describe('FlexDrawer', () => {
    let container;

    beforeEach(() => { container = createTestContainer(); });
    afterEach(() => {
        cleanupTestContainer(container);
        document.body.innerHTML = '';
    });

    describe('Initialization', () => {
        it('should create drawer with closed state', () => {
            const drawer = new FlexDrawer(container);
            expect(drawer.state.open).toBe(false);
        });

        it('should render backdrop element', () => {
            const drawer = new FlexDrawer(container);
            expect(drawer.backdropElement).toBeTruthy();
        });

        it('should render drawer element', () => {
            const drawer = new FlexDrawer(container);
            expect(drawer.drawerElement).toBeTruthy();
        });

        it('should render title when provided', () => {
            const drawer = new FlexDrawer(container, { title: 'My Drawer' });
            expect(drawer.drawerElement.textContent).toContain('My Drawer');
        });
    });

    describe('Open/Close', () => {
        it('should open drawer', () => {
            const drawer = new FlexDrawer(container);
            drawer.open();
            expect(drawer.state.open).toBe(true);
        });

        it('should close drawer', () => {
            const drawer = new FlexDrawer(container);
            drawer.open();
            drawer.close();
            expect(drawer.state.open).toBe(false);
        });

        it('should emit open event', () => {
            const cb = vi.fn();
            const drawer = new FlexDrawer(container);
            drawer.on('open', cb);
            drawer.open();
            expect(cb).toHaveBeenCalled();
        });

        it('should emit close event', () => {
            const cb = vi.fn();
            const drawer = new FlexDrawer(container);
            drawer.on('close', cb);
            drawer.open();
            drawer.close();
            expect(cb).toHaveBeenCalled();
        });

        it('should call onOpen callback', () => {
            const cb = vi.fn();
            const drawer = new FlexDrawer(container, { onOpen: cb });
            drawer.open();
            expect(cb).toHaveBeenCalled();
        });

        it('should call onClose callback', () => {
            const cb = vi.fn();
            const drawer = new FlexDrawer(container, { onClose: cb });
            drawer.open();
            drawer.close();
            expect(cb).toHaveBeenCalled();
        });

        it('should toggle open state', () => {
            const drawer = new FlexDrawer(container);
            drawer.toggle();
            expect(drawer.state.open).toBe(true);
            drawer.toggle();
            expect(drawer.state.open).toBe(false);
        });
    });

    describe('Positions', () => {
        it('should default to right position', () => {
            const drawer = new FlexDrawer(container);
            expect(drawer.options.position).toBe('right');
        });

        it('should accept left position', () => {
            const drawer = new FlexDrawer(container, { position: 'left' });
            expect(drawer.options.position).toBe('left');
        });
    });

    describe('Backdrop dismiss', () => {
        it('should close on backdrop click when backdropDismiss is true', () => {
            const drawer = new FlexDrawer(container, { backdropDismiss: true });
            drawer.open();
            click(drawer.backdropElement);
            expect(drawer.state.open).toBe(false);
        });

        it('should not close on backdrop click when backdropDismiss is false', () => {
            const drawer = new FlexDrawer(container, { backdropDismiss: false });
            drawer.open();
            click(drawer.backdropElement);
            expect(drawer.state.open).toBe(true);
        });
    });

    describe('Cleanup', () => {
        it('should destroy component', () => {
            const drawer = new FlexDrawer(container);
            expect(() => drawer.destroy()).not.toThrow();
        });
    });
});
