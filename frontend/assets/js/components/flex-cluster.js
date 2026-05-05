/**
 * FlexCluster - Wrap-when-overflow inline cluster primitive
 *
 * Layout primitive that arranges children inline (horizontal) and
 * wraps to additional rows when the container is narrower than the
 * intrinsic content width. Useful for badge groups, tag lists,
 * action button rows.
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
    start: 'items-start',
    center: 'items-center',
    end: 'items-end'
};

const JUSTIFY_CLASSES = {
    start: 'justify-start',
    center: 'justify-center',
    end: 'justify-end',
    'space-between': 'justify-between'
};

export default class FlexCluster extends BaseComponent {
    static DEFAULTS = {
        gap: 'md',
        align: 'start',
        justify: 'start',
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
        const gap = GAP_CLASSES[this.options.gap] || GAP_CLASSES.md;
        const align = ALIGN_CLASSES[this.options.align] || ALIGN_CLASSES.start;
        const justify = JUSTIFY_CLASSES[this.options.justify] || JUSTIFY_CLASSES.start;

        const classes = ['flex', 'flex-wrap', gap, align, justify, ...this.options.classes].filter(Boolean);
        this.container.classList.add(...classes);
        this.container.dataset.flexComponent = 'cluster';
    }
}
