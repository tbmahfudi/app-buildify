import { test, expect } from '@playwright/test';

const BASE = 'http://localhost:8000';

test.describe('Settings API', () => {
    let token;

    test.beforeEach(async ({ page }) => {
        const resp = await page.request.post(BASE + '/api/v1/auth/login', {
            data: { email: 'ceo@techstart.com', password: 'password123' }
        });
        token = (await resp.json()).access_token;
    });

    test('should get or 404 user settings', async ({ page }) => {
        const resp = await page.request.get(BASE + '/api/v1/settings/user', {
            headers: { Authorization: 'Bearer ' + token }
        });
        expect([200, 404].includes(resp.status())).toBe(true);
    });

    test('should get or 404 tenant settings', async ({ page }) => {
        const resp = await page.request.get(BASE + '/api/v1/settings/tenant', {
            headers: { Authorization: 'Bearer ' + token }
        });
        expect([200, 404].includes(resp.status())).toBe(true);
    });

    test('should update user settings', async ({ page }) => {
        const resp = await page.request.put(BASE + '/api/v1/settings/user', {
            headers: { Authorization: 'Bearer ' + token },
            data: { theme: 'dark', language: 'en' }
        });
        expect([200, 201, 204].includes(resp.status())).toBe(true);
    });

    test('should require auth for settings', async ({ page }) => {
        const resp = await page.request.get(BASE + '/api/v1/settings/user');
        expect([401, 403].includes(resp.status())).toBe(true);
    });
});
