/**
 * Journal Entries Page
 */

import { apiFetch } from '../../../../frontend/assets/js/api.js';
import { DataTable } from '../components/data-table.js';
import { FormBuilder } from '../components/form-builder.js';

export class JournalEntriesPage {
    constructor() {
        this.selectedEntry = null;
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
        const response = await fetch('/modules/financial/frontend/pages/journal-entries.html');
        const html = await response.text();
        document.getElementById('app-content').innerHTML = html;
        await this.init();
    }

    async init() {
        this.attachEventListeners();
        this.initializeTable();
    }

    attachEventListeners() {
        document.getElementById('btn-create-entry')?.addEventListener('click', () => this.openEntryModal());
        document.getElementById('btn-close-modal')?.addEventListener('click', () => this.closeEntryModal());
        document.getElementById('entry-modal')?.addEventListener('click', (e) => {
            if (e.target.id === 'entry-modal') this.closeEntryModal();
        });
    }

    initializeTable() {
        this.dataTable = new DataTable({
            containerId: 'entries-table-container',
            columns: [
                { field: 'entry_number', label: 'Entry #', sortable: true },
                {
                    field: 'entry_date',
                    label: 'Date',
                    sortable: true,
                    formatter: (value) => new Date(value).toLocaleDateString()
                },
                { field: 'description', label: 'Description', sortable: true },
                {
                    field: 'total_debit',
                    label: 'Debit',
                    sortable: true,
                    formatter: (value) => this.formatCurrency(value),
                    className: 'text-right'
                },
                {
                    field: 'total_credit',
                    label: 'Credit',
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

                const response = await apiFetch(`/financial/journal-entries?${queryParams.toString()}`);
                if (!response.ok) throw new Error('Failed to load journal entries');

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
                    handler: (row) => this.viewEntry(row)
                },
                {
                    name: 'edit',
                    icon: 'ph-pencil-simple',
                    title: 'Edit',
                    handler: (row) => this.editEntry(row),
                    condition: (row) => row.status === 'DRAFT'
                },
                {
                    name: 'post',
                    icon: 'ph-check',
                    title: 'Post',
                    handler: (row) => this.postEntry(row),
                    condition: (row) => row.status === 'DRAFT'
                }
            ],
            pageSize: 10
        });

        this.dataTable.init();
    }

    openEntryModal(entry = null) {
        this.selectedEntry = entry;
        document.getElementById('modal-title').textContent = entry ? 'Edit Journal Entry' : 'New Journal Entry';

        const formBuilder = new FormBuilder({
            formId: 'entry-form',
            fields: [
                {
                    name: 'entry_date',
                    label: 'Entry Date',
                    type: 'date',
                    required: true,
                    defaultValue: new Date().toISOString().split('T')[0]
                },
                {
                    name: 'description',
                    label: 'Description',
                    type: 'textarea',
                    required: true,
                    rows: 3,
                    fullWidth: true
                },
                {
                    name: 'reference',
                    label: 'Reference',
                    type: 'text',
                    placeholder: 'Reference number or document'
                }
            ],
            values: entry || {},
            submitLabel: entry ? 'Update Entry' : 'Create Entry',
            onSubmit: async (formData) => {
                await this.saveEntry(formData);
            },
            onCancel: () => this.closeEntryModal()
        });

        formBuilder.render('entry-form-container');
        document.getElementById('entry-modal').style.display = 'flex';
    }

    closeEntryModal() {
        document.getElementById('entry-modal').style.display = 'none';
        this.selectedEntry = null;
    }

    async saveEntry(formData) {
        try {
            const context = await this.getTenantContext();
            const data = {
                ...formData,
                tenant_id: context.tenant_id,
                company_id: context.company_id
            };

            let response;
            if (this.selectedEntry) {
                response = await apiFetch(`/financial/journal-entries/${this.selectedEntry.id}`, {
                    method: 'PUT',
                    body: JSON.stringify(data)
                });
            } else {
                response = await apiFetch('/financial/journal-entries', {
                    method: 'POST',
                    body: JSON.stringify(data)
                });
            }

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to save journal entry');
            }

            this.showToast(
                this.selectedEntry ? 'Journal entry updated successfully' : 'Journal entry created successfully',
                'success'
            );

            this.closeEntryModal();
            this.dataTable.refresh();

        } catch (error) {
            console.error('Error saving entry:', error);
            throw error;
        }
    }

    viewEntry(entry) {
        alert('View journal entry: ' + entry.entry_number);
    }

    editEntry(entry) {
        this.openEntryModal(entry);
    }

    async postEntry(entry) {
        if (!confirm('Post this journal entry? This action cannot be undone.')) return;

        try {
            const context = await this.getTenantContext();
            const queryParams = new URLSearchParams({
                tenant_id: context.tenant_id,
                company_id: context.company_id
            });

            const response = await apiFetch(`/financial/journal-entries/${entry.id}/post?${queryParams.toString()}`, {
                method: 'POST'
            });

            if (!response.ok) throw new Error('Failed to post journal entry');

            this.showToast('Journal entry posted successfully', 'success');
            this.dataTable.refresh();

        } catch (error) {
            console.error('Error posting entry:', error);
            this.showToast(error.message, 'error');
        }
    }

    formatStatus(status) {
        const statusConfig = {
            DRAFT: { label: 'Draft', class: 'bg-gray-100 text-gray-800' },
            POSTED: { label: 'Posted', class: 'bg-green-100 text-green-800' },
            REVERSED: { label: 'Reversed', class: 'bg-red-100 text-red-800' }
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
