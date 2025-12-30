/**
 * Builder Page - Main GrapeJS UI Builder
 *
 * Comprehensive UI builder with component library integration
 *
 * Pattern: Template-based (similar to tenants.js)
 * - HTML template loaded from /assets/templates/builder.html
 * - This script listens for 'route:loaded' event
 * - Initializes GrapeJS editor after template is in DOM
 */

import { can } from './rbac.js';
import { showToast } from './ui-utils.js';
import { registerComponents } from './components/builder-component-registry.js';
import { BuilderConfigPanel } from './components/builder-config-panel.js';
import { authService } from './auth-service.js';

let builderPage = null;

// App load (first time)
document.addEventListener('DOMContentLoaded', () => {
    builderPage = new BuilderPage();
});

// Route change
document.addEventListener('route:loaded', async (event) => {
    if (event.detail.route === 'builder') {
        console.log('Builder page route loaded');
        // Ensure DOM from template is ready
        setTimeout(async () => {
            try {
                if (!builderPage) {
                    console.log('Creating new BuilderPage instance');
                    builderPage = new BuilderPage();
                }
                await builderPage.afterRender();
            } catch (error) {
                console.error('Error initializing builder page:', error);
                showToast('Failed to initialize builder page: ' + error.message, 'error');
            }
        }, 0);
    }
});

document.addEventListener('route:before-change', (event) => {
    if (event.detail.from === 'builder' && builderPage) {
        builderPage.cleanup();
        builderPage = null;
    }
});

export class BuilderPage {
    constructor() {
        this.editor = null;
        this.currentPage = null;
        this.configPanel = null;
        this.currentTab = 'design';
    }

    async afterRender() {
        // Parse page ID from hash-based URL (e.g., #builder?page=123)
        const hash = window.location.hash;
        const queryString = hash.includes('?') ? hash.split('?')[1] : '';
        const params = new URLSearchParams(queryString);
        const pageId = params.get('page');

        console.log('Checking for page ID in URL:', { hash, queryString, pageId });

        // If editor already exists, just load the new page
        if (this.editor) {
            console.log('Builder already initialized, loading new page');
            if (pageId) {
                await this.loadPage(pageId);
            }
            return;
        }

        // Initialize GrapeJS for the first time
        await this.initializeGrapeJS();
        this.setupEventListeners();

        this.configPanel = new BuilderConfigPanel(this.editor);
        await this.configPanel.init();

        if (pageId) {
            console.log('Loading page:', pageId);
            await this.loadPage(pageId);
        }
    }

    async initializeGrapeJS() {
        // Load GrapeJS from CDN if not already loaded
        if (!window.grapesjs) {
            await this.loadGrapeJSLibrary();
        }

        // Verify container exists
        const container = document.getElementById('gjs');
        if (!container) {
            console.error('GrapeJS container (#gjs) not found in DOM!');
            throw new Error('GrapeJS container element not found. Please ensure the template is loaded correctly.');
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
                                    { value: 'left', name: 'Left', className: 'ph ph-text-align-left' },
                                    { value: 'center', name: 'Center', className: 'ph ph-text-align-center' },
                                    { value: 'right', name: 'Right', className: 'ph ph-text-align-right' },
                                    { value: 'justify', name: 'Justify', className: 'ph ph-text-align-justify' }
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
        console.log('Loading GrapeJS');        
        return new Promise((resolve, reject) => {
            // Check if already loaded
            if (window.grapesjs) {
                console.log('GrapeJS Already Loaded!');        
                resolve();
                return;
            }
            console.log('Adding GrapeJS');        

            // Load CSS
            const css = document.createElement('link');
            css.rel = 'stylesheet';
            css.href = 'https://unpkg.com/grapesjs/dist/css/grapes.min.css';
            document.head.appendChild(css);

            // Add custom CSS override for panel positioning (after GrapeJS CSS)
            const customStyle = document.createElement('style');
            customStyle.textContent = `
                /* Override GrapeJS absolute positioning for toolbar panels */
                .gjs-pn-panel {
                    position: relative !important;
                    display: inline-flex !important;
                    vertical-align: middle !important;
                }

                /* Ensure panel buttons are properly styled */
                .gjs-pn-btn {
                    display: inline-flex !important;
                    align-items: center !important;
                    justify-content: center !important;
                }
            `;
            document.head.appendChild(customStyle);

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
            const token = authService.getToken();
            if (!token) {
                showToast('Please log in to save pages', 'error');
                return;
            }

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
                response = await fetch(`/api/v1/builder/${this.currentPage.id}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify(payload)
                });
            } else {
                // Create new page
                response = await fetch('/api/v1/builder/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
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
            const token = authService.getToken();
            if (!token) {
                showToast('Please log in to load pages', 'error');
                return;
            }

            const response = await fetch(`/api/v1/builder/${pageId}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
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
            const response = await fetch(`/api/v1/builder/${this.currentPage.id}/publish`, {
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
