/**
 * Chart of Accounts Page
 */

import { moduleLoader } from '../../../assets/js/core/module-system/module-loader.js';

export default class AccountsPage {
  constructor() {
    this.accounts = [];
    this.financialModule = moduleLoader.getModule('financial');
  }

  async render() {
    const container = document.getElementById('app-content');
    if (!container) return;

    container.innerHTML = `
      <div class="accounts-page">
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-2xl font-bold">Chart of Accounts</h1>
          <button id="create-account-btn" class="btn btn-primary">
            ➕ Add Account
          </button>
        </div>

        <!-- Account Type Tabs -->
        <div class="tabs mb-6">
          <button class="tab-btn active" data-type="all">All Accounts</button>
          <button class="tab-btn" data-type="asset">Assets</button>
          <button class="tab-btn" data-type="liability">Liabilities</button>
          <button class="tab-btn" data-type="equity">Equity</button>
          <button class="tab-btn" data-type="revenue">Revenue</button>
          <button class="tab-btn" data-type="expense">Expenses</button>
        </div>

        <div id="accounts-loading" class="text-center py-8">
          <div class="spinner"></div>
          <p>Loading accounts...</p>
        </div>

        <div id="accounts-list" class="hidden">
          <!-- Accounts will be rendered here -->
        </div>
      </div>
    `;

    this.setupEventListeners();
    await this.loadAccounts();
  }

  setupEventListeners() {
    const createBtn = document.getElementById('create-account-btn');
    if (createBtn) {
      createBtn.addEventListener('click', () => this.showCreateAccountForm());
    }

    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
      btn.addEventListener('click', (e) => {
        const type = e.currentTarget.dataset.type;
        this.filterAccountsByType(type);
      });
    });
  }

  async loadAccounts() {
    try {
      // Get current company ID (you would get this from your app state)
      const companyId = localStorage.getItem('current_company_id') || 'demo-company-id';

      if (this.financialModule) {
        this.accounts = await this.financialModule.getAccounts(companyId);
      }

      this.renderAccounts();
    } catch (error) {
      console.error('Error loading accounts:', error);
      document.getElementById('accounts-loading').innerHTML = `
        <div class="alert alert-error">
          Failed to load accounts: ${error.message}
        </div>
      `;
    }
  }

  renderAccounts(filteredAccounts = null) {
    const loading = document.getElementById('accounts-loading');
    const list = document.getElementById('accounts-list');

    loading.classList.add('hidden');
    list.classList.remove('hidden');

    const accounts = filteredAccounts || this.accounts;

    if (accounts.length === 0) {
      list.innerHTML = `
        <div class="card">
          <div class="card-body text-center py-8">
            <p class="text-gray-500">No accounts found. Create your first account to get started.</p>
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
              <th>Account Code</th>
              <th>Account Name</th>
              <th>Type</th>
              <th>Balance</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            ${accounts.map(account => `
              <tr>
                <td><strong>${account.code}</strong></td>
                <td>${account.name}</td>
                <td><span class="badge">${account.account_type}</span></td>
                <td class="text-right font-mono">
                  ${account.currency} ${account.current_balance.toFixed(2)}
                </td>
                <td>
                  <span class="badge ${account.is_active ? 'badge-success' : 'badge-error'}">
                    ${account.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td>
                  <button class="btn btn-sm btn-secondary" onclick="accountsPage.editAccount('${account.id}')">
                    Edit
                  </button>
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
  }

  filterAccountsByType(type) {
    // Update active tab
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.type === type);
    });

    if (type === 'all') {
      this.renderAccounts();
    } else {
      const filtered = this.accounts.filter(acc => acc.account_type === type);
      this.renderAccounts(filtered);
    }
  }

  showCreateAccountForm() {
    alert('Create account form - To be implemented');
    // TODO: Show modal with account creation form
  }

  editAccount(accountId) {
    alert(`Edit account ${accountId} - To be implemented`);
    // TODO: Show modal with account edit form
  }
}

// Make available globally for onclick handlers
window.accountsPage = new AccountsPage();
