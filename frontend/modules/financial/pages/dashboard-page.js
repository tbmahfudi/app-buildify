/**
 * Financial Dashboard Page
 */

export default class FinancialDashboardPage {
  async render() {
    const container = document.getElementById('app-content');
    if (!container) return;

    container.innerHTML = `
      <div class="financial-dashboard">
        <h1 class="text-2xl font-bold mb-6">Financial Dashboard</h1>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <!-- Revenue Card -->
          <div class="card">
            <div class="card-body">
              <h3 class="text-sm text-gray-600 mb-2">Total Revenue</h3>
              <p class="text-3xl font-bold text-green-600">$0.00</p>
              <p class="text-xs text-gray-500 mt-2">This Month</p>
            </div>
          </div>

          <!-- Expenses Card -->
          <div class="card">
            <div class="card-body">
              <h3 class="text-sm text-gray-600 mb-2">Total Expenses</h3>
              <p class="text-3xl font-bold text-red-600">$0.00</p>
              <p class="text-xs text-gray-500 mt-2">This Month</p>
            </div>
          </div>

          <!-- Profit Card -->
          <div class="card">
            <div class="card-body">
              <h3 class="text-sm text-gray-600 mb-2">Net Profit</h3>
              <p class="text-3xl font-bold text-blue-600">$0.00</p>
              <p class="text-xs text-gray-500 mt-2">This Month</p>
            </div>
          </div>
        </div>

        <!-- Quick Actions -->
        <div class="card mb-6">
          <div class="card-header">
            <h2 class="text-lg font-semibold">Quick Actions</h2>
          </div>
          <div class="card-body">
            <div class="flex gap-3 flex-wrap">
              <a href="#/financial/invoices" class="btn btn-primary">
                🧾 Create Invoice
              </a>
              <a href="#/financial/accounts" class="btn btn-secondary">
                📊 View Accounts
              </a>
              <a href="#/financial/payments" class="btn btn-secondary">
                💳 Record Payment
              </a>
              <a href="#/financial/reports" class="btn btn-secondary">
                📈 View Reports
              </a>
            </div>
          </div>
        </div>

        <!-- Recent Invoices -->
        <div class="card">
          <div class="card-header">
            <h2 class="text-lg font-semibold">Recent Invoices</h2>
          </div>
          <div class="card-body">
            <p class="text-gray-500 text-center py-4">No invoices yet. Create your first invoice to get started.</p>
          </div>
        </div>
      </div>
    `;
  }
}
