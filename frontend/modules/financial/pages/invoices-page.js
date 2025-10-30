/**
 * Invoices Page
 */

import { moduleLoader } from '../../../assets/js/core/module-system/module-loader.js';

export default class InvoicesPage {
  constructor() {
    this.invoices = [];
    this.financialModule = moduleLoader.getModule('financial');
  }

  async render() {
    const container = document.getElementById('app-content');
    if (!container) return;

    container.innerHTML = `
      <div class="invoices-page">
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-2xl font-bold">Invoices</h1>
          <button id="create-invoice-btn" class="btn btn-primary">
            ➕ Create Invoice
          </button>
        </div>

        <!-- Status Filter -->
        <div class="tabs mb-6">
          <button class="tab-btn active" data-status="all">All</button>
          <button class="tab-btn" data-status="draft">Draft</button>
          <button class="tab-btn" data-status="sent">Sent</button>
          <button class="tab-btn" data-status="paid">Paid</button>
          <button class="tab-btn" data-status="overdue">Overdue</button>
        </div>

        <div id="invoices-loading" class="text-center py-8">
          <div class="spinner"></div>
          <p>Loading invoices...</p>
        </div>

        <div id="invoices-list" class="hidden">
          <!-- Invoices will be rendered here -->
        </div>
      </div>
    `;

    this.setupEventListeners();
    await this.loadInvoices();
  }

  setupEventListeners() {
    const createBtn = document.getElementById('create-invoice-btn');
    if (createBtn) {
      createBtn.addEventListener('click', () => this.showCreateInvoiceForm());
    }

    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
      btn.addEventListener('click', (e) => {
        const status = e.currentTarget.dataset.status;
        this.filterInvoicesByStatus(status);
      });
    });
  }

  async loadInvoices() {
    try {
      const companyId = localStorage.getItem('current_company_id') || 'demo-company-id';

      if (this.financialModule) {
        this.invoices = await this.financialModule.getInvoices(companyId);
      }

      this.renderInvoices();
    } catch (error) {
      console.error('Error loading invoices:', error);
      document.getElementById('invoices-loading').innerHTML = `
        <div class="alert alert-error">
          Failed to load invoices: ${error.message}
        </div>
      `;
    }
  }

  renderInvoices(filteredInvoices = null) {
    const loading = document.getElementById('invoices-loading');
    const list = document.getElementById('invoices-list');

    loading.classList.add('hidden');
    list.classList.remove('hidden');

    const invoices = filteredInvoices || this.invoices;

    if (invoices.length === 0) {
      list.innerHTML = `
        <div class="card">
          <div class="card-body text-center py-8">
            <p class="text-gray-500">No invoices found. Create your first invoice to get started.</p>
          </div>
        </div>
      `;
      return;
    }

    list.innerHTML = `
      <div class="card">
        <table class="table">
          <thead>
            <tr>
              <th>Invoice #</th>
              <th>Customer</th>
              <th>Date</th>
              <th>Due Date</th>
              <th>Amount</th>
              <th>Paid</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            ${invoices.map(invoice => `
              <tr>
                <td><strong>${invoice.invoice_number}</strong></td>
                <td>${invoice.customer_name}</td>
                <td>${new Date(invoice.invoice_date).toLocaleDateString()}</td>
                <td>${new Date(invoice.due_date).toLocaleDateString()}</td>
                <td class="text-right font-mono">
                  ${invoice.currency} ${invoice.total_amount.toFixed(2)}
                </td>
                <td class="text-right font-mono">
                  ${invoice.currency} ${invoice.paid_amount.toFixed(2)}
                </td>
                <td>
                  <span class="badge ${this.getStatusBadgeClass(invoice.status)}">
                    ${invoice.status}
                  </span>
                </td>
                <td>
                  <button class="btn btn-sm btn-secondary" onclick="invoicesPage.viewInvoice('${invoice.id}')">
                    View
                  </button>
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
  }

  filterInvoicesByStatus(status) {
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.status === status);
    });

    if (status === 'all') {
      this.renderInvoices();
    } else {
      const filtered = this.invoices.filter(inv => inv.status === status);
      this.renderInvoices(filtered);
    }
  }

  getStatusBadgeClass(status) {
    const classes = {
      'draft': 'badge-secondary',
      'sent': 'badge-info',
      'paid': 'badge-success',
      'overdue': 'badge-error',
      'cancelled': 'badge-warning'
    };
    return classes[status] || 'badge-secondary';
  }

  showCreateInvoiceForm() {
    alert('Create invoice form - To be implemented');
    // TODO: Show modal with invoice creation form
  }

  viewInvoice(invoiceId) {
    alert(`View invoice ${invoiceId} - To be implemented`);
    // TODO: Navigate to invoice detail page or show modal
  }
}

window.invoicesPage = new InvoicesPage();
