/**
 * FlexTabs - Flexible Tabs Component
 *
 * A reusable tabs component with Tailwind styling supporting:
 * - Horizontal/vertical orientation
 * - Pill or underline style
 * - Icon support
 * - Badge/counter on tabs
 * - Lazy loading tab content
 * - URL hash synchronization
 * - Responsive behavior
 * - RBAC integration
 *
 * @author Claude Code
 * @version 1.0.0
 */

import { hasPermission } from '../rbac.js';

export class FlexTabs {
    /**
     * Create a new FlexTabs instance
     * @param {string|HTMLElement} container - Container selector or element
     * @param {Object} options - Configuration options
     */
    constructor(container, options = {}) {
        this.container = typeof container === 'string'
            ? document.querySelector(container)
            : container;

        if (!this.container) {
            throw new Error('FlexTabs: Container not found');
        }

        this.options = {
            // Tabs configuration
            tabs: [], // [{id, label, icon, badge, content, disabled, rbacPermission, onShow}]

            // Styling
            orientation: 'horizontal', // horizontal, vertical
            variant: 'underline', // underline, pills, enclosed
            size: 'md', // sm, md, lg
            fullWidth: false, // Tabs take full width

            // Behavior
            defaultTab: null, // ID of default tab (first tab if not specified)
            lazyLoad: false, // Load content only when tab is shown
            syncUrl: false, // Sync active tab with URL hash
            destroyOnHide: false, // Destroy content when tab is hidden

            // Callbacks
            onTabChange: null,
            onTabShown: null,
            onTabHidden: null,

            ...options
        };

        this.state = {
            activeTab: null,
            loadedTabs: new Set()
        };

        this.elements = {};
        this.render();
        this.initialize();
    }

    /**
     * Initialize tabs
     */
    initialize() {
        // Determine initial tab
        let initialTab = this.options.defaultTab;

        // Check URL hash if syncUrl is enabled
        if (this.options.syncUrl && window.location.hash) {
            const hashTab = window.location.hash.substring(1);
            const tab = this.options.tabs.find(t => t.id === hashTab);
            if (tab) {
                initialTab = hashTab;
            }
        }

        // Fallback to first available tab
        if (!initialTab) {
            const firstAvailableTab = this.options.tabs.find(t =>
                !t.disabled && (!t.rbacPermission || hasPermission(t.rbacPermission))
            );
            if (firstAvailableTab) {
                initialTab = firstAvailableTab.id;
            }
        }

        // Show initial tab
        if (initialTab) {
            this.showTab(initialTab, false);
        }

        // Setup URL sync
        if (this.options.syncUrl) {
            this.hashChangeHandler = () => {
                const hash = window.location.hash.substring(1);
                if (hash && hash !== this.state.activeTab) {
                    const tab = this.options.tabs.find(t => t.id === hash);
                    if (tab) {
                        this.showTab(hash);
                    }
                }
            };
            window.addEventListener('hashchange', this.hashChangeHandler);
        }
    }

    /**
     * Render the tabs
     */
    render() {
        const wrapper = document.createElement('div');
        wrapper.className = this.getWrapperClasses();

        // Tab list
        this.elements.tabList = this.renderTabList();
        wrapper.appendChild(this.elements.tabList);

        // Tab panels container
        this.elements.panelsContainer = this.renderPanelsContainer();
        wrapper.appendChild(this.elements.panelsContainer);

        // Clear container and append
        this.container.innerHTML = '';
        this.container.appendChild(wrapper);
        this.elements.wrapper = wrapper;
    }

    /**
     * Get wrapper classes
     */
    getWrapperClasses() {
        const baseClasses = 'flex gap-6';

        if (this.options.orientation === 'vertical') {
            return `${baseClasses} flex-row`;
        }

        return `${baseClasses} flex-col`;
    }

    /**
     * Render tab list
     */
    renderTabList() {
        const tabList = document.createElement('div');
        tabList.className = this.getTabListClasses();
        tabList.setAttribute('role', 'tablist');

        this.options.tabs.forEach(tab => {
            // Check RBAC permission
            if (tab.rbacPermission && !hasPermission(tab.rbacPermission)) {
                return;
            }

            const tabButton = this.renderTabButton(tab);
            tabList.appendChild(tabButton);
        });

        return tabList;
    }

    /**
     * Get tab list classes
     */
    getTabListClasses() {
        const baseClasses = 'flex';
        const orientationClasses = this.options.orientation === 'vertical'
            ? 'flex-col space-y-1'
            : 'flex-row space-x-1';

        const variantClasses = {
            underline: 'border-b border-gray-200',
            pills: '',
            enclosed: 'border-b border-gray-200'
        };

        const widthClasses = this.options.fullWidth && this.options.orientation === 'horizontal'
            ? 'w-full'
            : '';

        return `${baseClasses} ${orientationClasses} ${variantClasses[this.options.variant]} ${widthClasses}`;
    }

