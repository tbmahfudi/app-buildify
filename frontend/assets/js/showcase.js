/**
 * Components Showcase Module
 *
 * Demonstrates all components: Layout (FlexStack, FlexGrid), Phase 2 (FlexContainer, FlexSection, FlexSidebar),
 * FlexCard, FlexModal, and FlexTabs
 *
 * @author Claude Code
 * @version 2.0.0
 */

import { FlexCard } from './components/flex-card.js';
import { FlexModal } from './components/flex-modal.js';
import { FlexTabs } from './components/flex-tabs.js';
import { FlexStack } from './layout/flex-stack.js';
import { FlexGrid } from './layout/flex-grid.js';
import FlexContainer from './layout/flex-container.js';
import FlexSection from './layout/flex-section.js';
import FlexSidebar from './layout/flex-sidebar.js';
import { showToast } from './ui-utils.js';

let modals = {};
let cards = {};
let tabs = {};
let stacks = {};
let grids = {};
let containers = {};
let sections = {};
let sidebars = {};

/**
 * Initialize showcase on route load
 */
document.addEventListener('route:loaded', async (e) => {
    if (e.detail.route === 'components-showcase') {
        initShowcase();
    }
});

/**
 * Initialize all component demonstrations
 */
function initShowcase() {
    console.log('Initializing Components Showcase...');

    // Initialize layout components (Foundation MVP)
    initLayoutExamples();

    // Initialize Phase 2 components
    initPhase2ContainerExamples();
    initPhase2SectionExamples();
    initPhase2SidebarExamples();
    initPhase2CombinedExample();

    // Initialize card examples
    initCardExamples();

    // Initialize modal examples
    initModalExamples();

    // Initialize tabs examples
    initTabsExamples();

    // Initialize combined example (Foundation MVP)
    initCombinedExample();
}

/**
 * Initialize Layout Examples (FlexStack and FlexGrid)
 */
function initLayoutExamples() {
    // FlexStack Examples

    // 1. Horizontal Stack
    const stackHorizontal = new FlexStack('#stack-horizontal', {
        direction: 'horizontal',
        gap: 3,
        align: 'center',
        justify: 'start',
        items: [
            {
                content: `<button class="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 flex items-center gap-2">
                    <i class="ph ph-plus"></i>
                    <span>New</span>
                </button>`
            },
            {
                content: `<button class="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 flex items-center gap-2">
                    <i class="ph ph-pencil"></i>
                    <span>Edit</span>
                </button>`
            },
            {
                content: `<button class="px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600 flex items-center gap-2">
                    <i class="ph ph-trash"></i>
                    <span>Delete</span>
                </button>`
            }
        ]
    });

    // 2. Vertical Stack
    const stackVertical = new FlexStack('#stack-vertical', {
        direction: 'vertical',
        gap: 2,
        align: 'stretch',
        items: [
            {
                content: `<div class="p-3 bg-blue-50 border border-blue-200 rounded-md">
                    <div class="flex items-center gap-2">
                        <i class="ph-fill ph-check-circle text-blue-600"></i>
                        <span class="text-sm text-blue-900">Task completed</span>
                    </div>
                </div>`
            },
            {
                content: `<div class="p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                    <div class="flex items-center gap-2">
                        <i class="ph-fill ph-warning text-yellow-600"></i>
                        <span class="text-sm text-yellow-900">Pending review</span>
                    </div>
                </div>`
            },
            {
                content: `<div class="p-3 bg-green-50 border border-green-200 rounded-md">
                    <div class="flex items-center gap-2">
                        <i class="ph-fill ph-info text-green-600"></i>
                        <span class="text-sm text-green-900">All systems operational</span>
                    </div>
                </div>`
            }
        ]
    });

    // 3. Stack with Dividers
    const stackDividers = new FlexStack('#stack-dividers', {
        direction: 'horizontal',
        gap: 4,
        align: 'center',
        divider: {
            enabled: true,
            variant: 'line',
            color: 'gray-300'
        },
        items: [
            {
                content: `<div class="text-center">
                    <div class="text-2xl font-bold text-gray-900">1,234</div>
                    <div class="text-xs text-gray-500">Users</div>
                </div>`
            },
            {
                content: `<div class="text-center">
                    <div class="text-2xl font-bold text-gray-900">89</div>
                    <div class="text-xs text-gray-500">Active</div>
                </div>`
            },
            {
                content: `<div class="text-center">
                    <div class="text-2xl font-bold text-gray-900">45</div>
                    <div class="text-xs text-gray-500">Pending</div>
                </div>`
            }
        ]
    });

    // 4. Responsive Stack (vertical on mobile, horizontal on desktop)
    const stackResponsive = new FlexStack('#stack-responsive', {
        direction: { xs: 'vertical', md: 'horizontal' },
        gap: { xs: 2, md: 4 },
        align: 'center',
        items: [
            {
                content: `<div class="px-4 py-2 bg-purple-100 text-purple-800 rounded-md font-medium">
                    Mobile: Vertical
                </div>`
            },
            {
                content: `<div class="px-4 py-2 bg-blue-100 text-blue-800 rounded-md font-medium">
                    Desktop: Horizontal
                </div>`
            },
            {
                content: `<div class="px-4 py-2 bg-green-100 text-green-800 rounded-md font-medium">
                    Resize to see!
                </div>`
            }
        ]
    });

    stacks = { stackHorizontal, stackVertical, stackDividers, stackResponsive };

    // FlexGrid Examples

    // 1. Basic Responsive Grid
    const gridBasic = new FlexGrid('#grid-basic', {
        columns: { xs: 1, sm: 2, md: 3, lg: 4 },
        gap: 4,
        items: Array.from({ length: 8 }, (_, i) => ({
            id: `grid-item-${i}`,
            content: `<div class="p-6 bg-gradient-to-br from-blue-50 to-blue-100 border border-blue-200 rounded-lg text-center">
                <div class="text-3xl font-bold text-blue-600">${i + 1}</div>
                <div class="text-sm text-blue-700 mt-1">Grid Item</div>
            </div>`
        }))
    });

    // 2. Grid with Column Spans
    const gridSpans = new FlexGrid('#grid-spans', {
        columns: { xs: 1, sm: 2, md: 4 },
        gap: 4,
        items: [
            {
                id: 'span-1',
                span: { xs: 1, md: 2 },
                content: `<div class="p-6 bg-gradient-to-br from-purple-50 to-purple-100 border border-purple-200 rounded-lg">
                    <div class="text-lg font-semibold text-purple-900">Span 2 Columns</div>
                    <div class="text-sm text-purple-700 mt-1">Takes up 2 columns on desktop</div>
                </div>`
            },
            {
                id: 'span-2',
                span: 1,
                content: `<div class="p-6 bg-gradient-to-br from-green-50 to-green-100 border border-green-200 rounded-lg text-center">
                    <div class="text-lg font-semibold text-green-900">1 Col</div>
                </div>`
            },
            {
                id: 'span-3',
                span: 1,
                content: `<div class="p-6 bg-gradient-to-br from-green-50 to-green-100 border border-green-200 rounded-lg text-center">
                    <div class="text-lg font-semibold text-green-900">1 Col</div>
                </div>`
            },
            {
                id: 'span-4',
                span: { xs: 1, md: 4 },
                content: `<div class="p-6 bg-gradient-to-br from-orange-50 to-orange-100 border border-orange-200 rounded-lg">
                    <div class="text-lg font-semibold text-orange-900">Full Width (Span 4)</div>
                    <div class="text-sm text-orange-700 mt-1">Takes up all 4 columns</div>
                </div>`
            }
        ]
    });

    // 3. Dashboard Grid Example
    const gridDashboard = new FlexGrid('#grid-dashboard', {
        columns: { xs: 1, md: 2, lg: 4 },
        gap: 6,
        items: [
            {
                id: 'stats',
                span: { xs: 1, lg: 4 },
                content: `<div class="p-6 bg-white border border-gray-200 rounded-lg shadow-sm">
                    <h3 class="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                        <i class="ph-duotone ph-chart-line text-blue-600"></i>
                        Statistics Overview
                    </h3>
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div class="text-center">
                            <div class="text-3xl font-bold text-blue-600">1.2K</div>
                            <div class="text-sm text-gray-600">Total Users</div>
                        </div>
                        <div class="text-center">
                            <div class="text-3xl font-bold text-green-600">$45K</div>
                            <div class="text-sm text-gray-600">Revenue</div>
                        </div>
                        <div class="text-center">
                            <div class="text-3xl font-bold text-purple-600">89%</div>
                            <div class="text-sm text-gray-600">Satisfaction</div>
                        </div>
                        <div class="text-center">
                            <div class="text-3xl font-bold text-orange-600">+12%</div>
                            <div class="text-sm text-gray-600">Growth</div>
                        </div>
                    </div>
                </div>`
            },
            {
                id: 'recent',
                span: { xs: 1, md: 2, lg: 2 },
                content: `<div class="p-6 bg-white border border-gray-200 rounded-lg shadow-sm">
                    <h3 class="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                        <i class="ph ph-clock text-indigo-600"></i>
                        Recent Activity
                    </h3>
                    <div class="space-y-3">
                        <div class="text-sm text-gray-700">User logged in</div>
                        <div class="text-sm text-gray-700">New order placed</div>
                        <div class="text-sm text-gray-700">Report generated</div>
                    </div>
                </div>`
            },
            {
                id: 'quick',
                span: { xs: 1, md: 2, lg: 2 },
                content: `<div class="p-6 bg-white border border-gray-200 rounded-lg shadow-sm">
                    <h3 class="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                        <i class="ph-duotone ph-lightning text-yellow-600"></i>
                        Quick Actions
                    </h3>
                    <div class="space-y-2">
                        <button class="w-full px-3 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 text-sm">
                            <i class="ph ph-plus"></i> New User
                        </button>
                        <button class="w-full px-3 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 text-sm">
                            <i class="ph ph-download"></i> Export Data
                        </button>
                    </div>
                </div>`
            }
        ]
    });

    grids = { gridBasic, gridSpans, gridDashboard };

    // Combined Layout Example
    initCombinedLayoutExample();
}

