/**
 * FlexToolbar Component
 *
 * Header/footer toolbar with action groups, sticky positioning, and responsive overflow handling.
 * Perfect for app headers, navigation bars, and action toolbars.
 *
 * @extends BaseComponent
 *
 * Features:
 * - Position: top, bottom, or both
 * - Action groups: left, center, right positioning
 * - Sticky positioning with z-index control
 * - Responsive overflow handling
 * - Dividers between action groups
 * - Theming support (light, dark, custom)
 * - Title/branding section
 * - Dropdown menu integration
 * - Elevation/shadow support
 *
 * @example
 * // App header toolbar
 * const header = new FlexToolbar('#header', {
 *   position: 'top',
 *   sticky: true,
 *   theme: 'light',
 *   actions: {
 *     left: [
 *       { content: '<button id="menu">☰</button>' },
 *       { content: '<h1>App Name</h1>' }
 *     ],
 *     right: [
 *       { content: '<button>Profile</button>' },
 *       { content: '<button>Logout</button>' }
 *     ]
 *   }
 * });
 *
 * @example
 * // Bottom action toolbar
 * const footer = new FlexToolbar('#footer', {
 *   position: 'bottom',
 *   sticky: true,
 *   theme: 'dark',
 *   actions: {
 *     center: [
 *       { content: '<button>Cancel</button>' },
 *       { content: '<button class="primary">Save</button>' }
 *     ]
 *   }
 * });
 */

import { SPACING_SCALE, EVENTS } from '../core/constants.js';
import BaseComponent from '../core/base-component.js';
import { getResponsive } from '../utilities/flex-responsive.js';

export default class FlexToolbar extends BaseComponent {
    /**
     * Default configuration
     */
    static DEFAULTS = {
        position: 'top',           // top | bottom | both
        sticky: true,
        stickyOffset: 0,
        height: { xs: '56px', md: '64px' },
        padding: { xs: 4, md: 6 },
        theme: 'light',            // light | dark | custom
        elevation: 2,              // 0-5 (shadow depth)
        dividers: false,
        actions: {
            left: [],
            center: [],
            right: []
        },
        overflow: 'auto',          // auto | scroll | hidden | menu
        responsive: null,
        tag: 'header',
        classes: []
    };

    /**
     * Theme presets
     */
    static THEMES = {
        light: {
            background: '#ffffff',
            color: '#1f2937',
            border: '#e5e7eb'
        },
        dark: {
            background: '#1f2937',
            color: '#ffffff',
            border: '#374151'
        }
    };

