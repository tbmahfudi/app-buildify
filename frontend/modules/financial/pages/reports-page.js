/**
 * Financial Reports Page
 * Placeholder for reporting functionality
 */

export default class ReportsPage {
  async render() {
    const container = document.getElementById('app-content');
    if (!container) return;

    container.innerHTML = `
      <div class="reports-page">
        <h1 class="text-2xl font-bold mb-6">Financial Reports</h1>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <!-- Profit & Loss -->
          <div class="card">
            <div class="card-header">
              <h3 class="font-semibold">Profit & Loss</h3>
            </div>
            <div class="card-body">
              <p class="text-sm text-gray-600 mb-4">
                View income and expenses over a period
              </p>
              <button class="btn btn-secondary w-full" disabled>
                Generate Report
              </button>
            </div>
          </div>

          <!-- Balance Sheet -->
          <div class="card">
            <div class="card-header">
              <h3 class="font-semibold">Balance Sheet</h3>
            </div>
            <div class="card-body">
              <p class="text-sm text-gray-600 mb-4">
                View assets, liabilities, and equity
              </p>
              <button class="btn btn-secondary w-full" disabled>
                Generate Report
              </button>
            </div>
          </div>

          <!-- Cash Flow -->
          <div class="card">
            <div class="card-header">
              <h3 class="font-semibold">Cash Flow</h3>
            </div>
            <div class="card-body">
              <p class="text-sm text-gray-600 mb-4">
                View cash inflows and outflows
              </p>
              <button class="btn btn-secondary w-full" disabled>
                Generate Report
              </button>
            </div>
          </div>

          <!-- Accounts Receivable -->
          <div class="card">
            <div class="card-header">
              <h3 class="font-semibold">Accounts Receivable</h3>
            </div>
            <div class="card-body">
              <p class="text-sm text-gray-600 mb-4">
                View outstanding invoices
              </p>
              <button class="btn btn-secondary w-full" disabled>
                Generate Report
              </button>
            </div>
          </div>

          <!-- Trial Balance -->
          <div class="card">
            <div class="card-header">
              <h3 class="font-semibold">Trial Balance</h3>
            </div>
            <div class="card-body">
              <p class="text-sm text-gray-600 mb-4">
                View all account balances
              </p>
              <button class="btn btn-secondary w-full" disabled>
                Generate Report
              </button>
            </div>
          </div>

          <!-- General Ledger -->
          <div class="card">
            <div class="card-header">
              <h3 class="font-semibold">General Ledger</h3>
            </div>
            <div class="card-body">
              <p class="text-sm text-gray-600 mb-4">
                View all transactions by account
              </p>
              <button class="btn btn-secondary w-full" disabled>
                Generate Report
              </button>
            </div>
          </div>
        </div>

        <div class="alert alert-info mt-6">
          <strong>Coming Soon:</strong> Financial reporting features will be available in a future update.
        </div>
      </div>
    `;
  }
}
