/**
 * FlexModal - Flexible Modal/Dialog Component
 *
 * A reusable modal component with Tailwind styling supporting:
 * - Multiple sizes (sm, md, lg, xl, full)
 * - Header with close button
 * - Scrollable body
 * - Sticky footer with action buttons
 * - Backdrop blur/opacity control
 * - Keyboard navigation (ESC to close, tab trapping)
 * - RBAC integration
 *
 * @author Claude Code
 * @version 1.0.0
 */

import { hasPermission } from '../rbac.js';

export class FlexModal {
    static openModals = [];
    static zIndexBase = 1000;

    /**
     * Create a new FlexModal instance
     * @param {Object} options - Configuration options
     */
    constructor(options = {}) {
        this.options = {
            // Header options
            title: '',
            subtitle: '',
            icon: null, // Phosphor icon class
            showClose: true,

            // Body options
            content: null, // HTML string or element
            scrollable: true,

            // Footer options
            footer: null, // HTML string or element
            footerActions: [], // [{label, icon, onClick, variant, rbacPermission, disabled}]
            showFooter: true,

            // Styling
            size: 'md', // sm, md, lg, xl, full
            backdrop: true, // Show backdrop
            backdropBlur: true,
            backdropDismiss: true, // Click backdrop to close
            centered: true, // Center modal vertically

            // Behavior
            keyboard: true, // ESC to close
            trapFocus: true, // Trap tab navigation
            autoFocus: true, // Auto focus first input

            // Callbacks
            onShow: null,
            onHide: null,
            onShown: null,
            onHidden: null,

            ...options
        };

        this.state = {
            isOpen: false,
            zIndex: FlexModal.zIndexBase + (FlexModal.openModals.length * 10)
        };

        this.elements = {};
        this.previousActiveElement = null;
        this.render();
    }

    /**
     * Render the modal
     */
    render() {
        // Create backdrop
        this.elements.backdrop = this.renderBackdrop();

        // Create modal container
        this.elements.modal = this.renderModal();

        // Append to body
        document.body.appendChild(this.elements.backdrop);
        document.body.appendChild(this.elements.modal);

        // Setup event listeners
        this.setupEventListeners();
    }

    /**
     * Render backdrop
     */
    renderBackdrop() {
        const backdrop = document.createElement('div');
        backdrop.className = `fixed inset-0 bg-gray-900 transition-opacity duration-300 ${this.options.backdropBlur ? 'backdrop-blur-sm' : ''}`;
        backdrop.style.opacity = '0';
        backdrop.style.zIndex = this.state.zIndex;
        backdrop.style.display = 'none';

        if (this.options.backdropDismiss) {
            backdrop.onclick = (e) => {
                if (e.target === backdrop) {
                    this.hide();
                }
            };
        }

        return backdrop;
    }

    /**
     * Render modal
     */
    renderModal() {
        const container = document.createElement('div');
        container.className = `fixed inset-0 overflow-y-auto ${this.options.centered ? 'flex items-center justify-center' : ''} p-4`;
        container.style.zIndex = this.state.zIndex + 1;
        container.style.display = 'none';

        const modalWrapper = document.createElement('div');
        modalWrapper.className = `relative bg-white rounded-lg shadow-2xl ${this.getModalSizeClasses()} transform transition-all duration-300 scale-95 opacity-0`;
        modalWrapper.style.maxHeight = '90vh';
        modalWrapper.style.display = 'flex';
        modalWrapper.style.flexDirection = 'column';

        this.elements.modalWrapper = modalWrapper;

        // Header
        if (this.shouldRenderHeader()) {
            modalWrapper.appendChild(this.renderHeader());
        }

        // Body
        this.elements.body = this.renderBody();
        modalWrapper.appendChild(this.elements.body);

        // Footer
        if (this.shouldRenderFooter()) {
            modalWrapper.appendChild(this.renderFooter());
        }

        container.appendChild(modalWrapper);
        return container;
    }

    /**
     * Get modal size classes
     */
    getModalSizeClasses() {
        const sizeClasses = {
            sm: 'w-full max-w-md',
            md: 'w-full max-w-lg',
            lg: 'w-full max-w-2xl',
            xl: 'w-full max-w-4xl',
            full: 'w-full h-full max-w-full rounded-none'
        };

        return sizeClasses[this.options.size];
    }

    /**
     * Check if header should be rendered
     */
    shouldRenderHeader() {
        return this.options.title || this.options.subtitle || this.options.showClose;
    }

