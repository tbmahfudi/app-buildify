/**
 * FlexFileUpload Component
 *
 * File drag-and-drop upload with preview, progress, and validation.
 *
 * @version 1.0.0
 */

import BaseComponent from '../core/base-component.js';

export default class FlexFileUpload extends BaseComponent {
    static DEFAULTS = {
        label: null,
        accept: '*/*',               // MIME types or extensions, e.g. 'image/*,.pdf'
        multiple: false,
        maxFiles: 10,
        maxSizeBytes: 10 * 1024 * 1024,  // 10 MB
        disabled: false,
        required: false,
        helperText: null,
        errorMessage: null,
        showPreview: true,           // image thumbnails
        uploadUrl: null,             // if set, auto-upload on select
        uploadHeaders: {},
        onSelect: null,              // (files: File[]) => void
        onUpload: null,              // (file, response) => void
        onError: null,               // (file, error) => void
        onRemove: null,              // (file) => void
    };

    constructor(element, options = {}) {
        super(element, options);
        this.state = {
            ...this.state,
            files: [],       // { file: File, id, status, progress, preview, error }
            dragging: false,
        };
        this.init();
    }

    init() {
        this.render();
        this._bindEvents();
        this.state.initialized = true;
    }

    // ── Rendering ──────────────────────────────────────────────────────────

    render() {
        const { label, disabled, required, helperText, errorMessage, multiple, accept } = this.options;

        this.container.innerHTML = `
            <div class="flex-file-upload w-full" data-flex-file-upload>
                ${label ? `<label class="block text-sm font-medium text-gray-700 mb-1">
                    ${label}${required ? ' <span class="text-red-500">*</span>' : ''}
                </label>` : ''}

                <div class="flex-fu-dropzone relative border-2 border-dashed rounded-xl p-6 text-center transition-colors
                            ${disabled ? 'opacity-50 cursor-not-allowed border-gray-200 bg-gray-50'
                                       : 'border-gray-300 bg-gray-50 hover:border-blue-400 hover:bg-blue-50 cursor-pointer'}
                            ${this.state.dragging ? 'border-blue-500 bg-blue-50' : ''}">
                    <input type="file"
                        class="flex-fu-input absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                        ${multiple ? 'multiple' : ''}
                        accept="${accept}"
                        ${disabled ? 'disabled' : ''}>
                    <div class="pointer-events-none">
                        <i class="ph-duotone ph-cloud-arrow-up text-4xl text-blue-400 mb-2 block"></i>
                        <p class="text-sm font-medium text-gray-700">
                            Drop files here or <span class="text-blue-600">browse</span>
                        </p>
                        <p class="text-xs text-gray-400 mt-1">
                            ${accept !== '*/*' ? accept + ' — ' : ''}max ${this._fmtSize(this.options.maxSizeBytes)}
                            ${multiple ? ` · up to ${this.options.maxFiles} files` : ''}
                        </p>
                    </div>
                </div>

                ${errorMessage ? `<p class="mt-1 text-xs text-red-500">${errorMessage}</p>` : ''}
                ${helperText && !errorMessage ? `<p class="mt-1 text-xs text-gray-500">${helperText}</p>` : ''}

                <div class="flex-fu-list mt-3 space-y-2">
                    ${this.state.files.map(f => this._renderFileItem(f)).join('')}
                </div>
            </div>`;

        this.elements.dropzone = this.container.querySelector('.flex-fu-dropzone');
        this.elements.input    = this.container.querySelector('.flex-fu-input');
        this.elements.list     = this.container.querySelector('.flex-fu-list');
    }

    _renderFileItem(f) {
        const isImg   = f.file.type.startsWith('image/');
        const isError = f.status === 'error';
        const isDone  = f.status === 'done';
        const isUploading = f.status === 'uploading';

        return `
            <div class="flex-fu-item flex items-center gap-3 p-3 rounded-lg border
                        ${isError ? 'border-red-200 bg-red-50' : 'border-gray-200 bg-white'}"
                 data-file-id="${f.id}">
                <div class="flex-shrink-0 w-10 h-10 rounded-lg overflow-hidden bg-gray-100 flex items-center justify-center">
                    ${isImg && f.preview
                        ? `<img src="${f.preview}" class="w-full h-full object-cover">`
                        : `<i class="ph ph-file text-gray-400 text-xl"></i>`}
                </div>
                <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium text-gray-800 truncate">${f.file.name}</p>
                    <p class="text-xs text-gray-400">${this._fmtSize(f.file.size)}</p>
                    ${isUploading ? `
                        <div class="mt-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                            <div class="h-full bg-blue-500 transition-all" style="width:${f.progress}%"></div>
                        </div>` : ''}
                    ${isError ? `<p class="text-xs text-red-500 mt-0.5">${f.error}</p>` : ''}
                </div>
                <div class="flex items-center gap-2 flex-shrink-0">
                    ${isDone ? `<i class="ph ph-check-circle text-green-500"></i>` : ''}
                    ${isError ? `<i class="ph ph-warning-circle text-red-500"></i>` : ''}
                    <button class="flex-fu-remove text-gray-400 hover:text-red-500 transition p-1" data-file-id="${f.id}" aria-label="Remove">
                        <i class="ph ph-trash pointer-events-none"></i>
                    </button>
                </div>
            </div>`;
    }

