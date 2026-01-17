/**
 * Menu Sync Page
 *
 * Handles synchronization of menu configuration from menu.json to database.
 * Provides UI for viewing sync status, previewing changes, and managing sync history.
 */

import { apiFetch } from './api.js';

class MenuSyncPage {
    constructor() {
        this.syncStatus = null;
        this.menuStructure = null;
        this.syncHistory = [];
        this.init();
    }

    async init() {
        this.setupEventListeners();
        await this.loadSyncStatus();
        await this.loadMenuStructure();
        await this.loadSyncHistory();
    }

    setupEventListeners() {
        // Sync Now button
        const syncNowBtn = document.getElementById('sync-now-btn');
        if (syncNowBtn) {
            syncNowBtn.addEventListener('click', () => this.handleSyncNow());
        }

        // Preview Changes button
        const previewBtn = document.getElementById('preview-changes-btn');
        if (previewBtn) {
            previewBtn.addEventListener('click', () => this.handlePreviewChanges());
        }

        // Refresh Status button
        const refreshBtn = document.getElementById('refresh-status-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshStatus());
        }

        // Toggle menu preview
        const toggleMenuBtn = document.getElementById('toggle-menu-preview');
        if (toggleMenuBtn) {
            toggleMenuBtn.addEventListener('click', () => this.toggleMenuPreview());
        }

        // Toggle advanced options
        const toggleAdvancedBtn = document.getElementById('toggle-advanced-options');
        if (toggleAdvancedBtn) {
            toggleAdvancedBtn.addEventListener('click', () => this.toggleAdvancedOptions());
        }

        // Reset menu button
        const resetMenuBtn = document.getElementById('reset-menu-btn');
        if (resetMenuBtn) {
            resetMenuBtn.addEventListener('click', () => this.handleResetMenu());
        }
    }

    async loadSyncStatus() {
        try {
            const response = await apiFetch('/menu/sync/status');

            if (response.ok) {
                this.syncStatus = await response.json();
                this.renderSyncStatus();
            } else {
                console.warn('Failed to load sync status, using defaults');
                this.syncStatus = {
                    last_sync: null,
                    menu_items_count: 0,
                    sync_version: null,
                    is_synced: false
                };
                this.renderSyncStatus();
            }
        } catch (error) {
            console.error('Error loading sync status:', error);
            this.syncStatus = {
                last_sync: null,
                menu_items_count: 0,
                sync_version: null,
                is_synced: false
            };
            this.renderSyncStatus();
        }
    }

    async loadMenuStructure() {
        try {
            const response = await fetch('/config/menu.json');
            if (response.ok) {
                const menuData = await response.json();
                this.menuStructure = menuData.items || menuData;
                this.renderMenuStructure();
            }
        } catch (error) {
            console.error('Error loading menu structure:', error);
            document.getElementById('menu-structure-preview').innerHTML = `
                <div class="text-center py-4 text-gray-500">
                    <i class="ph ph-warning-circle text-2xl mb-2"></i>
                    <p>Failed to load menu structure</p>
                </div>
            `;
        }
    }

    async loadSyncHistory() {
        try {
            const response = await apiFetch('/menu/sync/history');

            if (response.ok) {
                this.syncHistory = await response.json();
                this.renderSyncHistory();
            } else {
                console.warn('Failed to load sync history');
                this.syncHistory = [];
                this.renderSyncHistory();
            }
        } catch (error) {
            console.error('Error loading sync history:', error);
            this.syncHistory = [];
            this.renderSyncHistory();
        }
    }

    renderSyncStatus() {
        // Update status badge
        const statusBadge = document.getElementById('sync-status-badge');
        if (statusBadge) {
            if (this.syncStatus.is_synced) {
                statusBadge.innerHTML = '<i class="ph ph-check-circle mr-2"></i>Synced';
                statusBadge.className = 'badge badge-lg bg-green-100 text-green-800';
            } else {
                statusBadge.innerHTML = '<i class="ph ph-clock mr-2"></i>Not Synced';
                statusBadge.className = 'badge badge-lg bg-gray-100 text-gray-800';
            }
        }

        // Update last sync time
        const lastSyncEl = document.getElementById('last-sync-time');
        if (lastSyncEl) {
            lastSyncEl.textContent = this.syncStatus.last_sync
                ? this.formatDate(this.syncStatus.last_sync)
                : 'Never';
        }

        // Update menu items count
        const menuCountEl = document.getElementById('menu-items-count');
        if (menuCountEl) {
            menuCountEl.textContent = this.syncStatus.menu_items_count || 0;
        }

        // Update sync version
        const versionEl = document.getElementById('sync-version');
        if (versionEl) {
            versionEl.textContent = this.syncStatus.sync_version || '-';
        }
    }

