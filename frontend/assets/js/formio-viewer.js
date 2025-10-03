export function renderFormioViewer(el, json) {
  if (!window.Formio) {
    el.innerHTML = '<div class="alert alert-warning">Form.io library not loaded.</div>';
    return;
  }
  window.Formio.createForm(el, json, { readOnly: true, noAlerts: true });
}
