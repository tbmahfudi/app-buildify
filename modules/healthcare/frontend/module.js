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
            },
            {
                // epic-08 Organization/Departments. TODO: switch to a dedicated
                // 'healthcare:organization:read' once RBAC provisioning for new
                // module permissions is batched; reuse schedules:read meanwhile.
                path: '#/healthcare/departments',
                handler: async () => (await import('./pages/departments.js')).default,
                permission: 'healthcare:schedules:read'
            },
            {
                // epic-09 Visit Registration & Queue. Reuse appointments:read
                // until a dedicated healthcare:registration:read is provisioned.
                path: '#/healthcare/registration',
                handler: async () => (await import('./pages/registration.js')).default,
                permission: 'healthcare:appointments:read'
            },
            {
                path: '#/healthcare/queue-board',
                handler: async () => (await import('./pages/queue-board.js')).default,
                permission: 'healthcare:appointments:read'
            },
            {
                // epic-10 EMR Clinical Coding. Reuse dashboard:read until a
                // dedicated healthcare:emr:read is provisioned.
                path: '#/healthcare/emr-coding',
                handler: async () => (await import('./pages/emr-coding.js')).default,
                permission: 'healthcare:dashboard:read'
            },
            {
                // epic-11 HR. Reuse schedules:read until a dedicated
                // healthcare:hr:read is provisioned.
                path: '#/healthcare/doctors',
                handler: async () => (await import('./pages/doctors.js')).default,
                permission: 'healthcare:schedules:read'
            },
            {
                path: '#/healthcare/rooms',
                handler: async () => (await import('./pages/rooms.js')).default,
                permission: 'healthcare:schedules:read'
            },
            {
                // epic-18 Feature 18.10 (Q3) — clinic-staff approval of patient-link requests.
                path: '#/healthcare/family-approvals',
                handler: async () => (await import('./pages/family-approvals.js')).default,
                permission: 'healthcare:schedules:read'
            },
            {
                // epic-12 Reporting & Executive Dashboard.
                path: '#/healthcare/reports',
                handler: async () => (await import('./pages/reports.js')).default,
                permission: 'healthcare:dashboard:read'
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
                    { title: 'Lab Orders', route: 'healthcare/lab-orders', icon: 'ph-duotone ph-flask', permission: 'healthcare:lab:read' },
                    { title: 'Departments', route: 'healthcare/departments', icon: 'ph-duotone ph-buildings', permission: 'healthcare:schedules:read' },
                    { title: 'Registration', route: 'healthcare/registration', icon: 'ph-duotone ph-user-plus', permission: 'healthcare:appointments:read' },
                    { title: 'Queue Board', route: 'healthcare/queue-board', icon: 'ph-duotone ph-users-three', permission: 'healthcare:appointments:read' },
                    { title: 'EMR Coding', route: 'healthcare/emr-coding', icon: 'ph-duotone ph-notepad', permission: 'healthcare:dashboard:read' },
                    { title: 'Doctors', route: 'healthcare/doctors', icon: 'ph-duotone ph-stethoscope', permission: 'healthcare:schedules:read' },
                    { title: 'Rooms', route: 'healthcare/rooms', icon: 'ph-duotone ph-door-open', permission: 'healthcare:schedules:read' },
                    { title: 'Family Approvals', route: 'healthcare/family-approvals', icon: 'ph-duotone ph-users-three', permission: 'healthcare:schedules:read' },
                    { title: 'Reports', route: 'healthcare/reports', icon: 'ph-duotone ph-chart-line-up', permission: 'healthcare:dashboard:read' }
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