    renderMenuStructure() {
        const container = document.getElementById('menu-structure-preview');
        if (!container || !this.menuStructure) return;

        const html = this.renderMenuItems(this.menuStructure, 0);
        container.innerHTML = html;
    }

    renderMenuItems(items, level) {
        if (!items || items.length === 0) return '';

        return items.map(item => {
            const hasSubmenu = (item.submenu && item.submenu.length > 0) ||
                             (item.children && item.children.length > 0);
            const submenuItems = item.submenu || item.children || [];

            const indent = level * 24;
            const icon = item.icon || 'ph-duotone ph-circle';
            const iconColor = item.iconColor || 'text-gray-600';

            let html = `
                <div class="flex items-center gap-3 py-2 px-3 hover:bg-gray-50 rounded" style="padding-left: ${indent + 12}px">
                    <i class="${icon} ${iconColor}"></i>
                    <span class="font-medium text-gray-900">${this.escapeHtml(item.title)}</span>
                    ${item.route ? `<span class="text-xs text-gray-500 ml-2">(${item.route})</span>` : ''}
                    ${item.permission ? `<span class="badge badge-sm bg-purple-100 text-purple-800 ml-2">${item.permission}</span>` : ''}
                    ${item.badge ? `<span class="badge badge-sm bg-${item.badgeColor || 'blue-500'} text-white ml-2">${item.badge}</span>` : ''}
                </div>
            `;

            if (hasSubmenu) {
                html += this.renderMenuItems(submenuItems, level + 1);
            }

            return html;
        }).join('');
    }

