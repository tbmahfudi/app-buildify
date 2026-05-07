/**
 * FlexMasonry - Column-balanced masonry layout primitive
 *
 * Wraps children into a column-flowed layout where the number of
 * columns auto-fits as ``floor(viewport / column-width)``. Uses CSS
 * ``column-width`` so the browser handles re-layout on resize — no
 * JS subscription needed.
 *
 * Children get ``break-inside: avoid`` so individual cards do not
 * split across columns, and a bottom margin equal to the gap so the
 * vertical spacing matches the column gap.
 *
 * Story 15.1.1 (epic-21 sprint 1)
 *
 * @author Claude Code
 * @version 1.0.0
 */

import BaseComponent from '../core/base-component.js';

const GAP_PX = {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32
};

export default class FlexMasonry extends BaseComponent {
    static DEFAULTS = {
        columnWidth: '240px',
        gap: 'md',
        classes: []
    };

    constructor(container, options = {}) {
        super(container, options);
        this.init();
    }

    init() {
        this._render();
        this.emit('init');
    }

    _render() {
        const colWidth = this._normalizeLength(this.options.columnWidth, '240px');
        const gapPx = GAP_PX[this.options.gap] != null ? GAP_PX[this.options.gap] : GAP_PX.md;

        this.container.style.columnWidth = colWidth;
        this.container.style.columnGap = `${gapPx}px`;
        this.container.classList.add(...this.options.classes);
        this.container.dataset.flexComponent = 'masonry';

        Array.from(this.container.children).forEach(el => {
            el.style.breakInside = 'avoid';
            el.style.webkitColumnBreakInside = 'avoid';
            el.style.pageBreakInside = 'avoid';
            el.style.marginBottom = `${gapPx}px`;
            el.style.width = '100%';
            el.style.display = 'inline-block';
        });
    }

    _normalizeLength(value, fallback) {
        if (typeof value === 'number' && Number.isFinite(value) && value > 0) {
            return `${value}px`;
        }
        const m = String(value || '').trim().match(/^(\d+(?:\.\d+)?)(px|rem|em|%|vw)?$/);
        if (!m) return fallback;
        const unit = m[2] || 'px';
        return `${m[1]}${unit}`;
    }
}
