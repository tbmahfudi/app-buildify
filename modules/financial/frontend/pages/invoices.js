/**
 * Invoices Page - Invoice Management
 */

import { apiFetch } from '../../../../frontend/assets/js/api.js';
import { DataTable } from '../components/data-table.js';
import { FormBuilder } from '../components/form-builder.js';

export class InvoicesPage {
    constructor() {
        this.selectedInvoice = null;
        this.dataTable = null;
        this.filters = {
            status: '',
            date_range: ''
        };
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
        const response = await fetch('/modules/financial/frontend/pages/invoices.html');
        const html = await response.text();

        const container = document.getElementById('app-content');
        if (container) {
            container.innerHTML = html;
        }

        await this.init();
    }

    async init() {
        this.attachEventListeners();
        await this.loadStats();
        this.initializeTable();
    }

    attachEventListeners() {
        document.getElementById('btn-create-invoice')?.addEventListener('click', () => this.openInvoiceModal());
        document.getElementById('btn-close-modal')?.addEventListener('click', () => this.closeInvoiceModal());

        document.getElementById('filter-status')?.addEventListener('change', (e) => {
            this.filters.status = e.target.value;
            this.dataTable?.refresh();
        });

        document.getElementById('filter-date-range')?.addEventListener('change', (e) => {
            this.filters.date_range = e.target.value;
            this.dataTable?.refresh();
        });

        document.getElementById('invoice-modal')?.addEventListener('click', (e) => {
            if (e.target.id === 'invoice-modal') this.closeInvoiceModal();
        });
    }

    async loadStats() {
        try {
            const context = await this.getTenantContext();
            const queryParams = new URLSearchParams({
                tenant_id: context.tenant_id,
                company_id: context.company_id
            });

            const response = await apiFetch(`/financial/invoices/stats?${queryParams.toString()}`);
            if (response.ok) {
                const stats = await response.json();
                document.getElementById('stat-total-invoices').textContent = stats.total_invoices || 0;
                document.getElementById('stat-paid').textContent = this.formatCurrency(stats.paid || 0);
                document.getElementById('stat-pending').textContent = this.formatCurrency(stats.pending || 0);
                document.getElementById('stat-overdue').textContent = this.formatCurrency(stats.overdue || 0);
            }
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    }

    initializeTable() {
        this.dataTable = new DataTable({
            containerId: 'invoices-table-container',
            columns: [
                { field: 'invoice_number', label: 'Invoice #', sortable: true },
                { field: 'customer_name', label: 'Customer', sortable: true },
                {
                    field: 'invoice_date',
                    label: 'Date',
                    sortable: true,
                    formatter: (value) => new Date(value).toLocaleDateString()
                },
                {
                    field: 'due_date',
                    label: 'Due Date',
                    sortable: true,
                    formatter: (value) => new Date(value).toLocaleDateString()
                },
                {
                    field: 'total_amount',
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
                if (this.filters.status) queryParams.append('status', this.filters.status);
                if (this.filters.date_range) queryParams.append('date_range', this.filters.date_range);

                const response = await apiFetch(`/financial/invoices?${queryParams.toString()}`);
                if (!response.ok) throw new Error('Failed to load invoices');

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
                    handler: (row) => this.viewInvoice(row)
                },
                {
                    name: 'edit',
                    icon: 'ph-pencil-simple',
                    title: 'Edit',
                    handler: (row) => this.editInvoice(row),
                    condition: (row) => row.status === 'DRAFT'
                },
                {
                    name: 'send',
                    icon: 'ph-paper-plane-tilt',
                    title: 'Send',
                    handler: (row) => this.sendInvoice(row),
                    condition: (row) => row.status === 'DRAFT'
                }
            ],
            pageSize: 10
        });

        this.dataTable.init();
    }

    openInvoiceModal(invoice = null) {
        this.selectedInvoice = invoice;
        document.getElementById('modal-title').textContent = invoice ? 'Edit Invoice' : 'New Invoice';

        const formBuilder = new FormBuilder({
            formId: 'invoice-form',
            fields: [
                {
                    name: 'customer_id',
                    label: 'Customer',
                    type: 'select',
                    required: true,
                    options: [] // Load from API in real implementation
                },
                {
                    name: 'invoice_date',
                    label: 'Invoice Date',
                    type: 'date',
                    required: true,
                    defaultValue: new Date().toISOString().split('T')[0]
                },
                {
                    name: 'due_date',
                    label: 'Due Date',
                    type: 'date',
                    required: true
                },
                {
                    name: 'description',
                    label: 'Description',
                    type: 'textarea',
                    rows: 3,
                    fullWidth: true
                }
            ],
            values: invoice || {},
            submitLabel: invoice ? 'Update Invoice' : 'Create Invoice',
            onSubmit: async (formData) => {
                await this.saveInvoice(formData);
            },
            onCancel: () => this.closeInvoiceModal()
        });

        formBuilder.render('invoice-form-container');
        document.getElementById('invoice-modal').style.display = 'flex';
    }

    closeInvoiceModal() {
        document.getElementById('invoice-modal').style.display = 'none';
        this.selectedInvoice = null;
    }

    async saveInvoice(formData) {
        try {
            const context = await this.getTenantContext();
            const data = {
                ...formData,
                tenant_id: context.tenant_id,
                company_id: context.company_id
            };

            let response;
            if (this.selectedInvoice) {
                response = await apiFetch(`/financial/invoices/${this.selectedInvoice.id}`, {
                    method: 'PUT',
                    body: JSON.stringify(data)
                });
            } else {
                response = await apiFetch('/financial/invoices', {
                    method: 'POST',
                    body: JSON.stringify(data)
                });
            }

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to save invoice');
            }

            this.showToast(
                this.selectedInvoice ? 'Invoice updated successfully' : 'Invoice created successfully',
                'success'
            );

            this.closeInvoiceModal();
            this.dataTable.refresh();
            await this.loadStats();

        } catch (error) {
            console.error('Error saving invoice:', error);
            throw error;
        }
    }

    viewInvoice(invoice) {
        window.location.hash = `financial/invoices/${invoice.id}`;
    }

    editInvoice(invoice) {
        this.openInvoiceModal(invoice);
    }

    async sendInvoice(invoice) {
        if (!confirm('Send this invoice to the customer?')) return;

        try {
            const context = await this.getTenantContext();
            const queryParams = new URLSearchParams({
                tenant_id: context.tenant_id,
                company_id: context.company_id
            });

            const response = await apiFetch(`/financial/invoices/${invoice.id}/send?${queryParams.toString()}`, {
                method: 'POST'
            });

            if (!response.ok) throw new Error('Failed to send invoice');

            this.showToast('Invoice sent successfully', 'success');
            this.dataTable.refresh();
            await this.loadStats();

        } catch (error) {
            console.error('Error sending invoice:', error);
            this.showToast(error.message, 'error');
        }
    }

    formatStatus(status) {
        const statusConfig = {
            DRAFT: { label: 'Draft', class: 'bg-gray-100 text-gray-800' },
            SENT: { label: 'Sent', class: 'bg-blue-100 text-blue-800' },
            PAID: { label: 'Paid', class: 'bg-green-100 text-green-800' },
            OVERDUE: { label: 'Overdue', class: 'bg-red-100 text-red-800' },
            CANCELLED: { label: 'Cancelled', class: 'bg-gray-100 text-gray-600' }
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
