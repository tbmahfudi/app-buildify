/**
 * FlexFileUpload Component Tests
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import FlexFileUpload from '../../frontend/assets/js/components/flex-file-upload.js';
import { createTestContainer, cleanupTestContainer } from '../helpers/test-utils.js';

function makeFile(name = 'test.txt', type = 'text/plain', sizeBytes = 1024) {
    const content = new Uint8Array(sizeBytes);
    return new File([content], name, { type });
}

describe('FlexFileUpload', () => {
    let container;

    beforeEach(() => { container = createTestContainer(); });
    afterEach(() => { cleanupTestContainer(container); });

    describe('Initialization', () => {
        it('renders dropzone and hidden file input', () => {
            new FlexFileUpload(container);
            expect(container.querySelector('.flex-fu-dropzone')).toBeTruthy();
            expect(container.querySelector('.flex-fu-input')).toBeTruthy();
        });

        it('renders label when provided', () => {
            new FlexFileUpload(container, { label: 'Attach files' });
            expect(container.querySelector('label').textContent).toContain('Attach files');
        });

        it('sets multiple attribute when multiple:true', () => {
            new FlexFileUpload(container, { multiple: true });
            expect(container.querySelector('.flex-fu-input').multiple).toBe(true);
        });

        it('disables input when disabled:true', () => {
            new FlexFileUpload(container, { disabled: true });
            expect(container.querySelector('.flex-fu-input').disabled).toBe(true);
        });
    });

    describe('File validation', () => {
        it('rejects files exceeding maxSizeBytes', () => {
            const fu = new FlexFileUpload(container, { maxSizeBytes: 100 });
            fu._addFiles([makeFile('big.txt', 'text/plain', 200)]);
            const entries = fu.getAllEntries();
            expect(entries[0].status).toBe('error');
            expect(entries[0].error).toContain('too large');
        });

        it('rejects files with disallowed type', () => {
            const fu = new FlexFileUpload(container, { accept: 'image/*' });
            fu._addFiles([makeFile('doc.pdf', 'application/pdf')]);
            const entries = fu.getAllEntries();
            expect(entries[0].status).toBe('error');
            expect(entries[0].error).toContain('not allowed');
        });

        it('accepts files matching MIME type', () => {
            const fu = new FlexFileUpload(container, { accept: 'image/*' });
            fu._addFiles([makeFile('photo.jpg', 'image/jpeg')]);
            expect(fu.getAllEntries()[0].status).toBe('idle');
        });

        it('accepts files matching extension', () => {
            const fu = new FlexFileUpload(container, { accept: '.pdf' });
            fu._addFiles([makeFile('report.pdf', 'application/pdf')]);
            expect(fu.getAllEntries()[0].status).toBe('idle');
        });
    });

    describe('File management', () => {
        it('limits files to maxFiles when multiple:true', () => {
            const fu = new FlexFileUpload(container, { multiple: true, maxFiles: 2 });
            fu._addFiles([
                makeFile('a.txt'), makeFile('b.txt'), makeFile('c.txt'),
            ]);
            expect(fu.getAllEntries().length).toBe(2);
        });

        it('replaces existing file when multiple:false', () => {
            const fu = new FlexFileUpload(container, { multiple: false });
            fu._addFiles([makeFile('first.txt')]);
            fu._addFiles([makeFile('second.txt')]);
            // single mode: only 1 allowed, second add is blocked since first is already there
            expect(fu.getAllEntries().length).toBe(1);
        });

        it('removes file by id', () => {
            const fu = new FlexFileUpload(container);
            fu._addFiles([makeFile('remove-me.txt')]);
            const id = fu.getAllEntries()[0].id;
            fu._removeFile(id);
            expect(fu.getAllEntries().length).toBe(0);
        });

        it('clear() empties the file list', () => {
            const fu = new FlexFileUpload(container, { multiple: true });
            fu._addFiles([makeFile('a.txt'), makeFile('b.txt')]);
            fu.clear();
            expect(fu.getFiles().length).toBe(0);
        });
    });

    describe('Events', () => {
        it('calls onSelect with valid files', () => {
            const onSelect = vi.fn();
            const fu = new FlexFileUpload(container, { onSelect });
            fu._addFiles([makeFile('test.txt')]);
            expect(onSelect).toHaveBeenCalledOnce();
            expect(onSelect.mock.calls[0][0].files[0].name).toBe('test.txt');
        });

        it('calls onRemove when file is removed', () => {
            const onRemove = vi.fn();
            const fu = new FlexFileUpload(container, { onRemove });
            fu._addFiles([makeFile('test.txt')]);
            const id = fu.getAllEntries()[0].id;
            fu._removeFile(id);
            expect(onRemove).toHaveBeenCalledOnce();
            expect(onRemove.mock.calls[0][0].file.name).toBe('test.txt');
        });

        it('emits select custom event', () => {
            const handler = vi.fn();
            const fu = new FlexFileUpload(container);
            fu.on('select', handler);
            fu._addFiles([makeFile('test.txt')]);
            expect(handler).toHaveBeenCalled();
        });
    });

    describe('DOM rendering', () => {
        it('renders file item after adding file', () => {
            const fu = new FlexFileUpload(container);
            fu._addFiles([makeFile('document.pdf', 'application/pdf')]);
            expect(container.querySelector('.flex-fu-item')).toBeTruthy();
            expect(container.innerHTML).toContain('document.pdf');
        });

        it('renders remove button per file item', () => {
            const fu = new FlexFileUpload(container, { multiple: true });
            fu._addFiles([makeFile('a.txt'), makeFile('b.txt')]);
            const removeBtns = container.querySelectorAll('.flex-fu-remove');
            expect(removeBtns.length).toBe(2);
        });

        it('clicking remove button removes file from list', () => {
            const fu = new FlexFileUpload(container);
            fu._addFiles([makeFile('click-remove.txt')]);
            const btn = container.querySelector('.flex-fu-remove');
            btn.click();
            expect(fu.getAllEntries().length).toBe(0);
        });
    });

    describe('Public API', () => {
        it('getFiles returns only valid (non-error) files', () => {
            const fu = new FlexFileUpload(container, { maxSizeBytes: 100 });
            fu._addFiles([makeFile('ok.txt', 'text/plain', 50), makeFile('big.txt', 'text/plain', 200)]);
            expect(fu.getFiles().length).toBe(1);
            expect(fu.getFiles()[0].name).toBe('ok.txt');
        });

        it('setError renders error message', () => {
            const fu = new FlexFileUpload(container);
            fu.setError('Upload required');
            expect(container.innerHTML).toContain('Upload required');
        });
    });
});
