/**
 * Report Designer Page Handler
 * Handles routing for report designer with dynamic report IDs
 */

import { ReportDesigner } from '../../components/report-designer.js';

// Listen for report designer routes
document.addEventListener('route:loaded', async (event) => {
    const route = event.detail.route;

    // Matches: reports/designer  OR  reports/designer/123
    const match = route.match(/^reports\/designer(?:\/(\d+))?$/);
    if (!match) return;

    const reportId = match[1] ? parseInt(match[1]) : null;

    const content = document.getElementById('content');
    if (!content) return;
    content.innerHTML = '<div id="app-content"></div>';
    const container = document.getElementById('app-content');

    const designer = new ReportDesigner(container, reportId);
    await designer.render();
});
