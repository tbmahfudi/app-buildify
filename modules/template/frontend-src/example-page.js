/**
 * Example built page — a Lit custom element extending ModulePage.
 *
 * Build:  npm run build   -> bundles this + Lit into ../frontend/pages/example-page.js
 * Mount:  a manifest route `{ "component": "pages/example-page.js" }` (relative to the
 *         module frontend/ dir); the page mounts the <template-example-page> element.
 */
import { html } from 'lit';
import { ModulePage } from './base-page.js';

const MODULE_API = '/api/v1/modules/TEMPLATE';

export class TemplateExamplePage extends ModulePage {
    static properties = {
        _items: { state: true },
        _error: { state: true },
        _loading: { state: true },
    };

    constructor() {
        super();
        this._items = [];
        this._error = null;
        this._loading = true;
    }

    connectedCallback() {
        super.connectedCallback();
        this._load();
    }

    async _load() {
        this._loading = true;
        try {
            const data = await this.api(`${MODULE_API}/items`);
            this._items = data.items || [];
            this._error = null;
        } catch (err) {
            this._error = err.message;
        } finally {
            this._loading = false;
        }
    }

    render() {
        return html`
            <div class="page-header">
                <h1 class="page-title">Example Page (Lit, built)</h1>
            </div>
            ${this._loading ? html`<p class="text-gray-500">Loading…</p>` : ''}
            ${this._error ? html`<div class="alert alert-error">${this._error}</div>` : ''}
            ${!this._loading && !this._error
                ? html`<ul class="divide-y">${this._items.map(
                    (i) => html`<li class="py-2">${i.name}</li>`
                  )}</ul>`
                : ''}
        `;
    }
}

customElements.define('template-example-page', TemplateExamplePage);
export default TemplateExamplePage;
