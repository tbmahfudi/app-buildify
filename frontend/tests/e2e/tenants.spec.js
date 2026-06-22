import { test, expect } from '@playwright/test';

const BASE = 'http://localhost:8000';

test.describe('Tenants API', () => {
    let token;

    test.beforeEach(async ({ page }) => {
        const resp = await page.request.post(BASE + '/api/v1/auth/login', {
            data: { email: 'superadmin@system.com', password: 'SuperAdmin123!' }
        });
        token = (await resp.json()).access_token;
    });

    test('should list tenants as superadmin', async ({ page }) => {
        const resp = await page.request.get(BASE + '/api/v1/org/tenants', {
            headers: { Authorization: 'Bearer ' + token }
        });
        expect(resp.ok()).toBe(true);
        const body = await resp.json();
        const tenants = Array.isArray(body) ? body : (body.items || body.data || []);
        expect(tenants.length).toBeGreaterThan(0);
    });

    test('should get tenant details', async ({ page }) => {
        const listResp = await page.request.get(BASE + '/api/v1/org/tenants', {
            headers: { Authorization: 'Bearer ' + token }
        });
        const list = await listResp.json();
        const tenants = Array.isArray(list) ? list : (list.items || list.data || []);
        if (tenants.length > 0) {
            const resp = await page.request.get(BASE + '/api/v1/org/tenants/' + tenants[0].id, {
                headers: { Authorization: 'Bearer ' + token }
            });
            expect(resp.ok()).toBe(true);
        }
    });

    test('should reject tenant list without auth', async ({ page }) => {
        const resp = await page.request.get(BASE + '/api/v1/org/tenants');
        expect([401, 403].includes(resp.status())).toBe(true);
    });
});
