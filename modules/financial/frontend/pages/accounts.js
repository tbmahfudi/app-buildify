/**
 * Accounts Page - Chart of Accounts Management
 */

import { apiFetch } from '../assets/js/api.js';
import { DataTable } from '../components/data-table.js';
import { FormBuilder } from '../components/form-builder.js';

export class AccountsPage {
    constructor() {
        this.accounts = [];
        this.selectedAccount = null;
        this.viewMode = 'tree'; // 'tree' or 'list'
        this.filters = {
            account_type: '',
            is_active: 'true'
        };
        this.dataTable = null;
    }

    /**
     * Get tenant context from current user
     */
    async getTenantContext() {
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        return {
            tenant_id: user.tenant_id,
            company_id: user.company_id
        };
    }

    /**
     * Render the page
     */
    async render() {
        // Load the HTML template
        const response = await fetch('/modules/financial/frontend/pages/accounts.html');
        const html = await response.text();

        const container = document.getElementById('app-content');
        if (container) {
            container.innerHTML = html;
        }

        // Initialize page
        await this.init();
    }

    /**
     * Initialize the page
     */
    async init() {
        this.attachEventListeners();
        await this.loadAccounts();
        this.renderTreeView();
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Create account button
        const createBtn = document.getElementById('btn-create-account');
        if (createBtn) {
            createBtn.addEventListener('click', () => this.openAccountModal());
        }

        // View mode buttons
        const treeViewBtn = document.getElementById('view-tree');
        const listViewBtn = document.getElementById('view-list');

        if (treeViewBtn) {
            treeViewBtn.addEventListener('click', () => this.switchView('tree'));
        }

        if (listViewBtn) {
            listViewBtn.addEventListener('click', () => this.switchView('list'));
        }

        // Expand all button
        const expandAllBtn = document.getElementById('btn-expand-all');
        if (expandAllBtn) {
            expandAllBtn.addEventListener('click', () => this.toggleExpandAll());
        }

        // Filters
        const typeFilter = document.getElementById('filter-account-type');
        const statusFilter = document.getElementById('filter-status');

        if (typeFilter) {
            typeFilter.addEventListener('change', (e) => {
                this.filters.account_type = e.target.value;
                this.applyFilters();
            });
        }

        if (statusFilter) {
            statusFilter.addEventListener('change', (e) => {
                this.filters.is_active = e.target.value;
                this.applyFilters();
            });
        }

        // Modal close buttons
        const closeModalBtn = document.getElementById('btn-close-modal');
        if (closeModalBtn) {
            closeModalBtn.addEventListener('click', () => this.closeAccountModal());
        }

        const cancelDeleteBtn = document.getElementById('btn-cancel-delete');
        if (cancelDeleteBtn) {
            cancelDeleteBtn.addEventListener('click', () => this.closeDeleteModal());
        }

        const confirmDeleteBtn = document.getElementById('btn-confirm-delete');
        if (confirmDeleteBtn) {
            confirmDeleteBtn.addEventListener('click', () => this.confirmDelete());
        }

        // Close modal on background click
        const accountModal = document.getElementById('account-modal');
        if (accountModal) {
            accountModal.addEventListener('click', (e) => {
                if (e.target === accountModal) {
                    this.closeAccountModal();
                }
            });
        }

        const deleteModal = document.getElementById('delete-modal');
        if (deleteModal) {
            deleteModal.addEventListener('click', (e) => {
                if (e.target === deleteModal) {
                    this.closeDeleteModal();
                }
            });
        }
    }

    /**
     * Load accounts from API
     */
    async loadAccounts() {
        try {
            const context = await this.getTenantContext();
            const queryParams = new URLSearchParams({
                tenant_id: context.tenant_id,
                company_id: context.company_id,
                ...this.filters
            });

            const response = await apiFetch(`/financial/accounts?${queryParams.toString()}`);

            if (!response.ok) {
                throw new Error('Failed to load accounts');
            }

            this.accounts = await response.json();
        } catch (error) {
            console.error('Error loading accounts:', error);
            this.showToast('Failed to load accounts', 'error');
            this.accounts = [];
        }
    }

