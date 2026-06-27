/**
 * No-code entity page — contract-conformant wrapper (ADR Step 3 convergence).
 *
 * Adapts the existing no-code runtime (`dynamicRouteRegistry` + `DynamicTable`
 * + `DynamicForm`) to the Step-1 module-frontend page-element contract so that
 * a no-code-generated CRUD page mounts/destroys EXACTLY like a hand-coded
 * module page — same lifecycle, same `#app-content` container, same teardown.
 *
 * It does NOT reimplement any CRUD: it delegates to
 * `dynamicRouteRegistry.handleRoute('dynamic/{entity}/{action...}', container)`,
 * which is the identical code path the legacy `#/dynamic/...` routes use today.
 *
 * Two equivalent shapes are exported (per the ADR):
 *   (a) custom element `<nocode-entity-page entity="..." action="...">`
 *   (b) light-DOM page class `NocodeEntityPage` ({ render(container), destroy() })
 *
 * Both render into `#app-content` (light DOM) so platform Tailwind + Phosphor
 * icons work verbatim — no Shadow DOM, no build.
 */

import { dynamicRouteRegistry } from './dynamic-route-registry.js';

/**
 * Build the legacy dynamic-route string the no-code runtime understands.
 * @param {string} entity
 * @param {string} [action='list'] - list | create | detail | edit
 * @param {string} [id]            - record id for detail/edit
 * @returns {string}
 */
function buildDynamicRoute(entity, action, id) {
  const act = action || 'list';
  switch (act) {
    case 'create':
      return `dynamic/${entity}/create`;
    case 'detail':
      return `dynamic/${entity}/${id}`;
    case 'edit':
      return `dynamic/${entity}/${id}/edit`;
    case 'list':
    default:
      return `dynamic/${entity}/list`;
  }
}

/**
 * Render a published no-code entity into a container via the existing runtime.
 * Renders a clean inline error card (never a raw 404 / blank screen) on failure.
 *
 * @param {HTMLElement} container
 * @param {{entity:string, action?:string, id?:string}} opts
 * @returns {Promise<boolean>} true if the no-code runtime handled it
 */
export async function renderNocodeEntity(container, opts) {
  const { entity, action, id } = opts || {};
  if (!container) return false;

  if (!entity) {
    container.innerHTML = `
      <div class="max-w-2xl mx-auto mt-8 p-6 bg-red-50 border border-red-200 rounded-lg">
        <h3 class="text-lg font-semibold text-red-900 mb-2">No-code page misconfigured</h3>
        <p class="text-red-700">This route declares a no-code page but no <code>entity</code> was provided.</p>
      </div>`;
    return false;
  }

  const dynamicRoute = buildDynamicRoute(entity, action, id);
  try {
    const handled = await dynamicRouteRegistry.handleRoute(dynamicRoute, container);
    if (!handled) {
      container.innerHTML = `
        <div class="max-w-2xl mx-auto mt-8 p-6 bg-amber-50 border border-amber-200 rounded-lg">
          <h3 class="text-lg font-semibold text-amber-900 mb-2">Entity unavailable</h3>
          <p class="text-amber-800">The no-code entity <code>${entity}</code> could not be rendered.</p>
        </div>`;
    }
    return handled;
  } catch (err) {
    console.error(`NocodeEntityPage: failed to render entity "${entity}":`, err);
    container.innerHTML = `
      <div class="max-w-2xl mx-auto mt-8 p-6 bg-red-50 border border-red-200 rounded-lg">
        <h3 class="text-lg font-semibold text-red-900 mb-2">This page could not be loaded</h3>
        <p class="text-red-700">The no-code page for <code>${entity}</code> failed to load.</p>
      </div>`;
    return false;
  }
}

/**
 * Light-DOM page class conforming to the Step-1 page contract.
 *
 * Usage (programmatic / module handler):
 *   const page = new NocodeEntityPage({ entity: 'customers', action: 'list' });
 *   await page.render(document.getElementById('app-content'));
 *   // ... on route change:
 *   await page.destroy();
 */
export class NocodeEntityPage {
  /**
   * @param {{entity:string, action?:string, id?:string}} [opts]
   */
  constructor(opts = {}) {
    this.entity = opts.entity;
    this.action = opts.action || 'list';
    this.id = opts.id;
    this._container = null;
  }

  /**
   * @param {HTMLElement} [container] - defaults to #app-content (shell mount point)
   */
  async render(container) {
    this._container = container || document.getElementById('app-content');
    await renderNocodeEntity(this._container, {
      entity: this.entity,
      action: this.action,
      id: this.id,
    });
  }

  async destroy() {
    // The no-code runtime renders plain innerHTML with no long-lived globals;
    // clearing the container is sufficient teardown for symmetry with module pages.
    if (this._container) {
      this._container.innerHTML = '';
      this._container = null;
    }
  }
}

/**
 * Custom element `<nocode-entity-page entity="..." action="..." record-id="...">`.
 * connectedCallback() renders into itself (light DOM); disconnectedCallback()
 * is the native teardown the shell triggers by removing the element.
 */
export class NocodeEntityPageElement extends HTMLElement {
  static get observedAttributes() {
    return ['entity', 'action', 'record-id'];
  }

  connectedCallback() {
    // Render into the element's own light children (no Shadow DOM).
    this._render();
  }

  attributeChangedCallback() {
    if (this.isConnected) this._render();
  }

  disconnectedCallback() {
    // Native teardown — nothing long-lived to release; clear markup.
    this.innerHTML = '';
  }

  async _render() {
    const entity = this.getAttribute('entity');
    const action = this.getAttribute('action') || 'list';
    const id = this.getAttribute('record-id') || undefined;
    await renderNocodeEntity(this, { entity, action, id });
  }
}

// Register the custom element once (idempotent — safe across re-imports).
if (typeof window !== 'undefined' && window.customElements
    && !customElements.get('nocode-entity-page')) {
  customElements.define('nocode-entity-page', NocodeEntityPageElement);
}

export default NocodeEntityPage;
