/**
 * FlexGrid - Responsive CSS grid wrapper primitive
 *
 * Layout primitive that arranges children in a grid with token-based
 * gap and either a static or responsive column count. Responsive
 * mode uses Tailwind breakpoint prefixes — the browser handles
 * breakpoint transitions natively, no FlexResponsive subscription
 * needed.
 *
 * Story 15.1.1 (epic-21 sprint 1)
 *
 * @author Claude Code
 * @version 1.0.0
 */

import BaseComponent from '../core/base-component.js';

const GAP_CLASSES = {
    xs: 'gap-1',
    sm: 'gap-2',
    md: 'gap-4',
    lg: 'gap-6',
    xl: 'gap-8'
};

const RESPONSIVE_PREFIXES = ['', 'md:', 'lg:', 'xl:'];

export default class FlexGrid extends BaseComponent {
    static DEFAULTS = {
        columns: 1,
        gap: 'md',
        classes: []
    };

    constructor(container, options = {}) {
        super(container, options);
        this.init();
    }

    init() {
        this.render();
        this.emit('init');
    }

    render() {
        const columnsAttr = String(this.options.columns ?? '').trim();
        const gap = GAP_CLASSES[this.options.gap] || GAP_CLASSES.md;
        const classes = ['grid', gap];

        if (columnsAttr.includes(' ')) {
            const counts = columnsAttr.split(/\s+/);
            counts.forEach((count, idx) => {
                const prefix = RESPONSIVE_PREFIXES[idx] ?? RESPONSIVE_PREFIXES[RESPONSIVE_PREFIXES.length - 1];
                const n = this._normalizeCount(count);
                classes.push(`${prefix}grid-cols-${n}`);
            });
        } else {
            const n = this._normalizeCount(columnsAttr || '1');
            classes.push(`grid-cols-${n}`);
        }

        classes.push(...this.options.classes);
        this.container.classList.add(...classes.filter(Boolean));
        this.container.dataset.flexComponent = 'grid';
    }

    _normalizeCount(raw) {
        const n = parseInt(raw, 10);
        return Number.isFinite(n) && n >= 1 ? n : 1;
    }
}
