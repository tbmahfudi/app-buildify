/**
 * FlexSplitPane Component
 *
 * Resizable split layout component for creating complex multi-pane interfaces
 * like code editors, dashboards, and file explorers.
 *
 * @extends BaseComponent
 *
 * Features:
 * - Horizontal and vertical splits
 * - Multiple panes (2+)
 * - Resizable with drag handles
 * - Min/max size constraints
 * - Collapsible panes
 * - Nested splits
 * - Keyboard navigation
 * - Size persistence
 * - Smooth animations
 *
 * @example
 * // Simple horizontal split (editor + preview)
 * const split = new FlexSplitPane('#container', {
 *   direction: 'horizontal',
 *   panes: [
 *     { id: 'editor', content: editorElement, size: '60%', minSize: '300px' },
 *     { id: 'preview', content: previewElement, size: '40%', minSize: '200px' }
 *   ]
 * });
 *
 * @example
 * // Multi-pane vertical split
 * const split = new FlexSplitPane('#container', {
 *   direction: 'vertical',
 *   panes: [
 *     { id: 'top', content: topElement, size: '30%' },
 *     { id: 'middle', content: middleElement, size: '50%' },
 *     { id: 'bottom', content: bottomElement, size: '20%' }
 *   ]
 * });
 */

import { EVENTS } from '../core/constants.js';
import BaseComponent from '../core/base-component.js';
import { getResponsive } from '../utilities/flex-responsive.js';

export default class FlexSplitPane extends BaseComponent {
    /**
     * Default configuration
     */
    static DEFAULTS = {
        direction: 'horizontal',   // horizontal | vertical
        panes: [],
        handleSize: 8,             // px
        handleColor: '#cbd5e1',
        handleHoverColor: '#3b82f6',
        minSize: '100px',          // Default min size for panes
        maxSize: null,             // Default max size for panes
        collapsible: false,
        animated: true,
        animationDuration: 200,    // ms
        persist: false,            // Save sizes to localStorage
        persistKey: 'flex-split-pane',
        tag: 'div',
        classes: []
    };

    constructor(container, options = {}) {
        super(container, { ...FlexSplitPane.DEFAULTS, ...options });

        this.responsive = getResponsive();
        this.splitElement = null;
        this.paneElements = [];
        this.handleElements = [];
        this.paneData = new Map();

        // Resize state
        this.isResizing = false;
        this.resizingIndex = null;
        this.resizeStartPos = 0;
        this.resizeStartSizes = [];

        this.init();
    }

    /**
     * Initialize the split pane
     */
    init() {
        this.loadPersistedSizes();
        this.render();
        this.attachEventListeners();
        this.emit(EVENTS.INIT);
    }

    /**
     * Load persisted sizes from localStorage
     */
    loadPersistedSizes() {
        if (!this.options.persist) return;

        try {
            const key = this.options.persistKey;
            const saved = localStorage.getItem(key);
            if (saved) {
                const sizes = JSON.parse(saved);
                sizes.forEach((size, index) => {
                    if (this.options.panes[index]) {
                        this.options.panes[index].size = size;
                    }
                });
            }
        } catch (e) {
            console.warn('FlexSplitPane: Failed to load persisted sizes', e);
        }
    }

    /**
     * Save sizes to localStorage
     */
    savePersistedSizes() {
        if (!this.options.persist) return;

        try {
            const sizes = this.options.panes.map(pane => pane.size);
            localStorage.setItem(this.options.persistKey, JSON.stringify(sizes));
        } catch (e) {
            console.warn('FlexSplitPane: Failed to save persisted sizes', e);
        }
    }

    /**
     * Render the split pane
     */
    render() {
        // Get or create split element
        if (this.container instanceof HTMLElement) {
            this.splitElement = this.container;
        } else {
            this.splitElement = document.querySelector(this.container);
        }

        if (!this.splitElement) {
            console.error(`FlexSplitPane: Container not found: ${this.container}`);
            return;
        }

        // Add base classes
        this.splitElement.classList.add('flex-split-pane');
        this.splitElement.classList.add(`flex-split-pane--${this.options.direction}`);

        // Add custom classes
        if (this.options.classes.length > 0) {
            this.splitElement.classList.add(...this.options.classes);
        }

        // Apply base styles
        this.applyBaseStyles();

        // Render panes and handles
        this.renderPanes();

        this.emit(EVENTS.RENDER);
    }

