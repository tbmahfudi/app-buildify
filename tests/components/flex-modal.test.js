import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import FlexModal from '../../frontend/assets/js/components/flex-modal.js';
import { click } from '../helpers/test-utils.js';

vi.mock('../../frontend/assets/js/rbac.js', () => ({
    hasPermission: vi.fn().mockReturnValue(true)
}));

describe('FlexModal', () => {
    afterEach(() => {
        vi.useRealTimers();
        document.body.innerHTML = '';
        FlexModal.openModals = [];
    });

    describe('Initialization', () => {
        it('should create modal with closed state', () => {
            const modal = new FlexModal({ title: 'Test Modal' });
            expect(modal.state.isOpen).toBe(false);
            modal.destroy();
        });

        it('should render title in DOM', () => {
            const modal = new FlexModal({ title: 'Hello World' });
            expect(document.body.innerHTML).toContain('Hello World');
            modal.destroy();
        });
    });

    describe('Show', () => {
        it('should show modal', () => {
            vi.useFakeTimers();
            const modal = new FlexModal({ title: 'Test' });
            modal.show();
            expect(modal.state.isOpen).toBe(true);
            modal.destroy();
        });

        it('should call onShow callback', () => {
            vi.useFakeTimers();
            const cb = vi.fn();
            const modal = new FlexModal({ title: 'Test', onShow: cb });
            modal.show();
            expect(cb).toHaveBeenCalled();
            modal.destroy();
        });
    });

    describe('Hide', () => {
        it('should hide modal', () => {
            vi.useFakeTimers();
            const modal = new FlexModal({ title: 'Test' });
            modal.show();
            modal.hide();
            vi.advanceTimersByTime(400);
            expect(modal.state.isOpen).toBe(false);
        });

        it('should call onHide callback', () => {
            vi.useFakeTimers();
            const cb = vi.fn();
            const modal = new FlexModal({ title: 'Test', onHide: cb });
            modal.show();
            modal.hide();
            expect(cb).toHaveBeenCalled();
        });
    });

    describe('Sizes', () => {
        it('should default to md size', () => {
            const modal = new FlexModal();
            expect(modal.options.size).toBe('md');
            modal.destroy();
        });

        it('should accept sm size', () => {
            const modal = new FlexModal({ size: 'sm' });
            expect(modal.options.size).toBe('sm');
            modal.destroy();
        });

        it('should accept lg size', () => {
            const modal = new FlexModal({ size: 'lg' });
            expect(modal.options.size).toBe('lg');
            modal.destroy();
        });
    });

    describe('Backdrop dismiss', () => {
        it('should close on backdrop click when backdropDismiss is true', () => {
            vi.useFakeTimers();
            const modal = new FlexModal({ backdropDismiss: true });
            modal.show();
            click(modal.elements.backdrop);
            vi.advanceTimersByTime(400);
            expect(modal.state.isOpen).toBe(false);
        });

        it('should not close on backdrop click when backdropDismiss is false', () => {
            vi.useFakeTimers();
            const modal = new FlexModal({ backdropDismiss: false });
            modal.show();
            click(modal.elements.backdrop);
            vi.advanceTimersByTime(400);
            expect(modal.state.isOpen).toBe(true);
            modal.destroy();
        });
    });

    describe('Footer actions', () => {
        it('should render footer action buttons', () => {
            vi.useFakeTimers();
            const modal = new FlexModal({
                footerActions: [
                    { label: 'Save', onClick: vi.fn() },
                    { label: 'Cancel', onClick: vi.fn() }
                ]
            });
            modal.show();
            expect(document.body.innerHTML).toContain('Save');
            expect(document.body.innerHTML).toContain('Cancel');
            modal.destroy();
        });
    });

    describe('Cleanup', () => {
        it('should destroy modal without throwing', () => {
            const modal = new FlexModal({ title: 'Test' });
            expect(() => modal.destroy()).not.toThrow();
        });
    });
});