    /**
     * Render header
     */
    renderHeader() {
        const header = document.createElement('div');
        header.className = 'flex items-start justify-between px-6 py-4 border-b border-gray-200 flex-shrink-0';

        // Left side: Icon, Title, Subtitle
        const leftSide = document.createElement('div');
        leftSide.className = 'flex items-start gap-3 flex-1 min-w-0';

        // Icon
        if (this.options.icon) {
            const iconEl = document.createElement('i');
            iconEl.className = `${this.options.icon} text-2xl text-gray-600 flex-shrink-0 mt-0.5`;
            leftSide.appendChild(iconEl);
        }

        // Title and subtitle
        if (this.options.title || this.options.subtitle) {
            const textContainer = document.createElement('div');
            textContainer.className = 'min-w-0 flex-1';

            if (this.options.title) {
                const title = document.createElement('h3');
                title.className = 'text-xl font-semibold text-gray-900';
                title.textContent = this.options.title;
                textContainer.appendChild(title);
            }

            if (this.options.subtitle) {
                const subtitle = document.createElement('p');
                subtitle.className = 'text-sm text-gray-500 mt-1';
                subtitle.textContent = this.options.subtitle;
                textContainer.appendChild(subtitle);
            }

            leftSide.appendChild(textContainer);
        }

        header.appendChild(leftSide);

        // Right side: Close button
        if (this.options.showClose) {
            const closeBtn = document.createElement('button');
            closeBtn.className = 'flex-shrink-0 ml-4 text-gray-400 hover:text-gray-600 transition-colors duration-200';
            closeBtn.innerHTML = '<i class="ph ph-x text-xl"></i>';
            closeBtn.onclick = () => this.hide();
            this.elements.closeBtn = closeBtn;
            header.appendChild(closeBtn);
        }

        return header;
    }

    /**
     * Render body
     */
    renderBody() {
        const body = document.createElement('div');
        body.className = `px-6 py-4 flex-1 ${this.options.scrollable ? 'overflow-y-auto' : ''}`;

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
        return this.options.showFooter && (this.options.footer || this.options.footerActions.length > 0);
    }

    /**
     * Render footer
     */
    renderFooter() {
        const footer = document.createElement('div');
        footer.className = 'px-6 py-4 border-t border-gray-200 bg-gray-50 flex-shrink-0';

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
            actionsContainer.className = 'flex items-center justify-end gap-3';

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
            ghost: 'bg-transparent hover:bg-gray-100 text-gray-700 border border-gray-300',
            link: 'bg-transparent hover:bg-blue-50 text-blue-600'
        };

        const variant = action.variant || 'ghost';
        btn.className = `px-4 py-2 rounded-md text-sm font-medium transition-colors duration-200 flex items-center gap-2 ${variantClasses[variant]}`;

        if (action.icon) {
            btn.innerHTML = `<i class="${action.icon}"></i>`;
        }

        if (action.label) {
            btn.innerHTML += `<span>${action.label}</span>`;
        }

        if (action.onClick) {
            btn.onclick = (e) => {
                action.onClick(e, this);
            };
        }

        if (action.disabled) {
            btn.disabled = true;
            btn.classList.add('opacity-50', 'cursor-not-allowed');
        }

        return btn;
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Keyboard events
        if (this.options.keyboard) {
            this.keydownHandler = (e) => {
                if (e.key === 'Escape' && this.state.isOpen) {
                    // Only close the topmost modal
                    const topModal = FlexModal.openModals[FlexModal.openModals.length - 1];
                    if (topModal === this) {
                        this.hide();
                    }
                }
            };
            document.addEventListener('keydown', this.keydownHandler);
        }