/**
 * Initialize combined layout example
 */
function initCombinedLayoutExample() {
    const combinedGrid = new FlexGrid('#layout-combined', {
        columns: { xs: 1, md: 2, lg: 3 },
        gap: 6,
        items: [
            {
                id: 'combined-1',
                span: { xs: 1, lg: 2 },
                content: (() => {
                    const card = new FlexCard(document.createElement('div'), {
                        title: 'Team Members',
                        icon: 'ph ph-users',
                        badge: { text: '4 Online', variant: 'success' },
                        content: (() => {
                            const stack = new FlexStack(document.createElement('div'), {
                                direction: 'vertical',
                                gap: 3,
                                items: [
                                    {
                                        content: `<div class="flex items-center gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                                            <div class="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white font-semibold">JD</div>
                                            <div class="flex-1">
                                                <div class="font-medium text-gray-900">John Doe</div>
                                                <div class="text-sm text-gray-500">john@example.com</div>
                                            </div>
                                            <span class="w-2 h-2 bg-green-500 rounded-full"></span>
                                        </div>`
                                    },
                                    {
                                        content: `<div class="flex items-center gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                                            <div class="w-10 h-10 bg-purple-500 rounded-full flex items-center justify-center text-white font-semibold">JS</div>
                                            <div class="flex-1">
                                                <div class="font-medium text-gray-900">Jane Smith</div>
                                                <div class="text-sm text-gray-500">jane@example.com</div>
                                            </div>
                                            <span class="w-2 h-2 bg-green-500 rounded-full"></span>
                                        </div>`
                                    },
                                    {
                                        content: `<div class="flex items-center gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                                            <div class="w-10 h-10 bg-green-500 rounded-full flex items-center justify-center text-white font-semibold">BJ</div>
                                            <div class="flex-1">
                                                <div class="font-medium text-gray-900">Bob Johnson</div>
                                                <div class="text-sm text-gray-500">bob@example.com</div>
                                            </div>
                                            <span class="w-2 h-2 bg-gray-400 rounded-full"></span>
                                        </div>`
                                    }
                                ]
                            });
                            return stack.getElement();
                        })()
                    });
                    return card.getElement();
                })()
            },
            {
                id: 'combined-2',
                span: 1,
                content: (() => {
                    const card = new FlexCard(document.createElement('div'), {
                        title: 'Quick Stats',
                        icon: 'ph-duotone ph-chart-bar',
                        variant: 'shadowed',
                        content: (() => {
                            const stack = new FlexStack(document.createElement('div'), {
                                direction: 'vertical',
                                gap: 4,
                                divider: { enabled: true },
                                items: [
                                    {
                                        content: `<div class="text-center">
                                            <div class="text-3xl font-bold text-blue-600">245</div>
                                            <div class="text-sm text-gray-600">Total Projects</div>
                                        </div>`
                                    },
                                    {
                                        content: `<div class="text-center">
                                            <div class="text-3xl font-bold text-green-600">89%</div>
                                            <div class="text-sm text-gray-600">Completion Rate</div>
                                        </div>`
                                    },
                                    {
                                        content: `<div class="text-center">
                                            <div class="text-3xl font-bold text-purple-600">12</div>
                                            <div class="text-sm text-gray-600">Active Tasks</div>
                                        </div>`
                                    }
                                ]
                            });
                            return stack.getElement();
                        })()
                    });
                    return card.getElement();
                })()
            }
        ]
    });
}

/**
 * Initialize FlexCard examples
 */
