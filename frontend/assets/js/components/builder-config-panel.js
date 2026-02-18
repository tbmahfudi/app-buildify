/**
 * Builder Configuration Panel
 *
 * Handles page metadata, module selection, menu creation, and RBAC permissions
 */
import { apiFetch } from '../api.js';

export class BuilderConfigPanel {
    constructor(editor) {
        this.editor = editor;
        this.config = {
            name: '',
            slug: '',
            description: '',
            module_name: null,
            route_path: '',
            menu_label: '',
            menu_icon: 'ph-duotone ph-file',
            menu_parent: null,
            menu_order: 100,
            show_in_menu: true,
            permission_code: '',
            permission_scope: 'company'
        };
        this.modules = [];
        this.menuItems = [];
    }

    async init() {
        // Load available modules
        await this.loadModules();

        // Load menu items for parent dropdown
        await this.loadMenuItems();

        // Add panel to GrapeJS
        this.addPanel();
    }

    async loadMenuItems() {
        try {
            const response = await apiFetch('/menu/admin');

            if (response.ok) {
                const data = await response.json();
                this.menuItems = data.items || [];
                console.log('Loaded menu items:', this.menuItems);
            } else {
                console.warn('Could not load menu items (this is optional)');
                this.menuItems = [];
            }
        } catch (error) {
            console.warn('Could not load menu items (this is optional):', error);
            this.menuItems = [];
        }
    }

    async loadModules() {
        try {
            const response = await apiFetch('/module-registry/enabled');

            if (response.ok) {
                const data = await response.json();
                console.log('Modules API response:', data);

                // The response has format: { modules: [...] }
                this.modules = (data.modules || []).map(m => ({
                    name: m.module_name || m.name,
                    display_name: m.display_name || m.module_name || m.name
                }));

                console.log('Loaded modules:', this.modules);
            } else {
                console.warn('Could not load modules (this is optional)');
                this.modules = [];
            }
        } catch (error) {
            console.warn('Could not load modules (this is optional):', error);
            this.modules = [];
        }
    }

    addPanel() {
        const panelManager = this.editor.Panels;

        // Add a custom panel for page configuration
        panelManager.addPanel({
            id: 'page-config-panel',
            el: '#page-config-container',
            buttons: []
        });

        // Create the config panel HTML
        this.renderConfigPanel();
    }

