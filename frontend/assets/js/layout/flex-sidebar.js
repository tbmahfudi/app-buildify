/**
 * FlexSidebar Component
 *
 * Responsive sidebar layout pattern with automatic mobile/desktop behavior,
 * collapsible navigation, and flexible positioning.
 *
 * @extends BaseComponent
 *
 * Features:
 * - Positioning (left, right, both sidebars)
 * - Responsive width control with breakpoints
 * - Collapsible behavior with breakpoint triggers
 * - Multiple display modes (overlay, push, reveal, drawer)
 * - Backdrop overlay with click-to-close
 * - Resizable sidebars with drag handles
 * - Sticky positioning and independent scrolling
 * - Keyboard navigation (Escape key)
 * - State management (open/closed)
 * - Animation support
 *
 * @example
 * // Basic left sidebar
 * const layout = new FlexSidebar('#app', {
 *   position: 'left',
 *   width: { xs: '100%', md: '280px' },
 *   collapsible: true,
 *   content: {
 *     sidebar: navElement,
 *     main: contentElement
 *   }
 * });
 *
 * @example
 * // Admin dashboard with resizable sidebar
 * const dashboard = new FlexSidebar('#dashboard', {
 *   position: 'left',
 *   width: { md: '280px' },
 *   resizable: true,
 *   sticky: true,
 *   mobileMode: 'overlay',
 *   desktopMode: 'push',
 *   content: {
 *     sidebar: navigationStack,
 *     main: dashboardContent
 *   }
 * });
 */

import { BREAKPOINTS, EVENTS } from '../core/constants.js';
import BaseComponent from '../core/base-component.js';
import { getResponsive } from '../utilities/flex-responsive.js';

export default class FlexSidebar extends BaseComponent {
    /**
     * Default configuration
     */
    static DEFAULTS = {
        position: 'left',           // left | right | both
        width: { xs: '100%', md: '280px' },
        minWidth: '240px',
        maxWidth: '400px',
        collapsible: true,
        collapseBreakpoint: 'md',
        mobileMode: 'overlay',      // overlay | push | drawer
        desktopMode: 'push',        // push | overlay | reveal
        defaultOpen: { xs: false, md: true },
        backdrop: true,
        backdropColor: 'black',
        backdropOpacity: 0.5,
        closeOnBackdropClick: true,
        closeOnEscape: true,
        resizable: false,
        resizeHandle: true,
        sticky: false,
        stickyOffset: 0,
        scrollable: true,
        maxHeight: '100vh',
        animated: true,
        animationDuration: 300,
        animations: {
            slide: true,
            fade: true,
            scale: false
        },
        content: {
            sidebar: null,
            main: null
        },
        sidebars: null,             // For 'both' position
        tag: 'div',
        classes: []
    };

    constructor(container, options = {}) {
        super(container, { ...FlexSidebar.DEFAULTS, ...options });

        this.responsive = getResponsive();
        this.layoutElement = null;
        this.sidebarElements = {};
        this.mainElement = null;
        this.backdropElement = null;
        this.resizeHandles = {};

        // State management
        this.state = {
            isOpen: false,
            currentWidth: null,
            currentMode: null,
            isResizing: false,
            resizeStartX: 0,
            resizeStartWidth: 0
        };

        this.init();
    }

    /**
     * Initialize the sidebar layout
     */
    init() {
        this.resolveOptions();
        this.render();
        this.attachEventListeners();
        this.emit(EVENTS.INIT);
    }

    /**
     * Resolve configuration options
     */
    resolveOptions() {
        const { width } = this.options;

        // Resolve width configuration
        this.widthConfig = typeof width === 'object' ? width : { xs: width };

        // Determine initial open state
        const currentBreakpoint = this.responsive.getCurrentBreakpoint();
        const defaultOpen = this.options.defaultOpen;

        if (typeof defaultOpen === 'object') {
            this.state.isOpen = this.getResponsiveValue(defaultOpen, currentBreakpoint);
        } else {
            this.state.isOpen = defaultOpen;
        }

        // Determine current mode
        this.state.currentMode = this.getModeForBreakpoint();
    }

