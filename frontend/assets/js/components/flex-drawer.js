/**
 * FlexDrawer - Flexible Drawer/Slide-out Panel Component
 *
 * A reusable drawer component with Tailwind styling supporting:
 * - Multiple positions (left, right, top, bottom)
 * - Multiple sizes
 * - Backdrop overlay
 * - Keyboard navigation (ESC to close)
 * - Focus trapping
 * - Custom header and footer
 * - Actions/buttons
 *
 * @author Claude Code
 * @version 1.0.0
 */

import BaseComponent from '../core/base-component.js';

export default class FlexDrawer extends BaseComponent {
    static DEFAULTS = {
        position: 'right',          // left | right | top | bottom
        size: 'md',                 // xs | sm | md | lg | xl | full
        title: '',
        subtitle: '',
        content: '',                // HTML string or element
        backdrop: true,
        backdropDismiss: true,
        keyboard: true,             // ESC to close
        closeButton: true,
        actions: [],                // Footer buttons
        persistent: false,          // Prevent closing
        trapFocus: true,
        returnFocus: true,
        classes: [],
        onOpen: null,
        onClose: null
    };

    static SIZES = {
        xs: '256px',
        sm: '384px',
        md: '512px',
        lg: '768px',
        xl: '1024px',
        full: '100%'
    };

    constructor(container, options = {}) {
        super(container, options);

        this.state = {
            open: false,
            previousActiveElement: null
        };

        this.backdropElement = null;
        this.drawerElement = null;
        this.init();
    }

    init() {
        this.render();
        this.emit('init');
    }

    render() {
        // Create backdrop
        this.backdropElement = document.createElement('div');
        this.backdropElement.className = 'fixed inset-0 bg-gray-900 bg-opacity-50 z-40 opacity-0 invisible transition-all duration-300';

        // Create drawer
        this.drawerElement = document.createElement('div');
        const isVertical = this.options.position === 'left' || this.options.position === 'right';
        const size = FlexDrawer.SIZES[this.options.size];

        const positionClasses = {
            left: `left-0 top-0 bottom-0 -translate-x-full ${isVertical ? `w-[${size}]` : 'w-full'}`,
            right: `right-0 top-0 bottom-0 translate-x-full ${isVertical ? `w-[${size}]` : 'w-full'}`,
            top: `top-0 left-0 right-0 -translate-y-full ${!isVertical ? `h-[${size}]` : 'h-full'}`,
            bottom: `bottom-0 left-0 right-0 translate-y-full ${!isVertical ? `h-[${size}]` : 'h-full'}`
        };

        this.drawerElement.className = `fixed bg-white shadow-xl z-50 flex flex-col transition-transform duration-300 ${positionClasses[this.options.position]} ${this.options.classes.join(' ')}`;
        this.drawerElement.style.maxWidth = isVertical ? size : '100%';
        this.drawerElement.style.maxHeight = !isVertical ? size : '100%';

        // Header
        const header = document.createElement('div');
        header.className = 'flex items-start justify-between p-6 border-b border-gray-200';

        const titleWrapper = document.createElement('div');
        titleWrapper.className = 'flex-1';

        if (this.options.title) {
            const title = document.createElement('h3');
            title.className = 'text-xl font-semibold text-gray-900';
            title.textContent = this.options.title;
            titleWrapper.appendChild(title);
        }

        if (this.options.subtitle) {
            const subtitle = document.createElement('p');
            subtitle.className = 'mt-1 text-sm text-gray-600';
            subtitle.textContent = this.options.subtitle;
            titleWrapper.appendChild(subtitle);
        }

        header.appendChild(titleWrapper);

        if (this.options.closeButton) {
            const closeBtn = document.createElement('button');
            closeBtn.className = 'text-gray-400 hover:text-gray-600 transition';
            closeBtn.innerHTML = '<i class="ph ph-x text-2xl"></i>';
            closeBtn.setAttribute('data-close', 'true');
            header.appendChild(closeBtn);
        }

        this.drawerElement.appendChild(header);

        // Content
        const contentWrapper = document.createElement('div');
        contentWrapper.className = 'flex-1 p-6 overflow-y-auto';

        if (typeof this.options.content === 'string') {
            contentWrapper.innerHTML = this.options.content;
        } else if (this.options.content instanceof HTMLElement) {
            contentWrapper.appendChild(this.options.content);
        }

        this.drawerElement.appendChild(contentWrapper);

        // Footer
        if (this.options.actions.length > 0) {
            const footer = document.createElement('div');
            footer.className = 'flex items-center justify-end gap-3 p-6 border-t border-gray-200';

            this.options.actions.forEach((action, index) => {
                const button = document.createElement('button');
                const variantClasses = {
                    primary: 'bg-blue-600 hover:bg-blue-700 text-white',
                    secondary: 'bg-gray-600 hover:bg-gray-700 text-white',
                    ghost: 'bg-transparent hover:bg-gray-100 text-gray-700 border border-gray-300'
                };

                button.className = `px-4 py-2 rounded-lg font-medium transition ${variantClasses[action.variant || 'ghost']}`;
                button.textContent = action.label;
                button.setAttribute('data-action', index);

                footer.appendChild(button);
            });

            this.drawerElement.appendChild(footer);
        }

        // Append to body
        document.body.appendChild(this.backdropElement);
        document.body.appendChild(this.drawerElement);

        this.attachEventListeners();
    }

