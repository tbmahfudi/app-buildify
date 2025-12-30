/**
 * Builder Showcase Page - Display all pages created with UI Builder
 *
 * Shows published pages in a gallery/grid format with preview and actions
 *
 * Pattern: Template-based (similar to tenants.js)
 * - HTML template loaded from /assets/templates/builder-showcase.html
 * - This script listens for 'route:loaded' event
 * - Initializes showcase after template is in DOM
 */
import { apiFetch } from './api.js';
import { can } from './rbac.js';
import { showToast } from './ui-utils.js';
import { authService } from './auth-service.js';
import { FlexModal } from './components/flex-modal.js';

let showcasePage = null;

// Route change
document.addEventListener('route:loaded', async (event) => {
    console.log('Builder showcase event listener triggered. Route:', event.detail.route);
    if (event.detail.route === 'builder-showcase') {
        console.log('Route matched! Initializing showcase...');
        // Ensure DOM from template is ready
        setTimeout(async () => {
            try {
                if (!showcasePage) {
                    console.log('Creating new BuilderShowcasePage instance');
                    showcasePage = new BuilderShowcasePage();
                }
                await showcasePage.afterRender();
            } catch (error) {
                console.error('Error initializing showcase page:', error);
                showToast('Failed to initialize showcase page', 'error');
            }
        }, 0);
    } else {
        console.log('Route did not match. Expected: builder-showcase, Got:', event.detail.route);
    }
});

document.addEventListener('route:before-change', (event) => {
    if (event.detail.from === 'builder-showcase' && showcasePage) {
        showcasePage.cleanup();
        showcasePage = null;
    }
});

export class BuilderShowcasePage {
    constructor() {
        this.pages = [];
        this.viewMode = 'grid'; // 'grid' or 'list'
        this.filterStatus = 'all'; // 'all', 'published', 'draft'
    }

    async afterRender() {
        console.log('BuilderShowcasePage.afterRender() called');

        // Load pages
        await this.loadPages();

        // Setup event listeners
        this.setupEventListeners();

        console.log('BuilderShowcasePage.afterRender() completed');
    }

    setupEventListeners() {
        // View mode toggle
        document.getElementById('view-grid')?.addEventListener('click', () => {
            this.setViewMode('grid');
        });

        document.getElementById('view-list')?.addEventListener('click', () => {
            this.setViewMode('list');
        });

        // Filter
        document.getElementById('filter-status')?.addEventListener('change', (e) => {
            this.filterStatus = e.target.value;
            this.renderPages();
        });

        // Create sample page
        const createSampleBtn = document.getElementById('create-sample-btn');
        console.log('Create sample button element:', createSampleBtn);

        if (createSampleBtn) {
            createSampleBtn.addEventListener('click', () => {
                console.log('Create sample button clicked!');
                this.showTemplateSelectionPopup();
            });
            console.log('Create sample button listener attached');
        } else {
            console.warn('Create sample button not found in DOM!');
        }

        // Modal close
        document.getElementById('close-preview')?.addEventListener('click', () => {
            this.closePreview();
        });

        document.getElementById('preview-modal')?.addEventListener('click', (e) => {
            if (e.target.id === 'preview-modal') {
                this.closePreview();
            }
        });
    }

    setViewMode(mode) {
        this.viewMode = mode;

        const gridBtn = document.getElementById('view-grid');
        const listBtn = document.getElementById('view-list');

        if (mode === 'grid') {
            gridBtn.classList.add('bg-white', 'dark:bg-slate-600', 'text-blue-600', 'dark:text-blue-400', 'shadow');
            gridBtn.classList.remove('text-gray-600', 'dark:text-gray-400');
            listBtn.classList.remove('bg-white', 'dark:bg-slate-600', 'text-blue-600', 'dark:text-blue-400', 'shadow');
            listBtn.classList.add('text-gray-600', 'dark:text-gray-400');
        } else {
            listBtn.classList.add('bg-white', 'dark:bg-slate-600', 'text-blue-600', 'dark:text-blue-400', 'shadow');
            listBtn.classList.remove('text-gray-600', 'dark:text-gray-400');
            gridBtn.classList.remove('bg-white', 'dark:bg-slate-600', 'text-blue-600', 'dark:text-blue-400', 'shadow');
            gridBtn.classList.add('text-gray-600', 'dark:text-gray-400');
        }

        this.renderPages();
    }

    async loadPages() {
        try {
            const token = authService.getToken();

            if (!token) {
                throw new Error('Not authenticated. Please log in.');
            }

            const response = await apiFetch('/builder/', {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.status === 401) {
                throw new Error('Session expired. Please log in again.');
            }

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Failed to load pages');
            }

            const data = await response.json();
            console.log('Raw API response:', data);
            console.log('Response type:', typeof data);
            console.log('Is array?', Array.isArray(data));

            // Handle different response formats
            if (Array.isArray(data)) {
                this.pages = data;
            } else if (data && Array.isArray(data.pages)) {
                console.log('Response is wrapped in pages property');
                this.pages = data.pages;
            } else if (data && Array.isArray(data.data)) {
                console.log('Response is wrapped in data property');
                this.pages = data.data;
            } else {
                console.warn('Unexpected response format, using empty array');
                this.pages = [];
            }

            console.log('Pages loaded:', this.pages.length, 'pages');

            if (this.pages.length > 0) {
                console.log('First page sample:', this.pages[0]);
            }

            this.updateStats();
            this.renderPages();

        } catch (error) {
            console.error('Error loading pages:', error);
            showToast(error.message || 'Failed to load pages', 'error');

            const isAuthError = error.message.includes('authenticated') || error.message.includes('Session expired');

            document.getElementById('pages-container').innerHTML = `
                <div class="col-span-full text-center py-12">
                    <i class="ph-duotone ph-warning-circle text-5xl text-red-600 mb-4" style="color: #DC2626"></i>
                    <p class="text-lg font-medium text-gray-900 mb-2">${error.message}</p>
                    ${isAuthError ? `
                        <a href="/#login" class="inline-block mt-4 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
                            <i class="ph-duotone ph-sign-in mr-2"></i>
                            Go to Login
                        </a>
                    ` : `
                        <button onclick="location.reload()" class="inline-block mt-4 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
                            <i class="ph-duotone ph-arrow-clockwise mr-2"></i>
                            Try Again
                        </button>
                    `}
                </div>
            `;
        }
    }

