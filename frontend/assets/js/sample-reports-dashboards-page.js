/**
 * Sample Reports and Dashboards Page
 *
 * Displays sample reports and dashboards using the report and dashboard services
 */

import { reportService } from './report-service.js';
import { dashboardService } from './dashboard-service.js';
import { ReportViewer } from '../components/report-viewer.js';
import { DashboardViewer } from '../components/dashboard-viewer.js';
import { showNotification } from './notifications.js';

// Page loads when route is accessed
document.addEventListener('route:loaded', async (event) => {
    if (event.detail.route !== 'sample-reports-dashboards') return;

    const content = document.getElementById('content');
    if (!content) return;

    // Render page structure
    content.innerHTML = `
        <div class="container mx-auto px-6 py-8">
            <!-- Page Header -->
            <div class="mb-8">
                <h1 class="text-3xl font-bold text-gray-800 mb-2">Sample Reports & Dashboards</h1>
                <p class="text-gray-600">Browse and view sample reports and dashboards using the report and dashboard services.</p>
            </div>

            <!-- Tab Navigation -->
            <div class="mb-6">
                <div class="border-b border-gray-200">
                    <nav class="-mb-px flex space-x-8">
                        <button id="tab-reports" class="tab-button active border-b-2 border-blue-500 py-4 px-1 text-sm font-medium text-blue-600">
                            📊 Reports
                        </button>
                        <button id="tab-dashboards" class="tab-button border-b-2 border-transparent py-4 px-1 text-sm font-medium text-gray-500 hover:text-gray-700 hover:border-gray-300">
                            📈 Dashboards
                        </button>
                    </nav>
                </div>
            </div>

            <!-- Reports Tab Content -->
            <div id="reports-content" class="tab-content">
                <div id="reports-list" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
                    <!-- Report cards will be loaded here -->
                </div>
                <div id="report-viewer-container" class="hidden"></div>
            </div>

            <!-- Dashboards Tab Content -->
            <div id="dashboards-content" class="tab-content hidden">
                <div id="dashboards-list" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
                    <!-- Dashboard cards will be loaded here -->
                </div>
                <div id="dashboard-viewer-container" class="hidden"></div>
            </div>
        </div>
    `;

    // Setup tab switching
    setupTabs();

    // Load reports and dashboards
    await loadReports();
    await loadDashboards();
});

function setupTabs() {
    const reportsTab = document.getElementById('tab-reports');
    const dashboardsTab = document.getElementById('tab-dashboards');
    const reportsContent = document.getElementById('reports-content');
    const dashboardsContent = document.getElementById('dashboards-content');

    reportsTab?.addEventListener('click', () => {
        // Update tabs
        reportsTab.classList.add('active', 'border-blue-500', 'text-blue-600');
        reportsTab.classList.remove('border-transparent', 'text-gray-500');
        dashboardsTab.classList.remove('active', 'border-blue-500', 'text-blue-600');
        dashboardsTab.classList.add('border-transparent', 'text-gray-500');

        // Update content
        reportsContent?.classList.remove('hidden');
        dashboardsContent?.classList.add('hidden');
    });

    dashboardsTab?.addEventListener('click', () => {
        // Update tabs
        dashboardsTab.classList.add('active', 'border-blue-500', 'text-blue-600');
        dashboardsTab.classList.remove('border-transparent', 'text-gray-500');
        reportsTab.classList.remove('active', 'border-blue-500', 'text-blue-600');
        reportsTab.classList.add('border-transparent', 'text-gray-500');

        // Update content
        dashboardsContent?.classList.remove('hidden');
        reportsContent?.classList.add('hidden');
    });
}