    /**
     * Render the layout
     */
    render() {
        // Get or create layout element
        if (this.container instanceof HTMLElement) {
            this.layoutElement = this.container;
        } else {
            this.layoutElement = document.querySelector(this.container);
        }

        if (!this.layoutElement) {
            console.error(`FlexSidebar: Container not found: ${this.container}`);
            return;
        }

        // Add base classes
        this.layoutElement.classList.add('flex-sidebar-layout');
        this.layoutElement.classList.add(`flex-sidebar-layout--${this.options.position}`);

        // Add custom classes
        if (this.options.classes.length > 0) {
            this.layoutElement.classList.add(...this.options.classes);
        }

        // Create layout structure
        this.createLayoutStructure();

        // Create backdrop if needed
        if (this.options.backdrop) {
            this.createBackdrop();
        }

        // Apply initial layout
        this.applyLayout();

        this.emit(EVENTS.RENDER);
    }

    /**
     * Create layout structure based on position
     */
    createLayoutStructure() {
        const { position, content, sidebars } = this.options;

        // Create wrapper
        const wrapper = this.createElement('div', ['flex-sidebar-layout__wrapper']);

        if (position === 'both' && sidebars) {
            // Both sidebars
            this.createSidebar('left', sidebars.left, wrapper);
            this.createMainArea(content.main, wrapper);
            this.createSidebar('right', sidebars.right, wrapper);
        } else if (position === 'left') {
            // Left sidebar only
            this.createSidebar('left', content.sidebar, wrapper);
            this.createMainArea(content.main, wrapper);
        } else if (position === 'right') {
            // Right sidebar only
            this.createMainArea(content.main, wrapper);
            this.createSidebar('right', content.sidebar, wrapper);
        }

        this.layoutElement.appendChild(wrapper);
    }

    /**
     * Create sidebar element
     */
    createSidebar(position, content, wrapper) {
        const sidebar = this.createElement('div', [
            'flex-sidebar-layout__sidebar',
            `flex-sidebar-layout__sidebar--${position}`
        ]);

        // Add content
        if (content) {
            if (typeof content === 'string') {
                sidebar.innerHTML = content;
            } else if (content instanceof HTMLElement) {
                sidebar.appendChild(content);
            } else if (content.getElement && typeof content.getElement === 'function') {
                sidebar.appendChild(content.getElement());
            }
        }

        // Apply scrollable
        if (this.options.scrollable) {
            sidebar.style.overflowY = 'auto';
            sidebar.style.maxHeight = this.options.maxHeight;
        }

        // Apply sticky
        if (this.options.sticky) {
            sidebar.style.position = 'sticky';
            sidebar.style.top = this.options.stickyOffset + 'px';
        }

        this.sidebarElements[position] = sidebar;
        wrapper.appendChild(sidebar);

        // Create resize handle if enabled
        if (this.options.resizable && this.options.resizeHandle) {
            this.createResizeHandle(position, sidebar, wrapper);
        }
    }

    /**
     * Create main content area
     */
    createMainArea(content, wrapper) {
        const main = this.createElement('div', ['flex-sidebar-layout__main']);

        // Add content
        if (content) {
            if (typeof content === 'string') {
                main.innerHTML = content;
            } else if (content instanceof HTMLElement) {
                main.appendChild(content);
            } else if (content.getElement && typeof content.getElement === 'function') {
                main.appendChild(content.getElement());
            }
        }

        this.mainElement = main;
        wrapper.appendChild(main);
    }

    /**
     * Create resize handle
     */
    createResizeHandle(position, sidebar, wrapper) {
        const handle = this.createElement('div', [
            'flex-sidebar-layout__resize-handle',
            `flex-sidebar-layout__resize-handle--${position}`
        ]);

        handle.style.cursor = position === 'left' ? 'ew-resize' : 'ew-resize';
        handle.style.width = '4px';
        handle.style.position = 'absolute';
        handle.style.top = '0';
        handle.style.bottom = '0';
        handle.style.zIndex = '100';

        if (position === 'left') {
            handle.style.right = '-2px';
        } else {
            handle.style.left = '-2px';
        }

        sidebar.style.position = 'relative';
        sidebar.appendChild(handle);

        this.resizeHandles[position] = handle;

        // Attach resize event listeners
        this.attachResizeListeners(handle, position);
    }

    /**
     * Create backdrop overlay
     */
    createBackdrop() {
        const backdrop = this.createElement('div', ['flex-sidebar-layout__backdrop']);

        backdrop.style.display = 'none';
        backdrop.style.position = 'fixed';
        backdrop.style.top = '0';
        backdrop.style.left = '0';
        backdrop.style.width = '100%';
        backdrop.style.height = '100%';
        backdrop.style.backgroundColor = this.options.backdropColor;
        backdrop.style.opacity = '0';
        backdrop.style.zIndex = '998';
        backdrop.style.transition = `opacity ${this.options.animationDuration}ms ease`;

        this.backdropElement = backdrop;
        this.layoutElement.appendChild(backdrop);

        // Attach backdrop click listener
        if (this.options.closeOnBackdropClick) {
            backdrop.addEventListener('click', () => this.close());
        }
    }