    showTemplateSelectionPopup() {
        const templates = [
            {
                id: 'basic-components',
                icon: 'ph-duotone ph-squares-four',
                title: 'Basic Components Showcase',
                description: 'Demonstrates buttons, inputs, textarea, select, badge, and alert components',
                color: 'bg-blue-500'
            },
            {
                id: 'layout-demo',
                icon: 'ph-duotone ph-layout',
                title: 'Layout Components Demo',
                description: 'Shows container, section, stack, grid, cluster, sidebar, and toolbar layouts',
                color: 'bg-purple-500'
            },
            {
                id: 'card-gallery',
                icon: 'ph-duotone ph-cards',
                title: 'Card & Content Gallery',
                description: 'Features cards, badges, masonry layout, and split pane components',
                color: 'bg-pink-500'
            },
            {
                id: 'data-tables',
                icon: 'ph-duotone ph-table',
                title: 'Data & Tables Showcase',
                description: 'Displays data table, dynamic form, and API datatable components',
                color: 'bg-green-500'
            },
            {
                id: 'api-integration',
                icon: 'ph-duotone ph-plugs-connected',
                title: 'API Integration Demo',
                description: 'Shows API button, API form, and API datatable with backend integration',
                color: 'bg-orange-500'
            },
            {
                id: 'interactive-components',
                icon: 'ph-duotone ph-magic-wand',
                title: 'Interactive Components',
                description: 'Demonstrates modal, tabs, accordion, dropdown, and drawer components',
                color: 'bg-indigo-500'
            },
            {
                id: 'landing-page',
                icon: 'ph-duotone ph-rocket-launch',
                title: 'Complete Landing Page',
                description: 'A full landing page template with hero, features, content, and footer',
                color: 'bg-cyan-500'
            },
            {
                id: 'admin-dashboard',
                icon: 'ph-duotone ph-gauge',
                title: 'Admin Dashboard Template',
                description: 'Complete admin interface with toolbar, sidebar, data grid, cards, and alerts',
                color: 'bg-red-500'
            }
        ];

        const templateCards = templates.map(template => `
            <div class="template-card group cursor-pointer bg-white hover:bg-gray-50 border-2 border-gray-200 hover:border-blue-500 rounded-lg p-4 transition-all duration-200 hover:shadow-lg"
                 data-template-id="${template.id}">
                <div class="flex items-start gap-4">
                    <div class="${template.color} w-12 h-12 rounded-lg flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform duration-200">
                        <i class="${template.icon} text-2xl text-white"></i>
                    </div>
                    <div class="flex-1 min-w-0">
                        <h4 class="font-semibold text-gray-900 mb-1 group-hover:text-blue-600 transition-colors">${template.title}</h4>
                        <p class="text-sm text-gray-600 line-clamp-2">${template.description}</p>
                    </div>
                    <i class="ph ph-arrow-right text-gray-400 group-hover:text-blue-500 group-hover:translate-x-1 transition-all duration-200"></i>
                </div>
            </div>
        `).join('');

        const modalContent = `
            <div class="space-y-4">
                <p class="text-gray-600">Select a template to create a sample page with pre-configured components:</p>
                <div class="grid grid-cols-1 gap-3 max-h-[500px] overflow-y-auto pr-2">
                    ${templateCards}
                </div>
            </div>
        `;

        const modal = new FlexModal({
            title: 'Create Sample Page',
            subtitle: 'Choose a template to get started',
            icon: 'ph-duotone ph-sparkle',
            content: modalContent,
            size: 'lg',
            footerActions: [
                {
                    label: 'Cancel',
                    variant: 'ghost',
                    onClick: (e, modal) => modal.hide()
                }
            ]
        });

        modal.show();

        // Add click handlers to template cards
        setTimeout(() => {
            const templateCardElements = modal.getBodyElement().querySelectorAll('.template-card');
            templateCardElements.forEach(card => {
                card.addEventListener('click', () => {
                    const templateId = card.dataset.templateId;
                    modal.hide();
                    this.createSamplePage(templateId);
                });
            });
        }, 100);
    }

    async createSamplePage(templateType = 'basic-components') {
        console.log('createSamplePage() called with template:', templateType);

        try {
            const token = authService.getToken();
            console.log('Token exists:', !!token);

            if (!token) {
                showToast('Please log in to create pages', 'error');
                return;
            }

            // Generate unique identifier
            const timestamp = Date.now();
            const randomId = Math.random().toString(36).substring(2, 8);

            // Get template configuration
            const templateConfig = this.getTemplateConfig(templateType);

            const pageData = {
                name: templateConfig.name.replace('{id}', randomId),
                slug: `${templateType}-${timestamp}`,
                description: templateConfig.description,
                route_path: `/${templateType}-${randomId}`,
                grapejs_data: templateConfig.grapejsData,
                html_output: templateConfig.html.trim(),
                css_output: templateConfig.css.trim(),
                js_output: templateConfig.js || "",
                menu_label: templateConfig.menuLabel.replace('{id}', randomId),
                menu_icon: templateConfig.icon,
                menu_parent: null,
                menu_order: 100,
                show_in_menu: true,
                permission_code: null,
                permission_scope: "company"
            };

            console.log('Creating sample page:', pageData);

            const response = await apiFetch('/builder/', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(pageData)
            });

            if (response.status === 401) {
                showToast('Session expired. Please log in again.', 'error');
                return;
            }

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Failed to create sample page');
            }

            const createdPage = await response.json();
            console.log('Sample page created:', createdPage);

            showToast(`${templateConfig.name.replace('{id}', randomId)} created successfully!`, 'success');