    /**
     * Apply base styles
     */
    applyBaseStyles() {
        this.splitElement.style.display = 'flex';
        this.splitElement.style.width = '100%';
        this.splitElement.style.height = '100%';
        this.splitElement.style.overflow = 'hidden';

        // Set flex direction
        if (this.options.direction === 'horizontal') {
            this.splitElement.style.flexDirection = 'row';
        } else {
            this.splitElement.style.flexDirection = 'column';
        }
    }

    /**
     * Render all panes and handles
     */
    renderPanes() {
        // Clear existing content
        this.splitElement.innerHTML = '';
        this.paneElements = [];
        this.handleElements = [];
        this.paneData.clear();

        // Render each pane with handles between them
        this.options.panes.forEach((pane, index) => {
            // Render pane
            const paneElement = this.renderPane(pane, index);
            this.paneElements.push(paneElement);
            this.splitElement.appendChild(paneElement);

            // Render handle (except after last pane)
            if (index < this.options.panes.length - 1) {
                const handle = this.renderHandle(index);
                this.handleElements.push(handle);
                this.splitElement.appendChild(handle);
            }
        });
    }

    /**
     * Render individual pane
     */
    renderPane(pane, index) {
        const paneElement = this.createElement('div', ['flex-split-pane__pane']);

        // Apply pane styles
        paneElement.style.overflow = 'auto';
        paneElement.style.position = 'relative';

        // Apply size
        this.applyPaneSize(paneElement, pane);

        // Add content
        if (typeof pane.content === 'string') {
            paneElement.innerHTML = pane.content;
        } else if (pane.content instanceof HTMLElement) {
            paneElement.appendChild(pane.content);
        } else if (pane.content && typeof pane.content.getElement === 'function') {
            paneElement.appendChild(pane.content.getElement());
        }

        // Add custom pane classes
        if (pane.classes) {
            paneElement.classList.add(...pane.classes);
        }

        // Store pane ID
        if (pane.id) {
            paneElement.dataset.paneId = pane.id;
        }

        // Store pane data
        this.paneData.set(pane.id || `pane-${index}`, {
            element: paneElement,
            config: pane,
            index
        });

        // Apply animation
        if (this.options.animated) {
            paneElement.style.transition = `flex ${this.options.animationDuration}ms ease`;
        }

        return paneElement;
    }

    /**
     * Apply pane size
     */
    applyPaneSize(paneElement, pane) {
        const size = pane.size || 'auto';

        // Parse size (percentage or pixel)
        if (typeof size === 'string' && size.endsWith('%')) {
            const percentage = parseFloat(size);
            paneElement.style.flex = `${percentage} 1 0`;
        } else if (typeof size === 'string' && size.endsWith('px')) {
            paneElement.style.flex = `0 0 ${size}`;
        } else {
            paneElement.style.flex = '1 1 0';
        }

        // Apply min/max sizes
        const minSize = pane.minSize || this.options.minSize;
        const maxSize = pane.maxSize || this.options.maxSize;

        if (this.options.direction === 'horizontal') {
            if (minSize) paneElement.style.minWidth = minSize;
            if (maxSize) paneElement.style.maxWidth = maxSize;
        } else {
            if (minSize) paneElement.style.minHeight = minSize;
            if (maxSize) paneElement.style.maxHeight = maxSize;
        }
    }

