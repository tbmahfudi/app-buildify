/**
 * Reports List Page
 *
 * Populates the reports-list.html template with live data.
 * Follows the nocode-workflows / nocode-data-model pattern:
 *   app.js  →  loadTemplate('reports-list')  →  loadScript('reports-list-page.js')
 *           →  route:loaded { route: 'reports' }
 *           →  this file responds and fills in the DOM
 */

import { apiFetch } from './api.js';
import { showNotification } from './notifications.js';

let allReports = [];

document.addEventListener('route:loaded', async (event) => {
    if (event.detail.route !== 'reports') return;

    // Wire up static controls already in the template
    document.getElementById('create-report-btn')?.addEventListener('click', () => {
        window.location.hash = '#/reports/designer';
    });

    document.getElementById('rp-search')?.addEventListener('input', applyFilters);
    document.getElementById('rp-type-filter')?.addEventListener('change', applyFilters);

    await loadReports();
});

async function loadReports() {
    try {
        const res = await apiFetch('/reports/definitions?limit=200');
        if (res.ok) {
            const data = await res.json();
            allReports = Array.isArray(data) ? data : (data.items || data.reports || []);
        } else {
            allReports = [];
        }
    } catch (e) {
        console.error('Failed to load reports:', e);
        allReports = [];
    }
    renderGrid(allReports);
}

function applyFilters() {
    const q    = (document.getElementById('rp-search')?.value || '').toLowerCase();
    const type = document.getElementById('rp-type-filter')?.value || '';
    renderGrid(allReports.filter(r => {
        const matchQ    = !q    || r.name.toLowerCase().includes(q) || (r.description || '').toLowerCase().includes(q);
        const matchType = !type || r.report_type === type;
        return matchQ && matchType;
    }));
}

function renderGrid(reports) {
    const grid = document.getElementById('reports-grid');
    if (!grid) return;

    if (reports.length === 0) {
        grid.innerHTML = `
            <div class="col-span-full text-center py-16">
                <i class="ph-duotone ph-chart-bar text-6xl text-gray-300 mb-4"></i>
                <h3 class="text-lg font-semibold text-gray-600 mb-1">No reports found</h3>
                <p class="text-sm text-gray-400 mb-4">Create your first report to get started.</p>
                <button onclick="window.location.hash='#/reports/designer'"
                    class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition text-sm">
                    Create Report
                </button>
            </div>`;
        return;
    }

    const typeColors = {
        tabular:   'bg-blue-100 text-blue-700',
        summary:   'bg-purple-100 text-purple-700',
        chart:     'bg-green-100 text-green-700',
        dashboard: 'bg-orange-100 text-orange-700',
    };
    const typeIcons = {
        tabular:   'ph-table',
        summary:   'ph-sigma',
        chart:     'ph-chart-line',
        dashboard: 'ph-squares-four',
    };

    grid.innerHTML = reports.map(r => {
        const badge    = typeColors[r.report_type] || 'bg-gray-100 text-gray-600';
        const icon     = typeIcons[r.report_type]  || 'ph-file-text';
        const date     = r.updated_at ? new Date(r.updated_at).toLocaleDateString() : '';
        const safeName = (r.name || '').replace(/'/g, "\\'");
        return `
        <div class="bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow flex flex-col">
            <div class="p-5 flex-1">
                <div class="flex items-start justify-between mb-3">
                    <div class="flex items-center gap-2">
                        <i class="ph-duotone ${icon} text-2xl text-blue-500"></i>
                        <span class="text-xs font-medium px-2 py-0.5 rounded-full ${badge}">${r.report_type || 'tabular'}</span>
                    </div>
                    ${r.is_public ? '<span class="text-xs px-2 py-0.5 bg-emerald-50 text-emerald-600 rounded-full">Public</span>' : ''}
                </div>
                <h3 class="font-semibold text-gray-900 mb-1 line-clamp-1">${r.name}</h3>
                ${r.description
                    ? `<p class="text-xs text-gray-500 line-clamp-2 mb-2">${r.description}</p>`
                    : '<p class="text-xs text-gray-400 italic mb-2">No description</p>'}
                <div class="flex items-center gap-3 text-xs text-gray-400 flex-wrap">
                    ${r.base_entity ? `<span><i class="ph ph-database mr-1"></i>${r.base_entity}</span>` : ''}
                    ${date ? `<span><i class="ph ph-calendar mr-1"></i>${date}</span>` : ''}
                </div>
            </div>
            <div class="border-t border-gray-100 px-5 py-3 flex gap-2">
                <button onclick="window.location.hash='#/reports/designer/${r.id}'"
                    class="flex-1 py-1.5 text-sm font-medium text-blue-600 hover:bg-blue-50 rounded-lg transition flex items-center justify-center gap-1">
                    <i class="ph ph-pencil-simple"></i> Edit
                </button>
                <button onclick="window.reportsList_run('${r.id}')"
                    class="flex-1 py-1.5 text-sm font-medium text-green-600 hover:bg-green-50 rounded-lg transition flex items-center justify-center gap-1">
                    <i class="ph ph-play"></i> Run
                </button>
                <button onclick="window.reportsList_delete('${r.id}', '${safeName}')"
                    class="py-1.5 px-3 text-sm font-medium text-red-500 hover:bg-red-50 rounded-lg transition">
                    <i class="ph ph-trash"></i>
                </button>
            </div>
        </div>`;
    }).join('');
}

window.reportsList_run = (reportId) => {
    window.location.hash = `#/report-viewer/${reportId}`;
};

window.reportsList_delete = async (reportId, reportName) => {
    if (!confirm(`Delete report "${reportName}"? This cannot be undone.`)) return;
    try {
        const res = await apiFetch(`/reports/definitions/${reportId}`, { method: 'DELETE' });
        if (res.ok || res.status === 204) {
            showNotification('Report deleted', 'success');
            await loadReports();
        } else {
            showNotification('Failed to delete report', 'error');
        }
    } catch (e) {
        showNotification('Error: ' + e.message, 'error');
    }
};
