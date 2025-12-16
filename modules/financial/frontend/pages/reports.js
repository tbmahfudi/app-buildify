/**
 * Financial Reports Page
 */

import { apiFetch } from '/assets/js/api.js';

export class ReportsPage {
    constructor() {
        this.currentReport = 'balance-sheet';
        this.reportData = null;
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
        const response = await fetch('/modules/financial/pages/reports.html');
        const html = await response.text();
        document.getElementById('app-content').innerHTML = html;
        await this.init();
    }

    async init() {
        this.attachEventListeners();
        this.setDefaultDates();
    }

    attachEventListeners() {
        // Tab switching
        document.querySelectorAll('.report-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                this.switchReport(e.target.dataset.report);
            });
        });

        // Period selector
        document.getElementById('filter-period')?.addEventListener('change', (e) => {
            this.applyPeriod(e.target.value);
        });

        // Generate button
        document.getElementById('btn-generate-report')?.addEventListener('click', () => {
            this.generateReport();
        });

        // Export button
        document.getElementById('btn-export-report')?.addEventListener('click', () => {
            this.exportReport();
        });

        // Print button
        document.getElementById('btn-print-report')?.addEventListener('click', () => {
            this.printReport();
        });
    }

    setDefaultDates() {
        const today = new Date();
        const yearStart = new Date(today.getFullYear(), 0, 1);

        document.getElementById('filter-date-from').value = yearStart.toISOString().split('T')[0];
        document.getElementById('filter-date-to').value = today.toISOString().split('T')[0];
    }

    switchReport(reportType) {
        this.currentReport = reportType;

        // Update tab styling
        document.querySelectorAll('.report-tab').forEach(tab => {
            if (tab.dataset.report === reportType) {
                tab.classList.add('active', 'border-blue-600', 'text-blue-600');
                tab.classList.remove('border-transparent', 'text-gray-600');
            } else {
                tab.classList.remove('active', 'border-blue-600', 'text-blue-600');
                tab.classList.add('border-transparent', 'text-gray-600');
            }
        });

        // Clear report container
        document.getElementById('report-container').innerHTML = `
            <div class="text-center py-12">
                <i class="ph-duotone ph-chart-line text-6xl text-gray-300 mb-4"></i>
                <p class="text-gray-500 text-lg">Click Generate to view the report</p>
            </div>
        `;
    }

    applyPeriod(period) {
        const today = new Date();
        let dateFrom, dateTo;

        switch (period) {
            case 'today':
                dateFrom = dateTo = today;
                break;
            case 'yesterday':
                dateFrom = dateTo = new Date(today.setDate(today.getDate() - 1));
                break;
            case 'this_week':
                const firstDay = today.getDate() - today.getDay();
                dateFrom = new Date(today.setDate(firstDay));
                dateTo = new Date();
                break;
            case 'this_month':
                dateFrom = new Date(today.getFullYear(), today.getMonth(), 1);
                dateTo = new Date();
                break;
            case 'this_quarter':
                const quarter = Math.floor(today.getMonth() / 3);
                dateFrom = new Date(today.getFullYear(), quarter * 3, 1);
                dateTo = new Date();
                break;
            case 'this_year':
                dateFrom = new Date(today.getFullYear(), 0, 1);
                dateTo = new Date();
                break;
            case 'last_month':
                dateFrom = new Date(today.getFullYear(), today.getMonth() - 1, 1);
                dateTo = new Date(today.getFullYear(), today.getMonth(), 0);
                break;
            case 'last_quarter':
                const lastQuarter = Math.floor(today.getMonth() / 3) - 1;
                dateFrom = new Date(today.getFullYear(), lastQuarter * 3, 1);
                dateTo = new Date(today.getFullYear(), lastQuarter * 3 + 3, 0);
                break;
            case 'last_year':
                dateFrom = new Date(today.getFullYear() - 1, 0, 1);
                dateTo = new Date(today.getFullYear() - 1, 11, 31);
                break;
            default:
                return;
        }

        if (dateFrom) {
            document.getElementById('filter-date-from').value = dateFrom.toISOString().split('T')[0];
        }
        if (dateTo) {
            document.getElementById('filter-date-to').value = dateTo.toISOString().split('T')[0];
        }
    }

    async generateReport() {
        const dateFrom = document.getElementById('filter-date-from').value;
        const dateTo = document.getElementById('filter-date-to').value;

        if (!dateFrom || !dateTo) {
            this.showToast('Please select date range', 'error');
            return;
        }

        const container = document.getElementById('report-container');
        container.innerHTML = `
            <div class="text-center py-12">
                <div class="inline-block w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mb-4"></div>
                <p class="text-gray-600">Generating report...</p>
            </div>
        `;

        try {
            const context = await this.getTenantContext();
            const queryParams = new URLSearchParams({
                tenant_id: context.tenant_id,
                company_id: context.company_id,
                date_from: dateFrom,
                date_to: dateTo
            });

            const response = await apiFetch(`/financial/reports/${this.currentReport}?${queryParams.toString()}`);

            if (!response.ok) {
                throw new Error('Failed to generate report');
            }

            this.reportData = await response.json();
            this.renderReport();

        } catch (error) {
            console.error('Error generating report:', error);
            container.innerHTML = `
                <div class="text-center py-12">
                    <i class="ph-duotone ph-warning-circle text-6xl text-red-400 mb-4"></i>
                    <p class="text-red-600 text-lg">Error generating report</p>
                    <p class="text-gray-500 text-sm mt-2">${error.message}</p>
                </div>
            `;
        }
    }

    renderReport() {
        const container = document.getElementById('report-container');

        if (!this.reportData) {
            container.innerHTML = `
                <div class="text-center py-12">
                    <i class="ph-duotone ph-database text-6xl text-gray-300 mb-4"></i>
                    <p class="text-gray-500 text-lg">No data available</p>
                </div>
            `;
            return;
        }

        const reportTitle = this.getReportTitle(this.currentReport);
        const dateFrom = document.getElementById('filter-date-from').value;
        const dateTo = document.getElementById('filter-date-to').value;

        let reportHtml = `
            <div class="report-header mb-6">
                <h2 class="text-2xl font-bold text-gray-900">${reportTitle}</h2>
                <p class="text-gray-600 mt-1">
                    For the period ${new Date(dateFrom).toLocaleDateString()} to ${new Date(dateTo).toLocaleDateString()}
                </p>
            </div>

            <div class="report-content">
                ${this.renderReportContent()}
            </div>
        `;

        container.innerHTML = reportHtml;
    }

    renderReportContent() {
        switch (this.currentReport) {
            case 'balance-sheet':
                return this.renderBalanceSheet();
            case 'income-statement':
                return this.renderIncomeStatement();
            case 'cash-flow':
                return this.renderCashFlow();
            case 'trial-balance':
                return this.renderTrialBalance();
            case 'aging':
                return this.renderAgingReport();
            default:
                return '<p>Report not implemented</p>';
        }
    }

    renderBalanceSheet() {
        return `
            <div class="space-y-6">
                <div>
                    <h3 class="text-lg font-semibold text-gray-900 mb-3">Assets</h3>
                    <table class="w-full">
                        <tbody>
                            ${this.renderReportSection(this.reportData.assets || [])}
                            <tr class="font-bold border-t-2 border-gray-900">
                                <td class="py-2">Total Assets</td>
                                <td class="py-2 text-right">${this.formatCurrency(this.reportData.total_assets || 0)}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <div>
                    <h3 class="text-lg font-semibold text-gray-900 mb-3">Liabilities</h3>
                    <table class="w-full">
                        <tbody>
                            ${this.renderReportSection(this.reportData.liabilities || [])}
                            <tr class="font-bold border-t-2 border-gray-900">
                                <td class="py-2">Total Liabilities</td>
                                <td class="py-2 text-right">${this.formatCurrency(this.reportData.total_liabilities || 0)}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <div>
                    <h3 class="text-lg font-semibold text-gray-900 mb-3">Equity</h3>
                    <table class="w-full">
                        <tbody>
                            ${this.renderReportSection(this.reportData.equity || [])}
                            <tr class="font-bold border-t-2 border-gray-900">
                                <td class="py-2">Total Equity</td>
                                <td class="py-2 text-right">${this.formatCurrency(this.reportData.total_equity || 0)}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }

    renderIncomeStatement() {
        return `
            <div class="space-y-6">
                <div>
                    <h3 class="text-lg font-semibold text-gray-900 mb-3">Revenue</h3>
                    <table class="w-full">
                        <tbody>
                            ${this.renderReportSection(this.reportData.revenue || [])}
                            <tr class="font-bold border-t border-gray-300">
                                <td class="py-2">Total Revenue</td>
                                <td class="py-2 text-right">${this.formatCurrency(this.reportData.total_revenue || 0)}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <div>
                    <h3 class="text-lg font-semibold text-gray-900 mb-3">Expenses</h3>
                    <table class="w-full">
                        <tbody>
                            ${this.renderReportSection(this.reportData.expenses || [])}
                            <tr class="font-bold border-t border-gray-300">
                                <td class="py-2">Total Expenses</td>
                                <td class="py-2 text-right">${this.formatCurrency(this.reportData.total_expenses || 0)}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <div class="pt-4 border-t-2 border-gray-900">
                    <table class="w-full">
                        <tbody>
                            <tr class="text-xl font-bold">
                                <td class="py-2">Net Income</td>
                                <td class="py-2 text-right ${(this.reportData.net_income || 0) >= 0 ? 'text-green-600' : 'text-red-600'}">
                                    ${this.formatCurrency(this.reportData.net_income || 0)}
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }

    renderCashFlow() {
        return `
            <div class="space-y-6">
                <div>
                    <h3 class="text-lg font-semibold text-gray-900 mb-3">Operating Activities</h3>
                    <table class="w-full">
                        <tbody>
                            ${this.renderReportSection(this.reportData.operating || [])}
                            <tr class="font-bold border-t border-gray-300">
                                <td class="py-2">Net Cash from Operating</td>
                                <td class="py-2 text-right">${this.formatCurrency(this.reportData.total_operating || 0)}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <div>
                    <h3 class="text-lg font-semibold text-gray-900 mb-3">Investing Activities</h3>
                    <table class="w-full">
                        <tbody>
                            ${this.renderReportSection(this.reportData.investing || [])}
                            <tr class="font-bold border-t border-gray-300">
                                <td class="py-2">Net Cash from Investing</td>
                                <td class="py-2 text-right">${this.formatCurrency(this.reportData.total_investing || 0)}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <div>
                    <h3 class="text-lg font-semibold text-gray-900 mb-3">Financing Activities</h3>
                    <table class="w-full">
                        <tbody>
                            ${this.renderReportSection(this.reportData.financing || [])}
                            <tr class="font-bold border-t border-gray-300">
                                <td class="py-2">Net Cash from Financing</td>
                                <td class="py-2 text-right">${this.formatCurrency(this.reportData.total_financing || 0)}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <div class="pt-4 border-t-2 border-gray-900">
                    <table class="w-full">
                        <tbody>
                            <tr class="text-xl font-bold">
                                <td class="py-2">Net Change in Cash</td>
                                <td class="py-2 text-right ${(this.reportData.net_change || 0) >= 0 ? 'text-green-600' : 'text-red-600'}">
                                    ${this.formatCurrency(this.reportData.net_change || 0)}
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }

    renderTrialBalance() {
        return `
            <table class="w-full">
                <thead class="bg-gray-50">
                    <tr>
                        <th class="px-4 py-3 text-left text-sm font-semibold text-gray-700">Account</th>
                        <th class="px-4 py-3 text-right text-sm font-semibold text-gray-700">Debit</th>
                        <th class="px-4 py-3 text-right text-sm font-semibold text-gray-700">Credit</th>
                    </tr>
                </thead>
                <tbody>
                    ${(this.reportData.accounts || []).map(account => `
                        <tr class="border-b border-gray-200">
                            <td class="px-4 py-2">${account.name}</td>
                            <td class="px-4 py-2 text-right">${account.debit ? this.formatCurrency(account.debit) : '-'}</td>
                            <td class="px-4 py-2 text-right">${account.credit ? this.formatCurrency(account.credit) : '-'}</td>
                        </tr>
                    `).join('')}
                    <tr class="font-bold border-t-2 border-gray-900">
                        <td class="px-4 py-3">Total</td>
                        <td class="px-4 py-3 text-right">${this.formatCurrency(this.reportData.total_debit || 0)}</td>
                        <td class="px-4 py-3 text-right">${this.formatCurrency(this.reportData.total_credit || 0)}</td>
                    </tr>
                </tbody>
            </table>
        `;
    }

    renderAgingReport() {
        return `
            <table class="w-full">
                <thead class="bg-gray-50">
                    <tr>
                        <th class="px-4 py-3 text-left text-sm font-semibold text-gray-700">Customer</th>
                        <th class="px-4 py-3 text-right text-sm font-semibold text-gray-700">Current</th>
                        <th class="px-4 py-3 text-right text-sm font-semibold text-gray-700">1-30 Days</th>
                        <th class="px-4 py-3 text-right text-sm font-semibold text-gray-700">31-60 Days</th>
                        <th class="px-4 py-3 text-right text-sm font-semibold text-gray-700">61-90 Days</th>
                        <th class="px-4 py-3 text-right text-sm font-semibold text-gray-700">Over 90</th>
                        <th class="px-4 py-3 text-right text-sm font-semibold text-gray-700">Total</th>
                    </tr>
                </thead>
                <tbody>
                    ${(this.reportData.customers || []).map(customer => `
                        <tr class="border-b border-gray-200">
                            <td class="px-4 py-2">${customer.name}</td>
                            <td class="px-4 py-2 text-right">${this.formatCurrency(customer.current || 0)}</td>
                            <td class="px-4 py-2 text-right">${this.formatCurrency(customer.days_1_30 || 0)}</td>
                            <td class="px-4 py-2 text-right">${this.formatCurrency(customer.days_31_60 || 0)}</td>
                            <td class="px-4 py-2 text-right">${this.formatCurrency(customer.days_61_90 || 0)}</td>
                            <td class="px-4 py-2 text-right">${this.formatCurrency(customer.over_90 || 0)}</td>
                            <td class="px-4 py-2 text-right font-semibold">${this.formatCurrency(customer.total || 0)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    }

    renderReportSection(items) {
        return items.map(item => `
            <tr class="border-b border-gray-200">
                <td class="py-2 ${item.indent ? 'pl-' + (item.indent * 4) : ''}">${item.name}</td>
                <td class="py-2 text-right">${this.formatCurrency(item.amount || 0)}</td>
            </tr>
        `).join('');
    }

    getReportTitle(reportType) {
        const titles = {
            'balance-sheet': 'Balance Sheet',
            'income-statement': 'Income Statement',
            'cash-flow': 'Cash Flow Statement',
            'trial-balance': 'Trial Balance',
            'aging': 'Accounts Receivable Aging'
        };
        return titles[reportType] || 'Report';
    }

    exportReport() {
        this.showToast('Export functionality coming soon', 'info');
    }

    printReport() {
        window.print();
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
