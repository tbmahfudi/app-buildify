async function navigate() {
  const route = location.hash.slice(1) || 'dashboard';
  const el = document.getElementById('content');
  let html;
  try {
    html = await (await fetch(`assets/templates/${route}.html`)).text();
  } catch {
    html = `<div class="alert alert-warning">Template not found for route: ${route}</div>`;
  }
  el.innerHTML = html;
  document.dispatchEvent(new CustomEvent('route:loaded', { detail: { route } }));
}
function initRouter() {
  window.addEventListener('hashchange', navigate);
  navigate();
}
export { initRouter, navigate };