    /**
     * Render tab button
     */
    renderTabButton(tab) {
        const button = document.createElement('button');
        button.className = this.getTabButtonClasses(tab);
        button.setAttribute('role', 'tab');
        button.setAttribute('aria-controls', `panel-${tab.id}`);
        button.setAttribute('aria-selected', 'false');
        button.setAttribute('data-tab-id', tab.id);

        if (tab.disabled) {
            button.disabled = true;
        }

        // Icon
        if (tab.icon) {
            const icon = document.createElement('i');
            icon.className = `${tab.icon}`;
            button.appendChild(icon);
        }

        // Label
        const label = document.createElement('span');
        label.textContent = tab.label;
        button.appendChild(label);

        // Badge
        if (tab.badge !== undefined && tab.badge !== null) {
            const badge = this.renderBadge(tab.badge);
            button.appendChild(badge);
        }

        // Click handler
        button.onclick = () => {
            if (!tab.disabled) {
                this.showTab(tab.id);
            }
        };

        return button;
    }

    /**
     * Get tab button classes
     */
    getTabButtonClasses(tab) {
        const baseClasses = 'flex items-center gap-2 transition-all duration-200 font-medium';

        const sizeClasses = {
            sm: 'px-3 py-1.5 text-sm',
            md: 'px-4 py-2 text-base',
            lg: 'px-5 py-3 text-lg'
        };

        const variantClasses = {
            underline: 'border-b-2 border-transparent hover:border-gray-300 hover:text-gray-700 -mb-px',
            pills: 'rounded-md hover:bg-gray-100',
            enclosed: 'border border-transparent rounded-t-md hover:border-gray-300 -mb-px'
        };

        const disabledClasses = tab.disabled
            ? 'opacity-50 cursor-not-allowed'
            : 'cursor-pointer';

        const widthClasses = this.options.fullWidth && this.options.orientation === 'horizontal'
            ? 'flex-1 justify-center'
            : '';

        return `${baseClasses} ${sizeClasses[this.options.size]} ${variantClasses[this.options.variant]} ${disabledClasses} ${widthClasses} text-gray-600`;
    }

    /**
     * Render badge
     */
    renderBadge(badge) {
        const badgeEl = document.createElement('span');

        if (typeof badge === 'object') {
            const variantClasses = {
                primary: 'bg-blue-100 text-blue-800',
                success: 'bg-green-100 text-green-800',
                danger: 'bg-red-100 text-red-800',
                warning: 'bg-yellow-100 text-yellow-800',
                info: 'bg-indigo-100 text-indigo-800',
                default: 'bg-gray-100 text-gray-800'
            };

            const variant = badge.variant || 'default';
            badgeEl.className = `px-2 py-0.5 rounded-full text-xs font-medium ${variantClasses[variant]}`;
            badgeEl.textContent = badge.text;
        } else {
            // Simple number/string badge
            badgeEl.className = 'px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800';
            badgeEl.textContent = badge;
        }

        return badgeEl;
    }

    /**
     * Render panels container
     */
    renderPanelsContainer() {
        const container = document.createElement('div');
        container.className = 'flex-1';

        this.options.tabs.forEach(tab => {
            // Check RBAC permission
            if (tab.rbacPermission && !hasPermission(tab.rbacPermission)) {
                return;
            }

            const panel = this.renderTabPanel(tab);
            container.appendChild(panel);
        });

        return container;
    }

    /**
     * Render tab panel
     */
    renderTabPanel(tab) {
        const panel = document.createElement('div');
        panel.className = 'hidden';
        panel.setAttribute('role', 'tabpanel');
        panel.setAttribute('id', `panel-${tab.id}`);
        panel.setAttribute('aria-labelledby', `tab-${tab.id}`);
        panel.setAttribute('data-panel-id', tab.id);

        // Add content if not lazy loading
        if (!this.options.lazyLoad && tab.content) {
            this.loadTabContent(panel, tab);
        }

        return panel;
    }

    /**
     * Load tab content
     */
    loadTabContent(panel, tab) {
        if (typeof tab.content === 'string') {
            panel.innerHTML = tab.content;
        } else if (typeof tab.content === 'function') {
            const content = tab.content();
            if (typeof content === 'string') {
                panel.innerHTML = content;
            } else if (content instanceof HTMLElement) {
                panel.appendChild(content);
            } else if (content instanceof Promise) {
                // Handle async content
                panel.innerHTML = '<div class="flex items-center justify-center py-8"><div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div></div>';
                content.then(result => {
                    panel.innerHTML = '';
                    if (typeof result === 'string') {
                        panel.innerHTML = result;
                    } else if (result instanceof HTMLElement) {
                        panel.appendChild(result);
                    }
                });
            }
        } else if (tab.content instanceof HTMLElement) {
            panel.appendChild(tab.content);
        }

        this.state.loadedTabs.add(tab.id);
    }

