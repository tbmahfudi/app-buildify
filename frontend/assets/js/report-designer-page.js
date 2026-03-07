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

    // Wire template tab nav to designer step navigation
    document.querySelectorAll('.tab-btn[data-step]').forEach(btn => {
        btn.addEventListener('click', () => {
            const step = parseInt(btn.dataset.step);
            if (!isNaN(step)) {
                designer.goToStep(step);
                document.querySelectorAll('.tab-btn').forEach(b => {
                    const active = b === btn;
                    b.classList.toggle('border-blue-600', active);
                    b.classList.toggle('text-blue-600', active);
                    b.classList.toggle('border-transparent', !active);
                    b.classList.toggle('text-gray-500', !active);
                });
            }
        });
    });

    // Keep tab nav in sync when designer moves between steps
    document.addEventListener('designer:step-changed', (e) => {
        const step = e.detail?.step;
        document.querySelectorAll('.tab-btn[data-step]').forEach(btn => {
            const active = parseInt(btn.dataset.step) === step;
            btn.classList.toggle('border-blue-600', active);
            btn.classList.toggle('text-blue-600', active);
            btn.classList.toggle('border-transparent', !active);
            btn.classList.toggle('text-gray-500', !active);
        });
    });
});