    /**
     * Apply layout based on current state and mode
     */
    applyLayout() {
        const currentBreakpoint = this.responsive.getCurrentBreakpoint();
        const width = this.getResponsiveValue(this.widthConfig, currentBreakpoint);

        // Update mode based on breakpoint
        this.state.currentMode = this.getModeForBreakpoint();

        // Apply layout for each sidebar
        Object.keys(this.sidebarElements).forEach(position => {
            const sidebar = this.sidebarElements[position];
            this.applySidebarLayout(sidebar, position, width);
        });

        // Show/hide backdrop based on mode and state
        this.updateBackdrop();
    }

    /**
     * Apply sidebar layout
     */
    applySidebarLayout(sidebar, position, width) {
        const { currentMode } = this.state;

        // Set width
        sidebar.style.width = width;
        this.state.currentWidth = width;

        // Apply mode-specific styles
        if (currentMode === 'overlay') {
            sidebar.style.position = 'fixed';
            sidebar.style.top = '0';
            sidebar.style.bottom = '0';
            sidebar.style.zIndex = '999';

            if (position === 'left') {
                sidebar.style.left = this.state.isOpen ? '0' : `-${width}`;
            } else {
                sidebar.style.right = this.state.isOpen ? '0' : `-${width}`;
            }

            if (this.options.animated && this.options.animations.slide) {
                sidebar.style.transition = `${position} ${this.options.animationDuration}ms ease`;
            }

            // Main content not affected
            if (this.mainElement) {
                this.mainElement.style.marginLeft = '';
                this.mainElement.style.marginRight = '';
            }
        } else if (currentMode === 'push') {
            sidebar.style.position = 'relative';
            sidebar.style.zIndex = '1';

            if (!this.state.isOpen) {
                sidebar.style.marginLeft = position === 'left' ? `-${width}` : '';
                sidebar.style.marginRight = position === 'right' ? `-${width}` : '';
            } else {
                sidebar.style.marginLeft = '';
                sidebar.style.marginRight = '';
            }

            if (this.options.animated && this.options.animations.slide) {
                sidebar.style.transition = `margin ${this.options.animationDuration}ms ease`;
            }
        } else if (currentMode === 'reveal') {
            sidebar.style.position = 'fixed';
            sidebar.style.top = '0';
            sidebar.style.bottom = '0';
            sidebar.style.zIndex = '1';

            if (position === 'left') {
                sidebar.style.left = '0';
            } else {
                sidebar.style.right = '0';
            }

            // Main content slides over/away from sidebar
            if (this.mainElement) {
                if (this.state.isOpen) {
                    if (position === 'left') {
                        this.mainElement.style.marginLeft = width;
                    } else {
                        this.mainElement.style.marginRight = width;
                    }
                } else {
                    this.mainElement.style.marginLeft = '';
                    this.mainElement.style.marginRight = '';
                }

                if (this.options.animated) {
                    this.mainElement.style.transition = `margin ${this.options.animationDuration}ms ease`;
                }
            }
        } else if (currentMode === 'drawer') {
            // Similar to overlay but with scale animation
            sidebar.style.position = 'fixed';
            sidebar.style.top = '0';
            sidebar.style.bottom = '0';
            sidebar.style.zIndex = '999';

            if (position === 'left') {
                sidebar.style.left = this.state.isOpen ? '0' : `-${width}`;
            } else {
                sidebar.style.right = this.state.isOpen ? '0' : `-${width}`;
            }

            if (this.options.animated) {
                sidebar.style.transition = `${position} ${this.options.animationDuration}ms ease, transform ${this.options.animationDuration}ms ease`;
            }

            // Scale main content when drawer is open
            if (this.mainElement && this.options.animations.scale) {
                if (this.state.isOpen) {
                    this.mainElement.style.transform = 'scale(0.95)';
                } else {
                    this.mainElement.style.transform = 'scale(1)';
                }

                if (this.options.animated) {
                    this.mainElement.style.transition = `transform ${this.options.animationDuration}ms ease`;
                }
            }
        }
    }

