/**
 * Components Showcase Module
 *
 * Demonstrates FlexCard, FlexModal, and FlexTabs components with interactive examples
 *
 * @author Claude Code
 * @version 1.0.0
 */

import { FlexCard } from './components/flex-card.js';
import { FlexModal } from './components/flex-modal.js';
import { FlexTabs } from './components/flex-tabs.js';
import { showToast } from './ui-utils.js';

let modals = {};
let cards = {};
let tabs = {};

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

    // Initialize card examples
    initCardExamples();

    // Initialize modal examples
    initModalExamples();

    // Initialize tabs examples
    initTabsExamples();

    // Initialize combined example
    initCombinedExample();
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

export { initShowcase };
