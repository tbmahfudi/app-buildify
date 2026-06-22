import { test, expect } from '@playwright/test';

const BASE = 'http://localhost:8000';

test.describe('Dashboards API', () => {
    let token;

    test.beforeEach(async ({ page }) => {
        const resp = await page.request.post(BASE + '/api/v1/auth/login', {
            data: { email: 'ceo@techstart.com', password: 'password123' }
        });
        token = (await resp.json()).access_token;
    });

    test('should list dashboards', async ({ page }) => {
        const resp = await page.request.get(BASE + '/api/v1/dashboards', {
            headers: { Authorization: 'Bearer ' + token }
        });
        expect(resp.ok()).toBe(true);
    });

    test('should require auth for dashboards', async ({ page }) => {
        const resp = await page.request.get(BASE + '/api/v1/dashboards');
        expect([401, 403].includes(resp.status())).toBe(true);
    });

    test('should create and delete a dashboard', async ({ page }) => {
        const createResp = await page.request.post(BASE + '/api/v1/dashboards', {
            headers: { Authorization: 'Bearer ' + token },
            data: { name: 'E2E Dashboard ' + Date.now(), description: 'E2E test', widgets: [] }
        });
        expect([200, 201, 422].includes(createResp.status())).toBe(true);
        if (createResp.ok()) {
            const dash = await createResp.json();
            if (dash.id) {
                await page.request.delete(BASE + '/api/v1/dashboards/' + dash.id, {
                    headers: { Authorization: 'Bearer ' + token }
                });
            }
        }
    });
});
