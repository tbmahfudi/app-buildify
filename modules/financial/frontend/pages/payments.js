/**
 * Payments Page - Payment Management
 */

import { apiFetch } from '../../../../frontend/assets/js/api.js';
import { DataTable } from '../components/data-table.js';
import { FormBuilder } from '../components/form-builder.js';

export class PaymentsPage {
    constructor() {
        this.selectedPayment = null;
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

    async render() {
        const response = await fetch('/modules/financial/frontend/pages/payments.html');
        const html = await response.text();
        document.getElementById('app-content').innerHTML = html;
        await this.init();
    }

    async init() {
        this.attachEventListeners();
        await this.loadStats();
        this.initializeTable();
    }

    attachEventListeners() {
        document.getElementById('btn-create-payment')?.addEventListener('click', () => this.openPaymentModal());
        document.getElementById('btn-close-modal')?.addEventListener('click', () => this.closePaymentModal());
        document.getElementById('payment-modal')?.addEventListener('click', (e) => {
            if (e.target.id === 'payment-modal') this.closePaymentModal();
        });
    }

    async loadStats() {
        try {
            const context = await this.getTenantContext();
            const queryParams = new URLSearchParams({
                tenant_id: context.tenant_id,
                company_id: context.company_id
            });

            const response = await apiFetch(`/financial/payments/stats?${queryParams.toString()}`);
            if (response.ok) {
                const stats = await response.json();
                document.getElementById('stat-total-payments').textContent = stats.total_payments || 0;
                document.getElementById('stat-total-amount').textContent = this.formatCurrency(stats.total_amount || 0);
                document.getElementById('stat-this-month').textContent = this.formatCurrency(stats.this_month || 0);
                document.getElementById('stat-today').textContent = this.formatCurrency(stats.today || 0);
            }
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    }

    initializeTable() {
        this.dataTable = new DataTable({
            containerId: 'payments-table-container',
            columns: [
                { field: 'payment_number', label: 'Payment #', sortable: true },
                { field: 'customer_name', label: 'Customer', sortable: true },
                {
                    field: 'payment_date',
                    label: 'Date',
                    sortable: true,
                    formatter: (value) => new Date(value).toLocaleDateString()
                },
                { field: 'payment_method', label: 'Method', sortable: true },
                {
                    field: 'amount',
                    label: 'Amount',
                    sortable: true,
                    formatter: (value) => this.formatCurrency(value),
                    className: 'text-right'
                },
                {
                    field: 'status',
                    label: 'Status',
                    formatter: (value) => this.formatStatus(value)
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
                if (params.search) queryParams.append('search', params.search);
                if (params.sort_by) {
                    queryParams.append('sort_by', params.sort_by);
                    queryParams.append('sort_dir', params.sort_dir);
                }

                const response = await apiFetch(`/financial/payments?${queryParams.toString()}`);
                if (!response.ok) throw new Error('Failed to load payments');

                const data = await response.json();
                return {
                    data: data.items || data,
                    total: data.total || (data.items ? data.items.length : data.length)
                };
            },
            actions: [
                {
                    name: 'view',
                    icon: 'ph-eye',
                    title: 'View',
                    handler: (row) => this.viewPayment(row)
                },
                {
                    name: 'edit',
                    icon: 'ph-pencil-simple',
                    title: 'Edit',
                    handler: (row) => this.editPayment(row),
                    condition: (row) => row.status !== 'POSTED'
                }
            ],
            pageSize: 10
        });

        this.dataTable.init();
    }

    openPaymentModal(payment = null) {
        this.selectedPayment = payment;
        document.getElementById('modal-title').textContent = payment ? 'Edit Payment' : 'New Payment';

        const formBuilder = new FormBuilder({
            formId: 'payment-form',
            fields: [
                {
                    name: 'customer_id',
                    label: 'Customer',
                    type: 'select',
                    required: true,
                    options: []
                },
                {
                    name: 'payment_date',
                    label: 'Payment Date',
                    type: 'date',
                    required: true,
                    defaultValue: new Date().toISOString().split('T')[0]
                },
                {
                    name: 'amount',
                    label: 'Amount',
                    type: 'number',
                    required: true,
                    min: 0,
                    step: 0.01
                },
                {
                    name: 'payment_method',
                    label: 'Payment Method',
                    type: 'select',
                    required: true,
                    options: [
                        { value: 'CASH', label: 'Cash' },
                        { value: 'CHECK', label: 'Check' },
                        { value: 'BANK_TRANSFER', label: 'Bank Transfer' },
                        { value: 'CREDIT_CARD', label: 'Credit Card' },
                        { value: 'OTHER', label: 'Other' }
                    ]
                },
                {
                    name: 'reference_number',
                    label: 'Reference Number',
                    type: 'text',
                    placeholder: 'Check number, transaction ID, etc.'
                },
                {
                    name: 'notes',
                    label: 'Notes',
                    type: 'textarea',
                    rows: 3,
                    fullWidth: true
                }
            ],
            values: payment || {},
            submitLabel: payment ? 'Update Payment' : 'Create Payment',
            onSubmit: async (formData) => {
                await this.savePayment(formData);
            },
            onCancel: () => this.closePaymentModal()
        });

        formBuilder.render('payment-form-container');
        document.getElementById('payment-modal').style.display = 'flex';
    }

    closePaymentModal() {
        document.getElementById('payment-modal').style.display = 'none';
        this.selectedPayment = null;
    }

    async savePayment(formData) {
        try {
            const context = await this.getTenantContext();
            const data = {
                ...formData,
                tenant_id: context.tenant_id,
                company_id: context.company_id
            };

            let response;
            if (this.selectedPayment) {
                response = await apiFetch(`/financial/payments/${this.selectedPayment.id}`, {
                    method: 'PUT',
                    body: JSON.stringify(data)
                });
            } else {
                response = await apiFetch('/financial/payments', {
                    method: 'POST',
                    body: JSON.stringify(data)
                });
            }

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to save payment');
            }

            this.showToast(
                this.selectedPayment ? 'Payment updated successfully' : 'Payment created successfully',
                'success'
            );

            this.closePaymentModal();
            this.dataTable.refresh();
            await this.loadStats();

        } catch (error) {
            console.error('Error saving payment:', error);
            throw error;
        }
    }

    viewPayment(payment) {
        alert('View payment details: ' + payment.payment_number);
    }

    editPayment(payment) {
        this.openPaymentModal(payment);
    }

    formatStatus(status) {
        const statusConfig = {
            DRAFT: { label: 'Draft', class: 'bg-gray-100 text-gray-800' },
            PENDING: { label: 'Pending', class: 'bg-yellow-100 text-yellow-800' },
            POSTED: { label: 'Posted', class: 'bg-green-100 text-green-800' },
            CANCELLED: { label: 'Cancelled', class: 'bg-red-100 text-red-800' }
        };

        const config = statusConfig[status] || { label: status, class: 'bg-gray-100 text-gray-800' };
        return `<span class="px-2 py-1 text-xs rounded ${config.class}">${config.label}</span>`;
    }

    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg z-50 ${
            type === 'success' ? 'bg-green-600' :
            type === 'error' ? 'bg-red-600' :
            'bg-blue-600'
        } text-white`;
        toast.textContent = message;

        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }
}
