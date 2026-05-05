/**
 * FlexContainer - Bounded-width centered wrapper primitive
 *
 * Layout primitive that constrains content width and centers it
 * horizontally with optional padding. Use as the outermost wrapper
 * of a page section to prevent content sprawling on wide viewports.
 *
 * Story 15.1.1 (epic-21 sprint 1)
 *
 * @author Claude Code
 * @version 1.0.0
 */

import BaseComponent from '../core/base-component.js';

const PADDING_CLASSES = {
    none: '',
    xs: 'p-1',
    sm: 'p-2',
    md: 'p-4',
    lg: 'p-6',
    xl: 'p-8'
};

const MAX_WIDTH_TOKEN_CLASSES = {
    sm: 'max-w-2xl',
    md: 'max-w-4xl',
    lg: 'max-w-6xl',
    xl: 'max-w-7xl',
    full: 'max-w-full'
};

export default class FlexContainer extends BaseComponent {
    static DEFAULTS = {
        maxWidth: 'lg',
        padding: 'md',
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
        const padding = PADDING_CLASSES[this.options.padding] !== undefined
            ? PADDING_CLASSES[this.options.padding]
            : PADDING_CLASSES.md;

        const tokenClass = MAX_WIDTH_TOKEN_CLASSES[this.options.maxWidth];
        const isToken = tokenClass !== undefined;

        const classes = ['mx-auto', 'w-full'];
        if (isToken) classes.push(tokenClass);
        if (padding) classes.push(padding);
        classes.push(...this.options.classes);

        this.container.classList.add(...classes.filter(Boolean));

        if (!isToken && typeof this.options.maxWidth === 'string') {
            this.container.style.maxWidth = this.options.maxWidth;
        }

        this.container.dataset.flexComponent = 'container';
    }
}
