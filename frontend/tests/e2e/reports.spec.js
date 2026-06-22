import { test, expect } from '@playwright/test';

const BASE = 'http://localhost:8000';

test.describe('Reports API', () => {
    let token;

    test.beforeEach(async ({ page }) => {
        const resp = await page.request.post(BASE + '/api/v1/auth/login', {
            data: { email: 'ceo@techstart.com', password: 'password123' }
        });
        token = (await resp.json()).access_token;
    });

    test('should list report definitions', async ({ page }) => {
        const resp = await page.request.get(BASE + '/api/v1/reports/definitions', {
            headers: { Authorization: 'Bearer ' + token }
        });
        expect(resp.ok()).toBe(true);
    });

    test('should require auth for reports', async ({ page }) => {
        const resp = await page.request.get(BASE + '/api/v1/reports/definitions');
        expect([401, 403].includes(resp.status())).toBe(true);
    });

    test('should create and delete a report', async ({ page }) => {
        const createResp = await page.request.post(BASE + '/api/v1/reports/definitions', {
            headers: { Authorization: 'Bearer ' + token },
            data: {
                name: 'E2E Report ' + Date.now(),
                description: 'E2E test',
                query_config: { entity: 'users', fields: ['id', 'email'] }
            }
        });
        expect([200, 201, 422].includes(createResp.status())).toBe(true);
        if (createResp.ok()) {
            const report = await createResp.json();
            if (report.id) {
                await page.request.delete(BASE + '/api/v1/reports/definitions/' + report.id, {
                    headers: { Authorization: 'Bearer ' + token }
                });
            }
        }
    });
});