    /**
     * Switch view mode
     */
    switchView(mode) {
        this.viewMode = mode;

        const treeView = document.getElementById('accounts-tree-view');
        const listView = document.getElementById('accounts-list-view');
        const treeViewBtn = document.getElementById('view-tree');
        const listViewBtn = document.getElementById('view-list');
        const expandAllBtn = document.getElementById('btn-expand-all');

        if (mode === 'tree') {
            treeView?.classList.remove('hidden');
            listView?.classList.add('hidden');
            treeViewBtn?.classList.add('bg-blue-600', 'text-white');
            treeViewBtn?.classList.remove('bg-white', 'border', 'border-gray-300');
            listViewBtn?.classList.remove('bg-blue-600', 'text-white');
            listViewBtn?.classList.add('bg-white', 'border', 'border-gray-300');
            expandAllBtn?.classList.remove('hidden');
            this.renderTreeView();
        } else {
            treeView?.classList.add('hidden');
            listView?.classList.remove('hidden');
            treeViewBtn?.classList.remove('bg-blue-600', 'text-white');
            treeViewBtn?.classList.add('bg-white', 'border', 'border-gray-300');
            listViewBtn?.classList.add('bg-blue-600', 'text-white');
            listViewBtn?.classList.remove('bg-white', 'border', 'border-gray-300');
            expandAllBtn?.classList.add('hidden');
            this.renderListView();
        }
    }

    /**
     * Render tree view
     */
    renderTreeView() {
        const container = document.getElementById('accounts-tree-container');
        if (!container) return;

        const filteredAccounts = this.filterAccounts(this.accounts);
        const tree = this.buildAccountTree(filteredAccounts);

        container.innerHTML = tree.length > 0 ? this.renderTreeNodes(tree) : this.renderEmptyState();
    }

    /**
     * Build account tree from flat list
     */
    buildAccountTree(accounts) {
        const tree = [];
        const map = {};

        // Create map of all accounts
        accounts.forEach(account => {
            map[account.id] = { ...account, children: [] };
        });

        // Build tree structure
        accounts.forEach(account => {
            if (account.parent_account_id && map[account.parent_account_id]) {
                map[account.parent_account_id].children.push(map[account.id]);
            } else {
                tree.push(map[account.id]);
            }
        });

        return tree;
    }

    /**
     * Render tree nodes recursively
     */
    renderTreeNodes(nodes, level = 0) {
        let html = '<ul class="tree-list">';

        nodes.forEach(node => {
            const hasChildren = node.children && node.children.length > 0;
            const indent = level * 24;

            html += `
                <li class="tree-node" data-account-id="${node.id}">
                    <div class="tree-node-content flex items-center gap-2 py-2 px-3 hover:bg-gray-50 rounded-lg cursor-pointer" style="padding-left: ${indent + 12}px">
                        ${hasChildren ? `
                            <button class="tree-toggle w-6 h-6 flex items-center justify-center rounded hover:bg-gray-200 transition">
                                <i class="ph ph-caret-right text-gray-600"></i>
                            </button>
                        ` : '<span class="w-6"></span>'}
                        <div class="flex items-center gap-2 flex-1">
                            <i class="ph-duotone ${this.getAccountIcon(node.account_type)} text-xl ${this.getAccountColor(node.account_type)}"></i>
                            <div class="flex-1">
                                <div class="flex items-center gap-2">
                                    <span class="font-mono text-sm text-gray-600">${node.code || ''}</span>
                                    <span class="font-medium text-gray-900">${node.name}</span>
                                    ${!node.is_active ? '<span class="px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded">Inactive</span>' : ''}
                                </div>
                                ${node.description ? `<p class="text-sm text-gray-500 mt-0.5">${node.description}</p>` : ''}
                            </div>
                            <div class="account-balance text-sm font-medium ${node.balance >= 0 ? 'text-green-600' : 'text-red-600'}">
                                ${this.formatCurrency(node.balance || 0)}
                            </div>
                        </div>
                        <div class="account-actions flex gap-1">
                            <button class="btn-edit-account p-2 text-gray-600 hover:text-blue-600 transition" data-account-id="${node.id}" title="Edit">
                                <i class="ph ph-pencil-simple"></i>
                            </button>
                            <button class="btn-add-child p-2 text-gray-600 hover:text-green-600 transition" data-account-id="${node.id}" title="Add Child Account">
                                <i class="ph ph-plus-circle"></i>
                            </button>
                            <button class="btn-delete-account p-2 text-gray-600 hover:text-red-600 transition" data-account-id="${node.id}" title="Delete">
                                <i class="ph ph-trash"></i>
                            </button>
                        </div>
                    </div>
                    ${hasChildren ? `<div class="tree-children hidden">${this.renderTreeNodes(node.children, level + 1)}</div>` : ''}
                </li>
            `;
        });

        html += '</ul>';

        // Attach event listeners after rendering
        setTimeout(() => this.attachTreeEventListeners(), 0);

        return html;
    }