function initCardExamples() {
    // Basic Card
    cards.basic = new FlexCard('#card-basic', {
        title: 'Basic Card',
        subtitle: 'A simple card with title and subtitle',
        icon: 'ph ph-article',
        content: '<p class="text-gray-700">This is a basic card component with minimal configuration. Perfect for displaying simple content blocks.</p>'
    });

    // Card with Actions
    cards.actions = new FlexCard('#card-actions', {
        title: 'User Profile',
        subtitle: 'John Doe',
        icon: 'ph ph-user-circle',
        content: `
            <div class="space-y-2 text-sm">
                <div class="flex justify-between">
                    <span class="text-gray-600">Email:</span>
                    <span class="text-gray-900 font-medium">john.doe@example.com</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-gray-600">Role:</span>
                    <span class="text-gray-900 font-medium">Administrator</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-gray-600">Status:</span>
                    <span class="text-green-600 font-medium">Active</span>
                </div>
            </div>
        `,
        actions: [
            {
                icon: 'ph ph-pencil',
                variant: 'ghost',
                onClick: () => showToast('Edit action clicked!', 'info')
            },
            {
                icon: 'ph ph-trash',
                variant: 'ghost',
                onClick: () => showToast('Delete action clicked!', 'warning')
            }
        ]
    });

    // Card with Badge
    cards.badge = new FlexCard('#card-badge', {
        title: 'Premium Feature',
        icon: 'ph-fill ph-star',
        badge: { text: 'PRO', variant: 'warning' },
        content: '<p class="text-gray-700">This feature is available for premium users. Upgrade your plan to unlock advanced capabilities.</p>',
        variant: 'bordered'
    });

    // Collapsible Card
    cards.collapsible = new FlexCard('#card-collapsible', {
        title: 'Collapsible Content',
        subtitle: 'Click the chevron to toggle',
        icon: 'ph ph-caret-down',
        collapsible: true,
        collapsed: false,
        content: `
            <p class="text-gray-700 mb-3">This card can be collapsed to save space. Great for:</p>
            <ul class="list-disc list-inside space-y-1 text-sm text-gray-600">
                <li>FAQ sections</li>
                <li>Form sections</li>
                <li>Hierarchical data</li>
                <li>Settings groups</li>
            </ul>
        `,
        onCollapse: () => showToast('Card collapsed', 'info'),
        onExpand: () => showToast('Card expanded', 'info')
    });

    // Card with Footer
    cards.footer = new FlexCard('#card-footer', {
        title: 'Task Assignment',
        icon: 'ph ph-clipboard-text',
        content: `
            <div class="space-y-3">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Task Name</label>
                    <input type="text" class="w-full px-3 py-2 border border-gray-300 rounded-md" placeholder="Enter task name" />
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Assigned To</label>
                    <select class="w-full px-3 py-2 border border-gray-300 rounded-md">
                        <option>Select user...</option>
                        <option>John Doe</option>
                        <option>Jane Smith</option>
                    </select>
                </div>
            </div>
        `,
        footerActions: [
            {
                label: 'Cancel',
                variant: 'ghost',
                onClick: () => showToast('Cancelled', 'info')
            },
            {
                label: 'Assign Task',
                variant: 'primary',
                icon: 'ph ph-check',
                onClick: () => showToast('Task assigned successfully!', 'success')
            }
        ]
    });

    // Shadowed Card
    cards.shadowed = new FlexCard('#card-shadowed', {
        title: 'Elevated Card',
        subtitle: 'With shadow effect',
        icon: 'ph ph-package',
        variant: 'shadowed',
        content: '<p class="text-gray-700">This card uses the shadowed variant for a more prominent, elevated appearance.</p>'
    });

    // Loading Card
    cards.loading = new FlexCard('#card-loading', {
        title: 'Data Dashboard',
        subtitle: 'Real-time metrics',
        icon: 'ph ph-chart-bar',
        content: `
            <div class="space-y-4">
                <div class="flex justify-between items-center">
                    <span class="text-gray-600">Total Users:</span>
                    <span class="text-2xl font-bold text-blue-600">1,234</span>
                </div>
                <div class="flex justify-between items-center">
                    <span class="text-gray-600">Active Sessions:</span>
                    <span class="text-2xl font-bold text-green-600">89</span>
                </div>
                <div class="flex justify-between items-center">
                    <span class="text-gray-600">Revenue (MTD):</span>
                    <span class="text-2xl font-bold text-purple-600">$45.2K</span>
                </div>
            </div>
        `,
        actions: [
            {
                icon: 'ph ph-arrows-clockwise',
                variant: 'ghost',
                onClick: () => {
                    cards.loading.setLoading(true);
                    setTimeout(() => {
                        cards.loading.setLoading(false);
                        showToast('Data refreshed!', 'success');
                    }, 1500);
                }
            }
        ]
    });

    // Loading toggle button
    const toggleBtn = document.getElementById('toggle-loading');
    if (toggleBtn) {
        let isLoading = false;
        toggleBtn.onclick = () => {
            isLoading = !isLoading;
            cards.loading.setLoading(isLoading);
            toggleBtn.textContent = isLoading ? 'Stop Loading' : 'Start Loading';
        };
    }
}

/**
 * Initialize FlexModal examples
 */
function initModalExamples() {
    // Basic Modal
    modals.basic = new FlexModal({
        title: 'Basic Modal',
        subtitle: 'A simple modal dialog',
        icon: 'ph ph-info',
        content: `
            <p class="text-gray-700 mb-4">This is a basic modal with a title, subtitle, and content. You can close it by:</p>
            <ul class="list-disc list-inside space-y-2 text-sm text-gray-600">
                <li>Clicking the X button</li>
                <li>Pressing ESC key</li>
                <li>Clicking outside the modal</li>
                <li>Clicking the Close button</li>
            </ul>
        `,
        footerActions: [
            {
                label: 'Close',
                variant: 'ghost',
                onClick: (e, modal) => modal.hide()
            }
        ]
    });

    document.getElementById('modal-basic-btn')?.addEventListener('click', () => {
        modals.basic.show();
    });

    // Form Modal
    modals.form = new FlexModal({
        title: 'Create New User',
        subtitle: 'Enter user details below',
        icon: 'ph ph-user-plus',
        size: 'md',
        content: `
            <form id="user-form" class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                    <input type="text" name="name" class="w-full px-3 py-2 border border-gray-300 rounded-md" placeholder="John Doe" required />
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
                    <input type="email" name="email" class="w-full px-3 py-2 border border-gray-300 rounded-md" placeholder="john@example.com" required />
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Role</label>
                    <select name="role" class="w-full px-3 py-2 border border-gray-300 rounded-md">
                        <option>User</option>
                        <option>Admin</option>
                        <option>Manager</option>
                    </select>
                </div>
                <div>
                    <label class="flex items-center gap-2">
                        <input type="checkbox" name="active" class="rounded" checked />
                        <span class="text-sm text-gray-700">Active user</span>
                    </label>
                </div>
            </form>
        `,
        footerActions: [
            {
                label: 'Cancel',
                variant: 'ghost',
                onClick: (e, modal) => modal.hide()
            },
            {
                label: 'Create User',
                variant: 'primary',
                icon: 'ph ph-check',
                onClick: (e, modal) => {
                    showToast('User created successfully!', 'success');
                    modal.hide();
                }
            }
        ]
    });

    document.getElementById('modal-form-btn')?.addEventListener('click', () => {
        modals.form.show();
    });

    // Confirmation Modal
    modals.confirm = new FlexModal({
        title: 'Delete Confirmation',
        icon: 'ph ph-warning',
        size: 'sm',
        content: `
            <div class="text-center py-4">
                <div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 mb-4">
                    <i class="ph-fill ph-trash text-red-600 text-xl"></i>
                </div>
                <p class="text-gray-700 mb-2">Are you sure you want to delete this item?</p>
                <p class="text-sm text-gray-500">This action cannot be undone.</p>
            </div>
        `,
        footerActions: [
            {
                label: 'Cancel',
                variant: 'ghost',
                onClick: (e, modal) => modal.hide()
            },
            {
                label: 'Delete',
                variant: 'danger',
                icon: 'ph ph-trash',
                onClick: (e, modal) => {
                    showToast('Item deleted', 'success');
                    modal.hide();
                }
            }
        ]
    });

    document.getElementById('modal-confirm-btn')?.addEventListener('click', () => {
        modals.confirm.show();
    });

    // Large Modal
    modals.large = new FlexModal({
        title: 'Large Modal Example',
        subtitle: 'With more content space',
        icon: 'ph ph-app-window',
        size: 'xl',
        content: `
            <div class="prose max-w-none">
                <h3 class="text-lg font-semibold text-gray-900 mb-3">Features of Large Modals</h3>
                <p class="text-gray-700 mb-4">Large modals are perfect for displaying detailed information or complex forms. They provide ample space for:</p>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <div class="p-4 bg-blue-50 rounded-lg">
                        <h4 class="font-semibold text-blue-900 mb-2">Rich Content</h4>
                        <p class="text-sm text-blue-800">Display detailed information, images, charts, and multimedia content.</p>
                    </div>
                    <div class="p-4 bg-green-50 rounded-lg">
                        <h4 class="font-semibold text-green-900 mb-2">Complex Forms</h4>
                        <p class="text-sm text-green-800">Multi-section forms with many fields and validation.</p>
                    </div>
                    <div class="p-4 bg-purple-50 rounded-lg">
                        <h4 class="font-semibold text-purple-900 mb-2">Data Tables</h4>
                        <p class="text-sm text-purple-800">Display tabular data with multiple columns.</p>
                    </div>
                    <div class="p-4 bg-yellow-50 rounded-lg">
                        <h4 class="font-semibold text-yellow-900 mb-2">Wizards</h4>
                        <p class="text-sm text-yellow-800">Multi-step processes and guided workflows.</p>
                    </div>
                </div>
            </div>
        `,
        footerActions: [
            {
                label: 'Got it',
                variant: 'primary',
                onClick: (e, modal) => modal.hide()
            }
        ]
    });

    document.getElementById('modal-large-btn')?.addEventListener('click', () => {
        modals.large.show();
    });

    // Scrollable Modal
    modals.scrollable = new FlexModal({
        title: 'Scrollable Content',
        subtitle: 'Long content with scroll',
        size: 'lg',
        content: `
            <div class="space-y-4">
                ${Array.from({ length: 20 }, (_, i) => `
                    <div class="p-4 bg-gray-50 rounded-lg">
                        <h4 class="font-semibold text-gray-900 mb-2">Section ${i + 1}</h4>
                        <p class="text-sm text-gray-600">Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>
                    </div>
                `).join('')}
            </div>
        `,
        footerActions: [
            {
                label: 'Close',
                variant: 'ghost',
                onClick: (e, modal) => modal.hide()
            }
        ]
    });

    document.getElementById('modal-scrollable-btn')?.addEventListener('click', () => {
        modals.scrollable.show();
    });

    // Nested Modal Demo
    modals.nested1 = new FlexModal({
        title: 'First Modal',
        content: '<p class="text-gray-700 mb-4">This demonstrates modal stacking. Click the button below to open a second modal on top of this one.</p>',
        footerActions: [
            {
                label: 'Open Second Modal',
                variant: 'primary',
                onClick: () => modals.nested2.show()
            },
            {
                label: 'Close',
                variant: 'ghost',
                onClick: (e, modal) => modal.hide()
            }
        ]
    });

    modals.nested2 = new FlexModal({
        title: 'Second Modal',
        size: 'sm',
        content: '<p class="text-gray-700">This modal is stacked on top of the first one. ESC will close only the topmost modal.</p>',
        footerActions: [
            {
                label: 'Close',
                variant: 'primary',
                onClick: (e, modal) => modal.hide()
            }
        ]
    });

    document.getElementById('modal-nested-btn')?.addEventListener('click', () => {
        modals.nested1.show();
    });
}

