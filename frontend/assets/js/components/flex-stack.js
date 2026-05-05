/**
 * FlexStack - Vertical or horizontal flex arrangement primitive
 *
 * Layout primitive for stacking children with consistent spacing in
 * either vertical or horizontal direction. Pure layout — no state,
 * no events beyond `init`.
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

const ALIGN_CLASSES = {
    vertical: {
        start: 'items-start',
        center: 'items-center',
        end: 'items-end',
        stretch: 'items-stretch'
    },
    horizontal: {
        start: 'items-start',
        center: 'items-center',
        end: 'items-end',
        stretch: 'items-stretch'
    }
};

export default class FlexStack extends BaseComponent {
    static DEFAULTS = {
        direction: 'vertical',
        gap: 'md',
        align: 'stretch',
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
        const direction = this.options.direction === 'horizontal' ? 'flex-row' : 'flex-col';
        const gap = GAP_CLASSES[this.options.gap] || GAP_CLASSES.md;
        const align = (ALIGN_CLASSES[this.options.direction] || ALIGN_CLASSES.vertical)[this.options.align]
            || ALIGN_CLASSES.vertical.stretch;

        const classes = ['flex', direction, gap, align, ...this.options.classes].filter(Boolean);
        this.container.classList.add(...classes);
        this.container.dataset.flexComponent = 'stack';
    }
}
