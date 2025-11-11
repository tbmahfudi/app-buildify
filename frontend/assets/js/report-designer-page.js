/**
 * Report Designer Page Handler
 * Handles routing for report designer with dynamic report IDs
 */

import { ReportDesigner } from '../../components/report-designer.js';

// Listen for report designer routes
document.addEventListener('route:loaded', async (event) => {
    const route = event.detail.route;

    // Check if this is a report designer route
    // Matches: reports/designer or reports/designer/123
    const match = route.match(/^reports\/designer(?:\/(\d+))?$/);

    if (!match) return;

    const reportId = match[1] ? parseInt(match[1]) : null;

    // Get or create app-content container
    let container = document.getElementById('app-content');
    if (!container) {
        const content = document.getElementById('content');
        content.innerHTML = '<div id="app-content"></div>';
        container = document.getElementById('app-content');
    }

    // Create and render the designer
    const designer = new ReportDesigner(container, reportId);
    await designer.render();
});
