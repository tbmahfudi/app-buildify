/**
 * FlexSection - Semantic section wrapper with optional title and actions
 *
 * Layout primitive that wraps a logical page section with a real
 * heading element (for screen readers / outline) and an optional
 * inline actions row. Children with ``data-slot="actions"`` are
 * relocated into the header next to the title; all other children
 * remain in document order as the section body.
 *
 * Story 15.1.1 (epic-21 sprint 1)
 *
 * @author Claude Code
 * @version 1.0.0
 */

import BaseComponent from '../core/base-component.js';

const HEADING_LEVELS = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'];

const HEADING_CLASSES = {
    h1: 'text-3xl font-bold',
    h2: 'text-2xl font-semibold',
    h3: 'text-xl font-semibold',
    h4: 'text-lg font-semibold',
    h5: 'text-base font-semibold',
    h6: 'text-sm font-semibold uppercase tracking-wide'
};

export default class FlexSection extends BaseComponent {
    static DEFAULTS = {
        title: null,
        level: 'h2',
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
        const level = HEADING_LEVELS.includes(this.options.level) ? this.options.level : 'h2';
        const title = this.options.title;

        const existing = Array.from(this.container.children);
        const actions = existing.filter(el => el.dataset && el.dataset.slot === 'actions');
        const body = existing.filter(el => !(el.dataset && el.dataset.slot === 'actions'));

        this.container.innerHTML = '';
        this.container.classList.add('flex-section', ...this.options.classes);

        if (title || actions.length) {
            const header = document.createElement('div');
            header.className = 'flex justify-between items-center mb-4 gap-4';

            if (title) {
                const heading = document.createElement(level);
                heading.className = HEADING_CLASSES[level];
                heading.textContent = title;
                header.appendChild(heading);
            } else {
                header.appendChild(document.createElement('div'));
            }

            if (actions.length) {
                const actionsWrap = document.createElement('div');
                actionsWrap.className = 'flex items-center gap-2';
                actions.forEach(el => actionsWrap.appendChild(el));
                header.appendChild(actionsWrap);
            }

            this.container.appendChild(header);
        }

        body.forEach(el => this.container.appendChild(el));
        this.container.dataset.flexComponent = 'section';
    }
}
