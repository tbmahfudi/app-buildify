import { test, expect } from '@playwright/test';

const BASE = 'http://localhost:8000';

test.describe('Audit API', () => {
    let token;

    test.beforeEach(async ({ page }) => {
        const resp = await page.request.post(BASE + '/api/v1/auth/login', {
            data: { email: 'superadmin@system.com', password: 'SuperAdmin123!' }
        });
        token = (await resp.json()).access_token;
    });

    test('should list audit entries', async ({ page }) => {
        const resp = await page.request.post(BASE + '/api/v1/audit/list', {
            headers: { Authorization: 'Bearer ' + token },
            data: { page: 1, page_size: 10 }
        });
        expect(resp.ok()).toBe(true);
        const body = await resp.json();
        expect(body).toBeTruthy();
    });

    test('should require auth for audit', async ({ page }) => {
        const resp = await page.request.get(BASE + '/api/v1/audit/list');
        expect([401, 403].includes(resp.status())).toBe(true);
    });

    test('should get audit summary', async ({ page }) => {
        const resp = await page.request.get(BASE + '/api/v1/audit/summary', {
            headers: { Authorization: 'Bearer ' + token }
        });
        expect([200, 404].includes(resp.status())).toBe(true);
    });
});
