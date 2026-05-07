/**
 * FlexSidebar - Fixed-width sidebar + flexible content primitive
 *
 * Layout primitive that splits its container into a fixed-width
 * sidebar (left or right) and a flex-1 content pane. When the
 * viewport gets too narrow (``container.width < sidebarWidth +
 * contentMinWidth``), the sidebar auto-collapses and the content
 * spans the full width. Subscribes to ``FlexResponsive.onResize``
 * for live re-evaluation of the threshold.
 *
 * Slot semantics: children with ``data-slot="sidebar"`` populate
 * the sidebar; all other children become content.
 *
 * Story 15.1.1 (epic-21 sprint 1)
 *
 * @author Claude Code
 * @version 1.0.0
 */

import BaseComponent from '../core/base-component.js';
import { getResponsive } from '../utilities/flex-responsive.js';

export default class FlexSidebar extends BaseComponent {
    static DEFAULTS = {
        side: 'left',
        sidebarWidth: '240px',
        contentMinWidth: '320px',
        classes: []
    };

    constructor(container, options = {}) {
        super(container, options);
        this._isCollapsed = false;
        this.init();
    }

    init() {
        const children = Array.from(this.container.children);
        this._sidebarSlot = children.find(el => el.dataset && el.dataset.slot === 'sidebar') || null;
        this._defaultChildren = children.filter(el => !(el.dataset && el.dataset.slot === 'sidebar'));

        this._render();
        this._evaluateCollapse();
        this._subscribeResize();
        this.emit('init');
    }

    _render() {
        this.container.innerHTML = '';
        this.container.classList.add('flex', 'h-full', ...this.options.classes);
        this.container.dataset.flexComponent = 'sidebar';

        const sidebarEl = document.createElement('div');
        sidebarEl.className = 'flex-shrink-0 overflow-auto';
        sidebarEl.style.width = this._normalizeLength(this.options.sidebarWidth, '240px');
        sidebarEl.dataset.flexSidebarPart = 'sidebar';
        if (this._sidebarSlot) sidebarEl.appendChild(this._sidebarSlot);
        this._sidebarEl = sidebarEl;

        const contentEl = document.createElement('div');
        contentEl.className = 'flex-1 min-w-0 overflow-auto';
        contentEl.dataset.flexSidebarPart = 'content';
        this._defaultChildren.forEach(c => contentEl.appendChild(c));
        this._contentEl = contentEl;

        if (this.options.side === 'right') {
            this.container.appendChild(contentEl);
            this.container.appendChild(sidebarEl);
        } else {
            this.container.appendChild(sidebarEl);
            this.container.appendChild(contentEl);
        }
    }

    _evaluateCollapse() {
        if (!this._sidebarEl) return;
        const rect = this.container.getBoundingClientRect();
        if (rect.width === 0) return;
        const sidebarPx = this._parsePixels(this.options.sidebarWidth);
        const minContentPx = this._parsePixels(this.options.contentMinWidth);
        const collapsed = rect.width < sidebarPx + minContentPx;
        if (collapsed !== this._isCollapsed) {
            this._isCollapsed = collapsed;
            this._sidebarEl.style.display = collapsed ? 'none' : '';
            this.container.classList.toggle('flex-sidebar-collapsed', collapsed);
            this.emit('collapsed-change', { collapsed });
        }
    }

    _subscribeResize() {
        try {
            const responsive = getResponsive();
            this._unsubscribe = responsive.onResize(() => this._evaluateCollapse());
        } catch (e) {
            this._resizeHandler = this.debounce(() => this._evaluateCollapse(), 150);
            window.addEventListener('resize', this._resizeHandler);
        }
    }

    _parsePixels(value) {
        if (typeof value === 'number' && Number.isFinite(value)) return Math.max(0, value);
        const m = String(value || '').trim().match(/^(\d+(?:\.\d+)?)(px)?$/);
        if (!m) return 0;
        const n = parseFloat(m[1]);
        return Number.isFinite(n) ? Math.max(0, n) : 0;
    }

    _normalizeLength(value, fallback) {
        if (typeof value === 'number' && Number.isFinite(value) && value > 0) {
            return `${value}px`;
        }
        const m = String(value || '').trim().match(/^(\d+(?:\.\d+)?)(px|rem|em|%|vw)?$/);
        if (!m) return fallback;
        return `${m[1]}${m[2] || 'px'}`;
    }

    isCollapsed() {
        return this._isCollapsed;
    }

    destroy() {
        if (this._unsubscribe) {
            this._unsubscribe();
            this._unsubscribe = null;
        }
        if (this._resizeHandler) {
            window.removeEventListener('resize', this._resizeHandler);
            this._resizeHandler = null;
        }
        super.destroy();
    }
}
