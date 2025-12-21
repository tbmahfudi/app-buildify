/**
 * Pages List Page
 *
 * Shows all builder pages with actions to edit, publish, delete
 */

import { can } from '../../../../frontend/assets/js/rbac.js';
import { showToast } from '../../../../frontend/assets/js/ui-utils.js';

export class PagesListPage {
    constructor() {
        this.pages = [];
    }

    async render() {
        if (!can('builder:pages:read:tenant')) {
            return `
                <div class="flex items-center justify-center h-screen">
                    <div class="text-center">
                        <i class="ph-duotone ph-lock text-6xl text-gray-400 mb-4"></i>
                        <h2 class="text-2xl font-bold text-gray-700 dark:text-gray-300">Access Denied</h2>
                        <p class="text-gray-500 dark:text-gray-400 mt-2">
                            You don't have permission to view pages
                        </p>
                    </div>
                </div>
            `;
        }

        return `
            <div class="p-6">
                <div class="mb-6 flex items-center justify-between">
                    <div>
                        <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">Builder Pages</h1>
                        <p class="text-gray-500 dark:text-gray-400 mt-1">Manage your custom UI pages</p>
                    </div>
                    ${can('builder:pages:create:tenant') ? `
                        <a href="#/builder" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg flex items-center gap-2 transition">
                            <i class="ph-duotone ph-plus"></i>
                            Create New Page
                        </a>
                    ` : ''}
                </div>

                <!-- Filters -->
                <div class="mb-4 flex gap-4">
                    <select id="filter-module" class="px-4 py-2 border border-gray-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-gray-900 dark:text-gray-100">
                        <option value="">All Modules</option>
                    </select>
                    <select id="filter-status" class="px-4 py-2 border border-gray-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-gray-900 dark:text-gray-100">
                        <option value="">All Status</option>
                        <option value="published">Published</option>
                        <option value="draft">Draft</option>
                    </select>
                </div>

                <!-- Pages Grid -->
                <div id="pages-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <!-- Pages will be loaded here -->
                </div>
            </div>
        `;
    }

    async afterRender() {
        await this.loadPages();
        this.setupEventListeners();
    }

    async loadPages() {
        try {
            const response = await fetch('/api/v1/builder/pages/', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            if (response.ok) {
                this.pages = await response.json();
                this.renderPages();
            }
        } catch (error) {
            console.error('Error loading pages:', error);
            showToast('Failed to load pages', 'error');
        }
    }

    renderPages() {
        const grid = document.getElementById('pages-grid');
        if (!grid) return;

        if (this.pages.length === 0) {
            grid.innerHTML = `
                <div class="col-span-full text-center py-12">
                    <i class="ph-duotone ph-files text-6xl text-gray-300 dark:text-gray-600 mb-4"></i>
                    <p class="text-gray-500 dark:text-gray-400">No pages found. Create your first page!</p>
                </div>
            `;
            return;
        }

        grid.innerHTML = this.pages.map(page => `
            <div class="bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-lg p-6 hover:shadow-lg transition">
                <div class="flex items-start justify-between mb-4">
                    <div class="flex-1">
                        <h3 class="font-semibold text-gray-900 dark:text-gray-100 mb-1">${page.name}</h3>
                        <p class="text-sm text-gray-500 dark:text-gray-400">${page.description || 'No description'}</p>
                    </div>
                    ${page.published ?
                        '<span class="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 rounded-full">Published</span>' :
                        '<span class="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200 rounded-full">Draft</span>'
                    }
                </div>

                <div class="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-4">
                    <i class="ph-duotone ph-hash"></i>
                    <span>${page.route_path}</span>
                </div>

                ${page.module_name ? `
                    <div class="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-4">
                        <i class="ph-duotone ph-puzzle-piece"></i>
                        <span>${page.module_name}</span>
                    </div>
                ` : ''}

                <div class="flex items-center gap-2 pt-4 border-t border-gray-200 dark:border-slate-700">
                    ${can('builder:pages:edit:tenant') ? `
                        <a href="#/builder?page=${page.id}" class="flex-1 px-3 py-2 text-sm font-medium text-blue-600 hover:text-blue-700 border border-blue-600 rounded-md hover:bg-blue-50 dark:hover:bg-blue-900/20 text-center transition">
                            <i class="ph-duotone ph-pencil mr-1"></i>Edit
                        </a>
                    ` : ''}
                    ${can('builder:pages:delete:tenant') ? `
                        <button class="px-3 py-2 text-sm font-medium text-red-600 hover:text-red-700 border border-red-600 rounded-md hover:bg-red-50 dark:hover:bg-red-900/20 transition" data-page-id="${page.id}" onclick="window.deletePage('${page.id}')">
                            <i class="ph-duotone ph-trash"></i>
                        </button>
                    ` : ''}
                </div>
            </div>
        `).join('');
    }

    setupEventListeners() {
        // Make delete function available globally
        window.deletePage = async (pageId) => {
            if (!confirm('Are you sure you want to delete this page?')) return;

            try {
                const response = await fetch(`/api/v1/builder/pages/${pageId}`, {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                });

                if (response.ok) {
                    showToast('Page deleted successfully', 'success');
                    await this.loadPages();
                } else {
                    throw new Error('Failed to delete page');
                }
            } catch (error) {
                console.error('Error deleting page:', error);
                showToast('Failed to delete page', 'error');
            }
        };

        // Filter listeners
        document.getElementById('filter-module')?.addEventListener('change', () => {
            this.loadPages();
        });

        document.getElementById('filter-status')?.addEventListener('change', () => {
            this.loadPages();
        });
    }

    cleanup() {
        delete window.deletePage;
    }
}
