import { AuditWidget } from './audit-widget.js';

document.addEventListener('route:loaded', async (e) => {
  if (e.detail.route === 'audit') {
    initAuditPage();
  }
});

function initAuditPage() {
  const container = document.getElementById('audit-container');
  
  const widget = new AuditWidget(container, {
    showFilters: true,
    pageSize: 20
  });
  
  widget.render();

  // Refresh button
  document.getElementById('btn-refresh-audit').onclick = () => {
    widget.refresh();
  };
}