    /**
     * Update backdrop visibility
     */
    updateBackdrop() {
        if (!this.backdropElement) return;

        const { currentMode, isOpen } = this.state;

        // Show backdrop for overlay/drawer modes when open
        if ((currentMode === 'overlay' || currentMode === 'drawer') && isOpen) {
            this.backdropElement.style.display = 'block';
            // Force reflow
            this.backdropElement.offsetHeight;
            this.backdropElement.style.opacity = this.options.backdropOpacity;
        } else {
            this.backdropElement.style.opacity = '0';
            setTimeout(() => {
                if (!this.state.isOpen) {
                    this.backdropElement.style.display = 'none';
                }
            }, this.options.animationDuration);
        }
    }

    /**
     * Get mode for current breakpoint
     */
    getModeForBreakpoint() {
        const currentBreakpoint = this.responsive.getCurrentBreakpoint();
        const { collapseBreakpoint, mobileMode, desktopMode } = this.options;

        // Check if we're below collapse breakpoint
        const isMobile = this.responsive.isBelow(collapseBreakpoint);

        return isMobile ? mobileMode : desktopMode;
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Listen for breakpoint changes
        this.responsive.onBreakpointChange(() => {
            this.applyLayout();
            this.emit(EVENTS.UPDATE, {
                breakpoint: this.responsive.getCurrentBreakpoint(),
                mode: this.state.currentMode
            });
        });

        // Listen for Escape key
        if (this.options.closeOnEscape) {
            this.handleEscapeKey = (event) => {
                if (event.key === 'Escape' && this.state.isOpen) {
                    this.close();
                }
            };

            document.addEventListener('keydown', this.handleEscapeKey);
        }
    }

    /**
     * Attach resize listeners to handle
     */
    attachResizeListeners(handle, position) {
        const startResize = (event) => {
            event.preventDefault();
            this.state.isResizing = true;
            this.state.resizeStartX = event.clientX;

            const sidebar = this.sidebarElements[position];
            this.state.resizeStartWidth = sidebar.offsetWidth;

            // Add event listeners for mousemove and mouseup
            document.addEventListener('mousemove', this.handleResize);
            document.addEventListener('mouseup', this.endResize);

            // Add resizing class
            this.layoutElement.classList.add('flex-sidebar-layout--resizing');

            this.emit('resize:start', { position, width: this.state.resizeStartWidth });
        };

        this.handleResize = (event) => {
            if (!this.state.isResizing) return;

            const sidebar = this.sidebarElements[position];
            const delta = position === 'left' ?
                event.clientX - this.state.resizeStartX :
                this.state.resizeStartX - event.clientX;

            let newWidth = this.state.resizeStartWidth + delta;

            // Apply min/max constraints
            const minWidth = parseInt(this.options.minWidth);
            const maxWidth = parseInt(this.options.maxWidth);

            newWidth = Math.max(minWidth, Math.min(maxWidth, newWidth));

            sidebar.style.width = `${newWidth}px`;
            this.state.currentWidth = `${newWidth}px`;

            this.emit('resize', { position, width: newWidth });
        };

        this.endResize = () => {
            if (!this.state.isResizing) return;

            this.state.isResizing = false;

            // Remove event listeners
            document.removeEventListener('mousemove', this.handleResize);
            document.removeEventListener('mouseup', this.endResize);

            // Remove resizing class
            this.layoutElement.classList.remove('flex-sidebar-layout--resizing');

            this.emit('resize:end', { position: position, width: this.state.currentWidth });
        };

        handle.addEventListener('mousedown', startResize);
    }

    /**
     * Open sidebar
     */
    open() {
        if (this.state.isOpen) return;

        this.state.isOpen = true;
        this.applyLayout();

        this.emit('open');
    }

    /**
     * Close sidebar
     */
    close() {
        if (!this.state.isOpen) return;

        this.state.isOpen = false;
        this.applyLayout();

        this.emit('close');
    }

    /**
     * Toggle sidebar
     */
    toggle() {
        if (this.state.isOpen) {
            this.close();
        } else {
            this.open();
        }
    }

    /**
     * Check if sidebar is open
     * @returns {boolean}
     */
    isOpen() {
        return this.state.isOpen;
    }

    /**
     * Set sidebar width
     * @param {string} width - New width
     * @param {string} position - Sidebar position (for 'both' mode)
     */
    setWidth(width, position = null) {
        if (this.options.position === 'both' && !position) {
            console.warn('FlexSidebar: Position required when setting width in "both" mode');
            return;
        }

        const targetPosition = position || this.options.position;
        const sidebar = this.sidebarElements[targetPosition];

        if (!sidebar) return;

        sidebar.style.width = width;
        this.state.currentWidth = width;

        this.emit(EVENTS.UPDATE, { width });
    }