    /**
     * Show tab
     */
    showTab(tabId, triggerCallback = true) {
        const tab = this.options.tabs.find(t => t.id === tabId);
        if (!tab || tab.disabled) return;

        // Check RBAC permission
        if (tab.rbacPermission && !hasPermission(tab.rbacPermission)) {
            return;
        }

        const previousTab = this.state.activeTab;

        // Trigger onTabChange callback
        if (triggerCallback && this.options.onTabChange) {
            const shouldChange = this.options.onTabChange(tabId, previousTab);
            if (shouldChange === false) return;
        }

        // Hide previous tab
        if (previousTab) {
            this.hideTab(previousTab);
        }

        // Update state
        this.state.activeTab = tabId;

        // Update tab button styles
        this.updateTabButtons(tabId);

        // Show panel
        const panel = this.elements.panelsContainer.querySelector(`[data-panel-id="${tabId}"]`);
        if (panel) {
            // Load content if lazy loading and not yet loaded
            if (this.options.lazyLoad && !this.state.loadedTabs.has(tabId)) {
                this.loadTabContent(panel, tab);
            }

            panel.classList.remove('hidden');
            panel.classList.add('block');
        }

        // Update URL if syncUrl is enabled
        if (this.options.syncUrl && triggerCallback) {
            window.location.hash = tabId;
        }

        // Trigger tab's onShow callback
        if (triggerCallback && tab.onShow) {
            tab.onShow();
        }

        // Trigger onTabShown callback
        if (triggerCallback && this.options.onTabShown) {
            this.options.onTabShown(tabId);
        }
    }

    /**
     * Hide tab
     */
    hideTab(tabId) {
        const tab = this.options.tabs.find(t => t.id === tabId);
        if (!tab) return;

        const panel = this.elements.panelsContainer.querySelector(`[data-panel-id="${tabId}"]`);
        if (panel) {
            panel.classList.remove('block');
            panel.classList.add('hidden');

            // Destroy content if option is enabled
            if (this.options.destroyOnHide) {
                panel.innerHTML = '';
                this.state.loadedTabs.delete(tabId);
            }
        }

        // Trigger onTabHidden callback
        if (this.options.onTabHidden) {
            this.options.onTabHidden(tabId);
        }
    }

    /**
     * Update tab button styles
     */
    updateTabButtons(activeTabId) {
        const buttons = this.elements.tabList.querySelectorAll('[data-tab-id]');

        buttons.forEach(button => {
            const tabId = button.getAttribute('data-tab-id');
            const isActive = tabId === activeTabId;

            button.setAttribute('aria-selected', isActive ? 'true' : 'false');

            // Remove all active styles
            button.classList.remove('text-blue-600', 'border-blue-500', 'bg-blue-50', 'border-gray-300');

            if (isActive) {
                // Add active styles based on variant
                if (this.options.variant === 'underline') {
                    button.classList.add('text-blue-600', 'border-blue-500');
                } else if (this.options.variant === 'pills') {
                    button.classList.add('bg-blue-50', 'text-blue-600');
                } else if (this.options.variant === 'enclosed') {
                    button.classList.add('text-blue-600', 'border-gray-300', 'bg-white');
                }
            } else {
                // Reset to default styles
                button.classList.add('text-gray-600');
            }
        });
    }

    /**
     * Add a new tab
     */
    addTab(tab, index = -1) {
        // Check if tab already exists
        if (this.options.tabs.find(t => t.id === tab.id)) {
            console.warn(`FlexTabs: Tab with id "${tab.id}" already exists`);
            return;
        }

        // Add to tabs array
        if (index >= 0 && index < this.options.tabs.length) {
            this.options.tabs.splice(index, 0, tab);
        } else {
            this.options.tabs.push(tab);
        }

        // Re-render
        this.render();

        // Re-initialize if needed
        if (this.state.activeTab) {
            this.showTab(this.state.activeTab, false);
        }
    }

    /**
     * Remove a tab
     */
    removeTab(tabId) {
        const index = this.options.tabs.findIndex(t => t.id === tabId);
        if (index === -1) return;

        // If removing active tab, show another tab
        if (this.state.activeTab === tabId) {
            const nextTab = this.options.tabs[index + 1] || this.options.tabs[index - 1];
            if (nextTab) {
                this.showTab(nextTab.id);
            }
        }

        // Remove from tabs array
        this.options.tabs.splice(index, 1);

        // Re-render
        this.render();
    }

    /**
     * Update tab badge
     */
    updateBadge(tabId, badge) {
        const tab = this.options.tabs.find(t => t.id === tabId);
        if (!tab) return;

        tab.badge = badge;

        // Update button
        const button = this.elements.tabList.querySelector(`[data-tab-id="${tabId}"]`);
        if (button) {
            const oldBadge = button.querySelector('span:last-child');
            if (oldBadge && oldBadge.classList.contains('rounded-full')) {
                oldBadge.remove();
            }

            if (badge !== undefined && badge !== null) {
                const newBadge = this.renderBadge(badge);
                button.appendChild(newBadge);
            }
        }
    }

    /**
     * Get active tab
     */
    getActiveTab() {
        return this.state.activeTab;
    }

    /**
     * Destroy the tabs
     */
    destroy() {
        // Remove event listener
        if (this.hashChangeHandler) {
            window.removeEventListener('hashchange', this.hashChangeHandler);
        }

        // Clear container
        if (this.container) {
            this.container.innerHTML = '';
        }

        this.elements = {};
        this.state = { activeTab: null, loadedTabs: new Set() };
    }
}

export default FlexTabs;
