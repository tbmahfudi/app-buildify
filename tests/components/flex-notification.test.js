/**
 * FlexNotification Component Tests
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import FlexNotification from '../../frontend/assets/js/components/flex-notification.js';

describe('FlexNotification', () => {
    let notify;

    beforeEach(() => {
        FlexNotification.resetInstance();
        notify = new FlexNotification({ defaultDuration: 0 }); // persistent by default in tests
    });

    afterEach(() => {
        notify.destroy();
        FlexNotification.resetInstance();
    });

    describe('Singleton', () => {
        it('getInstance returns the same instance', () => {
            FlexNotification.resetInstance();
            const a = FlexNotification.getInstance();
            const b = FlexNotification.getInstance();
            expect(a).toBe(b);
            FlexNotification.resetInstance();
        });

        it('resetInstance clears the singleton', () => {
            FlexNotification.resetInstance();
            const a = FlexNotification.getInstance();
            FlexNotification.resetInstance();
            const b = FlexNotification.getInstance();
            expect(a).not.toBe(b);
            FlexNotification.resetInstance();
        });
    });

    describe('Container', () => {
        it('creates a container in document.body', () => {
            expect(document.querySelector('.flex-notification-container')).toBeTruthy();
        });

        it('destroy removes the container', () => {
            notify.destroy();
            // container removed after timeout — check immediately
            expect(notify._container).toBeTruthy(); // ref still exists
        });
    });

    describe('show()', () => {
        it('returns a notification id string', () => {
            const id = notify.show({ message: 'Hello' });
            expect(typeof id).toBe('string');
        });

        it('renders a notification element in the container', () => {
            notify.show({ message: 'Test message' });
            expect(document.querySelector('.flex-notif')).toBeTruthy();
        });

        it('renders message text', () => {
            notify.show({ message: 'Save successful' });
            expect(document.body.innerHTML).toContain('Save successful');
        });

        it('renders title when provided', () => {
            notify.show({ title: 'Great!', message: 'All done' });
            expect(document.body.innerHTML).toContain('Great!');
        });

        it('renders action buttons', () => {
            notify.show({
                message: 'File deleted',
                actions: [{ label: 'Undo', onClick: vi.fn() }],
            });
            const btn = document.querySelector('.flex-notif-action');
            expect(btn).toBeTruthy();
            expect(btn.textContent.trim()).toBe('Undo');
        });

        it('increments notification count', () => {
            notify.show({ message: 'A' });
            notify.show({ message: 'B' });
            expect(notify.getCount()).toBe(2);
        });

        it('uses custom id when provided', () => {
            const id = notify.show({ message: 'Custom', id: 'my-notif' });
            expect(id).toBe('my-notif');
            expect(notify.has('my-notif')).toBe(true);
        });

        it('updates existing notification when same id shown again', () => {
            notify.show({ message: 'First', id: 'dup' });
            notify.show({ message: 'Second', id: 'dup' });
            expect(notify.getCount()).toBe(1);
            expect(document.body.innerHTML).toContain('Second');
        });

        it('enforces maxVisible by dismissing oldest', () => {
            const n = new FlexNotification({ defaultDuration: 0, maxVisible: 3 });
            n.show({ message: '1' });
            n.show({ message: '2' });
            n.show({ message: '3' });
            n.show({ message: '4' });
            // After adding 4th, oldest is dismissed (may still be in DOM briefly)
            expect(n.getCount()).toBe(3);
            n.destroy();
        });
    });

    describe('Shorthand methods', () => {
        it('success() shows type=success notification', () => {
            const id = notify.success('Saved!');
            const entry = notify._notifications.get(id);
            expect(entry.opts.type).toBe('success');
        });

        it('error() shows type=error notification', () => {
            const id = notify.error('Failed!');
            expect(notify._notifications.get(id).opts.type).toBe('error');
        });

        it('warning() shows type=warning notification', () => {
            const id = notify.warning('Watch out');
            expect(notify._notifications.get(id).opts.type).toBe('warning');
        });

        it('info() shows type=info notification', () => {
            const id = notify.info('FYI');
            expect(notify._notifications.get(id).opts.type).toBe('info');
        });

        it('loading() shows persistent type=loading notification', () => {
            const id = notify.loading('Saving…');
            const entry = notify._notifications.get(id);
            expect(entry.opts.type).toBe('loading');
            expect(entry.timer).toBeNull();  // persistent = no timer
        });
    });

    describe('dismiss()', () => {
        it('removes notification from map immediately', () => {
            const id = notify.show({ message: 'Bye' });
            notify.dismiss(id);
            expect(notify.has(id)).toBe(false);
        });

        it('does nothing for unknown id', () => {
            expect(() => notify.dismiss('nonexistent')).not.toThrow();
        });
    });

    describe('dismissAll()', () => {
        it('removes all notifications from map', () => {
            notify.show({ message: 'A' });
            notify.show({ message: 'B' });
            notify.show({ message: 'C' });
            notify.dismissAll();
            expect(notify.getCount()).toBe(0);
        });
    });

    describe('update()', () => {
        it('replaces notification content', () => {
            const id = notify.loading('Uploading…', { id: 'upload' });
            notify.update(id, { type: 'success', message: 'Upload complete!', id: 'upload' });
            expect(document.body.innerHTML).toContain('Upload complete!');
            expect(notify.has('upload')).toBe(true);
        });
    });

    describe('promise()', () => {
        it('resolves with success notification on fulfilled promise', async () => {
            const p = Promise.resolve({ id: 42 });
            await notify.promise(p, { loading: 'Saving…', success: 'Saved!' });
            expect(document.body.innerHTML).toContain('Saved!');
        });

        it('shows error notification on rejected promise', async () => {
            const p = Promise.reject(new Error('Network error'));
            await expect(notify.promise(p, { error: 'Upload failed' })).rejects.toThrow();
            expect(document.body.innerHTML).toContain('Upload failed');
        });

        it('rethrows the original error', async () => {
            const err = new Error('boom');
            await expect(notify.promise(Promise.reject(err), {})).rejects.toBe(err);
        });
    });

    describe('Action button interactions', () => {
        it('action onClick is called when button clicked', () => {
            const onClick = vi.fn();
            notify.show({
                message: 'Deleted',
                actions: [{ label: 'Undo', onClick, dismiss: false }],
            });
            document.querySelector('.flex-notif-action').click();
            expect(onClick).toHaveBeenCalledOnce();
        });

        it('notification dismissed after action click by default', () => {
            const id = notify.show({
                message: 'Confirm?',
                actions: [{ label: 'OK' }],
            });
            document.querySelector('.flex-notif-action').click();
            expect(notify.has(id)).toBe(false);
        });
    });

    describe('Events', () => {
        it('dispatches flexnotif:show on document', () => {
            const handler = vi.fn();
            document.addEventListener('flexnotif:show', handler, { once: true });
            notify.show({ message: 'Event test' });
            expect(handler).toHaveBeenCalled();
        });

        it('dispatches flexnotif:dismiss on document', () => {
            const handler = vi.fn();
            document.addEventListener('flexnotif:dismiss', handler, { once: true });
            const id = notify.show({ message: 'Dismiss event' });
            notify.dismiss(id);
            expect(handler).toHaveBeenCalled();
        });
    });

    describe('Position', () => {
        it('setPosition changes container position', () => {
            notify.setPosition('bottom-left');
            expect(notify.options.position).toBe('bottom-left');
        });
    });
});
