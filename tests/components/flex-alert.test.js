import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import FlexAlert from '../../frontend/assets/js/components/flex-alert.js';
import { createTestContainer, cleanupTestContainer, click } from '../helpers/test-utils.js';

describe('FlexAlert', () => {
    let container;

    beforeEach(() => { container = createTestContainer(); });
    afterEach(() => { cleanupTestContainer(container); vi.useRealTimers(); });

    describe('Initialization', () => {
        it('should create alert element', () => {
            const alert = new FlexAlert(container, { message: 'Hello' });
            expect(alert.alertElement).toBeTruthy();
        });

        it('should render message', () => {
            const alert = new FlexAlert(container, { message: 'Test message' });
            expect(alert.alertElement.textContent).toContain('Test message');
        });

        it('should render title when provided', () => {
            const alert = new FlexAlert(container, { title: 'Warning', message: 'Msg' });
            expect(alert.alertElement.textContent).toContain('Warning');
        });
    });

    describe('Variants', () => {
        it('should apply info variant by default', () => {
            const alert = new FlexAlert(container, { message: 'Info' });
            expect(alert.alertElement.className).toContain('bg-blue-50');
        });

        it('should apply success variant', () => {
            const alert = new FlexAlert(container, { variant: 'success', message: 'Done' });
            expect(alert.alertElement.className).toContain('bg-green-50');
        });

        it('should apply error variant', () => {
            const alert = new FlexAlert(container, { variant: 'error', message: 'Fail' });
            expect(alert.alertElement.className).toContain('bg-red-50');
        });

        it('should apply warning variant', () => {
            const alert = new FlexAlert(container, { variant: 'warning', message: 'Warn' });
            expect(alert.alertElement.className).toContain('bg-amber-50');
        });
    });

    describe('Dismissible', () => {
        it('should show close button by default', () => {
            const alert = new FlexAlert(container, { message: 'X' });
            const closeBtn = alert.alertElement.querySelector('button');
            expect(closeBtn).toBeTruthy();
        });

        it('should hide close button when dismissible is false', () => {
            const alert = new FlexAlert(container, { message: 'X', dismissible: false });
            const closeBtn = alert.alertElement.querySelector('button');
            expect(closeBtn).toBeNull();
        });

        it('should dismiss on close button click', () => {
            vi.useFakeTimers();
            const cb = vi.fn();
            const alert = new FlexAlert(container, { message: 'X', onDismiss: cb });
            const closeBtn = alert.alertElement.querySelector('[data-dismiss=true]');
            click(closeBtn);
            vi.advanceTimersByTime(400);
            expect(cb).toHaveBeenCalled();
        });

        it('should emit dismiss event', () => {
            vi.useFakeTimers();
            const cb = vi.fn();
            const alert = new FlexAlert(container, { message: 'X' });
            alert.on('dismiss', cb);
            const closeBtn = alert.alertElement.querySelector('[data-dismiss=true]');
            click(closeBtn);
            vi.advanceTimersByTime(400);
            expect(cb).toHaveBeenCalled();
        });
    });

    describe('Auto dismiss', () => {
        it('should auto dismiss after timeout', () => {
            vi.useFakeTimers();
            const cb = vi.fn();
            const alert = new FlexAlert(container, {
                message: 'X',
                autoDismiss: true,
                dismissTimeout: 1000,
                onDismiss: cb
            });
            vi.advanceTimersByTime(1400);
            expect(cb).toHaveBeenCalled();
        });
    });

    describe('Cleanup', () => {
        it('should destroy component', () => {
            const alert = new FlexAlert(container, { message: 'X' });
            expect(() => alert.destroy()).not.toThrow();
        });
    });
});
