/**
 * Dashboard Designer Page Handler
 * Handles routing for dashboard designer with dynamic dashboard IDs
 */

import { DashboardDesigner } from '../../components/dashboard-designer.js';

// Listen for dashboard designer routes
document.addEventListener('route:loaded', async (event) => {
    const route = event.detail.route;

    // Check if this is a dashboard designer route
    // Matches: dashboards/designer or dashboards/designer/123
    const match = route.match(/^dashboards\/designer(?:\/(\d+))?$/);

    if (!match) return;

    const dashboardId = match[1] ? parseInt(match[1]) : null;

    // Get or create app-content container
    let container = document.getElementById('app-content');
    if (!container) {
        const content = document.getElementById('content');
        content.innerHTML = '<div id="app-content"></div>';
        container = document.getElementById('app-content');
    }

    // Create and render the designer
    const designer = new DashboardDesigner(container, dashboardId);
    await designer.render();
});