async function loadReports() {
    const reportsList = document.getElementById('reports-list');
    if (!reportsList) return;

    reportsList.innerHTML = `
        <div class="col-span-full flex justify-center py-12">
            <div class="text-center">
                <div class="inline-block w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                <p class="mt-4 text-gray-600">Loading reports...</p>
            </div>
        </div>
    `;

    try {
        const reports = await reportService.listReportDefinitions({ limit: 50 });

        if (!reports || reports.length === 0) {
            reportsList.innerHTML = `
                <div class="col-span-full text-center py-12">
                    <div class="text-gray-400 text-6xl mb-4">📊</div>
                    <h3 class="text-xl font-semibold text-gray-700 mb-2">No Reports Available</h3>
                    <p class="text-gray-500">There are no sample reports to display at this time.</p>
                </div>
            `;
            return;
        }

        reportsList.innerHTML = reports.map(report => `
            <div class="bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200 overflow-hidden border border-gray-200">
                <div class="p-6">
                    <!-- Report Icon & Category -->
                    <div class="flex items-start justify-between mb-4">
                        <div class="text-4xl">📊</div>
                        ${report.category ? `
                            <span class="px-3 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded-full">
                                ${report.category}
                            </span>
                        ` : ''}
                    </div>

                    <!-- Report Title & Description -->
                    <h3 class="text-lg font-bold text-gray-800 mb-2">${report.name}</h3>
                    ${report.description ? `
                        <p class="text-sm text-gray-600 mb-4 line-clamp-2">${report.description}</p>
                    ` : `
                        <p class="text-sm text-gray-400 mb-4 italic">No description available</p>
                    `}

                    <!-- Report Metadata -->
                    <div class="flex items-center gap-4 text-xs text-gray-500 mb-4">
                        ${report.base_entity ? `
                            <div class="flex items-center gap-1">
                                <span class="font-medium">Entity:</span>
                                <span>${report.base_entity}</span>
                            </div>
                        ` : ''}
                        ${report.parameters && report.parameters.length > 0 ? `
                            <div class="flex items-center gap-1">
                                <span class="font-medium">Parameters:</span>
                                <span>${report.parameters.length}</span>
                            </div>
                        ` : ''}
                    </div>

                    <!-- Actions -->
                    <div class="flex gap-2">
                        <button
                            onclick="viewReport(${report.id})"
                            class="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded transition-colors duration-200">
                            View Report
                        </button>
                        ${report.parameters && report.parameters.length === 0 ? `
                            <button
                                onclick="quickExecuteReport(${report.id})"
                                class="bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded transition-colors duration-200"
                                title="Quick Execute">
                                ▶️
                            </button>
                        ` : ''}
                    </div>
                </div>
            </div>
        `).join('');

    } catch (error) {
        console.error('Error loading reports:', error);
        reportsList.innerHTML = `
            <div class="col-span-full">
                <div class="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg">
                    <p class="font-bold">Error Loading Reports</p>
                    <p class="text-sm mt-1">${error.message}</p>
                </div>
            </div>
        `;
    }
}

async function loadDashboards() {
    const dashboardsList = document.getElementById('dashboards-list');
    if (!dashboardsList) return;

    dashboardsList.innerHTML = `
        <div class="col-span-full flex justify-center py-12">
            <div class="text-center">
                <div class="inline-block w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                <p class="mt-4 text-gray-600">Loading dashboards...</p>
            </div>
        </div>
    `;

    try {
        const dashboards = await dashboardService.listDashboards({ limit: 50 });

        if (!dashboards || dashboards.length === 0) {
            dashboardsList.innerHTML = `
                <div class="col-span-full text-center py-12">
                    <div class="text-gray-400 text-6xl mb-4">📈</div>
                    <h3 class="text-xl font-semibold text-gray-700 mb-2">No Dashboards Available</h3>
                    <p class="text-gray-500">There are no sample dashboards to display at this time.</p>
                </div>
            `;
            return;
        }

        dashboardsList.innerHTML = dashboards.map(dashboard => `
            <div class="bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200 overflow-hidden border border-gray-200">
                <div class="p-6">
                    <!-- Dashboard Icon & Category -->
                    <div class="flex items-start justify-between mb-4">
                        <div class="text-4xl">📈</div>
                        ${dashboard.category ? `
                            <span class="px-3 py-1 bg-purple-100 text-purple-800 text-xs font-medium rounded-full">
                                ${dashboard.category}
                            </span>
                        ` : ''}
                    </div>

                    <!-- Dashboard Title & Description -->
                    <h3 class="text-lg font-bold text-gray-800 mb-2">${dashboard.name}</h3>
                    ${dashboard.description ? `
                        <p class="text-sm text-gray-600 mb-4 line-clamp-2">${dashboard.description}</p>
                    ` : `
                        <p class="text-sm text-gray-400 mb-4 italic">No description available</p>
                    `}

                    <!-- Dashboard Metadata -->
                    <div class="flex items-center gap-4 text-xs text-gray-500 mb-4">
                        ${dashboard.pages ? `
                            <div class="flex items-center gap-1">
                                <span class="font-medium">Pages:</span>
                                <span>${Array.isArray(dashboard.pages) ? dashboard.pages.length : 0}</span>
                            </div>
                        ` : ''}
                        ${dashboard.layout_type ? `
                            <div class="flex items-center gap-1">
                                <span class="font-medium">Layout:</span>
                                <span>${dashboard.layout_type}</span>
                            </div>
                        ` : ''}
                    </div>

                    <!-- Actions -->
                    <button
                        onclick="viewDashboard(${dashboard.id})"
                        class="w-full bg-purple-600 hover:bg-purple-700 text-white font-medium py-2 px-4 rounded transition-colors duration-200">
                        View Dashboard
                    </button>
                </div>
            </div>
        `).join('');

    } catch (error) {
        console.error('Error loading dashboards:', error);
        dashboardsList.innerHTML = `
            <div class="col-span-full">
                <div class="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg">
                    <p class="font-bold">Error Loading Dashboards</p>
                    <p class="text-sm mt-1">${error.message}</p>
                </div>
            </div>
        `;
    }
}