    renderConfigPanel() {
        const container = document.createElement('div');
        container.id = 'page-config-container';
        container.className = 'absolute top-16 right-4 w-80 bg-white border border-gray-200 rounded-lg shadow-lg p-4 max-h-[calc(100vh-100px)] overflow-y-auto z-50';
        container.innerHTML = `
            <div class="space-y-4">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-semibold text-gray-900">Page Configuration</h3>
                    <button id="close-config-panel" class="text-gray-500 hover:text-gray-700">
                        <i class="ph-duotone ph-x text-xl"></i>
                    </button>
                </div>

                <!-- Basic Info -->
                <div class="space-y-3">
                    <h4 class="font-medium text-gray-700 flex items-center gap-2">
                        <i class="ph-duotone ph-info"></i> Basic Information
                    </h4>

                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Page Name *</label>
                        <input type="text" id="config-page-name" class="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900" placeholder="My Custom Page">
                    </div>

                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Slug *</label>
                        <input type="text" id="config-slug" class="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900" placeholder="my-custom-page">
                        <p class="text-xs text-gray-500 mt-1">URL-friendly identifier</p>
                    </div>

                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
                        <textarea id="config-description" rows="2" class="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900" placeholder="Page description..."></textarea>
                    </div>

                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Route Path *</label>
                        <input type="text" id="config-route-path" class="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900" placeholder="#/my-page">
                        <p class="text-xs text-gray-500 mt-1">e.g., #/dashboard or #/module/page</p>
                    </div>
                </div>

                <!-- Module Selection -->
                <div class="space-y-3 pt-3 border-t border-gray-200">
                    <h4 class="font-medium text-gray-700 flex items-center gap-2">
                        <i class="ph-duotone ph-puzzle-piece"></i> Module Assignment
                    </h4>

                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Target Module</label>
                        <select id="config-module" class="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900">
                            <option value="">Core (No module)</option>
                        </select>
                        <p class="text-xs text-gray-500 mt-1">Page will inherit module permissions</p>
                    </div>
                </div>

                <!-- Menu Configuration -->
                <div class="space-y-3 pt-3 border-t border-gray-200">
                    <h4 class="font-medium text-gray-700 flex items-center gap-2">
                        <i class="ph-duotone ph-list"></i> Menu Configuration
                    </h4>

                    <div class="flex items-center gap-2">
                        <input type="checkbox" id="config-show-in-menu" class="rounded" checked>
                        <label for="config-show-in-menu" class="text-sm text-gray-700">Show in navigation menu</label>
                    </div>

                    <div id="menu-config-fields">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Menu Label</label>
                            <input type="text" id="config-menu-label" class="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900" placeholder="My Page">
                        </div>

                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Icon</label>
                            <input type="text" id="config-menu-icon" class="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900" placeholder="ph-duotone ph-file">
                            <p class="text-xs text-gray-500 mt-1">Phosphor icon class</p>
                        </div>

                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Parent Menu</label>
                            <select id="config-menu-parent" class="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900">
                                <option value="">None (Top Level)</option>
                            </select>
                            <p class="text-xs text-gray-500 mt-1">Select parent menu or leave as top level</p>
                        </div>

                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Order</label>
                            <input type="number" id="config-menu-order" class="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900" value="100">
                        </div>
                    </div>
                </div>

                <!-- RBAC Configuration -->
                <div class="space-y-3 pt-3 border-t border-gray-200">
                    <h4 class="font-medium text-gray-700 flex items-center gap-2">
                        <i class="ph-duotone ph-shield-check"></i> Access Control
                    </h4>

                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Permission Code</label>
                        <input type="text" id="config-permission-code" class="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900" placeholder="module:page:read:company">
                        <p class="text-xs text-gray-500 mt-1">Format: resource:action:scope</p>
                    </div>

                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Scope</label>
                        <select id="config-permission-scope" class="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900">
                            <option value="all">All Tenants (Superuser)</option>
                            <option value="tenant">Tenant-wide</option>
                            <option value="company" selected>Company-specific</option>
                            <option value="department">Department-specific</option>
                            <option value="own">Own data only</option>
                        </select>
                    </div>
                </div>

                <!-- Action Buttons -->
                <div class="pt-3 border-t border-gray-200">
                    <button id="auto-generate-config" class="w-full px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-700 border border-blue-600 rounded-md hover:bg-blue-50 transition">
                        <i class="ph-duotone ph-magic-wand mr-2"></i>Auto-generate from name
                    </button>
                </div>
            </div>
        `;

        // Append to editor container
        document.getElementById('builder-container')?.appendChild(container);

        // Initially hide the panel
        container.style.display = 'none';

        // Add toggle button to editor toolbar
        this.addToggleButton();

        // Setup event listeners
        this.setupEventListeners(container);

        // Populate modules dropdown
        this.populateModulesDropdown();

        // Populate parent menu dropdown
        this.populateParentMenuDropdown();
    }

    addToggleButton() {
        // Attach event listener to the Configure button in the template
        const configBtn = document.getElementById('btn-config');
        if (configBtn) {
            configBtn.addEventListener('click', () => {
                const panel = document.getElementById('page-config-container');
                if (panel) {
                    panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
                }
            });
        } else {
            console.warn('Configure button (btn-config) not found in template');
        }
    }

    setupEventListeners(container) {
        // Close button
        container.querySelector('#close-config-panel')?.addEventListener('click', () => {
            container.style.display = 'none';
        });

        // Auto-generate button
        container.querySelector('#auto-generate-config')?.addEventListener('click', () => {
            this.autoGenerateConfig();
        });

        // Toggle menu fields
        container.querySelector('#config-show-in-menu')?.addEventListener('change', (e) => {
            const menuFields = container.querySelector('#menu-config-fields');
            if (menuFields) {
                menuFields.style.display = e.target.checked ? 'block' : 'none';
            }
        });

        // Sync name to slug
        container.querySelector('#config-page-name')?.addEventListener('input', (e) => {
            const slugInput = container.querySelector('#config-slug');
            if (slugInput && !slugInput.value) {
                slugInput.value = this.slugify(e.target.value);
            }
        });
    }

    populateModulesDropdown() {
        const select = document.getElementById('config-module');
        if (select) {
            this.modules.forEach(module => {
                const option = document.createElement('option');
                option.value = module.name || module;
                option.textContent = module.display_name || module;
                select.appendChild(option);
            });
        }
    }

