/**
 * FlexToolbar - Horizontal action bar with optional sticky behavior
 *
 * Layout primitive that arranges children in a horizontal toolbar.
 * Slot semantics: ``data-slot="start"`` children land in the
 * left-aligned group, ``data-slot="end"`` in the right-aligned
 * group, all others in the centre. When ``sticky=true`` is set,
 * the toolbar sticks to the viewport edge on scroll and gains a
 * ``stuck`` state class (with shadow) detected via an
 * IntersectionObserver sentinel.
 *
 * Story 15.1.1 (epic-21 sprint 1)
 *
 * @author Claude Code
 * @version 1.0.0
 */

import BaseComponent from '../core/base-component.js';

export default class FlexToolbar extends BaseComponent {
    static DEFAULTS = {
        position: 'top',
        sticky: false,
        classes: []
    };

    constructor(container, options = {}) {
        super(container, options);
        this.init();
    }

    init() {
        const children = Array.from(this.container.children);
        this._startChildren = children.filter(el => el.dataset && el.dataset.slot === 'start');
        this._endChildren = children.filter(el => el.dataset && el.dataset.slot === 'end');
        this._defaultChildren = children.filter(el => !(el.dataset && el.dataset.slot));

        this._render();
        if (this.options.sticky) this._observeStuckState();
        this.emit('init');
    }

    _render() {
        this.container.innerHTML = '';

        const baseClasses = ['flex', 'items-center', 'gap-4', 'px-3', 'py-2', 'bg-white', 'border-b', 'border-gray-200'];
        if (this.options.sticky) {
            baseClasses.push('sticky', 'z-10', 'transition-shadow');
            baseClasses.push(this.options.position === 'bottom' ? 'bottom-0' : 'top-0');
            if (this.options.position === 'bottom') {
                baseClasses.push('border-b-0', 'border-t');
            }
        }
        this.container.classList.add(...baseClasses, ...this.options.classes);
        this.container.setAttribute('role', 'toolbar');
        this.container.dataset.flexComponent = 'toolbar';

        const start = document.createElement('div');
        start.className = 'flex items-center gap-2';
        start.dataset.flexToolbarPart = 'start';
        this._startChildren.forEach(el => start.appendChild(el));
        this.container.appendChild(start);

        const middle = document.createElement('div');
        middle.className = 'flex items-center gap-2 flex-1 min-w-0';
        middle.dataset.flexToolbarPart = 'default';
        this._defaultChildren.forEach(el => middle.appendChild(el));
        this.container.appendChild(middle);

        const end = document.createElement('div');
        end.className = 'flex items-center gap-2';
        end.dataset.flexToolbarPart = 'end';
        this._endChildren.forEach(el => end.appendChild(el));
        this.container.appendChild(end);
    }

    _observeStuckState() {
        if (typeof IntersectionObserver === 'undefined') return;
        const parent = this.container.parentElement;
        if (!parent) return;

        const sentinel = document.createElement('div');
        sentinel.setAttribute('aria-hidden', 'true');
        sentinel.style.height = '1px';
        sentinel.style.pointerEvents = 'none';
        sentinel.dataset.flexToolbarSentinel = 'true';

        if (this.options.position === 'bottom') {
            parent.insertBefore(sentinel, this.container.nextSibling);
        } else {
            parent.insertBefore(sentinel, this.container);
        }
        this._sentinel = sentinel;

        this._stuckObserver = new IntersectionObserver(
            (entries) => {
                const entry = entries[0];
                if (!entry) return;
                const stuck = !entry.isIntersecting;
                this.container.classList.toggle('stuck', stuck);
                this.container.classList.toggle('shadow-md', stuck);
            },
            { threshold: 0 }
        );
        this._stuckObserver.observe(sentinel);
    }

    destroy() {
        if (this._stuckObserver) {
            this._stuckObserver.disconnect();
            this._stuckObserver = null;
        }
        if (this._sentinel && this._sentinel.parentElement) {
            this._sentinel.parentElement.removeChild(this._sentinel);
            this._sentinel = null;
        }
        super.destroy();
    }
}