    attachEventListeners() {
        // Close button
        const closeBtn = this.drawerElement.querySelector('[data-close]');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.close());
        }

        // Backdrop click
        if (this.options.backdropDismiss) {
            this.backdropElement.addEventListener('click', () => this.close());
        }

        // Keyboard
        if (this.options.keyboard) {
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && this.state.open) {
                    this.close();
                }
            });
        }

        // Actions
        this.drawerElement.addEventListener('click', (e) => {
            const actionBtn = e.target.closest('[data-action]');
            if (actionBtn) {
                const index = parseInt(actionBtn.getAttribute('data-action'));
                const action = this.options.actions[index];
                if (action.onClick) {
                    action.onClick();
                }
                this.emit('action', { action, index });
            }
        });
    }

    open() {
        if (this.state.open) return;

        this.state.open = true;
        this.state.previousActiveElement = document.activeElement;

        // Show backdrop
        this.backdropElement.classList.remove('opacity-0', 'invisible');
        this.backdropElement.classList.add('opacity-100', 'visible');

        // Show drawer
        setTimeout(() => {
            this.drawerElement.classList.remove('-translate-x-full', 'translate-x-full', '-translate-y-full', 'translate-y-full');
            this.drawerElement.classList.add('translate-x-0', 'translate-y-0');
        }, 10);

        // Trap focus
        if (this.options.trapFocus) {
            this.trapFocus();
        }

        if (this.options.onOpen) {
            this.options.onOpen();
        }

        this.emit('open');
    }

    close() {
        if (!this.state.open || this.options.persistent) return;

        this.state.open = false;

        // Hide backdrop
        this.backdropElement.classList.remove('opacity-100', 'visible');
        this.backdropElement.classList.add('opacity-0', 'invisible');

        // Hide drawer
        const positionTransform = {
            left: '-translate-x-full',
            right: 'translate-x-full',
            top: '-translate-y-full',
            bottom: 'translate-y-full'
        };

        this.drawerElement.classList.remove('translate-x-0', 'translate-y-0');
        this.drawerElement.classList.add(positionTransform[this.options.position]);

        // Return focus
        if (this.options.returnFocus && this.state.previousActiveElement) {
            this.state.previousActiveElement.focus();
        }

        if (this.options.onClose) {
            this.options.onClose();
        }

        this.emit('close');
    }

    toggle() {
        if (this.state.open) {
            this.close();
        } else {
            this.open();
        }
    }

    trapFocus() {
        const focusableElements = this.drawerElement.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );

        if (focusableElements.length === 0) return;

        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        firstElement.focus();

        this.drawerElement.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                if (e.shiftKey) {
                    if (document.activeElement === firstElement) {
                        e.preventDefault();
                        lastElement.focus();
                    }
                } else {
                    if (document.activeElement === lastElement) {
                        e.preventDefault();
                        firstElement.focus();
                    }
                }
            }
        });
    }

    setContent(content) {
        const contentWrapper = this.drawerElement.querySelector('.overflow-y-auto');
        if (contentWrapper) {
            if (typeof content === 'string') {
                contentWrapper.innerHTML = content;
            } else if (content instanceof HTMLElement) {
                contentWrapper.innerHTML = '';
                contentWrapper.appendChild(content);
            }
        }
        this.emit('contentChange', { content });
    }

    destroy() {
        if (this.backdropElement) {
            this.backdropElement.remove();
        }
        if (this.drawerElement) {
            this.drawerElement.remove();
        }
        super.destroy();
    }
}
