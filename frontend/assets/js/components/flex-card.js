/**
 * FlexCard - Flexible Card/Panel Component
 *
 * A reusable card component with Tailwind styling supporting:
 * - Customizable header with title, subtitle, actions, and badges
 * - Collapsible/expandable sections
 * - Footer support
 * - Loading state overlay
 * - Multiple variants and sizes
 * - RBAC integration
 *
 * @author Claude Code
 * @version 1.0.0
 */

import { hasPermission } from '../rbac.js';

export class FlexCard {
    /**
     * Create a new FlexCard instance
     * @param {string|HTMLElement} container - Container selector or element
     * @param {Object} options - Configuration options
     */
    constructor(container, options = {}) {
        this.container = typeof container === 'string'
            ? document.querySelector(container)
            : container;

        if (!this.container) {
            throw new Error('FlexCard: Container not found');
        }

        this.options = {
            // Header options
            title: '',
            subtitle: '',
            icon: null, // Phosphor icon class
            badge: null, // {text, variant: 'primary'|'success'|'danger'|'warning'|'info'}

            // Actions (buttons in header)
            actions: [], // [{label, icon, onClick, variant, rbacPermission}]

            // Body options
            content: null, // HTML string or element
            collapsible: false,
            collapsed: false,

            // Footer options
            footer: null, // HTML string or element
            footerActions: [], // [{label, icon, onClick, variant, rbacPermission}]

            // Styling
            variant: 'default', // default, bordered, shadowed, flat
            size: 'md', // sm, md, lg, xl
            headerClass: '',
            bodyClass: '',
            footerClass: '',

            // State
            loading: false,

            // Callbacks
            onCollapse: null,
            onExpand: null,

            ...options
        };

        this.state = {
            collapsed: this.options.collapsed,
            loading: this.options.loading
        };

        this.elements = {};
        this.render();
    }

    /**
     * Render the card
     */
    render() {
        const card = document.createElement('div');
        card.className = this.getCardClasses();

        // Header
        if (this.shouldRenderHeader()) {
            card.appendChild(this.renderHeader());
        }

        // Body
        this.elements.body = this.renderBody();
        card.appendChild(this.elements.body);

        // Footer
        if (this.shouldRenderFooter()) {
            card.appendChild(this.renderFooter());
        }

        // Loading overlay
        this.elements.loadingOverlay = this.renderLoadingOverlay();
        card.appendChild(this.elements.loadingOverlay);

        // Clear container and append card
        this.container.innerHTML = '';
        this.container.appendChild(card);
        this.elements.card = card;

        // Apply initial state
        if (this.state.collapsed) {
            this.elements.body.style.display = 'none';
        }
        if (this.state.loading) {
            this.elements.loadingOverlay.style.display = 'flex';
        }
    }

    /**
     * Get card base classes based on variant and size
     */
    getCardClasses() {
        const baseClasses = 'relative bg-white rounded-lg overflow-hidden';

        const variantClasses = {
            default: 'border border-gray-200',
            bordered: 'border-2 border-gray-300',
            shadowed: 'shadow-lg border border-gray-100',
            flat: 'shadow-none border-0'
        };

        const sizeClasses = {
            sm: 'text-sm',
            md: '',
            lg: 'text-lg',
            xl: 'text-xl'
        };

        return `${baseClasses} ${variantClasses[this.options.variant]} ${sizeClasses[this.options.size]}`;
    }

    /**
     * Check if header should be rendered
     */
    shouldRenderHeader() {
        return this.options.title ||
               this.options.subtitle ||
               this.options.actions.length > 0 ||
               this.options.badge ||
               this.options.collapsible;
    }