    /**
     * Render resize handle
     */
    renderHandle(index) {
        const handle = this.createElement('div', ['flex-split-pane__handle']);

        // Apply handle styles
        handle.style.backgroundColor = this.options.handleColor;
        handle.style.cursor = this.options.direction === 'horizontal' ? 'ew-resize' : 'ns-resize';
        handle.style.flexShrink = '0';
        handle.style.userSelect = 'none';
        handle.style.transition = 'background-color 0.2s ease';

        if (this.options.direction === 'horizontal') {
            handle.style.width = `${this.options.handleSize}px`;
            handle.style.height = '100%';
        } else {
            handle.style.width = '100%';
            handle.style.height = `${this.options.handleSize}px`;
        }

        // Store handle index
        handle.dataset.handleIndex = index;

        // Hover effect
        handle.addEventListener('mouseenter', () => {
            handle.style.backgroundColor = this.options.handleHoverColor;
        });

        handle.addEventListener('mouseleave', () => {
            if (!this.isResizing) {
                handle.style.backgroundColor = this.options.handleColor;
            }
        });

        // Attach resize listeners
        this.attachHandleListeners(handle, index);

        return handle;
    }

    /**
     * Attach handle resize listeners
     */
    attachHandleListeners(handle, index) {
        const startResize = (event) => {
            event.preventDefault();
            this.isResizing = true;
            this.resizingIndex = index;

            // Store initial position
            this.resizeStartPos = this.options.direction === 'horizontal' ? event.clientX : event.clientY;

            // Store initial sizes
            this.resizeStartSizes = this.paneElements.map(pane => {
                return this.options.direction === 'horizontal' ? pane.offsetWidth : pane.offsetHeight;
            });

            // Add resizing class
            this.splitElement.classList.add('flex-split-pane--resizing');

            // Add global listeners
            document.addEventListener('mousemove', this.handleResize);
            document.addEventListener('mouseup', this.endResize);

            this.emit('resize:start', { index });
        };

        handle.addEventListener('mousedown', startResize);
    }

    /**
     * Handle resize
     */
    handleResize = (event) => {
        if (!this.isResizing) return;

        const currentPos = this.options.direction === 'horizontal' ? event.clientX : event.clientY;
        const delta = currentPos - this.resizeStartPos;

        // Get panes being resized
        const leftPane = this.paneElements[this.resizingIndex];
        const rightPane = this.paneElements[this.resizingIndex + 1];

        // Calculate new sizes
        const leftNewSize = this.resizeStartSizes[this.resizingIndex] + delta;
        const rightNewSize = this.resizeStartSizes[this.resizingIndex + 1] - delta;

        // Apply min/max constraints
        const leftConfig = this.options.panes[this.resizingIndex];
        const rightConfig = this.options.panes[this.resizingIndex + 1];

        const leftMin = this.parseSize(leftConfig.minSize || this.options.minSize);
        const rightMin = this.parseSize(rightConfig.minSize || this.options.minSize);

        if (leftNewSize >= leftMin && rightNewSize >= rightMin) {
            // Apply new sizes
            if (this.options.direction === 'horizontal') {
                leftPane.style.flex = `0 0 ${leftNewSize}px`;
                rightPane.style.flex = `0 0 ${rightNewSize}px`;
            } else {
                leftPane.style.flex = `0 0 ${leftNewSize}px`;
                rightPane.style.flex = `0 0 ${rightNewSize}px`;
            }

            // Update config
            this.options.panes[this.resizingIndex].size = `${leftNewSize}px`;
            this.options.panes[this.resizingIndex + 1].size = `${rightNewSize}px`;

            this.emit('resize', {
                index: this.resizingIndex,
                leftSize: leftNewSize,
                rightSize: rightNewSize
            });
        }
    };

    /**
     * End resize
     */
    endResize = () => {
        if (!this.isResizing) return;

        this.isResizing = false;

        // Remove resizing class
        this.splitElement.classList.remove('flex-split-pane--resizing');

        // Reset handle color
        const handle = this.handleElements[this.resizingIndex];
        if (handle) {
            handle.style.backgroundColor = this.options.handleColor;
        }

        // Remove global listeners
        document.removeEventListener('mousemove', this.handleResize);
        document.removeEventListener('mouseup', this.endResize);

        // Save sizes if persist is enabled
        this.savePersistedSizes();

        this.emit('resize:end', { index: this.resizingIndex });

        this.resizingIndex = null;
    };

    /**
     * Parse size string to pixels
     */
    parseSize(size) {
        if (!size) return 0;
        if (typeof size === 'number') return size;
        if (typeof size === 'string' && size.endsWith('px')) {
            return parseFloat(size);
        }
        return 0;
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Listen for breakpoint changes
        this.responsive.onBreakpointChange(() => {
            this.emit(EVENTS.UPDATE, {
                breakpoint: this.responsive.getCurrentBreakpoint()
            });
        });
    }

