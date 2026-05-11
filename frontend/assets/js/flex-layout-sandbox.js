/**
 * Flex Layout Sandbox — wires up one instance of every layout primitive
 * shipped in epic-21 sprint 1 (story 15.1.1) onto the sandbox template.
 * Loaded when the `flex-layout-sandbox` route resolves. Not in the
 * main menu — reachable via direct hash navigation only, so the page
 * is dev-discoverable but doesn't surface in production navigation.
 *
 * T-21.1.7
 *
 * @author Claude Code
 * @version 1.0.0
 */

import FlexStack from './components/flex-stack.js';
import FlexCluster from './components/flex-cluster.js';
import FlexContainer from './components/flex-container.js';
import FlexGrid from './components/flex-grid.js';
import FlexSection from './components/flex-section.js';
import FlexSidebar from './components/flex-sidebar.js';
import FlexSplitPane from './components/flex-split-pane.js';
import FlexToolbar from './components/flex-toolbar.js';
import FlexMasonry from './components/flex-masonry.js';

function initSandbox() {
    const targets = [
        ['#sb-stack',      () => new FlexStack('#sb-stack',      { direction: 'vertical', gap: 'md', align: 'stretch' })],
        ['#sb-cluster',    () => new FlexCluster('#sb-cluster',  { gap: 'sm', align: 'center' })],
        ['#sb-container',  () => new FlexContainer('#sb-container', { maxWidth: 'md', padding: 'lg' })],
        ['#sb-grid',       () => new FlexGrid('#sb-grid',        { columns: '1 2 3', gap: 'md' })],
        ['#sb-section',    () => new FlexSection('#sb-section',  { title: 'Quarterly Report', level: 'h3' })],
        ['#sb-sidebar',    () => new FlexSidebar('#sb-sidebar',  { side: 'left', sidebarWidth: '200px', contentMinWidth: '300px' })],
        ['#sb-split',      () => new FlexSplitPane('#sb-split',  { initialSplit: '40%', minLeft: '120px', minRight: '120px' })],
        ['#sb-toolbar',    () => new FlexToolbar('#sb-toolbar',  { sticky: false })],
        ['#sb-masonry',    () => new FlexMasonry('#sb-masonry',  { columnWidth: '200px', gap: 'md' })]
    ];

    for (const [selector, factory] of targets) {
        const el = document.querySelector(selector);
        if (!el) continue;
        try {
            factory();
        } catch (err) {
            console.error(`flex-layout-sandbox: ${selector} failed to initialize`, err);
            el.innerHTML = `<div class="text-red-700 text-sm bg-red-50 p-3 rounded">Failed to initialize: ${err.message}</div>`;
        }
    }
}

document.addEventListener('route:loaded', (event) => {
    const route = event.detail && event.detail.route;
    if (route === 'flex-layout-sandbox') {
        initSandbox();
    }
});

export { initSandbox };