    /**
     * Render header section
     */
    renderHeader() {
        const header = document.createElement('div');
        header.className = `flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-gray-50 ${this.options.headerClass}`;

        // Left side: Icon, Title, Subtitle, Badge
        const leftSide = document.createElement('div');
        leftSide.className = 'flex items-center gap-3 flex-1 min-w-0';

        // Collapse button
        if (this.options.collapsible) {
            const collapseBtn = document.createElement('button');
            collapseBtn.className = 'flex-shrink-0 text-gray-500 hover:text-gray-700 transition-transform duration-200';
            collapseBtn.innerHTML = '<i class="ph ph-caret-down"></i>';
            collapseBtn.onclick = () => this.toggle();
            this.elements.collapseBtn = collapseBtn;
            leftSide.appendChild(collapseBtn);
        }

        // Icon
        if (this.options.icon) {
            const iconEl = document.createElement('i');
            iconEl.className = `${this.options.icon} text-xl text-gray-600 flex-shrink-0`;
            leftSide.appendChild(iconEl);
        }

        // Title and subtitle
        if (this.options.title || this.options.subtitle) {
            const textContainer = document.createElement('div');
            textContainer.className = 'min-w-0 flex-1';

            if (this.options.title) {
                const title = document.createElement('h3');
                title.className = 'text-lg font-semibold text-gray-900 truncate';
                title.textContent = this.options.title;
                textContainer.appendChild(title);
            }

            if (this.options.subtitle) {
                const subtitle = document.createElement('p');
                subtitle.className = 'text-sm text-gray-500 truncate';
                subtitle.textContent = this.options.subtitle;
                textContainer.appendChild(subtitle);
            }

            leftSide.appendChild(textContainer);
        }

        // Badge
        if (this.options.badge) {
            const badge = this.renderBadge(this.options.badge);
            leftSide.appendChild(badge);
        }

        header.appendChild(leftSide);

        // Right side: Actions
        if (this.options.actions.length > 0) {
            const actionsContainer = document.createElement('div');
            actionsContainer.className = 'flex items-center gap-2 flex-shrink-0 ml-4';

            this.options.actions.forEach(action => {
                // Check RBAC permission
                if (action.rbacPermission && !hasPermission(action.rbacPermission)) {
                    return;
                }

                const btn = this.renderActionButton(action);
                actionsContainer.appendChild(btn);
            });

            header.appendChild(actionsContainer);
        }

        return header;
    }

    /**
     * Render badge
     */
    renderBadge(badge) {
        const badgeEl = document.createElement('span');

        const variantClasses = {
            primary: 'bg-blue-100 text-blue-800',
            success: 'bg-green-100 text-green-800',
            danger: 'bg-red-100 text-red-800',
            warning: 'bg-yellow-100 text-yellow-800',
            info: 'bg-indigo-100 text-indigo-800',
            default: 'bg-gray-100 text-gray-800'
        };

        const variant = badge.variant || 'default';
        badgeEl.className = `px-2.5 py-0.5 rounded-full text-xs font-medium flex-shrink-0 ${variantClasses[variant]}`;
        badgeEl.textContent = badge.text;

        return badgeEl;
    }

    /**
     * Render action button
     */
    renderActionButton(action) {
        const btn = document.createElement('button');

        const variantClasses = {
            primary: 'bg-blue-500 hover:bg-blue-600 text-white',
            secondary: 'bg-gray-500 hover:bg-gray-600 text-white',
            success: 'bg-green-500 hover:bg-green-600 text-white',
            danger: 'bg-red-500 hover:bg-red-600 text-white',
            warning: 'bg-yellow-500 hover:bg-yellow-600 text-white',
            ghost: 'bg-transparent hover:bg-gray-100 text-gray-700',
            link: 'bg-transparent hover:bg-blue-50 text-blue-600'
        };

        const variant = action.variant || 'ghost';
        btn.className = `px-3 py-1.5 rounded-md text-sm font-medium transition-colors duration-200 flex items-center gap-2 ${variantClasses[variant]}`;

        if (action.icon) {
            btn.innerHTML = `<i class="${action.icon}"></i>`;
        }

        if (action.label) {
            btn.innerHTML += `<span>${action.label}</span>`;
        } else if (action.icon) {
            // Icon only button - make it square
            btn.classList.add('px-2');
        }

        if (action.onClick) {
            btn.onclick = action.onClick;
        }

        if (action.disabled) {
            btn.disabled = true;
            btn.classList.add('opacity-50', 'cursor-not-allowed');
        }

        return btn;
    }