    // ── Events ─────────────────────────────────────────────────────────────

    _bindEvents() {
        const dz    = this.container.querySelector('.flex-fu-dropzone');
        const input = this.container.querySelector('.flex-fu-input');
        const list  = this.container.querySelector('.flex-fu-list');

        dz?.addEventListener('dragover',  (e) => { e.preventDefault(); this.state.dragging = true;  dz.classList.add('border-blue-500','bg-blue-50'); });
        dz?.addEventListener('dragleave', ()  => { this.state.dragging = false; dz.classList.remove('border-blue-500','bg-blue-50'); });
        dz?.addEventListener('drop',      (e) => {
            e.preventDefault();
            this.state.dragging = false;
            dz.classList.remove('border-blue-500','bg-blue-50');
            if (!this.options.disabled) this._addFiles(Array.from(e.dataTransfer.files));
        });

        input?.addEventListener('change', () => {
            if (input.files.length) this._addFiles(Array.from(input.files));
            input.value = '';
        });

        list?.addEventListener('click', (e) => {
            const btn = e.target.closest('.flex-fu-remove');
            if (btn) this._removeFile(btn.dataset.fileId);
        });
    }

    // ── File handling ──────────────────────────────────────────────────────

    _addFiles(files) {
        const maxFiles = this.options.multiple ? this.options.maxFiles : 1;
        const remaining = maxFiles - this.state.files.length;
        if (remaining <= 0) return;

        const toAdd = files.slice(0, remaining);
        const added = [];
        for (const file of toAdd) {
            const err = this._validate(file);
            const id  = `fu_${Date.now()}_${Math.random().toString(36).slice(2)}`;
            const entry = { file, id, status: err ? 'error' : 'idle', progress: 0, preview: null, error: err };
            this.state.files.push(entry);
            added.push(entry);

            if (!err && file.type.startsWith('image/') && this.options.showPreview) {
                const reader = new FileReader();
                reader.onload = (ev) => {
                    entry.preview = ev.target.result;
                    this._updateList();
                };
                reader.readAsDataURL(file);
            }
        }

        this._updateList();
        const validAdded = added.filter(e => e.status !== 'error').map(e => e.file);
        if (validAdded.length) {
            this.emit('select', { files: validAdded });
            
            if (this.options.uploadUrl) validAdded.forEach(f => this._upload(this.state.files.find(e => e.file === f)));
        }
    }

    _validate(file) {
        if (file.size > this.options.maxSizeBytes)
            return `File too large (max ${this._fmtSize(this.options.maxSizeBytes)})`;
        if (this.options.accept !== '*/*') {
            const types = this.options.accept.split(',').map(s => s.trim());
            const ok = types.some(t => {
                if (t.startsWith('.')) return file.name.toLowerCase().endsWith(t.toLowerCase());
                if (t.endsWith('/*')) return file.type.startsWith(t.slice(0, -1));
                return file.type === t;
            });
            if (!ok) return `File type not allowed`;
        }
        return null;
    }

    _removeFile(id) {
        const entry = this.state.files.find(f => f.id === id);
        if (!entry) return;
        this.state.files = this.state.files.filter(f => f.id !== id);
        this._updateList();
        this.emit('remove', { file: entry.file });
        
    }

    _updateList() {
        const list = this.container.querySelector('.flex-fu-list');
        if (list) list.innerHTML = this.state.files.map(f => this._renderFileItem(f)).join('');
    }

    async _upload(entry) {
        if (!entry || entry.status === 'error') return;
        entry.status   = 'uploading';
        entry.progress = 0;
        this._updateList();

        const formData = new FormData();
        formData.append('file', entry.file);

        return new Promise((resolve) => {
            const xhr = new XMLHttpRequest();
            xhr.open('POST', this.options.uploadUrl);
            Object.entries(this.options.uploadHeaders).forEach(([k, v]) => xhr.setRequestHeader(k, v));

            xhr.upload.onprogress = (e) => {
                if (e.lengthComputable) {
                    entry.progress = Math.round((e.loaded / e.total) * 100);
                    this._updateList();
                }
            };

            xhr.onload = () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    entry.status   = 'done';
                    entry.progress = 100;
                    this._updateList();
                    const resp = JSON.parse(xhr.responseText || 'null');
                    this.emit('upload', { file: entry.file, response: resp });
                    
                } else {
                    entry.status = 'error';
                    entry.error  = `Upload failed (HTTP ${xhr.status})`;
                    this._updateList();
                    this.emit('error', { file: entry.file, error: entry.error });
                    
                }
                resolve();
            };

            xhr.onerror = () => {
                entry.status = 'error';
                entry.error  = 'Network error';
                this._updateList();
                resolve();
            };

            xhr.send(formData);
        });
    }

    // ── Public API ─────────────────────────────────────────────────────────

    getFiles() { return this.state.files.filter(f => f.status !== 'error').map(f => f.file); }
    getAllEntries() { return [...this.state.files]; }
    clear() { this.state.files = []; this._updateList(); }
    setError(msg) { this.options.errorMessage = msg; this.render(); this._bindEvents(); }

    // ── Utilities ──────────────────────────────────────────────────────────

    _fmtSize(bytes) {
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`;
        return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
    }
}