/**
 * Initialize FlexTabs examples
 */
function initTabsExamples() {
    // Underline Tabs
    tabs.underline = new FlexTabs('#tabs-underline', {
        variant: 'underline',
        tabs: [
            {
                id: 'home',
                label: 'Home',
                icon: 'ph ph-house',
                content: `
                    <div class="p-6 bg-white border border-gray-200 rounded-b-lg">
                        <h3 class="text-lg font-semibold text-gray-900 mb-3">Welcome Home</h3>
                        <p class="text-gray-700">This is the home tab content. Underline tabs are great for navigation-style interfaces.</p>
                    </div>
                `
            },
            {
                id: 'profile',
                label: 'Profile',
                icon: 'ph ph-user',
                content: `
                    <div class="p-6 bg-white border border-gray-200 rounded-b-lg">
                        <h3 class="text-lg font-semibold text-gray-900 mb-3">User Profile</h3>
                        <p class="text-gray-700">View and edit your profile information here.</p>
                    </div>
                `
            },
            {
                id: 'settings',
                label: 'Settings',
                icon: 'ph ph-gear',
                content: `
                    <div class="p-6 bg-white border border-gray-200 rounded-b-lg">
                        <h3 class="text-lg font-semibold text-gray-900 mb-3">Settings</h3>
                        <p class="text-gray-700">Configure your application preferences.</p>
                    </div>
                `
            }
        ]
    });

    // Pills Tabs
    tabs.pills = new FlexTabs('#tabs-pills', {
        variant: 'pills',
        tabs: [
            {
                id: 'overview',
                label: 'Overview',
                icon: 'ph ph-grid-four',
                content: `
                    <div class="p-6 bg-gray-50 rounded-lg mt-3">
                        <h3 class="text-lg font-semibold text-gray-900 mb-3">Dashboard Overview</h3>
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div class="bg-white p-4 rounded-lg shadow-sm">
                                <div class="text-3xl font-bold text-blue-600">245</div>
                                <div class="text-sm text-gray-600 mt-1">Total Users</div>
                            </div>
                            <div class="bg-white p-4 rounded-lg shadow-sm">
                                <div class="text-3xl font-bold text-green-600">89%</div>
                                <div class="text-sm text-gray-600 mt-1">Completion Rate</div>
                            </div>
                            <div class="bg-white p-4 rounded-lg shadow-sm">
                                <div class="text-3xl font-bold text-purple-600">$12.4K</div>
                                <div class="text-sm text-gray-600 mt-1">Revenue</div>
                            </div>
                        </div>
                    </div>
                `
            },
            {
                id: 'analytics',
                label: 'Analytics',
                icon: 'ph ph-chart-line-up',
                content: `
                    <div class="p-6 bg-gray-50 rounded-lg mt-3">
                        <h3 class="text-lg font-semibold text-gray-900 mb-3">Analytics Dashboard</h3>
                        <p class="text-gray-700">Charts and graphs would go here.</p>
                    </div>
                `
            },
            {
                id: 'reports',
                label: 'Reports',
                icon: 'ph ph-file-text',
                content: `
                    <div class="p-6 bg-gray-50 rounded-lg mt-3">
                        <h3 class="text-lg font-semibold text-gray-900 mb-3">Reports</h3>
                        <p class="text-gray-700">Generate and view reports.</p>
                    </div>
                `
            }
        ]
    });

    // Enclosed Tabs
    tabs.enclosed = new FlexTabs('#tabs-enclosed', {
        variant: 'enclosed',
        tabs: [
            {
                id: 'code',
                label: 'Code',
                icon: 'ph ph-code',
                content: `
                    <div class="p-6 bg-white border-l border-r border-b border-gray-200 rounded-b-lg">
                        <pre class="bg-gray-800 text-gray-100 p-4 rounded overflow-x-auto"><code>function greet(name) {
  return \`Hello, \${name}!\`;
}

console.log(greet('World'));</code></pre>
                    </div>
                `
            },
            {
                id: 'preview',
                label: 'Preview',
                icon: 'ph ph-eye',
                content: `
                    <div class="p-6 bg-white border-l border-r border-b border-gray-200 rounded-b-lg">
                        <div class="text-center py-8">
                            <div class="text-4xl mb-2">👋</div>
                            <div class="text-2xl font-bold text-gray-900">Hello, World!</div>
                        </div>
                    </div>
                `
            },
            {
                id: 'docs',
                label: 'Documentation',
                icon: 'ph ph-book',
                content: `
                    <div class="p-6 bg-white border-l border-r border-b border-gray-200 rounded-b-lg">
                        <h3 class="text-lg font-semibold text-gray-900 mb-3">Function Documentation</h3>
                        <p class="text-gray-700">The greet() function returns a greeting message.</p>
                    </div>
                `
            }
        ]
    });

    // Tabs with Badges
    tabs.badges = new FlexTabs('#tabs-badges', {
        variant: 'pills',
        tabs: [
            {
                id: 'all',
                label: 'All',
                badge: { text: '142', variant: 'default' },
                content: `
                    <div class="p-6 bg-gray-50 rounded-lg mt-3">
                        <p class="text-gray-700">Showing all 142 items</p>
                    </div>
                `
            },
            {
                id: 'active',
                label: 'Active',
                badge: { text: '89', variant: 'success' },
                content: `
                    <div class="p-6 bg-gray-50 rounded-lg mt-3">
                        <p class="text-gray-700">Showing 89 active items</p>
                    </div>
                `
            },
            {
                id: 'pending',
                label: 'Pending',
                badge: { text: '23', variant: 'warning' },
                content: `
                    <div class="p-6 bg-gray-50 rounded-lg mt-3">
                        <p class="text-gray-700">Showing 23 pending items</p>
                    </div>
                `
            },
            {
                id: 'archived',
                label: 'Archived',
                badge: { text: '30', variant: 'info' },
                content: `
                    <div class="p-6 bg-gray-50 rounded-lg mt-3">
                        <p class="text-gray-700">Showing 30 archived items</p>
                    </div>
                `
            }
        ]
    });

    // Vertical Tabs
    tabs.vertical = new FlexTabs('#tabs-vertical', {
        variant: 'pills',
        orientation: 'vertical',
        tabs: [
            {
                id: 'general',
                label: 'General',
                icon: 'ph ph-sliders',
                content: `
                    <div class="p-6 bg-white border border-gray-200 rounded-lg">
                        <h3 class="text-lg font-semibold text-gray-900 mb-4">General Settings</h3>
                        <div class="space-y-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-1">Application Name</label>
                                <input type="text" class="w-full px-3 py-2 border border-gray-300 rounded-md" value="My Application" />
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-1">Language</label>
                                <select class="w-full px-3 py-2 border border-gray-300 rounded-md">
                                    <option>English</option>
                                    <option>Spanish</option>
                                    <option>French</option>
                                </select>
                            </div>
                        </div>
                    </div>
                `
            },
            {
                id: 'security',
                label: 'Security',
                icon: 'ph ph-shield-check',
                content: `
                    <div class="p-6 bg-white border border-gray-200 rounded-lg">
                        <h3 class="text-lg font-semibold text-gray-900 mb-4">Security Settings</h3>
                        <div class="space-y-3">
                            <label class="flex items-center gap-2">
                                <input type="checkbox" class="rounded" checked />
                                <span class="text-sm text-gray-700">Enable two-factor authentication</span>
                            </label>
                            <label class="flex items-center gap-2">
                                <input type="checkbox" class="rounded" />
                                <span class="text-sm text-gray-700">Require password change every 90 days</span>
                            </label>
                            <label class="flex items-center gap-2">
                                <input type="checkbox" class="rounded" checked />
                                <span class="text-sm text-gray-700">Enable session timeout</span>
                            </label>
                        </div>
                    </div>
                `
            },
            {
                id: 'notifications',
                label: 'Notifications',
                icon: 'ph ph-bell',
                content: `
                    <div class="p-6 bg-white border border-gray-200 rounded-lg">
                        <h3 class="text-lg font-semibold text-gray-900 mb-4">Notification Preferences</h3>
                        <div class="space-y-3">
                            <label class="flex items-center gap-2">
                                <input type="checkbox" class="rounded" checked />
                                <span class="text-sm text-gray-700">Email notifications</span>
                            </label>
                            <label class="flex items-center gap-2">
                                <input type="checkbox" class="rounded" checked />
                                <span class="text-sm text-gray-700">Push notifications</span>
                            </label>
                            <label class="flex items-center gap-2">
                                <input type="checkbox" class="rounded" />
                                <span class="text-sm text-gray-700">SMS notifications</span>
                            </label>
                        </div>
                    </div>
                `
            },
            {
                id: 'privacy',
                label: 'Privacy',
                icon: 'ph ph-eye-slash',
                content: `
                    <div class="p-6 bg-white border border-gray-200 rounded-lg">
                        <h3 class="text-lg font-semibold text-gray-900 mb-4">Privacy Settings</h3>
                        <p class="text-gray-700 mb-4">Control who can see your information</p>
                        <div class="space-y-3">
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-1">Profile Visibility</label>
                                <select class="w-full px-3 py-2 border border-gray-300 rounded-md">
                                    <option>Public</option>
                                    <option>Friends Only</option>
                                    <option>Private</option>
                                </select>
                            </div>
                        </div>
                    </div>
                `
            }
        ]
    });
}