    /**
     * Render body section
     */
    renderBody() {
        const body = document.createElement('div');
        body.className = `px-6 py-4 ${this.options.bodyClass}`;

        if (this.options.content) {
            if (typeof this.options.content === 'string') {
                body.innerHTML = this.options.content;
            } else if (this.options.content instanceof HTMLElement) {
                body.appendChild(this.options.content);
            }
        }

        return body;
    }

    /**
     * Check if footer should be rendered
     */
    shouldRenderFooter() {
        return this.options.footer || this.options.footerActions.length > 0;
    }

    /**
     * Render footer section
     */
    renderFooter() {
        const footer = document.createElement('div');
        footer.className = `px-6 py-4 border-t border-gray-200 bg-gray-50 ${this.options.footerClass}`;

        if (this.options.footer) {
            const content = document.createElement('div');
            if (typeof this.options.footer === 'string') {
                content.innerHTML = this.options.footer;
            } else if (this.options.footer instanceof HTMLElement) {
                content.appendChild(this.options.footer);
            }
            footer.appendChild(content);
        }

        if (this.options.footerActions.length > 0) {
            const actionsContainer = document.createElement('div');
            actionsContainer.className = 'flex items-center justify-end gap-2 mt-3';

            this.options.footerActions.forEach(action => {
                // Check RBAC permission
                if (action.rbacPermission && !hasPermission(action.rbacPermission)) {
                    return;
                }

                const btn = this.renderActionButton(action);
                actionsContainer.appendChild(btn);
            });

            footer.appendChild(actionsContainer);
        }

        return footer;
    }

    /**
     * Render loading overlay
     */
    renderLoadingOverlay() {
        const overlay = document.createElement('div');
        overlay.className = 'absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center';
        overlay.style.display = 'none';
        overlay.innerHTML = `
            <div class="flex flex-col items-center gap-3">
                <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
                <span class="text-sm text-gray-600">Loading...</span>
            </div>
        `;
        return overlay;
    }

    /**
     * Toggle collapse/expand
     */
    toggle() {
        if (this.state.collapsed) {
            this.expand();
        } else {
            this.collapse();
        }
    }

    /**
     * Collapse the card body
     */
    collapse() {
        if (!this.options.collapsible || this.state.collapsed) return;

        this.state.collapsed = true;
        this.elements.body.style.display = 'none';

        if (this.elements.collapseBtn) {
            this.elements.collapseBtn.style.transform = 'rotate(-90deg)';
        }

        if (this.options.onCollapse) {
            this.options.onCollapse();
        }
    }

    /**
     * Expand the card body
     */
    expand() {
        if (!this.options.collapsible || !this.state.collapsed) return;

        this.state.collapsed = false;
        this.elements.body.style.display = 'block';

        if (this.elements.collapseBtn) {
            this.elements.collapseBtn.style.transform = 'rotate(0deg)';
        }

        if (this.options.onExpand) {
            this.options.onExpand();
        }
    }

    /**
     * Set loading state
     */
    setLoading(loading) {
        this.state.loading = loading;
        if (this.elements.loadingOverlay) {
            this.elements.loadingOverlay.style.display = loading ? 'flex' : 'none';
        }
    }

    /**
     * Update card content
     */
    setContent(content) {
        this.options.content = content;
        if (this.elements.body) {
            this.elements.body.innerHTML = '';
            if (typeof content === 'string') {
                this.elements.body.innerHTML = content;
            } else if (content instanceof HTMLElement) {
                this.elements.body.appendChild(content);
            }
        }
    }

    /**
     * Update card title
     */
    setTitle(title) {
        this.options.title = title;
        this.render();
    }

    /**
     * Update badge
     */
    setBadge(badge) {
        this.options.badge = badge;
        this.render();
    }

    /**
     * Destroy the card
     */
    destroy() {
        if (this.container) {
            this.container.innerHTML = '';
        }
        this.elements = {};
    }

    /**
     * Get the card element
     */
    getElement() {
        return this.elements.card;
    }

    /**
     * Get the body element
     */
    getBodyElement() {
        return this.elements.body;
    }
}

export default FlexCard;
