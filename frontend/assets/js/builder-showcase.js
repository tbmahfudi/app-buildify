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
        document.getElementById('create-sample-btn')?.addEventListener('click', () => {
            this.createSamplePage();
        });

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
                    <p class="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">${error.message}</p>
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

    async createSamplePage() {
        try {
            const token = authService.getToken();

            if (!token) {
                showToast('Please log in to create pages', 'error');
                return;
            }

            // Generate unique identifier
            const timestamp = Date.now();
            const randomId = Math.random().toString(36).substring(2, 8);

            // Sample GrapeJS data with basic components
            const sampleGrapejsData = {
                "assets": [],
                "styles": [
                    {
                        "selectors": ["#sample-header"],
                        "style": {
                            "padding": "40px 20px",
                            "text-align": "center",
                            "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                            "color": "#ffffff"
                        }
                    },
                    {
                        "selectors": ["#sample-content"],
                        "style": {
                            "padding": "40px 20px",
                            "max-width": "1200px",
                            "margin": "0 auto"
                        }
                    }
                ],
                "pages": [
                    {
                        "component": {
                            "type": "wrapper",
                            "components": [
                                {
                                    "tagName": "header",
                                    "attributes": { "id": "sample-header" },
                                    "components": [
                                        {
                                            "tagName": "h1",
                                            "type": "text",
                                            "components": [{ "type": "textnode", "content": "Welcome to Sample Page" }]
                                        },
                                        {
                                            "tagName": "p",
                                            "type": "text",
                                            "components": [{ "type": "textnode", "content": "This is a sample page created automatically" }]
                                        }
                                    ]
                                },
                                {
                                    "tagName": "div",
                                    "attributes": { "id": "sample-content" },
                                    "components": [
                                        {
                                            "tagName": "h2",
                                            "type": "text",
                                            "components": [{ "type": "textnode", "content": "Getting Started" }]
                                        },
                                        {
                                            "tagName": "p",
                                            "type": "text",
                                            "components": [{ "type": "textnode", "content": "Click 'Edit' to customize this page with the visual builder." }]
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                ]
            };

            // Generate HTML output
            const sampleHtml = `
<header id="sample-header">
    <h1>Welcome to Sample Page</h1>
    <p>This is a sample page created automatically</p>
</header>
<div id="sample-content">
    <h2>Getting Started</h2>
    <p>Click 'Edit' to customize this page with the visual builder.</p>
</div>`;

            // Generate CSS output
            const sampleCss = `
#sample-header {
    padding: 40px 20px;
    text-align: center;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: #ffffff;
}

#sample-content {
    padding: 40px 20px;
    max-width: 1200px;
    margin: 0 auto;
}`;

            const pageData = {
                name: `Sample Page ${randomId}`,
                slug: `sample-page-${timestamp}`,
                description: "Auto-generated sample page for testing",
                route_path: `/sample-${randomId}`,
                grapejs_data: sampleGrapejsData,
                html_output: sampleHtml.trim(),
                css_output: sampleCss.trim(),
                js_output: "",
                menu_label: `Sample ${randomId}`,
                menu_icon: "ph-duotone ph-star",
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

            showToast('Sample page created successfully!', 'success');

            // Reload pages to show the new page
            await this.loadPages();

        } catch (error) {
            console.error('Error creating sample page:', error);
            showToast(error.message || 'Failed to create sample page', 'error');
        }
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
                    <p class="text-gray-600 dark:text-gray-400 text-lg font-medium">No pages found</p>
                    <p class="text-gray-500 dark:text-gray-500 text-sm mt-2">Create your first page with the UI Builder</p>
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
            ? '<span class="px-2 py-1 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 text-xs font-medium rounded-full">Published</span>'
            : '<span class="px-2 py-1 bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-200 text-xs font-medium rounded-full">Draft</span>';

        const menuBadge = page.show_in_menu
            ? '<i class="ph-duotone ph-list-bullets text-purple-600" style="color: #8B5CF6" title="Shown in menu"></i>'
            : '';

        return `
            <div class="bg-white dark:bg-slate-800 rounded-lg border border-gray-200 dark:border-slate-700 overflow-hidden hover:shadow-lg transition group">
                <!-- Preview Thumbnail -->
                <div class="h-48 bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-slate-700 dark:to-slate-600 flex items-center justify-center overflow-hidden relative">
                    <i class="${page.menu_icon || 'ph-duotone ph-file-html'} text-6xl" style="color: #3B82F6"></i>
                    <div class="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-10 transition"></div>
                </div>

                <!-- Card Content -->
                <div class="p-4">
                    <div class="flex items-start justify-between mb-2">
                        <h3 class="font-semibold text-gray-900 dark:text-gray-100 text-lg flex-1 line-clamp-1">${page.name}</h3>
                        ${menuBadge}
                    </div>

                    <p class="text-sm text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">${page.description || 'No description'}</p>

                    <div class="flex items-center gap-2 mb-4">
                        ${statusBadge}
                        <span class="text-xs text-gray-500 dark:text-gray-500">
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
                           class="flex-1 px-3 py-2 bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-gray-300 text-sm font-medium rounded hover:bg-gray-200 dark:hover:bg-slate-600 transition text-center">
                            <i class="ph-duotone ph-pencil mr-1"></i>
                            Edit
                        </a>
                        <button onclick="window.builderShowcase.deletePage('${page.id}')"
                                class="px-3 py-2 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm font-medium rounded hover:bg-red-100 dark:hover:bg-red-900/40 transition">
                            <i class="ph-duotone ph-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    renderPageListItem(page) {
        const statusBadge = page.published
            ? '<span class="px-2 py-1 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 text-xs font-medium rounded-full">Published</span>'
            : '<span class="px-2 py-1 bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-200 text-xs font-medium rounded-full">Draft</span>';

        return `
            <div class="bg-white dark:bg-slate-800 rounded-lg border border-gray-200 dark:border-slate-700 p-4 hover:shadow-md transition">
                <div class="flex items-center gap-4">
                    <div class="w-16 h-16 bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-slate-700 dark:to-slate-600 rounded-lg flex items-center justify-center flex-shrink-0">
                        <i class="${page.menu_icon || 'ph-duotone ph-file-html'} text-3xl" style="color: #3B82F6"></i>
                    </div>

                    <div class="flex-1 min-w-0">
                        <div class="flex items-center gap-2 mb-1">
                            <h3 class="font-semibold text-gray-900 dark:text-gray-100 text-lg">${page.name}</h3>
                            ${statusBadge}
                            ${page.show_in_menu ? '<i class="ph-duotone ph-list-bullets text-purple-600" style="color: #8B5CF6"></i>' : ''}
                        </div>
                        <p class="text-sm text-gray-600 dark:text-gray-400 mb-1">${page.description || 'No description'}</p>
                        <div class="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-500">
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
                           class="px-4 py-2 bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-gray-300 text-sm font-medium rounded hover:bg-gray-200 dark:hover:bg-slate-600 transition">
                            <i class="ph-duotone ph-pencil mr-1"></i>
                            Edit
                        </a>
                        <button onclick="window.builderShowcase.deletePage('${page.id}')"
                                class="px-4 py-2 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm font-medium rounded hover:bg-red-100 dark:hover:bg-red-900/40 transition">
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
                        <span class="text-gray-600 dark:text-gray-400">Route:</span>
                        <span class="font-mono text-blue-600 dark:text-blue-400 ml-2">${page.route_path}</span>
                    </div>
                    <div>
                        <span class="text-gray-600 dark:text-gray-400">Status:</span>
                        <span class="ml-2">${page.published ? '✅ Published' : '📝 Draft'}</span>
                    </div>
                </div>
                <iframe srcdoc="${previewHTML.replace(/"/g, '&quot;')}"
                        class="w-full h-[600px] border border-gray-200 dark:border-slate-700 rounded-lg bg-white">
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