    /**
     * Attach tree event listeners
     */
    attachTreeEventListeners() {
        // Toggle expand/collapse
        document.querySelectorAll('.tree-toggle').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const node = btn.closest('.tree-node');
                const children = node.querySelector('.tree-children');
                const icon = btn.querySelector('i');

                if (children) {
                    children.classList.toggle('hidden');
                    icon.classList.toggle('ph-caret-right');
                    icon.classList.toggle('ph-caret-down');
                }
            });
        });

        // Edit account
        document.querySelectorAll('.btn-edit-account').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const accountId = parseInt(btn.dataset.accountId);
                this.editAccount(accountId);
            });
        });

        // Add child account
        document.querySelectorAll('.btn-add-child').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const accountId = parseInt(btn.dataset.accountId);
                this.addChildAccount(accountId);
            });
        });

        // Delete account
        document.querySelectorAll('.btn-delete-account').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const accountId = parseInt(btn.dataset.accountId);
                this.deleteAccount(accountId);
            });
        });
    }

    /**
     * Render list view
     */
    renderListView() {
        if (!this.dataTable) {
            this.dataTable = new DataTable({
                containerId: 'accounts-table-container',
                columns: [
                    { field: 'code', label: 'Code', sortable: true },
                    { field: 'name', label: 'Name', sortable: true },
                    {
                        field: 'account_type',
                        label: 'Type',
                        sortable: true,
                        formatter: (value) => this.formatAccountType(value)
                    },
                    {
                        field: 'balance',
                        label: 'Balance',
                        sortable: true,
                        formatter: (value) => this.formatCurrency(value || 0),
                        className: 'text-right'
                    },
                    {
                        field: 'is_active',
                        label: 'Status',
                        formatter: (value) => value
                            ? '<span class="px-2 py-1 text-xs bg-green-100 text-green-800 rounded">Active</span>'
                            : '<span class="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded">Inactive</span>'
                    }
                ],
                dataSource: async (params) => {
                    const filteredAccounts = this.filterAccounts(this.accounts);
                    return {
                        data: filteredAccounts,
                        total: filteredAccounts.length
                    };
                },
                actions: [
                    {
                        name: 'edit',
                        label: '',
                        icon: 'ph-pencil-simple',
                        className: 'text-gray-600 hover:text-blue-600',
                        title: 'Edit',
                        handler: (row) => this.editAccount(row.id)
                    },
                    {
                        name: 'delete',
                        label: '',
                        icon: 'ph-trash',
                        className: 'text-gray-600 hover:text-red-600',
                        title: 'Delete',
                        handler: (row) => this.deleteAccount(row.id)
                    }
                ],
                pageSize: 20
            });
        }

        this.dataTable.init();
    }

    /**
     * Filter accounts based on current filters
     */
    filterAccounts(accounts) {
        return accounts.filter(account => {
            if (this.filters.account_type && account.account_type !== this.filters.account_type) {
                return false;
            }

            if (this.filters.is_active !== '') {
                const isActive = this.filters.is_active === 'true';
                if (account.is_active !== isActive) {
                    return false;
                }
            }

            return true;
        });
    }

    /**
     * Apply filters
     */
    applyFilters() {
        if (this.viewMode === 'tree') {
            this.renderTreeView();
        } else {
            this.dataTable?.refresh();
        }
    }

    /**
     * Toggle expand/collapse all
     */
    toggleExpandAll() {
        const allChildren = document.querySelectorAll('.tree-children');
        const allToggles = document.querySelectorAll('.tree-toggle i');
        const isExpanded = Array.from(allChildren).some(child => !child.classList.contains('hidden'));

        if (isExpanded) {
            // Collapse all
            allChildren.forEach(child => child.classList.add('hidden'));
            allToggles.forEach(icon => {
                icon.classList.remove('ph-caret-down');
                icon.classList.add('ph-caret-right');
            });
            document.getElementById('btn-expand-all').innerHTML = '<i class="ph ph-arrows-out"></i> Expand All';
        } else {
            // Expand all
            allChildren.forEach(child => child.classList.remove('hidden'));
            allToggles.forEach(icon => {
                icon.classList.remove('ph-caret-right');
                icon.classList.add('ph-caret-down');
            });
            document.getElementById('btn-expand-all').innerHTML = '<i class="ph ph-arrows-in"></i> Collapse All';
        }
    }

    /**
     * Open account modal
     */
    openAccountModal(account = null, parentId = null) {
        this.selectedAccount = account;

        const modal = document.getElementById('account-modal');
        const modalTitle = document.getElementById('modal-title');

        if (modalTitle) {
            modalTitle.textContent = account ? 'Edit Account' : 'New Account';
        }

        const formBuilder = new FormBuilder({
            formId: 'account-form',
            fields: [
                {
                    name: 'code',
                    label: 'Account Code',
                    type: 'text',
                    required: true,
                    placeholder: 'e.g., 1000'
                },
                {
                    name: 'name',
                    label: 'Account Name',
                    type: 'text',
                    required: true,
                    placeholder: 'e.g., Cash and Bank'
                },
                {
                    name: 'account_type',
                    label: 'Account Type',
                    type: 'select',
                    required: true,
                    options: [
                        { value: 'ASSET', label: 'Asset' },
                        { value: 'LIABILITY', label: 'Liability' },
                        { value: 'EQUITY', label: 'Equity' },
                        { value: 'REVENUE', label: 'Revenue' },
                        { value: 'EXPENSE', label: 'Expense' }
                    ]
                },
                {
                    name: 'parent_account_id',
                    label: 'Parent Account',
                    type: 'select',
                    options: [
                        { value: '', label: 'None (Top Level)' },
                        ...this.accounts
                            .filter(a => !account || a.id !== account.id)
                            .map(a => ({ value: a.id, label: `${a.code} - ${a.name}` }))
                    ]
                },
                {
                    name: 'description',
                    label: 'Description',
                    type: 'textarea',
                    rows: 3,
                    fullWidth: true
                },
                {
                    name: 'is_active',
                    label: 'Active',
                    type: 'checkbox',
                    checkboxLabel: 'This account is active',
                    defaultValue: true
                }
            ],
            values: account ? {
                ...account,
                parent_account_id: account.parent_account_id || ''
            } : {
                parent_account_id: parentId || '',
                is_active: true
            },
            submitLabel: account ? 'Update Account' : 'Create Account',
            onSubmit: async (formData) => {
                await this.saveAccount(formData);
            },
            onCancel: () => this.closeAccountModal()
        });

        formBuilder.render('account-form-container');

        if (modal) {
            modal.style.display = 'flex';
        }
    }

    /**
     * Close account modal
     */
    closeAccountModal() {
        const modal = document.getElementById('account-modal');
        if (modal) {
            modal.style.display = 'none';
        }
        this.selectedAccount = null;
    }

    /**
     * Add child account
     */
    addChildAccount(parentId) {
        this.openAccountModal(null, parentId);
    }

    /**
     * Edit account
     */
    editAccount(accountId) {
        const account = this.accounts.find(a => a.id === accountId);
        if (account) {
            this.openAccountModal(account);
        }
    }

    /**
     * Save account (create or update)
     */
    async saveAccount(formData) {
        try {
            const context = await this.getTenantContext();
            const data = {
                ...formData,
                tenant_id: context.tenant_id,
                company_id: context.company_id,
                parent_account_id: formData.parent_account_id || null
            };

            let response;
            if (this.selectedAccount) {
                // Update existing account
                response = await apiFetch(`/financial/accounts/${this.selectedAccount.id}`, {
                    method: 'PUT',
                    body: JSON.stringify(data)
                });
            } else {
                // Create new account
                response = await apiFetch('/financial/accounts', {
                    method: 'POST',
                    body: JSON.stringify(data)
                });
            }

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to save account');
            }

            this.showToast(
                this.selectedAccount ? 'Account updated successfully' : 'Account created successfully',
                'success'
            );

            this.closeAccountModal();
            await this.loadAccounts();
            this.applyFilters();

        } catch (error) {
            console.error('Error saving account:', error);
            throw error;
        }
    }

    /**
     * Delete account
     */
    deleteAccount(accountId) {
        this.selectedAccount = this.accounts.find(a => a.id === accountId);

        const modal = document.getElementById('delete-modal');
        if (modal) {
            modal.style.display = 'flex';
        }
    }

    /**
     * Close delete modal
     */
    closeDeleteModal() {
        const modal = document.getElementById('delete-modal');
        if (modal) {
            modal.style.display = 'none';
        }
        this.selectedAccount = null;
    }

    /**
     * Confirm delete
     */
    async confirmDelete() {
        if (!this.selectedAccount) return;

        try {
            const context = await this.getTenantContext();
            const queryParams = new URLSearchParams({
                tenant_id: context.tenant_id,
                company_id: context.company_id
            });

            const response = await apiFetch(`/financial/accounts/${this.selectedAccount.id}?${queryParams.toString()}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to delete account');
            }

            this.showToast('Account deleted successfully', 'success');
            this.closeDeleteModal();
            await this.loadAccounts();
            this.applyFilters();

        } catch (error) {
            console.error('Error deleting account:', error);
            this.showToast(error.message, 'error');
        }
    }

    /**
     * Render empty state
     */
    renderEmptyState() {
        return `
            <div class="text-center py-12">
                <i class="ph-duotone ph-tree-structure text-6xl text-gray-300 mb-4"></i>
                <p class="text-gray-500 text-lg">No accounts found</p>
                <p class="text-gray-400 text-sm mt-2">Create your first account to get started</p>
            </div>
        `;
    }

    /**
     * Get account icon based on type
     */
    getAccountIcon(type) {
        const icons = {
            ASSET: 'ph-coins',
            LIABILITY: 'ph-credit-card',
            EQUITY: 'ph-chart-pie-slice',
            REVENUE: 'ph-trend-up',
            EXPENSE: 'ph-trend-down'
        };
        return icons[type] || 'ph-circle';
    }

    /**
     * Get account color based on type
     */
    getAccountColor(type) {
        const colors = {
            ASSET: 'text-green-600',
            LIABILITY: 'text-red-600',
            EQUITY: 'text-blue-600',
            REVENUE: 'text-emerald-600',
            EXPENSE: 'text-orange-600'
        };
        return colors[type] || 'text-gray-600';
    }

    /**
     * Format account type
     */
    formatAccountType(type) {
        const types = {
            ASSET: 'Asset',
            LIABILITY: 'Liability',
            EQUITY: 'Equity',
            REVENUE: 'Revenue',
            EXPENSE: 'Expense'
        };
        return types[type] || type;
    }

    /**
     * Format currency
     */
    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    }

    /**
     * Show toast notification
     */
    showToast(message, type = 'info') {
        // Simple toast implementation - can be replaced with a more sophisticated toast library
        const toast = document.createElement('div');
        toast.className = `fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg z-50 ${
            type === 'success' ? 'bg-green-600' :
            type === 'error' ? 'bg-red-600' :
            'bg-blue-600'
        } text-white`;
        toast.textContent = message;

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 3000);
    }
}
