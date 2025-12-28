/**
 * Builder Configuration Panel
 *
 * Handles page metadata, module selection, menu creation, and RBAC permissions
 */

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
    }

    async init() {
        // Load available modules
        await this.loadModules();

        // Add panel to GrapeJS
        this.addPanel();
    }

    async loadModules() {
        try {
            const response = await fetch('/api/modules/enabled/names', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            if (response.ok) {
                this.modules = await response.json();
            }
        } catch (error) {
            console.error('Error loading modules:', error);
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
        container.className = 'absolute top-16 right-4 w-80 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-lg shadow-lg p-4 max-h-[calc(100vh-100px)] overflow-y-auto z-50';
        container.innerHTML = `
            <div class="space-y-4">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">Page Configuration</h3>
                    <button id="close-config-panel" class="text-gray-500 hover:text-gray-700">
                        <i class="ph-duotone ph-x text-xl"></i>
                    </button>
                </div>

                <!-- Basic Info -->
                <div class="space-y-3">
                    <h4 class="font-medium text-gray-700 dark:text-gray-300 flex items-center gap-2">
                        <i class="ph-duotone ph-info"></i> Basic Information
                    </h4>

                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Page Name *</label>
                        <input type="text" id="config-page-name" class="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-md bg-white dark:bg-slate-700 text-gray-900 dark:text-gray-100" placeholder="My Custom Page">
                    </div>

                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Slug *</label>
                        <input type="text" id="config-slug" class="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-md bg-white dark:bg-slate-700 text-gray-900 dark:text-gray-100" placeholder="my-custom-page">
                        <p class="text-xs text-gray-500 mt-1">URL-friendly identifier</p>
                    </div>

                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Description</label>
                        <textarea id="config-description" rows="2" class="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-md bg-white dark:bg-slate-700 text-gray-900 dark:text-gray-100" placeholder="Page description..."></textarea>
                    </div>

                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Route Path *</label>
                        <input type="text" id="config-route-path" class="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-md bg-white dark:bg-slate-700 text-gray-900 dark:text-gray-100" placeholder="#/my-page">
                        <p class="text-xs text-gray-500 mt-1">e.g., #/dashboard or #/module/page</p>
                    </div>
                </div>

                <!-- Module Selection -->
                <div class="space-y-3 pt-3 border-t border-gray-200 dark:border-slate-700">
                    <h4 class="font-medium text-gray-700 dark:text-gray-300 flex items-center gap-2">
                        <i class="ph-duotone ph-puzzle-piece"></i> Module Assignment
                    </h4>

                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Target Module</label>
                        <select id="config-module" class="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-md bg-white dark:bg-slate-700 text-gray-900 dark:text-gray-100">
                            <option value="">Core (No module)</option>
                        </select>
                        <p class="text-xs text-gray-500 mt-1">Page will inherit module permissions</p>
                    </div>
                </div>

                <!-- Menu Configuration -->
                <div class="space-y-3 pt-3 border-t border-gray-200 dark:border-slate-700">
                    <h4 class="font-medium text-gray-700 dark:text-gray-300 flex items-center gap-2">
                        <i class="ph-duotone ph-list"></i> Menu Configuration
                    </h4>

                    <div class="flex items-center gap-2">
                        <input type="checkbox" id="config-show-in-menu" class="rounded" checked>
                        <label for="config-show-in-menu" class="text-sm text-gray-700 dark:text-gray-300">Show in navigation menu</label>
                    </div>

                    <div id="menu-config-fields">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Menu Label</label>
                            <input type="text" id="config-menu-label" class="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-md bg-white dark:bg-slate-700 text-gray-900 dark:text-gray-100" placeholder="My Page">
                        </div>

                        <div>
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Icon</label>
                            <input type="text" id="config-menu-icon" class="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-md bg-white dark:bg-slate-700 text-gray-900 dark:text-gray-100" placeholder="ph-duotone ph-file">
                            <p class="text-xs text-gray-500 mt-1">Phosphor icon class</p>
                        </div>

                        <div>
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Parent Menu</label>
                            <input type="text" id="config-menu-parent" class="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-md bg-white dark:bg-slate-700 text-gray-900 dark:text-gray-100" placeholder="tools">
                            <p class="text-xs text-gray-500 mt-1">Leave empty for root level</p>
                        </div>

                        <div>
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Order</label>
                            <input type="number" id="config-menu-order" class="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-md bg-white dark:bg-slate-700 text-gray-900 dark:text-gray-100" value="100">
                        </div>
                    </div>
                </div>

                <!-- RBAC Configuration -->
                <div class="space-y-3 pt-3 border-t border-gray-200 dark:border-slate-700">
                    <h4 class="font-medium text-gray-700 dark:text-gray-300 flex items-center gap-2">
                        <i class="ph-duotone ph-shield-check"></i> Access Control
                    </h4>

                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Permission Code</label>
                        <input type="text" id="config-permission-code" class="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-md bg-white dark:bg-slate-700 text-gray-900 dark:text-gray-100" placeholder="module:page:read:company">
                        <p class="text-xs text-gray-500 mt-1">Format: resource:action:scope</p>
                    </div>

                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Scope</label>
                        <select id="config-permission-scope" class="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-md bg-white dark:bg-slate-700 text-gray-900 dark:text-gray-100">
                            <option value="all">All Tenants (Superuser)</option>
                            <option value="tenant">Tenant-wide</option>
                            <option value="company" selected>Company-specific</option>
                            <option value="department">Department-specific</option>
                            <option value="own">Own data only</option>
                        </select>
                    </div>
                </div>

                <!-- Action Buttons -->
                <div class="pt-3 border-t border-gray-200 dark:border-slate-700">
                    <button id="auto-generate-config" class="w-full px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-700 border border-blue-600 rounded-md hover:bg-blue-50 dark:hover:bg-blue-900/20 transition">
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
        if (config.name) document.getElementById('config-page-name').value = config.name;
        if (config.slug) document.getElementById('config-slug').value = config.slug;
        if (config.description) document.getElementById('config-description').value = config.description;
        if (config.module_name) document.getElementById('config-module').value = config.module_name;
        if (config.route_path) document.getElementById('config-route-path').value = config.route_path;
        if (config.menu_label) document.getElementById('config-menu-label').value = config.menu_label;
        if (config.menu_icon) document.getElementById('config-menu-icon').value = config.menu_icon;
        if (config.menu_parent) document.getElementById('config-menu-parent').value = config.menu_parent;
        if (config.menu_order) document.getElementById('config-menu-order').value = config.menu_order;
        if (config.show_in_menu !== undefined) document.getElementById('config-show-in-menu').checked = config.show_in_menu;
        if (config.permission_code) document.getElementById('config-permission-code').value = config.permission_code;
        if (config.permission_scope) document.getElementById('config-permission-scope').value = config.permission_scope;
    }
}
