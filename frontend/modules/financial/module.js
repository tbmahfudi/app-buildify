/**
 * Financial Module
 *
 * Main module class for the Financial Management frontend module.
 */

import { BaseModule } from '../../assets/js/core/module-system/base-module.js';

export default class FinancialModule extends BaseModule {
  constructor(manifest) {
    super(manifest);
  }

  async init() {
    await super.init();
    console.log('Financial module initialized');

    // Register dashboard widget if dashboard manager exists
    this.initDashboardWidget();
  }

  initDashboardWidget() {
    if (window.dashboardManager) {
      window.dashboardManager.registerWidget({
        id: 'financial-summary',
        name: 'Financial Summary',
        component: () => import('./components/financial-widget.js'),
        permission: 'financial:accounts:read:company',
        size: 'large'
      });
      console.log('Financial dashboard widget registered');
    }
  }

  /**
   * Get account balance for a specific account
   */
  async getAccountBalance(accountId) {
    try {
      const response = await this.apiRequest(`/accounts/${accountId}`, {
        method: 'GET'
      });

      if (response.ok) {
        const account = await response.json();
        return account.current_balance;
      }

      return null;
    } catch (error) {
      console.error('Error fetching account balance:', error);
      return null;
    }
  }

  /**
   * Get all accounts for a company
   */
  async getAccounts(companyId) {
    try {
      const response = await this.apiRequest(`/accounts?company_id=${companyId}`, {
        method: 'GET'
      });

      if (response.ok) {
        return await response.json();
      }

      return [];
    } catch (error) {
      console.error('Error fetching accounts:', error);
      return [];
    }
  }

  /**
   * Get all invoices for a company
   */
  async getInvoices(companyId) {
    try {
      const response = await this.apiRequest(`/invoices?company_id=${companyId}`, {
        method: 'GET'
      });

      if (response.ok) {
        return await response.json();
      }

      return [];
    } catch (error) {
      console.error('Error fetching invoices:', error);
      return [];
    }
  }

  /**
   * Create a new invoice
   */
  async createInvoice(invoiceData) {
    try {
      const response = await this.apiRequest('/invoices', {
        method: 'POST',
        body: JSON.stringify(invoiceData)
      });

      if (response.ok) {
        return await response.json();
      }

      const error = await response.json();
      throw new Error(error.detail || 'Failed to create invoice');
    } catch (error) {
      console.error('Error creating invoice:', error);
      throw error;
    }
  }
}
