import { test, expect } from '@playwright/test';

const BASE = 'http://localhost:8000';

test.describe('Authentication', () => {
    test('should login with valid credentials', async ({ page }) => {
        const resp = await page.request.post(BASE + '/api/v1/auth/login', {
            data: { email: 'ceo@techstart.com', password: 'password123' }
        });
        expect(resp.ok()).toBe(true);
        const body = await resp.json();
        expect(body.access_token || body.token).toBeTruthy();
    });

    test('should reject invalid credentials', async ({ page }) => {
        const resp = await page.request.post(BASE + '/api/v1/auth/login', {
            data: { email: 'wrong@email.com', password: 'wrongpass' }
        });
        expect(resp.ok()).toBe(false);
    });

    test('should return current user info', async ({ page }) => {
        const loginResp = await page.request.post(BASE + '/api/v1/auth/login', {
            data: { email: 'ceo@techstart.com', password: 'password123' }
        });
        const body = await loginResp.json();
        const token = body.access_token;
        const meResp = await page.request.get(BASE + '/api/v1/auth/me', {
            headers: { Authorization: 'Bearer ' + token }
        });
        expect(meResp.ok()).toBe(true);
        const me = await meResp.json();
        expect(me.email).toBe('ceo@techstart.com');
    });

    test('should reject unauthenticated /auth/me', async ({ page }) => {
        const resp = await page.request.get(BASE + '/api/v1/auth/me');
        expect([401, 403].includes(resp.status())).toBe(true);
    });

    test('should refresh token', async ({ page }) => {
        const loginResp = await page.request.post(BASE + '/api/v1/auth/login', {
            data: { email: 'ceo@techstart.com', password: 'password123' }
        });
        const body = await loginResp.json();
        const refreshToken = body.refresh_token;
        if (!refreshToken) { return; }
        const refreshResp = await page.request.post(BASE + '/api/v1/auth/refresh', {
            data: { refresh_token: refreshToken }
        });
        expect([200, 201].includes(refreshResp.status())).toBe(true);
    });
});
