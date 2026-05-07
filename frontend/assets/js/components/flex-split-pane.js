/**
 * FlexSplitPane - Draggable two-pane horizontal split primitive
 *
 * Layout primitive that splits its container into a left and right
 * pane with a draggable handle between them. Slot semantics: child
 * elements with ``data-slot="left"`` land in the left pane,
 * ``data-slot="right"`` in the right pane. Children without a
 * data-slot are silently discarded.
 *
 * Story 15.1.1 (epic-21 sprint 1)
 *
 * @author Claude Code
 * @version 1.0.0
 */

import BaseComponent from '../core/base-component.js';

const STEP_PCT = 1;

export default class FlexSplitPane extends BaseComponent {
    static DEFAULTS = {
        initialSplit: '50%',
        minLeft: '100px',
        minRight: '100px',
        classes: []
    };

    constructor(container, options = {}) {
        super(container, options);
        this._isDragging = false;
        this._splitPct = 50;
        this._onMouseMove = this._onMouseMove.bind(this);
        this._onMouseUp = this._onMouseUp.bind(this);
        this.init();
    }

    init() {
        const children = Array.from(this.container.children);
        this._leftSlot = children.find(el => el.dataset && el.dataset.slot === 'left') || null;
        this._rightSlot = children.find(el => el.dataset && el.dataset.slot === 'right') || null;

        this._splitPct = this._parsePercent(this.options.initialSplit, 50);
        this._render();
        this._bindEvents();
        this.emit('init');
    }

    _render() {
        this.container.innerHTML = '';
        this.container.classList.add('flex', 'h-full', 'relative', ...this.options.classes);
        this.container.dataset.flexComponent = 'split-pane';

        this._leftPane = document.createElement('div');
        this._leftPane.className = 'overflow-auto';
        this._leftPane.style.flex = `0 0 ${this._splitPct}%`;
        this._leftPane.dataset.flexSplitPart = 'left';
        if (this._leftSlot) this._leftPane.appendChild(this._leftSlot);
        this.container.appendChild(this._leftPane);

        this._handle = document.createElement('div');
        this._handle.className = 'flex-split-handle w-2 bg-gray-300 hover:bg-blue-400 cursor-col-resize transition-colors flex-shrink-0';
        this._handle.setAttribute('role', 'separator');
        this._handle.setAttribute('aria-orientation', 'vertical');
        this._handle.setAttribute('aria-valuemin', '0');
        this._handle.setAttribute('aria-valuemax', '100');
        this._handle.setAttribute('aria-valuenow', String(Math.round(this._splitPct)));
        this._handle.setAttribute('tabindex', '0');
        this.container.appendChild(this._handle);

        this._rightPane = document.createElement('div');
        this._rightPane.className = 'overflow-auto flex-1';
        this._rightPane.dataset.flexSplitPart = 'right';
        if (this._rightSlot) this._rightPane.appendChild(this._rightSlot);
        this.container.appendChild(this._rightPane);
    }

    _bindEvents() {
        this._handle.addEventListener('mousedown', (e) => {
            if (this._isConstrained()) return;
            e.preventDefault();
            this._isDragging = true;
            this.container.classList.add('flex-split-dragging');
            this._leftPane.style.transition = 'none';
            document.addEventListener('mousemove', this._onMouseMove);
            document.addEventListener('mouseup', this._onMouseUp);
        });

        this._handle.addEventListener('keydown', (e) => {
            if (this._isConstrained()) return;
            if (e.key === 'ArrowLeft') {
                e.preventDefault();
                this._setPct(this._clampPct(this._splitPct - STEP_PCT));
                this._emitChange();
            } else if (e.key === 'ArrowRight') {
                e.preventDefault();
                this._setPct(this._clampPct(this._splitPct + STEP_PCT));
                this._emitChange();
            }
        });
    }

    _onMouseMove(e) {
        if (!this._isDragging) return;
        const rect = this.container.getBoundingClientRect();
        if (rect.width === 0) return;
        const offsetX = e.clientX - rect.left;
        const pct = (offsetX / rect.width) * 100;
        this._setPct(this._clampPct(pct));
    }

    _onMouseUp() {
        if (!this._isDragging) return;
        this._isDragging = false;
        this.container.classList.remove('flex-split-dragging');
        this._leftPane.style.transition = '';
        document.removeEventListener('mousemove', this._onMouseMove);
        document.removeEventListener('mouseup', this._onMouseUp);
        this._emitChange();
    }

    _parsePercent(value, fallback) {
        if (typeof value === 'number' && Number.isFinite(value)) {
            return Math.max(0, Math.min(100, value));
        }
        const m = String(value).trim().match(/^(\d+(?:\.\d+)?)%?$/);
        if (!m) return fallback;
        const n = parseFloat(m[1]);
        return Number.isFinite(n) ? Math.max(0, Math.min(100, n)) : fallback;
    }

    _parsePixels(value) {
        if (typeof value === 'number' && Number.isFinite(value)) return Math.max(0, value);
        const m = String(value).trim().match(/^(\d+(?:\.\d+)?)(px)?$/);
        if (!m) return 0;
        const n = parseFloat(m[1]);
        return Number.isFinite(n) ? Math.max(0, n) : 0;
    }

    _isConstrained() {
        const rect = this.container.getBoundingClientRect();
        const minLeft = this._parsePixels(this.options.minLeft);
        const minRight = this._parsePixels(this.options.minRight);
        return rect.width > 0 && rect.width < (minLeft + minRight);
    }

    _clampPct(pct) {
        const rect = this.container.getBoundingClientRect();
        const minLeft = this._parsePixels(this.options.minLeft);
        const minRight = this._parsePixels(this.options.minRight);
        if (rect.width === 0 || rect.width < minLeft + minRight) {
            return 50;
        }
        const minPct = (minLeft / rect.width) * 100;
        const maxPct = 100 - (minRight / rect.width) * 100;
        return Math.max(minPct, Math.min(maxPct, pct));
    }

    _setPct(pct) {
        this._splitPct = pct;
        if (this._leftPane) this._leftPane.style.flex = `0 0 ${pct}%`;
        if (this._handle) this._handle.setAttribute('aria-valuenow', String(Math.round(pct)));
    }

    _emitChange() {
        this.emit('split-change', {
            leftPct: this._splitPct,
            rightPct: 100 - this._splitPct
        });
    }

    setSplit(pct) {
        const clamped = this._clampPct(this._parsePercent(pct, this._splitPct));
        this._setPct(clamped);
        this._emitChange();
    }
}