    /**
     * Set sidebar position
     * @param {string} position - Position (left, right)
     */
    setPosition(position) {
        if (!['left', 'right'].includes(position)) {
            console.warn(`FlexSidebar: Invalid position "${position}"`);
            return;
        }

        this.options.position = position;
        this.layoutElement.className = this.layoutElement.className
            .split(' ')
            .filter(cls => !cls.includes('--left') && !cls.includes('--right'))
            .join(' ');

        this.layoutElement.classList.add(`flex-sidebar-layout--${position}`);

        this.emit(EVENTS.UPDATE, { position });
    }

    /**
     * Set display mode
     * @param {string} mode - Mode (overlay, push, reveal, drawer)
     */
    setMode(mode) {
        if (!['overlay', 'push', 'reveal', 'drawer'].includes(mode)) {
            console.warn(`FlexSidebar: Invalid mode "${mode}"`);
            return;
        }

        // Determine if this is mobile or desktop mode
        const isMobile = this.responsive.isBelow(this.options.collapseBreakpoint);

        if (isMobile) {
            this.options.mobileMode = mode;
        } else {
            this.options.desktopMode = mode;
        }

        this.state.currentMode = mode;
        this.applyLayout();

        this.emit(EVENTS.UPDATE, { mode });
    }

    /**
     * Update sidebar content
     * @param {object} config - Content configuration
     */
    updateContent(config) {
        const { sidebar, main, position } = config;

        if (sidebar) {
            const targetPosition = position || this.options.position;
            const sidebarElement = this.sidebarElements[targetPosition];

            if (sidebarElement) {
                sidebarElement.innerHTML = '';

                if (typeof sidebar === 'string') {
                    sidebarElement.innerHTML = sidebar;
                } else if (sidebar instanceof HTMLElement) {
                    sidebarElement.appendChild(sidebar);
                } else if (sidebar.getElement && typeof sidebar.getElement === 'function') {
                    sidebarElement.appendChild(sidebar.getElement());
                }
            }
        }

        if (main && this.mainElement) {
            this.mainElement.innerHTML = '';

            if (typeof main === 'string') {
                this.mainElement.innerHTML = main;
            } else if (main instanceof HTMLElement) {
                this.mainElement.appendChild(main);
            } else if (main.getElement && typeof main.getElement === 'function') {
                this.mainElement.appendChild(main.getElement());
            }
        }

        this.emit(EVENTS.UPDATE, { content: true });
    }

    /**
     * Enable or disable resize
     * @param {boolean} enabled - Whether to enable resize
     */
    enableResize(enabled) {
        this.options.resizable = enabled;

        Object.keys(this.resizeHandles).forEach(position => {
            const handle = this.resizeHandles[position];

            if (enabled) {
                handle.style.display = 'block';
            } else {
                handle.style.display = 'none';
            }
        });

        this.emit(EVENTS.UPDATE, { resizable: enabled });
    }

    /**
     * Get layout element
     * @returns {HTMLElement}
     */
    getElement() {
        return this.layoutElement;
    }

    /**
     * Get sidebar element
     * @param {string} position - Sidebar position (for 'both' mode)
     * @returns {HTMLElement|null}
     */
    getSidebar(position = null) {
        const targetPosition = position || this.options.position;
        return this.sidebarElements[targetPosition] || null;
    }

    /**
     * Get main element
     * @returns {HTMLElement}
     */
    getMain() {
        return this.mainElement;
    }

    /**
     * Destroy the sidebar layout
     */
    destroy() {
        // Remove event listeners
        if (this.handleEscapeKey) {
            document.removeEventListener('keydown', this.handleEscapeKey);
        }

        if (this.handleResize) {
            document.removeEventListener('mousemove', this.handleResize);
            document.removeEventListener('mouseup', this.endResize);
        }

        // Remove classes
        this.layoutElement.classList.remove(
            'flex-sidebar-layout',
            `flex-sidebar-layout--${this.options.position}`
        );

        if (this.options.classes.length > 0) {
            this.layoutElement.classList.remove(...this.options.classes);
        }

        // Remove backdrop
        if (this.backdropElement) {
            this.backdropElement.remove();
        }

        this.emit(EVENTS.DESTROY);

        super.destroy();
    }
}