    /**
     * Elevation shadows
     */
    static ELEVATIONS = {
        0: 'none',
        1: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        2: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
        3: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        4: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
        5: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)'
    };

    constructor(container, options = {}) {
        super(container, { ...FlexToolbar.DEFAULTS, ...options });

        this.responsive = getResponsive();
        this.toolbarElement = null;
        this.actionElements = {
            left: [],
            center: [],
            right: []
        };

        this.init();
    }

    /**
     * Initialize the toolbar
     */
    init() {
        this.render();
        this.attachEventListeners();
        this.emit(EVENTS.INIT);
    }

    /**
     * Render the toolbar
     */
    render() {
        // Get or create toolbar element
        if (this.container instanceof HTMLElement) {
            this.toolbarElement = this.container;
        } else {
            this.toolbarElement = document.querySelector(this.container);
        }

        if (!this.toolbarElement) {
            console.error(`FlexToolbar: Container not found: ${this.container}`);
            return;
        }

        // Add base classes
        this.toolbarElement.classList.add('flex-toolbar');
        this.toolbarElement.classList.add(`flex-toolbar--${this.options.position}`);
        this.toolbarElement.classList.add(`flex-toolbar--${this.options.theme}`);

        // Add custom classes
        if (this.options.classes.length > 0) {
            this.toolbarElement.classList.add(...this.options.classes);
        }

        // Apply base styles
        this.applyBaseStyles();

        // Apply theme
        this.applyTheme();

        // Apply positioning
        this.applyPositioning();

        // Render action groups
        this.renderActions();

        this.emit(EVENTS.RENDER);
    }

    /**
     * Apply base styles
     */
    applyBaseStyles() {
        this.toolbarElement.style.display = 'flex';
        this.toolbarElement.style.alignItems = 'center';
        this.toolbarElement.style.width = '100%';

        // Apply height
        const currentBreakpoint = this.responsive.getCurrentBreakpoint();
        const height = this.getResponsiveValue(this.options.height, currentBreakpoint);
        this.toolbarElement.style.height = height;

        // Apply padding
        const padding = this.getResponsiveValue(this.options.padding, currentBreakpoint);
        const paddingValue = SPACING_SCALE[padding] || padding;
        this.toolbarElement.style.paddingLeft = paddingValue;
        this.toolbarElement.style.paddingRight = paddingValue;

        // Apply elevation
        const elevation = FlexToolbar.ELEVATIONS[this.options.elevation] || FlexToolbar.ELEVATIONS[2];
        this.toolbarElement.style.boxShadow = elevation;

        // Apply overflow
        if (this.options.overflow === 'scroll') {
            this.toolbarElement.style.overflowX = 'auto';
        } else if (this.options.overflow === 'hidden') {
            this.toolbarElement.style.overflowX = 'hidden';
        }
    }

    /**
     * Apply theme
     */
    applyTheme() {
        const { theme } = this.options;

        if (FlexToolbar.THEMES[theme]) {
            const themeConfig = FlexToolbar.THEMES[theme];
            this.toolbarElement.style.backgroundColor = themeConfig.background;
            this.toolbarElement.style.color = themeConfig.color;
            this.toolbarElement.style.borderBottom = `1px solid ${themeConfig.border}`;
        } else if (typeof theme === 'object') {
            // Custom theme
            if (theme.background) this.toolbarElement.style.backgroundColor = theme.background;
            if (theme.color) this.toolbarElement.style.color = theme.color;
            if (theme.border) this.toolbarElement.style.borderBottom = `1px solid ${theme.border}`;
        }
    }

    /**
     * Apply positioning (sticky, fixed, etc.)
     */
    applyPositioning() {
        const { position, sticky, stickyOffset } = this.options;

        if (sticky) {
            this.toolbarElement.style.position = 'sticky';

            if (position === 'top') {
                this.toolbarElement.style.top = `${stickyOffset}px`;
                this.toolbarElement.style.zIndex = '1000';
            } else if (position === 'bottom') {
                this.toolbarElement.style.bottom = `${stickyOffset}px`;
                this.toolbarElement.style.zIndex = '1000';
            }
        }
    }

    /**
     * Render action groups
     */
    renderActions() {
        // Clear existing actions
        this.toolbarElement.innerHTML = '';
        this.actionElements = { left: [], center: [], right: [] };

        // Create action groups
        ['left', 'center', 'right'].forEach(position => {
            if (this.options.actions[position] && this.options.actions[position].length > 0) {
                this.renderActionGroup(position);
            }
        });
    }

    /**
     * Render action group (left, center, or right)
     */
    renderActionGroup(position) {
        const group = this.createElement('div', ['flex-toolbar__group', `flex-toolbar__group--${position}`]);

        // Set group layout
        group.style.display = 'flex';
        group.style.alignItems = 'center';
        group.style.gap = SPACING_SCALE[2]; // 0.5rem gap

        // Set group positioning
        if (position === 'left') {
            group.style.marginRight = 'auto';
        } else if (position === 'center') {
            group.style.marginLeft = 'auto';
            group.style.marginRight = 'auto';
        } else if (position === 'right') {
            group.style.marginLeft = 'auto';
        }

        // Add actions to group
        this.options.actions[position].forEach((action, index) => {
            const actionElement = this.createActionElement(action, position, index);
            group.appendChild(actionElement);
            this.actionElements[position].push(actionElement);
        });

        // Add divider if configured
        if (this.options.dividers && position !== 'right') {
            const divider = this.createElement('div', ['flex-toolbar__divider']);
            divider.style.width = '1px';
            divider.style.height = '24px';
            divider.style.backgroundColor = 'currentColor';
            divider.style.opacity = '0.2';
            divider.style.marginLeft = SPACING_SCALE[2];
            divider.style.marginRight = SPACING_SCALE[2];
            this.toolbarElement.appendChild(divider);
        }

        this.toolbarElement.appendChild(group);
    }

    /**
     * Create action element
     */
    createActionElement(action, position, index) {
        const actionWrapper = this.createElement('div', ['flex-toolbar__action']);

        // Add action content
        if (typeof action.content === 'string') {
            actionWrapper.innerHTML = action.content;
        } else if (action.content instanceof HTMLElement) {
            actionWrapper.appendChild(action.content);
        } else if (action.content && typeof action.content.getElement === 'function') {
            actionWrapper.appendChild(action.content.getElement());
        }

        // Add custom action classes
        if (action.classes) {
            actionWrapper.classList.add(...action.classes);
        }

        // Store action ID
        if (action.id) {
            actionWrapper.dataset.actionId = action.id;
        } else {
            actionWrapper.dataset.actionId = `${position}-${index}`;
        }

        // Apply action-specific styles
        if (action.style) {
            Object.assign(actionWrapper.style, action.style);
        }

        return actionWrapper;
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Listen for breakpoint changes
        this.responsive.onBreakpointChange(() => {
            this.handleResponsiveChange();
            this.emit(EVENTS.UPDATE, {
                breakpoint: this.responsive.getCurrentBreakpoint()
            });
        });
    }

    /**
     * Handle responsive changes
     */
    handleResponsiveChange() {
        const currentBreakpoint = this.responsive.getCurrentBreakpoint();

        // Update height
        const height = this.getResponsiveValue(this.options.height, currentBreakpoint);
        this.toolbarElement.style.height = height;

        // Update padding
        const padding = this.getResponsiveValue(this.options.padding, currentBreakpoint);
        const paddingValue = SPACING_SCALE[padding] || padding;
        this.toolbarElement.style.paddingLeft = paddingValue;
        this.toolbarElement.style.paddingRight = paddingValue;

        // Handle responsive config
        if (this.options.responsive) {
            const responsive = this.options.responsive;

            // Update actions if responsive
            if (responsive.actions) {
                const newActions = this.getResponsiveValue(responsive.actions, currentBreakpoint);
                if (newActions) {
                    this.options.actions = newActions;
                    this.renderActions();
                }
            }
        }
    }

    /**
     * Add action to group
     * @param {string} position - left | center | right
     * @param {object} action - Action configuration
     * @param {number} index - Optional index
     */
    addAction(position, action, index = null) {
        if (!['left', 'center', 'right'].includes(position)) {
            console.warn(`FlexToolbar: Invalid position "${position}"`);
            return;
        }

        if (!this.options.actions[position]) {
            this.options.actions[position] = [];
        }

        if (index !== null && index >= 0) {
            this.options.actions[position].splice(index, 0, action);
        } else {
            this.options.actions[position].push(action);
        }

        this.renderActions();

        this.emit('action:add', { position, action, index });
    }

    /**
     * Remove action from group
     * @param {string} position - left | center | right
     * @param {string} actionId - Action ID
     */
    removeAction(position, actionId) {
        if (!this.options.actions[position]) return;

        const index = this.options.actions[position].findIndex(a => a.id === actionId);

        if (index === -1) {
            console.warn(`FlexToolbar: Action not found: ${actionId}`);
            return;
        }

        const removedAction = this.options.actions[position].splice(index, 1)[0];
        this.renderActions();

        this.emit('action:remove', { position, action: removedAction });
    }

    /**
     * Update action
     * @param {string} position - left | center | right
     * @param {string} actionId - Action ID
     * @param {object} updates - Updates to apply
     */
    updateAction(position, actionId, updates) {
        if (!this.options.actions[position]) return;

        const action = this.options.actions[position].find(a => a.id === actionId);

        if (!action) {
            console.warn(`FlexToolbar: Action not found: ${actionId}`);
            return;
        }

        Object.assign(action, updates);
        this.renderActions();

        this.emit('action:update', { position, actionId, updates });
    }

    /**
     * Set theme
     * @param {string|object} theme - Theme name or custom theme object
     */
    setTheme(theme) {
        this.options.theme = theme;
        this.applyTheme();

        this.emit(EVENTS.UPDATE, { theme });
    }

    /**
     * Set elevation
     * @param {number} elevation - Elevation level (0-5)
     */
    setElevation(elevation) {
        if (elevation < 0 || elevation > 5) {
            console.warn(`FlexToolbar: Elevation must be 0-5, got ${elevation}`);
            return;
        }

        this.options.elevation = elevation;
        const shadow = FlexToolbar.ELEVATIONS[elevation];
        this.toolbarElement.style.boxShadow = shadow;

        this.emit(EVENTS.UPDATE, { elevation });
    }

    /**
     * Set sticky state
     * @param {boolean} sticky - Whether toolbar should be sticky
     */
    setSticky(sticky) {
        this.options.sticky = sticky;
        this.applyPositioning();

        this.emit(EVENTS.UPDATE, { sticky });
    }

    /**
     * Get action element
     * @param {string} position - left | center | right
     * @param {string} actionId - Action ID
     * @returns {HTMLElement|null}
     */
    getActionElement(position, actionId) {
        const element = this.toolbarElement.querySelector(
            `.flex-toolbar__group--${position} [data-action-id="${actionId}"]`
        );
        return element || null;
    }

    /**
     * Get toolbar element
     * @returns {HTMLElement}
     */
    getElement() {
        return this.toolbarElement;
    }

    /**
     * Destroy the toolbar
     */
    destroy() {
        // Remove classes
        this.toolbarElement.classList.remove(
            'flex-toolbar',
            `flex-toolbar--${this.options.position}`,
            `flex-toolbar--${this.options.theme}`
        );

        if (this.options.classes.length > 0) {
            this.toolbarElement.classList.remove(...this.options.classes);
        }

        // Remove inline styles
        this.toolbarElement.style.display = '';
        this.toolbarElement.style.alignItems = '';
        this.toolbarElement.style.width = '';
        this.toolbarElement.style.height = '';
        this.toolbarElement.style.paddingLeft = '';
        this.toolbarElement.style.paddingRight = '';
        this.toolbarElement.style.boxShadow = '';
        this.toolbarElement.style.backgroundColor = '';
        this.toolbarElement.style.color = '';
        this.toolbarElement.style.borderBottom = '';
        this.toolbarElement.style.position = '';
        this.toolbarElement.style.top = '';
        this.toolbarElement.style.bottom = '';
        this.toolbarElement.style.zIndex = '';
        this.toolbarElement.style.overflowX = '';

        // Clear actions
        this.actionElements = { left: [], center: [], right: [] };

        this.emit(EVENTS.DESTROY);

        super.destroy();
    }
}
