/**
 * ModulePage — Lit base for build-optional module pages (ADR: Web Components + Lit).
 *
 * Renders into the LIGHT DOM (createRenderRoot returns `this`) so the platform's
 * Tailwind utility classes, CSS variables and Phosphor icons apply to module markup
 * exactly as they do to the core SPA. Extend this for page custom elements, then build
 * with Vite (see vite.config.js) to a self-contained static bundle under frontend/pages/.
 *
 * This is the OPTIONAL build path. A module may equally ship a plain, no-build
 * ES-module (see ../frontend/module.js). Both deploy as static files — no platform build.
 */
import { LitElement } from 'lit';

export class ModulePage extends LitElement {
    // Light DOM: do not isolate styles in a shadow root — inherit the platform theme.
    createRenderRoot() {
        return this;
    }

    /** Convenience: authenticated fetch that carries platform auth + tenant headers. */
    api(path, options) {
        return window.apiFetch(path, options);
    }
}

export default ModulePage;