    renderSyncHistory() {
        const container = document.getElementById('sync-history-container');
        if (!container) return;

        if (this.syncHistory.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <i class="ph-duotone ph-clock-counter-clockwise text-4xl mb-2"></i>
                    <p>No sync history available</p>
                </div>
            `;
            return;
        }

        container.innerHTML = `
            <div class="overflow-x-auto">
                <table class="table">
                    <thead>
                        <tr>
                            <th>Date & Time</th>
                            <th>Status</th>
                            <th>Items Synced</th>
                            <th>Version</th>
                            <th>User</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${this.syncHistory.map(entry => `
                            <tr>
                                <td class="text-sm">${this.formatDate(entry.timestamp)}</td>
                                <td>
                                    ${entry.status === 'success'
                                        ? '<span class="badge badge-sm bg-green-100 text-green-800">Success</span>'
                                        : '<span class="badge badge-sm bg-red-100 text-red-800">Failed</span>'
                                    }
                                </td>
                                <td class="text-center">${entry.items_synced || 0}</td>
                                <td class="text-sm text-gray-600">${entry.version || '-'}</td>
                                <td class="text-sm text-gray-600">${this.escapeHtml(entry.user || 'System')}</td>
                                <td>
                                    <button
                                        class="btn btn-sm btn-secondary"
                                        onclick="menuSyncPage.viewSyncDetails('${entry.id}')"
                                        title="View Details"
                                    >
                                        <i class="ph ph-eye"></i>
                                    </button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }

    async handleSyncNow() {
        if (!confirm('Are you sure you want to sync the menu configuration? This will update the database with the current menu.json structure.')) {
            return;
        }

        const syncBtn = document.getElementById('sync-now-btn');
        const originalContent = syncBtn.innerHTML;
        syncBtn.disabled = true;
        syncBtn.innerHTML = '<i class="ph ph-spinner ph-spin mr-2"></i>Syncing...';

        try {
            // Get advanced options
            const forceSync = document.getElementById('force-sync-checkbox')?.checked || false;
            const preserveCustomizations = document.getElementById('preserve-customizations-checkbox')?.checked || true;
            const clearCache = document.getElementById('clear-cache-checkbox')?.checked || true;

            const response = await apiFetch('/menu/sync', {
                method: 'POST',
                body: JSON.stringify({
                    force_sync: forceSync,
                    preserve_customizations: preserveCustomizations,
                    clear_cache: clearCache
                })
            });

            if (response.ok) {
                const result = await response.json();
                alert(`Menu synced successfully!\n\n${result.items_synced || 0} items synced.`);
                await this.refreshStatus();
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Sync failed');
            }
        } catch (error) {
            console.error('Error syncing menu:', error);
            alert(`Failed to sync menu: ${error.message}`);
        } finally {
            syncBtn.disabled = false;
            syncBtn.innerHTML = originalContent;
        }
    }

    async handlePreviewChanges() {
        const previewBtn = document.getElementById('preview-changes-btn');
        const originalContent = previewBtn.innerHTML;
        previewBtn.disabled = true;
        previewBtn.innerHTML = '<i class="ph ph-spinner ph-spin mr-2"></i>Loading...';

        try {
            const response = await apiFetch('/menu/sync/preview');

            if (response.ok) {
                const preview = await response.json();
                this.showPreviewModal(preview);
            } else {
                throw new Error('Failed to load preview');
            }
        } catch (error) {
            console.error('Error loading preview:', error);
            alert('Failed to load preview. The preview feature may not be available yet.');
        } finally {
            previewBtn.disabled = false;
            previewBtn.innerHTML = originalContent;
        }
    }

    showPreviewModal(preview) {
        // Create a modal to show preview
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
                <div class="flex items-center justify-between p-6 border-b border-gray-200">
                    <h3 class="text-xl font-semibold text-gray-900">Sync Preview</h3>
                    <button class="close-modal text-gray-400 hover:text-gray-600">
                        <i class="ph ph-x text-2xl"></i>
                    </button>
                </div>
                <div class="p-6 overflow-y-auto max-h-[70vh]">
                    <div class="space-y-4">
                        <div class="grid grid-cols-3 gap-4">
                            <div class="bg-green-50 p-4 rounded-lg">
                                <div class="text-sm text-gray-600 mb-1">New Items</div>
                                <div class="text-2xl font-bold text-green-600">${preview.new_items || 0}</div>
                            </div>
                            <div class="bg-blue-50 p-4 rounded-lg">
                                <div class="text-sm text-gray-600 mb-1">Updated Items</div>
                                <div class="text-2xl font-bold text-blue-600">${preview.updated_items || 0}</div>
                            </div>
                            <div class="bg-red-50 p-4 rounded-lg">
                                <div class="text-sm text-gray-600 mb-1">Removed Items</div>
                                <div class="text-2xl font-bold text-red-600">${preview.removed_items || 0}</div>
                            </div>
                        </div>
                        <div class="bg-gray-50 p-4 rounded">
                            <h4 class="font-semibold text-gray-900 mb-2">Changes Summary</h4>
                            <pre class="text-xs text-gray-700 overflow-x-auto">${JSON.stringify(preview, null, 2)}</pre>
                        </div>
                    </div>
                </div>
                <div class="flex justify-end gap-3 p-6 border-t border-gray-200">
                    <button class="close-modal btn btn-secondary">Close</button>
                    <button class="btn btn-primary" onclick="menuSyncPage.handleSyncNow(); this.closest('.fixed').remove();">
                        Proceed with Sync
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Close modal handlers
        modal.querySelectorAll('.close-modal').forEach(btn => {
            btn.addEventListener('click', () => modal.remove());
        });

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }

    async refreshStatus() {
        await this.loadSyncStatus();
        await this.loadSyncHistory();
    }

    toggleMenuPreview() {
        const button = document.getElementById('toggle-menu-preview');
        const container = document.getElementById('menu-structure-preview');

        if (container.classList.contains('max-h-96')) {
            container.classList.remove('max-h-96', 'overflow-y-auto');
            button.querySelector('span').textContent = 'Show Less';
            button.querySelector('i').style.transform = 'rotate(180deg)';
        } else {
            container.classList.add('max-h-96', 'overflow-y-auto');
            button.querySelector('span').textContent = 'Show All';
            button.querySelector('i').style.transform = 'rotate(0deg)';
        }
    }

    toggleAdvancedOptions() {
        const content = document.getElementById('advanced-options-content');
        const icon = document.querySelector('#toggle-advanced-options i');

        content.classList.toggle('hidden');
        if (content.classList.contains('hidden')) {
            icon.style.transform = 'rotate(0deg)';
        } else {
            icon.style.transform = 'rotate(180deg)';
        }
    }

    async handleResetMenu() {
        if (!confirm('⚠️ WARNING: This will reset the menu to default configuration and remove all customizations.\n\nThis action cannot be undone. Are you sure you want to continue?')) {
            return;
        }

        if (!confirm('This is your last chance. Proceed with menu reset?')) {
            return;
        }

        try {
            const response = await apiFetch('/menu/reset', {
                method: 'POST'
            });

            if (response.ok) {
                alert('Menu has been reset to default configuration successfully.');
                await this.refreshStatus();
            } else {
                throw new Error('Failed to reset menu');
            }
        } catch (error) {
            console.error('Error resetting menu:', error);
            alert('Failed to reset menu. Please try again or contact support.');
        }
    }

    viewSyncDetails(entryId) {
        // Find the entry
        const entry = this.syncHistory.find(e => e.id === entryId);
        if (!entry) return;

        // Show details in a modal or expand inline
        alert(`Sync Details:\n\nID: ${entry.id}\nDate: ${this.formatDate(entry.timestamp)}\nStatus: ${entry.status}\nItems: ${entry.items_synced}\nVersion: ${entry.version}\nUser: ${entry.user}`);
    }

    formatDate(dateString) {
        if (!dateString) return 'N/A';

        const date = new Date(dateString);
        return date.toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize the page when DOM is ready
let menuSyncPage;
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        menuSyncPage = new MenuSyncPage();
    });
} else {
    menuSyncPage = new MenuSyncPage();
}
