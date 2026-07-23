/**
 * Document Management (DMS) — Frontend module entry.
 *
 * Follows the platform module loader contract: default-exported class with a
 * manifest-aware constructor and async init(); routes lazily import page
 * modules. Auth token comes from localStorage (set by the platform shell).
 */
export default class DmsModule {
    constructor(manifest) {
        this.manifest = manifest;
        this.name = manifest.name;
        this.routes = [];
    }

    async init() {
        console.log(`Initializing DMS Module v${this.manifest.version}`);
        this.setupRoutes();
        console.log('DMS Module initialized');
    }

    setupRoutes() {
        this.routes = [
            {
                path: '#/dms/documents',
                handler: async () => {
                    const { DocumentsPage } = await import('./pages/documents.js');
                    return DocumentsPage;
                },
                permission: 'dms:document:read:company',
            },
        ];
    }
}
