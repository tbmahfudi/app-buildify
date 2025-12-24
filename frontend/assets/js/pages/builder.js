/**
 * Builder Page - Main GrapeJS UI Builder
 *
 * Comprehensive UI builder with component library integration
 */

import { can } from '../rbac.js';
import { showToast } from '../ui-utils.js';
import { registerComponents } from '../components/builder-component-registry.js';
import { BuilderConfigPanel } from '../components/builder-config-panel.js';

export class BuilderPage {
    constructor() {
        this.editor = null;
        this.currentPage = null;
        this.configPanel = null;
        this.currentTab = 'design';
    }

    async render() {
        // Check permission
        if (!can('builder:design:tenant')) {
            return `
                <div class="flex items-center justify-center h-screen">
                    <div class="text-center">
                        <i class="ph-duotone ph-lock text-6xl text-gray-400 mb-4"></i>
                        <h2 class="text-2xl font-bold text-gray-700 dark:text-gray-300">Access Denied</h2>
                        <p class="text-gray-500 dark:text-gray-400 mt-2">
                            You don't have permission to access the UI Builder
                        </p>
                    </div>
                </div>
            `;
        }

        return `
            <div id="builder-container" class="h-screen flex flex-col bg-gray-50 dark:bg-slate-900">
                <!-- Header -->
                <div class="bg-white dark:bg-slate-800 border-b border-gray-200 dark:border-slate-700 px-4 py-3 flex items-center justify-between">
                    <div class="flex items-center gap-4">
                        <h1 class="text-xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                            <i class="ph-duotone ph-code-block text-blue-600"></i>
                            UI Builder
                        </h1>
                        <div id="page-name-display" class="text-sm text-gray-500 dark:text-gray-400">
                            <span id="current-page-name">New Page</span>
                        </div>
                    </div>
                    <div class="flex items-center gap-2">
                        <!-- Toolbar Panels -->
                        <div class="panel__devices flex items-center gap-1 mr-4"></div>
                        <div class="panel__basic-actions flex items-center gap-1 mr-4"></div>

                        <button id="btn-load" class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-slate-700 border border-gray-300 dark:border-slate-600 rounded-lg hover:bg-gray-50 dark:hover:bg-slate-600 transition">
                            <i class="ph-duotone ph-folder-open mr-2"></i>Load
                        </button>
                        <button id="btn-save" class="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition">
                            <i class="ph-duotone ph-floppy-disk mr-2"></i>Save
                        </button>
                        <button id="btn-publish" class="px-4 py-2 text-sm font-medium text-white bg-green-600 hover:bg-green-700 rounded-lg transition" disabled>
                            <i class="ph-duotone ph-rocket-launch mr-2"></i>Publish
                        </button>
                        <button id="btn-preview" class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-slate-700 border border-gray-300 dark:border-slate-600 rounded-lg hover:bg-gray-50 dark:hover:bg-slate-600 transition">
                            <i class="ph-duotone ph-eye mr-2"></i>Preview
                        </button>
                    </div>
                </div>

                <!-- Editor Container -->
                <div class="flex-1 flex overflow-hidden">
                    <!-- Left Sidebar - Blocks & Components -->
                    <div class="w-64 bg-white dark:bg-slate-800 border-r border-gray-200 dark:border-slate-700 overflow-y-auto">
                        <div class="p-4">
                            <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
                                <i class="ph-duotone ph-stack"></i>
                                Components
                            </h3>
                            <div id="blocks"></div>
                        </div>
                    </div>

                    <!-- GrapeJS Editor -->
                    <div id="gjs" class="flex-1"></div>

                    <!-- Right Sidebar - Layers, Styles & Traits -->
                    <div class="w-80 bg-white dark:bg-slate-800 border-l border-gray-200 dark:border-slate-700 flex flex-col">
                        <!-- Tab Navigation -->
                        <div class="flex border-b border-gray-200 dark:border-slate-700">
                            <button id="tab-design" class="flex-1 px-4 py-3 text-sm font-medium text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400 bg-blue-50 dark:bg-slate-900">
                                <i class="ph-duotone ph-palette mr-2"></i>Design
                            </button>
                            <button id="tab-source" class="flex-1 px-4 py-3 text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-slate-700 transition">
                                <i class="ph-duotone ph-code mr-2"></i>Source
                            </button>
                        </div>

                        <!-- Tab Content Container -->
                        <div class="flex-1 overflow-y-auto">
                            <!-- Design Tab -->
                            <div id="design-tab-content" class="tab-content">
                                <!-- Layers -->
                                <div class="border-b border-gray-200 dark:border-slate-700 p-4">
                                    <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
                                        <i class="ph-duotone ph-tree-structure"></i>
                                        Layers
                                    </h3>
                                    <div class="layers-container"></div>
                                </div>

                                <!-- Traits -->
                                <div class="border-b border-gray-200 dark:border-slate-700 p-4">
                                    <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
                                        <i class="ph-duotone ph-sliders"></i>
                                        Settings
                                    </h3>
                                    <div class="traits-container"></div>
                                </div>

                                <!-- Styles -->
                                <div class="p-4">
                                    <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
                                        <i class="ph-duotone ph-palette"></i>
                                        Styles
                                    </h3>
                                    <div class="styles-container"></div>
                                </div>
                            </div>

                            <!-- Source Tab -->
                            <div id="source-tab-content" class="tab-content hidden">
                                <!-- HTML Section -->
                                <div class="border-b border-gray-200 dark:border-slate-700 p-4">
                                    <div class="flex items-center justify-between mb-3">
                                        <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
                                            <i class="ph-duotone ph-file-html"></i>
                                            HTML
                                        </h3>
                                        <button id="copy-html" class="px-2 py-1 text-xs bg-gray-200 dark:bg-slate-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-300 dark:hover:bg-slate-600 transition">
                                            <i class="ph-duotone ph-copy"></i> Copy
                                        </button>
                                    </div>
                                    <pre id="html-output" class="bg-gray-900 text-green-400 p-3 rounded text-xs overflow-auto max-h-64 font-mono"></pre>
                                </div>

                                <!-- CSS Section -->
                                <div class="border-b border-gray-200 dark:border-slate-700 p-4">
                                    <div class="flex items-center justify-between mb-3">
                                        <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
                                            <i class="ph-duotone ph-file-css"></i>
                                            CSS
                                        </h3>
                                        <button id="copy-css" class="px-2 py-1 text-xs bg-gray-200 dark:bg-slate-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-300 dark:hover:bg-slate-600 transition">
                                            <i class="ph-duotone ph-copy"></i> Copy
                                        </button>
                                    </div>
                                    <pre id="css-output" class="bg-gray-900 text-blue-400 p-3 rounded text-xs overflow-auto max-h-64 font-mono"></pre>
                                </div>

                                <!-- JS Section -->
                                <div class="p-4">
                                    <div class="flex items-center justify-between mb-3">
                                        <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
                                            <i class="ph-duotone ph-file-js"></i>
                                            JavaScript
                                        </h3>
                                        <button id="copy-js" class="px-2 py-1 text-xs bg-gray-200 dark:bg-slate-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-300 dark:hover:bg-slate-600 transition">
                                            <i class="ph-duotone ph-copy"></i> Copy
                                        </button>
                                    </div>
                                    <pre id="js-output" class="bg-gray-900 text-yellow-400 p-3 rounded text-xs overflow-auto max-h-64 font-mono"></pre>
                                </div>

                                <!-- Refresh Button -->
                                <div class="p-4 border-t border-gray-200 dark:border-slate-700">
                                    <button id="refresh-source" class="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition text-sm font-medium">
                                        <i class="ph-duotone ph-arrows-clockwise mr-2"></i>
                                        Refresh Source
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    async afterRender() {
        // Initialize GrapeJS
        await this.initializeGrapeJS();

        // Setup event listeners
        this.setupEventListeners();

        // Initialize config panel
        this.configPanel = new BuilderConfigPanel(this.editor);
        await this.configPanel.init();

        // Check if loading existing page
        const urlParams = new URLSearchParams(window.location.search);
        const pageId = urlParams.get('page');
        if (pageId) {
            await this.loadPage(pageId);
        }
    }

    async initializeGrapeJS() {
        // Load GrapeJS from CDN if not already loaded
        if (!window.grapesjs) {
            await this.loadGrapeJSLibrary();
        }

        const gjs = window.grapesjs;

        // Initialize editor
        this.editor = gjs.init({
            container: '#gjs',
            height: '100%',
            width: '100%',

            // Storage
            storageManager: false, // We'll handle storage via our API

            // Panels
            panels: {
                defaults: [
                    {
                        id: 'basic-actions',
                        el: '.panel__basic-actions',
                        buttons: [
                            {
                                id: 'visibility',
                                active: true,
                                className: 'btn-toggle-borders',
                                label: '<i class="ph-duotone ph-eye"></i>',
                                command: 'sw-visibility',
                            },
                            {
                                id: 'fullscreen',
                                className: 'btn-fullscreen',
                                label: '<i class="ph-duotone ph-arrows-out"></i>',
                                command: 'fullscreen',
                                context: 'fullscreen',
                                attributes: { title: 'Fullscreen' }
                            }
                        ]
                    },
                    {
                        id: 'panel-devices',
                        el: '.panel__devices',
                        buttons: [
                            {
                                id: 'device-desktop',
                                label: '<i class="ph-duotone ph-desktop"></i>',
                                command: 'set-device-desktop',
                                active: true,
                                togglable: false,
                            },
                            {
                                id: 'device-tablet',
                                label: '<i class="ph-duotone ph-device-tablet"></i>',
                                command: 'set-device-tablet',
                                togglable: false,
                            },
                            {
                                id: 'device-mobile',
                                label: '<i class="ph-duotone ph-device-mobile"></i>',
                                command: 'set-device-mobile',
                                togglable: false,
                            }
                        ]
                    }
                ]
            },

            // Device manager
            deviceManager: {
                devices: [
                    {
                        name: 'Desktop',
                        width: '',
                    },
                    {
                        name: 'Tablet',
                        width: '768px',
                        widthMedia: '768px'
                    },
                    {
                        name: 'Mobile',
                        width: '375px',
                        widthMedia: '375px'
                    }
                ]
            },

            // Block Manager
            blockManager: {
                appendTo: '#blocks',
                blocks: [] // Will be populated by component registry
            },

            // Style Manager
            styleManager: {
                appendTo: '.styles-container',
                sectors: [
                    {
                        name: 'Dimension',
                        open: false,
                        buildProps: ['width', 'min-height', 'padding', 'margin'],
                        properties: [
                            {
                                type: 'integer',
                                name: 'Width',
                                property: 'width',
                                units: ['px', '%', 'vw'],
                                defaults: 'auto'
                            },
                            {
                                property: 'min-height',
                                type: 'integer',
                                units: ['px', '%', 'vh'],
                                defaults: '0'
                            },
                            {
                                property: 'padding',
                                properties: [
                                    { name: 'Top', property: 'padding-top' },
                                    { name: 'Right', property: 'padding-right' },
                                    { name: 'Bottom', property: 'padding-bottom' },
                                    { name: 'Left', property: 'padding-left' }
                                ]
                            },
                            {
                                property: 'margin',
                                properties: [
                                    { name: 'Top', property: 'margin-top' },
                                    { name: 'Right', property: 'margin-right' },
                                    { name: 'Bottom', property: 'margin-bottom' },
                                    { name: 'Left', property: 'margin-left' }
                                ]
                            }
                        ]
                    },
                    {
                        name: 'Typography',
                        open: false,
                        buildProps: ['font-family', 'font-size', 'font-weight', 'letter-spacing', 'color', 'line-height', 'text-align'],
                        properties: [
                            { name: 'Font', property: 'font-family' },
                            { name: 'Weight', property: 'font-weight' },
                            { name: 'Font color', property: 'color' },
                            {
                                property: 'text-align',
                                type: 'radio',
                                defaults: 'left',
                                list: [
                                    { value: 'left', name: 'Left', className: 'fa fa-align-left' },
                                    { value: 'center', name: 'Center', className: 'fa fa-align-center' },
                                    { value: 'right', name: 'Right', className: 'fa fa-align-right' },
                                    { value: 'justify', name: 'Justify', className: 'fa fa-align-justify' }
                                ]
                            }
                        ]
                    },
                    {
                        name: 'Decorations',
                        open: false,
                        buildProps: ['background-color', 'border-radius', 'border', 'box-shadow', 'background'],
                    },
                    {
                        name: 'Extra',
                        open: false,
                        buildProps: ['transition', 'perspective', 'transform'],
                    },
                    {
                        name: 'Flex',
                        open: false,
                        properties: [
                            {
                                name: 'Flex Container',
                                property: 'display',
                                type: 'select',
                                defaults: 'block',
                                list: [
                                    { value: 'block', name: 'Block' },
                                    { value: 'flex', name: 'Flex' },
                                    { value: 'grid', name: 'Grid' }
                                ]
                            },
                            {
                                name: 'Flex Direction',
                                property: 'flex-direction',
                                type: 'radio',
                                defaults: 'row',
                                list: [
                                    { value: 'row', name: 'Row' },
                                    { value: 'row-reverse', name: 'Row reverse' },
                                    { value: 'column', name: 'Column' },
                                    { value: 'column-reverse', name: 'Column reverse' }
                                ]
                            },
                            {
                                name: 'Justify',
                                property: 'justify-content',
                                type: 'select',
                                list: [
                                    { value: 'flex-start', name: 'Start' },
                                    { value: 'flex-end', name: 'End' },
                                    { value: 'center', name: 'Center' },
                                    { value: 'space-between', name: 'Space between' },
                                    { value: 'space-around', name: 'Space around' },
                                    { value: 'space-evenly', name: 'Space evenly' }
                                ]
                            },
                            {
                                name: 'Align',
                                property: 'align-items',
                                type: 'select',
                                list: [
                                    { value: 'flex-start', name: 'Start' },
                                    { value: 'flex-end', name: 'End' },
                                    { value: 'center', name: 'Center' },
                                    { value: 'baseline', name: 'Baseline' },
                                    { value: 'stretch', name: 'Stretch' }
                                ]
                            },
                            {
                                name: 'Gap',
                                property: 'gap',
                                type: 'integer',
                                units: ['px', 'rem', 'em'],
                                defaults: '0'
                            }
                        ]
                    }
                ]
            },

            // Layer Manager
            layerManager: {
                appendTo: '.layers-container'
            },

            // Trait Manager
            traitManager: {
                appendTo: '.traits-container'
            },

            // Canvas
            canvas: {
                styles: [
                    'https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css'
                ],
                scripts: []
            }
        });

        // Register all components
        await registerComponents(this.editor);

        // Add custom commands
        this.registerCommands();

        console.log('GrapeJS initialized');
    }

    async loadGrapeJSLibrary() {
        return new Promise((resolve, reject) => {
            // Check if already loaded
            if (window.grapesjs) {
                resolve();
                return;
            }

            // Load CSS
            const css = document.createElement('link');
            css.rel = 'stylesheet';
            css.href = 'https://unpkg.com/grapesjs/dist/css/grapes.min.css';
            document.head.appendChild(css);

            // Load JS
            const script = document.createElement('script');
            script.src = 'https://unpkg.com/grapesjs';
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    registerCommands() {
        const editor = this.editor;

        // Device commands
        editor.Commands.add('set-device-desktop', {
            run: editor => editor.setDevice('Desktop')
        });
        editor.Commands.add('set-device-tablet', {
            run: editor => editor.setDevice('Tablet')
        });
        editor.Commands.add('set-device-mobile', {
            run: editor => editor.setDevice('Mobile')
        });

        // Fullscreen command
        editor.Commands.add('fullscreen', {
            run(editor) {
                const el = editor.getContainer();
                if (el.requestFullscreen) {
                    el.requestFullscreen();
                } else if (el.webkitRequestFullscreen) {
                    el.webkitRequestFullscreen();
                }
            },
            stop(editor) {
                if (document.exitFullscreen) {
                    document.exitFullscreen();
                } else if (document.webkitExitFullscreen) {
                    document.webkitExitFullscreen();
                }
            }
        });
    }

    setupEventListeners() {
        // Save button
        document.getElementById('btn-save')?.addEventListener('click', () => {
            this.savePage();
        });

        // Load button
        document.getElementById('btn-load')?.addEventListener('click', () => {
            this.showLoadPageDialog();
        });

        // Publish button
        document.getElementById('btn-publish')?.addEventListener('click', () => {
            this.publishPage();
        });

        // Preview button
        document.getElementById('btn-preview')?.addEventListener('click', () => {
            this.previewPage();
        });

        // Tab switching
        document.getElementById('tab-design')?.addEventListener('click', () => {
            this.switchTab('design');
        });

        document.getElementById('tab-source')?.addEventListener('click', () => {
            this.switchTab('source');
            this.updateSourceCode();
        });

        // Refresh source button
        document.getElementById('refresh-source')?.addEventListener('click', () => {
            this.updateSourceCode();
            showToast('Source code refreshed', 'success');
        });

        // Copy buttons
        document.getElementById('copy-html')?.addEventListener('click', () => {
            this.copyToClipboard('html');
        });

        document.getElementById('copy-css')?.addEventListener('click', () => {
            this.copyToClipboard('css');
        });

        document.getElementById('copy-js')?.addEventListener('click', () => {
            this.copyToClipboard('js');
        });

        // Auto-refresh source on editor changes (debounced)
        let sourceUpdateTimeout;
        this.editor.on('component:update', () => {
            if (this.currentTab === 'source') {
                clearTimeout(sourceUpdateTimeout);
                sourceUpdateTimeout = setTimeout(() => {
                    this.updateSourceCode();
                }, 500);
            }
        });
    }

    switchTab(tabName) {
        this.currentTab = tabName;

        const designTab = document.getElementById('tab-design');
        const sourceTab = document.getElementById('tab-source');
        const designContent = document.getElementById('design-tab-content');
        const sourceContent = document.getElementById('source-tab-content');

        if (tabName === 'design') {
            // Activate design tab
            designTab.classList.add('text-blue-600', 'dark:text-blue-400', 'border-b-2', 'border-blue-600', 'dark:border-blue-400', 'bg-blue-50', 'dark:bg-slate-900');
            designTab.classList.remove('text-gray-600', 'dark:text-gray-400');
            sourceTab.classList.remove('text-blue-600', 'dark:text-blue-400', 'border-b-2', 'border-blue-600', 'dark:border-blue-400', 'bg-blue-50', 'dark:bg-slate-900');
            sourceTab.classList.add('text-gray-600', 'dark:text-gray-400');

            // Show design content
            designContent.classList.remove('hidden');
            sourceContent.classList.add('hidden');
        } else {
            // Activate source tab
            sourceTab.classList.add('text-blue-600', 'dark:text-blue-400', 'border-b-2', 'border-blue-600', 'dark:border-blue-400', 'bg-blue-50', 'dark:bg-slate-900');
            sourceTab.classList.remove('text-gray-600', 'dark:text-gray-400');
            designTab.classList.remove('text-blue-600', 'dark:text-blue-400', 'border-b-2', 'border-blue-600', 'dark:border-blue-400', 'bg-blue-50', 'dark:bg-slate-900');
            designTab.classList.add('text-gray-600', 'dark:text-gray-400');

            // Show source content
            sourceContent.classList.remove('hidden');
            designContent.classList.add('hidden');
        }
    }

    updateSourceCode() {
        if (!this.editor) return;

        // Get HTML
        const html = this.editor.getHtml();
        const htmlOutput = document.getElementById('html-output');
        if (htmlOutput) {
            htmlOutput.textContent = this.formatHTML(html);
        }

        // Get CSS
        const css = this.editor.getCss();
        const cssOutput = document.getElementById('css-output');
        if (cssOutput) {
            cssOutput.textContent = css || '/* No styles yet */';
        }

        // Get JS (from component scripts)
        const js = this.extractJavaScript();
        const jsOutput = document.getElementById('js-output');
        if (jsOutput) {
            jsOutput.textContent = js || '// No JavaScript yet';
        }
    }

    formatHTML(html) {
        // Simple HTML formatter
        if (!html) return '<!-- No HTML yet -->';

        let formatted = '';
        let indent = 0;
        const tab = '  ';

        html.split(/>\s*</).forEach((node, index) => {
            if (node.match(/^\/\w/)) {
                indent = Math.max(0, indent - 1);
            }

            if (index > 0) formatted += '<';
            formatted += tab.repeat(indent) + node + (index < html.split(/>\s*</).length - 1 ? '>\n' : '');

            if (node.match(/^<?\w[^>]*[^\/]$/) && !node.startsWith('input') && !node.startsWith('img') && !node.startsWith('br') && !node.startsWith('hr')) {
                indent++;
            }
        });

        return formatted.trim();
    }

    extractJavaScript() {
        // Extract JavaScript from component scripts
        const components = this.editor.getComponents();
        let scripts = [];

        const extractScripts = (component) => {
            const script = component.get('script');
            if (script && typeof script === 'function') {
                scripts.push(script.toString());
            }

            // Recursively extract from children
            const children = component.components();
            if (children && children.length > 0) {
                children.forEach(child => extractScripts(child));
            }
        };

        components.forEach(component => extractScripts(component));

        if (scripts.length === 0) {
            return '// No JavaScript yet';
        }

        return '// Component Scripts\n\n' + scripts.join('\n\n// ---\n\n');
    }

    async copyToClipboard(type) {
        let content = '';
        let label = '';

        switch (type) {
            case 'html':
                content = this.editor.getHtml();
                label = 'HTML';
                break;
            case 'css':
                content = this.editor.getCss();
                label = 'CSS';
                break;
            case 'js':
                content = this.extractJavaScript();
                label = 'JavaScript';
                break;
        }

        try {
            await navigator.clipboard.writeText(content);
            showToast(`${label} copied to clipboard`, 'success');
        } catch (error) {
            console.error('Failed to copy:', error);
            showToast(`Failed to copy ${label}`, 'error');
        }
    }

    async savePage() {
        try {
            const pageData = this.configPanel.getPageConfig();
            const grapesjsData = this.editor.getProjectData();
            const html = this.editor.getHtml();
            const css = this.editor.getCss();

            const payload = {
                ...pageData,
                grapejs_data: grapesjsData,
                html_output: html,
                css_output: css
            };

            let response;
            if (this.currentPage?.id) {
                // Update existing page
                response = await fetch(`/api/v1/builder/pages/${this.currentPage.id}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                    },
                    body: JSON.stringify(payload)
                });
            } else {
                // Create new page
                response = await fetch('/api/v1/builder/pages/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                    },
                    body: JSON.stringify(payload)
                });
            }

            if (response.ok) {
                const savedPage = await response.json();
                this.currentPage = savedPage;
                document.getElementById('current-page-name').textContent = savedPage.name;
                document.getElementById('btn-publish').disabled = false;
                showToast('Page saved successfully', 'success');
            } else {
                throw new Error('Failed to save page');
            }
        } catch (error) {
            console.error('Error saving page:', error);
            showToast('Failed to save page', 'error');
        }
    }

    async loadPage(pageId) {
        try {
            const response = await fetch(`/api/v1/builder/pages/${pageId}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            if (response.ok) {
                const page = await response.json();
                this.currentPage = page;

                // Load into editor
                this.editor.loadProjectData(page.grapejs_data);

                // Update config panel
                this.configPanel.setPageConfig(page);

                // Update UI
                document.getElementById('current-page-name').textContent = page.name;
                document.getElementById('btn-publish').disabled = !page.published;

                showToast('Page loaded successfully', 'success');
            } else {
                throw new Error('Failed to load page');
            }
        } catch (error) {
            console.error('Error loading page:', error);
            showToast('Failed to load page', 'error');
        }
    }

    showLoadPageDialog() {
        // TODO: Implement load page dialog with page list
        showToast('Load page dialog coming soon', 'info');
    }

    async publishPage() {
        if (!this.currentPage?.id) {
            showToast('Please save the page first', 'warning');
            return;
        }

        try {
            const response = await fetch(`/api/v1/builder/pages/${this.currentPage.id}/publish`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({
                    commit_message: `Published version at ${new Date().toISOString()}`
                })
            });

            if (response.ok) {
                const publishedPage = await response.json();
                this.currentPage = publishedPage;
                showToast('Page published successfully', 'success');
            } else {
                throw new Error('Failed to publish page');
            }
        } catch (error) {
            console.error('Error publishing page:', error);
            showToast('Failed to publish page', 'error');
        }
    }

    previewPage() {
        const html = this.editor.getHtml();
        const css = this.editor.getCss();

        const previewContent = `
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
                <style>${css}</style>
            </head>
            <body>
                ${html}
            </body>
            </html>
        `;

        const previewWindow = window.open('', '_blank');
        previewWindow.document.write(previewContent);
        previewWindow.document.close();
    }

    cleanup() {
        if (this.editor) {
            this.editor.destroy();
        }
    }
}
