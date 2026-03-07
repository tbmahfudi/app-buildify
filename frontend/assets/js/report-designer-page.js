/**
 * Report Designer Page Handler
 *
 * Responds to route:loaded events dispatched by app.js after
 * loadTemplate('reports-designer') + loadScript('report-designer-page.js').
 *
 * Supported routes:
 *   reports/designer          → create new report
 *   reports/designer/123      → edit existing report (id = 123)
 */

import { ReportDesigner } from '../../components/report-designer.js';

document.addEventListener('route:loaded', async (event) => {
    const route = event.detail.route;

    // Matches: reports/designer  OR  reports/designer/123
    const match = route.match(/^reports\/designer(?:\/(\d+))?$/);
    if (!match) return;

    const reportId = match[1] ? parseInt(match[1]) : null;

    // Template provides #app-content; replace loading spinner with designer
    const container = document.getElementById('app-content');
    if (!container) return;

    const designer = new ReportDesigner(container, reportId);
    await designer.render();
});