// Global functions for report actions
window.viewReport = async function(reportId) {
    const reportsList = document.getElementById('reports-list');
    const viewerContainer = document.getElementById('report-viewer-container');

    if (!viewerContainer) return;

    // Hide list, show viewer
    if (reportsList) reportsList.classList.add('hidden');
    viewerContainer.classList.remove('hidden');

    // Add back button
    viewerContainer.innerHTML = `
        <div class="mb-4">
            <button onclick="backToReportsList()" class="btn-secondary">
                ← Back to Reports
            </button>
        </div>
        <div id="report-viewer"></div>
    `;

    // Render report viewer
    const reportViewerDiv = document.getElementById('report-viewer');
    if (reportViewerDiv) {
        const viewer = new ReportViewer(reportViewerDiv, reportId);
        await viewer.render();
    }
};

window.quickExecuteReport = async function(reportId) {
    try {
        showNotification('Executing report...', 'info');
        const execution = await reportService.executeReport(reportId, {}, true);

        if (execution.status === 'completed') {
            showNotification(`Report executed successfully! ${execution.row_count} rows returned in ${execution.execution_time_ms}ms`, 'success');
        } else {
            showNotification('Report execution failed', 'error');
        }
    } catch (error) {
        showNotification('Failed to execute report: ' + error.message, 'error');
    }
};

window.backToReportsList = function() {
    const reportsList = document.getElementById('reports-list');
    const viewerContainer = document.getElementById('report-viewer-container');

    if (reportsList) reportsList.classList.remove('hidden');
    if (viewerContainer) {
        viewerContainer.classList.add('hidden');
        viewerContainer.innerHTML = '';
    }
};

// Global functions for dashboard actions
window.viewDashboard = async function(dashboardId) {
    const dashboardsList = document.getElementById('dashboards-list');
    const viewerContainer = document.getElementById('dashboard-viewer-container');

    if (!viewerContainer) return;

    // Hide list, show viewer
    if (dashboardsList) dashboardsList.classList.add('hidden');
    viewerContainer.classList.remove('hidden');

    // Add back button
    viewerContainer.innerHTML = `
        <div class="mb-4">
            <button onclick="backToDashboardsList()" class="btn-secondary">
                ← Back to Dashboards
            </button>
        </div>
        <div id="dashboard-viewer"></div>
    `;

    // Render dashboard viewer
    const dashboardViewerDiv = document.getElementById('dashboard-viewer');
    if (dashboardViewerDiv) {
        const viewer = new DashboardViewer(dashboardViewerDiv, dashboardId);
        await viewer.render();
    }
};

window.backToDashboardsList = function() {
    const dashboardsList = document.getElementById('dashboards-list');
    const viewerContainer = document.getElementById('dashboard-viewer-container');

    if (dashboardsList) dashboardsList.classList.remove('hidden');
    if (viewerContainer) {
        viewerContainer.classList.add('hidden');
        viewerContainer.innerHTML = '';
    }
};
