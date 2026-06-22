import { test, expect } from '@playwright/test';

const BASE = 'http://localhost:8000';

test.describe('Users API', () => {
    let token;

    test.beforeEach(async ({ page }) => {
        const resp = await page.request.post(BASE + '/api/v1/auth/login', {
            data: { email: 'ceo@techstart.com', password: 'password123' }
        });
        token = (await resp.json()).access_token;
    });

    test('should list users', async ({ page }) => {
        const resp = await page.request.get(BASE + '/api/v1/org/users', {
            headers: { Authorization: 'Bearer ' + token }
        });
        expect(resp.ok()).toBe(true);
        const body = await resp.json();
        const users = Array.isArray(body) ? body : (body.items || body.data || []);
        expect(Array.isArray(users)).toBe(true);
    });

    test('should get current user profile', async ({ page }) => {
        const resp = await page.request.get(BASE + '/api/v1/auth/me', {
            headers: { Authorization: 'Bearer ' + token }
        });
        expect(resp.ok()).toBe(true);
        const me = await resp.json();
        expect(me.email).toBeTruthy();
    });

    test('should require auth for user list', async ({ page }) => {
        const resp = await page.request.get(BASE + '/api/v1/org/users');
        expect([401, 403].includes(resp.status())).toBe(true);
    });
});