    populateParentMenuDropdown(selectedValue = null) {
        const select = document.getElementById('config-menu-parent');
        if (!select) return;

        // Clear existing options except first
        select.innerHTML = '<option value="">None (Top Level)</option>';

        // Add menu items as options
        this.menuItems.forEach(item => {
            const option = document.createElement('option');
            option.value = item.id || item.code;
            option.textContent = item.title || item.label;
            if (item.id === selectedValue || item.code === selectedValue) {
                option.selected = true;
            }
            select.appendChild(option);
        });
    }

    autoGenerateConfig() {
        const nameInput = document.getElementById('config-page-name');
        const name = nameInput?.value || 'New Page';

        // Generate slug
        const slug = this.slugify(name);
        document.getElementById('config-slug').value = slug;

        // Generate route path
        const moduleName = document.getElementById('config-module')?.value;
        const routePath = moduleName ? `#/${moduleName}/${slug}` : `#/${slug}`;
        document.getElementById('config-route-path').value = routePath;

        // Generate menu label
        if (!document.getElementById('config-menu-label')?.value) {
            document.getElementById('config-menu-label').value = name;
        }

        // Generate permission code
        const resource = slug.replace(/-/g, '_');
        const module = moduleName || 'custom';
        const permissionCode = `${module}:${resource}:read:company`;
        document.getElementById('config-permission-code').value = permissionCode;
    }

    slugify(text) {
        return text
            .toLowerCase()
            .replace(/[^\w\s-]/g, '')
            .replace(/\s+/g, '-')
            .replace(/-+/g, '-')
            .trim();
    }

    getPageConfig() {
        return {
            name: document.getElementById('config-page-name')?.value || '',
            slug: document.getElementById('config-slug')?.value || '',
            description: document.getElementById('config-description')?.value || '',
            module_name: document.getElementById('config-module')?.value || null,
            route_path: document.getElementById('config-route-path')?.value || '',
            menu_label: document.getElementById('config-menu-label')?.value || '',
            menu_icon: document.getElementById('config-menu-icon')?.value || 'ph-duotone ph-file',
            menu_parent: document.getElementById('config-menu-parent')?.value || null,
            menu_order: parseInt(document.getElementById('config-menu-order')?.value) || 100,
            show_in_menu: document.getElementById('config-show-in-menu')?.checked || false,
            permission_code: document.getElementById('config-permission-code')?.value || '',
            permission_scope: document.getElementById('config-permission-scope')?.value || 'company'
        };
    }

    setPageConfig(config) {
        const nameEl = document.getElementById('config-page-name');
        const slugEl = document.getElementById('config-slug');
        const descEl = document.getElementById('config-description');
        const moduleEl = document.getElementById('config-module');
        const routeEl = document.getElementById('config-route-path');
        const menuLabelEl = document.getElementById('config-menu-label');
        const menuIconEl = document.getElementById('config-menu-icon');
        const menuParentEl = document.getElementById('config-menu-parent');
        const menuOrderEl = document.getElementById('config-menu-order');
        const showInMenuEl = document.getElementById('config-show-in-menu');
        const permCodeEl = document.getElementById('config-permission-code');
        const permScopeEl = document.getElementById('config-permission-scope');

        if (config.name && nameEl) nameEl.value = config.name;
        if (config.slug && slugEl) slugEl.value = config.slug;
        if (config.description && descEl) descEl.value = config.description;
        if (config.module_name && moduleEl) moduleEl.value = config.module_name;
        if (config.route_path && routeEl) routeEl.value = config.route_path;
        if (config.menu_label && menuLabelEl) menuLabelEl.value = config.menu_label;
        if (config.menu_icon && menuIconEl) menuIconEl.value = config.menu_icon;
        if (config.menu_parent && menuParentEl) menuParentEl.value = config.menu_parent;
        if (config.menu_order && menuOrderEl) menuOrderEl.value = config.menu_order;
        if (config.show_in_menu !== undefined && showInMenuEl) showInMenuEl.checked = config.show_in_menu;
        if (config.permission_code && permCodeEl) permCodeEl.value = config.permission_code;
        if (config.permission_scope && permScopeEl) permScopeEl.value = config.permission_scope;
    }
}