    /**
     * Set pane size
     * @param {string} paneId - Pane ID
     * @param {string} size - New size
     */
    setPaneSize(paneId, size) {
        const paneData = this.paneData.get(paneId);

        if (!paneData) {
            console.warn(`FlexSplitPane: Pane not found: ${paneId}`);
            return;
        }

        // Update config
        paneData.config.size = size;

        // Apply new size
        this.applyPaneSize(paneData.element, paneData.config);

        // Save if persist enabled
        this.savePersistedSizes();

        this.emit('pane:resize', { paneId, size });
    }

    /**
     * Collapse pane
     * @param {string} paneId - Pane ID
     */
    collapsePane(paneId) {
        const paneData = this.paneData.get(paneId);

        if (!paneData) {
            console.warn(`FlexSplitPane: Pane not found: ${paneId}`);
            return;
        }

        paneData.element.style.flex = '0 0 0';
        paneData.element.style.overflow = 'hidden';
        paneData.config.collapsed = true;

        this.emit('pane:collapse', { paneId });
    }

    /**
     * Expand pane
     * @param {string} paneId - Pane ID
     */
    expandPane(paneId) {
        const paneData = this.paneData.get(paneId);

        if (!paneData) {
            console.warn(`FlexSplitPane: Pane not found: ${paneId}`);
            return;
        }

        this.applyPaneSize(paneData.element, paneData.config);
        paneData.element.style.overflow = 'auto';
        paneData.config.collapsed = false;

        this.emit('pane:expand', { paneId });
    }

    /**
     * Toggle pane collapse
     * @param {string} paneId - Pane ID
     */
    togglePane(paneId) {
        const paneData = this.paneData.get(paneId);

        if (!paneData) {
            console.warn(`FlexSplitPane: Pane not found: ${paneId}`);
            return;
        }

        if (paneData.config.collapsed) {
            this.expandPane(paneId);
        } else {
            this.collapsePane(paneId);
        }
    }

    /**
     * Update pane content
     * @param {string} paneId - Pane ID
     * @param {*} content - New content
     */
    updatePaneContent(paneId, content) {
        const paneData = this.paneData.get(paneId);

        if (!paneData) {
            console.warn(`FlexSplitPane: Pane not found: ${paneId}`);
            return;
        }

        // Clear current content
        paneData.element.innerHTML = '';

        // Add new content
        if (typeof content === 'string') {
            paneData.element.innerHTML = content;
        } else if (content instanceof HTMLElement) {
            paneData.element.appendChild(content);
        } else if (content && typeof content.getElement === 'function') {
            paneData.element.appendChild(content.getElement());
        }

        paneData.config.content = content;

        this.emit('pane:update', { paneId });
    }

    /**
     * Get pane element
     * @param {string} paneId - Pane ID
     * @returns {HTMLElement|null}
     */
    getPaneElement(paneId) {
        const paneData = this.paneData.get(paneId);
        return paneData ? paneData.element : null;
    }

    /**
     * Get split pane element
     * @returns {HTMLElement}
     */
    getElement() {
        return this.splitElement;
    }

    /**
     * Destroy the split pane
     */
    destroy() {
        // Remove resize listeners
        document.removeEventListener('mousemove', this.handleResize);
        document.removeEventListener('mouseup', this.endResize);

        // Remove classes
        this.splitElement.classList.remove(
            'flex-split-pane',
            `flex-split-pane--${this.options.direction}`
        );

        if (this.options.classes.length > 0) {
            this.splitElement.classList.remove(...this.options.classes);
        }

        // Remove inline styles
        this.splitElement.style.display = '';
        this.splitElement.style.width = '';
        this.splitElement.style.height = '';
        this.splitElement.style.overflow = '';
        this.splitElement.style.flexDirection = '';

        // Clear data
        this.paneElements = [];
        this.handleElements = [];
        this.paneData.clear();

        this.emit(EVENTS.DESTROY);

        super.destroy();
    }
}
