import { defineConfig } from 'vite';
import { resolve } from 'path';
import { fileURLToPath } from 'url';

const __dirname = fileURLToPath(new URL('.', import.meta.url));

/**
 * Build-optional module bundling (ADR: static-deployable micro-frontends).
 *
 * Compiles Lit page sources in frontend-src/ into self-contained ES bundles under
 * frontend/pages/ (Lit is inlined, so the output is a plain static .js nginx serves at
 * /modules/TEMPLATE/pages/<name>.js). No SSR, no Node at request time, no platform build.
 *
 * emptyOutDir:false so the built bundles coexist with any hand-authored no-build files
 * already in frontend/.
 */
export default defineConfig({
    build: {
        outDir: resolve(__dirname, 'frontend/pages'),
        emptyOutDir: false,
        target: 'es2020',
        lib: {
            entry: resolve(__dirname, 'frontend-src/example-page.js'),
            formats: ['es'],
            fileName: () => 'example-page.js',
        },
        rollupOptions: {
            output: { inlineDynamicImports: true },
        },
    },
});