        // Focus trap
        if (this.options.trapFocus) {
            this.focusHandler = (e) => {
                if (!this.state.isOpen) return;

                const focusableElements = this.getFocusableElements();
                const firstFocusable = focusableElements[0];
                const lastFocusable = focusableElements[focusableElements.length - 1];

                if (e.key === 'Tab') {
                    if (e.shiftKey) {
                        // Shift + Tab
                        if (document.activeElement === firstFocusable) {
                            e.preventDefault();
                            lastFocusable.focus();
                        }
                    } else {
                        // Tab
                        if (document.activeElement === lastFocusable) {
                            e.preventDefault();
                            firstFocusable.focus();
                        }
                    }
                }
            };
            document.addEventListener('keydown', this.focusHandler);
        }
    }

    /**
     * Get focusable elements in modal
     */
    getFocusableElements() {
        const selector = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
        return Array.from(this.elements.modalWrapper.querySelectorAll(selector)).filter(el => {
            return !el.disabled && el.offsetParent !== null;
        });
    }

    /**
     * Show the modal
     */
    show() {
        if (this.state.isOpen) return;

        // Trigger onShow callback
        if (this.options.onShow) {
            const shouldShow = this.options.onShow();
            if (shouldShow === false) return;
        }

        this.state.isOpen = true;
        FlexModal.openModals.push(this);

        // Store current active element
        this.previousActiveElement = document.activeElement;

        // Prevent body scroll
        if (FlexModal.openModals.length === 1) {
            document.body.style.overflow = 'hidden';
        }

        // Show backdrop
        if (this.options.backdrop) {
            this.elements.backdrop.style.display = 'block';
            requestAnimationFrame(() => {
                this.elements.backdrop.style.opacity = '0.5';
            });
        }

        // Show modal
        this.elements.modal.style.display = this.options.centered ? 'flex' : 'block';

        // Trigger animation
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                this.elements.modalWrapper.classList.remove('scale-95', 'opacity-0');
                this.elements.modalWrapper.classList.add('scale-100', 'opacity-100');
            });
        });

        // Auto focus first input
        if (this.options.autoFocus) {
            setTimeout(() => {
                const focusableElements = this.getFocusableElements();
                const firstInput = focusableElements.find(el => el.tagName === 'INPUT' || el.tagName === 'TEXTAREA');
                if (firstInput) {
                    firstInput.focus();
                } else if (focusableElements[0]) {
                    focusableElements[0].focus();
                }
            }, 300);
        }

        // Trigger onShown callback after animation
        setTimeout(() => {
            if (this.options.onShown) {
                this.options.onShown();
            }
        }, 300);
    }

    /**
     * Hide the modal
     */
    hide() {
        if (!this.state.isOpen) return;

        // Trigger onHide callback
        if (this.options.onHide) {
            const shouldHide = this.options.onHide();
            if (shouldHide === false) return;
        }

        this.state.isOpen = false;

        // Remove from open modals
        const index = FlexModal.openModals.indexOf(this);
        if (index > -1) {
            FlexModal.openModals.splice(index, 1);
        }

        // Trigger animation
        this.elements.modalWrapper.classList.remove('scale-100', 'opacity-100');
        this.elements.modalWrapper.classList.add('scale-95', 'opacity-0');

        // Hide backdrop
        if (this.options.backdrop) {
            this.elements.backdrop.style.opacity = '0';
        }

        // Hide modal after animation
        setTimeout(() => {
            this.elements.modal.style.display = 'none';
            if (this.options.backdrop) {
                this.elements.backdrop.style.display = 'none';
            }

            // Restore body scroll if no more modals
            if (FlexModal.openModals.length === 0) {
                document.body.style.overflow = '';
            }

            // Restore focus
            if (this.previousActiveElement) {
                this.previousActiveElement.focus();
                this.previousActiveElement = null;
            }

            // Trigger onHidden callback
            if (this.options.onHidden) {
                this.options.onHidden();
            }
        }, 300);
    }

    /**
     * Toggle modal visibility
     */
    toggle() {
        if (this.state.isOpen) {
            this.hide();
        } else {
            this.show();
        }
    }

    /**
     * Update modal content
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
     * Update modal title
     */
    setTitle(title) {
        this.options.title = title;
        // Re-render would be complex, so just update the text
        const titleEl = this.elements.modalWrapper.querySelector('h3');
        if (titleEl) {
            titleEl.textContent = title;
        }
    }

    /**
     * Destroy the modal
     */
    destroy() {
        this.hide();

        // Remove event listeners
        if (this.keydownHandler) {
            document.removeEventListener('keydown', this.keydownHandler);
        }
        if (this.focusHandler) {
            document.removeEventListener('keydown', this.focusHandler);
        }

        // Remove elements
        if (this.elements.backdrop && this.elements.backdrop.parentNode) {
            this.elements.backdrop.parentNode.removeChild(this.elements.backdrop);
        }
        if (this.elements.modal && this.elements.modal.parentNode) {
            this.elements.modal.parentNode.removeChild(this.elements.modal);
        }

        this.elements = {};
    }

    /**
     * Get modal element
     */
    getElement() {
        return this.elements.modalWrapper;
    }

    /**
     * Get body element
     */
    getBodyElement() {
        return this.elements.body;
    }

    /**
     * Check if modal is open
     */
    isOpen() {
        return this.state.isOpen;
    }
}

export default FlexModal;
