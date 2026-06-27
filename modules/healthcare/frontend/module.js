/**
 * Healthcare Module - Frontend
 *
 * Main module class for the Healthcare module frontend. Mirrors the financial
 * module's first-class structure: extends nothing platform-specific but exposes
 * init/setupRoutes/setupMenu/getRoutes/getMenuItems so the shell loader can
 * register routes and menu entries from a single entry point.
 *
 * Conforms to docs/modules/MODULE_FRONTEND_CONTRACT.md.
 */

export default class HealthcareModule {
    constructor(manifest) {
        this.manifest = manifest;
        this.name = manifest.name;
        this.config = {};
        this.routes = [];
        this.menuItems = [];
    }

    async init() {
        console.log(`Initializing Healthcare Module v${this.manifest.version}`);
        this.setupRoutes();
        this.setupMenu();
        console.log('Healthcare Module initialized');
    }

    setupRoutes() {
        this.routes = [
            {
                path: '#/healthcare/dashboard',
                handler: async () => (await import('./pages/dashboard.js')).default,
                permission: 'healthcare:dashboard:read'
            },
            {
                path: '#/healthcare/appointments',
                handler: async () => (await import('./pages/appointments.js')).default,
                permission: 'healthcare:appointments:read'
            },
            {
                path: '#/healthcare/schedules',
                handler: async () => (await import('./pages/schedules.js')).default,
                permission: 'healthcare:schedules:read'
            },
            {
                path: '#/healthcare/invoices',
                handler: async () => (await import('./pages/invoices.js')).default,
                permission: 'healthcare:billing:read'
            },
            {
                path: '#/healthcare/prescriptions',
                handler: async () => (await import('./pages/prescriptions.js')).default,
                permission: 'healthcare:pharmacy:read'
            },
            {
                path: '#/healthcare/lab-orders',
                handler: async () => (await import('./pages/lab-orders.js')).default,
                permission: 'healthcare:lab:read'
            }
        ];
    }

    setupMenu() {
        this.menuItems = [
            {
                title: 'Healthcare',
                icon: 'ph-duotone ph-first-aid-kit',
                iconColor: 'text-rose-600',
                children: [
                    { title: 'Dashboard', route: 'healthcare/dashboard', icon: 'ph-duotone ph-squares-four', permission: 'healthcare:dashboard:read' },
                    { title: 'Appointments', route: 'healthcare/appointments', icon: 'ph-duotone ph-calendar-check', permission: 'healthcare:appointments:read' },
                    { title: 'Schedules', route: 'healthcare/schedules', icon: 'ph-duotone ph-calendar', permission: 'healthcare:schedules:read' },
                    { title: 'Invoices', route: 'healthcare/invoices', icon: 'ph-duotone ph-receipt', permission: 'healthcare:billing:read' },
                    { title: 'Prescriptions', route: 'healthcare/prescriptions', icon: 'ph-duotone ph-pill', permission: 'healthcare:pharmacy:read' },
                    { title: 'Lab Orders', route: 'healthcare/lab-orders', icon: 'ph-duotone ph-flask', permission: 'healthcare:lab:read' }
                ]
            }
        ];
    }

    getRoutes() {
        return this.routes;
    }

    getMenuItems() {
        return this.menuItems;
    }

    cleanup() {
        console.log('Cleaning up Healthcare Module');
    }
}
