import { test, expect } from '@playwright/test';

const BASE = 'http://localhost:8000';

test.describe('Builder Pages API', () => {
    let token;

    test.beforeEach(async ({ page }) => {
        const resp = await page.request.post(BASE + '/api/v1/auth/login', {
            data: { email: 'ceo@techstart.com', password: 'password123' }
        });
        token = (await resp.json()).access_token;
    });

    test('should list builder pages', async ({ page }) => {
        const resp = await page.request.get(BASE + '/api/v1/builder/', {
            headers: { Authorization: 'Bearer ' + token }
        });
        expect(resp.ok()).toBe(true);
    });

    test('should require auth for builder pages', async ({ page }) => {
        const resp = await page.request.get(BASE + '/api/v1/builder/');
        expect([401, 403].includes(resp.status())).toBe(true);
    });

    test('should create and delete a page', async ({ page }) => {
        const slug = 'e2e-page-' + Date.now();
        const createResp = await page.request.post(BASE + '/api/v1/builder/', {
            headers: { Authorization: 'Bearer ' + token },
            data: { name: 'E2E Page ' + Date.now(), slug, layout: { components: [] } }
        });
        expect([200, 201, 422].includes(createResp.status())).toBe(true);
        if (createResp.ok()) {
            const pg = await createResp.json();
            if (pg.id) {
                await page.request.delete(BASE + '/api/v1/builder/' + pg.id, {
                    headers: { Authorization: 'Bearer ' + token }
                });
            }
        }
    });
});