            // Reload pages to show the new page
            await this.loadPages();

        } catch (error) {
            console.error('Error creating sample page:', error);
            showToast(error.message || 'Failed to create sample page', 'error');
        }
    }

    getTemplateConfig(templateType) {
        const templates = {
            'basic-components': this.getBasicComponentsTemplate(),
            'layout-demo': this.getLayoutDemoTemplate(),
            'card-gallery': this.getCardGalleryTemplate(),
            'data-tables': this.getDataTablesTemplate(),
            'api-integration': this.getApiIntegrationTemplate(),
            'interactive-components': this.getInteractiveComponentsTemplate(),
            'landing-page': this.getLandingPageTemplate(),
            'admin-dashboard': this.getAdminDashboardTemplate()
        };

        return templates[templateType] || templates['basic-components'];
    }

    getBasicComponentsTemplate() {
        const html = `<div class="container mx-auto p-8">
    <h1 class="text-3xl font-bold mb-8">Basic Components Showcase</h1>

    <!-- Buttons Section -->
    <section class="mb-12">
        <h2 class="text-2xl font-semibold mb-4">Buttons</h2>
        <div class="flex flex-wrap gap-4">
            <button type="ui-button" data-variant="primary">Primary Button</button>
            <button type="ui-button" data-variant="secondary">Secondary Button</button>
            <button type="ui-button" data-variant="success">Success Button</button>
            <button type="ui-button" data-variant="danger">Danger Button</button>
            <button type="ui-button" data-variant="warning">Warning Button</button>
            <button type="ui-button" data-variant="ghost">Ghost Button</button>
        </div>
    </section>

    <!-- Inputs Section -->
    <section class="mb-12">
        <h2 class="text-2xl font-semibold mb-4">Input Fields</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div data-component="ui-input-wrapper">
                <label>Text Input</label>
                <input type="text" placeholder="Enter text...">
            </div>
            <div data-component="ui-input-wrapper">
                <label>Email Input</label>
                <input type="email" placeholder="email@example.com">
            </div>
            <div data-component="ui-input-wrapper">
                <label>Password Input</label>
                <input type="password" placeholder="Password">
            </div>
            <div data-component="ui-input-wrapper">
                <label>Number Input</label>
                <input type="number" placeholder="123">
            </div>
        </div>
    </section>

    <!-- Textarea & Select -->
    <section class="mb-12">
        <h2 class="text-2xl font-semibold mb-4">Textarea & Select</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div data-component="ui-textarea">
                <label>Textarea</label>
                <textarea rows="4" placeholder="Enter multiple lines..."></textarea>
            </div>
            <div data-component="ui-select">
                <label>Select Dropdown</label>
                <select>
                    <option>Option 1</option>
                    <option>Option 2</option>
                    <option>Option 3</option>
                </select>
            </div>
        </div>
    </section>

    <!-- Badges -->
    <section class="mb-12">
        <h2 class="text-2xl font-semibold mb-4">Badges</h2>
        <div class="flex flex-wrap gap-3">
            <span data-component="ui-badge" data-variant="primary">Primary</span>
            <span data-component="ui-badge" data-variant="success">Success</span>
            <span data-component="ui-badge" data-variant="warning">Warning</span>
            <span data-component="ui-badge" data-variant="danger">Danger</span>
            <span data-component="ui-badge" data-variant="info">Info</span>
        </div>
    </section>

    <!-- Alerts -->
    <section class="mb-12">
        <h2 class="text-2xl font-semibold mb-4">Alerts</h2>
        <div class="space-y-4">
            <div data-component="ui-alert" data-variant="info">
                <strong>Info:</strong> This is an informational alert.
            </div>
            <div data-component="ui-alert" data-variant="success">
                <strong>Success:</strong> Operation completed successfully!
            </div>
            <div data-component="ui-alert" data-variant="warning">
                <strong>Warning:</strong> Please review this information.
            </div>
            <div data-component="ui-alert" data-variant="danger">
                <strong>Error:</strong> Something went wrong.
            </div>
        </div>
    </section>
</div>`;

        return {
            name: 'Basic Components {id}',
            menuLabel: 'Components {id}',
            description: 'Showcase of basic UI components including buttons, inputs, textarea, select, badge, and alerts',
            icon: 'ph-duotone ph-squares-four',
            html: html,
            css: ``,
            grapejsData: {
                assets: [],
                styles: [],
                pages: [{
                    component: {
                        type: "wrapper",
                        components: html
                    }
                }]
            }
        };
    }

    getLayoutDemoTemplate() {
        const html = `<div class="min-h-screen bg-gray-50">
    <!-- Toolbar -->
    <div data-component="flex-toolbar" class="bg-white shadow">
        <div class="flex justify-between items-center px-6 py-4">
            <h1 class="text-xl font-bold">Layout Components Demo</h1>
            <nav class="flex gap-4">
                <a href="#" class="text-blue-600 hover:text-blue-800">Home</a>
                <a href="#" class="text-blue-600 hover:text-blue-800">About</a>
                <a href="#" class="text-blue-600 hover:text-blue-800">Contact</a>
            </nav>
        </div>
    </div>

    <!-- Hero Section -->
    <section data-component="flex-section" data-variant="hero" class="bg-gradient-to-r from-blue-600 to-purple-600 text-white py-20">
        <div data-component="flex-container">
            <h2 class="text-4xl font-bold mb-4">Flexible Layout System</h2>
            <p class="text-xl mb-6">Build responsive layouts with ease using our component library</p>
        </div>
    </section>

    <!-- Grid Layout -->
    <section class="py-12">
        <div data-component="flex-container">
            <h3 class="text-2xl font-bold mb-6">Grid Layout</h3>
            <div data-component="flex-grid" data-columns="3" class="gap-6">
                <div data-component="ui-card">
                    <h4 class="font-semibold mb-2">Card 1</h4>
                    <p>Grid column content</p>
                </div>
                <div data-component="ui-card">
                    <h4 class="font-semibold mb-2">Card 2</h4>
                    <p>Grid column content</p>
                </div>
                <div data-component="ui-card">
                    <h4 class="font-semibold mb-2">Card 3</h4>
                    <p>Grid column content</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Stack Layout -->
    <section class="py-12 bg-white">
        <div data-component="flex-container">
            <h3 class="text-2xl font-bold mb-6">Stack Layout</h3>
            <div data-component="flex-stack" data-direction="vertical" class="gap-4">
                <div class="p-4 bg-blue-100 rounded">Stack Item 1</div>
                <div class="p-4 bg-blue-100 rounded">Stack Item 2</div>
                <div class="p-4 bg-blue-100 rounded">Stack Item 3</div>
            </div>
        </div>
    </section>

    <!-- Cluster Layout -->
    <section class="py-12">
        <div data-component="flex-container">
            <h3 class="text-2xl font-bold mb-6">Cluster Layout (Tags)</h3>
            <div data-component="flex-cluster" class="gap-2">
                <span data-component="ui-badge">Tag 1</span>
                <span data-component="ui-badge">Tag 2</span>
                <span data-component="ui-badge">Tag 3</span>
                <span data-component="ui-badge">Tag 4</span>
                <span data-component="ui-badge">Tag 5</span>
            </div>
        </div>
    </section>
</div>`;

        return {
            name: 'Layout Demo {id}',
            menuLabel: 'Layouts {id}',
            description: 'Demonstration of flexible layout components including container, grid, stack, and sidebar',
            icon: 'ph-duotone ph-layout',
            html: html,
            css: ``,
            grapejsData: {
                assets: [],
                styles: [],
                pages: [{
                    component: {
                        type: "wrapper",
                        components: html
                    }
                }]
            }
        };
    }

    getCardGalleryTemplate() {
        const html = `<div class="container mx-auto p-8">
    <header class="text-center mb-12">
        <h1 class="text-4xl font-bold mb-4">Card & Content Gallery</h1>
        <p class="text-gray-600">Explore different card styles and layouts</p>
    </header>

    <!-- Card Variants -->
    <section class="mb-12">
        <h2 class="text-2xl font-semibold mb-6">Card Variants</h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div data-component="ui-card" data-variant="default">
                <h3 class="text-lg font-semibold mb-2">Default Card</h3>
                <p class="text-gray-600 mb-4">This is a default card with standard styling.</p>
                <button type="ui-button" data-variant="primary">Learn More</button>
            </div>
            <div data-component="ui-card" data-variant="bordered">
                <h3 class="text-lg font-semibold mb-2">Bordered Card</h3>
                <p class="text-gray-600 mb-4">This card has a prominent border.</p>
                <button type="ui-button" data-variant="secondary">Learn More</button>
            </div>
            <div data-component="ui-card" data-variant="elevated">
                <h3 class="text-lg font-semibold mb-2">Elevated Card</h3>
                <p class="text-gray-600 mb-4">This card has an elevated shadow effect.</p>
                <button type="ui-button" data-variant="success">Learn More</button>
            </div>
        </div>
    </section>

    <!-- Masonry Layout -->
    <section class="mb-12">
        <h2 class="text-2xl font-semibold mb-6">Masonry Gallery</h2>
        <div data-component="flex-masonry" data-columns="3">
            <div data-component="ui-card">
                <div class="h-48 bg-gradient-to-br from-blue-400 to-blue-600 rounded mb-3"></div>
                <h4 class="font-semibold">Gallery Item 1</h4>
                <p class="text-sm text-gray-600">Beautiful content here</p>
            </div>
            <div data-component="ui-card">
                <div class="h-64 bg-gradient-to-br from-purple-400 to-purple-600 rounded mb-3"></div>
                <h4 class="font-semibold">Gallery Item 2</h4>
                <p class="text-sm text-gray-600">Taller content card</p>
            </div>
            <div data-component="ui-card">
                <div class="h-40 bg-gradient-to-br from-pink-400 to-pink-600 rounded mb-3"></div>
                <h4 class="font-semibold">Gallery Item 3</h4>
                <p class="text-sm text-gray-600">Compact content</p>
            </div>
            <div data-component="ui-card">
                <div class="h-56 bg-gradient-to-br from-green-400 to-green-600 rounded mb-3"></div>
                <h4 class="font-semibold">Gallery Item 4</h4>
                <p class="text-sm text-gray-600">Medium sized card</p>
            </div>
            <div data-component="ui-card">
                <div class="h-48 bg-gradient-to-br from-orange-400 to-orange-600 rounded mb-3"></div>
                <h4 class="font-semibold">Gallery Item 5</h4>
                <p class="text-sm text-gray-600">Another beautiful card</p>
            </div>
            <div data-component="ui-card">
                <div class="h-72 bg-gradient-to-br from-cyan-400 to-cyan-600 rounded mb-3"></div>
                <h4 class="font-semibold">Gallery Item 6</h4>
                <p class="text-sm text-gray-600">Tallest content here</p>
            </div>
        </div>
    </section>

    <!-- Split Pane Example -->
    <section class="mb-12">
        <h2 class="text-2xl font-semibold mb-6">Split Pane Layout</h2>
        <div data-component="flex-split-pane" class="h-64">
            <div class="p-6 bg-blue-50">
                <h3 class="font-semibold mb-2">Left Pane</h3>
                <p>Resizable split pane content</p>
            </div>
            <div class="p-6 bg-purple-50">
                <h3 class="font-semibold mb-2">Right Pane</h3>
                <p>Drag the divider to resize</p>
            </div>
        </div>
    </section>
</div>`;

        return {
            name: 'Card Gallery {id}',
            menuLabel: 'Gallery {id}',
            description: 'Beautiful card gallery with masonry layout and various card variants',
            icon: 'ph-duotone ph-cards',
            html: html,
            css: ``,
            grapejsData: {
                assets: [],
                styles: [],
                pages: [{
                    component: {
                        type: "wrapper",
                        components: html
                    }
                }]
            }
        };
    }

    getDataTablesTemplate() {
        const html = `<div class="container mx-auto p-8">
    <h1 class="text-3xl font-bold mb-8">Data & Tables Showcase</h1>

    <!-- Basic Data Table -->
    <section class="mb-12">
        <h2 class="text-2xl font-semibold mb-4">Basic Data Table</h2>
        <div data-component="data-table">
            <table class="w-full">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Role</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>1</td>
                        <td>John Doe</td>
                        <td>john@example.com</td>
                        <td>Admin</td>
                        <td><span data-component="ui-badge" data-variant="success">Active</span></td>
                    </tr>
                    <tr>
                        <td>2</td>
                        <td>Jane Smith</td>
                        <td>jane@example.com</td>
                        <td>User</td>
                        <td><span data-component="ui-badge" data-variant="success">Active</span></td>
                    </tr>
                    <tr>
                        <td>3</td>
                        <td>Bob Johnson</td>
                        <td>bob@example.com</td>
                        <td>Manager</td>
                        <td><span data-component="ui-badge" data-variant="warning">Pending</span></td>
                    </tr>
                    <tr>
                        <td>4</td>
                        <td>Alice Williams</td>
                        <td>alice@example.com</td>
                        <td>User</td>
                        <td><span data-component="ui-badge" data-variant="success">Active</span></td>
                    </tr>
                    <tr>
                        <td>5</td>
                        <td>Charlie Brown</td>
                        <td>charlie@example.com</td>
                        <td>User</td>
                        <td><span data-component="ui-badge" data-variant="danger">Inactive</span></td>
                    </tr>
                </tbody>
            </table>
        </div>
    </section>

    <!-- Dynamic Form -->
    <section class="mb-12">
        <h2 class="text-2xl font-semibold mb-4">Dynamic Form</h2>
        <div data-component="ui-card">
            <form data-component="dynamic-form">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                    <div data-component="ui-input-wrapper">
                        <label>First Name</label>
                        <input type="text" placeholder="Enter first name" required>
                    </div>
                    <div data-component="ui-input-wrapper">
                        <label>Last Name</label>
                        <input type="text" placeholder="Enter last name" required>
                    </div>
                    <div data-component="ui-input-wrapper">
                        <label>Email</label>
                        <input type="email" placeholder="email@example.com" required>
                    </div>
                    <div data-component="ui-select">
                        <label>Department</label>
                        <select required>
                            <option value="">Select department</option>
                            <option>Engineering</option>
                            <option>Marketing</option>
                            <option>Sales</option>
                            <option>HR</option>
                        </select>
                    </div>
                </div>
                <div class="flex gap-3">
                    <button type="ui-button" data-variant="primary">Submit</button>
                    <button type="ui-button" data-variant="ghost">Cancel</button>
                </div>
            </form>
        </div>
    </section>

    <!-- Table Statistics -->
    <section class="mb-12">
        <h2 class="text-2xl font-semibold mb-4">Table Statistics</h2>
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div data-component="ui-card" class="text-center">
                <div class="text-3xl font-bold text-blue-600 mb-2">150</div>
                <div class="text-gray-600">Total Records</div>
            </div>
            <div data-component="ui-card" class="text-center">
                <div class="text-3xl font-bold text-green-600 mb-2">120</div>
                <div class="text-gray-600">Active Users</div>
            </div>
            <div data-component="ui-card" class="text-center">
                <div class="text-3xl font-bold text-orange-600 mb-2">25</div>
                <div class="text-gray-600">Pending</div>
            </div>
            <div data-component="ui-card" class="text-center">
                <div class="text-3xl font-bold text-red-600 mb-2">5</div>
                <div class="text-gray-600">Inactive</div>
            </div>
        </div>
    </section>
</div>`;

        return {
            name: 'Data Tables {id}',
            menuLabel: 'Tables {id}',
            description: 'Interactive data tables with sorting, filtering, and pagination',
            icon: 'ph-duotone ph-table',
            html: html,
            css: ``,
            grapejsData: {
                assets: [],
                styles: [],
                pages: [{
                    component: {
                        type: "wrapper",
                        components: html
                    }
                }]
            }
        };
    }

    getApiIntegrationTemplate() {
        const html = `<div class="container mx-auto p-8">
    <h1 class="text-3xl font-bold mb-8">API Integration Demo</h1>

    <!-- API Buttons -->
    <section class="mb-12">
        <h2 class="text-2xl font-semibold mb-4">API Buttons</h2>
        <div data-component="ui-card">
            <p class="text-gray-600 mb-4">These buttons trigger API calls when clicked:</p>
            <div class="flex flex-wrap gap-3">
                <button data-component="api-button" data-endpoint="/api/v1/test" data-method="GET" data-variant="primary">
                    Fetch Data
                </button>
                <button data-component="api-button" data-endpoint="/api/v1/test" data-method="POST" data-variant="success">
                    Create Record
                </button>
                <button data-component="api-button" data-endpoint="/api/v1/test" data-method="PUT" data-variant="warning">
                    Update Record
                </button>
                <button data-component="api-button" data-endpoint="/api/v1/test" data-method="DELETE" data-variant="danger">
                    Delete Record
                </button>
            </div>
        </div>
    </section>

    <!-- API Form -->
    <section class="mb-12">
        <h2 class="text-2xl font-semibold mb-4">API Form</h2>
        <div data-component="ui-card">
            <form data-component="api-form" data-endpoint="/api/v1/users" data-method="POST">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                    <div data-component="ui-input-wrapper">
                        <label>Name</label>
                        <input type="text" name="name" placeholder="Enter name" required>
                    </div>
                    <div data-component="ui-input-wrapper">
                        <label>Email</label>
                        <input type="email" name="email" placeholder="email@example.com" required>
                    </div>
                    <div data-component="ui-select">
                        <label>Role</label>
                        <select name="role" required>
                            <option value="">Select role</option>
                            <option value="admin">Admin</option>
                            <option value="user">User</option>
                            <option value="manager">Manager</option>
                        </select>
                    </div>
                    <div data-component="ui-select">
                        <label>Status</label>
                        <select name="status" required>
                            <option value="active">Active</option>
                            <option value="inactive">Inactive</option>
                        </select>
                    </div>
                </div>
                <div data-component="ui-textarea" class="mb-6">
                    <label>Notes</label>
                    <textarea name="notes" rows="3" placeholder="Additional notes..."></textarea>
                </div>
                <div class="flex gap-3">
                    <button type="submit" data-variant="primary">Submit to API</button>
                    <button type="reset" data-variant="ghost">Reset</button>
                </div>
            </form>
        </div>
    </section>

    <!-- API DataTable -->
    <section class="mb-12">
        <h2 class="text-2xl font-semibold mb-4">API DataTable</h2>
        <div data-component="api-datatable"
             data-endpoint="/api/v1/users"
             data-columns='["id", "name", "email", "role", "status"]'>
            <div class="text-center py-8 text-gray-500">
                Loading data from API...
            </div>
        </div>
    </section>

    <!-- API Response Display -->
    <section class="mb-12">
        <h2 class="text-2xl font-semibold mb-4">API Response</h2>
        <div data-component="ui-card">
            <pre class="bg-gray-100 p-4 rounded overflow-x-auto"><code>{
  "status": "success",
  "data": {
    "message": "API integration working correctly",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}</code></pre>
        </div>
    </section>
</div>`;

        return {
            name: 'API Integration {id}',
            menuLabel: 'API Demo {id}',
            description: 'Examples of API button, API form, and API datatable components with backend integration',
            icon: 'ph-duotone ph-plugs-connected',
            html: html,
            css: ``,
            grapejsData: {
                assets: [],
                styles: [],
                pages: [{
                    component: {
                        type: "wrapper",
                        components: html
                    }
                }]
            }
        };
    }

    getInteractiveComponentsTemplate() {
        const html = `<div class="container mx-auto p-8">
    <h1 class="text-3xl font-bold mb-8">Interactive Components</h1>

    <!-- Modal Trigger -->
    <section class="mb-12">
        <h2 class="text-2xl font-semibold mb-4">Modal Component</h2>
        <div data-component="ui-card">
            <p class="text-gray-600 mb-4">Click the button to open a modal dialog:</p>
            <button type="ui-button" data-variant="primary" data-modal-trigger="sample-modal">
                Open Modal
            </button>
            <div data-component="flex-modal" data-modal-id="sample-modal" data-size="md" class="hidden">
                <div class="modal-content">
                    <h3 class="text-xl font-semibold mb-4">Modal Title</h3>
                    <p class="mb-4">This is a modal dialog with sample content.</p>
                    <div class="flex gap-3">
                        <button type="ui-button" data-variant="primary">Confirm</button>
                        <button type="ui-button" data-variant="ghost" data-modal-close>Cancel</button>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Tabs -->
    <section class="mb-12">
        <h2 class="text-2xl font-semibold mb-4">Tabs Component</h2>
        <div data-component="ui-card">
            <div data-component="flex-tabs">
                <div class="tab-headers flex gap-2 border-b mb-4">
                    <button class="tab-header px-4 py-2 font-medium text-blue-600 border-b-2 border-blue-600" data-tab="tab1">Tab 1</button>
                    <button class="tab-header px-4 py-2 font-medium text-gray-600 hover:text-blue-600" data-tab="tab2">Tab 2</button>
                    <button class="tab-header px-4 py-2 font-medium text-gray-600 hover:text-blue-600" data-tab="tab3">Tab 3</button>
                </div>
                <div class="tab-contents">
                    <div class="tab-content" data-tab-content="tab1">
                        <h3 class="font-semibold mb-2">Tab 1 Content</h3>
                        <p>This is the content for the first tab.</p>
                    </div>
                    <div class="tab-content hidden" data-tab-content="tab2">
                        <h3 class="font-semibold mb-2">Tab 2 Content</h3>
                        <p>This is the content for the second tab.</p>
                    </div>
                    <div class="tab-content hidden" data-tab-content="tab3">
                        <h3 class="font-semibold mb-2">Tab 3 Content</h3>
                        <p>This is the content for the third tab.</p>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Accordion -->
    <section class="mb-12">
        <h2 class="text-2xl font-semibold mb-4">Accordion Component</h2>
        <div data-component="flex-accordion" class="space-y-2">
            <div class="accordion-item border rounded">
                <button class="accordion-header w-full text-left px-4 py-3 font-medium flex justify-between items-center hover:bg-gray-50">
                    <span>Accordion Item 1</span>
                    <i class="ph ph-caret-down"></i>
                </button>
                <div class="accordion-content hidden px-4 py-3 border-t">
                    <p>Content for accordion item 1. Click the header to expand/collapse.</p>
                </div>
            </div>
            <div class="accordion-item border rounded">
                <button class="accordion-header w-full text-left px-4 py-3 font-medium flex justify-between items-center hover:bg-gray-50">
                    <span>Accordion Item 2</span>
                    <i class="ph ph-caret-down"></i>
                </button>
                <div class="accordion-content hidden px-4 py-3 border-t">
                    <p>Content for accordion item 2. Multiple items can be expanded at once.</p>
                </div>
            </div>
            <div class="accordion-item border rounded">
                <button class="accordion-header w-full text-left px-4 py-3 font-medium flex justify-between items-center hover:bg-gray-50">
                    <span>Accordion Item 3</span>
                    <i class="ph ph-caret-down"></i>
                </button>
                <div class="accordion-content hidden px-4 py-3 border-t">
                    <p>Content for accordion item 3. Great for FAQs and collapsible content.</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Dropdown -->
    <section class="mb-12">
        <h2 class="text-2xl font-semibold mb-4">Dropdown Component</h2>
        <div data-component="ui-card">
            <p class="text-gray-600 mb-4">Click to show dropdown menu:</p>
            <div data-component="flex-dropdown" class="relative inline-block">
                <button type="ui-button" data-variant="secondary" class="dropdown-trigger">
                    Actions <i class="ph ph-caret-down ml-1"></i>
                </button>
                <div class="dropdown-menu hidden absolute mt-2 w-48 bg-white border rounded-lg shadow-lg">
                    <a href="#" class="block px-4 py-2 hover:bg-gray-100">Edit</a>
                    <a href="#" class="block px-4 py-2 hover:bg-gray-100">Duplicate</a>
                    <a href="#" class="block px-4 py-2 hover:bg-gray-100">Archive</a>
                    <div class="border-t"></div>
                    <a href="#" class="block px-4 py-2 text-red-600 hover:bg-gray-100">Delete</a>
                </div>
            </div>
        </div>
    </section>
</div>`;

        return {
            name: 'Interactive Components {id}',
            menuLabel: 'Interactive {id}',
            description: 'Showcase of modal, tabs, accordion, dropdown, and drawer interactive components',
            icon: 'ph-duotone ph-magic-wand',
            html: html,
            css: ``,
            grapejsData: {
                assets: [],
                styles: [],
                pages: [{
                    component: {
                        type: "wrapper",
                        components: html
                    }
                }]
            }
        };
    }

    getLandingPageTemplate() {
        const html = `<!-- Hero Section -->
<section class="bg-gradient-to-br from-blue-600 via-purple-600 to-pink-500 text-white py-20">
    <div class="container mx-auto px-8 text-center">
        <h1 class="text-5xl font-bold mb-6">Build Amazing Web Applications</h1>
        <p class="text-xl mb-8 max-w-2xl mx-auto">Create beautiful, responsive interfaces with our powerful component library and visual builder</p>
        <div class="flex justify-center gap-4">
            <button type="ui-button" data-variant="primary" class="bg-white text-blue-600 hover:bg-gray-100">
                Get Started
            </button>
            <button type="ui-button" data-variant="ghost" class="border-white text-white hover:bg-white/10">
                Learn More
            </button>
        </div>
    </div>
</section>

<!-- Features Section -->
<section class="py-20 bg-white">
    <div class="container mx-auto px-8">
        <div class="text-center mb-12">
            <h2 class="text-4xl font-bold mb-4">Powerful Features</h2>
            <p class="text-gray-600 text-lg">Everything you need to build modern web applications</p>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div data-component="ui-card" class="text-center">
                <div class="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <i class="ph-duotone ph-lightning text-3xl text-blue-600"></i>
                </div>
                <h3 class="text-xl font-semibold mb-3">Lightning Fast</h3>
                <p class="text-gray-600">Optimized performance for the best user experience</p>
            </div>
            <div data-component="ui-card" class="text-center">
                <div class="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <i class="ph-duotone ph-paint-brush text-3xl text-purple-600"></i>
                </div>
                <h3 class="text-xl font-semibold mb-3">Fully Customizable</h3>
                <p class="text-gray-600">Tailor every component to match your brand</p>
            </div>
            <div data-component="ui-card" class="text-center">
                <div class="w-16 h-16 bg-pink-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <i class="ph-duotone ph-devices text-3xl text-pink-600"></i>
                </div>
                <h3 class="text-xl font-semibold mb-3">Responsive Design</h3>
                <p class="text-gray-600">Works perfectly on all devices and screen sizes</p>
            </div>
        </div>
    </div>
</section>

<!-- Content Section -->
<section class="py-20 bg-gray-50">
    <div class="container mx-auto px-8">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
            <div>
                <h2 class="text-3xl font-bold mb-6">Build with Confidence</h2>
                <p class="text-gray-600 mb-6">Our comprehensive component library provides everything you need to create professional web applications. From basic UI elements to complex data tables and API integrations.</p>
                <ul class="space-y-3">
                    <li class="flex items-start gap-3">
                        <i class="ph-duotone ph-check-circle text-green-600 text-xl mt-1"></i>
                        <span>22+ pre-built components ready to use</span>
                    </li>
                    <li class="flex items-start gap-3">
                        <i class="ph-duotone ph-check-circle text-green-600 text-xl mt-1"></i>
                        <span>Visual drag-and-drop builder</span>
                    </li>
                    <li class="flex items-start gap-3">
                        <i class="ph-duotone ph-check-circle text-green-600 text-xl mt-1"></i>
                        <span>API integration support</span>
                    </li>
                    <li class="flex items-start gap-3">
                        <i class="ph-duotone ph-check-circle text-green-600 text-xl mt-1"></i>
                        <span>Full TypeScript support</span>
                    </li>
                </ul>
            </div>
            <div class="bg-gradient-to-br from-blue-400 to-purple-500 rounded-lg h-96 flex items-center justify-center text-white">
                <i class="ph-duotone ph-code text-9xl"></i>
            </div>
        </div>
    </div>
</section>

<!-- Stats Section -->
<section class="py-20 bg-blue-600 text-white">
    <div class="container mx-auto px-8">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-8 text-center">
            <div>
                <div class="text-5xl font-bold mb-2">22+</div>
                <div class="text-blue-100">Components</div>
            </div>
            <div>
                <div class="text-5xl font-bold mb-2">1000+</div>
                <div class="text-blue-100">Users</div>
            </div>
            <div>
                <div class="text-5xl font-bold mb-2">50+</div>
                <div class="text-blue-100">Templates</div>
            </div>
            <div>
                <div class="text-5xl font-bold mb-2">99.9%</div>
                <div class="text-blue-100">Uptime</div>
            </div>
        </div>
    </div>
</section>

<!-- CTA Section -->
<section class="py-20 bg-white">
    <div class="container mx-auto px-8 text-center">
        <h2 class="text-4xl font-bold mb-6">Ready to Get Started?</h2>
        <p class="text-gray-600 text-lg mb-8 max-w-2xl mx-auto">Join thousands of developers building amazing applications with our platform</p>
        <button type="ui-button" data-variant="primary" class="text-lg px-8 py-4">
            Start Building Now
        </button>
    </div>
</section>

<!-- Footer -->
<footer class="bg-gray-900 text-gray-300 py-12">
    <div class="container mx-auto px-8">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
            <div>
                <h3 class="text-white font-semibold mb-4">Product</h3>
                <ul class="space-y-2">
                    <li><a href="#" class="hover:text-white">Features</a></li>
                    <li><a href="#" class="hover:text-white">Pricing</a></li>
                    <li><a href="#" class="hover:text-white">Documentation</a></li>
                </ul>
            </div>
            <div>
                <h3 class="text-white font-semibold mb-4">Company</h3>
                <ul class="space-y-2">
                    <li><a href="#" class="hover:text-white">About</a></li>
                    <li><a href="#" class="hover:text-white">Blog</a></li>
                    <li><a href="#" class="hover:text-white">Careers</a></li>
                </ul>
            </div>
            <div>
                <h3 class="text-white font-semibold mb-4">Resources</h3>
                <ul class="space-y-2">
                    <li><a href="#" class="hover:text-white">Community</a></li>
                    <li><a href="#" class="hover:text-white">Support</a></li>
                    <li><a href="#" class="hover:text-white">Contact</a></li>
                </ul>
            </div>
            <div>
                <h3 class="text-white font-semibold mb-4">Legal</h3>
                <ul class="space-y-2">
                    <li><a href="#" class="hover:text-white">Privacy</a></li>
                    <li><a href="#" class="hover:text-white">Terms</a></li>
                    <li><a href="#" class="hover:text-white">License</a></li>
                </ul>
            </div>
        </div>
        <div class="border-t border-gray-800 pt-8 text-center">
            <p>&copy; 2024 BuilderApp. All rights reserved.</p>
        </div>
    </div>
</footer>`;

        return {
            name: 'Landing Page {id}',
            menuLabel: 'Landing {id}',
            description: 'Complete landing page with hero, features, content sections, and footer',
            icon: 'ph-duotone ph-rocket-launch',
            html: html,
            css: ``,
            grapejsData: {
                assets: [],
                styles: [],
                pages: [{
                    component: {
                        type: "wrapper",
                        components: html
                    }
                }]
            }
        };
    }

    getAdminDashboardTemplate() {
        const html = `<div class="flex h-screen bg-gray-100">
    <!-- Sidebar -->
    <aside data-component="flex-sidebar" class="w-64 bg-gray-900 text-white flex-shrink-0">
        <div class="p-6">
            <h1 class="text-xl font-bold mb-8">Admin Panel</h1>
            <nav class="space-y-2">
                <a href="#" class="flex items-center gap-3 px-4 py-3 bg-blue-600 rounded-lg">
                    <i class="ph-duotone ph-gauge"></i>
                    <span>Dashboard</span>
                </a>
                <a href="#" class="flex items-center gap-3 px-4 py-3 hover:bg-gray-800 rounded-lg">
                    <i class="ph-duotone ph-users"></i>
                    <span>Users</span>
                </a>
                <a href="#" class="flex items-center gap-3 px-4 py-3 hover:bg-gray-800 rounded-lg">
                    <i class="ph-duotone ph-chart-bar"></i>
                    <span>Analytics</span>
                </a>
                <a href="#" class="flex items-center gap-3 px-4 py-3 hover:bg-gray-800 rounded-lg">
                    <i class="ph-duotone ph-gear"></i>
                    <span>Settings</span>
                </a>
            </nav>
        </div>
    </aside>

    <!-- Main Content -->
    <div class="flex-1 overflow-y-auto">
        <!-- Top Bar -->
        <header data-component="flex-toolbar" class="bg-white shadow-sm px-8 py-4">
            <div class="flex justify-between items-center">
                <h2 class="text-2xl font-bold text-gray-800">Dashboard Overview</h2>
                <div class="flex items-center gap-4">
                    <button type="ui-button" data-variant="ghost">
                        <i class="ph-duotone ph-bell"></i>
                    </button>
                    <button type="ui-button" data-variant="ghost">
                        <i class="ph-duotone ph-user-circle"></i>
                    </button>
                </div>
            </div>
        </header>

        <!-- Dashboard Content -->
        <main class="p-8">
            <!-- Stats Grid -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <div data-component="ui-card" class="bg-gradient-to-br from-blue-500 to-blue-600 text-white">
                    <div class="flex justify-between items-start mb-4">
                        <div>
                            <p class="text-blue-100 text-sm mb-1">Total Users</p>
                            <h3 class="text-3xl font-bold">2,543</h3>
                        </div>
                        <div class="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center">
                            <i class="ph-duotone ph-users text-2xl"></i>
                        </div>
                    </div>
                    <div class="flex items-center gap-2 text-sm">
                        <span data-component="ui-badge" data-variant="success" class="bg-green-500">+12%</span>
                        <span class="text-blue-100">vs last month</span>
                    </div>
                </div>

                <div data-component="ui-card" class="bg-gradient-to-br from-green-500 to-green-600 text-white">
                    <div class="flex justify-between items-start mb-4">
                        <div>
                            <p class="text-green-100 text-sm mb-1">Revenue</p>
                            <h3 class="text-3xl font-bold">$45,231</h3>
                        </div>
                        <div class="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center">
                            <i class="ph-duotone ph-currency-dollar text-2xl"></i>
                        </div>
                    </div>
                    <div class="flex items-center gap-2 text-sm">
                        <span data-component="ui-badge" data-variant="success" class="bg-green-700">+8%</span>
                        <span class="text-green-100">vs last month</span>
                    </div>
                </div>

                <div data-component="ui-card" class="bg-gradient-to-br from-orange-500 to-orange-600 text-white">
                    <div class="flex justify-between items-start mb-4">
                        <div>
                            <p class="text-orange-100 text-sm mb-1">Active Projects</p>
                            <h3 class="text-3xl font-bold">127</h3>
                        </div>
                        <div class="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center">
                            <i class="ph-duotone ph-briefcase text-2xl"></i>
                        </div>
                    </div>
                    <div class="flex items-center gap-2 text-sm">
                        <span data-component="ui-badge" data-variant="warning" class="bg-orange-700">+5</span>
                        <span class="text-orange-100">new this week</span>
                    </div>
                </div>

                <div data-component="ui-card" class="bg-gradient-to-br from-purple-500 to-purple-600 text-white">
                    <div class="flex justify-between items-start mb-4">
                        <div>
                            <p class="text-purple-100 text-sm mb-1">Completion Rate</p>
                            <h3 class="text-3xl font-bold">94.5%</h3>
                        </div>
                        <div class="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center">
                            <i class="ph-duotone ph-chart-line text-2xl"></i>
                        </div>
                    </div>
                    <div class="flex items-center gap-2 text-sm">
                        <span data-component="ui-badge" data-variant="success" class="bg-purple-700">+2.1%</span>
                        <span class="text-purple-100">vs last month</span>
                    </div>
                </div>
            </div>

            <!-- Recent Activity & Quick Actions -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                <!-- Recent Activity -->
                <div data-component="ui-card">
                    <h3 class="text-lg font-semibold mb-4">Recent Activity</h3>
                    <div class="space-y-4">
                        <div class="flex items-start gap-3 pb-4 border-b">
                            <div class="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                                <i class="ph-duotone ph-user-plus text-blue-600"></i>
                            </div>
                            <div class="flex-1">
                                <p class="font-medium">New user registered</p>
                                <p class="text-sm text-gray-600">John Doe joined the platform</p>
                                <p class="text-xs text-gray-500 mt-1">2 hours ago</p>
                            </div>
                        </div>
                        <div class="flex items-start gap-3 pb-4 border-b">
                            <div class="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0">
                                <i class="ph-duotone ph-check-circle text-green-600"></i>
                            </div>
                            <div class="flex-1">
                                <p class="font-medium">Project completed</p>
                                <p class="text-sm text-gray-600">Website redesign finished</p>
                                <p class="text-xs text-gray-500 mt-1">5 hours ago</p>
                            </div>
                        </div>
                        <div class="flex items-start gap-3">
                            <div class="w-10 h-10 bg-orange-100 rounded-full flex items-center justify-center flex-shrink-0">
                                <i class="ph-duotone ph-warning text-orange-600"></i>
                            </div>
                            <div class="flex-1">
                                <p class="font-medium">System alert</p>
                                <p class="text-sm text-gray-600">Database backup completed</p>
                                <p class="text-xs text-gray-500 mt-1">1 day ago</p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Quick Actions -->
                <div data-component="ui-card">
                    <h3 class="text-lg font-semibold mb-4">Quick Actions</h3>
                    <div class="grid grid-cols-2 gap-3">
                        <button type="ui-button" data-variant="primary" class="justify-center">
                            <i class="ph-duotone ph-plus-circle mr-2"></i>
                            New User
                        </button>
                        <button type="ui-button" data-variant="secondary" class="justify-center">
                            <i class="ph-duotone ph-file-plus mr-2"></i>
                            New Project
                        </button>
                        <button type="ui-button" data-variant="success" class="justify-center">
                            <i class="ph-duotone ph-download mr-2"></i>
                            Export Data
                        </button>
                        <button type="ui-button" data-variant="warning" class="justify-center">
                            <i class="ph-duotone ph-gear mr-2"></i>
                            Settings
                        </button>
                    </div>
                    <div class="mt-6">
                        <div data-component="ui-alert" data-variant="info">
                            <strong>Tip:</strong> You can customize your dashboard layout in settings.
                        </div>
                    </div>
                </div>
            </div>

            <!-- Data Table -->
            <div data-component="ui-card">
                <h3 class="text-lg font-semibold mb-4">Recent Users</h3>
                <div data-component="data-table">
                    <table class="w-full">
                        <thead>
                            <tr>
                                <th class="text-left">Name</th>
                                <th class="text-left">Email</th>
                                <th class="text-left">Role</th>
                                <th class="text-left">Status</th>
                                <th class="text-left">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td class="py-3">John Doe</td>
                                <td>john@example.com</td>
                                <td>Admin</td>
                                <td><span data-component="ui-badge" data-variant="success">Active</span></td>
                                <td>
                                    <button type="ui-button" data-variant="ghost" class="text-sm">
                                        <i class="ph ph-pencil"></i>
                                    </button>
                                </td>
                            </tr>
                            <tr>
                                <td class="py-3">Jane Smith</td>
                                <td>jane@example.com</td>
                                <td>Manager</td>
                                <td><span data-component="ui-badge" data-variant="success">Active</span></td>
                                <td>
                                    <button type="ui-button" data-variant="ghost" class="text-sm">
                                        <i class="ph ph-pencil"></i>
                                    </button>
                                </td>
                            </tr>
                            <tr>
                                <td class="py-3">Bob Johnson</td>
                                <td>bob@example.com</td>
                                <td>User</td>
                                <td><span data-component="ui-badge" data-variant="warning">Pending</span></td>
                                <td>
                                    <button type="ui-button" data-variant="ghost" class="text-sm">
                                        <i class="ph ph-pencil"></i>
                                    </button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </main>
    </div>
</div>`;

        return {
            name: 'Admin Dashboard {id}',
            menuLabel: 'Dashboard {id}',
            description: 'Complete admin dashboard with sidebar, data widgets, charts, and management tools',
            icon: 'ph-duotone ph-gauge',
            html: html,
            css: ``,
            grapejsData: {
                assets: [],
                styles: [],
                pages: [{
                    component: {
                        type: "wrapper",
                        components: html
                    }
                }]
            }
        };
    }

    updateStats() {
        const total = this.pages.length;
        const published = this.pages.filter(p => p.published).length;
        const drafts = total - published;
        const inMenu = this.pages.filter(p => p.show_in_menu).length;

        const statTotal = document.getElementById('stat-total');
        const statPublished = document.getElementById('stat-published');
        const statDrafts = document.getElementById('stat-drafts');
        const statMenu = document.getElementById('stat-menu');

        if (statTotal) statTotal.textContent = total;
        if (statPublished) statPublished.textContent = published;
        if (statDrafts) statDrafts.textContent = drafts;
        if (statMenu) statMenu.textContent = inMenu;
    }

    renderPages() {
        const container = document.getElementById('pages-container');
        console.log('renderPages called. Container:', container);
        console.log('Filtered pages to render:', this.filterStatus, 'Total pages:', this.pages.length);

        if (!container) {
            console.error('ERROR: pages-container element not found in DOM!');
            return;
        }

        // Filter pages
        let filteredPages = this.pages;
        if (this.filterStatus === 'published') {
            filteredPages = this.pages.filter(p => p.published);
        } else if (this.filterStatus === 'draft') {
            filteredPages = this.pages.filter(p => !p.published);
        }

        if (filteredPages.length === 0) {
            container.innerHTML = `
                <div class="col-span-full text-center py-12">
                    <i class="ph-duotone ph-files text-5xl text-gray-400 mb-4" style="color: #9CA3AF"></i>
                    <p class="text-gray-600 text-lg font-medium">No pages found</p>
                    <p class="text-gray-500 text-sm mt-2">Create your first page with the UI Builder</p>
                    <a href="/#builder" class="inline-block mt-4 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
                        <i class="ph-duotone ph-plus-circle mr-2"></i>
                        Create Page
                    </a>
                </div>
            `;
            return;
        }

        if (this.viewMode === 'grid') {
            container.className = 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6';
            container.innerHTML = filteredPages.map(page => this.renderPageCard(page)).join('');
        } else {
            container.className = 'space-y-4';
            container.innerHTML = filteredPages.map(page => this.renderPageListItem(page)).join('');
        }

        // Attach event listeners to cards
        this.attachCardListeners();
    }

    renderPageCard(page) {
        const statusBadge = page.published
            ? '<span class="px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">Published</span>'
            : '<span class="px-2 py-1 bg-orange-100 text-orange-800 text-xs font-medium rounded-full">Draft</span>';

        const menuBadge = page.show_in_menu
            ? '<i class="ph-duotone ph-list-bullets text-purple-600" style="color: #8B5CF6" title="Shown in menu"></i>'
            : '';

        return `
            <div class="bg-white rounded-lg border border-gray-200 overflow-hidden hover:shadow-lg transition group">
                <!-- Preview Thumbnail -->
                <div class="h-48 bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center overflow-hidden relative">
                    <i class="${page.menu_icon || 'ph-duotone ph-file-html'} text-6xl" style="color: #3B82F6"></i>
                    <div class="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-10 transition"></div>
                </div>

                <!-- Card Content -->
                <div class="p-4">
                    <div class="flex items-start justify-between mb-2">
                        <h3 class="font-semibold text-gray-900 text-lg flex-1 line-clamp-1">${page.name}</h3>
                        ${menuBadge}
                    </div>

                    <p class="text-sm text-gray-600 mb-3 line-clamp-2">${page.description || 'No description'}</p>

                    <div class="flex items-center gap-2 mb-4">
                        ${statusBadge}
                        <span class="text-xs text-gray-500">
                            <i class="ph-duotone ph-path"></i>
                            ${page.route_path}
                        </span>
                    </div>

                    <!-- Actions -->
                    <div class="flex gap-2">
                        <button onclick="window.builderShowcase.previewPage('${page.id}')"
                                class="flex-1 px-3 py-2 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 transition">
                            <i class="ph-duotone ph-eye mr-1"></i>
                            Preview
                        </button>
                        <a href="/#builder?page=${page.id}"
                           class="flex-1 px-3 py-2 bg-gray-100 text-gray-700 text-sm font-medium rounded hover:bg-gray-200 dark:hover:bg-slate-600 transition text-center">
                            <i class="ph-duotone ph-pencil mr-1"></i>
                            Edit
                        </a>
                        <button onclick="window.builderShowcase.deletePage('${page.id}')"
                                class="px-3 py-2 bg-red-50/20 text-red-600 text-sm font-medium rounded hover:bg-red-100 dark:hover:bg-red-900/40 transition">
                            <i class="ph-duotone ph-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    renderPageListItem(page) {
        const statusBadge = page.published
            ? '<span class="px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">Published</span>'
            : '<span class="px-2 py-1 bg-orange-100 text-orange-800 text-xs font-medium rounded-full">Draft</span>';

        return `
            <div class="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition">
                <div class="flex items-center gap-4">
                    <div class="w-16 h-16 bg-gradient-to-br from-blue-50 to-indigo-100 rounded-lg flex items-center justify-center flex-shrink-0">
                        <i class="${page.menu_icon || 'ph-duotone ph-file-html'} text-3xl" style="color: #3B82F6"></i>
                    </div>

                    <div class="flex-1 min-w-0">
                        <div class="flex items-center gap-2 mb-1">
                            <h3 class="font-semibold text-gray-900 text-lg">${page.name}</h3>
                            ${statusBadge}
                            ${page.show_in_menu ? '<i class="ph-duotone ph-list-bullets text-purple-600" style="color: #8B5CF6"></i>' : ''}
                        </div>
                        <p class="text-sm text-gray-600 mb-1">${page.description || 'No description'}</p>
                        <div class="flex items-center gap-4 text-xs text-gray-500">
                            <span><i class="ph-duotone ph-path"></i> ${page.route_path}</span>
                            ${page.module_name ? `<span><i class="ph-duotone ph-package"></i> ${page.module_name}</span>` : ''}
                            ${page.created_at ? `<span><i class="ph-duotone ph-calendar"></i> ${new Date(page.created_at).toLocaleDateString()}</span>` : ''}
                        </div>
                    </div>

                    <div class="flex gap-2 flex-shrink-0">
                        <button onclick="window.builderShowcase.previewPage('${page.id}')"
                                class="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 transition">
                            <i class="ph-duotone ph-eye mr-1"></i>
                            Preview
                        </button>
                        <a href="/#builder?page=${page.id}"
                           class="px-4 py-2 bg-gray-100 text-gray-700 text-sm font-medium rounded hover:bg-gray-200 dark:hover:bg-slate-600 transition">
                            <i class="ph-duotone ph-pencil mr-1"></i>
                            Edit
                        </a>
                        <button onclick="window.builderShowcase.deletePage('${page.id}')"
                                class="px-4 py-2 bg-red-50/20 text-red-600 text-sm font-medium rounded hover:bg-red-100 dark:hover:bg-red-900/40 transition">
                            <i class="ph-duotone ph-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    attachCardListeners() {
        // Make builderShowcase globally accessible for inline onclick handlers
        window.builderShowcase = this;
    }

    async previewPage(pageId) {
        const page = this.pages.find(p => p.id === pageId);
        if (!page) return;

        const modal = document.getElementById('preview-modal');
        const title = document.getElementById('preview-title');
        const content = document.getElementById('preview-content');

        title.textContent = page.name;

        // Create preview iframe
        const previewHTML = `
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
                <style>${page.css_output || ''}</style>
            </head>
            <body>
                ${page.html_output || '<p class="p-4 text-gray-500">No preview available</p>'}
            </body>
            </html>
        `;

        content.innerHTML = `
            <div class="space-y-4">
                <div class="grid grid-cols-2 gap-4 text-sm">
                    <div>
                        <span class="text-gray-600">Route:</span>
                        <span class="font-mono text-blue-600 ml-2">${page.route_path}</span>
                    </div>
                    <div>
                        <span class="text-gray-600">Status:</span>
                        <span class="ml-2">${page.published ? '✅ Published' : '📝 Draft'}</span>
                    </div>
                </div>
                <iframe srcdoc="${previewHTML.replace(/"/g, '&quot;')}"
                        class="w-full h-[600px] border border-gray-200 rounded-lg bg-white">
                </iframe>
            </div>
        `;

        modal.classList.remove('hidden');
    }

    closePreview() {
        document.getElementById('preview-modal').classList.add('hidden');
    }

    async deletePage(pageId) {
        const page = this.pages.find(p => p.id === pageId);
        if (!page) return;

        if (!confirm(`Are you sure you want to delete "${page.name}"? This action cannot be undone.`)) {
            return;
        }

        try {
            const token = authService.getToken();

            if (!token) {
                showToast('Not authenticated. Please log in.', 'error');
                return;
            }            

            const response = await apiFetch(`/builder/${pageId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.status === 401) {
                showToast('Session expired. Please log in again.', 'error');
                return;
            }

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Failed to delete page');
            }

            showToast('Page deleted successfully', 'success');
            await this.loadPages();

        } catch (error) {
            console.error('Error deleting page:', error);
            showToast(error.message || 'Failed to delete page', 'error');
        }
    }

    cleanup() {
        window.builderShowcase = null;
    }
}
