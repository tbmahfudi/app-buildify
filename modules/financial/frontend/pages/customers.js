/**
 * Customers Page - Customer Management
 */

import { apiFetch } from '../assets/js/api.js';
import { DataTable } from '../components/data-table.js';
import { FormBuilder } from '../components/form-builder.js';

export class CustomersPage {
    constructor() {
        this.selectedCustomer = null;
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
        const response = await fetch('/modules/financial/frontend/pages/customers.html');
        const html = await response.text();

        const container = document.getElementById('app-content');
        if (container) {
            container.innerHTML = html;
        }

        await this.init();
    }

    /**
     * Initialize the page
     */
    async init() {
        this.attachEventListeners();
        await this.loadStats();
        this.initializeTable();
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        const createBtn = document.getElementById('btn-create-customer');
        if (createBtn) {
            createBtn.addEventListener('click', () => this.openCustomerModal());
        }

        const closeModalBtn = document.getElementById('btn-close-modal');
        if (closeModalBtn) {
            closeModalBtn.addEventListener('click', () => this.closeCustomerModal());
        }

        const closeDetailsBtn = document.getElementById('btn-close-details-modal');
        if (closeDetailsBtn) {
            closeDetailsBtn.addEventListener('click', () => this.closeDetailsModal());
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
        const customerModal = document.getElementById('customer-modal');
        if (customerModal) {
            customerModal.addEventListener('click', (e) => {
                if (e.target === customerModal) this.closeCustomerModal();
            });
        }

        const detailsModal = document.getElementById('customer-details-modal');
        if (detailsModal) {
            detailsModal.addEventListener('click', (e) => {
                if (e.target === detailsModal) this.closeDetailsModal();
            });
        }

        const deleteModal = document.getElementById('delete-modal');
        if (deleteModal) {
            deleteModal.addEventListener('click', (e) => {
                if (e.target === deleteModal) this.closeDeleteModal();
            });
        }
    }

    /**
     * Load statistics
     */
    async loadStats() {
        try {
            const context = await this.getTenantContext();
            const queryParams = new URLSearchParams({
                tenant_id: context.tenant_id,
                company_id: context.company_id
            });

            const response = await apiFetch(`/financial/customers/stats?${queryParams.toString()}`);

            if (response.ok) {
                const stats = await response.json();

                document.getElementById('stat-total-customers').textContent = stats.total_customers || 0;
                document.getElementById('stat-active-customers').textContent = stats.active_customers || 0;
                document.getElementById('stat-total-receivables').textContent = this.formatCurrency(stats.total_receivables || 0);
                document.getElementById('stat-overdue').textContent = this.formatCurrency(stats.overdue || 0);
            }
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    }

    /**
     * Initialize data table
     */
    initializeTable() {
        this.dataTable = new DataTable({
            containerId: 'customers-table-container',
            columns: [
                { field: 'code', label: 'Code', sortable: true },
                { field: 'name', label: 'Name', sortable: true },
                { field: 'email', label: 'Email', sortable: true },
                { field: 'phone', label: 'Phone' },
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
                const context = await this.getTenantContext();
                const queryParams = new URLSearchParams({
                    tenant_id: context.tenant_id,
                    company_id: context.company_id
                });
                queryParams.append('page', params.page);
                queryParams.append('page_size', params.page_size);

                if (params.search) {
                    queryParams.append('search', params.search);
                }
                if (params.sort_by) {
                    queryParams.append('sort_by', params.sort_by);
                    queryParams.append('sort_dir', params.sort_dir);
                }

                const response = await apiFetch(`/financial/customers?${queryParams.toString()}`);

                if (!response.ok) {
                    throw new Error('Failed to load customers');
                }

                const data = await response.json();
                return {
                    data: data.customers || [],
                    total: data.total || 0
                };
            },
            actions: [
                {
                    name: 'view',
                    label: '',
                    icon: 'ph-eye',
                    className: 'text-gray-600 hover:text-blue-600',
                    title: 'View Details',
                    handler: (row) => this.viewCustomer(row)
                },
                {
                    name: 'edit',
                    label: '',
                    icon: 'ph-pencil-simple',
                    className: 'text-gray-600 hover:text-green-600',
                    title: 'Edit',
                    handler: (row) => this.editCustomer(row)
                },
                {
                    name: 'delete',
                    label: '',
                    icon: 'ph-trash',
                    className: 'text-gray-600 hover:text-red-600',
                    title: 'Delete',
                    handler: (row) => this.deleteCustomer(row)
                }
            ],
            onRowClick: (row) => this.viewCustomer(row),
            pageSize: 10
        });

        this.dataTable.init();
    }

    /**
     * Open customer modal
     */
    openCustomerModal(customer = null) {
        this.selectedCustomer = customer;

        const modal = document.getElementById('customer-modal');
        const modalTitle = document.getElementById('modal-title');

        if (modalTitle) {
            modalTitle.textContent = customer ? 'Edit Customer' : 'New Customer';
        }

        const formBuilder = new FormBuilder({
            formId: 'customer-form',
            fields: [
                {
                    name: 'code',
                    label: 'Customer Code',
                    type: 'text',
                    required: true,
                    placeholder: 'e.g., CUST-001'
                },
                {
                    name: 'name',
                    label: 'Customer Name',
                    type: 'text',
                    required: true,
                    placeholder: 'Full name or company name'
                },
                {
                    name: 'email',
                    label: 'Email',
                    type: 'email',
                    required: true,
                    placeholder: 'customer@example.com'
                },
                {
                    name: 'phone',
                    label: 'Phone',
                    type: 'text',
                    placeholder: '+1 (555) 000-0000'
                },
                {
                    name: 'tax_id',
                    label: 'Tax ID',
                    type: 'text',
                    placeholder: 'Tax identification number'
                },
                {
                    name: 'credit_limit',
                    label: 'Credit Limit',
                    type: 'number',
                    min: 0,
                    step: 0.01,
                    defaultValue: 0
                },
                {
                    name: 'payment_terms',
                    label: 'Payment Terms (Days)',
                    type: 'number',
                    min: 0,
                    defaultValue: 30,
                    helpText: 'Number of days for payment'
                },
                {
                    name: 'billing_address',
                    label: 'Billing Address',
                    type: 'textarea',
                    rows: 2,
                    fullWidth: true
                },
                {
                    name: 'shipping_address',
                    label: 'Shipping Address',
                    type: 'textarea',
                    rows: 2,
                    fullWidth: true
                },
                {
                    name: 'notes',
                    label: 'Notes',
                    type: 'textarea',
                    rows: 3,
                    fullWidth: true
                },
                {
                    name: 'is_active',
                    label: 'Active',
                    type: 'checkbox',
                    checkboxLabel: 'This customer is active',
                    defaultValue: true
                }
            ],
            values: customer || { is_active: true, payment_terms: 30, credit_limit: 0 },
            submitLabel: customer ? 'Update Customer' : 'Create Customer',
            onSubmit: async (formData) => {
                await this.saveCustomer(formData);
            },
            onCancel: () => this.closeCustomerModal()
        });

        formBuilder.render('customer-form-container');

        if (modal) {
            modal.style.display = 'flex';
        }
    }

    /**
     * Close customer modal
     */
    closeCustomerModal() {
        const modal = document.getElementById('customer-modal');
        if (modal) {
            modal.style.display = 'none';
        }
        this.selectedCustomer = null;
    }

    /**
     * Save customer
     */
    async saveCustomer(formData) {
        try {
            const context = await this.getTenantContext();
            const data = {
                ...formData,
                tenant_id: context.tenant_id,
                company_id: context.company_id
            };

            let response;
            if (this.selectedCustomer) {
                response = await apiFetch(`/financial/customers/${this.selectedCustomer.id}`, {
                    method: 'PUT',
                    body: JSON.stringify(data)
                });
            } else {
                response = await apiFetch('/financial/customers', {
                    method: 'POST',
                    body: JSON.stringify(data)
                });
            }

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to save customer');
            }

            this.showToast(
                this.selectedCustomer ? 'Customer updated successfully' : 'Customer created successfully',
                'success'
            );

            this.closeCustomerModal();
            this.dataTable.refresh();
            await this.loadStats();

        } catch (error) {
            console.error('Error saving customer:', error);
            throw error;
        }
    }

    /**
     * View customer details
     */
    async viewCustomer(customer) {
        try {
            const context = await this.getTenantContext();
            const queryParams = new URLSearchParams({
                tenant_id: context.tenant_id,
                company_id: context.company_id
            });

            const response = await apiFetch(`/financial/customers/${customer.id}?${queryParams.toString()}`);

            if (!response.ok) {
                throw new Error('Failed to load customer details');
            }

            const customerData = await response.json();

            const detailsContainer = document.getElementById('customer-details-content');
            if (detailsContainer) {
                detailsContainer.innerHTML = `
                    <div class="space-y-6">
                        <!-- Basic Information -->
                        <div>
                            <h3 class="text-lg font-semibold text-gray-900 mb-4">Basic Information</h3>
                            <div class="grid grid-cols-2 gap-4">
                                <div>
                                    <p class="text-sm text-gray-600">Customer Code</p>
                                    <p class="text-base font-medium text-gray-900">${customerData.code}</p>
                                </div>
                                <div>
                                    <p class="text-sm text-gray-600">Name</p>
                                    <p class="text-base font-medium text-gray-900">${customerData.name}</p>
                                </div>
                                <div>
                                    <p class="text-sm text-gray-600">Email</p>
                                    <p class="text-base font-medium text-gray-900">${customerData.email}</p>
                                </div>
                                <div>
                                    <p class="text-sm text-gray-600">Phone</p>
                                    <p class="text-base font-medium text-gray-900">${customerData.phone || 'N/A'}</p>
                                </div>
                                <div>
                                    <p class="text-sm text-gray-600">Tax ID</p>
                                    <p class="text-base font-medium text-gray-900">${customerData.tax_id || 'N/A'}</p>
                                </div>
                                <div>
                                    <p class="text-sm text-gray-600">Status</p>
                                    <p class="text-base font-medium ${customerData.is_active ? 'text-green-600' : 'text-gray-600'}">
                                        ${customerData.is_active ? 'Active' : 'Inactive'}
                                    </p>
                                </div>
                            </div>
                        </div>

                        <!-- Financial Information -->
                        <div>
                            <h3 class="text-lg font-semibold text-gray-900 mb-4">Financial Information</h3>
                            <div class="grid grid-cols-2 gap-4">
                                <div>
                                    <p class="text-sm text-gray-600">Credit Limit</p>
                                    <p class="text-base font-medium text-gray-900">${this.formatCurrency(customerData.credit_limit || 0)}</p>
                                </div>
                                <div>
                                    <p class="text-sm text-gray-600">Current Balance</p>
                                    <p class="text-base font-medium text-gray-900">${this.formatCurrency(customerData.balance || 0)}</p>
                                </div>
                                <div>
                                    <p class="text-sm text-gray-600">Payment Terms</p>
                                    <p class="text-base font-medium text-gray-900">${customerData.payment_terms || 0} days</p>
                                </div>
                            </div>
                        </div>

                        <!-- Addresses -->
                        <div>
                            <h3 class="text-lg font-semibold text-gray-900 mb-4">Addresses</h3>
                            <div class="grid grid-cols-2 gap-4">
                                <div>
                                    <p class="text-sm text-gray-600 mb-1">Billing Address</p>
                                    <p class="text-base text-gray-900 whitespace-pre-line">${customerData.billing_address || 'N/A'}</p>
                                </div>
                                <div>
                                    <p class="text-sm text-gray-600 mb-1">Shipping Address</p>
                                    <p class="text-base text-gray-900 whitespace-pre-line">${customerData.shipping_address || 'N/A'}</p>
                                </div>
                            </div>
                        </div>

                        ${customerData.notes ? `
                            <div>
                                <h3 class="text-lg font-semibold text-gray-900 mb-4">Notes</h3>
                                <p class="text-base text-gray-700 whitespace-pre-line">${customerData.notes}</p>
                            </div>
                        ` : ''}
                    </div>
                `;
            }

            const modal = document.getElementById('customer-details-modal');
            if (modal) {
                modal.style.display = 'flex';
            }

        } catch (error) {
            console.error('Error loading customer details:', error);
            this.showToast('Failed to load customer details', 'error');
        }
    }

    /**
     * Close details modal
     */
    closeDetailsModal() {
        const modal = document.getElementById('customer-details-modal');
        if (modal) {
            modal.style.display = 'none';
        }
    }

    /**
     * Edit customer
     */
    editCustomer(customer) {
        this.openCustomerModal(customer);
    }

    /**
     * Delete customer
     */
    deleteCustomer(customer) {
        this.selectedCustomer = customer;

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
        this.selectedCustomer = null;
    }

    /**
     * Confirm delete
     */
    async confirmDelete() {
        if (!this.selectedCustomer) return;

        try {
            const context = await this.getTenantContext();
            const queryParams = new URLSearchParams({
                tenant_id: context.tenant_id,
                company_id: context.company_id
            });

            const response = await apiFetch(`/financial/customers/${this.selectedCustomer.id}?${queryParams.toString()}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to delete customer');
            }

            this.showToast('Customer deleted successfully', 'success');
            this.closeDeleteModal();
            this.dataTable.refresh();
            await this.loadStats();

        } catch (error) {
            console.error('Error deleting customer:', error);
            this.showToast(error.message, 'error');
        }
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