/**
 * Initialize combined example
 */
function initCombinedExample() {
    // Create a card with tabs inside
    const combinedCard = new FlexCard('#combined-example', {
        title: 'User Management Dashboard',
        subtitle: 'Combining Card and Tabs components',
        icon: 'ph ph-users',
        badge: { text: 'Live', variant: 'success' },
        actions: [
            {
                label: 'Add User',
                icon: 'ph ph-user-plus',
                variant: 'primary',
                onClick: () => {
                    const modal = new FlexModal({
                        title: 'Add New User',
                        icon: 'ph ph-user-plus',
                        size: 'md',
                        content: `
                            <div class="space-y-4">
                                <div>
                                    <label class="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                                    <input type="text" class="w-full px-3 py-2 border border-gray-300 rounded-md" placeholder="Enter name" />
                                </div>
                                <div>
                                    <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
                                    <input type="email" class="w-full px-3 py-2 border border-gray-300 rounded-md" placeholder="Enter email" />
                                </div>
                                <div>
                                    <label class="block text-sm font-medium text-gray-700 mb-1">Role</label>
                                    <select class="w-full px-3 py-2 border border-gray-300 rounded-md">
                                        <option>User</option>
                                        <option>Admin</option>
                                        <option>Manager</option>
                                    </select>
                                </div>
                            </div>
                        `,
                        footerActions: [
                            {
                                label: 'Cancel',
                                variant: 'ghost',
                                onClick: (e, m) => m.hide()
                            },
                            {
                                label: 'Add User',
                                variant: 'primary',
                                onClick: (e, m) => {
                                    showToast('User added successfully!', 'success');
                                    m.hide();
                                }
                            }
                        ]
                    });
                    modal.show();
                }
            },
            {
                icon: 'ph ph-arrows-clockwise',
                variant: 'ghost',
                onClick: () => showToast('Refreshed!', 'info')
            }
        ],
        variant: 'shadowed'
    });

    // Create tabs inside the card body
    setTimeout(() => {
        const cardBody = combinedCard.getBodyElement();
        const tabsContainer = document.createElement('div');
        cardBody.appendChild(tabsContainer);

        new FlexTabs(tabsContainer, {
            variant: 'underline',
            tabs: [
                {
                    id: 'users-list',
                    label: 'All Users',
                    icon: 'ph ph-users',
                    badge: '48',
                    content: `
                        <div class="py-4">
                            <div class="space-y-2">
                                ${['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Williams'].map(name => `
                                    <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                                        <div class="flex items-center gap-3">
                                            <div class="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white font-semibold">
                                                ${name.split(' ').map(n => n[0]).join('')}
                                            </div>
                                            <div>
                                                <div class="font-medium text-gray-900">${name}</div>
                                                <div class="text-sm text-gray-500">${name.toLowerCase().replace(' ', '.')}@example.com</div>
                                            </div>
                                        </div>
                                        <span class="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">Active</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    `
                },
                {
                    id: 'admins',
                    label: 'Admins',
                    icon: 'ph ph-shield-check',
                    badge: { text: '5', variant: 'warning' },
                    content: `
                        <div class="py-4">
                            <p class="text-gray-700">Showing 5 admin users with elevated privileges.</p>
                        </div>
                    `
                },
                {
                    id: 'activity',
                    label: 'Activity',
                    icon: 'ph ph-activity',
                    content: `
                        <div class="py-4">
                            <div class="space-y-3">
                                <div class="flex gap-3 text-sm">
                                    <span class="text-gray-500">2 min ago</span>
                                    <span class="text-gray-700">John Doe logged in</span>
                                </div>
                                <div class="flex gap-3 text-sm">
                                    <span class="text-gray-500">15 min ago</span>
                                    <span class="text-gray-700">Jane Smith updated profile</span>
                                </div>
                                <div class="flex gap-3 text-sm">
                                    <span class="text-gray-500">1 hour ago</span>
                                    <span class="text-gray-700">New user registered</span>
                                </div>
                            </div>
                        </div>
                    `
                }
            ]
        });
    }, 100);
}

/**
 * Initialize Phase 2 Container Examples
 */
function initPhase2ContainerExamples() {
    console.log('Initializing Phase 2 Container Examples...');

    // Example 1: Preset Comparison
    const presetsContainer = document.querySelector('#container-presets');
    if (presetsContainer) {
        presetsContainer.innerHTML = `
            <div class="space-y-4">
                ${['narrow', 'standard', 'wide', 'full'].map(preset => `
                    <div class="bg-white border border-gray-200 rounded-lg overflow-hidden">
                        <div class="bg-gray-100 px-4 py-2 border-b border-gray-200">
                            <code class="text-sm font-semibold text-gray-700">preset: "${preset}"</code>
                        </div>
                        <div id="container-preset-${preset}" class="p-4 bg-gradient-to-r from-blue-50 to-indigo-50">
                            <div class="bg-white border-2 border-dashed border-indigo-300 rounded p-4 text-center">
                                <p class="text-gray-700">Content within ${preset} container</p>
                                <p class="text-xs text-gray-500 mt-1">Max-width: ${
                                    preset === 'narrow' ? '768px' :
                                    preset === 'standard' ? '1280px' :
                                    preset === 'wide' ? '1536px' :
                                    '100%'
                                }</p>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;

        // Initialize containers
        ['narrow', 'standard', 'wide', 'full'].forEach(preset => {
            containers[`preset-${preset}`] = new FlexContainer(`#container-preset-${preset}`, {
                preset: preset,
                align: 'center',
                gutter: true
            });
        });
    }

    // Example 2: Responsive Gutters
    const guttersContainer = document.querySelector('#container-gutters');
    if (guttersContainer) {
        guttersContainer.innerHTML = `
            <div class="bg-white border border-gray-200 rounded-lg overflow-hidden">
                <div class="bg-gray-100 px-4 py-2 border-b border-gray-200">
                    <code class="text-sm font-semibold text-gray-700">gutter: { xs: 4, md: 6, lg: 8 }</code>
                </div>
                <div id="container-gutters-demo" class="bg-gradient-to-r from-purple-50 to-pink-50 p-1">
                    <div class="bg-white border-2 border-dashed border-purple-300 rounded p-6">
                        <p class="text-gray-700">Resize your browser to see responsive gutters</p>
                        <p class="text-sm text-gray-500 mt-2">Mobile: 1rem • Tablet: 1.5rem • Desktop: 2rem</p>
                    </div>
                </div>
            </div>
        `;

        containers['gutters'] = new FlexContainer('#container-gutters-demo', {
            preset: 'standard',
            padding: { xs: 4, md: 6, lg: 8 },
            align: 'center'
        });
    }

    // Example 3: Alignment Variations
    const alignmentContainer = document.querySelector('#container-alignment');
    if (alignmentContainer) {
        alignmentContainer.innerHTML = `
            <div class="space-y-4">
                ${['left', 'center', 'right'].map(align => `
                    <div class="bg-white border border-gray-200 rounded-lg overflow-hidden">
                        <div class="bg-gray-100 px-4 py-2 border-b border-gray-200">
                            <code class="text-sm font-semibold text-gray-700">align: "${align}"</code>
                        </div>
                        <div id="container-align-${align}" class="p-4 bg-gradient-to-r from-green-50 to-teal-50">
                            <div class="bg-white border-2 border-dashed border-green-300 rounded p-4">
                                <p class="text-gray-700">${align.charAt(0).toUpperCase() + align.slice(1)}-aligned content</p>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;

        ['left', 'center', 'right'].forEach(align => {
            containers[`align-${align}`] = new FlexContainer(`#container-align-${align}`, {
                preset: 'narrow',
                align: align,
                gutter: false
            });
        });
    }

    // Example 4: Breakout Demo
    const breakoutContainer = document.querySelector('#container-breakout');
    if (breakoutContainer) {
        breakoutContainer.innerHTML = `
            <div class="bg-white border border-gray-200 rounded-lg overflow-hidden">
                <div class="bg-gray-100 px-4 py-2 border-b border-gray-200">
                    <code class="text-sm font-semibold text-gray-700">allowBreakout: true</code>
                </div>
                <div id="container-breakout-demo" class="p-4 bg-gradient-to-r from-amber-50 to-orange-50">
                    <div class="space-y-4">
                        <div class="bg-white border border-amber-300 rounded p-4">
                            <p class="text-gray-700">Contained content (respects max-width)</p>
                        </div>
                        <div class="bg-indigo-600 text-white p-6 rounded -mx-4">
                            <p class="font-semibold">Full-width breakout content</p>
                            <p class="text-sm text-indigo-100 mt-1">This escapes the container width constraints</p>
                        </div>
                        <div class="bg-white border border-amber-300 rounded p-4">
                            <p class="text-gray-700">Back to contained content</p>
                        </div>
                    </div>
                </div>
            </div>
        `;

        containers['breakout'] = new FlexContainer('#container-breakout-demo', {
            preset: 'narrow',
            allowBreakout: true,
            gutter: true
        });
    }
}

/**
 * Initialize Phase 2 Section Examples
 */
function initPhase2SectionExamples() {
    console.log('Initializing Phase 2 Section Examples...');

    // Example 1: Hero Section
    const heroContainer = document.querySelector('#section-hero');
    if (heroContainer) {
        heroContainer.innerHTML = '<div id="section-hero-demo"></div>';

        setTimeout(() => {
            sections['hero'] = new FlexSection('#section-hero-demo', {
                variant: 'hero',
                padding: '2xl',
                background: {
                    type: 'gradient',
                    gradient: {
                        from: 'indigo-600',
                        to: 'purple-600',
                        direction: 'to-br'
                    }
                },
                slots: {
                    body: {
                        content: `
                            <div class="text-center text-white space-y-6">
                                <h1 class="text-4xl font-bold">Welcome to Phase 2</h1>
                                <p class="text-xl text-indigo-100">Advanced layout components for modern web applications</p>
                                <div class="flex gap-4 justify-center">
                                    <button class="px-6 py-3 bg-white text-indigo-600 font-semibold rounded-lg hover:bg-indigo-50 transition-colors">
                                        Get Started
                                    </button>
                                    <button class="px-6 py-3 border-2 border-white text-white font-semibold rounded-lg hover:bg-white hover:text-indigo-600 transition-colors">
                                        Learn More
                                    </button>
                                </div>
                            </div>
                        `,
                        align: 'center'
                    }
                }
            });
        }, 50);
    }

    // Example 2: Content Section
    const contentContainer = document.querySelector('#section-content');
    if (contentContainer) {
        contentContainer.innerHTML = '<div id="section-content-demo"></div>';

        setTimeout(() => {
            sections['content'] = new FlexSection('#section-content-demo', {
                variant: 'content',
                padding: 'xl',
                background: {
                    type: 'solid',
                    color: 'white'
                },
                divider: {
                    top: true,
                    bottom: true,
                    color: 'gray-200'
                },
                slots: {
                    header: {
                        content: '<h2 class="text-2xl font-bold text-gray-900">About Our Platform</h2>',
                        align: 'left'
                    },
                    body: {
                        content: `
                            <p class="text-gray-600 leading-relaxed">
                                FlexSection provides a powerful way to create semantic page sections with consistent spacing,
                                backgrounds, and content organization. Perfect for building landing pages, marketing sites,
                                and content-heavy applications.
                            </p>
                        `
                    }
                }
            });
        }, 50);
    }

    // Example 3: Feature Section
    const featureContainer = document.querySelector('#section-feature');
    if (featureContainer) {
        featureContainer.innerHTML = '<div id="section-feature-demo"></div>';

        setTimeout(() => {
            sections['feature'] = new FlexSection('#section-feature-demo', {
                variant: 'feature',
                padding: { xs: 'lg', lg: 'xl' },
                background: {
                    type: 'solid',
                    color: 'gray-900'
                },
                slots: {
                    header: {
                        content: '<h2 class="text-2xl font-bold text-white">Key Features</h2>',
                        align: 'center'
                    },
                    body: {
                        content: `
                            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
                                <div class="bg-white/10 backdrop-blur-sm rounded-lg p-6 text-white">
                                    <i class="ph-duotone ph-rocket text-4xl text-indigo-400 mb-3 block"></i>
                                    <h3 class="text-lg font-semibold mb-2">Fast Performance</h3>
                                    <p class="text-gray-300 text-sm">Optimized for speed and efficiency</p>
                                </div>
                                <div class="bg-white/10 backdrop-blur-sm rounded-lg p-6 text-white">
                                    <i class="ph-duotone ph-palette text-4xl text-purple-400 mb-3 block"></i>
                                    <h3 class="text-lg font-semibold mb-2">Beautiful Design</h3>
                                    <p class="text-gray-300 text-sm">Carefully crafted user experience</p>
                                </div>
                                <div class="bg-white/10 backdrop-blur-sm rounded-lg p-6 text-white">
                                    <i class="ph-duotone ph-shield-check text-4xl text-green-400 mb-3 block"></i>
                                    <h3 class="text-lg font-semibold mb-2">Secure & Reliable</h3>
                                    <p class="text-gray-300 text-sm">Built with security in mind</p>
                                </div>
                            </div>
                        `
                    }
                }
            });
        }, 50);
    }

    // Example 4: CTA Section
    const ctaContainer = document.querySelector('#section-cta');
    if (ctaContainer) {
        ctaContainer.innerHTML = '<div id="section-cta-demo"></div>';

        setTimeout(() => {
            sections['cta'] = new FlexSection('#section-cta-demo', {
                variant: 'cta',
                padding: 'lg',
                background: {
                    type: 'gradient',
                    gradient: {
                        from: 'green-400',
                        to: 'blue-500',
                        direction: 'to-r'
                    }
                },
                slots: {
                    body: {
                        content: `
                            <div class="flex flex-col md:flex-row items-center justify-between gap-6 text-white">
                                <div>
                                    <h3 class="text-2xl font-bold mb-2">Ready to get started?</h3>
                                    <p class="text-green-50">Join thousands of satisfied users today</p>
                                </div>
                                <button class="px-8 py-3 bg-white text-green-600 font-bold rounded-lg hover:bg-green-50 transition-colors whitespace-nowrap">
                                    Sign Up Free
                                </button>
                            </div>
                        `,
                        align: 'center'
                    }
                }
            });
        }, 50);
    }

    // Example 5: Solid Background
    const solidBgContainer = document.querySelector('#section-bg-solid');
    if (solidBgContainer) {
        solidBgContainer.innerHTML = '<div id="section-bg-solid-demo"></div>';

        setTimeout(() => {
            sections['bg-solid'] = new FlexSection('#section-bg-solid-demo', {
                variant: 'content',
                padding: 'md',
                background: {
                    type: 'solid',
                    color: 'blue-50'
                },
                slots: {
                    body: {
                        content: `
                            <div class="text-center">
                                <h4 class="font-semibold text-blue-900 mb-2">Solid Color</h4>
                                <p class="text-sm text-blue-700">bg-blue-50</p>
                            </div>
                        `
                    }
                }
            });
        }, 50);
    }

    // Example 6: Gradient Background
    const gradientBgContainer = document.querySelector('#section-bg-gradient');
    if (gradientBgContainer) {
        gradientBgContainer.innerHTML = '<div id="section-bg-gradient-demo"></div>';

        setTimeout(() => {
            sections['bg-gradient'] = new FlexSection('#section-bg-gradient-demo', {
                variant: 'content',
                padding: 'md',
                background: {
                    type: 'gradient',
                    gradient: {
                        from: 'pink-500',
                        via: 'purple-500',
                        to: 'indigo-500',
                        direction: 'to-r'
                    }
                },
                slots: {
                    body: {
                        content: `
                            <div class="text-center text-white">
                                <h4 class="font-semibold mb-2">Gradient</h4>
                                <p class="text-sm text-pink-100">pink → purple → indigo</p>
                            </div>
                        `
                    }
                }
            });
        }, 50);
    }
}

/**
 * Initialize Phase 2 Sidebar Examples
 */
function initPhase2SidebarExamples() {
    console.log('Initializing Phase 2 Sidebar Examples...');

    // Example 1: Basic Sidebar
    const basicContainer = document.querySelector('#sidebar-basic');
    if (basicContainer) {
        basicContainer.innerHTML = '<div id="sidebar-basic-demo" class="border border-gray-200 rounded-lg overflow-hidden" style="height: 400px;"></div>';

        setTimeout(() => {
            sidebars['basic'] = new FlexSidebar('#sidebar-basic-demo', {
                position: 'left',
                width: { xs: '100%', md: '240px' },
                collapsible: true,
                collapseBreakpoint: 'md',
                mobileMode: 'overlay',
                desktopMode: 'push',
                defaultOpen: { xs: false, md: true },
                backdrop: true,
                content: {
                    sidebar: `
                        <div class="bg-gray-900 text-white h-full p-4">
                            <h3 class="font-bold text-lg mb-4">Navigation</h3>
                            <nav class="space-y-2">
                                <a href="#" class="block px-3 py-2 rounded hover:bg-gray-800 transition-colors">
                                    <i class="ph ph-house mr-2"></i>Dashboard
                                </a>
                                <a href="#" class="block px-3 py-2 rounded hover:bg-gray-800 transition-colors">
                                    <i class="ph ph-user mr-2"></i>Profile
                                </a>
                                <a href="#" class="block px-3 py-2 rounded hover:bg-gray-800 transition-colors">
                                    <i class="ph ph-gear mr-2"></i>Settings
                                </a>
                            </nav>
                        </div>
                    `,
                    main: `
                        <div class="p-6 bg-gray-50 h-full">
                            <h2 class="text-xl font-bold text-gray-900 mb-4">Main Content</h2>
                            <p class="text-gray-600 mb-4">Click the button below to toggle the sidebar</p>
                            <button onclick="window.toggleBasicSidebar()" class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors">
                                <i class="ph ph-sidebar mr-2"></i>Toggle Sidebar
                            </button>
                        </div>
                    `
                }
            });

            // Make toggle function globally available
            window.toggleBasicSidebar = () => sidebars['basic'].toggle();
        }, 50);
    }

    // Example 2: Admin Dashboard
    const adminContainer = document.querySelector('#sidebar-admin');
    if (adminContainer) {
        adminContainer.innerHTML = '<div id="sidebar-admin-demo" class="border border-gray-200 rounded-lg overflow-hidden" style="height: 500px;"></div>';

        setTimeout(() => {
            sidebars['admin'] = new FlexSidebar('#sidebar-admin-demo', {
                position: 'left',
                width: { md: '280px' },
                minWidth: '240px',
                maxWidth: '400px',
                resizable: true,
                sticky: false,
                collapsible: true,
                mobileMode: 'overlay',
                desktopMode: 'push',
                defaultOpen: { xs: false, md: true },
                content: {
                    sidebar: `
                        <div class="bg-indigo-900 text-white h-full">
                            <div class="p-4 border-b border-indigo-800">
                                <h3 class="font-bold text-lg">Admin Panel</h3>
                                <p class="text-xs text-indigo-300 mt-1">Resizable sidebar</p>
                            </div>
                            <nav class="p-4 space-y-1">
                                <a href="#" class="flex items-center gap-3 px-3 py-2 rounded bg-indigo-800 text-white">
                                    <i class="ph ph-gauge"></i>
                                    <span>Dashboard</span>
                                </a>
                                <a href="#" class="flex items-center gap-3 px-3 py-2 rounded hover:bg-indigo-800 transition-colors">
                                    <i class="ph ph-users"></i>
                                    <span>Users</span>
                                </a>
                                <a href="#" class="flex items-center gap-3 px-3 py-2 rounded hover:bg-indigo-800 transition-colors">
                                    <i class="ph ph-chart-bar"></i>
                                    <span>Analytics</span>
                                </a>
                                <a href="#" class="flex items-center gap-3 px-3 py-2 rounded hover:bg-indigo-800 transition-colors">
                                    <i class="ph ph-gear"></i>
                                    <span>Settings</span>
                                </a>
                            </nav>
                        </div>
                    `,
                    main: `
                        <div class="p-6 bg-gray-50 h-full overflow-y-auto">
                            <div class="mb-6">
                                <h2 class="text-2xl font-bold text-gray-900 mb-2">Dashboard Overview</h2>
                                <p class="text-gray-600">Drag the sidebar edge to resize</p>
                            </div>
                            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div class="bg-white rounded-lg p-4 border border-gray-200">
                                    <p class="text-sm text-gray-500">Total Users</p>
                                    <p class="text-2xl font-bold text-gray-900 mt-1">1,234</p>
                                </div>
                                <div class="bg-white rounded-lg p-4 border border-gray-200">
                                    <p class="text-sm text-gray-500">Active Sessions</p>
                                    <p class="text-2xl font-bold text-gray-900 mt-1">456</p>
                                </div>
                                <div class="bg-white rounded-lg p-4 border border-gray-200">
                                    <p class="text-sm text-gray-500">Revenue</p>
                                    <p class="text-2xl font-bold text-gray-900 mt-1">$12.5K</p>
                                </div>
                            </div>
                        </div>
                    `
                }
            });
        }, 50);
    }

    // Example 3: Overlay Mode
    const overlayContainer = document.querySelector('#sidebar-overlay');
    if (overlayContainer) {
        overlayContainer.innerHTML = '<div id="sidebar-overlay-demo" class="border border-gray-200 rounded-lg overflow-hidden" style="height: 300px;"></div>';

        setTimeout(() => {
            sidebars['overlay'] = new FlexSidebar('#sidebar-overlay-demo', {
                position: 'left',
                width: '200px',
                mobileMode: 'overlay',
                desktopMode: 'overlay',
                defaultOpen: false,
                backdrop: true,
                content: {
                    sidebar: `
                        <div class="bg-purple-900 text-white h-full p-4">
                            <h4 class="font-bold mb-3">Overlay Mode</h4>
                            <p class="text-xs text-purple-200">Floats over content</p>
                        </div>
                    `,
                    main: `
                        <div class="p-4 bg-gray-50 h-full flex items-center justify-center">
                            <button onclick="window.toggleOverlaySidebar()" class="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700">
                                Toggle Overlay
                            </button>
                        </div>
                    `
                }
            });

            window.toggleOverlaySidebar = () => sidebars['overlay'].toggle();
        }, 50);
    }

    // Example 4: Push Mode
    const pushContainer = document.querySelector('#sidebar-push');
    if (pushContainer) {
        pushContainer.innerHTML = '<div id="sidebar-push-demo" class="border border-gray-200 rounded-lg overflow-hidden" style="height: 300px;"></div>';

        setTimeout(() => {
            sidebars['push'] = new FlexSidebar('#sidebar-push-demo', {
                position: 'left',
                width: '200px',
                mobileMode: 'push',
                desktopMode: 'push',
                defaultOpen: false,
                backdrop: false,
                content: {
                    sidebar: `
                        <div class="bg-green-900 text-white h-full p-4">
                            <h4 class="font-bold mb-3">Push Mode</h4>
                            <p class="text-xs text-green-200">Pushes content aside</p>
                        </div>
                    `,
                    main: `
                        <div class="p-4 bg-gray-50 h-full flex items-center justify-center">
                            <button onclick="window.togglePushSidebar()" class="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700">
                                Toggle Push
                            </button>
                        </div>
                    `
                }
            });

            window.togglePushSidebar = () => sidebars['push'].toggle();
        }, 50);
    }
}

/**
 * Initialize Phase 2 Combined Example
 */
function initPhase2CombinedExample() {
    console.log('Initializing Phase 2 Combined Example...');

    const combinedContainer = document.querySelector('#phase2-combined');
    if (combinedContainer) {
        combinedContainer.innerHTML = '<div id="phase2-combined-demo" class="border-2 border-indigo-300 rounded-lg overflow-hidden" style="height: 600px;"></div>';

        setTimeout(() => {
            // Create sidebar layout
            sidebars['combined'] = new FlexSidebar('#phase2-combined-demo', {
                position: 'left',
                width: { xs: '100%', md: '260px' },
                collapsible: true,
                mobileMode: 'overlay',
                desktopMode: 'push',
                defaultOpen: { xs: false, md: true },
                backdrop: true,
                content: {
                    sidebar: `
                        <div class="bg-gradient-to-b from-indigo-900 to-purple-900 text-white h-full">
                            <div class="p-4 border-b border-indigo-700">
                                <h3 class="font-bold">Complete Example</h3>
                                <p class="text-xs text-indigo-200 mt-1">All components working together</p>
                            </div>
                            <nav class="p-4 space-y-1">
                                <a href="#" class="flex items-center gap-2 px-3 py-2 rounded bg-indigo-800">
                                    <i class="ph ph-layout"></i>
                                    <span class="text-sm">Overview</span>
                                </a>
                                <a href="#" class="flex items-center gap-2 px-3 py-2 rounded hover:bg-indigo-800">
                                    <i class="ph ph-copy"></i>
                                    <span class="text-sm">Sections</span>
                                </a>
                                <a href="#" class="flex items-center gap-2 px-3 py-2 rounded hover:bg-indigo-800">
                                    <i class="ph ph-sidebar"></i>
                                    <span class="text-sm">Layouts</span>
                                </a>
                            </nav>
                        </div>
                    `,
                    main: `
                        <div class="bg-gray-50 h-full overflow-y-auto">
                            <!-- Hero Section -->
                            <div id="combined-hero"></div>

                            <!-- Stats Section -->
                            <div id="combined-stats"></div>

                            <!-- CTA Section -->
                            <div id="combined-cta"></div>
                        </div>
                    `
                }
            });

            // Wait for sidebar to render, then create sections inside
            setTimeout(() => {
                // Hero Section
                new FlexSection('#combined-hero', {
                    variant: 'hero',
                    padding: { xs: 'lg', md: 'xl' },
                    background: {
                        type: 'gradient',
                        gradient: {
                            from: 'blue-600',
                            to: 'indigo-600',
                            direction: 'to-br'
                        }
                    },
                    slots: {
                        body: {
                            content: `
                                <div class="text-center text-white">
                                    <h1 class="text-3xl font-bold mb-3">Complete Layout System</h1>
                                    <p class="text-blue-100">FlexSidebar + FlexSection + FlexContainer</p>
                                    <button onclick="window.toggleCombinedSidebar()" class="mt-4 px-4 py-2 bg-white text-blue-600 rounded-lg hover:bg-blue-50">
                                        <i class="ph ph-sidebar mr-2"></i>Toggle Sidebar
                                    </button>
                                </div>
                            `
                        }
                    }
                });

                // Stats Section
                new FlexSection('#combined-stats', {
                    variant: 'content',
                    padding: 'lg',
                    width: 'contained',
                    background: {
                        type: 'solid',
                        color: 'white'
                    },
                    slots: {
                        body: {
                            content: `
                                <div class="grid grid-cols-3 gap-4">
                                    <div class="text-center">
                                        <p class="text-3xl font-bold text-indigo-600">3</p>
                                        <p class="text-sm text-gray-600">Components</p>
                                    </div>
                                    <div class="text-center">
                                        <p class="text-3xl font-bold text-purple-600">∞</p>
                                        <p class="text-sm text-gray-600">Possibilities</p>
                                    </div>
                                    <div class="text-center">
                                        <p class="text-3xl font-bold text-pink-600">100%</p>
                                        <p class="text-sm text-gray-600">Flexible</p>
                                    </div>
                                </div>
                            `
                        }
                    }
                });

                // CTA Section
                new FlexSection('#combined-cta', {
                    variant: 'cta',
                    padding: 'md',
                    background: {
                        type: 'gradient',
                        gradient: {
                            from: 'green-400',
                            to: 'teal-500',
                            direction: 'to-r'
                        }
                    },
                    slots: {
                        body: {
                            content: `
                                <div class="text-center text-white">
                                    <p class="font-semibold">Phase 2 is complete!</p>
                                </div>
                            `
                        }
                    }
                });

                window.toggleCombinedSidebar = () => sidebars['combined'].toggle();
            }, 100);
        }, 50);
    }
}

export { initShowcase };
