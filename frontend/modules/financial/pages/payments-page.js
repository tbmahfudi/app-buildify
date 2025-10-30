/**
 * Payments Page
 * Placeholder for payments functionality
 */

export default class PaymentsPage {
  async render() {
    const container = document.getElementById('app-content');
    if (!container) return;

    container.innerHTML = `
      <div class="payments-page">
        <h1 class="text-2xl font-bold mb-6">Payments</h1>
        <div class="card">
          <div class="card-body text-center py-12">
            <p class="text-gray-500 text-lg">Payments module coming soon...</p>
            <p class="text-sm text-gray-400 mt-2">
              This page will display payment records and allow you to record new payments.
            </p>
          </div>
        </div>
      </div>
    `;
  }
}
